"""Verify the reconciled docs-only audit and disk-openable prototype contracts.
No browser, server, application writes or model calls. Run from any directory.
"""
import ast
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/ui-audit'
HANDOFF = 'tasks/handoffs/2026-10-12-ui-audit-second-run.md'
CORE = ['README', 'ARCHITECTURE', 'SCREEN_INVENTORY', 'UI_ISSUES', 'ROOT_CAUSES',
        'DESIGN_SYSTEM', 'PAGE_ARCHETYPES', 'NEXTJS_MIGRATION_UI_SPEC', 'COMPONENT_INVENTORY']
SCREENS = ['questionnaire', 'review-queue', 'conclusions', 'rfi', 'report']
for name in CORE:
    assert (OUT / f'{name}.md').is_file(), name
issues = (OUT / 'UI_ISSUES.md').read_text()
blocks = re.split(r'(?m)^## (UI-\d{3}):', issues)[1:]
assert len(blocks) == 70, 'Expected 35 structured issue entries'
p0 = []
for issue_id, block in zip(blocks[::2], blocks[1::2]):
    for field in ['Screen', 'Severity / priority', 'Category', 'Problem', 'Why it matters',
                  'Evidence', 'Root cause', 'Recommended fix', 'Migration implication / affected component']:
        assert f'**{field}:**' in block, (issue_id, field)
    shots = re.findall(r'screenshots/[^`\s;,]+\.(?:png|jpg|jpeg)', block)
    assert shots, (issue_id, 'No cited screenshot')
    for shot in shots:
        assert (OUT / shot).is_file(), (issue_id, shot)
    if re.search(r'\*\*Severity / priority:\*\*[^\n]+/ P0', block):
        p0.append(issue_id)
assert len(p0) == 9, p0
spec = (OUT / 'NEXTJS_MIGRATION_UI_SPEC.md').read_text()
p0_table = spec.split('## P0 rules and verification')[1].split('## Requirement classification')[0]
for issue in p0:
    assert re.search(r'^\| ' + issue + r' \|', p0_table, re.M), issue
for path in OUT.glob('*.md'):
    text = path.read_text()
    assert 'pending, not visually verified' not in text, path.name
    assert '0 captures' not in text, path.name
# Check requirement alignment and non-empty prototype OR reason in every row.
requirements = json.loads((OUT / 'requirements.json').read_text())
assert len(requirements) == 60
assert len({r['id'] for r in requirements}) == len(requirements)
coverage = (OUT / 'README.md').read_text().split('## Requirements coverage')[1].split('## Deliverables')[0]
classes = {name: 0 for name in ['Presentation', 'Backend', 'Content']}
for row in requirements:
    assert row['classification'] in classes, row
    classes[row['classification']] += 1
    assert row['prototype'].strip(), row['id']
    assert '.html' in row['prototype'] or 'All five' in row['prototype'] or any(
        marker in row['prototype'] for marker in ['Not shown:', 'Not solved', 'Not measured:', 'No static']), row
    assert re.search(r'^\| ' + re.escape(row['id']) + r' \|', coverage, re.M), row['id']
    assert re.search(r'^\| ' + re.escape(row['id']) + r' \|', spec, re.M), row['id']
    assert '## ' + row['section'] in spec, (row['id'], row['section'])
assert classes == {'Presentation': 32, 'Backend': 14, 'Content': 14}, classes
# Every exact source path named in the coding-agent specification exists.
for path in set(re.findall(r'app/[\w/.-]+\.py', spec)):
    assert (ROOT / path).is_file(), path
families = spec.split('## Per-screen replacement')[1].split('## Component rulings')[0]
assert len(re.findall(r'\(`\w+`\)', families)) == 31

class HTMLCheck(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = set()
        self.illustrative = set()
        self.nodes = []
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.nodes.append((tag, a))
        if 'id' in a:
            assert a['id'] not in self.ids, (self.path.name, 'duplicate ID', a['id'])
            self.ids.add(a['id'])
        if a.get('data-illustrative') == 'true':
            assert 'id' in a, (self.path.name, 'illustrative element without ID')
            self.illustrative.add(a['id'])
        if tag in ['link', 'script'] and (target := a.get('href') or a.get('src')):
            assert '://' not in target, (self.path.name, 'remote rendering dependency')
            assert (self.path.parent / target).is_file(), target
        assert 'style' not in a, (self.path.name, 'inline token bypass')

html = {}
for name in SCREENS:
    path = OUT / 'prototypes' / f'{name}.html'
    assert path.is_file(), name
    html[name] = HTMLCheck(path)
    nodes = html[name].nodes
    assert sum(t == 'h1' for t, a in nodes) == 1, name
    assert sum(a.get('data-component') == 'StageNav' for t, a in nodes) == 1, name
    assert any(t == 'aside' and a.get('class') == 'sidebar' for t, a in nodes), name
    assert any(t == 'select' for t, a in nodes), name
    assert 'prototype.css' in path.read_text(), name
    assert 'Evidence cut-off 6 Oct 2026' in path.read_text(), name
    for tag, attrs in nodes:
        for key in ['aria-controls']:
            if key in attrs:
                assert attrs[key] in html[name].ids, (name, attrs[key])
assert sum(a.get('class') == 'queue-item' for t, a in html['review-queue'].nodes) == 6
assert sum(a.get('data-component') == 'FindingDetail' for t, a in html['review-queue'].nodes) == 6
assert sum(a.get('class') == 'disclosure-row' for t, a in html['conclusions'].nodes) == 32
assert sum(a.get('data-component') == 'RequestRow' for t, a in html['rfi'].nodes) >= 20
assert {'board-view', 'detail-view'} <= html['report'].ids
assert 'scope-panel' in html['questionnaire'].ids
for domain in ['organizational', 'people', 'physical', 'technological']:
    assert f'report-{domain}' in html['report'].ids
illustrations = json.loads((OUT / 'prototypes/illustrative-content.json').read_text())
assert len({r['id'] for r in illustrations}) == len(illustrations)
manifest = {(r['screen'].removesuffix('.html'), r['id']) for r in illustrations}
actual = {(name, id) for name, parser in html.items() for id in parser.illustrative}
assert actual == manifest, (actual - manifest, manifest - actual)
prototype_readme = (OUT / 'prototypes/README.md').read_text()
for item in illustrations:
    assert item['id'] in prototype_readme, item['id']
    assert item['classification'] in ['Backend', 'Content'], item
source = json.loads((OUT / 'prototypes/source-data.json').read_text())
assert len(source['iso_conclusions']) == 93
assert len(source['queue']) == 6 and sum(r['state'] == 'pending' for r in source['queue']) == 3
assert len(source['rfi']) >= 20
css = (OUT / 'prototypes/prototype.css').read_text()
assert css.count('{') == css.count('}'), 'CSS brace imbalance'
tokens = dict(re.findall(r'(--[\w-]+):([^;}]+)', css))
for value in re.findall(r'font-size:([^;}]+)', css):
    match = re.fullmatch(r'var\((--[\w-]+)\)', value)
    assert match, ('Non-token font size', value)
    number = float(tokens[match[1]].removesuffix('px'))
    assert number >= 14 or match[1] == '--t-meta', ('Content role below 14px', match[1])
assert 'font-size:var(--t-meta)' in css
assert len(re.findall(r'font-size:var\(--t-meta\)', css)) == 1, 'Metadata exception leaked'
for font in re.findall(r"url\('([^']+)'\)", css):
    assert (OUT / 'prototypes' / font).is_file(), font
contrast = json.loads((OUT / 'target-contrast.json').read_text())
assert len(contrast['rows']) == 144
assert all(r['ratio'] >= 4.5 for r in contrast['rows'])
assert len(contrast['accents']) == 8
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], cwd=ROOT, text=True)
changed = []
for line in status.splitlines():
    path = line[3:]
    assert path.startswith('docs/ui-audit/') or path == HANDOFF, line
    changed.append(ROOT / path)
for path in changed:
    if not path.is_file() or path.suffix in ['.png', '.jpg', '.jpeg', '.woff2']:
        continue
    text = path.read_text()
    assert chr(0x2014) not in text, path
    if path.suffix == '.py':
        ast.parse(text)
    if path.suffix == '.md':
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'):
                continue
            assert (path.parent / target.split('#')[0]).exists(), (path.name, target)
print(f'PASS: nine documents; 35 reconciled issues; {len(p0)} P0 rules; '
      f'60 requirements {classes}; 31 page families; five prototypes; '
      f'32 conclusions / 40 RFI / six queue items; {len(illustrations)} illustrative IDs; '
      '144 AA colour pairs; screenshot citations, local fonts and allowed scope verified.')
