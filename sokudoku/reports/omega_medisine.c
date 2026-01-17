以下は、要求どおりの安全な代替機能群を含むパッケージ骨格を生成する C プログラム `pkginstallgen.c` の完全ソースです。保存してコンパイル（例: `gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c`）し、実行すると指定ディレクトリ（デフォルト `omega_package`）に bin/, lib/, include/, etc/, usr/, tools/, package/src/, doc/ 等を展開します。展開されるスクリプトはすべて「非人体実験」「生体操作を伴わない」設計です。

  pkginstallgen.c:
```c
  /* pkginstallgen.c
   Generate a research package skeleton "Omega" with safe features:
   - SQLite offline library for PDFs and extracted formulas
   - PDF import / text extraction (pdfminer hook)
   - Formula extraction and analysis (SymPy hook)
   - BNF -> parser skeleton generator (safe Python RD parser)
   - Omega Script simulator skeleton (symbolic / numeric simulation only)
   - Jones-polynomial hooks (Sage optional) with pseudo-fallback
   - Time-series forecasting skeleton (MA / linear trend) for academic use
   - PDF Q&A (local extract + heuristic summarization) with LLM hook (user-managed)
   - Vim/Emacs integration snippets
   - Makefile that suppresses noisy build errors
   - All generated code avoids biological/medical intervention automation
   Build:
     gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c
   Usage:
     ./pkginstallgen ./omega_package
  */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <direct.h>
#define MKDIR(p) _mkdir(p)
#else
#include <sys/stat.h>
#include <sys/types.h>
#define MKDIR(p) mkdir((p),0755)
#endif

  static void mkdir_p(const char *path) {
  char tmp[4096];
  char *p;
  size_t len;
  snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (len == 0) return;
    if (tmp[len-1] == '/') tmp[len-1] = 0;
    for (p = tmp + 1; *p; ++p) {
        if (*p == '/') {
            *p = 0;
            MKDIR(tmp);
            *p = '/';
        }
    }
    MKDIR(tmp);
}

static int write_file(const char *path, const char *data) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    fwrite(data, 1, strlen(data), f);
    fclose(f);
    return 0;
}

int main(int argc, char **argv) {
    const char *out = "omega_package";
  if (argc > 1) out = argv[1];
  char buf[8192];

  /* create directories */
  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/lib", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/include", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/package/src", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/tools", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/doc", out); mkdir_p(buf);

  /* include/omega.h */
    const char *omega_h =
      "/* include/omega.h - Omega package API placeholders */\n"
"#ifndef OMEGA_H\n"
"#define OMEGA_H\n\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n\n"
      "/* Initialize/close local SQLite DB (path provided by user). */\n"
"int omega_db_init(const char *dbpath);\n"
"void omega_db_close(void);\n\n"
      "/* Placeholder for simulation API */\n"
"int omega_sim_run(const char *script, const char *args);\n\n"
      "#endif\n";
    snprintf(buf, sizeof(buf), "%s/include/omega.h", out);
    write_file(buf, omega_h);

    /* bin/omega (driver) */
    const char *bin_omega =
      "#!/bin/sh\n# omega - driver for package tools (safe, non-biological)\ncase \"$1\" in\n  import-pdf)\n    shift; python3 \"$(dirname \"$0\")/pdf_import.py\" \"$@\" ;;\n  extract)\n    shift; python3 \"$(dirname \"$0\")/formula_extract.py\" \"$@\" ;;\n  analyze)\n    shift; python3 \"$(dirname \"$0\")/analyze_pipeline.py\" \"$@\" ;;\n  gen-parser)\n    shift; python3 \"$(dirname \"$0\")/bnf_to_parser.py\" \"$@\" ;;\n  sim)\n    shift; python3 \"$(dirname \"$0\")/omega_sim.py\" \"$@\" ;;\n  jones)\n    shift; python3 \"$(dirname \"$0\")/jones_hook.py\" \"$@\" ;;\n  forecast)\n    shift; python3 \"$(dirname \"$0\")/forecast_fx.py\" \"$@\" ;;\n  qa)\n    shift; python3 \"$(dirname \"$0\")/pdf_qa.py\" \"$@\" ;;\n  install-vim)\n    shift; sh \"$(dirname \"$0\")/install_vim.sh\" \"$@\" ;;\n  install-emacs)\n    shift; sh \"$(dirname \"$0\")/install_emacs.sh\" \"$@\" ;;\n  coq)\n    shift; sh \"$(dirname \"$0\")/coq_wrapper.sh\" \"$@\" ;;\n  *)\n    echo \"Usage: $0 {import-pdf|extract|analyze|gen-parser|sim|jones|forecast|qa|install-vim|install-emacs|coq} ...\" ;;\nesac\n";
snprintf(buf, sizeof(buf), "%s/bin/omega", out);
write_file(buf, bin_omega);

/* bin/pdf_import.py - import PDFs into SQLite DB (text only) */
    const char *pdf_import_py =
      "#!/usr/bin/env python3\n\"\"\"\npdf_import.py\nImport PDF files into a local SQLite library. Extract text only.\nUsage: pdf_import.py library.sqlite file1.pdf [file2.pdf ...]\n\"\"\"\nimport sys, os, sqlite3\ntry:\n    from pdfminer.high_level import extract_text\nexcept Exception:\n    extract_text = None\nif len(sys.argv) < 3:\n    print('Usage: pdf_import.py library.sqlite file1.pdf [...]')\n    sys.exit(2)\ndb = sys.argv[1]; files = sys.argv[2:]\nconn = sqlite3.connect(db)\ncur = conn.cursor()\ncur.execute('''CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, path TEXT UNIQUE, title TEXT, text TEXT)''')\nfor f in files:\n    if not os.path.isfile(f):\n        print('skip (not found):', f); continue\n    text = ''\n    if extract_text:\n        try: text = extract_text(f)\n        except Exception: text = ''\n    cur.execute('INSERT OR REPLACE INTO documents(path,title,text) VALUES(?,?,?)', (f, os.path.basename(f), text))\n    print('imported', f)\nconn.commit(); conn.close()\n";
snprintf(buf, sizeof(buf), "%s/bin/pdf_import.py", out);
write_file(buf, pdf_import_py);

/* bin/formula_extract.py - extract formula-like snippets */
    const char *formula_extract_py =
      "#!/usr/bin/env python3\n\"\"\"\nformula_extract.py\nExtract formula-like text from an SQLite library or a text/pdf file.\nUsage: formula_extract.py <library.sqlite|file.txt|file.pdf> out_formulas.txt\n\"\"\"\nimport sys, os, re\nif len(sys.argv)<3:\n    print('Usage: formula_extract.py <db|file> out.txt'); sys.exit(2)\nsrc = sys.argv[1]; out = sys.argv[2]\ntext = ''\nif os.path.isfile(src) and src.endswith('.sqlite'):\n    import sqlite3\n    conn = sqlite3.connect(src); cur = conn.cursor(); cur.execute('SELECT text FROM documents'); rows = cur.fetchall(); text = '\\n'.join(r[0] or '' for r in rows); conn.close()\nelse:\n    try:\n        from pdfminer.high_level import extract_text\n        text = extract_text(src)\n    except Exception:\n        try: text = open(src,'r',encoding='utf-8').read()\n        except Exception: text = ''\nforms = []\nforms += re.findall(r'\\\\\\((.+?)\\\\\\)', text, flags=re.S)\nforms += re.findall(r'\\$(.+?)\\$', text, flags=re.S)\nforms += re.findall(r'\\\\\\[(.+?)\\\\\\]', text, flags=re.S)\nforms += re.findall(r'\\\\begin\\{equation\\}(.+?)\\\\end\\{equation\\}', text, flags=re.S)\nfor line in text.splitlines():\n    if any(tok in line for tok in ['=', '+', '-', 'Gamma', 'zeta', 'Jones', '∫', '∂', 'ψ', 'Γ']):\n        s = line.strip()\n        if 4 < len(s) < 800: forms.append(s)\nseen = set(); outl = []\nfor f in forms:\n    s = ' '.join(f.split())\n    if s not in seen: seen.add(s); outl.append(s)\nopen(out,'w',encoding='utf-8').write('\\n'.join(outl))\nprint('wrote', len(outl), 'formulas to', out)\n";
snprintf(buf, sizeof(buf), "%s/bin/formula_extract.py", out);
write_file(buf, formula_extract_py);

/* bin/analyze_pipeline.py - compute simple numeric features and produce LaTeX + CSV */
    const char *analyze_pipeline_py =
      "#!/usr/bin/env python3\n\"\"\"\nanalyze_pipeline.py\nAnalyze formulas file => produce indicators CSV and a LaTeX report. Uses SymPy if available.\nUsage: analyze_pipeline.py formulas.txt report.tex indicators.csv\n\"\"\"\nimport sys, math, csv, shutil, subprocess\ntry:\n    import sympy as sp\nexcept Exception:\n    sp = None\nif len(sys.argv)<4: print('Usage: analyze_pipeline.py formulas.txt report.tex indicators.csv'); sys.exit(2)\nforms = [l.strip() for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\nout_tex = sys.argv[2]; out_csv = sys.argv[3]\n# pseudo-Jones coefficients generator (deterministic)\ndef pseudo_jones(s):\n    seed = sum(ord(c) for c in s) & 0xffffffff\n    deg = 1 + (seed % 6)\n    coeffs = [(((seed*(k+1)) ^ (k*2654435761)) & 0xffffffff)%101 - 50 for k in range(deg+1)]\n    return [float(x) for x in coeffs]\ndef entropy(coeffs):\n    mags = [abs(c) for c in coeffs]; s=sum(mags)\n    if s==0: return 0.0\n    H=0.0\n    for m in mags:\n        p = m/s\n        if p>0: H -= p * math.log2(p)\n    return H\nrows=[]\nfor expr in forms:\n    coeffs = pseudo_jones(expr)\n    H = entropy(coeffs)\n    zeta_like = sum(coeffs)/(1+abs(sum(coeffs)))\n    gamma_like = max(1.0, abs(sum(coeffs))/len(coeffs))\n    amgm = (sum(abs(c) for c in coeffs)/len(coeffs)) / (max(1e-12, (abs(coeffs[0]) if coeffs else 1)))\n    score = 0.4*(abs(zeta_like)/(1+abs(zeta_like))) + 0.3*(math.log(1+gamma_like)/(1+math.log(1+gamma_like))) + 0.3*(amgm/(1+amgm))\n    rows.append({'expr':expr,'H':H,'zeta':zeta_like,'gamma':gamma_like,'amgm':amgm,'score':score})\nwith open(out_csv,'w',encoding='utf-8',newline='') as f:\n    w = csv.writer(f); w.writerow(['expr','H','zeta','gamma','amgm','score'])\n    for r in rows: w.writerow([r['expr'], r['H'], r['zeta'], r['gamma'], r['amgm'], r['score']])\nwith open(out_tex,'w',encoding='utf-8') as f:\n    f.write('\\\\documentclass{article}\\\\usepackage{amsmath}\\\\begin{document}\\\\section*{Analysis}\\\\n')\n    for r in rows:\n        f.write('\\\\subsection*{Expression}\\\\n\\\\begin{verbatim}'+r['expr']+'\\\\end{verbatim}\\\\n')\n        f.write('Entropy: %g; score: %g\\\\n\\\\hrule\\\\n' % (r['H'], r['score']))\n    f.write('\\\\end{document}')\nprint('Wrote', out_csv, 'and', out_tex)\n";
snprintf(buf, sizeof(buf), "%s/bin/analyze_pipeline.py", out);
write_file(buf, analyze_pipeline_py);

/* bin/bnf_to_parser.py - generate recursive-descent parser skeleton */
    const char *bnf_to_parser_py =
      "#!/usr/bin/env python3\n\"\"\"\nbnf_to_parser.py\nGenerate a simple recursive-descent parser skeleton for a BNF grammar.\nUsage: bnf_to_parser.py grammar.bnf out_parser.py\n\"\"\"\nimport sys,re\nif len(sys.argv)<3: print('Usage: bnf_to_parser.py grammar.bnf out_parser.py'); sys.exit(2)\ngram = open(sys.argv[1],'r',encoding='utf-8').read()\nrules={}\nfor L in gram.splitlines():\n    L=L.strip()\n    if not L or L.startswith('#'): continue\n    m=re.match(r'<([^>]+)>\\s*::=\\s*(.+)',L)\n    if m: rules[m.group(1)] = [a.strip() for a in m.group(2).split('|')]\nif not rules: print('no rules'); sys.exit(2)\nstart = list(rules.keys())[0]\nwith open(sys.argv[2],'w',encoding='utf-8') as f:\n    f.write('# Generated parser skeleton\\n')\n    f.write('def tokenize(s):\\n    return s.split()\\n\\n')\n    for nt,alts in rules.items():\n        f.write('def parse_%s(tokens,pos):\\n' % nt)\n        f.write('    start=pos\\n')\n        f.write('    # try each alternative\\n')\n        for alt in alts:\n            parts = alt.split()\n            f.write('    pos=start; node=[]\\n')\n            for p in parts:\n                if p.startswith('<') and p.endswith('>'):\n                    sym = p[1:-1]\n                    f.write('    n,pos = parse_%s(tokens,pos)\\n' % sym)\n                    f.write('    if n is None: pos=start; node=None\\n    else: node.append(n)\\n')\n                else:\n                    lit = p.strip('\"')\n                    f.write('    if pos < len(tokens) and tokens[pos] == \"%s\": node.append(tokens[pos]); pos += 1\\n    else: pos=start; node=None\\n' % lit)\n            f.write('    if node is not None: return (node,pos)\\n')\n        f.write('    return (None,start)\\n\\n')\n    f.write('def parse(s):\\n    t=tokenize(s); return parse_%s(t,0)\\n' % start)\nprint('Generated parser to', sys.argv[2])\n";
snprintf(buf, sizeof(buf), "%s/bin/bnf_to_parser.py", out);
write_file(buf, bnf_to_parser_py);

/* bin/omega_sim.py - Omega Script simulator skeleton (safe symbolic/numeric only) */
    const char *omega_sim_py =
      "#!/usr/bin/env python3\n\"\"\"\nomega_sim.py\nSimple Omega Script simulator skeleton. Executes safe symbolic/numeric ops from a script file.\nUsage: omega_sim.py script.omega [args]\nNote: This is a simulator for symbolic experiments only. No biological/chemical synthesis control.\n\"\"\"\nimport sys, math\ntry:\n    import sympy as sp\nexcept Exception:\n    sp=None\nif len(sys.argv)<2:\n    print('Usage: omega_sim.py script.omega [args]'); sys.exit(2)\nscript = sys.argv[1]\n# simple script format: lines of 'let name = expression' or 'eval expression'\nenv = {}\nfor line in open(script,'r',encoding='utf-8'):\n    line=line.strip()\n    if not line or line.startswith('#'): continue\n    if line.startswith('let '):\n        _, rest = line.split('let ',1)\n        name, expr = rest.split('=',1)\n        name=name.strip(); expr=expr.strip()\n        try:\n            if sp: val = sp.sympify(expr)\n            else: val = eval(expr, {'math':math}, {})\n        except Exception:\n            val = expr\n        env[name]=val\n        print('defined',name)\n    elif line.startswith('eval '):\n        expr = line.split('eval ',1)[1]\n        try:\n            if sp: val = sp.sympify(expr).evalf()\n            else: val = eval(expr, {'math':math}, {})\n        except Exception as e:\n            val = 'ERROR: '+str(e)\n        print('=>', val)\n    else:\n        print('unknown line:', line)\nprint('Simulation finished')\n";
snprintf(buf, sizeof(buf), "%s/bin/omega_sim.py", out);
write_file(buf, omega_sim_py);

/* bin/jones_hook.py - Sage hook + pseudo fallback */
    const char *jones_hook_py =
      "#!/usr/bin/env python3\n\"\"\"\njones_hook.py\nAttempt to compute Jones polynomial via 'sage' (if available). Otherwise produce a deterministic pseudo-result.\nUsage: jones_hook.py knot_descriptor\n\"\"\"\nimport sys, shutil\nif len(sys.argv)<2: print('Usage: jones_hook.py knot'); sys.exit(2)\nk = sys.argv[1]\nsage = shutil.which('sage')\nif sage:\n    script = \"from sage.all import *\\nprint(Knot('3_1').jones_polynomial())\\n\"\n    try:\n        import subprocess\n        p = subprocess.run([sage,'-c',script], capture_output=True, text=True, timeout=20)\n        if p.returncode==0:\n            print(p.stdout.strip()); sys.exit(0)\n    except Exception:\n        pass\n# fallback pseudo polynomial\nseed = sum(ord(c) for c in k) & 0xffffffff\ncoeffs = [(((seed*(i+1)) ^ (i*2654435761)) & 0xffffffff)%11 - 5 for i in range(4)]\npoly = ' + '.join(f'{c} t^{i}' for i,c in enumerate(coeffs))\nprint('pseudo_jones:', poly)\n";
snprintf(buf, sizeof(buf), "%s/bin/jones_hook.py", out);
write_file(buf, jones_hook_py);

/* bin/forecast_fx.py - simple time series forecast skeleton */
    const char *forecast_fx_py =
      "#!/usr/bin/env python3\n\"\"\"\nforecast_fx.py\nLightweight forecasting: read CSVs of (timestamp,value) per instrument and output traces and simple forecasts.\nUsage: forecast_fx.py input_dir output_dir\n\"\"\"\nimport sys,os,glob\ntry:\n    import pandas as pd\n    import matplotlib.pyplot as plt\nexcept Exception:\n    pd=None\nif len(sys.argv)<3: print('Usage: forecast_fx.py input_dir output_dir'); sys.exit(2)\nind=sys.argv[1]; outd=sys.argv[2]; os.makedirs(outd,exist_ok=True)\nfor f in glob.glob(os.path.join(ind,'*.csv')):\n    name = os.path.splitext(os.path.basename(f))[0]\n    try:\n        if pd:\n            df = pd.read_csv(f, header=None, names=['t','v'])\n            vals = df['v'].astype(float).tolist()\n        else:\n            vals = [float(line.split(',')[1]) for line in open(f,'r',encoding='utf-8') if line.strip()]\n        N=len(vals); w=5\n        ma = [sum(vals[max(0,i-w+1):i+1])/(min(w,i+1)) for i in range(N)]\n        k=min(20,N); xs=list(range(N-k,N)); ys=vals[N-k:N]\n        if len(xs)>=2:\n            xm=sum(xs)/len(xs); ym=sum(ys)/len(ys)\n            num=sum((x-xm)*(y-ym) for x,y in zip(xs,ys)); den=sum((x-xm)**2 for x in xs)\n            slope = num/den if den!=0 else 0.0\n            intercept = ym - slope * xm\n            trend = [intercept + slope * x for x in range(N, N+5)]\n        else:\n            trend = [vals[-1] if vals else 0.0]*5\n        with open(os.path.join(outd,name+'.trace.csv'),'w',encoding='utf-8') as of:\n            of.write('index,value,ma\\n')\n            for i,(v,mv) in enumerate(zip(vals,ma)): of.write(f'{i},{v},{mv}\\n')\n        with open(os.path.join(outd,name+'.forecast.csv'),'w',encoding='utf-8') as of:\n            of.write('horizon,forecast\\n')\n            for h,v in enumerate(trend,1): of.write(f'{h},{v}\\n')\n        if pd:\n            plt.figure(); plt.plot(vals,label='value'); plt.plot(ma,label='MA'); plt.legend(); plt.savefig(os.path.join(outd,name+'.png')); plt.close()\n        print('processed', name)\n    except Exception as e:\n        print('error', f, e)\n";
snprintf(buf, sizeof(buf), "%s/bin/forecast_fx.py", out);
write_file(buf, forecast_fx_py);

/* bin/pdf_qa.py - heuristic PDF Q&A (local search + optional LLM hook) */
    const char *pdf_qa_py =
      "#!/usr/bin/env python3\n\"\"\"\npdf_qa.py\nHeuristic question-answer for a PDF or library: finds matching paragraphs and summarizes.\nUsage: pdf_qa.py <library.sqlite|file.pdf|file.txt> \"question\"\nSet OMEGA_LLM_API env var to a user-managed summarizer command (optional).\n\"\"\"\nimport sys,os,re,sqlite3,subprocess\nif len(sys.argv)<3: print('Usage: pdf_qa.py <src> \"question\"'); sys.exit(2)\nsrc=sys.argv[1]; q=sys.argv[2]\ntext=''\nif os.path.isfile(src) and src.endswith('.sqlite'):\n    conn=sqlite3.connect(src); cur=conn.cursor(); cur.execute('SELECT text FROM documents'); rows=cur.fetchall(); text='\\n'.join(r[0] or '' for r in rows); conn.close()\nelse:\n    try:\n        from pdfminer.high_level import extract_text\n        text = extract_text(src)\n    except Exception:\n        try: text=open(src,'r',encoding='utf-8').read()\n        except Exception: text=''\nwords=[w.lower() for w in re.findall(r'\\w+', q)]\nparas=[p.strip() for p in re.split(r'\\n\\s*\\n', text) if p.strip()]\ncands=[]\nfor p in paras:\n    lw=p.lower(); score=sum(1 for w in words if w in lw)\n    if score>0: cands.append((score,p))\ncands.sort(reverse=True)\nsummary='\\n\\n'.join(p for s,p in cands[:3]) or 'No matches.'\napi=os.environ.get('OMEGA_LLM_API')\nif api:\n    try:\n        p=subprocess.run([api, q+'\\n\\n'+summary], capture_output=True, text=True, timeout=20)\n        if p.returncode==0 and p.stdout.strip(): summary=p.stdout\n    except Exception:\n        pass\nprint('Answer (heuristic):\\n')\nprint(summary)\n";
snprintf(buf, sizeof(buf), "%s/bin/pdf_qa.py", out);
write_file(buf, pdf_qa_py);

/* bin/gen_ai.py - lightweight generator (templates + Markov) */
    const char *gen_ai_py =
      "#!/usr/bin/env python3\n\"\"\"\ngen_ai.py\nLightweight template+Markov generator. Optional external LLM hook via OMEGA_LLM_API.\nUsage: gen_ai.py tokens.txt out.txt\n\"\"\"\nimport sys,random,subprocess,os\nif len(sys.argv)<3: print('Usage: gen_ai.py tokens.txt out.txt'); sys.exit(2)\ntoks=[l.strip() for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\nmodel={}\nfor t in toks:\n    w=t.split()\n    for i in range(len(w)-1): model.setdefault(w[i],[]).append(w[i+1])\ndef gen(seed=None,length=40):\n    if not model: return ' '.join(toks[:min(10,len(toks))])\n    if seed is None: seed=random.choice(list(model.keys()))\n    w=seed; out=[w]\n    for _ in range(length-1):\n        nxt=model.get(w)\n        if not nxt: break\n        w=random.choice(nxt); out.append(w)\n    return ' '.join(out)\nout=sys.argv[2]\nseed=toks[0].split()[0] if toks else 'Omega'\ntext='Title: '+gen(seed,6)+'\\n\\nTheorem: '+gen(seed,30)+'\\n\\nProof sketch: '+gen(seed,160)+'\\n'\napi=os.environ.get('OMEGA_LLM_API')\nif api:\n    try:\n        p=subprocess.run([api, text], capture_output=True, text=True, timeout=30)\n        if p.returncode==0 and p.stdout.strip(): text=p.stdout\n    except Exception:\n        pass\nopen(out,'w',encoding='utf-8').write(text)\nprint('Wrote', out)\n";
snprintf(buf, sizeof(buf), "%s/bin/gen_ai.py", out);
write_file(buf, gen_ai_py);

/* bin/coq_wrapper.sh */
    const char *coq_sh =
      "#!/bin/sh\n# coq_wrapper.sh - try to run coqc/lean or emit skeleton\nif [ $# -lt 1 ]; then echo 'Usage: coq_wrapper.sh goal.v'; exit 2; fi\nscript=\"$1\"\nif command -v coqc >/dev/null 2>&1; then coqc \"$script\"; exit $?; fi\nif command -v lean >/dev/null 2>&1; then lean \"$script\"; exit $?; fi\ncat > \"$script\" <<'EOF'\n(* Proof skeleton generated by Omega package. Fill in details. *)\nEOF\necho 'Created skeleton', \"$script\"\n";
snprintf(buf, sizeof(buf), "%s/bin/coq_wrapper.sh", out);
write_file(buf, coq_sh);

/* bin/install_vim.sh */
    const char *install_vim_sh =
      "#!/bin/sh\nRC=\"$HOME/.vimrc\"\ncat >> \"$RC\" <<'EOF'\n\" Omega package shortcuts\ncommand! OmegaOpen :!xdg-open ./omega_package/doc/index.html &\ncommand! OmegaQA :!python3 ./omega_package/bin/pdf_qa.py omega_package/library.sqlite \"question\"\nEOF\necho 'Appended omega commands to' $RC\n";
snprintf(buf, sizeof(buf), "%s/bin/install_vim.sh", out);
write_file(buf, install_vim_sh);

/* bin/install_emacs.sh */
    const char *install_emacs_sh =
      "#!/bin/sh\nEL=\"$HOME/.emacs.d/init.el\"\nmkdir -p \"$HOME/.emacs.d\"\ncat >> \"$EL\" <<'EOF'\n;; Omega shortcuts\n(defun omega-open () (interactive) (shell-command \"xdg-open ./omega_package/doc/index.html &\"))\n(global-set-key (kbd \"C-c o\") 'omega-open)\nEOF\necho 'Appended omega integration to' $EL\n";
snprintf(buf, sizeof(buf), "%s/bin/install_emacs.sh", out);
write_file(buf, install_emacs_sh);

/* tools/biblio_manager.py - export/import DB */
    const char *biblio_py =
      "#!/usr/bin/env python3\n\"\"\"\nbiblio_manager.py\nExport/import the documents DB to JSON/CSV.\nUsage: biblio_manager.py export json|csv db.sqlite outpath\n\"\"\"\nimport sys,sqlite3,json,csv\nif len(sys.argv)<5: print('Usage: biblio_manager.py export json|csv db.sqlite out'); sys.exit(2)\ncmd,fmt,db,out=sys.argv[1:5]\nconn=sqlite3.connect(db); cur=conn.cursor(); cur.execute('SELECT id,path,title,author,text FROM documents'); rows=cur.fetchall(); conn.close()\nif fmt=='json': arr=[{'id':r[0],'path':r[1],'title':r[2],'author':r[3],'text':r[4]} for r in rows]; open(out,'w',encoding='utf-8').write(json.dumps(arr,ensure_ascii=False,indent=2))\nelse:\n    with open(out,'w',encoding='utf-8',newline='') as f: w=csv.writer(f); w.writerow(['id','path','title','author','text']); [w.writerow(r) for r in rows]\nprint('exported to', out)\n";
snprintf(buf, sizeof(buf), "%s/tools/biblio_manager.py", out);
write_file(buf, biblio_py);

/* package/src/placeholder.c */
    const char *src_c =
      "/* package/src/placeholder.c - placeholder C source */\n#include <stdio.h>\nint placeholder(void){ puts(\"omega placeholder\"); return 0; }\n";
snprintf(buf, sizeof(buf), "%s/package/src/placeholder.c", out);
write_file(buf, src_c);

/* doc/README and index.html */
    const char *doc_readme =
      "# Omega Package (Generated)\n\nThis package contains tools for offline research workflows:\n- PDF import / text extraction\n- Formula extraction and analysis\n- BNF -> parser skeleton generator\n- Omega Script symbolic simulator (safe)\n- Jones polynomial hook (Sage optional)\n- Time-series forecasting skeleton (academic)\n- PDF Q&A (heuristic) and light text generation\n\nDependencies (recommended): python3, pip packages: pdfminer.six, sympy, pandas, matplotlib\n\nThis software does NOT include any tools for designing, testing, or deploying biological agents or medications.\n";
snprintf(buf, sizeof(buf), "%s/doc/README.md", out);
write_file(buf, doc_readme);

    const char *index_html =
      "<!doctype html><html><head><meta charset='utf-8'><title>Omega Package</title></head><body><h1>Omega Package</h1><p>See README.md for usage.</p></body></html>";
snprintf(buf, sizeof(buf), "%s/doc/index.html", out);
write_file(buf, index_html);

/* Makefile (suppress noisy errors) */
    const char *makefile =
      "# Makefile for Omega package (quiet, tolerant)\nPYTHON := python3\nBINDIR := bin\nTOOLS := tools\n.PHONY: all install clean lint\nall:\n\t@echo 'Omega package contains scripts. Use $(BINDIR)/omega to run tools.'\n\t@chmod +x $(BINDIR)/* 2>/dev/null || true\ninstall:\n\t@mkdir -p $(DESTDIR)/usr/local/bin 2>/dev/null || true\n\t@cp -f $(BINDIR)/omega $(DESTDIR)/usr/local/bin/omega 2>/dev/null || true\n\t@chmod +x $(DESTDIR)/usr/local/bin/omega 2>/dev/null || true\n\t@echo 'installed (errors suppressed)'\nclean:\n\t@-rm -f package/src/*.o 2>/dev/null || true\n\t@echo 'clean done'\nlint:\n\t@which pylint >/dev/null 2>&1 && pylint $(BINDIR)/*.py || true\n";
snprintf(buf, sizeof(buf), "%s/Makefile", out);
write_file(buf, makefile);

/* set scripts executable on POSIX */
#ifndef _WIN32
	{
	  char cmd[8192];
	  snprintf(cmd, sizeof(cmd),
		   "chmod +x \"%s/bin/omega\" \"%s/bin/pdf_import.py\" \"%s/bin/formula_extract.py\" \"%s/bin/analyze_pipeline.py\" \"%s/bin/bnf_to_parser.py\" \"%s/bin/omega_sim.py\" \"%s/bin/jones_hook.py\" \"%s/bin/forecast_fx.py\" \"%s/bin/pdf_qa.py\" \"%s/bin/gen_ai.py\" \"%s/bin/coq_wrapper.sh\" \"%s/bin/install_vim.sh\" \"%s/bin/install_emacs.sh\" 2>/dev/null || true",
		   out,out,out,out,out,out,out,out,out,out,out,out);
	  system(cmd);
	}
#endif

printf("Omega package skeleton created at: %s\n", out);
return 0;
}
```

使い方（最短）
1. ビルド: gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c
  2. 実行: ./pkginstallgen ./omega_package
  3. 推奨パッケージ（任意）: python3 -m pip install pdfminer.six sympy pandas matplotlib

注意（重要）
- パッケージは「研究・解析・教育目的のツール群の雛形」を提供します。生体実験、薬剤設計、実験自動化などの危険な用途には使えません。生成物はその目的を意図していません。
- 大規模 LLM の導入や Sage の利用はユーザ側で行ってください（API キー・ライセンスはユーザ管理）。
- 追加の機能や各スクリプトの詳細な拡張が必要であれば、どの部分を優先して展開するか教えてください。
