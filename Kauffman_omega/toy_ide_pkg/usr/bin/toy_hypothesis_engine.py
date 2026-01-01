#!/usr/bin/env python3
"""
toy_hypothesis_engine.py
Generates concrete hypothesis artifacts (TeX, SymPy stubs, numeric harnesses)
from PDF inputs and optional web context. All outputs are labeled HYPOTHESIS / EXPLORATORY.
"""
import os, sys, subprocess, re, json, textwrap, hashlib

# Optional web support
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_OK = True
except Exception:
    WEB_OK = False

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def extract_text_from_pdf(path):
    if not os.path.exists(path):
        return ''
    # try pdftotext first
    try:
        out = subprocess.check_output(['pdftotext', path, '-'], stderr=subprocess.DEVNULL)
        return out.decode('utf-8', errors='ignore')
    except Exception:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return ''

def fetch_web_text(url, max_chars=3000):
    if os.environ.get('TOY_CHAT_WEB') != '1' or not WEB_OK:
        return ''
    try:
        r = requests.get(url, timeout=6)
        soup = BeautifulSoup(r.text, 'html.parser')
        parts = [p.get_text(' ', strip=True) for p in soup.find_all(['p','h1','h2','h3'])]
        return '\n'.join(parts)[:max_chars]
    except Exception:
        return ''

def sha256_hex(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def pseudo_entropy(s):
    h = sha256_hex(s or '')
    v = int(h[:16],16) / float(2**64-1)
    toks = set(re.split(r'\s+', s)) if s else set()
    variety = min(len(toks)/500.0, 1.0)
    length = min(len(s)/80000.0, 1.0)
    e = 0.6*v + 0.3*variety + 0.1*length
    return max(0.0, min(1.0, e))

# Heuristic LaTeX equation extraction
LATEX_PATTERN = re.compile(r'\$([^$]+)\$|\\\\\[(.*?)\\\\\]|\\\\begin\{equation\}(.+?)\\\\end\{equation\}', re.S)

def extract_equations(text):
    eqs = []
    for m in LATEX_PATTERN.finditer(text):
        for g in m.groups():
            if g:
                eq = re.sub(r'\s+', ' ', g.strip())
                eqs.append(eq)
    if not eqs:
        # fallback: capture ascii-like expressions
        cand = re.findall(r'([A-Za-z0-9_\\\^{}]+\s*=\s*[^\n]{10,200})', text)
        for c in cand[:10]: eqs.append(c.strip())
    return eqs

def normalize_to_latex(expr):
    t = expr.replace('Gamma(', '\\Gamma(').replace('gamma(', '\\Gamma(')
    t = t.replace('==','=').strip()
    return t

def derive_hypotheses(extracted_eqs, context, entropy):
    complexity = max(1, int(round(entropy*6)))
    derived = []
    if extracted_eqs:
        for i, e in enumerate(extracted_eqs):
            base = normalize_to_latex(e)
            v1 = f"%s \\quad (extracted)\\\\ G(s) := \\int_M K(x,s) \\Gamma(\\alpha(x,s)) \\; d\\mu(x)" % base
            v2 = "H(x) := (1/N)\\sum_{i=1}^N \\phi_i(x) + \\prod_{i=1}^N \\psi_i(x)  \\quad (Higgs-like ansatz)"
            v3 = f"D_s G(s) + \\lambda \\int_M H(x) K(x,s) d\\mu(x) + R_s = 0  (complexity={complexity})"
            derived.append({'source':base, 'variants':[v1,v2,v3]})
    else:
        derived.append({'source':None, 'variants':["\\Gamma-based integral: G(s)=\\int_M K(x,s)\\Gamma(\\alpha(x,s)) d\\mu(x)",
                                                  "H(x) = a0 + a1\\sin(x) + a2 \\prod_j (1 + b_j(x))",
                                                  "D_s G(s) + lambda \\int_M H K d\\mu + R_s = 0"]})
    return derived

def write_tex(title, extracted, derived, entropy, context, out_path):
    ensure_dir(os.path.dirname(out_path) or '.')
    with open(out_path,'w',encoding='utf-8') as f:
        f.write('%% HYPOTHESIS / EXPLORATORY DOCUMENT\\n')
        f.write('%% NOTE: Auto-generated exploratory hypotheses. NOT A PROOF.\\n')
        f.write('\\documentclass{article}\\n\\usepackage{amsmath,amssymb}\\n\\begin{document}\\n')
        f.write('\\title{%s (Hypothesis)}\\maketitle\\n' % title)
        f.write('\\section{Context}\\n')
        f.write('Pseudo-entropy: %.6f\\n\\begin{verbatim}\\n' % entropy)
        f.write(context[:2000])
        f.write('\\end{verbatim}\\n')
        if extracted:
            f.write('\\section{Extracted equations}\\n')
            for i,eq in enumerate(extracted):
                f.write('\\begin{equation}\\label{eq:ex%d}\\n' % i)
                f.write(normalize_to_latex(eq) + '\\n')
                f.write('\\end{equation}\\n')
        f.write('\\section{Derived hypothesis equations}\\n')
        for item in derived:
            for v in item['variants']:
                f.write('\\begin{equation}\\n'); f.write(v + '\\n'); f.write('\\end{equation}\\n')
        f.write('\\section{Validation plan}\\n')
        f.write('1) Specify M and measure; discretize.\\n2) Propose parametric forms; fit to data/synthetic tests.\\n3) Numerical convergence and residual analysis.\\n')
        f.write('\\section{Caution}\\nThis is EXPLORATORY/HYPOTHESIS output. Not a proof.\\n')
        f.write('\\end{document}\\n')
    print('Wrote TeX:', out_path)

def write_sympy_stub(derived, out_py):
    ensure_dir(os.path.dirname(out_py) or '.')
    lines = ['# SymPy stub (heuristic) - review before use', 'from sympy import symbols, Function, integrate, gamma', 'x,s = symbols("x s")', 'K=Function("K")', 'alpha=Function("alpha")']
    for item in derived:
        for v in item['variants']:
            if 'Gamma' in v or '\\Gamma' in v or 'Gamma(' in v:
                lines.append('# Heuristic: represent Gamma-based integral')
                lines.append('G = integrate(K(x,s)*gamma(alpha(x,s)), (x,0,1))  # placeholder bounds')
                lines.append('print(G)')
                break
    with open(out_py,'w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
    print('Wrote SymPy stub:', out_py)

def write_validation_harness(out_dir):
    ensure_dir(out_dir)
    harness = os.path.join(out_dir,'validation_harness.py')
    with open(harness,'w',encoding='utf-8') as f:
        f.write('# Experimental validation harness. Replace toy components.\n')
        f.write('import numpy as np, math\n')
        f.write('def toy_kernel(x,s): return np.exp(-x*(s+1))\n')
        f.write('def compute_G(s,xs):\n')
        f.write('    K=toy_kernel(xs,s)\n')
        f.write('    Gamma=np.vectorize(lambda a: math.gamma(a))\n')
        f.write('    return np.trapz(K*Gamma(1.0+0*xs), xs)\n')
        f.write('if __name__=="__main__":\n    xs=np.linspace(0,10,200)\n    print([compute_G(s,xs) for s in [0.5,1.0,2.0]])\n')
    ci = os.path.join('toy_ide_pkg','ci','run_validation.sh')
    with open(ci,'w',encoding='utf-8') as f:
        f.write('#!/usr/bin/env bash\nset -e\nDIR="$(cd "$(dirname "$0")" && pwd)/.."\ncd "$DIR"\npython3 %s > validation_output.txt 2>&1 || true\necho "validation_output.txt written"\n' % os.path.relpath(harness,'toy_ide_pkg'))
    try: os.chmod(ci, o755)
    except Exception: pass
    print('Wrote harness + CI wrapper')
    return harness

def generate_bnf_and_skeleton(text, out_bnf, out_skel_dir):
    ensure_dir(out_skel_dir)
    has_func = any(w in text.lower() for w in ('function','def','procedure'))
    has_types = any(w in text.lower() for w in ('int','float','string','bool','type'))
    with open(out_bnf,'w',encoding='utf-8') as f:
        f.write('/* EXPERIMENTAL BNF (auto-generated) */\n')
        f.write('<program> ::= <stmts>\n<stmts> ::= <stmt> | <stmts> <stmt>\n<stmt> ::= <assign> | <expr> | <decl>\n')
        f.write('<assign> ::= <identifier> "=" <expr> ";"\n')
        if has_func:
            f.write('<decl> ::= "func" <identifier> "(" <params> ")" "{" <stmts> "}"\n')
        if has_types: f.write('<type> ::= int | float | string | bool\n')
    with open(out_skel_dir+"/generated_module.py",'w',encoding='utf-8') as f:
        f.write('# Experimental skeleton\ndef main():\n    print("hello skeleton")\nif __name__=="__main__": main()\n')
    with open(out_skel_dir+"/generated_module.c",'w',encoding='utf-8') as f:
        f.write('/* Experimental C skeleton */\n#include <stdio.h>\nint main(){ printf("hello\n"); return 0; }\n')
    print('Wrote BNF and skeletons')

# CLI wrappers

def cmd_report(pdf):
    t = extract_text_from_pdf(pdf)
    e = pseudo_entropy(t)
    meta = {'source':pdf,'chars':len(t),'pseudo_entropy':e}
    out = pdf + '.report.json'
    with open(out,'w',encoding='utf-8') as f: json.dump(meta,f,indent=2)
    print('report ->', out)

def cmd_export_hypothesis(pdf,out_tex):
    txt = extract_text_from_pdf(pdf)
    extra = ''
    if os.environ.get('TOY_CHAT_WEB')=='1' and WEB_OK:
        for kw in ('Riemann','Poincare','Yang','Mills','Hodge','Navier','Stokes','Birch','Swinerton','Higgs'):
            if kw.lower() in txt.lower(): extra += fetch_web_text('https://en.wikipedia.org/wiki/'+kw)+'\n'
    combined = txt + '\n' + extra
    e = pseudo_entropy(combined)
    extracted = extract_equations(txt)
    derived = derive_hypotheses(extracted, combined, e)
    write_tex('Generated hypothesis from '+os.path.basename(pdf), extracted, derived, e, combined, out_tex)
    write_sympy_stub(derived, out_tex + '.sympy.py')
    harness_dir = os.path.join('toy_ide_pkg','ci','harness_'+os.path.splitext(os.path.basename(out_tex))[0])
    write_validation_harness(harness_dir)
    print('export_hypothesis complete')

def cmd_congen_skeleton(pdf,out_bnf):
    txt = extract_text_from_pdf(pdf)
    generate_bnf_and_skeleton(txt, out_bnf, out_bnf + '.skeleton')

def cmd_run_validation(eqfile, out_dir):
    harness = os.path.join('toy_ide_pkg','ci','harness_'+os.path.splitext(os.path.basename(eqfile))[0],'validation_harness.py')
    if not os.path.exists(harness): write_validation_harness(os.path.dirname(harness))
    print('Run: bash toy_ide_pkg/ci/run_validation.sh')

# interactive
if __name__=='__main__':
    if len(sys.argv)==3:
        cmd_export_hypothesis(sys.argv[1], sys.argv[2])
    else:
        print('toy_hypothesis_engine. Commands: .report <pdf> | .export_hypothesis "pdf" "out.tex" | .congen_skeleton "pdf" "out_bnf.txt" | .run_validation <eq> <outdir> | .to_sympy')
        try:
            while True:
                line = input('chat> ').strip()
                if not line: continue
                if line in ('.quit','quit','exit'): break
                if line.startswith('.report '): cmd_report(line[len('.report '):].strip()); continue
                if line.startswith('.export_hypothesis '):
                    rest = line[len('.export_hypothesis '):].strip()
                    if rest.startswith('"'):
                        a_end = rest.find('"',1); a=rest[1:a_end]; b = rest[a_end+1:].strip()
                        if b.startswith('"'):
                            b_end = b.find('"',1); b=b[1:b_end]; cmd_export_hypothesis(a,b); continue
                    print('Usage: .export_hypothesis "in.pdf" "out.tex"'); continue
                if line.startswith('.congen_skeleton '):
                    rest = line[len('.congen_skeleton '):].strip()
                    if rest.startswith('"'):
                        a_end = rest.find('"',1); a=rest[1:a_end]; b = rest[a_end+1:].strip()
                        if b.startswith('"'):
                            b_end = b.find('"',1); b=b[1:b_end]; cmd_congen_skeleton(a,b); continue
                    print('Usage: .congen_skeleton "in.pdf" "out_bnf.txt"'); continue
                if line.startswith('.run_validation '):
                    parts = line.split();
                    if len(parts)!=3: print('Usage: .run_validation <eqfile> <outdir>'); continue
                    cmd_run_validation(parts[1], parts[2]); continue
                print('Unknown command')
        except EOFError:
            print('\nEXIT')
