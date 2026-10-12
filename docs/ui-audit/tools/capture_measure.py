"""Complete deferred captures and actual DOM measurements on an unrestricted host.

Run from repo root: .venv/bin/python docs/ui-audit/tools/capture_measure.py
Captures use the existing harness URL/theme helpers and Playwright.
All non-GET browser requests are aborted, including saves and AI actions.
"""
import argparse
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/ui-audit'
spec=importlib.util.spec_from_file_location('audit_harness',ROOT/'design/harness/screenshot.py')
harness=importlib.util.module_from_spec(spec); spec.loader.exec_module(harness)
MEASURE=r'''() => {
 const root=document.querySelector('main') || document.body;
 const box=root.getBoundingClientRect();
 const sidebar=document.querySelector('.side')?.getBoundingClientRect().width || 0;
 const counts={}, samples=[], pairs={};
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
 let n;
 while(n=walker.nextNode()) {
  const e=n.parentElement, t=n.textContent.trim();
  if(!t || ['SCRIPT','STYLE'].includes(e.tagName)) continue;
  const range=document.createRange(); range.selectNodeContents(n);
  if(!range.getClientRects().length || e.closest('[hidden]')) continue;
  const s=getComputedStyle(e); if(s.visibility==='hidden' || s.display==='none') continue;
  const size=s.fontSize; counts[size]=(counts[size]||0)+1;
  let p=e, layers=[];
  while(p){const c=getComputedStyle(p);layers.push({tag:p.tagName,cls:p.className,bg:c.backgroundColor,image:c.backgroundImage,opacity:c.opacity});p=p.parentElement;}
  const key=JSON.stringify([s.color,layers.map(x=>[x.bg,x.image,x.opacity])]);
  if(!pairs[key])pairs[key]={foreground:s.color,layers,count:0,example:t.slice(0,160)};
  pairs[key].count++;
  samples.push({text:t.slice(0,250),characters:t.length,size,lineHeight:s.lineHeight,width:e.getBoundingClientRect().width,selector:e.tagName.toLowerCase()+(e.className?'.'+String(e.className).trim().split(/\s+/).join('.'):'')});
 }
 const candidates=Array.from(root.querySelectorAll('p,blockquote,li,[class*="rationale"],[class*="reason"]')).filter(e=>e.getClientRects().length && e.innerText.trim().length>40);
 const longest=candidates.sort((a,b)=>b.innerText.length-a.innerText.length)[0];
 let prose=null;
 if(longest) {
  // Count actual character rects by rendered y coordinate, excluding whitespace-only runs.
  const lines={};const w=document.createTreeWalker(longest,NodeFilter.SHOW_TEXT);let textNode;
  while(textNode=w.nextNode())for(let i=0;i<textNode.length;i++){
   const r=document.createRange();r.setStart(textNode,i);r.setEnd(textNode,i+1);const b=r.getBoundingClientRect();
   if(b.width>0 && b.height>0){const y=Math.round(b.y);lines[y]=(lines[y]||0)+1;}
  }
  prose={text:longest.innerText,blockCharacters:longest.innerText.length,width:longest.getBoundingClientRect().width,maxCharactersPerRenderedLine:Math.max(0,...Object.values(lines)),fontSize:getComputedStyle(longest).fontSize};
 }
 return {viewport:innerWidth,contentWidth:box.width,sidebarWidth:sidebar,unusedOutsideContent:innerWidth-sidebar-box.width,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,fontSizeTextNodeCounts:counts,below14:samples.filter(x=>parseFloat(x.size)<14),longestBodyBlock:prose,foregroundBackgroundPairs:Object.values(pairs),theme:document.documentElement.dataset.theme,height:document.documentElement.scrollHeight};
}'''
def interact(page,name):
    # Only read-only expand/select/edit presentation. Never change answer radios.
    if name=='questionnaire-open':
        page.locator('[data-section]').first.click()
        page.locator('#section-content [data-question-card]').first.wait_for()
        for details in page.locator('#section-content details').all(): details.evaluate('(e)=>e.open=true')
    elif name=='conclusions-expanded':
        page.locator('.rv-toggle').first.click()
    elif name=='review-selected':
        page.locator('[data-queue-select]').first.click()
        # Seven .rq-body panes exist; only the selected item's pane is visible.
        page.locator('.rq-body:visible').first.evaluate('(e)=>e.scrollTop=e.scrollHeight')
    elif name=='conclusions-edit':
        # Runs on the interim assessment: approved rows have no edit control, so open rows until one shows it.
        edit=page.locator('[data-conclusion-edit="open"]:visible')
        for toggle in page.locator('.rv-toggle').all():
            if edit.count(): break
            toggle.click()
        if not edit.count(): raise RuntimeError('No pending row with an edit control')
        edit.first.click()
    elif name=='evidence-cited':
        # Runs on the interim assessment, whose pending rows carry cited-span links.
        link=page.locator('a[href*="/evidence-versions/"]:visible')
        for toggle in page.locator('.rv-toggle').all():
            if link.count(): break
            toggle.click()
        if not link.count(): raise RuntimeError('No visible citation link')
        link.first.click(); page.wait_for_load_state('networkidle')
    elif name=='confirm-dialog':
        # The manifest points this capture at the b7-modals purge fixture: the live trigger posts, and posts are blocked.
        pass
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--only',help='Capture name filter');ap.add_argument('--measure-only',action='store_true');args=ap.parse_args()
    manifest=json.loads((OUT/'capture-manifest.json').read_text());results=[];errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        for item in manifest:
            if args.only and args.only not in item['name']: continue
            context=browser.new_context(viewport={'width':item['width'],'height':item['height']},device_scale_factor=1)
            context.route('**/*',lambda route: route.continue_() if route.request.method in ('GET','HEAD') else route.abort())
            context.add_init_script(f"localStorage.setItem('theme', {json.dumps(item['theme'])});")
            page=context.new_page();page.emulate_media(reduced_motion='reduce')
            try:
                response=page.goto(harness._source_url('http://127.0.0.1:8011'+item['path'],'http://127.0.0.1:8011',None,item['theme']),wait_until='networkidle')
                if response.status != 200: raise RuntimeError(f'HTTP {response.status}')
                page.evaluate('document.fonts.ready');page.wait_for_timeout(200)
                if item['group']=='interaction':interact(page,item['name'])
                data=page.evaluate(MEASURE);results.append({**item,**data,'actualURL':page.url})
                if not args.measure_only:
                    # The harness functions supply URL/theme policy; a shared browser retains
                    # read-only request interception and handles view interactions safely.
                    page.add_style_tag(content='*,:before,:after{animation:none!important;transition:none!important;caret-color:transparent!important}')
                    path=OUT/item['filename'];path.parent.mkdir(exist_ok=True)
                    if data['height']>6000:path=path.with_suffix('.jpg');page.screenshot(path=str(path),full_page=True,type='jpeg',quality=85)
                    else:page.screenshot(path=str(path),full_page=True)
                    results[-1]['actualFilename']=str(path.relative_to(OUT))
            except Exception as exc:errors.append({'capture':item['filename'],'error':str(exc)})
            finally:context.close()
            (OUT/'rendered-measurements.json').write_text(json.dumps({'results':results,'errors':errors},indent=2)+'\n')
        browser.close()
    print(f'{len(results)} measured, {len(errors)} errors')
if __name__=='__main__':main()
