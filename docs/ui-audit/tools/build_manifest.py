"""Build a read-only capture manifest from the handoff and literal fixture states."""
import ast
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/ui-audit'
A = 'd491ee73-0925-43bd-8cb2-3b5fff2cc8ac'
I = '506d1f04-9c19-44e4-9fdd-fa286f2b4eb6'
N = '195477f0-a4d4-4821-b48e-71d268996232'
P = '817a8d5b-37b9-430b-a6d9-3df4ea53f1a1'
with sqlite3.connect(f'file:{ROOT}/data/demo/ui-audit-demo.db?mode=ro', uri=True) as db:
    C = db.execute('select id from clients order by id limit 1').fetchone()[0]
    E = db.execute('select engagement_id from assessments where id=?', (A,)).fetchone()[0]
    V = db.execute('select id from evidence order by id limit 1').fetchone()[0]
rows = []
def add(name, path, task, density='Medium', components='Header, contextual navigation, structured content', interaction='Load; wait for fonts and HTMX read-only loads; scroll to bottom', group='live'):
    rows.append(dict(name=name, path=path, task=task, density=density, components=components, interaction=interaction, group=group))
for name,path,task in [
 ('home','/','Identify active work and next assessment'),('clients','/clients','Find a client'),('client',f'/clients/{C}','Review client engagements'),('engagements','/engagements','Find and filter engagements'),('portfolio-review','/review','Find pending decisions across engagements'),('reports','/reports','Find issued reports'),('new-engagement','/engagements/new','Configure client engagement'),('engagement',f'/engagements/{E}','Choose assessment and engagement work'),('new-assessment',f'/engagements/{E}/assessments/new','Configure framework assessment'),('remediation',f'/engagements/{E}/remediation','Track findings, owners and actions'),('integrated-reports',f'/engagements/{E}/integrated-reports','Read framework report coverage'),('requests',f'/engagements/{E}/requests','Manage client evidence upload links'),('aws-evidence',f'/engagements/{E}/aws-evidence','Configure read-only evidence connection'),('purge',f'/engagements/{E}/purge','Understand retention and deletion eligibility'),('settings','/settings','Configure firm branding and preferences'),('evidence-global','/evidence','Find evidence across clients'),('evidence-engagement',f'/engagements/{E}/evidence','Find engagement evidence'),('evidence-assessment',f'/assessments/{A}/evidence','Inspect assessment evidence and exclusions'),('evidence-record',f'/evidence/{V}','Read evidence version and content'),('evidence-reuse',f'/assessments/{A}/evidence-reuse','Choose existing evidence to reuse'),('desk-review',f'/assessments/{A}/desk-review','Inspect stored pre-fill and missing evidence'),('overview',f'/assessments/{A}','Understand assessment next step'),('scope',f'/assessments/{A}?tab=scope','Check assessment boundaries'),('questionnaire',f'/assessments/{A}?tab=questionnaire','Answer and verify control questions'),('report',f'/assessments/{A}?tab=report','Read released results'),('report-summary',f'/assessments/{A}/report-summary','Read report decision summary'),('review-queue',f'/assessments/{I}/review-queue','Select a pending control for decision'),('conclusions',f'/assessments/{A}/conclusions','Review approved conclusions and citations'),('findings',f'/assessments/{A}/findings','Inspect gaps and remediation owners'),('workpaper',f'/assessments/{A}/workpaper','Trace audit decisions to evidence'),('snapshots',f'/assessments/{A}/snapshots','Inspect issued report versions'),('comparison',f'/assessments/{A}/compare/{P}','Compare matched controls across periods'),('narrative',f'/assessments/{A}/narrative','Inspect stored executive narrative'),('board-inputs',f'/assessments/{A}/board-inputs','Supply board-level reporting context'),('soa',f'/assessments/{A}/soa','Inspect applicability and justification'),('rfi-items',f'/assessments/{A}/rfi?tab=items','Prepare evidence request items'),('rfi-versions',f'/assessments/{A}/rfi?tab=versions','Inspect RFI version history'),('rfi-links',f'/assessments/{A}/rfi?tab=links','Inspect client request links')]:
    high = name in {'questionnaire','conclusions','workpaper','report','comparison','soa','evidence-assessment','rfi-items'}
    add(name,path,task,'High' if high else 'Medium')
add('report-iso',f'/assessments/{A}?tab=report&framework=iso27001','Read ISO released report',group='additional-live')
add('report-summary-iso',f'/assessments/{A}/report-summary?framework=iso27001','Read ISO report decision summary',group='additional-live')
add('nist-overview',f'/assessments/{N}','Inspect early assessment next step',group='additional-live')
add('nist-questionnaire',f'/assessments/{N}?tab=questionnaire','Inspect partly answered questionnaire',group='additional-live')
add('interim-conclusions',f'/assessments/{I}/conclusions','Inspect pending and approved decisions',interaction='Load; expand pending row; inspect evidence; do not approve or reject',group='additional-live')
# Static parsing avoids importing app modules or touching application state.
fixtures = {}
for f in sorted((ROOT/'app/routers').glob('design*.py')):
    tree = ast.parse(f.read_text())
    for node in tree.body:
        if not isinstance(node,(ast.Assign,ast.AnnAssign)): continue
        targets = node.targets if isinstance(node,ast.Assign) else [node.target]
        if not any(isinstance(t,ast.Name) and t.id in {'SCREEN_STATES','S5_PREVIEW_STATES','STATE_HEADS','S5_LIVE_PREVIEWS','NARRATIVE_STATES','BOARD_INPUT_STATES'} for t in targets): continue
        try: value = ast.literal_eval(node.value)
        except (ValueError,TypeError): continue
        key = targets[0].id
        if key == 'NARRATIVE_STATES': fixtures['b5-narrative']=value
        elif key == 'BOARD_INPUT_STATES': fixtures['b5-board-inputs']=value
        elif isinstance(value,dict):
            for screen,states in value.items():
                if isinstance(states,dict): states=tuple(states)
                if key == 'S5_LIVE_PREVIEWS': states=states[1]
                if isinstance(states,(tuple,list)) and all(isinstance(x,str) for x in states): fixtures[screen]=states
fixtures.update({'login':('default','error','loading'),'aws_evidence':('ready','pulling','result','error','notconfigured'),'evidence_reuse':('default','error'),'workpaper_entry':('default','legacy','excluded'),'b6-magic_upload':('default','uploading','done','error'),'b6-magic_invalid':('expired','revoked','unknown'),'b7-link-expired':('expired',),'b5-report-loading':('loading',),'b6-report_snapshots':('default',),'b6-soa':('default',),'b6-comparison':('default',)})
for screen,states in sorted(fixtures.items()):
    for state in states:
        add(f'{screen}-{state}',f'/design/pages/{screen}?state={state}&assessment_id={A}' + (f'&assessment={A}' if screen=='evidence_reuse' else ''),f'Inspect {screen} {state} state',interaction='Load fixture; scroll all content; no submit or AI action',group='fixture')
add('gallery','/design','Inspect shared component gallery',group='gallery')
# Separate interaction captures on real data plus fixture edit/conflict states.
for name,base,instruction in [
 ('questionnaire-open','questionnaire','Open first section; expand View document evidence and notes; scroll questions; do not change radio buttons'),
 ('conclusions-expanded','conclusions','Expand first conclusion row and evidence details; no decision action'),
 ('conclusions-edit','interim-conclusions','Open Edit for a pending conclusion; do not save or draft AI action'),
 ('review-selected','review-queue','Select pending queue item; scroll reading and evidence panes; do not decide'),
 ('evidence-cited','conclusions','Follow first citation link to its exact evidence URL including passage parameters'),
 ('confirm-dialog','purge','Open confirmation only if enabled; capture dialog; cancel without submitting')]:
    base_row=next(r for r in rows if r['name']==base)
    add(name,base_row['path'],base_row['task'],interaction=instruction,group='interaction')
captures=[]
for row in rows:
    for width in (1440,1280):
        captures.append({**row,'width':width,'height':1000,'theme':'light','filename':f'screenshots/{row["name"]}-{width}.png'})
for name in ('requests','evidence-assessment','questionnaire','review-queue','report'):
    row=next(r for r in rows if r['name']==name)
    captures.append({**row,'width':1440,'height':1000,'theme':'dark','filename':f'screenshots/{name}-dark-1440.png'})
for row in rows:
    if row['name'].startswith('b6-magic_upload-'):
        captures.append({**row,'width':390,'height':1000,'theme':'light','filename':f'screenshots/{row["name"]}-390.png'})
(OUT/'capture-manifest.json').write_text(json.dumps(captures,indent=2)+'\n')
(OUT/'screen-manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'{len(rows)} route/state entries, {len(captures)} captures, {len(fixtures)} fixture names')
