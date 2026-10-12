"""Verify documentary coverage, source evidence references and allowed change scope."""
import ast
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/ui-audit'
required=['README.md','ARCHITECTURE.md','SCREEN_INVENTORY.md','UI_ISSUES.md','ROOT_CAUSES.md','MEASUREMENTS.md','CAPTURE_REQUESTS.md','STATUS_INVENTORY.md','CONTRAST_APPENDIX.md']
for name in required: assert (OUT/name).is_file(),name
for name in ['DESIGN_SYSTEM.md','PAGE_ARCHETYPES.md','NEXTJS_MIGRATION_UI_SPEC.md','COMPONENT_INVENTORY.md']:assert not (OUT/name).exists(),name
screens=json.loads((OUT/'screen-manifest.json').read_text())
captures=json.loads((OUT/'capture-manifest.json').read_text())
assert len({r['name'] for r in screens})==len(screens)
assert sum(r['group']=='live' for r in screens)==38
fixture_names={r['path'].split('/design/pages/')[1].split('?')[0] for r in screens if r['group']=='fixture'}
assert len(fixture_names)==44
for row in screens:
 for width in (1440,1280):assert any(c['name']==row['name'] and c['width']==width and c['theme']=='light' for c in captures),row['name']
assert sum(c['theme']=='dark' for c in captures)==5
assert sum(c['width']==390 for c in captures)==4
assert all(c['name'].startswith('b6-magic_upload-') for c in captures if c['width']==390)
register=(OUT/'UI_ISSUES.md').read_text()
issues=re.findall(r'^## (UI-\d+):',register,re.M)
assert len(issues)==len(set(issues))==24
expected={c['filename'] for c in captures}
for ref in re.findall(r'screenshots/[A-Za-z0-9_-]+\.(?:png|jpg)',register):assert ref in expected,ref
for block in re.split(r'^## UI-\d+:',register,flags=re.M)[1:]:
 for field in ['Screen','Severity / priority','Category','Problem','Why it matters','Evidence','Root cause','Recommended fix','Migration implication / affected component']:assert f'**{field}:**' in block,field
 assert re.search(r'app/(?:templates|static|routers)/',block) or 'design/baselines/' in block
for file in OUT.rglob('*'):
 if not file.is_file():continue
 assert chr(0x2014) not in file.read_text(),str(file)
 if file.suffix=='.py':ast.parse(file.read_text())
 if file.suffix=='.md':
  for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
   if '://' in target or target.startswith('#'):continue
   assert (file.parent/target.split('#')[0]).exists(),(file.name,target)
contrast=json.loads((OUT/'contrast-data.json').read_text())
assert len(contrast['rows'])==5198
assert all('worst_background' in r and 'best_background' in r for r in contrast['rows'])
http=json.loads((OUT/'http-observations.json').read_text())
assert len(http)==213
assert all(next(h for h in http if h['name']==r['name'])['status']=='200' for r in screens if r['group']=='live')
failed=[r['name'] for r in http if r['status']!='200']
assert len(failed)==5,failed
status=subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=ROOT,text=True)
for line in status.splitlines():
 path=line[3:]
 assert path.startswith('docs/ui-audit/') or path=='tasks/handoffs/2026-10-12-ui-audit.md',line
images=list((OUT/'screenshots').glob('*'))
assert not images,'This fallback run must not claim screenshots'
print(f'PASS: {len(screens)} entries; {len(captures)} capture requests; {len(issues)} issues; {len(contrast["rows"])} contrast rows; {len(http)} HTTP inspections; {len(failed)} disclosed fixture failures; allowed scope only')
