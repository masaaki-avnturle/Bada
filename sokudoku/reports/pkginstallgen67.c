了解しました。PDF と（任意の）既存理論・数式を入力すると、その内容を解析して「未知の理論と数式（仮説）」を自動生成する機能を含むパッケージを生成する単一の C プログラム `pkginstallgen.c` を示します。これをコンパイル・実行すると、パッケージ一式が作られます。生成されるツールは外部大規模モデルに依存せず、PDF からのテキスト抽出（`pdftotext` またはフォールバック）→解析→多様な数式生成→仮説合成、のパイプラインを自動で行います。出力は検証を要する「合成的仮説」です。

使い方（要約）
1. 保存: pkginstallgen.c
2. コンパイル: gcc -O2 -std=c11 -o pkginstallgen pkginstallgen.c
  3. 実行: ./pkginstallgen
  4. 生成ディレクトリへ移動: cd omega_theory_pkg
  5. 実行例:
   - ./bin/run_pipeline --pdf path/to/doc.pdf --seed_theory "x^{1/2+iy}=..." --outdir generated --count 5

注意
- 自動生成された「未知理論」は検証・査読が必須です。探究・実験用の合成出力として利用してください。
- 実行に `pdftotext` があると最良に動きます。なければ Python フォールバックでテキストを簡易抽出します。

以下が `pkginstallgen.c`（全文）です。保存してコンパイル・実行してください。

```c
  /*
   * pkginstallgen.c
   *
   * Generate omega_theory_pkg which includes:
   *  - tools/pdf_analyzer.py      : extract & analyze pdf text
   *  - tools/theory_gen.py        : formula/hypothesis diversity generator (enhanced)
   *  - tools/hypothesis_generator.py : combine pdf + optional seed theory to propose hypotheses
   *  - bin/run_pipeline           : runner script to run full pipeline
   *  - lib/__init__.py, README.md, Makefile
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
   * Run:
   *   ./pkginstallgen
   *
   * Then:
   *   cd omega_theory_pkg
   *   chmod +x bin/run_pipeline
   *   ./bin/run_pipeline --pdf /path/to/doc.pdf --seed_theory "x^{1/2+iy}=..." --outdir generated --count 5
   *
   * Outputs synthetic hypothesis files in generated/
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

  static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(path, 0755) == 0) return 0;
  if (errno == ENOENT) {
    char tmp[4096];
    strncpy(tmp, path, sizeof(tmp)-1);
    tmp[sizeof(tmp)-1]=0;
    char *p = strrchr(tmp, '/');
    if (p && p != tmp) { *p = 0; if (ensure_dir(tmp)==0) return mkdir(path,0755)==0?0:-1; }
  }
  return -1;
}

static int write_file(const char *path, const char *data, int mode) {
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
  if (fputs(data, f) == EOF) { fclose(f); return -1; }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

static int write_path(const char *root, const char *rel, const char *data, int mode) {
  char full[4096];
  snprintf(full, sizeof(full), "%s/%s", root, rel);
  char dir[4096];
  strncpy(dir, full, sizeof(dir)-1); dir[sizeof(dir)-1]=0;
  char *p = strrchr(dir, '/');
  if (p) { *p = 0; ensure_dir(dir); }
  return write_file(full, data, mode);
}

/* Makefile */
static const char *makefile =
"# Makefile for omega_theory_pkg\n"
"PY ?= python3\n"
".PHONY: all run clean\n"
"all: run\n"
"run:\n"
"\t@./bin/run_pipeline\n"
"clean:\n"
  "\t@rm -rf generated/* || true\n";

/* bin/run_pipeline */
static const char *bin_run =
"#!/usr/bin/env bash\n"
"set -euo pipefail\n"
"ROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n" 
"PY=${PY:-python3}\n"
"PDF_ANALYZER=\"$ROOT/tools/pdf_analyzer.py\"\n"
"HYP_GEN=\"$ROOT/tools/hypothesis_generator.py\"\n" 
"THEORY_GEN=\"$ROOT/tools/theory_gen.py\"\n"
"OUTDIR=\"$ROOT/generated\"\n"
"mkdir -p \"$OUTDIR\"\n"
"# simple argument parsing\n" 
"PDF=\"\"; SEED=\"\"; COUNT=3\n" 
"while [[ $# -gt 0 ]]; do case \"$1\" in\n"
"  --pdf) PDF=\"$2\"; shift 2;;\n"
"  --seed_theory) SEED=\"$2\"; shift 2;;\n" 
"  --outdir) OUTDIR=\"$2\"; shift 2;;\n"
"  --count) COUNT=\"$2\"; shift 2;;\n"
"  *) shift;;\n"
"esac; done\n"
"if [ -z \"$PDF\" ]; then echo \"No --pdf provided; expecting path to PDF\"; exit 1; fi\n"
"TMPTXT=\"$OUTDIR/$(basename \"$PDF\").txt\"\n"
"echo \"Extracting text from $PDF -> $TMPTXT\"\n"
"$PY \"$PDF_ANALYZER\" --pdf \"$PDF\" --out \"$TMPTXT\"\n"
"echo \"Generating hypotheses (count=$COUNT)\"\n"$PY \"$HYP_GEN\" --pdf_text \"$TMPTXT\" --seed \"$SEED\" --count \"$COUNT\" --outdir \"$OUTDIR\"\n"
"echo \"Also generating diverse formulas\""$PY \"$THEORY_GEN\" --count \"$COUNT\" --outdir \"$OUTDIR\" --seed 42\n"
  "echo \"Done. Check $OUTDIR\" \n";

/* tools/pdf_analyzer.py: extract text (pdftotext fallback) and basic analysis */
static const char *pdf_analyzer_py =
"#!/usr/bin/env python3\n"
"import argparse, subprocess, os, sys, re\n"
"\n"
"def extract_with_pdftotext(pdf, out):\n"
"    try:\n"
"        subprocess.run(['pdftotext', pdf, out], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n"
"        return True\n"
"    except Exception:\n"
"        return False\n"
"\n"
"def fallback_extract(pdf, out):\n"
"    # very simple fallback: attempt to read via strings (binary) and heuristics\n"
"    try:\n"
"        with open(pdf, 'rb') as f:\n"
"            b = f.read()\n" 
"        s = b.decode('utf-8', errors='ignore')\n"
"        # remove long binary blocks\n"
"        s = re.sub(r'[^\\x09\\x0A\\x0D\\x20-\\x7E\\n]+',' ', s)\n" 
"        with open(out, 'w', encoding='utf-8') as fo:\n"
"            fo.write(s)\n" 
"        return True\n"
"    except Exception:\n"
"        return False\n"
"\n"
"def analyze_text(path):\n"
"    with open(path, 'r', encoding='utf-8', errors='ignore') as f:\n"
"        txt = f.read()\n" 
"    # basic stats\n"
"    words = re.findall(r\"\\\\w+\", txt)\n"
"    uniq = set(words)\n" 
"    # extract LaTeX math-like fragments $...$ or \\[...\\]\n"
"    inline = re.findall(r\"\\$(.+?)\\$\", txt, flags=re.S)\n"
"    display = re.findall(r\"\\\\\\\\\\[(.+?)\\\\\\\\\\]\", txt, flags=re.S)\n" 
"    return {'words': len(words), 'unique_words': len(uniq), 'inline_math': inline[:20], 'display_math': display[:10]}\n"
"\n"
"def main():\n"
"    p = argparse.ArgumentParser()\n"
"    p.add_argument('--pdf', required=True)\n"
"    p.add_argument('--out', required=True)\n" 
"    args = p.parse_args()\n"
"    ok = extract_with_pdftotext(args.pdf, args.out)\n"
"    if not ok:\n"
"        fallback_extract(args.pdf, args.out)\n" 
"    stats = analyze_text(args.out)\n"
"    print('extracted:', args.out)\n" 
"    print('words:', stats['words'], 'unique:', stats['unique_words'])\n" 
"    if stats['inline_math']:\n" 
"        print('inline math snippets sample:')\n" 
"        for m in stats['inline_math'][:5]: print('-', m[:200])\n" 
"    if stats['display_math']:\n" 
"        print('display math sample:')\n" 
"        for m in stats['display_math'][:5]: print('-', m[:200])\n" 
"\n"
  "if __name__ == '__main__': main()\n";

/* tools/theory_gen.py - enhanced diversity (improved) */
static const char *theory_gen_py =
"#!/usr/bin/env python3\n"
"import os, sys, argparse, random, datetime\n"
"LATEX_SPECIAL = [r'\\\\alpha',r'\\\\beta',r'\\\\gamma',r'\\\\delta',r'\\\\epsilon',r'\\\\zeta',r'\\\\eta',r'\\\\theta',r'\\\\lambda',r'\\\\mu',r'\\\\nu',r'\\\\xi',r'\\\\pi',r'\\\\rho',r'\\\\sigma',r'\\\\phi',r'\\\\psi',r'\\\\omega']\n"
"FUNCTIONS = [r'\\\\sin',r'\\\\cos',r'\\\\exp',r'\\\\log',r'\\\\Gamma',r'\\\\zeta',r'\\\\mathrm{erf}',r'\\\\mathrm{Li}_2']\n"
"TEMPLATES = [\n"
"    r'\\\\sum_{n=1}^{\\\\infty} a_n %s',\n"
"    r'\\\\int_M (%s) \\\\, dV = %s',\n"
"    r'\\\\partial_t %s = %s + %s',\n"
"    r'%s_{\\\\mu\\\\nu} = %s + \\\\nabla_{\\\\mu}\\\\nabla_{\\\\nu} %s',\n"
"    r'\\\\mathcal{O} = %s \\\\circ %s + \\\\sum_{k=0}^N c_k %s^{k}',\n"
"]\n"
"FRAGMENTS = [r'e^{\\\\lambda x}', r'\\\\nabla_i\\\\nabla_j f', r'|\\\\nabla f|^2', r'\\\\Delta f', r'\\\\zeta(s)']\n"
"R = random.Random()\n"
"def pick(xs): return R.choice(xs)\n"
"def coeff():\n"
"    if R.random()<0.2: return str(R.randint(-5,5))\n"
"    return r\"\\\\frac{%d}{%d}\" % (R.randint(1,9), R.randint(1,9))\n"
"def fragment():\n"
"    p = R.random()\n"
"    if p<0.4: return pick(FRAGMENTS)\n"
"    return pick(FUNCTIONS) + '(x)\\\\;'+pick(['+','-','\\\\cdot','\\\\otimes'])+'\\\\;'+pick(FRAGMENTS)\n"
"def synth_formula():\n"
"    templ = pick(TEMPLATES)\n"
"    needed = templ.count('%s')\n"
"    parts = [fragment() for _ in range(needed)]\n"
"    try:\n"
"        return templ % tuple(parts)\n"
"    except Exception:\n"
"        return '\\\\mathrm{SYNTH}(' + ','.join(parts) + ')'\n"
"def make_text(title, formula):\n"
"    hdr = '# Generated Theory: %s\\\\n# %s\\\\n\\\\n' % (title, datetime.datetime.utcnow().isoformat())\n"
"    body = 'Abstract:\\nAutogenerated diverse formulaic fragment.\\\\n\\\\n'\n"
"    body += 'Conjecture:\\n\\\\begin{equation}\\\\n' + formula + '\\\\n\\\\end{equation}\\\\n\\\\n'\n"
"    body += 'Notes: synthetic, verify.\\\\n'\n"
"    return hdr+body\n"
"def main():\n"
"    p=argparse.ArgumentParser(); p.add_argument('--count',type=int,default=1); p.add_argument('--outdir',default='generated'); p.add_argument('--seed',type=int,default=None); args=p.parse_args()\n"
"    if args.seed is not None: R.seed(args.seed)\n"
"    os.makedirs(args.outdir, exist_ok=True)\n"
"    for i in range(args.count):\n"
"        title='diverse_%03d'%(i+1)\n"
"        f=synth_formula()\n"
"        with open(os.path.join(args.outdir,title+'.md'),'w',encoding='utf-8') as fo: fo.write(make_text(title,f))\n" 
"        with open(os.path.join(args.outdir,title+'.tex'),'w',encoding='utf-8') as fo: fo.write('\\\\begin{equation}\\\\n'+f+'\\\\n\\\\end{equation}')\n"
"    print('wrote',args.count,'diverse formulas to',args.outdir)\n"
  "if __name__=='__main__': main()\n";

/* tools/hypothesis_generator.py : combine pdf text + optional seed theory to propose hypotheses */
static const char *hyp_gen_py =
"#!/usr/bin/env python3\n"
"import argparse, os, random, re, datetime\n"
"\n"
"R = random.Random()\n"
"\n"
"def load_text(path):\n"
"    with open(path, 'r', encoding='utf-8', errors='ignore') as f:\n"
"        return f.read()\n"
"\n"
"def extract_keywords(text, k=20):\n"
"    words = re.findall(r\"\\\\w+\", text)\n"
"    freq = {}\n"
"    for w in words:\n"
"        if len(w)<3: continue\n"
"        freq[w] = freq.get(w,0)+1\n"
"    items = sorted(freq.items(), key=lambda x:-x[1])\n"
"    return [w for w,_ in items[:k]]\n"
"\n"
"OP_POOL = ['\\\\nabla','\\\\Delta','\\\\int','\\\\sum','\\\\zeta','\\\\Gamma','\\\\partial']\n"
"\n"
"def propose_hypotheses(pdf_text, seed_theory, count=3):\n"
"    kws = extract_keywords(pdf_text, k=40)\n"
"    hyps = []\n"
"    for i in range(count):\n"
"        # pick 2-4 keywords and combine with operator fragments\n"
"        ks = R.sample(kws, k=min(len(kws), 2+R.randint(0,2))) if kws else ['x']\n"
"        ops = R.sample(OP_POOL, k=1)\n"
"        coef = str(R.randint(1,9))\n"
"        # incorporate seed_theory sometimes\n"
"        seed_part = ''\n"
"        if seed_theory and R.random() < 0.6:\n"
"            seed_part = ' // seed: ' + (seed_theory[:200])\n"
"        formula = '%s %s %s = 0' % (coef, ops[0], '*'.join(ks))\n"
"        remark = 'autogenerated hypothesis #%d' % (i+1)\n"
"        hyps.append({'id':i+1,'formula':formula,'remark':remark,'seed_included': bool(seed_part),'seed_snippet': seed_part})\n"
"    return hyps\n"
"\n"
"def save_hypotheses(hyps, outdir, basename='hypothesis'):\n"
"    os.makedirs(outdir, exist_ok=True)\n" 
"    for h in hyps:\n"
"        ts = datetime.datetime.utcnow().isoformat()\n"
"        fname = os.path.join(outdir, '%s_%03d.md' % (basename, h['id']))\n"
"        with open(fname, 'w', encoding='utf-8') as f:\n"
"            f.write('# Hypothesis %d\\n# %s\\n\\n' % (h['id'], ts))\n"
"            f.write('Formula:\\n```\n'+ h['formula'] + '\\n```\\n\\n')\n" 
"            if h['seed_included']:\n"
"                f.write('Seed snippet included:\\n```\n' + h['seed_snippet'] + '\\n```\\n\\n')\n"
"            f.write('Remark: %s\\n' % h['remark'])\n" 
"    return len(hyps)\n"
"\n"
"def main():\n"
"    p = argparse.ArgumentParser()\n"
"    p.add_argument('--pdf_text', required=True)\n"
"    p.add_argument('--seed', default='')\n"
"    p.add_argument('--count', type=int, default=3)\n"
"    p.add_argument('--outdir', default='generated')\n"
"    args = p.parse_args()\n"
"    text = load_text(args.pdf_text)\n"
"    hyps = propose_hypotheses(text, args.seed, args.count)\n"
"    n = save_hypotheses(hyps, args.outdir, basename='hypothesis')\n" 
"    print('Saved', n, 'hypotheses to', args.outdir)\n"
"\n"
  "if __name__ == '__main__': main()\n";

/* lib/__init__.py */
static const char *lib_init = "# omega_theory_pkg.lib marker\n";

/* README */
static const char *readme =
  "# omega_theory_pkg\n\nThis package generates synthetic hypotheses (theories and formulas) by analyzing a provided PDF and optional seed theory/formula.\n\nUse bin/run_pipeline --pdf /path/to/doc.pdf --seed_theory \"...\" --outdir generated --count 5\n\nOutputs are synthetic and require rigorous verification.\n";

int main(void) {
  const char *root = "omega_theory_pkg";
  if (ensure_dir(root)!=0) { fprintf(stderr, "cannot create %s\n", root); return 1; }
  if (write_path(root, "Makefile", makefile, 0)!=0) return 2;
  if (write_path(root, "bin/run_pipeline", bin_run, 0755)!=0) return 3;
  if (ensure_dir("omega_theory_pkg/tools")!=0) return 4;
  if (write_path(root, "tools/pdf_analyzer.py", pdf_analyzer_py, 0755)!=0) return 5;
  if (write_path(root, "tools/theory_gen.py", theory_gen_py, 0755)!=0) return 6;
  if (write_path(root, "tools/hypothesis_generator.py", hyp_gen_py, 0755)!=0) return 7;
  if (ensure_dir("omega_theory_pkg/lib")!=0) return 8;
  if (write_path(root, "lib/__init__.py", lib_init, 0)!=0) return 9;
  if (write_path(root, "README.md", readme, 0)!=0) return 10;
  ensure_dir("omega_theory_pkg/generated");
  printf("omega_theory_pkg created. Run: cd %s && ./bin/run_pipeline --pdf <file> --seed_theory '<theory>' --outdir generated --count N\n", root);
  return 0;
}
```

必要なら：
- 生成アルゴリズムの複雑化（AST ベース、テンプレート追加、係数分布の指定、確率微分方程式テンプレートなど）
- 出力 LaTeX の簡易検算（pdflatex 実行）や MathJax 表示用 HTML 生成
- 生成物のメタ情報（キーワード、出典抜粋、関連箇所行番号）を付与

どれを優先するか指示をください。
