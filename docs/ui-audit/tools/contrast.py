"""Source-derived WCAG contrast bounds. No network, app writes or model calls.
Run: .venv/bin/python docs/ui-audit/tools/contrast.py
This is a conservative token/surface matrix, not a browser accessibility certification.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOKEN_FILE = ROOT / 'app/static/css/yozora-tokens.css'
CSS_FILES = [ROOT / 'app/static/css/yozora-components.css', ROOT / 'app/static/css/yozora-patterns.css', ROOT / 'app/static/css/style.css', ROOT / 'app/static/css/src/shell.css']


def parse_color(value):
    if value.startswith('#'):
        h = value[1:]
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1]
    return [float(x) / 255 for x in re.findall(r'[\d.]+', value)[:3]] + [float(re.findall(r'[\d.]+', value)[3]) if value.startswith('rgba') else 1]


def over(fg, bg):
    return [fg[i] * fg[3] + bg[i] * (1 - fg[3]) for i in range(3)] + [1]


def mix(a, b, p):
    return [a[i] * p + b[i] * (1 - p) for i in range(4)]


def luminance(c):
    v = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c[:3]]
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]


def ratio(a, b):
    x, y = sorted([luminance(a), luminance(b)])
    return (y + .05) / (x + .05)


def rgb(c):
    return '#' + ''.join(f'{round(min(1, max(0, x)) * 255):02X}' for x in c[:3])


def background_extremes(values, samples):
    low = min(range(len(values)), key=values.__getitem__)
    high = max(range(len(values)), key=values.__getitem__)
    return {'worst_background': rgb(samples[low]), 'best_background': rgb(samples[high])}


def saturation(c, factor):
    # CSS filter saturate matrix, applied before glass compositing.
    r, g, b = c[:3]
    grey = .213 * r + .715 * g + .072 * b
    return [min(1, max(0, grey + factor * (v - grey))) for v in (r, g, b)] + [1]


blocks = {sel.strip(): dict(re.findall(r'--([\w-]+)\s*:\s*([^;]+);', body)) for sel, body in re.findall(r'([^{}]+)\{([^{}]+)\}', TOKEN_FILE.read_text())}
base = blocks[':root']
text_tokens = set()
usages = {}
for path in CSS_FILES + [p for p in (ROOT / 'app/templates').rglob('*.html') if 'reports' not in p.relative_to(ROOT / 'app/templates').parts]:
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        for token in re.findall(r'(?<![-\w])color\s*:\s*var\(--([\w-]+)\)', line):
            text_tokens.add(token)
            usages.setdefault(token, []).append(f'{path.relative_to(ROOT)}:{line_no}')
# Dynamic --c is also used as icon foreground. Record its possible resolutions.
text_tokens.discard('c')
text_tokens |= {'critical', 'high', 'medium', 'low', 'compliant', 'partial', 'noncompliant', 'insufficient'}

rows = []
for theme in ('light', 'dark'):
    tokens = dict(base)
    if theme == 'dark':
        tokens.update(blocks['[data-theme=dark]'])
    colors = {k: parse_color(v) for k, v in tokens.items() if v.startswith(('#', 'rgb'))}
    stops = [colors['canvas-' + x] for x in ('top', 'mid', 'bottom')]
    gradient = []
    for a, b in zip(stops, stops[1:]):
        gradient.extend(mix(a, b, i / 100) for i in range(101))
    surfaces = {'canvas': gradient}
    for name in ('glass', 'glass-strong', 'solid'):
        surfaces[name] = [over(colors[name], saturation(c, 1.4 if theme == 'light' else 1.2)) for c in gradient]
    parents = dict(surfaces)
    for parent, samples in parents.items():
        for name in ('hover', 'press', 'track'):
            surfaces[f'{parent}/{name}'] = [over(colors[name], c) for c in samples]
        for name, alpha in [('field', .5 if theme == 'light' else .05), ('field-hover', .7), ('field-focus', 1 if theme == 'light' else .08), ('chip', .7 if theme == 'light' else .05), ('nav-selected', .92 if theme == 'light' else .09), ('secondary-button', .88 if theme == 'light' else .07), ('secondary-hover', 1 if theme == 'light' else .11), ('secondary-active', 1 if theme == 'light' else .05), ('file-button', .88 if theme == 'light' else .1), ('segment-selected', 1 if theme == 'light' else .14), ('kbd', 1 if theme == 'light' else .08)]:
            overlays = [[1, 1, 1, alpha]]
            if name == 'secondary-active' and theme == 'light':
                overlays = [parse_color('#F3F4F8')]
            if name == 'kbd' and theme == 'light':
                overlays += [parse_color('#F2F3F7')]
            surfaces[f'{parent}/{name}'] = [over(o, c) for o in overlays for c in samples]
        for status in ('critical', 'high', 'medium', 'low', 'compliant', 'partial', 'noncompliant', 'insufficient'):
            overlay = colors[status][:3] + [.14 if theme == 'light' else .22]
            surfaces[f'{parent}/tint-{status}'] = [over(overlay, c) for c in samples]
        surfaces[f'{parent}/mark'] = [over(colors['medium'][:3] + [.3 if theme == 'light' else .34], c) for c in samples]
    # Modal sits above a scrim rather than directly on the canvas.
    surfaces['modal-over-scrim'] = [over(colors['solid'], saturation(over([20 / 255, 24 / 255, 40 / 255, .32], c), 1.4 if theme == 'light' else 1.2)) for c in gradient]
    for token in sorted(text_tokens - {'accent-text', 'accent', 'on-accent'}):
        if token not in colors:
            continue
        for surface, backgrounds in surfaces.items():
            values = [(ratio(colors[token], c), c) for c in backgrounds]
            lo, hi = min(values, key=lambda x: x[0]), max(values, key=lambda x: x[0])
            rows.append({'theme': theme, 'accent': 'all', 'text': token, 'surface': surface, 'min': round(lo[0], 3), 'max': round(hi[0], 3), 'worst_background': rgb(lo[1]), 'best_background': rgb(hi[1]), 'scope': 'conservative candidate pairing', 'aa_normal': lo[0] >= 4.5})
    for accent in ('graphite', 'azure', 'cobalt', 'midnight', 'teal', 'violet', 'plum', 'slate'):
        ac = dict(tokens)
        ac.update(blocks[f'[data-accent={accent}]'])
        if theme == 'dark':
            ac.update(blocks[f'[data-theme=dark][data-accent={accent}]'])
        foreground = parse_color(ac['accent-text'])
        fill = parse_color(ac['accent'])
        for surface, backgrounds in surfaces.items():
            values = [ratio(foreground, c) for c in backgrounds]
            rows.append({'theme': theme, 'accent': accent, 'text': 'accent-text', 'surface': surface, 'min': round(min(values), 3), 'max': round(max(values), 3), **background_extremes(values, backgrounds), 'scope': 'conservative candidate pairing', 'aa_normal': min(values) >= 4.5})
        for parent, samples in parents.items():
            tinted = [over(foreground[:3] + [.14 if theme == 'light' else .22], c) for c in samples]
            for token in sorted(text_tokens - {'accent-text', 'accent', 'on-accent'}):
                if token not in colors:
                    continue
                values = [ratio(colors[token], c) for c in tinted]
                rows.append({'theme': theme, 'accent': accent, 'text': token, 'surface': parent + '/tint-accent', 'min': round(min(values), 3), 'max': round(max(values), 3), **background_extremes(values, tinted), 'scope': 'conservative candidate pairing; pill uses text', 'aa_normal': min(values) >= 4.5})
            soft = mix(fill, [1, 1, 1, 1], .11) if theme == 'light' else foreground[:3] + [.16]
            backgrounds = [over(soft, c) for c in samples]
            for token, fg in [('accent-text', foreground), ('text', colors['text']), ('text-2', colors['text-2']), ('muted', colors['muted'])]:
                values = [ratio(fg, c) for c in backgrounds]
                rows.append({'theme': theme, 'accent': accent, 'text': token, 'surface': parent + '/accent-soft', 'min': round(min(values), 3), 'max': round(max(values), 3), **background_extremes(values, backgrounds), 'scope': 'declared component pairing for text and accent-text; candidate for text-2 and muted', 'aa_normal': min(values) >= 4.5})
        on = parse_color(ac['on-accent'])
        for name, samples in [('primary-button', [fill, over([1, 1, 1, .14], fill)]), ('primary-kbd', [over([0, 0, 0, .08] if theme == 'dark' and accent == 'graphite' else [1, 1, 1, .16], x) for x in (fill, over([1, 1, 1, .14], fill))])]:
            values = [ratio(on, c) for c in samples]
            rows.append({'theme': theme, 'accent': accent, 'text': 'on-accent', 'surface': name, 'min': round(min(values), 3), 'max': round(max(values), 3), **background_extremes(values, samples), 'scope': 'declared component pairing', 'aa_normal': min(values) >= 4.5})
    for token, bg in [('canvas-mid', colors['text']), ('literal-white', colors['noncompliant'])]:
        fg = colors[token] if token in colors else [1, 1, 1, 1]
        value = ratio(fg, bg)
        rows.append({'theme': theme, 'accent': 'all', 'text': token, 'surface': 'tooltip' if token == 'canvas-mid' else 'destructive-button', 'min': round(value, 3), 'max': round(value, 3), 'worst_background': rgb(bg), 'best_background': rgb(bg), 'scope': 'declared component pairing', 'aa_normal': value >= 4.5})

out = {'method': 'WCAG sRGB relative luminance, source token values, alpha compositing; 101 points per gradient segment; saturate matrix on flat canvas backdrop for glass; no pixel sampling', 'limitations': ['Conservative matrix includes combinations not rendered by the app; failures alone do not establish an actual screen defect.', 'No live DOM association; source file citations locate foreground declarations, while nesting must be confirmed from rendered pages.', 'Print/export templates under app/templates/reports have a separate dynamic brand palette and are excluded from this portal token matrix.', 'Blur and nested translucent backdrops are approximated by flat gradient samples. Shadow, edge, scrim contents, image and local saturated content effects are not pixel verified.', 'Primary gradient endpoints are included. Hover accent uses oklab mixing and is not included; disabled opacity and pseudo-element geometry are not accessibility certified.', 'The undefined surface-2 token has no computable fill and falls back to inherited/transparent background.', 'Status-token rows often concern icons/dots rather than text; use 3:1 non-text threshold where applicable.'], 'text_token_sources': usages, 'dynamic_token_resolutions': {'c': ['critical', 'high', 'medium', 'low', 'compliant', 'partial', 'noncompliant', 'insufficient', 'accent-text']}, 'rows': rows}
path = ROOT / 'docs/ui-audit/contrast-data.json'
path.write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'output': str(path.relative_to(ROOT)), 'rows': len(rows), 'tokens': sorted(text_tokens), 'body': [r for r in rows if r['text'] in ('text', 'text-2', 'muted') and r['surface'] in ('canvas', 'glass', 'solid')], 'primary': [r for r in rows if r['surface'] == 'primary-button']}, indent=2))
assert abs(ratio([0, 0, 0, 1], [1, 1, 1, 1]) - 21) < 1e-10
assert abs(ratio([.5, .5, .5, 1], [.5, .5, .5, 1]) - 1) < 1e-10
assert over([1, 1, 1, .5], [0, 0, 0, 1]) == [.5, .5, .5, 1]
