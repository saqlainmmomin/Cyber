"""Run from the repo root. First: python3.13 scripts/ucf/authoring/dump_sources.py (writes json to $UCF_SRC_DIR, default /tmp/ucf_src).
Usage: brief.py OUTDIR ORIGIN[,ORIGIN] DOMAIN[,DOMAIN]...  -> writes OUTDIR/brief_<DOMAIN>.md"""
import csv,json,sys,glob,os
D='docs/ucf/drafts/'; import os
SRC=os.environ.get('UCF_SRC_DIR','/tmp/ucf_src')+'/'
out,origins,doms=sys.argv[1],sys.argv[2].split(','),sys.argv[3].split(',')
rd=lambda p:[r for f in sorted(glob.glob(D+p)) for r in csv.DictReader(open(f))]
controls=[c for c in rd('controls_*.csv') if c['origin'] in origins and c['domain'] in doms]
atoms={a['atom_id']:a for a in rd('atoms_*.csv')}
maps=rd('mappings_*.csv')
rec={}
for fw,f in [('iso27001','iso27001'),('nist_csf','nist_csf'),('dpdpa','dpdpa')]:
    for r in json.load(open(SRC+f+'_records.json')): rec[r['id']]=r
ev=[]
for f in ['iso27001','nist_csf']:
    ev+=json.load(open(SRC+f+'_evidence.json'))
os.makedirs(out,exist_ok=True)
for dom in doms:
    L=[f'# Brief: domain {dom}\n']
    for c in [c for c in controls if c['domain']==dom]:
        L.append(f"## {c['id']} {c['title']}\n- domain {dom}; theme {c['iso_theme'] or '-'}; owner {c['owner_role']}; importance {c['importance']}; origin {c['origin']}\n- goal: {c['goal']}\n- note: {c['note']}")
        rows=[m for m in maps if m['unified_control_id']==c['id']]
        recs=[]
        L.append('- source atoms mapped (source framework, atom, ref, match/coverage, paraphrase):')
        for m in rows:
            a=atoms.get(m['atom_id'],{})
            L.append(f"  - [{m['source_framework']}] {m['atom_id']} ({m['source_ref']}) {m['match_type']}/{m['coverage']}{' REMAINDER of '+m['remainder_of'] if m['remainder_of'] else ''}: {a.get('paraphrase','')}")
            if m['record_id'] not in recs: recs.append(m['record_id'])
        L.append('- signed test criteria of the source records (seed for the test field):')
        for rid in recs:
            r=rec.get(rid)
            if r:
                for t in r['criteria']: L.append(f"  - {rid}: ({t['kind']}) {t['stmt']} | evidence: {t['hint']}")
        if any(r.get('question') for rid in recs for r in [rec.get(rid,{})]):
            L.append('- curated question and guidance of source records (reuse if good):')
            for rid in recs:
                r=rec.get(rid)
                if r and r['question'] and r['id'].split('.')[0] not in('ISO','NIST'):
                    L.append(f"  - {rid}: Q: {r['question']} | guidance: {r['guidance'][:400]}")
        evs=[e for e in ev if any(m in recs for m in e['maps_to'])]
        if evs:
            L.append('- existing evidence requests (seed for expected_evidence; paraphrase, do not name frameworks):')
            for e in evs: L.append(f"  - {e['label']} ({'required' if e['required'] else 'recommended'}): {e['reason']}")
        L.append('')
    open(f'{out}/brief_{dom}.md','w').write('\n'.join(L))
    print(dom,len([c for c in controls if c['domain']==dom]),'controls')
