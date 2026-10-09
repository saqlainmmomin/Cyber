"""Citations open the evidence record at the cited passage, with the whole document around it."""
from tests.test_evidence_viewer import upload
from tests.yozora_support import (  # noqa: F401
    _register_frameworks, db, db_path, engine, http, upload_root, seed_engagement,
)


def test_long_document_shows_full_text_around_the_highlight(db, http, monkeypatch):
    opening = 'Opening clause. ' * 400
    quote = 'Access is reviewed every quarter by the system owner, who signs the review record.'
    closing = 'Closing clause. ' * 400
    text = 'FIRST LINE\n' + opening + quote + closing + '\nLAST LINE'
    _, evidence, version = upload(db, http, monkeypatch, text)
    start = text.index(quote)
    ref = f'chars:{start}-{start + len(quote)}'

    redirect = http.get(f'/evidence-versions/{version.id}/span', params={'ref': ref}, follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers['location'].startswith(f'/evidence/{evidence.id}?version={version.id}&ref=chars%3A')

    page = http.get(redirect.headers['location'])
    assert page.status_code == 200
    assert f'<mark id="cited-span" data-cited-span>{quote}</mark>' in page.text
    assert 'FIRST LINE' in page.text and 'LAST LINE' in page.text
    assert f'Characters {start}–{start + len(quote)}' in page.text


def test_document_comes_first_and_file_details_are_collapsed_last(db, http, monkeypatch):
    _, evidence, _ = upload(db, http, monkeypatch, 'Body of the policy')
    page = http.get(f'/evidence/{evidence.id}').text
    document = page.index('id="read-heading"')
    assert document < page.index('id="original-heading"')
    details = page.index('data-file-details')
    assert page.index('<h2>Versions</h2>') < details
    assert document < details < page.index('Original SHA-256')
    assert '<details class="glass dr-disclose" style="margin-top:var(--s-10)" data-file-details>' in page
    assert 'id="cited-span"' not in page


def test_unknown_version_or_bad_location_is_refused(db, http, monkeypatch):
    _, evidence, version = upload(db, http, monkeypatch, 'Some text here')
    page = http.get(f'/evidence/{evidence.id}', params={'version': 'missing', 'ref': 'chars:0-4'})
    assert page.status_code == 404
    bad = http.get(f'/evidence/{evidence.id}', params={'version': version.id, 'ref': 'chars:4-0'})
    assert bad.status_code == 400


def _desk_review(db, assessment, version, catalog=True):
    import json
    from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
    if catalog:
        db.add(DeskReviewSummary(assessment_id=assessment.id, status='completed', document_catalog=json.dumps([
            {'filename': version.original_filename, 'document_type': 'Access policy',
             'summary': 'Sets quarterly access reviews.', 'coverage_areas': ['ISO.A5.18', 'CH2.CONSENT']}])))
    db.add(DeskReviewFinding(assessment_id=assessment.id, finding_type='evidence', framework_id='iso27001',
                             requirement_id='ISO.A5.18', content='Access reviews are quarterly',
                             citations_json=json.dumps([{'evidence_version_id': version.id, 'location_type': 'chars',
                                                         'location_ref': 'chars:0-6', 'excerpt': 'Access'}])))
    db.add(DeskReviewFinding(assessment_id=assessment.id, finding_type='evidence', framework_id='iso27001',
                             requirement_id='ISO.A5.15', content='Legacy finding'))
    db.commit()


def test_summary_opens_the_page_when_desk_review_read_the_file(db, http, monkeypatch):
    from tests.yozora_support import seed_engagement as seed
    monkeypatch.setattr('tests.test_evidence_viewer.seed_engagement',
                        lambda db: seed(db, frameworks=('iso27001', 'dpdpa')))
    assessment, evidence, version = upload(db, http, monkeypatch, 'Access is reviewed quarterly.')
    _desk_review(db, assessment, version)
    page = http.get(f'/evidence/{evidence.id}').text
    summary = page.index('id="summary-heading"')
    assert summary < page.index('id="read-heading"')
    block = page[summary:page.index('id="read-heading"')]
    assert 'Access policy' in block and 'Sets quarterly access reviews.' in block
    assert 'Controls it covers' in block
    assert 'Access rights · ISO.A5.18' in block
    assert '<span class="chip">CH2.CONSENT</span>' in block
    assert 'Key passages' in block and '<span data-passage-excerpt>Access</span>' in block
    assert 'Legacy finding' not in block and 'ISO.A5.15' not in block
    assert "Desk review hasn't read this file yet." not in page
    href = f'/evidence-versions/{version.id}/span?ref=chars%3A0-6#cited-span'
    assert f'href="{href}"' in block
    opened = http.get(href.split('#')[0])
    assert '<mark id="cited-span" data-cited-span>Access</mark>' in opened.text


def test_no_catalog_entry_keeps_document_text_first(db, http, monkeypatch):
    assessment, evidence, version = upload(db, http, monkeypatch, 'Access is reviewed quarterly.')
    _desk_review(db, assessment, version, catalog=False)
    page = http.get(f'/evidence/{evidence.id}').text
    assert 'data-ai-summary' not in page and 'id="summary-heading"' not in page
    assert 'Key passages' not in page
    assert "Desk review hasn't read this file yet." in page
    assert page.index('id="read-heading"') < page.index('id="original-heading"')


def test_catalog_is_not_shown_twice(db, http, monkeypatch):
    assessment, evidence, version = upload(db, http, monkeypatch, 'Access is reviewed quarterly.')
    _desk_review(db, assessment, version)
    page = http.get(f'/evidence/{evidence.id}').text
    assert 'What the AI made of it' not in page and 'catalog-heading' not in page
    assert page.count('Sets quarterly access reviews.') == 1
    # The Citations list still carries the finding.
    assert 'Access reviews are quarterly' in page[page.index('<h3 style="margin-top:var(--s-5)">Citations</h3>'):]


def test_same_passage_cited_twice_shows_once_and_untagged_findings_use_the_assessment_frameworks(db, http, monkeypatch):
    from tests.yozora_support import seed_engagement as seed
    import json
    from app.models.desk_review import DeskReviewFinding
    monkeypatch.setattr('tests.test_evidence_viewer.seed_engagement',
                        lambda db: seed(db, frameworks=('iso27001',)))
    assessment, evidence, version = upload(db, http, monkeypatch, 'Access is reviewed quarterly.')
    _desk_review(db, assessment, version)
    db.add(DeskReviewFinding(assessment_id=assessment.id, finding_type='evidence', framework_id=None,
                             requirement_id='ISO.A5.18', content='Same quote again',
                             citations_json=json.dumps([{'evidence_version_id': version.id, 'location_type': 'chars',
                                                         'location_ref': 'chars:0-6', 'excerpt': 'Access'}])))
    db.commit()
    page = http.get(f'/evidence/{evidence.id}').text
    block = page[page.index('id="summary-heading"'):page.index('id="read-heading"')]
    assert block.count('<span data-passage-excerpt>Access</span>') == 1
    assert block.count('Access rights · ISO.A5.18') >= 1
