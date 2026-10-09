"""Checkable conclusions use real source links and scoped evidence mappings."""
import json
import re
from datetime import datetime, timezone
from html import unescape

import pytest
from sqlalchemy import event

from app.models.analysis_run import AnalysisRun
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewSummary
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from tests.yozora_support import (  # noqa: F401
    _register_frameworks, db, db_path, engine, http, upload_root, seed_engagement,
)


def add_file(db, assessment, name, *, status='active', requirement='ISO.A5.18'):
    evidence = Evidence(engagement_id=assessment.engagement_id, assessment_id=assessment.id,
                        original_filename=name, storage_path='unused', file_hash_sha256='a' * 64,
                        file_size_bytes=20, mime_type='text/plain', status=status, uploaded_by='Tester')
    db.add(evidence)
    db.flush()
    version = EvidenceVersion(evidence_id=evidence.id, version_number=1, status='active',
                              original_filename=name, storage_path='unused', file_hash_sha256='a' * 64,
                              file_size_bytes=20, mime_type='text/plain', extracted_text='A reviewed passage. End.')
    db.add(version)
    db.add(EvidenceUse(evidence_id=evidence.id, assessment_id=assessment.id,
                       framework_id='iso27001', requirement_id=requirement, relevance='supports'))
    db.flush()
    return evidence, version


def add_conclusion(db, assessment, citations, requirement='ISO.A5.18'):
    conclusion = Conclusion(assessment_id=assessment.id, framework_id='iso27001', requirement_id=requirement,
                            outcome='partially_compliant', rationale='A review is incomplete.', evidence_summary='',
                            gaps_identified='', risk_level='medium', recommended_action='', ai_proposed=True)
    db.add(conclusion)
    db.flush()
    run = AnalysisRun(assessment_id=assessment.id, framework_id='iso27001', status='completed',
                      claims_json='{}', model_id='fixture', started_at=datetime.now(timezone.utc))
    db.add(run)
    db.flush()
    revision = ConclusionRevision(conclusion_id=conclusion.id, actor='ai', action='proposed',
                                  analysis_run_id=run.id, citations_json=json.dumps(citations))
    db.add(revision)
    db.flush()
    run.claims_json = json.dumps({'claims': [{'revision_id': revision.id, 'outcome': conclusion.outcome,
                                              'item': {'gap_description': conclusion.rationale}}]})
    db.commit()
    return conclusion


def card_html(http, assessment, conclusion):
    response = http.get(f'/assessments/{assessment.id}/conclusions')
    assert response.status_code == 200, response.text
    start = response.text.index(f'id="conclusion-card-{conclusion.id}"')
    end = response.text.find('<div id="conclusion-card-', start + 1)
    return response.text[start:] if end == -1 else response.text[start:end]


@pytest.mark.parametrize('ref,label', [('chars:2-18', 'Characters 2–18'), ('whole', 'Whole document')])
def test_citation_label_links_to_original_record_and_passage(db, http, ref, label):
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    evidence, version = add_file(db, assessment, 'Review.docx')
    excerpt = version.extracted_text[2:18] if ref != 'whole' else ''
    conclusion = add_conclusion(db, assessment, [{'evidence_version_id': version.id,
        'location_type': 'text_span' if ref != 'whole' else 'whole_item', 'location_ref': ref, 'excerpt': excerpt}])
    html = card_html(http, assessment, conclusion)
    assert f'href="/evidence/{evidence.id}">Review.docx</a>' in html
    link = re.search(r'href="([^"]+/span\?ref=[^"]+#cited-span)"[^>]*>' + label + '</a>', html)
    assert link, html
    span = http.get(unescape(link.group(1)))
    assert span.status_code == 200
    assert label in span.text
    if excerpt:
        assert f'<mark id="cited-span" data-cited-span>{excerpt}</mark>' in span.text


def test_linked_evidence_status_counts_scope_and_skipped_notice(db, http):
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    evidence, version = add_file(db, assessment, 'Q2 review.docx')
    unused, _ = add_file(db, assessment, 'Export.xlsx')
    add_file(db, assessment, 'Archived.docx', status='archived')
    add_file(db, assessment, 'Other control.docx', requirement='ISO.A5.1')
    _, _, other_assessment = seed_engagement(db, frameworks=('iso27001',), client_name='Other client')
    add_file(db, other_assessment, 'Other assessment.docx')
    db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', raw_ai_response=json.dumps(
        {'budget_skipped_filenames': ['Export.xlsx', 'Other control.docx'],
         'budget_partial_filenames': ['Q2 review.docx']})))
    conclusion = add_conclusion(db, assessment, [{'evidence_version_id': version.id,
        'location_type': 'text_span', 'location_ref': 'chars:2-18', 'excerpt': version.extracted_text[2:18]}])
    html = card_html(http, assessment, conclusion)
    assert 'Evidence on this control' in html
    assert '2 files linked, 1 cited' in html
    assert 'Missing evidence' not in html
    rows = re.findall(r'<li data-control-evidence="([^"]+)".*?</li>', html, re.S)
    assert set(rows) == {evidence.id, unused.id}
    assert re.search(r'data-control-evidence="' + evidence.id + r'".*?Cited', html, re.S)
    assert re.search(r'data-control-evidence="' + unused.id + r'".*?Not cited by the analysis', html, re.S)
    assert 'Not read by the analysis (size limit): Export.xlsx' in html
    assert 'Partly read by the analysis (size limit): Q2 review.docx' in html
    assert 'Other control.docx' not in html
    assert 'Other assessment.docx' not in html


def test_missing_evidence_suggestion_remains_without_links(db, http):
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    conclusion = add_conclusion(db, assessment, [])
    html = card_html(http, assessment, conclusion)
    assert 'Missing evidence' in html
    assert 'data-linked-evidence-count' not in html


def test_evidence_links_are_batched_once_for_the_conclusions_page(db, http, engine):
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    add_file(db, assessment, 'Access review.xlsx')
    for requirement in ('ISO.A5.18', 'ISO.A5.1', 'ISO.A5.2'):
        add_conclusion(db, assessment, [], requirement)
    queries = []
    def capture(_conn, _cursor, statement, _params, _context, _many):
        if 'evidence_uses' in statement.lower() and 'JOIN evidence_versions' in statement:
            queries.append(statement)
    event.listen(engine, 'before_cursor_execute', capture)
    try:
        page = http.get(f'/assessments/{assessment.id}/conclusions')
    finally:
        event.remove(engine, 'before_cursor_execute', capture)
    assert page.status_code == 200
    assert len(queries) == 1
    assert 'evidence_uses.assessment_id =' in queries[0]


def test_linked_files_keep_requests_already_on_the_draft_rfi(db, http):
    from app.services import rfi_evidence_requests
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    add_file(db, assessment, 'Access review.xlsx')
    conclusion = add_conclusion(db, assessment, [])
    rfi_evidence_requests.record_request(
        db, conclusion=conclusion, request_key_value='iso27001:ISO.A5.18:access-review',
        document_type='access_review', title='Access review records', request='Send the Q3 review.',
        analysis_run_id=None, actor='Tester')
    db.commit()
    html = card_html(http, assessment, conclusion)
    assert '1 file linked, 0 cited' in html
    assert 'Also on the draft RFI for this conclusion' in html
    assert 'Remove from draft RFI' in html
