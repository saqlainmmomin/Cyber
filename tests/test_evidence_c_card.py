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


def add_conclusion(db, assessment, citations, requirement='ISO.A5.18', manifest=None):
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
    if manifest is not None:
        envelope = json.loads(run.claims_json)
        envelope['document_manifest'] = manifest
        run.claims_json = json.dumps(envelope)
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
    unused, unused_version = add_file(db, assessment, 'Export.xlsx')
    add_file(db, assessment, 'Archived.docx', status='archived')
    add_file(db, assessment, 'Other control.docx', requirement='ISO.A5.1')
    _, _, other_assessment = seed_engagement(db, frameworks=('iso27001',), client_name='Other client')
    add_file(db, other_assessment, 'Other assessment.docx')
    db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', raw_ai_response=json.dumps(
        {'budget_skipped_filenames': ['Export.xlsx', 'Other control.docx'],
         'budget_partial_filenames': ['Q2 review.docx']})))
    conclusion = add_conclusion(db, assessment, [{'evidence_version_id': version.id,
        'location_type': 'text_span', 'location_ref': 'chars:2-18', 'excerpt': version.extracted_text[2:18]}], manifest={
            'selection': [
                {'evidence_version_id': version.id, 'filename': 'Q2 review.docx', 'status': 'partial'},
                {'evidence_version_id': unused_version.id, 'filename': 'Export.xlsx', 'status': 'not_read'},
            ],
            'judge': {'passages': {'ISO.A5.18': [{'evidence_version_id': unused_version.id,
                'filename': 'Export.xlsx', 'quote': 'A reviewed passage.',
                'reused_from_desk_review': True, 'outside_cut': True}]}},
        })
    html = card_html(http, assessment, conclusion)
    assert 'Evidence on this control' in html
    assert '2 files linked, 1 cited' in html
    assert f'data-evidence-version="{version.id}"' in html
    assert f'data-evidence-version="{unused_version.id}"' in html
    assert 'Missing evidence' not in html
    rows = re.findall(r'<li data-control-evidence="([^"]+)".*?</li>', html, re.S)
    assert set(rows) == {evidence.id, unused.id}
    assert re.search(r'data-control-evidence="' + evidence.id + r'".*?Cited', html, re.S)
    assert re.search(r'data-control-evidence="' + unused.id + r'".*?Not cited by the analysis', html, re.S)
    assert 'Not included in this run’s document cut (size limit): Export.xlsx' in html
    assert 'Partly included in this run’s document cut (size limit): Q2 review.docx' in html
    assert 'Quotes reused from desk review outside this run’s document cut: Export.xlsx' in html
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


def test_legacy_filename_budget_is_not_a_record_of_this_analysis(db, http):
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    add_file(db, assessment, 'Same.pdf')
    db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', raw_ai_response=json.dumps(
        {'budget_skipped_filenames': ['Same.pdf']})))
    conclusion = add_conclusion(db, assessment, [])
    assert 'data-budget-skipped' not in card_html(http, assessment, conclusion)


def test_duplicate_filename_notice_uses_linked_version(db, http):
    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    _, linked = add_file(db, assessment, 'Same.pdf')
    _, unlinked = add_file(db, assessment, 'Same.pdf', requirement='ISO.A5.1')
    conclusion = add_conclusion(db, assessment, [], manifest={'selection': [
        {'evidence_version_id': linked.id, 'filename': 'Same.pdf', 'status': 'read'},
        {'evidence_version_id': unlinked.id, 'filename': 'Same.pdf', 'status': 'not_read'},
    ]})
    assert 'data-budget-skipped' not in card_html(http, assessment, conclusion)


def test_report_basis_counts_actual_documents_and_names_reused_quotes(db):
    from types import SimpleNamespace
    from app.services.approved_report import _evidence_basis_line

    _, _, assessment = seed_engagement(db, frameworks=('iso27001',))
    _, version = add_file(db, assessment, 'Review.pdf')
    _, skipped = add_file(db, assessment, 'Skipped.pdf')
    documents = [
        {'evidence_version_id': version.id, 'filename': 'Review.pdf', 'status': 'read'},
        {'evidence_version_id': skipped.id, 'filename': 'Skipped.pdf', 'status': 'not_read'},
    ]
    conclusion = add_conclusion(db, assessment, [], manifest={
        'selection': documents,
        'extraction': {'mode': 'documents', 'documents': documents[:1]},
        'judge': {'documents': [], 'passages': {'ISO.A5.18': [
            {'evidence_version_id': skipped.id, 'filename': 'Skipped.pdf',
             'quote': 'Reused text', 'reused_from_desk_review': True, 'outside_cut': True},
        ]}},
    })
    row = SimpleNamespace(conclusion_id=conclusion.id, framework_id='iso27001', requirement_id='ISO.A5.18')
    line = _evidence_basis_line(db, [row])
    assert '1 file read, 1 not read' in line
    assert 'Read: Review.pdf' in line
    assert 'Not read: Skipped.pdf' in line
    assert 'Desk-review quotes reused for judging: Skipped.pdf' in line

    run = db.query(AnalysisRun).filter_by(assessment_id=assessment.id).one()
    envelope = json.loads(run.claims_json)
    envelope['document_manifest']['extraction'] = {'mode': 'reused_desk_review', 'documents': []}
    run.claims_json = json.dumps(envelope)
    db.flush()
    assert '1 file read, 1 not read' in _evidence_basis_line(db, [row])


    # A full read in any framework beats partial and unread selections.
    envelope['document_manifest'] = {'frameworks': {
        'iso27001': {'selection': documents},
        'nist_csf': {'selection': [{**documents[1], 'status': 'partial'}]},
        'dpdpa': {'selection': [{**documents[1], 'status': 'read'}]},
    }}
    run.claims_json = json.dumps(envelope)
    db.flush()
    line = _evidence_basis_line(db, [row])
    assert '2 files read, 0 not read' in line
    assert 'Partly read:' not in line

    # Later runs cannot turn a full read back into an unread or partial file.
    second = add_conclusion(db, assessment, [], requirement='ISO.A5.1', manifest={
        'selection': [{**documents[1], 'status': 'partial'}],
    })
    second_row = SimpleNamespace(conclusion_id=second.id, framework_id='iso27001', requirement_id='ISO.A5.1')
    for rows in ([row, second_row], [second_row, row]):
        line = _evidence_basis_line(db, rows)
        assert '2 files read, 0 not read' in line
        assert 'Partly read:' not in line

    many = [{'evidence_version_id': f'file-{i}', 'filename': f'File {i}.pdf', 'status': 'read'}
            for i in range(10)]
    envelope['document_manifest'] = {'selection': many}
    run.claims_json = json.dumps(envelope)
    db.flush()
    full = _evidence_basis_line(db, [row])
    short = _evidence_basis_line(db, [row], filename_limit=8)
    assert '10 files read, 0 not read.' in short
    assert 'File 7.pdf and 2 more; the full list is in the PDF and DOCX report' in short
    assert 'File 8.pdf' not in short
    assert 'File 9.pdf' in full


def test_report_basis_pdf_moves_long_paragraph_to_continuation_page(canonical_dpdpa_assessment):
    import io
    import pdfplumber
    from tests.test_golden_dpdpa import _analyze
    from tests.support.canonical_dpdpa import materialize_report
    from app.utils.pdf_export import generate_pdf, CONTENT_BOTTOM

    canonical = canonical_dpdpa_assessment
    report, items = materialize_report(canonical.session, canonical.assessment, _analyze(canonical))
    report.evidence_basis_line = 'Analysis document input: 100 files read, 0 not read. Read: ' + ', '.join(
        f'Evidence document number {i:03d} reviewed.pdf' for i in range(100)
    ) + '.'
    content = generate_pdf(report, items, canonical.assessment.company_name,
                           initiatives=[], selected_frameworks=['dpdpa'])
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        page = next(page for page in pdf.pages if 'Analysis document input:' in (page.extract_text() or ''))
        assert 'Methodology (continued)' in page.extract_text()
        assert 'number 099 reviewed.pdf' in page.extract_text()
        ending = page.search(r'number 099 reviewed\.pdf')[0]
        assert ending['bottom'] < CONTENT_BOTTOM * 72 / 25.4
