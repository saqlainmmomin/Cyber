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
