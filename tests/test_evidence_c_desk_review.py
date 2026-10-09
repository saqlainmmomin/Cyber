"""Desk-review size-limit and evidence filename behavior."""
import json

import pytest

from app.config import settings
from app.models.assessment import AssessmentDocument
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.services import desk_review, evidence as evidence_service
from tests.test_evidence_viewer import upload
from tests.yozora_support import (  # noqa: F401
    _register_frameworks, db, db_path, engine, http, upload_root, seed_engagement,
)


def test_budget_skipped_files_persist_and_render(db, http, monkeypatch):
    _, _, assessment = seed_engagement(db)
    for filename, text in [('First.pdf', 'one two three'), ('Partial.pdf', 'four five six'),
                           ('Skipped.pdf', 'seven eight'), ('Also_skipped.pdf', 'nine')]:
        db.add(AssessmentDocument(assessment_id=assessment.id, filename=filename,
                                 file_path='/tmp/fake.pdf', file_type='pdf',
                                 document_category='other', extracted_text=text))
        db.commit()
    monkeypatch.setattr(settings, 'max_total_document_words', 4)
    monkeypatch.setattr(settings, 'analysis_pipeline_version', 'v1')
    sent_documents = []

    def review(framework_id, **kwargs):
        sent_documents.extend(kwargs['documents'])
        return {'document_catalog': [{'filename': doc['filename']} for doc in kwargs['documents']],
                'coverage_summary': {}, 'evidence_map': {}, 'signal_flags': [], 'absence_findings': []}

    monkeypatch.setattr(desk_review, '_desk_review_call', review)
    summary = desk_review.run_desk_review(assessment.id, db)
    assert summary.status == 'completed'
    assert [doc['filename'] for doc in sent_documents] == ['First.pdf', 'Partial.pdf']
    assert sent_documents[1]['text'].startswith('four\n\n[... truncated ...]')
    assert desk_review.budget_skipped_filenames(summary) == ['Skipped.pdf', 'Also_skipped.pdf']
    page = http.get(f'/assessments/{assessment.id}/desk-review')
    assert page.status_code == 200
    assert 'Not read by the analysis (size limit): Skipped.pdf, Also_skipped.pdf' in page.text
    assert 'Not read by the analysis (size limit): Partial.pdf' not in page.text
    assert desk_review.budget_partial_filenames(summary) == ['Partial.pdf']
    assert 'Partly read by the analysis (size limit): Partial.pdf' in page.text
    assert 'Partly read by the analysis (size limit): First.pdf' not in page.text


def test_new_evidence_finding_names_use_cited_version(db, http, monkeypatch):
    assessment, evidence, version = upload(db, http, monkeypatch, filename='Real_access_review.pdf')
    assert evidence_service.analysis_documents(db, assessment.id)[0]['legacy_document_id'] is None
    citation = json.dumps([{'evidence_version_id': version.id, 'location_type': 'text_span',
                            'location_ref': 'chars:0-4', 'excerpt': 'full'}])
    db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', document_catalog='[]'))
    for kind in ('evidence', 'signal'):
        db.add(DeskReviewFinding(assessment_id=assessment.id, framework_id='dpdpa', finding_type=kind,
                                requirement_id='DPDPA-S4', content=f'{kind} found', source_quote='full',
                                document_id=None, citations_json=citation))
    db.commit()
    page = http.get(f'/assessments/{assessment.id}/desk-review')
    assert page.status_code == 200
    assert page.text.count('Real_access_review.pdf') >= 2
    assert '<span>Document</span>' not in page.text
    names = evidence_service.document_names_in_scope(db, assessment.id)
    assert names[evidence.id] == names[version.id] == 'Real_access_review.pdf'


@pytest.mark.parametrize('raw', [None, '{}', '[]', 'broken', '{"budget_skipped_filenames":null}'])
def test_old_summaries_have_no_skipped_files(raw):
    assert desk_review.budget_skipped_filenames(DeskReviewSummary(raw_ai_response=raw)) == []
