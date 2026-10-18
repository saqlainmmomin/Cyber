// Smoke test for the re-key review page (jsdom). Run from the repo root:
//   JSDOM_PATH=/path/to/node_modules/jsdom node scripts/ucf/authoring/smoke_rekey_review_page.js
// Expected counts come from the data files, so the test follows the data.
// One known jsdom artifact: 'URL.revokeObjectURL is not a function' after the export test. Ignore it.
const { JSDOM } = require(process.env.JSDOM_PATH || 'jsdom');
const fs = require('fs');
const html = fs.readFileSync(process.env.REVIEW_HTML || 'tasks/2026-10-14-ucf-rekey-review.html', 'utf8');
const csvRows = f => fs.readFileSync(f, 'utf8').trim().split('\n').slice(1);
const proposed = csvRows('docs/ucf/drafts/criteria_map.csv').filter(l => /,"proposed",/.test(l));
const N = { crit: proposed.length, records: new Set(proposed.map(l => l.split('","')[1])).size,
  scope: csvRows('docs/ucf/drafts/scope_proposals.csv').length };
const KEY = 'ucf-rekey-review-1.0.0';
const errs = [];
const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'http://localhost/review.html', pretendToBeVisual: true,
  beforeParse(w) { w.addEventListener('error', e => errs.push(String(e.error || e.message))); w.URL.createObjectURL = () => 'blob:x'; w.alert = m => errs.push('alert ' + m); } });
const w = dom.window, d = w.document;
const assert = (c, m) => { if (!c) { console.log('FAIL', m); process.exitCode = 1 } else console.log('ok  ', m) };
const fire = (el, ev) => el.dispatchEvent(new w.Event(ev));
assert(errs.length === 0, 'no script errors on load ' + errs.join('|'));
assert(d.querySelectorAll('#tabs button').length === 3, '3 tabs');
assert(new RegExp(' of ' + (N.crit + N.scope + 2) + ' items').test(d.getElementById('prog').textContent), 'progress counts ' + (N.crit + N.scope + 2) + ' items');

// criteria
[...d.querySelectorAll('#tabs button')].find(b => b.dataset.tab === 'criteria').click();
const cards = () => d.querySelectorAll('#crlist article');
let firstId = null, secondId = null, other = null, nDp = 0;
if (N.crit === 0) {
  assert(cards().length === 0 && /Nothing undecided/.test(d.getElementById('crlist').textContent), 'no criteria left: criteria tab says so');
} else {
assert(cards().length === N.crit, N.crit + ' criterion cards match the proposed rows');
assert(d.querySelectorAll('#crlist .recblock').length === N.records, N.records + ' record groups');
assert([...cards()].every(a => { const r = a.querySelector('input[type=radio]:checked'); return r && a.querySelector('.tag') && r.closest('label').contains(a.querySelector('.tag')); }),
  'every card has the proposed control pre-selected');
assert([...cards()].every(a => a.querySelectorAll('input[type=radio]').length >= 3), 'every card offers 2+ controls plus the flag');
// choose another control on the first card
const first = cards()[0]; firstId = first.id.slice(2);
other = [...first.querySelectorAll('input[type=radio]')].find(r => !r.checked && r.value !== 'FLAG');
other.checked = true; fire(other, 'change');
let st = JSON.parse(w.localStorage.getItem(KEY));
assert(st['t:' + firstId].s === 'change' && st['t:' + firstId].c === other.value, 'choosing another control saves a change: ' + other.value);
assert(first.classList.contains('s-change'), 'change marks the card');
// flag the second card with a note
const second = cards()[1]; secondId = second.id.slice(2);
const flag = second.querySelector('input[value=FLAG]'); flag.checked = true; fire(flag, 'change');
const ta = second.querySelector('textarea'); ta.value = 'tests both'; fire(ta, 'input');
// accept proposed on the third
const third = cards()[2], thirdId = third.id.slice(2);
third.querySelector('button.approve').click();
st = JSON.parse(w.localStorage.getItem(KEY));
assert(st['t:' + secondId].s === 'flag' && st['t:' + secondId].n === 'tests both', 'flag and note saved');
assert(st['t:' + thirdId].s === 'accept', 'accept proposed saved');
assert(cards().length === N.crit - 3, 'undecided list drops the three decided cards');
// hard filter
const hard = d.getElementById('cHard'); hard.checked = true; fire(hard, 'change');
const nHard = cards().length;
assert(nHard > 0 && nHard < N.crit, 'close-call filter narrows the list to ' + nHard);
hard.checked = false; fire(hard, 'change');
// framework filter + accept all shown
const fw = d.getElementById('cFw'); fw.value = 'dpdpa'; fire(fw, 'change');
nDp = cards().length;
d.getElementById('acceptShown').click();
assert(cards().length === 0, 'accept all shown clears the DPDPA list (' + nDp + ')');
fw.value = 'all'; fire(fw, 'change');
const cs = d.getElementById('cStatus'); cs.value = 'all'; fire(cs, 'change');
assert(cards().length === N.crit, 'status All shows every card again');
// search
const q = d.getElementById('cQ'); q.value = firstId.toLowerCase(); fire(q, 'input');
assert(cards().length >= 1, 'search finds the first card');
q.value = ''; fire(q, 'input');
}

// scope
[...d.querySelectorAll('#tabs button')].find(b => b.dataset.tab === 'scope').click();
const scards = d.querySelectorAll('#p-scope .card');
assert(scards.length === N.scope + 2, N.scope + ' scope cards plus 2 decision cards');
scards[0].querySelector('button.approve').click();
scards[1].querySelector('button.change').click();
const sta = scards[1].querySelector('textarea'); sta.value = 'keep A.8.31 in'; fire(sta, 'input');
d.querySelector('[data-card="h:held"] button.approve').click();
d.querySelector('[data-card="q:four"] button.change').click();
assert(scards[0].classList.contains('s-approve') && scards[1].classList.contains('s-change'), 'scope cards marked');

// export
let blobs = []; w.Blob = function (p) { blobs.push(p[0]); };
d.getElementById('exportJson').click(); d.getElementById('exportMd').click();
const j = JSON.parse(blobs[0]);
if (N.crit) {
  assert(j.totals.change === 1 && j.totals.flag === 1 && j.totals.accept === 1 + nDp, 'json totals ' + JSON.stringify(j.totals));
  assert(j.criteria[firstId].unified_control_id === other.value, 'json carries the chosen control');
  assert(j.criteria[secondId].unified_control_id === '' && j.criteria[secondId].status === 'flag', 'json flag has no control');
}
assert(Object.values(j.scope).filter(v => v.status).length === 2 && j.held_back.status === 'keep_out' && j.four_questions.status === 'more', 'json scope and decisions');
assert((!N.crit || (/CHANGE /.test(blobs[1]) && /FLAG /.test(blobs[1]))) && /S2 four scope questions: more/.test(blobs[1]), 'markdown lists change, flag and decisions');
console.log(d.getElementById('prog').textContent);
console.log('errors:', errs);
