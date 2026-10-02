"""Parse design/yozora-tokens.css into design/tokens.json, or check they match.
Usage: python design/tokens_tool.py write | check   (check exits 1 on drift)"""
import json, re, sys, pathlib
D = pathlib.Path(__file__).parent
def parse(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = {}
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        sel = ' '.join(sel.split())
        out[sel] = dict((k.strip(), v.strip()) for k, v in re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', body))
    return out
def main(mode):
    cur = parse((D / 'yozora-tokens.css').read_text())
    path = D / 'tokens.json'
    if mode == 'write':
        path.write_text(json.dumps(cur, indent=2) + '\n'); print('wrote', path)
    else:
        saved = json.loads(path.read_text())
        if saved != cur:
            print('DRIFT between tokens.json and yozora-tokens.css'); sys.exit(1)
        print('tokens match')
main(sys.argv[1] if len(sys.argv) > 1 else 'check')
