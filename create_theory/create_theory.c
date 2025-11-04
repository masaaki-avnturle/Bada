```c
/* pkginstallgen.c
   Generates toy_ide_pkg containing a concrete hypothesis engine:
    - extracts text/equations from PDFs (pdftotext if available),
    - computes a deterministic pseudo-entropy,
    - extracts/normalizes equations to LaTeX, derives concrete hypothesis equations
      and produces a TeX (LaTeX) hypothesis document (explicitly labeled HYPOTHESIS / EXPLORATORY),
    - emits SymPy stubs, numeric validation harness (NumPy) and a simple CI script,
    - can optionally fetch web context when TOY_CHAT_WEB=1 and requests/bs4 available,
    - produces experimental BNF + code skeletons from language descriptions.
   Safety: never claims proofs of unresolved mathematics; every generated artifact
   contains a clear warning ("HYPOTHESIS / EXPLORATORY — NOT A PROOF").

   Build:
     gcc -O2 -o pkginstallgen pkginstallgen.c
   Run:
     ./pkginstallgen
   Then:
     bash toy_ide_pkg/bin/run.sh
     or
     python3 toy_ide_pkg/usr/bin/toy_hypothesis_engine.py
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static void ensure_dir(const char *p) {
  char cmd[1024];
  snprintf(cmd, sizeof(cmd), "mkdir -p %s", p);
  system(cmd);
}
static void write_file(const char *path, const char *content) {
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "cannot write %s\n", path); exit(1); }
  fwrite(content,1,strlen(content),f);
  fclose(f);
}
/* Write many small chunks (avoids huge C string escaping issues) */
static void write_chunks(const char *path, const char **chunks, size_t n) {
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "cannot write %s\n", path); exit(1); }
  for (size_t i=0;i<n;++i) fputs(chunks[i], f);
  fclose(f);
}

int main(void){
  system("rm -rf toy_ide_pkg");
  ensure_dir("toy_ide_pkg/bin");
  ensure_dir("toy_ide_pkg/usr/bin");
  ensure_dir("toy_ide_pkg/lib");
  ensure_dir("toy_ide_pkg/include");
  ensure_dir("toy_ide_pkg/etc");
  ensure_dir("toy_ide_pkg/ci");
  ensure_dir("toy_ide_pkg/share/doc");

  write_file("toy_ide_pkg/README.md",
"# toy_ide_pkg (hypothesis engine — safe, concrete)\n\n"
"This package generates exploratory hypothesis documents (LaTeX), SymPy stubs,\n"
"validation harnesses and experimental BNF/skeletons from PDF inputs and optional\n"
"web context. All outputs are explicitly labeled HYPOTHESIS / EXPLORATORY and are NOT proofs.\n\n"
"Run: bash bin/run.sh\n"
	     "Commands (interactive): .report, .export_hypothesis, .congen_skeleton, .run_validation, .to_sympy\n");

  write_file("toy_ide_pkg/bin/run.sh",
	     "#!/usr/bin/env bash\nset -e\nPKGROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\ncd \"$PKGROOT\"\nif [ ! -d \".venv\" ]; then python3 -m venv .venv || true; fi\n. .venv/bin/activate || true\npython3 -m pip install --upgrade pip setuptools || true\npython3 -m pip install requests beautifulsoup4 numpy scipy sympy pypandoc || true\npython3 usr/bin/toy_hypothesis_engine.py \"$@\"\n");
  system("chmod +x toy_ide_pkg/bin/run.sh");

  /* Python engine: split into safe chunks */
  const char *py_parts[] = {
    "#!/usr/bin/env python3\n\"\"\"\ntoy_hypothesis_engine.py\nGenerates concrete hypothesis artifacts (TeX, SymPy stubs, numeric harnesses)\nfrom PDF inputs and optional web context. All outputs are labeled HYPOTHESIS / EXPLORATORY.\n\"\"\"\nimport os, sys, subprocess, re, json, textwrap, hashlib\n\n# Optional web support\ntry:\n    import requests\n    from bs4 import BeautifulSoup\n    WEB_OK = True\nexcept Exception:\n    WEB_OK = False\n\ndef ensure_dir(d):\n    os.makedirs(d, exist_ok=True)\n\ndef extract_text_from_pdf(path):\n    if not os.path.exists(path):\n        return ''\n    # try pdftotext first\n    try:\n        out = subprocess.check_output(['pdftotext', path, '-'], stderr=subprocess.DEVNULL)\n        return out.decode('utf-8', errors='ignore')\n    except Exception:\n        try:\n            with open(path, 'r', encoding='utf-8', errors='ignore') as f:\n                return f.read()\n        except Exception:\n            return ''\n\ndef fetch_web_text(url, max_chars=3000):\n    if os.environ.get('TOY_CHAT_WEB') != '1' or not WEB_OK:\n        return ''\n    try:\n        r = requests.get(url, timeout=6)\n        soup = BeautifulSoup(r.text, 'html.parser')\n        parts = [p.get_text(' ', strip=True) for p in soup.find_all(['p','h1','h2','h3'])]\n        return '\\n'.join(parts)[:max_chars]\n    except Exception:\n        return ''\n\ndef sha256_hex(s):\n    return hashlib.sha256(s.encode('utf-8')).hexdigest()\n\ndef pseudo_entropy(s):\n    h = sha256_hex(s or '')\n    v = int(h[:16],16) / float(2**64-1)\n    toks = set(re.split(r'\\s+', s)) if s else set()\n    variety = min(len(toks)/500.0, 1.0)\n    length = min(len(s)/80000.0, 1.0)\n    e = 0.6*v + 0.3*variety + 0.1*length\n    return max(0.0, min(1.0, e))\n\n# Heuristic LaTeX equation extraction\nLATEX_PATTERN = re.compile(r'\\$([^$]+)\\$|\\\\\\\\\\[(.*?)\\\\\\\\\\]|\\\\\\\\begin\\{equation\\}(.+?)\\\\\\\\end\\{equation\\}', re.S)\n\ndef extract_equations(text):\n    eqs = []\n    for m in LATEX_PATTERN.finditer(text):\n        for g in m.groups():\n            if g:\n                eq = re.sub(r'\\s+', ' ', g.strip())\n                eqs.append(eq)\n    if not eqs:\n        # fallback: capture ascii-like expressions\n        cand = re.findall(r'([A-Za-z0-9_\\\\\\^{}]+\\s*=\\s*[^\\n]{10,200})', text)\n        for c in cand[:10]: eqs.append(c.strip())\n    return eqs\n\ndef normalize_to_latex(expr):\n    t = expr.replace('Gamma(', '\\\\Gamma(').replace('gamma(', '\\\\Gamma(')\n    t = t.replace('==','=').strip()\n    return t\n\ndef derive_hypotheses(extracted_eqs, context, entropy):\n    complexity = max(1, int(round(entropy*6)))\n    derived = []\n    if extracted_eqs:\n        for i, e in enumerate(extracted_eqs):\n            base = normalize_to_latex(e)\n            v1 = f\"%s \\\\quad (extracted)\\\\\\\\ G(s) := \\\\int_M K(x,s) \\\\Gamma(\\\\alpha(x,s)) \\\\; d\\\\mu(x)\" % base\n            v2 = \"H(x) := (1/N)\\\\sum_{i=1}^N \\\\phi_i(x) + \\\\prod_{i=1}^N \\\\psi_i(x)  \\\\quad (Higgs-like ansatz)\"\n            v3 = f\"D_s G(s) + \\\\lambda \\\\int_M H(x) K(x,s) d\\\\mu(x) + R_s = 0  (complexity={complexity})\"\n            derived.append({'source':base, 'variants':[v1,v2,v3]})\n    else:\n        derived.append({'source':None, 'variants':[\"\\\\Gamma-based integral: G(s)=\\\\int_M K(x,s)\\\\Gamma(\\\\alpha(x,s)) d\\\\mu(x)\",\n                                                  \"H(x) = a0 + a1\\\\sin(x) + a2 \\\\prod_j (1 + b_j(x))\",\n                                                  \"D_s G(s) + lambda \\\\int_M H K d\\\\mu + R_s = 0\"]})\n    return derived\n\ndef write_tex(title, extracted, derived, entropy, context, out_path):\n    ensure_dir(os.path.dirname(out_path) or '.')\n    with open(out_path,'w',encoding='utf-8') as f:\n        f.write('%% HYPOTHESIS / EXPLORATORY DOCUMENT\\\\n')\n        f.write('%% NOTE: Auto-generated exploratory hypotheses. NOT A PROOF.\\\\n')\n        f.write('\\\\documentclass{article}\\\\n\\\\usepackage{amsmath,amssymb}\\\\n\\\\begin{document}\\\\n')\n        f.write('\\\\title{%s (Hypothesis)}\\\\maketitle\\\\n' % title)\n        f.write('\\\\section{Context}\\\\n')\n        f.write('Pseudo-entropy: %.6f\\\\n\\\\begin{verbatim}\\\\n' % entropy)\n        f.write(context[:2000])\n        f.write('\\\\end{verbatim}\\\\n')\n        if extracted:\n            f.write('\\\\section{Extracted equations}\\\\n')\n            for i,eq in enumerate(extracted):\n                f.write('\\\\begin{equation}\\\\label{eq:ex%d}\\\\n' % i)\n                f.write(normalize_to_latex(eq) + '\\\\n')\n                f.write('\\\\end{equation}\\\\n')\n        f.write('\\\\section{Derived hypothesis equations}\\\\n')\n        for item in derived:\n            for v in item['variants']:\n                f.write('\\\\begin{equation}\\\\n'); f.write(v + '\\\\n'); f.write('\\\\end{equation}\\\\n')\n        f.write('\\\\section{Validation plan}\\\\n')\n        f.write('1) Specify M and measure; discretize.\\\\n2) Propose parametric forms; fit to data/synthetic tests.\\\\n3) Numerical convergence and residual analysis.\\\\n')\n        f.write('\\\\section{Caution}\\\\nThis is EXPLORATORY/HYPOTHESIS output. Not a proof.\\\\n')\n        f.write('\\\\end{document}\\\\n')\n    print('Wrote TeX:', out_path)\n\ndef write_sympy_stub(derived, out_py):\n    ensure_dir(os.path.dirname(out_py) or '.')\n    lines = ['# SymPy stub (heuristic) - review before use', 'from sympy import symbols, Function, integrate, gamma', 'x,s = symbols(\"x s\")', 'K=Function(\"K\")', 'alpha=Function(\"alpha\")']\n    for item in derived:\n        for v in item['variants']:\n            if 'Gamma' in v or '\\\\Gamma' in v or 'Gamma(' in v:\n                lines.append('# Heuristic: represent Gamma-based integral')\n                lines.append('G = integrate(K(x,s)*gamma(alpha(x,s)), (x,0,1))  # placeholder bounds')\n                lines.append('print(G)')\n                break\n    with open(out_py,'w',encoding='utf-8') as f: f.write('\\n'.join(lines)+'\\n')\n    print('Wrote SymPy stub:', out_py)\n\ndef write_validation_harness(out_dir):\n    ensure_dir(out_dir)\n    harness = os.path.join(out_dir,'validation_harness.py')\n    with open(harness,'w',encoding='utf-8') as f:\n        f.write('# Experimental validation harness. Replace toy components.\\n')\n        f.write('import numpy as np, math\\n')\n        f.write('def toy_kernel(x,s): return np.exp(-x*(s+1))\\n')\n        f.write('def compute_G(s,xs):\\n')\n        f.write('    K=toy_kernel(xs,s)\\n')\n        f.write('    Gamma=np.vectorize(lambda a: math.gamma(a))\\n')\n        f.write('    return np.trapz(K*Gamma(1.0+0*xs), xs)\\n')\n        f.write('if __name__==\"__main__\":\\n    xs=np.linspace(0,10,200)\\n    print([compute_G(s,xs) for s in [0.5,1.0,2.0]])\\n')\n    ci = os.path.join('toy_ide_pkg','ci','run_validation.sh')\n    with open(ci,'w',encoding='utf-8') as f:\n        f.write('#!/usr/bin/env bash\\nset -e\\nDIR=\"$(cd \"$(dirname \"$0\")\" && pwd)/..\"\\ncd \"$DIR\"\\npython3 %s > validation_output.txt 2>&1 || true\\necho \"validation_output.txt written\"\\n' % os.path.relpath(harness,'toy_ide_pkg'))\n    try: os.chmod(ci, 0755)\n    except Exception: pass\n    print('Wrote harness + CI wrapper')\n    return harness\n\ndef generate_bnf_and_skeleton(text, out_bnf, out_skel_dir):\n    ensure_dir(out_skel_dir)\n    has_func = any(w in text.lower() for w in ('function','def','procedure'))\n    has_types = any(w in text.lower() for w in ('int','float','string','bool','type'))\n    with open(out_bnf,'w',encoding='utf-8') as f:\n        f.write('/* EXPERIMENTAL BNF (auto-generated) */\\n')\n        f.write('<program> ::= <stmts>\\n<stmts> ::= <stmt> | <stmts> <stmt>\\n<stmt> ::= <assign> | <expr> | <decl>\\n')\n        f.write('<assign> ::= <identifier> \"=\" <expr> \";\"\\n')\n        if has_func:\n            f.write('<decl> ::= \"func\" <identifier> \"(\" <params> \")\" \"{\" <stmts> \"}\"\\n')\n        if has_types: f.write('<type> ::= int | float | string | bool\\n')\n    with open(out_skel_dir+\"/generated_module.py\",'w',encoding='utf-8') as f:\n        f.write('# Experimental skeleton\\ndef main():\\n    print(\"hello skeleton\")\\nif __name__==\"__main__\": main()\\n')\n    with open(out_skel_dir+\"/generated_module.c\",'w',encoding='utf-8') as f:\n        f.write('/* Experimental C skeleton */\\n#include <stdio.h>\\nint main(){ printf(\"hello\\n\"); return 0; }\\n')\n    print('Wrote BNF and skeletons')\n\n# CLI wrappers\n\ndef cmd_report(pdf):\n    t = extract_text_from_pdf(pdf)\n    e = pseudo_entropy(t)\n    meta = {'source':pdf,'chars':len(t),'pseudo_entropy':e}\n    out = pdf + '.report.json'\n    with open(out,'w',encoding='utf-8') as f: json.dump(meta,f,indent=2)\n    print('report ->', out)\n\ndef cmd_export_hypothesis(pdf,out_tex):\n    txt = extract_text_from_pdf(pdf)\n    extra = ''\n    if os.environ.get('TOY_CHAT_WEB')=='1' and WEB_OK:\n        for kw in ('Riemann','Poincare','Yang','Mills','Hodge','Navier','Stokes','Birch','Swinerton','Higgs'):\n            if kw.lower() in txt.lower(): extra += fetch_web_text('https://en.wikipedia.org/wiki/'+kw)+'\\n'\n    combined = txt + '\\n' + extra\n    e = pseudo_entropy(combined)\n    extracted = extract_equations(txt)\n    derived = derive_hypotheses(extracted, combined, e)\n    write_tex('Generated hypothesis from '+os.path.basename(pdf), extracted, derived, e, combined, out_tex)\n    write_sympy_stub(derived, out_tex + '.sympy.py')\n    harness_dir = os.path.join('toy_ide_pkg','ci','harness_'+os.path.splitext(os.path.basename(out_tex))[0])\n    write_validation_harness(harness_dir)\n    print('export_hypothesis complete')\n\ndef cmd_congen_skeleton(pdf,out_bnf):\n    txt = extract_text_from_pdf(pdf)\n    generate_bnf_and_skeleton(txt, out_bnf, out_bnf + '.skeleton')\n\ndef cmd_run_validation(eqfile, out_dir):\n    harness = os.path.join('toy_ide_pkg','ci','harness_'+os.path.splitext(os.path.basename(eqfile))[0],'validation_harness.py')\n    if not os.path.exists(harness): write_validation_harness(os.path.dirname(harness))\n    print('Run: bash toy_ide_pkg/ci/run_validation.sh')\n\n# interactive\nif __name__=='__main__':\n    if len(sys.argv)==3:\n        cmd_export_hypothesis(sys.argv[1], sys.argv[2])\n    else:\n        print('toy_hypothesis_engine. Commands: .report <pdf> | .export_hypothesis \"pdf\" \"out.tex\" | .congen_skeleton \"pdf\" \"out_bnf.txt\" | .run_validation <eq> <outdir> | .to_sympy')\n        try:\n            while True:\n                line = input('chat> ').strip()\n                if not line: continue\n                if line in ('.quit','quit','exit'): break\n                if line.startswith('.report '): cmd_report(line[len('.report '):].strip()); continue\n                if line.startswith('.export_hypothesis '):\n                    rest = line[len('.export_hypothesis '):].strip()\n                    if rest.startswith('\"'):\n                        a_end = rest.find('\"',1); a=rest[1:a_end]; b = rest[a_end+1:].strip()\n                        if b.startswith('\"'):\n                            b_end = b.find('\"',1); b=b[1:b_end]; cmd_export_hypothesis(a,b); continue\n                    print('Usage: .export_hypothesis \"in.pdf\" \"out.tex\"'); continue\n                if line.startswith('.congen_skeleton '):\n                    rest = line[len('.congen_skeleton '):].strip()\n                    if rest.startswith('\"'):\n                        a_end = rest.find('\"',1); a=rest[1:a_end]; b = rest[a_end+1:].strip()\n                        if b.startswith('\"'):\n                            b_end = b.find('\"',1); b=b[1:b_end]; cmd_congen_skeleton(a,b); continue\n                    print('Usage: .congen_skeleton \"in.pdf\" \"out_bnf.txt\"'); continue\n                if line.startswith('.run_validation '):\n                    parts = line.split();\n                    if len(parts)!=3: print('Usage: .run_validation <eqfile> <outdir>'); continue\n                    cmd_run_validation(parts[1], parts[2]); continue\n                print('Unknown command')\n        except EOFError:\n            print('\\nEXIT')\n"
  };
  size_t nparts = sizeof(py_parts)/sizeof(py_parts[0]);
  write_chunks("toy_ide_pkg/usr/bin/toy_hypothesis_engine.py", py_parts, nparts);
  system("chmod +x toy_ide_pkg/usr/bin/toy_hypothesis_engine.py");

  write_file("toy_ide_pkg/Makefile",
	     "PREFIX ?= /usr/local\nBINDIR = $(PREFIX)/bin\n.PHONY: all install uninstall clean\nall:\n\t@echo \"Nothing to build. Use 'make install' to install the hypothesis engine.\"\ninstall:\n\tinstall -d \"$(DESTDIR)$(BINDIR)\"\n\tinstall -m 755 usr/bin/toy_hypothesis_engine.py \"$(DESTDIR)$(BINDIR)/toy_hypothesis_engine\"\n\t@echo \"Installed $(DESTDIR)$(BINDIR)/toy_hypothesis_engine\"\nuninstall:\n\t-rm -f \"$(DESTDIR)$(BINDIR)/toy_hypothesis_engine\"\nclean:\n\t@echo \"clean: nothing to do\"\n");

  write_file("toy_ide_pkg/pkgmeta.json", "{ \"name\":\"toy_ide_pkg\", \"version\":\"0.8.0-hypothesis-safe\" }\n");
  write_file("toy_ide_pkg/LICENSE", "MIT\n");

  puts("Created toy_ide_pkg. Run: bash toy_ide_pkg/bin/run.sh");
  return 0;
}
```
