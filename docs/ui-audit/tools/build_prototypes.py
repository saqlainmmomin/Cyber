"""Build the static prototypes' shared shell and the two hand-designed screens.

Run from repo root: python3 docs/ui-audit/tools/build_prototypes.py
Writes all six screens from scratch. Content comes from the JSON files beside them
(findings, conclusions, rfi, report), which hold the Veldhara demo data and the illustrative text.
"""
import html
import json
import re
from pathlib import Path

PROTO = Path(__file__).resolve().parents[1] / 'prototypes'
APP = 'http://127.0.0.1:8011/assessments/d491ee73-0925-43bd-8cb2-3b5fff2cc8ac'
e = html.escape

CHECK = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 6.5l2.5 2.5 4.5-5.5"/></svg>'
PANEL = '<svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.25" y="3" width="13.5" height="12" rx="2.5"/><path d="M6.75 3v12"/></svg>'
CHEVRON = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>'

# stage -> (label, href, [(section label, href, count)])
STAGES = [
    ('overview', 'Overview', 'questionnaire.html#overview', []),
    ('scope', 'Scope', 'scope-applicability.html', [('Boundaries', 'scope-applicability.html#boundaries', ''), ('Applicability', 'scope-applicability.html', '')]),
    ('evidence', 'Evidence', 'rfi.html', [('Documents', APP + '/evidence', ''), ('Requests', 'rfi.html', ''), ('Client links', 'rfi.html#links', '')]),
    ('questionnaire', 'Questionnaire', 'questionnaire.html', []),
    ('review', 'Review', 'review-queue.html', [('Queue', 'review-queue.html', '3'), ('Conclusions', 'conclusions.html', ''), ('Findings', APP + '/findings', ''), ('Workpaper', APP + '/workpaper', '')]),
    ('report', 'Report', 'report.html', []),
]

SCRIPT = """<script>
(function(){var r=document.documentElement,b=document.getElementById('nav-toggle'),K='ca-proto-nav';
function set(h){r.dataset.nav=h?'hidden':'shown';b.setAttribute('aria-expanded',String(!h));b.setAttribute('aria-label',h?'Show navigation':'Hide navigation');}
var h=location.hash==='#wide';try{h=h||localStorage.getItem(K)==='hidden';}catch(x){}
set(h);b.addEventListener('click',function(){var n=r.dataset.nav!=='hidden';set(n);try{localStorage.setItem(K,n?'hidden':'shown');}catch(x){}});})();
</script>"""


def stepper(stage, section, in_progress_from):
    order = [s[0] for s in STAGES]
    cur = order.index(stage)
    out = ['<div class="stepper-wrap"><nav aria-label="Assessment stages" data-component="StageNav"><ol class="stepper">']
    for n, (key, label, href, subs) in enumerate(STAGES):
        state = 'current' if n == cur else ('done' if n < in_progress_from else 'todo')
        mark = CHECK if state == 'done' else str(n + 1)
        hint = {'done': ' (complete)', 'current': '', 'todo': ' (not started)'}[state]
        cur_attr = ' aria-current="step"' if state == 'current' else ''
        out.append(f'<li class="step" data-state="{state}"><a class="step-link" href="{href}"{cur_attr}><span class="step-mark">{mark}</span><span class="step-label">{label}<span hidden>{hint}</span></span></a>')
        if state == 'current' and subs:
            out.append(f'<ul class="substeps" aria-label="{label} sections">')
            for sl, sh, count in subs:
                c = ' aria-current="page"' if sl == section else ''
                badge = f'<span class="count">{count}</span>' if count else ''
                out.append(f'<li><a href="{sh}"{c}>{sl}{badge}</a></li>')
            out.append('</ul>')
        out.append('</li>')
    out.append('</ol></nav></div>')
    return ''.join(out)


def shell(title, stage, section, in_progress_from, right='1 Jul to 30 Sep 2026 · Evidence cut-off 6 Oct 2026'):
    return (
        '<body><a class="skip-link" href="#main">Skip to content</a><div class="app-shell" data-component="AppShell">'
        '<aside class="sidebar" id="global-nav" aria-label="Global navigation"><a class="brand" href="questionnaire.html">CyberAssess</a>'
        '<nav><a href="questionnaire.html#overview">Home</a><a href="questionnaire.html#overview">Clients</a><a href="questionnaire.html#overview" aria-current="true">Engagements</a><a href="rfi.html">Evidence library</a><a href="report.html">Reports</a></nav>'
        '<div class="identity"><span class="caption">Working as</span><strong>Meera Joshi</strong><a class="caption" href="scope-applicability.html">Settings</a></div></aside>'
        '<main id="main" class="page" data-component="Page">'
        f'<div class="context-bar"><button class="icon-button" id="nav-toggle" type="button" aria-controls="global-nav" aria-expanded="true" aria-label="Hide navigation">{PANEL}</button>'
        '<ol class="crumbs" aria-label="Breadcrumb"><li>Veldhara Logistics</li><li>FY2026-27 engagement</li><li aria-current="true">ISO 27001 assessment</li></ol>'
        f'<span class="caption">{right}</span></div>'
        + stepper(stage, section, in_progress_from)
    )


def page(title, body, script=''):
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title} | CyberAssess</title><link rel="stylesheet" href="prototype.css"></head>\n{body}</main></div>{SCRIPT}{script}</body></html>\n')


# ---------------------------------------------------------------- questionnaire
ROWS_BEFORE = [('A5.15', 'Access control', 'Fully implemented', 'success'), ('A5.16', 'Identity management', 'Fully implemented', 'success'), ('A5.17', 'Authentication information', 'Fully implemented', 'success')]
ROWS_AFTER = [('A5.25', 'Assessment and decision on information security events', 'Fully implemented', 'success'), ('A5.26', 'Response to information security incidents', 'Partially implemented', 'warning'), ('A5.27', 'Learning from information security incidents', 'Planned', 'neutral')]
CHOICES = [('fully', 'Fully implemented'), ('partial', 'Partially implemented'), ('none', 'Not implemented'), ('planned', 'Planned'), ('not_applicable', 'Not applicable')]


def q_row(code, name, state, tone, open_=False, qid=''):
    return (f'<button class="q-row" type="button" aria-expanded="{str(open_).lower()}"{f" aria-controls={qid}-body" if qid else ""} onclick="toggleQ(this)">'
            f'<span class="code">{code}</span><span class="name">{e(name)}</span><span class="status {tone}" data-family="progress">{state}</span>{CHEVRON}</button>')


def choices(name, checked=None):
    return '<div class="choices">' + ''.join(
        f'<label class="choice"><input type="radio" name="{name}" value="{v}"{" checked" if v == checked else ""}><span>{l}</span></label>' for v, l in CHOICES) + '</div>'


def questionnaire():
    closed = lambda rows: ''.join(f'<li class="q" data-open="false">{q_row(*r)}</li>' for r in rows)
    q1 = (
        '<li class="q" data-open="true" data-component="QuestionCard">' + q_row('A5.24', 'Information security incident management planning and preparation', 'Unanswered', 'neutral', True, 'q1') +
        '<div class="q-body" id="q1-body">'
        '<p class="q-text">The organization shall plan and prepare for managing information security incidents by defining, establishing and communicating incident management processes, roles and responsibilities.</p>'
        '<div class="pair">'
        '<div class="block"><h3 class="overline">Rationale</h3><p id="q1-why" data-illustrative="true">A response plan must be usable during disruption. An exercise reveals unclear responsibilities before a live incident.</p></div>'
        '<div class="block"><h3 class="overline">Steering the response</h3><p id="q1-hint" data-illustrative="true">Ask the incident owner to walk through the latest exercise and show how assigned improvements were closed.</p></div>'
        '</div>'
        '<div class="answer"><fieldset><legend class="overline">Client response</legend>' + choices('q1') + '</fieldset>'
        '<label class="field"><span class="overline">Auditor notes</span><textarea id="draft-notes" rows="3" placeholder="For example: plan approved in March, no tabletop held this year"></textarea></label>'
        '<div class="answer-foot"><span class="caption" id="draft-state" aria-live="polite">Nothing to save yet</span><button class="button" type="button">Next unanswered</button></div></div>'
        '</div></li>')
    q2 = (
        '<li class="q" data-open="true" data-component="QuestionCard">' + q_row('A5.18', 'Access rights', 'Partially implemented', 'warning', True, 'q2') +
        '<div class="q-body" id="q2-body">'
        '<p class="q-text">Access rights to information and other associated assets shall be provisioned, reviewed, modified and removed in accordance with the topic-specific policy and rules.</p>'
        '<div class="pair">'
        '<div class="block"><h3 class="overline">Rationale</h3><p id="q2-why" data-illustrative="true">Access reviews help find permissions that are no longer needed, including access retained after a person leaves.</p></div>'
        '<div class="block"><h3 class="overline">Steering the response</h3><p id="q2-hint" data-illustrative="true">Ask the system owner to show the last three review cycles, including excluded systems and removal tickets.</p></div>'
        '</div>'
        '<div class="answer"><div class="pair">'
        '<div class="block"><h3 class="overline">Client response</h3><p id="q2-response" data-illustrative="true"><span class="status warning">Partially implemented</span></p>'
        '<p>Eight approved removal actions remained open at 30 September, including four enabled terminated users; July and August lack signed reviews.</p></div>'
        '<div class="block"><h3 class="overline">Approved conclusion</h3><p><span class="status warning" data-family="outcome">Partially compliant</span></p>'
        '<p>Access rights are provisioned and reviewed by policy, but the quarter contains two incomplete cycles, two omitted systems and open removals.</p>'
        '<div class="evidence-quote"><a href="http://127.0.0.1:8011/evidence/508e0b3d-ccc0-40bc-9d78-48edaa412ebb">Veldhara_Access_Review_Q2_FY26.docx</a><span>“The completed review covered 9 of 11 production systems.”</span></div></div>'
        '</div><div class="answer-foot"><span class="caption">Answered and reviewed. Editing the response reopens the conclusion.</span><button class="button" type="button">Edit response</button></div></div>'
        '</div></li>')
    rail = ''.join(
        f'<li><a href="#{k}"{" aria-current=true" if cur else ""}><span class="rail-name">{n}</span><span class="count">{a} of {t}</span><progress class="rail-bar" value="{a}" max="{t}" aria-label="{n} answered"></progress></a></li>'
        for k, n, a, t, cur in [('organizational', 'Organizational', 36, 37, True), ('people', 'People', 8, 8, False), ('physical', 'Physical', 14, 14, False), ('technological', 'Technological', 34, 34, False)])
    body = (shell('Questionnaire', 'questionnaire', None, 3) +
            '<div class="split"><nav class="rail" aria-label="ISO 27001 domains"><span class="overline">Annex A domains</span><ul class="rail-list" id="q-rail-counts" data-illustrative="true">' + rail + '</ul></nav>'
            '<div class="stack" id="organizational">'
            '<header class="view-head"><div><h1>Organizational controls</h1><p class="caption" id="q-section-progress" data-illustrative="true">37 questions · 1 left to answer · drafts save as you type</p></div>'
            '<div class="cluster"><div class="segmented" role="group" aria-label="Show"><button type="button" aria-pressed="true">All</button><button type="button" aria-pressed="false">Unanswered</button></div>'
            '<button class="button primary" type="button" onclick="document.getElementById(\'complete-message\').hidden=false">Complete section</button></div></header>'
            '<p id="complete-message" class="caption" role="status" hidden>Answer A5.24 to complete this section.</p>'
            '<ol class="q-list" id="q-row-states" data-illustrative="true">' + closed(ROWS_BEFORE) + q2 + closed([('A5.19', 'Information security in supplier relationships', 'Fully implemented', 'success'), ('A5.23', 'Information security for use of cloud services', 'Fully implemented', 'success')]) + q1 + closed(ROWS_AFTER) + '</ol>'
            '</div></div>')
    script = """<script>
function toggleQ(b){var q=b.closest('.q');if(!q.querySelector('.q-body'))return;var o=q.dataset.open!=='true';q.dataset.open=o;b.setAttribute('aria-expanded',o);q.querySelector('.q-body').hidden=!o;}
(function(){var s=document.getElementById('draft-state');function saved(){s.textContent='Draft saved just now';}
document.getElementById('draft-notes').addEventListener('input',function(){s.textContent='Saving…';clearTimeout(window.__t);window.__t=setTimeout(saved,600);});
document.querySelectorAll('input[name=q1]').forEach(function(r){r.addEventListener('change',saved);});
document.querySelectorAll('.segmented button').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.segmented button').forEach(function(x){x.setAttribute('aria-pressed',x===b);});var only=b.textContent==='Unanswered';document.querySelectorAll('.q').forEach(function(q){q.hidden=only&&!q.querySelector('.status.neutral');});});});})();
</script>"""
    (PROTO / 'questionnaire.html').write_text(page('Questionnaire', body, script))


# ---------------------------------------------------------------- review queue
TONE = {'Partially compliant': 'warning', 'Compliant': 'success', 'Non-compliant': 'danger', 'High': 'danger', 'Critical': 'danger', 'Medium': 'warning', 'Low': 'neutral'}


def review():
    fs = json.loads((PROTO / 'findings.json').read_text())

    def item(f):
        cur = ' aria-current="true"' if f['i'] == 0 else ''
        decided = ' decided' if f['decided'] else ''
        tail = '<span>Approved</span>' if f['decided'] else ''
        return (f'<li><button class="queue-item{decided}" type="button" data-control="{f["code"]}" data-evidence-priority="{f["evidence_priority"]}" data-rank="{f["rank"]}" data-risk="{f["risk"]}"{cur} onclick="showFinding({f["i"]},this)">'
                f'<span class="q-title" id="queue-title-{f["i"]}" data-illustrative="true">{e(f["title"])}</span>'
                f'<span class="q-meta"><span class="code">{f["code"]}</span><span class="status {TONE[f["risk"]]}" data-family="severity">{f["risk"]} risk</span><span data-family="outcome">{f["outcome"]}</span>{tail}</span></button></li>')

    def detail(f):
        i = f['i']
        domain, cid, name = [p.strip() for p in f['meta'].split('·', 2)]
        quote = re.sub(r'^.*?Characters [\d–-]+\s*', '', f['quote'] or '')
        span = re.search(r'Characters [\d–-]+', f['quote'] or '')
        if f['decided']:
            actions = f'<span class="status success" id="decision-{i}" role="status">Approved</span><button class="button" type="button">Reopen</button>'
            decision = '<span class="status success">Approved</span>'
        else:
            actions = (f'<button class="button quiet destructive" type="button" onclick="decide({i},\'Rejected\')">Reject</button>'
                       f'<button class="button" type="button" onclick="document.getElementById(\'edit-{i}\').hidden=false">Edit</button>'
                       f'<button class="button primary" type="button" onclick="decide({i},\'Approved\')">Approve</button>')
            decision = f'<span id="decision-{i}" role="status">Awaiting your decision</span>'
        return (
            f'<article id="finding-{i}" class="surface finding" data-component="FindingDetail"{"" if i == 0 else " hidden"}>'
            f'<header class="finding-head"><div class="finding-id"><p class="overline">{f["code"]} {e(name)} · {domain}</p><h2 class="t-title" id="finding-title-{i}" data-illustrative="true">{e(f["title"])}</h2></div>'
            f'<div class="actions" data-component="ReviewDecision">{actions}</div></header>'
            '<dl class="verdict">'
            f'<div><dt class="overline">Compliance</dt><dd><span class="status {TONE[f["outcome"]]}" data-family="outcome">{f["outcome"]}</span></dd></div>'
            f'<div><dt class="overline">Risk</dt><dd><span class="status {TONE[f["risk"]]}" data-family="severity">{f["risk"]}</span></dd></div>'
            f'<div><dt class="overline">Decision</dt><dd>{decision}</dd></div>'
            '<div><dt class="overline">Proposed by</dt><dd><span data-family="provenance">AI, from cited evidence</span></dd></div></dl>'
            '<div class="finding-grid"><div class="finding-main">'
            f'<section class="block"><h2 class="overline">Gap</h2><p class="lead">{e(f["gap"])}</p></section>'
            f'<section class="block"><h2 class="overline">Impact if unresolved</h2><p id="finding-impact-{i}" data-illustrative="true">{e(f["impact"])}</p></section>'
            f'<section class="recommend"><div class="block"><h2 class="overline">Recommendation</h2><p class="rec-text">{e(f["rec"])}</p></div>'
            f'<div class="block"><h3 class="overline">Why this recommendation</h3><p id="finding-reason-{i}" data-illustrative="true">{e(f["why"])}</p></div></section>'
            f'<div id="edit-{i}" hidden><label class="field"><span class="overline">Edit gap statement</span><textarea rows="3">{e(f["gap"])}</textarea></label></div>'
            f'<section class="block reasoning"><h2 class="overline">Reasoning on record</h2><p>{e(f["rationale"])}</p></section>'
            '</div><aside class="finding-aside" aria-label="Where this finding came from">'
            f'<div class="block"><h2 class="overline">Evidence cited</h2><a href="{f["href"]}">{e(f["file"])}</a>'
            f'<div class="evidence-quote"><span>“{e(quote)}”</span><span class="caption">{span.group(0) if span else ""}</span></div></div>'
            f'<div class="block"><h2 class="overline">Interviews</h2><p id="finding-provenance-{i}" data-illustrative="true">None recorded for this control.</p></div>'
            f'<div class="block"><h2 class="overline">Control</h2><p>{cid} · {e(name)}</p><p>{domain} · ISO 27001</p></div>'
            '</aside></div></article>')

    pending = [f for f in fs if not f['decided']]
    decided = [f for f in fs if f['decided']]
    body = (shell('Review queue', 'review', 'Queue', 4) +
            '<div class="queue-split"><div class="queue">'
            '<div class="queue-head"><h1 class="t-sub">Findings</h1>'
            '<label class="select-label">Order<select onchange="sortQueue(this.value)"><option value="pending">Pending first</option><option value="evidence">Evidence problems first</option><option value="risk">Highest risk</option><option value="control">Control ID</option></select></label></div>'
            f'<div class="queue-group"><span class="overline" data-group>To decide · {len(pending)}</span><ul class="queue-list" id="queue-pending">{"".join(map(item, pending))}</ul></div>'
            f'<div class="queue-group"><span class="overline" data-group>Decided · {len(decided)}</span><ul class="queue-list" id="queue-decided">{"".join(map(item, decided))}</ul></div>'
            '</div><div>' + ''.join(map(detail, fs)) + '</div></div>')
    script = """<script>
function showFinding(i,b){document.querySelectorAll('.finding').forEach(function(n){n.hidden=n.id!=='finding-'+i;});document.querySelectorAll('.queue-item').forEach(function(n){n.removeAttribute('aria-current');});b.setAttribute('aria-current','true');history.replaceState(null,'','#finding-'+i);}
function decide(i,t){var s=document.getElementById('decision-'+i);s.textContent=t;s.className='status '+(t==='Approved'?'success':'danger');}
function sortQueue(v){var p=document.getElementById('queue-pending'),d=document.getElementById('queue-decided'),rows=[].slice.call(document.querySelectorAll('.queue-list li')),rk={Critical:0,High:1,Medium:2,Low:3};
function b(li){return li.firstElementChild;}
if(v==='pending'){rows.sort(function(x,y){return b(x).dataset.rank-b(y).dataset.rank;});rows.forEach(function(li){(b(li).classList.contains('decided')?d:p).append(li);});}
else{if(v==='evidence')rows.sort(function(x,y){return b(x).dataset.evidencePriority-b(y).dataset.evidencePriority;});else if(v==='risk')rows.sort(function(x,y){return rk[b(x).dataset.risk]-rk[b(y).dataset.risk]||b(x).dataset.rank-b(y).dataset.rank;});else rows.sort(function(x,y){return b(x).dataset.control.localeCompare(b(y).dataset.control,undefined,{numeric:true});});rows.forEach(function(li){p.append(li);});}
document.querySelectorAll('[data-group]').forEach(function(g){g.hidden=v!=='pending';});}
</script>"""
    (PROTO / 'review-queue.html').write_text(page('Review queue', body, script))


# ---------------------------------------------------------------- shared pieces
RISK_ORDER = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}


def status(text, family, suffix=''):
    return f'<span class="status {TONE.get(text, "neutral")}" data-family="{family}">{text}{suffix}</span>'


def cited(quote, href):
    """'File , Characters a-b text' -> link, quote and character span."""
    m = re.match(r'\s*(.*?)\s*,\s*(Characters [\d–-]+)\s*(.*)', quote or '', re.S)
    if not m:
        return '<p>No source is cited.</p>'
    name, span, text = m.groups()
    return (f'<a href="{href}">{e(name)}</a><div class="evidence-quote"><span>“{e(text)}”</span><span class="caption">{span}</span></div>')


def finding_body(gap, impact, impact_id, rec, why, why_id, rationale, aside):
    main = ''
    if gap:
        main += f'<section class="block"><h3 class="overline">Gap</h3><p class="lead">{e(gap)}</p></section>'
    if impact:
        main += f'<section class="block"><h3 class="overline">Impact if unresolved</h3><p id="{impact_id}" data-illustrative="true">{e(impact)}</p></section>'
    if rec:
        reason = f'<div class="block"><h3 class="overline">Why this recommendation</h3><p id="{why_id}" data-illustrative="true">{e(why)}</p></div>' if why else ''
        main += f'<section class="recommend"><div class="block"><h3 class="overline">Recommendation</h3><p class="rec-text">{e(rec)}</p></div>{reason}</section>'
    if rationale:
        main += f'<section class="block reasoning"><h3 class="overline">Reasoning on record</h3><p>{e(rationale)}</p></section>'
    return f'<div class="finding-grid"><div class="finding-main">{main}</div><aside class="finding-aside">{aside}</aside></div>'


# ---------------------------------------------------------------- conclusions
def conclusions():
    rows = json.loads((PROTO / 'conclusions.json').read_text())
    gaps = [r for r in rows if not r['gap'].startswith('No gap')]
    high = sum(r['risk'] == 'High' for r in gaps)
    out = []
    for i, r in enumerate(rows):
        has_gap = r in gaps
        aside = (f'<div class="block"><h3 class="overline">Evidence cited</h3>{cited(r["quote"], r["href"])}</div>'
                 f'<div class="block"><h3 class="overline">Interviews</h3><p id="conclusion-provenance-{i}" data-illustrative="true">None recorded for this control.</p></div>'
                 f'<div class="block"><h3 class="overline">Control</h3><p>{r["control_id"]} · {e(r["name"])}</p><p>{r["domain"]} · ISO 27001</p></div>')
        body = finding_body(r['gap_statement'] if has_gap else None, r['impact'], f'conclusion-impact-{i}', r['rec'], r['why'], f'conclusion-reason-{i}', r['rationale'], aside)
        out.append(
            f'<tr data-title="{r["control_id"]}" data-rank="{r["rank"]}" data-risk="{RISK_ORDER[r["risk"]]}" data-gap="{int(has_gap)}"><td>{r["domain"]}</td><td class="code">{r["code"]}</td>'
            f'<td><button class="row-disclosure{"" if has_gap else " quiet"}" id="conclusion-title-{i}" data-illustrative="true" aria-expanded="false" aria-controls="conclusion-detail-{i}" onclick="toggleConclusion(this)">{e(r["gap"])}</button>'
            f'<span class="caption row-sub">{e(r["name"])}</span></td><td>{status(r["risk"], "severity")}</td><td>{status(r["outcome"], "outcome")}</td></tr>'
            f'<tr id="conclusion-detail-{i}" class="disclosure-row" hidden><td colspan="5">{body}</td></tr>')
    body = (shell('Conclusions', 'review', 'Conclusions', 4) +
            f'<header class="view-head"><div><h1>Conclusions</h1><p class="caption">{len(rows)} controls with an approved conclusion · {len(gaps)} with a gap · {high} high risk</p></div>'
            '<div class="cluster"><div class="segmented" role="group" aria-label="Show"><button type="button" aria-pressed="true" onclick="filterGaps(this,false)">All</button><button type="button" aria-pressed="false" onclick="filterGaps(this,true)">With a gap</button></div>'
            '<label class="select-label inline">Sort<select onchange="sortConclusions(this.value)"><option value="rank">Domain and control</option><option value="risk">Highest risk</option></select></label></div></header>'
            '<div class="table-shell"><table class="data-table sheet" data-component="DataTable"><thead><tr><th scope="col">Domain</th><th scope="col">Control</th><th scope="col">Gap or conclusion</th><th scope="col">Risk</th><th scope="col">Status</th></tr></thead>'
            f'<tbody id="conclusion-rows">{"".join(out)}</tbody></table></div>')
    script = """<script>
function toggleConclusion(b){var r=document.getElementById(b.getAttribute('aria-controls'));r.hidden=!r.hidden;b.setAttribute('aria-expanded',String(!r.hidden));}
function detailOf(r){return document.getElementById(r.querySelector('button').getAttribute('aria-controls'));}
function sortConclusions(v){var root=document.getElementById('conclusion-rows'),rows=[].slice.call(root.querySelectorAll('tr[data-title]'));rows.sort(function(a,b){return v==='risk'?(a.dataset.risk-b.dataset.risk||b.dataset.gap-a.dataset.gap||a.dataset.rank-b.dataset.rank):a.dataset.rank-b.dataset.rank;});rows.forEach(function(r){root.append(r,detailOf(r));});}
function filterGaps(b,only){b.parentNode.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',String(x===b));});document.querySelectorAll('#conclusion-rows tr[data-title]').forEach(function(r){var hide=only&&r.dataset.gap==='0';r.hidden=hide;if(hide){detailOf(r).hidden=true;r.querySelector('button').setAttribute('aria-expanded','false');}});}
</script>"""
    (PROTO / 'conclusions.html').write_text(page('Conclusions', body, script))


# ---------------------------------------------------------------- evidence requests
def rfi():
    items = json.loads((PROTO / 'rfi.json').read_text())
    cols = [('title', 'Request'), ('required', 'Requirement'), ('mapped', 'Evidence held'), ('state', 'State')]

    def heading():
        return ('<div class="request-heading"><div class="request-summary">' + ''.join(
            f'<button class="request-sort" type="button" data-sort="{k}" onclick="sortRequests(\'{k}\')">{l}<span aria-hidden="true"></span></button>' for k, l in cols) + '</div><span class="overline">Action</span></div>')

    def row(it):
        what = [w.strip() for w in re.split(r'(?<=\))\s+', it['what'] or '') if w.strip()]
        what_html = ('<ul>' + ''.join(f'<li>{e(w)}</li>' for w in what) + '</ul>') if what else '<p>Not specified for this request.</p>'
        ident = f' id="{it["id"]}" data-illustrative="true"' if it['id'] else ''
        action = '' if it['included'] else '<button class="button" type="button" onclick="includeRequest(this)">Add to RFI</button>'
        req = 'Required' if it['required'] == 'Required' else '<span class="quiet">Optional</span>'
        state_tone = 'info' if it['included'] else 'neutral'
        return (f'<article class="request-row"{ident} data-component="RequestRow" data-title="{e(it["title"])}" data-required="{it["required"]}" data-state="{it["state"]}" data-mapped="{it["mapped"]}" data-total="{it["total"]}">'
                f'<details><summary class="request-summary"><span class="request-title">{e(it["title"])}</span><span>{req}</span>'
                f'<span class="held"><span class="numeric">{it["mapped"]} of {it["total"]}</span><progress class="rail-bar" value="{it["mapped"]}" max="{it["total"]}" aria-label="Evidence already held for {it["mapped"]} of {it["total"]} requirements"></progress></span>'
                f'<span class="status {state_tone} request-state" data-component="StatusBadge" data-family="progress">{it["state"]}</span></summary>'
                f'<div class="request-details"><p class="caption">{it["ref"] or ""}</p><div class="pair"><div class="block"><h3 class="overline">What to send</h3>{what_html}</div>'
                f'<div class="stack-s"><div class="block"><h3 class="overline">Example</h3><p>{e(it["example"] or "")}</p></div><div class="block"><h3 class="overline">What good looks like</h3><p>{e(it["good"] or "")}</p></div></div></div></div>'
                f'</details><div class="request-action">{action}</div></article>')

    inc = [i for i in items if i['included']]
    rest = [i for i in items if not i['included']]
    body = (shell('Evidence requests', 'evidence', 'Requests', 2) +
            f'<header class="view-head"><div><h1>Evidence requests</h1><p class="caption"><span id="rfi-count-in">{len(inc)}</span> in the draft RFI · <span id="rfi-count-out">{len(rest)}</span> not requested · sent as Meera Joshi</p></div>'
            '<button class="button primary" type="button">Generate RFI version</button></header>'
            f'<section class="stack-s" aria-labelledby="included-heading"><h2 id="included-heading">In this RFI</h2><div class="table-shell">{heading()}<div id="included-items" class="request-list">{"".join(map(row, inc))}</div></div></section>'
            f'<section class="stack-s" aria-labelledby="available-heading"><h2 id="available-heading">Not yet requested</h2><div class="table-shell">{heading()}<div id="request-items" class="request-list">{"".join(map(row, rest))}</div></div></section>'
            '<section class="stack-s empty" id="versions"><h2>RFI versions</h2><p class="prose">No version has been generated. Generate one when the list above is right, then issue it to the client.</p></section>'
            '<section class="stack-s empty" id="links"><h2>Client links</h2><p class="prose">A client upload link can be created once an RFI version is issued.</p></section>')
    script = """<script>
var rs={key:'title',dir:1},so={'Not requested':0,'In draft RFI':1,'Issued':2,'Received':3};
function applySort(){['included-items','request-items'].forEach(function(id){var root=document.getElementById(id),rows=[].slice.call(root.children);rows.sort(function(a,b){var c=0,k=rs.key;
if(k==='mapped')c=(a.dataset.mapped/a.dataset.total||0)-(b.dataset.mapped/b.dataset.total||0);else if(k==='state')c=so[a.dataset.state]-so[b.dataset.state];else if(k==='required')c=(a.dataset.required==='Required'?0:1)-(b.dataset.required==='Required'?0:1);else c=a.dataset.title.localeCompare(b.dataset.title);
return rs.dir*(c||a.dataset.title.localeCompare(b.dataset.title));});rows.forEach(function(r){root.append(r);});});
document.querySelectorAll('[data-sort]').forEach(function(b){var on=b.dataset.sort===rs.key;b.setAttribute('aria-pressed',String(on));b.querySelector('span').textContent=on?(rs.dir>0?' ↑':' ↓'):'';});}
function sortRequests(k){rs.dir=rs.key===k?-rs.dir:1;rs.key=k;applySort();}
function includeRequest(b){var r=b.closest('.request-row'),s=r.querySelector('.request-state');r.dataset.state='In draft RFI';s.textContent='In draft RFI';s.className='status info request-state';b.remove();document.getElementById('included-items').append(r);
document.getElementById('rfi-count-in').textContent=document.getElementById('included-items').children.length;document.getElementById('rfi-count-out').textContent=document.getElementById('request-items').children.length;applySort();}
applySort();
</script>"""
    (PROTO / 'rfi.html').write_text(page('Evidence requests', body, script))


# ---------------------------------------------------------------- report
def report():
    rep = json.loads((PROTO / 'report.json').read_text())
    counts = [[int(n) for n in re.findall(r'(\d+) (?:high|medium|low)', r[2])] for r in rep['table']]
    tot = [sum(c[i] for c in counts) for i in range(3)]

    def gap(g):
        marks = f'<p class="cluster">{status(g["risk"], "severity", " risk")}{status(g["outcome"], "outcome")}</p>'
        impact = f'<div class="block"><h4 class="overline">Impact if unresolved</h4><p id="{g["impact_id"]}" data-illustrative="true">{e(g["impact"])}</p></div>'
        why = f'<p id="{g["why_id"]}" data-illustrative="true">{e(g["why"])}</p>'
        head = f'<div class="block"><h4 class="overline">Recommendation</h4><p class="rec-text">{e(g["rec"])}</p></div>'
        if g['risk'] == 'High':
            rec = f'<div class="recommend">{head}<details class="why"><summary>Why this recommendation</summary>{why}</details></div>'
        else:
            rec = f'<div class="recommend">{head}<div class="block"><h4 class="overline">Why this recommendation</h4>{why}</div></div>'
        if g['risk'] == 'High':
            return f'<article class="board-gap" data-level="full"><div class="gap-lead"><h3 class="board-gap-title">{e(g["title"])}</h3>{marks}{impact}</div>{rec}</article>'
        return (f'<article class="board-gap" data-level="compact"><details><summary><span class="board-gap-title">{e(g["title"])}</span>{status(g["risk"], "severity", " risk")}</summary>'
                f'<div class="gap-open"><div class="gap-lead">{impact}</div>{rec}</div></details></article>')

    domains = ''
    for d in rep['domains']:
        score, label = [x.strip() for x in d['score'].split('·')]
        full = [g for g in d['gaps'] if g['risk'] == 'High']
        other = [g for g in d['gaps'] if g['risk'] != 'High']
        inner = ''
        if d['strength']:
            inner += f'<p id="{d["strength_id"]}" class="prose" data-illustrative="true">{e(d["strength"])}</p>'
        inner += f'<div class="board-domain-gaps">{"".join(map(gap, full))}</div>'
        if other:
            inner += f'<h3 class="overline">Medium risk · {len(other)}</h3><div class="board-domain-gaps compact">{"".join(map(gap, other))}</div>'
        sec = ' data-report-section="gaps"' if d['key'] == 'organizational' else ''
        domains += (f'<section id="report-{d["key"]}"{sec}><div class="domain-summary"><h2>{d["title"]}</h2><p class="domain-score"><strong class="numeric">{score}</strong><span class="caption">{label}</span></p></div>{inner}</section>')

    table = ''.join(
        f'<tr><td>{r[0]}</td><td class="score"><span class="numeric">{r[1]}</span><progress class="rail-bar" value="{r[1].rstrip("%")}" max="100" aria-label="{r[0]} score"></progress></td>'
        + ''.join(f'<td class="numeric{" zero" if n == 0 else ""}">{n}</td>' for n in c) + '</tr>' for r, c in zip(rep['table'], counts))
    weakest, strongest = rep['table'][0], rep['table'][-1]
    board = (
        '<section id="report-summary" class="report-top"><div class="block"><h2 class="overline">Executive summary</h2>'
        f'<p id="report-executive" class="lead" data-illustrative="true">{e(rep["executive"])}</p></div>'
        '<dl class="facts"><div><dt class="overline">Overall ISO 27001 score</dt><dd class="big numeric">84.3%</dd></div>'
        f'<div><dt class="overline">Open gaps</dt><dd><span class="status danger">{tot[0]} high</span> · {tot[1]} medium · {tot[2]} low</dd></div>'
        f'<div><dt class="overline">Weakest domain</dt><dd>{weakest[0]} · <span class="numeric">{weakest[1]}</span></dd></div>'
        f'<div><dt class="overline">Strongest domain</dt><dd>{strongest[0]} · <span class="numeric">{strongest[1]}</span></dd></div>'
        '<div><dt class="overline">Basis</dt><dd>93 controls, approved conclusions at 6 Oct 2026</dd></div></dl></section>'
        f'<section id="report-domains"><h2>Overall posture</h2><p class="prose" data-illustrative="true" id="report-posture">{rep["posture"]}</p>'
        '<div class="table-shell"><table class="data-table report-domain-table"><thead><tr><th scope="col">Domain, weakest first</th><th scope="col">Score</th><th scope="col">High</th><th scope="col">Medium</th><th scope="col">Low</th></tr></thead>'
        f'<tbody>{table}</tbody></table></div></section>' + domains)

    detail = ''
    names = []
    for x in rep['detail']:
        if x['domain'] not in names:
            if names:
                detail += '</div></section>'
            detail += f'<section id="auditor-domain-{len(names)}" data-domain="{x["domain"]}"><h2>{x["domain"]}</h2><div class="table-shell d-list">'
            names.append(x['domain'])
        has_gap = not x['gap'].startswith('No gap')
        aside = (f'<div class="block"><h4 class="overline">Evidence cited</h4>{cited(x["prov"], x["href"])}</div>'
                 f'<div class="block"><h4 class="overline">Control</h4><p>{x["code"]} · {e(x["name"])}</p></div>'
                 '<div class="block"><h4 class="overline">Not recorded</h4><p>Impact and the reasoning behind the recommendation.</p></div>')
        main = (f'<section class="block"><h4 class="overline">Conclusion</h4><p>{e(x["rationale"])}</p></section>'
                f'<section class="recommend"><div class="block"><h4 class="overline">Recommendation</h4><p class="rec-text">{e(x["rec"])}</p></div></section>')
        detail += (f'<details class="d-item" data-domain="{x["domain"]}" data-outcome="{x["outcome"]}" data-risk="{x["risk"]}"><summary class="d-row"><span class="code caption">{x["code"]}</span>'
                   f'<span class="d-title{"" if has_gap else " quiet"}">{e(x["gap"])}<span class="caption row-sub">{e(x["name"])}</span></span>{status(x["risk"], "severity")}{status(x["outcome"], "outcome")}</summary>'
                   f'<div class="d-body"><div class="finding-grid"><div class="finding-main">{main}</div><aside class="finding-aside">{aside}</aside></div></div></details>')
    detail += '</div></section>'
    sel = lambda i, label, opts: f'<label class="select-label">{label}<select id="{i}" onchange="filterReport()"><option value="all">All</option>{"".join(f"<option>{o}</option>" for o in opts)}</select></label>'
    filters = ('<div class="view-head"><div><h2>Auditor detail</h2><p class="caption" id="detail-count" role="status" aria-live="polite">93 controls shown</p></div><div class="toolbar-group report-filters">'
               + sel('detail-domain', 'Domain', names) + sel('detail-outcome', 'Outcome', ['Compliant', 'Partially compliant', 'Non-compliant']) + sel('detail-risk', 'Risk', ['High', 'Medium', 'Low']) + '</div></div>')
    toggle = ('<div class="report-toggle" role="group" aria-label="Report view" data-component="ReportViewToggle">'
              '<button type="button" class="button primary" id="board-toggle" aria-pressed="true" onclick="switchReport(\'board\')">Board summary</button>'
              '<button type="button" class="button" id="detail-toggle" aria-pressed="false" onclick="switchReport(\'detail\')">Auditor detail</button></div>')
    body = (shell('Report', 'report', None, 5) +
            f'<header class="view-head"><div><h1>Assessment report</h1><p class="caption">ISO 27001 · Veldhara Logistics Pvt Ltd · 1 Jul to 30 Sep 2026</p></div>{toggle}</header>'
            f'<div class="document report-document"><div id="board-view">{board}</div><div id="detail-view" hidden>{filters}{detail}</div></div>')
    script = """<script>
function switchReport(v){document.getElementById('board-view').hidden=v!=='board';document.getElementById('detail-view').hidden=v!=='detail';['board','detail'].forEach(function(n){var b=document.getElementById(n+'-toggle');b.setAttribute('aria-pressed',String(n===v));b.classList.toggle('primary',n===v);});}
function filterReport(){var d=document.getElementById('detail-domain').value,o=document.getElementById('detail-outcome').value,r=document.getElementById('detail-risk').value,n=0;
document.querySelectorAll('#detail-view details').forEach(function(x){var ok=(d==='all'||x.dataset.domain===d)&&(o==='all'||x.dataset.outcome===o)&&(r==='all'||x.dataset.risk===r);x.hidden=!ok;if(ok)n++;});
document.querySelectorAll('#detail-view section[data-domain]').forEach(function(s){s.hidden=!s.querySelector('details:not([hidden])');});
document.getElementById('detail-count').textContent=n+(n===1?' control shown':' controls shown');}
if(location.hash==='#detail'||location.hash==='#detail-wide')switchReport('detail');
</script>"""
    (PROTO / 'report.html').write_text(page('Report', body, script))


# ---------------------------------------------------------------- scope: applicability
def scope():
    excluded = [('A.8.30', 'Outsourced development', 'soa-exclusion-outsourcing', 'Veldhara does not commission third parties to develop software within this ISMS scope. Its transport systems are licensed services managed through supplier controls.'),
                ('A.8.28', 'Secure coding', 'soa-exclusion-coding', 'No software is developed or modified by Veldhara within the agreed scope. Configuration of licensed transport applications is covered by change management.')]
    rows = ''.join(f'<li class="exclusion"><div class="block"><h3><span class="code">{c}</span> {n}</h3><p id="{i}" class="prose" data-illustrative="true">{t}</p></div><button class="button quiet" type="button">Remove</button></li>' for c, n, i, t in excluded)
    body = (shell('Scope', 'scope', 'Applicability', 1) +
            '<header class="view-head"><div><h1>Applicability</h1><p class="caption">ISO 27001 Annex A · record only the controls that do not apply</p></div></header>'
            '<dl class="facts row"><div><dt class="overline">Annex A controls</dt><dd class="numeric">93</dd></div><div><dt class="overline">Applicable</dt><dd class="numeric">91</dd></div><div><dt class="overline">Excluded</dt><dd class="numeric">2</dd></div></dl>'
            '<section class="block"><h2 class="overline">Standard justification for every applicable control</h2>'
            '<p id="soa-standard" class="lead measure" data-illustrative="true">All other controls are applicable because they are included in the agreed ISMS scope. This is a scope justification, not a claim that the controls work.</p></section>'
            f'<section class="stack-s" data-component="ScopeExceptions"><h2>Controls that do not apply</h2><ul class="surface exclusions">{rows}</ul></section>'
            '<form class="recommend scope-form" onsubmit="event.preventDefault();document.getElementById(\'scope-message\').hidden=false"><h2 class="t-sub">Exclude another control</h2>'
            '<label class="field" for="exclude-control"><span class="overline">Control</span><select id="exclude-control" required><option value="">Choose a control</option><option>A.8.4 · Access to source code</option><option>A.8.25 · Secure development life cycle</option></select></label>'
            '<label class="field" for="exclude-reason"><span class="overline">Why it does not apply</span><textarea id="exclude-reason" rows="3" required placeholder="For example: no source code is held or changed within the agreed scope"></textarea></label>'
            '<div class="cluster"><button class="button primary" type="submit">Exclude control</button><span id="scope-message" class="caption" role="status" hidden>Exclusion added to the scope for review.</span></div></form>')
    (PROTO / 'scope-applicability.html').write_text(page('Scope', body))


if __name__ == '__main__':
    questionnaire(); review(); conclusions(); rfi(); report(); scope()
    print('built')
