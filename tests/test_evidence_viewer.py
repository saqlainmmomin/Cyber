"""Evidence viewer contracts exercised through the public HTTP surfaces."""
import io
import json

import pytest

from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.evidence import Evidence, EvidenceVersion
from app.services import evidence as evidence_service
from tests.test_yozora_s6 import _pdf
from tests.yozora_support import (  # noqa: F401
    _register_frameworks, db, db_path, engine, http, upload_root, seed_engagement,
)


def upload(db, http, monkeypatch, text="full extracted text", filename="Policy.pdf"):
    _, _, assessment = seed_engagement(db)
    monkeypatch.setattr(evidence_service, "extract_text", lambda *a, **kw: text)
    response = http.post(f"/assessments/{assessment.id}/upload", data={"category": "other"},
                         files={"file": (filename, io.BytesIO(_pdf("viewer")), "application/pdf")})
    assert response.status_code == 200
    return assessment, db.query(Evidence).one(), db.query(EvidenceVersion).one()


def test_original_bytes_inline_download_and_sanitized_filename(db, http, monkeypatch):
    _, evidence, version = upload(db, http, monkeypatch)
    version.original_filename = '../bad\\name\r\n".pdf'
    db.commit()
    response = http.get(f"/evidence-versions/{version.id}/file")
    assert response.status_code == 200
    assert response.content == _pdf("viewer")
    assert response.headers['content-type'] == 'application/pdf'
    assert response.headers['x-content-type-options'] == 'nosniff'
    disposition = response.headers['content-disposition']
    assert disposition.startswith('inline;')
    assert '\r' not in disposition and '\n' not in disposition and '..' not in disposition
    assert http.get(f"/evidence-versions/{version.id}/file?download=1").headers['content-disposition'].startswith('attachment;')
    version.mime_type = 'text/html'
    db.commit()
    assert http.get(f"/evidence-versions/{version.id}/file").headers['content-disposition'].startswith('attachment;')


@pytest.mark.parametrize('state', ['quarantined', 'rejected', 'superseded'])
def test_file_blocks_unavailable_versions(db, http, monkeypatch, state):
    _, _, version = upload(db, http, monkeypatch)
    version.status = state
    db.commit()
    assert http.get(f"/evidence-versions/{version.id}/file").status_code == 404


def test_file_blocks_archived_missing_and_escaping_paths(db, http, monkeypatch, upload_root, tmp_path):
    _, evidence, version = upload(db, http, monkeypatch)
    original_path = version.storage_path
    outside = tmp_path / 'outside.pdf'
    outside.write_bytes(b'secret')
    (upload_root / 'escape.pdf').symlink_to(outside)
    for path in (str(outside), '../outside.pdf', 'escape.pdf', 'missing.pdf'):
        version.storage_path = path
        db.commit()
        assert http.get(f"/evidence-versions/{version.id}/file").status_code == 404
    version.storage_path = original_path
    evidence.status = 'archived'
    db.commit()
    assert http.get(f"/evidence-versions/{version.id}/file").status_code == 404
    assert http.get('/evidence-versions/missing/file').status_code == 404


def test_full_text_catalog_category_and_finding_link(db, http, monkeypatch):
    text = '<script>bad</script>' + 'x' * 4500 + 'END OF FILE'
    assessment, evidence, version = upload(db, http, monkeypatch, text)
    evidence.document_category = 'access_control_policy'
    db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', document_catalog=json.dumps([
        {'filename': version.original_filename, 'summary': 'Signed access policy', 'document_type': 'Policy', 'coverage_areas': ['Access rights']}])))
    db.add(DeskReviewFinding(assessment_id=assessment.id, finding_type='evidence', content='Review finding',
                           citations_json=json.dumps([{'evidence_version_id': version.id, 'location_ref': 'chars:0-8'}])))
    db.commit()
    page = http.get(f'/evidence/{evidence.id}')
    assert page.status_code == 200
    for expected in ('Access control policy', 'Document text', 'Signed access policy', 'Access rights', 'Review finding', 'END OF FILE'):
        assert expected in page.text
    assert '&lt;script&gt;bad&lt;/script&gt;' in page.text
    assert f'/span?ref=chars%3A0-8#cited-span' in page.text
    whole = http.get(f'/evidence-versions/{version.id}/span?ref=whole')
    assert 'END OF FILE' in whole.text


def test_spreadsheet_all_rows_notes_and_no_catalog(db, http, monkeypatch):
    text = 'Sheet: Accounts\nID | Role\n' + '\n'.join(f'E{i} | Admin' for i in range(1, 221))
    text += '\n[stored rows 1-220 of 240 in sheet "Accounts"; the remaining rows were not stored]\nSheet: More\nID | Comment\nE221 | long [cell truncated]\n[sheet "Hidden" not stored: size limit reached]\n[OCR page 2]'
    _, evidence, version = upload(db, http, monkeypatch, text)
    version.mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    version.original_filename = 'Access.xlsx'
    db.commit()
    page = http.get(f'/evidence/{evidence.id}')
    assert page.status_code == 200
    assert "Desk review hasn't read this file yet." in page.text
    assert page.text.count('data-sheet-row') == 221
    assert page.text.count('data-sheet-table') == 2
    assert '<td>E131</td>' in page.text
    assert page.text.count('data-extraction-note') == 4
    assert f'/evidence-versions/{version.id}/file?download=1' in page.text
    assert '<iframe' not in page.text



def test_sheet_title_rows_become_preamble_and_empty_cells_stay_empty():
    from app.services.evidence_viewer import text_blocks
    text = ('Sheet: Detail\nAccess Review Detail\nExported records | 220 | Expected population | 200\n'
            'Record # | Employee ID | Role | Notes\n131 | E131 | Admin | access still enabled\n132 | E132 | | \n'
            'Sheet: Summary\nReview date | 2026-09-30 | | Coverage statement')
    detail, summary = [block for block in text_blocks(text, True) if block['kind'] == 'sheet']
    assert detail['header'] == ['Record #', 'Employee ID', 'Role', 'Notes']
    assert detail['preamble'] == [['Access Review Detail'], ['Exported records', '220', 'Expected population', '200']]
    assert detail['rows'] == [['131', 'E131', 'Admin', 'access still enabled'], ['132', 'E132', '', '']]
    assert summary['header'] is None
    assert summary['rows'] == [['Review date', '2026-09-30', '', 'Coverage statement']]


@pytest.mark.parametrize('mime', ['image/png', 'image/jpeg', 'image/webp'])
def test_image_preview_and_current_version_filename(db, http, monkeypatch, mime):
    _, evidence, version = upload(db, http, monkeypatch)
    version.original_filename = 'Current image.png'
    version.mime_type = mime
    db.commit()
    page = http.get(f'/evidence/{evidence.id}')
    assert f'<img src="/evidence-versions/{version.id}/file"' in page.text
    assert 'Download Current image.png' in page.text
    response = http.get(f'/evidence-versions/{version.id}/file')
    assert response.headers['content-disposition'].startswith('inline;')
    assert response.headers['content-type'] == mime


def test_catalog_scope_duplicate_matches_and_current_name(db, http, monkeypatch):
    assessment, evidence, version = upload(db, http, monkeypatch)
    _, _, unrelated = seed_engagement(db, client_name='Other client')
    version.original_filename = 'Current.pdf'
    db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', document_catalog=json.dumps([
        {'filename': 'Policy.pdf', 'summary': 'Old version'},
        {'filename': 'Current.pdf', 'summary': 'First matching entry'},
        {'filename': 'Current.pdf', 'summary': 'Second matching entry'}])))
    db.add(DeskReviewSummary(assessment_id=unrelated.id, status='completed', document_catalog=json.dumps([
        {'filename': 'Current.pdf', 'summary': 'Unrelated catalog'}])))
    db.commit()
    page = http.get(f'/evidence/{evidence.id}')
    assert 'Multiple matches' in page.text
    assert 'First matching entry' in page.text and 'Second matching entry' in page.text
    assert 'Old version' not in page.text and 'Unrelated catalog' not in page.text


def test_conclusion_citations_and_supports_link_visible(db, http, monkeypatch):
    from app.models.conclusion import Conclusion, ConclusionRevision
    assessment, evidence, version = upload(db, http, monkeypatch, 'Quoted passage followed by context')
    evidence_service.map_evidence(db, evidence_id=evidence.id, assessment_id=assessment.id,
                                  framework_id='dpdpa', requirement_id='CH2.CONSENT.1', relevance='primary', actor='consultant:Reviewer')
    conclusion = Conclusion(assessment_id=assessment.id, requirement_id='CH2.CONSENT.1', framework_id='dpdpa',
                            outcome='partial', rationale='Reason', evidence_summary='Summary', gaps_identified='Gap',
                            risk_level='medium', recommended_action='Action', ai_proposed=True)
    db.add(conclusion)
    db.flush()
    db.add(ConclusionRevision(conclusion_id=conclusion.id, actor='consultant:Reviewer', action='proposed',
                              citations_json=json.dumps([{'evidence_version_id': version.id, 'location_ref': 'chars:0-14', 'excerpt': 'Quoted passage'}])))
    db.commit()
    page = http.get(f'/evidence/{evidence.id}')
    assert 'Conclusion: ' in page.text and '(CH2.CONSENT.1)' in page.text
    assert 'Characters 0–14' in page.text
    span = http.get(f'/evidence-versions/{version.id}/span?ref=chars:0-14')
    assert '<mark id="cited-span" data-cited-span>Quoted passage</mark>' in span.text


def test_csv_upload_renders_all_sheets_and_escaped_cells(db, http):
    _, _, assessment = seed_engagement(db)
    content = b'Employee,Role,Notes\nE131,Admin,<script>access still enabled</script>\nE220,Read,Reviewed\n'
    response = http.post(f'/assessments/{assessment.id}/upload', data={'category': 'other'},
                         files={'file': ('Access.csv', content, 'text/csv')})
    assert response.status_code == 200
    evidence = db.query(Evidence).one()
    version = db.query(EvidenceVersion).one()
    page = http.get(f'/evidence/{evidence.id}')
    assert page.text.count('data-sheet-row') == 2
    assert '<th>Employee</th>' in page.text
    assert '&lt;script&gt;access still enabled&lt;/script&gt;' in page.text
    file = http.get(f'/evidence-versions/{version.id}/file')
    assert file.content == content
    assert file.headers['content-disposition'].startswith('attachment;')
