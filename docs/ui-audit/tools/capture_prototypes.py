"""Screenshot and measure the static prototypes on an unrestricted host.

Run from repo root: .venv/bin/python docs/ui-audit/tools/capture_prototypes.py
Writes docs/ui-audit/prototypes/screenshots/<name>-<width>.png and
docs/ui-audit/prototypes/measurements.json. Pass --grey <dir> to also write
greyscale copies for the hierarchy check.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3]
PROTO=ROOT/'docs/ui-audit/prototypes'
MEASURE=r'''() => {
 const counts={}, below=[];
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 let n;
 while(n=walker.nextNode()) {
  const e=n.parentElement, t=n.textContent.trim();
  if(!t || ['SCRIPT','STYLE'].includes(e.tagName)) continue;
  const range=document.createRange(); range.selectNodeContents(n);
  if(!range.getClientRects().length) continue;
  const s=getComputedStyle(e); if(s.visibility==='hidden') continue;
  counts[s.fontSize]=(counts[s.fontSize]||0)+1;
  if(parseFloat(s.fontSize)<14) below.push({text:t.slice(0,60),size:s.fontSize,cls:String(e.className).slice(0,60),tag:e.tagName});
 }
 // Longest rendered line, in characters, of each prose block over 120 characters.
 const prose=[];
 for(const el of document.querySelectorAll('p,li,blockquote,td,dd')) {
  if(!el.getClientRects().length || el.innerText.trim().length<120 || el.querySelector('p,li,table')) continue;
  const lines={}; const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT); let tn;
  while(tn=w.nextNode()) for(let i=0;i<tn.length;i++){
   const r=document.createRange(); r.setStart(tn,i); r.setEnd(tn,i+1); const b=r.getBoundingClientRect();
   if(b.width>0&&b.height>0){const y=Math.round(b.y/4); lines[y]=(lines[y]||0)+1;}
  }
  prose.push({chars:Math.max(0,...Object.values(lines)),size:getComputedStyle(el).fontSize,width:Math.round(el.getBoundingClientRect().width),text:el.innerText.trim().slice(0,50)});
 }
 prose.sort((a,b)=>b.chars-a.chars);
 const navs=[...document.querySelectorAll('nav,[role=tablist]')].filter(e=>e.getClientRects().length).map(e=>{const r=e.getBoundingClientRect();return {label:e.getAttribute('aria-label')||String(e.className).slice(0,40),top:Math.round(r.top+scrollY),left:Math.round(r.left),width:Math.round(r.width),height:Math.round(r.height)};});
 return {viewport:innerWidth,height:document.documentElement.scrollHeight,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,fontSizeTextNodeCounts:counts,below14:below,longestProseLines:prose.slice(0,5),navigation:navs,illustrative:document.querySelectorAll('[data-illustrative]').length};
}'''
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--grey');args=ap.parse_args()
    out=PROTO/'screenshots';out.mkdir(exist_ok=True);results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        # (file, url suffix, screenshot stem): the suffix selects a state such as the hidden sidebar.
        targets=[(h,'',h.stem) for h in sorted(PROTO.glob('*.html'))]+[(PROTO/'questionnaire.html','#wide','questionnaire-wide'),(PROTO/'review-queue.html','#wide','review-queue-wide'),(PROTO/'report.html','#detail','report-detail')]
        for html,suffix,stem in targets:
            for width in (1440,1280):
                page=browser.new_page(viewport={'width':width,'height':1000},device_scale_factor=1)
                errors=[];page.on('requestfailed',lambda r:errors.append(r.url))
                page.goto(html.as_uri()+suffix,wait_until='networkidle');page.evaluate('document.fonts.ready');page.wait_for_timeout(300)
                data=page.evaluate(MEASURE)
                shot=out/f'{stem}-{width}.png';page.screenshot(path=str(shot),full_page=True)
                if args.grey:
                    page.add_style_tag(content='html{filter:grayscale(1)!important}')
                    Path(args.grey).mkdir(parents=True,exist_ok=True);page.screenshot(path=str(Path(args.grey)/f'{stem}-{width}-grey.png'),full_page=True)
                results.append({'screen':stem,**data,'failedRequests':errors,'screenshot':str(shot.relative_to(PROTO))});page.close()
        browser.close()
    (PROTO/'measurements.json').write_text(json.dumps(results,indent=1)+'\n')
    for r in results:
        print(r['screen'],r['viewport'],'h',r['height'],'overflow',r['horizontalOverflow'],'below14',len(r['below14']),'longest',[p['chars'] for p in r['longestProseLines'][:3]],'failed',len(r['failedRequests']))
if __name__=='__main__':main()
