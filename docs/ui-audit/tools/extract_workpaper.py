"""Collect each prototype control's workpaper and remediation record from the demo app.

Run from repo root with the demo app on port 8011:
    python3 docs/ui-audit/tools/extract_workpaper.py
GET requests only (the workpaper and findings pages). Writes prototypes/workpaper.json,
keyed by control ID, for the controls listed in prototypes/conclusions.json.
"""
import html
import json
import re
import urllib.request
from pathlib import Path

PROTO = Path(__file__).resolve().parents[1] / 'prototypes'
HOST = 'http://127.0.0.1:8011'
APP = HOST + '/assessments/d491ee73-0925-43bd-8cb2-3b5fff2cc8ac'


def get(path):
    with urllib.request.urlopen(APP + path, timeout=120) as response:
        return re.sub(r'<svg.*?</svg>', '', response.read().decode(), flags=re.S)


def text(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def field(block, label):
    m = re.search(r'<span class="sub">' + re.escape(label) + r'</span><div[^>]*>(.*?)</div>', block, re.S)
    return html.unescape(m.group(1)).strip() if m else None


def card(entry, title):
    m = re.search(r'<h2>' + title + r'</h2>(.*?)(?=<div class="solid"|$)', entry, re.S)
    return m.group(1) if m else ''


def main():
    controls = [r['control_id'] for r in json.loads((PROTO / 'conclusions.json').read_text())]
    page = get('/workpaper')
    entries = {m.group(1): m.group(2) for m in re.finditer(r'<article data-workpaper-entry id="wp-iso27001-([^"]+)"(.*?)</article>', page, re.S)}

    remediation = {}
    for row in re.finditer(r'<tr data-finding-row="[^"]+".*?</tr>', get('/findings'), re.S):
        cells = [text(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', row.group(0), re.S)]
        remediation[cells[0]] = {'severity': cells[1], 'status': cells[2], 'owner': cells[3], 'target': cells[4]}

    out = {}
    for control in controls:
        entry = entries[control]
        client, evidence, proposal, history = (card(entry, t) for t in ['Client response', 'Evidence', 'AI proposal', 'Revision history'])
        notes = field(client, 'Notes') or ''
        own = re.search(r'(?m)^' + re.escape(control) + r':\s*(.+)$', notes)
        finding = re.search(r'data-workpaper-finding href="[^"]*">Finding: (.*?)</a>', entry)
        finding_title = html.unescape(finding.group(1)) if finding else None
        action = field(proposal, 'Remediation action')
        out[control] = {
            'answer': field(client, 'Answer'),
            'answer_source': field(client, 'Answer source'),
            'confidence': field(client, 'Confidence'),
            'submitted': field(client, 'Submitted'),
            'shared_question': 'Shared cluster question' in client,
            'client_note': own.group(1).strip() if own else (notes if notes and ':' not in notes[:12] else None),
            'evidence': [{'href': HOST + m.group(2), 'name': html.unescape(m.group(3)), 'relevance': m.group(4)}
                         for m in re.finditer(r'<div data-relevance="(\w+)">.*?<a href="([^"]+)">(.*?)</a></b><span class="sub">(.*?)</span>', evidence, re.S)],
            'proposal': {
                'outcome': text(re.search(r'<span class="pill[^"]*">(.*?)</span>', proposal, re.S).group(1)) if 'class="pill' in proposal else None,
                'model': field(proposal, 'Model'),
                'started': field(proposal, 'Started'),
                'checks': [[text(m.group(1)), text(m.group(2))] for m in re.finditer(r'<li><span class="ck[^"]*"></span>(.*?)<span class="res">(.*?)</span></li>', proposal, re.S)],
            },
            'history': [[text(m.group(1)), text(m.group(2))] for m in re.finditer(r'<div data-revision-action="\w+">.*?<b>(.*?)</b><span class="sub">(.*?)</span>', history, re.S)],
            'remediation': ({'title': finding_title, 'action': action, **remediation[finding_title]} if finding_title in remediation else None),
        }
    (PROTO / 'workpaper.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(len(out), 'controls;', sum(bool(v['remediation']) for v in out.values()), 'with a remediation record;',
          sum(bool(v['client_note']) for v in out.values()), 'with a client note')


if __name__ == '__main__':
    main()
