"""Build the static prototypes' shared shell and the two hand-designed screens.

Run from repo root: python3 docs/ui-audit/tools/build_prototypes.py
Writes questionnaire.html and review-queue.html from scratch (review content comes from
prototypes/findings.json) and replaces the shell of the other prototypes in place.
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
    out = ['<div class="stepper-wrap"><nav aria-label="Assessment stages"><ol class="stepper">']
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
            f'<span class="code">{code}</span><span class="name">{e(name)}</span><span class="status {tone}" data-family="progress" data-illustrative="true">{state}</span>{CHEVRON}</button>')


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
        '<div class="block"><h3 class="overline">Client response</h3><p><span class="status warning" data-illustrative="true">Partially implemented</span></p>'
        '<p>Eight approved removal actions remained open at 30 September, including four enabled terminated users; July and August lack signed reviews.</p></div>'
        '<div class="block"><h3 class="overline">Approved conclusion</h3><p><span class="status warning" data-family="outcome">Partially compliant</span></p>'
        '<p>Access rights are provisioned and reviewed by policy, but the quarter contains two incomplete cycles, two omitted systems and open removals.</p>'
        '<div class="evidence-quote"><a href="http://127.0.0.1:8011/evidence/508e0b3d-ccc0-40bc-9d78-48edaa412ebb">Veldhara_Access_Review_Q2_FY26.docx</a><span>“The completed review covered 9 of 11 production systems.”</span></div></div>'
        '</div><div class="answer-foot"><span class="caption">Answered and reviewed. Editing the response reopens the conclusion.</span><button class="button" type="button">Edit response</button></div></div>'
        '</div></li>')
    rail = ''.join(
        f'<li><a href="#{k}"{" aria-current=true" if cur else ""}><span class="rail-name">{n}</span><span class="count" data-illustrative="true">{a} of {t}</span><span class="rail-bar"><i style="width:{round(a / t * 100)}%"></i></span></a></li>'
        for k, n, a, t, cur in [('organizational', 'Organizational', 36, 37, True), ('people', 'People', 8, 8, False), ('physical', 'Physical', 14, 14, False), ('technological', 'Technological', 34, 34, False)])
    body = (shell('Questionnaire', 'questionnaire', None, 3) +
            '<div class="split"><nav class="rail" aria-label="ISO 27001 domains"><span class="overline">Annex A domains</span><ul class="rail-list">' + rail + '</ul></nav>'
            '<div class="stack" id="organizational">'
            '<header class="view-head"><div><h1>Organizational controls</h1><p class="caption" data-illustrative="true">37 questions · 1 left to answer · drafts save as you type</p></div>'
            '<div class="cluster"><div class="segmented" role="group" aria-label="Show"><button type="button" aria-pressed="true">All</button><button type="button" aria-pressed="false">Unanswered</button></div>'
            '<button class="button primary" type="button" onclick="document.getElementById(\'complete-message\').hidden=false">Complete section</button></div></header>'
            '<p id="complete-message" class="caption" role="status" hidden>Answer A5.24 to complete this section.</p>'
            '<ol class="q-list">' + closed(ROWS_BEFORE) + q2 + closed([('A5.19', 'Information security in supplier relationships', 'Fully implemented', 'success'), ('A5.23', 'Information security for use of cloud services', 'Fully implemented', 'success')]) + q1 + closed(ROWS_AFTER) + '</ol>'
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
                f'<span class="q-title" data-illustrative="true">{e(f["title"])}</span>'
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
            f'<header class="finding-head"><div class="finding-id"><p class="overline">{f["code"]} {e(name)} · {domain}</p><h1 id="finding-title-{i}" data-illustrative="true">{e(f["title"])}</h1></div>'
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
            '<div class="block"><h2 class="overline">Interviews</h2><p data-illustrative="true">None recorded for this control.</p></div>'
            f'<div class="block"><h2 class="overline">Control</h2><p>{cid} · {e(name)}</p><p>{domain} · ISO 27001</p></div>'
            '</aside></div></article>')

    pending = [f for f in fs if not f['decided']]
    decided = [f for f in fs if f['decided']]
    body = (shell('Review queue', 'review', 'Queue', 4) +
            '<div class="queue-split"><div class="queue">'
            '<div class="queue-head"><h2 class="t-sub">Findings</h2>'
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


# ---------------------------------------------------------------- other screens: shell only
OTHERS = {
    'conclusions.html': ('Conclusions', 'review', 'Conclusions', 4, 'Conclusions'),
    'rfi.html': ('Evidence requests', 'evidence', 'Requests', 2, 'Evidence requests'),
    'report.html': ('Report', 'report', None, 5, None),
    'scope-applicability.html': ('Scope', 'scope', 'Applicability', 1, 'Applicability'),
}


def reshell():
    for name, (title, stage, section, upto, h1) in OTHERS.items():
        t = (PROTO / name).read_text()
        start, end = t.index('<body>'), t.index('<div class="toolbar"')
        heading = f'<header class="view-head"><div><h1>{h1}</h1></div></header>' if h1 else ''
        t = t[:start] + shell(title, stage, section, upto) + heading + t[end:]
        t = re.sub(r'<label class="select-label">Section<select.*?</select></label>', '', t, count=1, flags=re.S)
        t = t.replace(SCRIPT, '').replace('</body>', SCRIPT + '</body>', 1)
        (PROTO / name).write_text(t)


if __name__ == '__main__':
    questionnaire(); review(); reshell()
    print('built')
