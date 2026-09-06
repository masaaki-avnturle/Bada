#!/usr/bin/env python3
"""usr/lang/verifier.py
Simple verifier:
  python3 usr/lang/verifier.py <equations.txt> <out_dir>
Reads lines with '=' from equations.txt, attempts sympify on both sides,
computes diff = simplify(L - R), and performs numeric sampling.
Outputs JSON to <out_dir>/verification.json
"""
import sys, os, json, random
try:
    import sympy as sp
except Exception:
    sp = None

def read_eqs(path):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if '=' in line]

def split_eq(line):
    a, _, b = line.partition('=')
    return a.strip(), b.strip()

def sample_and_check(expr, samples=8):
    syms = list(expr.free_symbols)
    checks = []
    ok_all = True
    for _ in range(samples):
        vals = {s: random.uniform(0.1, 3.0) for s in syms}
        try:
            v = expr.subs(vals)
            v = float(sp.N(v, 20)) if sp is not None else None
            ok = abs(v) < 1e-8 if v is not None else False
            checks.append({'vals': {str(k): float(vals[k]) for k in vals}, 'value': v, 'ok': ok})
            if not ok: ok_all = False
        except Exception as e:
            checks.append({'vals': {str(k): float(vals[k]) for k in vals} if 'vals' in locals() else {}, 'value': str(e), 'ok': False})
            ok_all = False
    return ok_all, checks

def main():
    if len(sys.argv) < 3:
        print('usage: verifier.py <equations.txt> <out_dir>')
        return 2
    inpath = sys.argv[1]; outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    lines = read_eqs(inpath)
    results = {'accepted': [], 'rejected': []}
    for line in lines:
        Ls, Rs = split_eq(line)
        try:
            if sp is None:
                results['rejected'].append({'equation': line, 'error': 'sympy not installed'})
                continue
            L = sp.sympify(Ls)
            R = sp.sympify(Rs)
            diff = sp.simplify(L - R)
            symbolic_ok = diff == 0
            numeric_ok, checks = sample_and_check(diff)
            entry = {'equation': line, 'symbolic': str(diff), 'numeric_ok': numeric_ok, 'checks': checks}
            if symbolic_ok or numeric_ok:
                results['accepted'].append(entry)
            else:
                results['rejected'].append(entry)
        except Exception as e:
            results['rejected'].append({'equation': line, 'error': str(e)})
    outpath = os.path.join(outdir, 'verification.json')
    with open(outpath, 'w', encoding='utf-8') as fo:
        json.dump(results, fo, ensure_ascii=False, indent=2)
    print('Wrote', outpath)

if __name__ == '__main__':
    sys.exit(main())
