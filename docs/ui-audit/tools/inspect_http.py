"""Inspect only explicit GET routes. curl does not execute JS, polls or AI actions."""
import concurrent.futures
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'docs/ui-audit'
class Inspect(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.links=[]; self.loads=[]; self.forms=[]; self.tags={}; self.skip=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs); self.tags[tag]=self.tags.get(tag,0)+1
        if tag in ('script','style'): self.skip+=1
        if tag=='a' and d.get('href'): self.links.append(d['href'])
        if d.get('hx-get'): self.loads.append({'url':d['hx-get'],'trigger':d.get('hx-trigger'),'target':d.get('hx-target')})
        if tag=='form': self.forms.append({'action':d.get('action') or d.get('hx-post'),'method':d.get('method','HTMX' if d.get('hx-post') else 'GET')})
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip(): self.text.append(data.strip().replace(chr(0x2014), ' - '))
def inspect(row):
    result=subprocess.run(['curl','--silent','--show-error','--location','--max-time','20','--write-out','\n%{http_code}\n%{url_effective}','http://127.0.0.1:8011'+row['path']],capture_output=True,text=True)
    body,_,meta=result.stdout.rpartition('\n')
    html,_,status=body.rpartition('\n')
    p=Inspect(); p.feed(html)
    return dict(name=row['name'],path=row['path'],status=status,final_url=meta,curl_exit=result.returncode,error=result.stderr,tags=p.tags,links=p.links,loads=p.loads,forms=p.forms,text=p.text)
rows=json.loads((OUT/'screen-manifest.json').read_text())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(inspect,[r for r in rows if r['group']!='interaction']))
# Load questionnaire partials by GET, so curl can inspect content HTMX would request.
extra=[]
for row in results:
    if row['name'] not in ('questionnaire','nist-questionnaire'): continue
    for load in row['loads']:
        if '/questionnaire/sections' in load['url']:
            sections=inspect(dict(name=row['name']+'-sections',path=load['url'])); extra.append(sections)
            for item in sections['loads']:
                if '/questionnaire/section/' in item['url']:
                    if not any(x['path']==item['url'] for x in extra): extra.append(inspect(dict(name=row['name']+'-section-'+item['url'].rsplit('/',1)[-1],path=item['url'])))
results+=extra
(OUT/'http-observations.json').write_text(json.dumps(results,indent=2)+'\n')
print('GET inspections:',len(results)); print('non-200:',[(r['name'],r['status']) for r in results if r['status']!='200'])
