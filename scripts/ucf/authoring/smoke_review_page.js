// Smoke test for the review page (jsdom). Run from the repo root:
//   JSDOM_PATH=/path/to/node_modules/jsdom node scripts/ucf/authoring/smoke_review_page.js
// One known jsdom artifact: 'URL.revokeObjectURL is not a function' after the export test. Ignore it.
const { JSDOM } = require(process.env.JSDOM_PATH || 'jsdom');
const fs = require('fs');
const html = fs.readFileSync((process.env.REVIEW_HTML || 'tasks/2026-10-13-ucf-review.html'),'utf8');
const errs=[];
const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'http://localhost/review.html', pretendToBeVisual: true,
  beforeParse(w){ w.addEventListener('error',e=>errs.push(String(e.error||e.message))); w.URL.createObjectURL=()=> 'blob:x'; w.alert=m=>errs.push('alert '+m); } });
const w = dom.window, d = w.document;
const assert=(c,m)=>{ if(!c){ console.log('FAIL',m); process.exitCode=1 } else console.log('ok  ',m) };
assert(errs.length===0,'no script errors on load '+errs.join('|'));
assert(d.querySelectorAll('#p-overview table tbody tr').length===7,'overview has 7 subset rows');
assert(d.querySelectorAll('#tabs button').length===6,'6 tabs');
// decisions
const dcards=d.querySelectorAll('#p-decisions .card'); assert(dcards.length===18,"18 decision cards");
dcards[0].querySelector('button.approve').click();
assert(dcards[0].classList.contains('s-approve'),'approve marks card');
// legal / clauses
assert(d.querySelectorAll('#p-clauses .card').length===25,'25 clause cards');
assert(d.querySelectorAll('#p-legal .card').length===16,'16 legal cards');
assert(d.querySelectorAll('#p-legal .card.s-approve').length===16,'legal items default to confirmed');
assert(d.querySelectorAll('#p-decisions button.keep').length===24,'24 D11 split/keep boxes');
assert(d.querySelectorAll('#p-decisions table').length===3,'3 decision tables');
// controls
[...d.querySelectorAll('#tabs button')].find(b=>b.dataset.tab==='controls').click();
assert(d.querySelectorAll('#ctlist article').length===195,'195 control cards');
const first=d.querySelector('#ctlist article'); first.querySelector('button.change').click();
const ta=first.querySelector('textarea'); ta.value='split this'; ta.dispatchEvent(new w.Event('input'));
assert(first.classList.contains('s-change'),'change marks card');
// scope filter ISO only => 125
const sc=d.getElementById('fScope'); sc.value='iso27001'; sc.dispatchEvent(new w.Event('change'));
assert(d.querySelectorAll('#ctlist article').length===125,'iso scope shows 125');
sc.value='dpdpa'; sc.dispatchEvent(new w.Event('change'));
assert(d.querySelectorAll('#ctlist article').length===54,'dpdpa scope shows 54');
sc.value='all'; sc.dispatchEvent(new w.Event('change'));
// domain bulk approve
d.querySelector('.domhead button').click();
const st=JSON.parse(w.localStorage.getItem('ucf-review-0.0.1-draft'));
assert(Object.keys(st).filter(k=>k.startsWith('c:')&&st[k].s==='approve').length>=10,'bulk approve saved '+Object.keys(st).length);
assert(st[Object.keys(st).find(k=>st[k].s==='change')].n==='split this','note saved');
// status filter: undecided
const ss=d.getElementById('fStatus'); ss.value='change'; ss.dispatchEvent(new w.Event('change'));
assert(d.querySelectorAll('#ctlist article').length===1,'change filter shows 1');
ss.value='all'; ss.dispatchEvent(new w.Event('change'));
// search
const q=d.getElementById('fQ'); q.value='UC-CRY-01'; q.dispatchEvent(new w.Event('input'));
assert(d.querySelectorAll('#ctlist article').length===1,'search finds one');
// records
assert(d.querySelectorAll('#trbody tr').length===265,'265 trace rows');
// progress text
console.log(d.getElementById('prog').textContent);
// export md
let blobs=[]; w.Blob=function(p,o){blobs.push(p[0]);}; 
d.getElementById('exportMd').click(); d.getElementById('exportJson').click();
assert(/CHANGE UC-/.test(blobs[0]),'markdown lists the change item'); assert(JSON.parse(blobs[1]).totals.change===1,'json totals');
// card text sanity
const c=d.querySelector('#ctlist article'); console.log(c.textContent.slice(0,400));
console.log('errors:',errs);
