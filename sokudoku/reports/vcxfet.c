了解しました。ご指定の優先順位に従い、以下を実装する単一の C プログラム `pkginstallgen.c` を作成しました。コンパイル・実行するとパッケージが生成されます。

優先順の実装内容（要約）
- 最優先 2: Jones 多項式に基づく改良版エントロピー不変量算出（より意味ある特徴抽出と正規化、JSON 出力）を tools/jones_entropy.py に実装。
- 次点 3: BNF→AST を深く使った式合成（AST をテンプレートにマッチングして文法準拠の式を生成）を tools/ast_generator.py と tools/formula_synth.py に実装。
- その次 1（要約）: 以前の「BNF ベース生成器」の要点を簡潔にまとめてパッケージに含める（tools/bnf_parser.py は簡潔版）。
- さらに 4（表示）: 生成結果を集約してブラウザで閲覧できる HTML ビューワ tools/viewer.py を追加（generated/ 内を HTML レポート化）。

使い方（短縮）
1. 保存: pkginstallgen.c
2. コンパイル: gcc -O2 -std=c11 -o pkginstallgen pkginstallgen.c
  3. 実行: ./pkginstallgen
  4. 生成: ./omega_ai_pkg/
  5. 実行例:
   cd omega_ai_pkg
   ./bin/run_pipeline --pdf /path/to/doc.pdf --seed "x^{1/2+iy}=..." --outdir generated --count 5
   # 生成後
   python3 usr/tools/viewer.py --dir generated --open

以下がコンパイル可能な `pkginstallgen.c`（そのまま保存して gcc でビルド可能）です。実行すると指定のディレクトリ構成とスクリプト群が作られます。

```c
  /*
   * pkginstallgen.c
   *
   * Generates omega_ai_pkg with:
   *  - Improved Jones-entropy (tools/jones_entropy.py)
   *  - BNF->AST deep use + template-based formula synthesis (tools/ast_generator.py, tools/formula_synth.py)
   *  - Compact BNF writer (tools/bnf_parser.py)
   *  - Viewer: HTML report generator and optional auto-open (tools/viewer.py)
   *  - Runner: bin/run_pipeline
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
   * Run:
   *   ./pkginstallgen
   */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

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
    if (p && p != tmp) {
      *p = 0;
      if (ensure_dir(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1;
    }
  }
  return -1;
}
  static int write_file_mode(const char *path, const char *data, int mode) {
    FILE *f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
    if (data && fputs(data, f) == EOF) { fclose(f); return -1; }
    fclose(f);
    if (mode) chmod(path, (mode_t)mode);
    return 0;
  }
static int write_path(const char *root, const char *rel, const char *data, int mode) {
  char full[4096];
  snprintf(full, sizeof(full), "%s/%s", root, rel);
  char dir[4096];
  strncpy(dir, full, sizeof(dir)-1);
  dir[sizeof(dir)-1]=0;
  char *p = strrchr(dir, '/');
  if (p) { *p = 0; ensure_dir(dir); }
  return write_file_mode(full, data, mode);
}

int main(void) {
  const char *root = "omega_ai_pkg";
  if (ensure_dir(root)!=0) { fprintf(stderr,"cannot create %s\n",root); return 1; }

  /* README */
    const char *readme =
"# omega_ai_pkg\n\n"
"Prototype package: improved Jones-entropy, BNF->AST->template formula synthesis, and viewer.\n"
      "Run: ./bin/run_pipeline --pdf <file> --seed \"...\" --outdir generated --count N\n";
    write_path(root,"README.md",readme,0644);

    /* bin/run_pipeline */
    ensure_dir("omega_ai_pkg/bin");
    const char *runner =
      "#!/usr/bin/env bash\nset -euo pipefail\nROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\nPY=${PY:-python3}\nPDF_TOOL=\"$ROOT/usr/tools/pdf_analyzer.py\"\nBNF=\"$ROOT/usr/tools/bnf_parser.py\"\nAST=\"$ROOT/usr/tools/ast_generator.py\"\nHYP=\"$ROOT/usr/tools/hypothesis_generator.py\"\nFORM=\"$ROOT/usr/tools/formula_synth.py\"\nJONES=\"$ROOT/usr/tools/jones_entropy.py\"\nTUPLE=\"$ROOT/usr/tools/tuplespace.py\"\nVIEW=\"$ROOT/usr/tools/viewer.py\"\nOUTDIR=\"$ROOT/generated\"\nmkdir -p \"$OUTDIR\"\nPDF=\"\"\nSEED=\"\"\nCOUNT=3\nwhile [[ $# -gt 0 ]]; do case \"$1\" in --pdf) PDF=\"$2\"; shift 2;; --seed) SEED=\"$2\"; shift 2;; --outdir) OUTDIR=\"$2\"; shift 2;; --count) COUNT=\"$2\"; shift 2;; *) shift;; esac; done\nif [ -n \"$PDF\" ]; then echo \"Extracting $PDF -> $OUTDIR/doc.txt\"; $PY \"$PDF_TOOL\" --pdf \"$PDF\" --out \"$OUTDIR/doc.txt\" || true; fi\n$PY \"$BNF\" --lang c --out \"$OUTDIR/bnf.json\"\n$PY \"$AST\" --bnf \"$OUTDIR/bnf.json\" --src \"$OUTDIR/doc.txt\" --out \"$OUTDIR/ast.json\"\n$PY \"$HYP\" --pdf_text \"$OUTDIR/doc.txt\" --seed \"$SEED\" --count \"$COUNT\" --outdir \"$OUTDIR\"\n$PY \"$FORM\" --bnf \"$OUTDIR/bnf.json\" --ast \"$OUTDIR/ast.json\" --seed \"$SEED\" --count \"$COUNT\" --outdir \"$OUTDIR\"\n$PY \"$JONES\" --dir \"$OUTDIR\" --out jones.json\n$PY \"$TUPLE\" --set entropy \"$OUTDIR/jones.json\"\n$PY \"$VIEW\" --dir \"$OUTDIR\" --open || true\necho \"Done. See $OUTDIR\"\n";
    write_path(root,"bin/run_pipeline",runner,0755);

    /* include */
    ensure_dir("omega_ai_pkg/include");
    write_path(root,"include/omega.h","/* omega helper */\n#ifndef OMEGA_H\n#define OMEGA_H\n#include <stdio.h>\nstatic inline void omega_log(const char*s){fprintf(stderr,\"[omega] %s\\n\",s);} \n#endif\n",0644);

    /* etc config */
    ensure_dir("omega_ai_pkg/etc");
    write_path(root,"etc/config.yaml","pdf_tool: pdftotext\nuse_pdflatex: true\n",0644);

    /* lib */
    ensure_dir("omega_ai_pkg/lib");
    write_path(root,"lib/omega_core.os","# Omega core stubs\nfunction tuplespace_save(k,v)\n  print('[tuplespace] '..k..' saved')\nend\n",0644);

    /* usr/tools */
    ensure_dir("omega_ai_pkg/usr");
    ensure_dir("omega_ai_pkg/usr/tools");
    ensure_dir("omega_ai_pkg/usr/lang");

    /* pdf_analyzer.py */
    write_path(root,"usr/tools/pdf_analyzer.py",
	       "#!/usr/bin/env python3\nimport argparse,subprocess,re,os\n\ndef extract(pdf,out):\n    try:\n        subprocess.run(['pdftotext',pdf,out],check=True)\n        return True\n    except Exception:\n        with open(pdf,'rb') as f: b=f.read()\n        s=b.decode('utf-8',errors='ignore')\n        s=re.sub(r'[^\\\\x09\\\\x0A\\\\x0D\\\\x20-\\\\x7E\\\\n]+',' ',s)\n        with open(out,'w',encoding='utf-8') as fo: fo.write(s)\n        return True\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--pdf',required=True); p.add_argument('--out',required=True); a=p.parse_args();\n    if extract(a.pdf,a.out): print('extracted',a.out)\n",0755);

    /* bnf_parser.py (compact) */
    write_path(root,"usr/tools/bnf_parser.py",
	       "#!/usr/bin/env python3\nimport json,argparse\n# compact BNF JSON for template-driven generator\nbnf={'C':{\n  'program':['declaration_list'],\n  'declaration_list':['declaration','declaration_list_tail'],\n  'declaration':['type_spec','declarator',';'],\n  'type_spec':['int','float','double','char','void'],\n  'declarator':['identifier','[','constant',']']\n}}\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--lang',default='c'); p.add_argument('--out',default='bnf.json'); a=p.parse_args();\n    with open(a.out,'w',encoding='utf-8') as f: json.dump(bnf,f,indent=2); print('wrote',a.out)\n",0755);

    /* ast_generator.py: deeper AST extraction (toy) */
    write_path(root,"usr/tools/ast_generator.py",
	       "#!/usr/bin/env python3\nimport json,os,argparse,re\n# Toy AST: parse simple declarations from source text and attach to BNF-derived nodes\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--bnf',required=True); p.add_argument('--src',default=''); p.add_argument('--out',default='ast.json'); a=p.parse_args()\n    bnf=json.load(open(a.bnf,'r',encoding='utf-8')) if os.path.exists(a.bnf) else {}\n    ast={'type':'program','children':[]}\n    if a.src and os.path.exists(a.src):\n        s=open(a.src,'r',encoding='utf-8',errors='ignore').read()\n        # find simple declarations like 'int x = 0;'\n        for m in re.finditer(r\"(int|float|double|char)\\s+([a-zA-Z_][a-zA-Z0-9_]*)\\s*(=\\s*[^;]+)?;\",s):\n            ast['children'].append({'type':'declaration','spec':m.group(1),'name':m.group(2),'init':m.group(3) or ''})\n    else:\n        ast['children'].append({'type':'declaration','spec':'int','name':'x','init':'=0'})\n    open(a.out,'w',encoding='utf-8').write(json.dumps(ast,indent=2))\n    print('wrote',a.out)\n",0755);

    /* hypothesis_generator.py (unchanged simple) */
    write_path(root,"usr/tools/hypothesis_generator.py",
	       "#!/usr/bin/env python3\nimport argparse,random,os\nR=random.Random()\nOPS=['nabla','Delta','sum','int','zeta','Gamma']\ndef extract_keywords(path):\n    if not path or not os.path.exists(path): return ['x']\n    t=open(path,'r',encoding='utf-8',errors='ignore').read(); words=[w for w in t.split() if len(w)>3]; return list(dict.fromkeys(words))[:40] or ['x']\n\ndef propose(pdf_text,seed,count):\n    kws=extract_keywords(pdf_text); hyps=[]\n    for i in range(count): k=R.choice(kws); op=R.choice(OPS); frm=f\"{R.randint(1,7)} {op}({k}) = 0\"; \n        \n        # small seed injection\n        if seed and R.random()<0.6: frm += ' //seed:'+seed[:120]\n        hyps.append({'id':i+1,'formula':frm})\n    return hyps\n\ndef save(hyps,outdir):\n    os.makedirs(outdir,exist_ok=True)\n    for h in hyps:\n        p=os.path.join(outdir,f\"hypothesis_{h['id']:03d}.md\")\n        open(p,'w',encoding='utf-8').write('# Hypothesis\\n'+h['formula']+'\\n')\n    print('saved',len(hyps))\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--pdf_text',default=''); p.add_argument('--seed',default=''); p.add_argument('--count',type=int,default=3); p.add_argument('--outdir',default='generated'); a=p.parse_args(); hyps=propose(a.pdf_text,a.seed,a.count); save(hyps,a.outdir)\n",0755);

    /* formula_synth.py: AST-aware template synthesis */
    write_path(root,"usr/tools/formula_synth.py",
	       "#!/usr/bin/env python3\nimport argparse,json,os,random\nR=random.Random()\nTEMPLATES=['A*FUNC(X) + B/X','SUM_n A_n FUNC(X_n)','INT FUNC(X) dX = C']\nFUNC=['sin','cos','exp','log','Gamma','zeta']\n\ndef synth_from_ast(ast,seed,count):\n    out=[]\n    decls=[c for c in ast.get('children',[]) if c.get('type')=='declaration']\n    names=[d.get('name') for d in decls] or ['x']\n    for i in range(count):\n        t=R.choice(TEMPLATES); f=R.choice(FUNC); n=R.choice(names)\n        s=t.replace('FUNC',f).replace('X',n).replace('A',str(R.randint(1,9))).replace('B',str(R.randint(1,5)))\n        if seed and R.random()<0.4: s += ' /*seed:'+seed[:60]+'*/'\n        out.append(s)\n    return out\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--bnf'); p.add_argument('--ast',required=True); p.add_argument('--seed',default=''); p.add_argument('--count',type=int,default=3); p.add_argument('--outdir',default='generated'); a=p.parse_args()\n    ast=json.load(open(a.ast,'r',encoding='utf-8')) if os.path.exists(a.ast) else {'children':[]}\n    os.makedirs(a.outdir,exist_ok=True)\n    for idx,s in enumerate(synth_from_ast(ast,a.seed,a.count),start=1):\n        path=os.path.join(a.outdir,f'formula_{idx:03d}.tex')\n        open(path,'w',encoding='utf-8').write('\\\\begin{equation}\\n'+s+'\\\\end{equation}\\n')\n    print('wrote',a.count,'formulas')\n",0755);

  /* jones_entropy.py: improved toy implementation */
  write_path(root,"usr/tools/jones_entropy.py",
	     "#!/usr/bin/env python3\nimport argparse,os,json,math,re\n# Improved toy Jones-inspired invariant: extract token-shape signature and compute normalized entropy\n\ndef tokenize_text(s):\n    # simple tokens: identifiers, numbers, symbols\n    toks = re.findall(r\"[A-Za-z_][A-Za-z0-9_]*|\\\\d+|[^\\sA-Za-z0-9_]\", s)\n    return toks\n\ndef compute_signature(dirpath):\n    token_counts = {}\n    total = 0\n    for fn in os.listdir(dirpath):\n        if fn.endswith('.tex') or fn.endswith('.md') or fn.endswith('.txt'):\n            with open(os.path.join(dirpath,fn),'r',encoding='utf-8',errors='ignore') as f:\n                t = f.read()\n                toks = tokenize_text(t)\n                for tk in toks:\n                    token_counts[tk] = token_counts.get(tk,0) + 1\n                total += len(toks)\n    if total == 0:\n        return {'total_tokens':0,'entropy':0.0,'signature':{}}\n    # compute Shannon entropy over token frequency distribution\n    import math\n    H = 0.0\n    for k,v in token_counts.items():\n        p = v/total\n        H -= p * math.log2(p)\n    # normalize by log2(unique_tokens)\n    uniq = max(1, len(token_counts))\n    H_norm = H / math.log2(uniq) if uniq>1 else 0.0\n    # produce toy 'Jones' polynomial coefficients from token length histogram\n    length_hist = {}\n    for k in token_counts.keys():\n        l = len(k)\n        length_hist[l] = length_hist.get(l,0) + 1\n    coeffs = [length_hist.get(i,0) for i in range(1, max(length_hist.keys())+1)] if length_hist else [0]\n    signature = {'total_tokens':total, 'unique_tokens':len(token_counts), 'H_bits':H, 'H_normalized':H_norm, 'length_coeffs':coeffs}\n    return signature\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--dir',required=True); p.add_argument('--out','-o',default='jones.json'); a=p.parse_args()\n    sig = compute_signature(a.dir)\n    with open(os.path.join(a.dir,a.out),'w',encoding='utf-8') as f: json.dump(sig,f,indent=2)\n    print('wrote',os.path.join(a.dir,a.out))\n",0755);

  /* tuplespace.py */
  write_path(root,"usr/tools/tuplespace.py",
	     "#!/usr/bin/env python3\nimport argparse,json,os\nDB='omega_tuples.json'\ndef load_db():\n    if os.path.exists(DB): return json.load(open(DB,'r',encoding='utf-8'))\n    return {}\n\ndef save_db(d): json.dump(d,open(DB,'w',encoding='utf-8'),indent=2)\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--set',nargs=2); p.add_argument('--get'); a=p.parse_args()\n    d=load_db()\n    if a.set: d[a.set[0]]=a.set[1]; save_db(d); print('set',a.set[0]); exit(0)\n    if a.get: print(d.get(a.get)); exit(0)\n    print('db',DB)\n",0755);

  /* viewer.py: generate HTML report and optionally open in browser */
  write_path(root,"usr/tools/viewer.py",
	     "#!/usr/bin/env python3\nimport argparse,os,json,webbrowser\nhtml_tmpl='''<!doctype html><html><head><meta charset=\"utf-8\"><title>Omega AI Report</title></head><body><h1>Omega AI Report</h1>{body}</body></html>'''\n\ndef build(dirpath):\n    items=[]\n    for fn in sorted(os.listdir(dirpath)):\n        if fn.endswith('.md') or fn.endswith('.txt'):\n            items.append('<h2>'+fn+'</h2><pre>'+open(os.path.join(dirpath,fn),'r',encoding='utf-8',errors='ignore').read()[:10000]+'</pre>')\n        if fn.endswith('.tex'):\n            items.append('<h2>'+fn+'</h2><pre>'+open(os.path.join(dirpath,fn),'r',encoding='utf-8',errors='ignore').read()[:10000]+'</pre>')\n        if fn.endswith('.json'):\n            items.append('<h2>'+fn+'</h2><pre>'+open(os.path.join(dirpath,fn),'r',encoding='utf-8',errors='ignore').read()+'</pre>')\n    body='\\n<hr/>\\n'.join(items)\n    return html_tmpl.format(body=body)\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--dir',required=True); p.add_argument('--out',default='report.html'); p.add_argument('--open',action='store_true'); a=p.parse_args()\n    html=build(a.dir)\n    outp=os.path.join(a.dir,a.out)\n    open(outp,'w',encoding='utf-8').write(html)\n    print('wrote',outp)\n    if a.open:\n        webbrowser.open('file://'+os.path.abspath(outp))\n",0755);

  /* omega interpreter stub */
  write_path(root,"usr/lang/omega_interpreter.py",
	     "#!/usr/bin/env python3\nimport argparse,os\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--run',default=''); a=p.parse_args();\n    path = os.path.join(a.run,'omega_example.os') if a.run else 'usr/lang/omega_example.os'\n    if os.path.exists(path):\n        print('[omega interpreter] preview of',path)\n        print(open(path,'r',encoding='utf-8',errors='ignore').read()[:1000])\n    else:\n        print('no omega script at',path)\n",0755);

  /* omega_example.os */
  write_path(root,"usr/lang/omega_example.os",
	     "-- Omega Script example (pseudo)\nprint('Omega script prototype')\n",0644);

  /* license */
  write_path(root,"etc/license.txt","omega_ai_pkg: prototype. No warranty.\n",0644);

  printf("Created '%s'. Run: cd %s && ./bin/run_pipeline --pdf <file> --seed '<seed>' --outdir generated --count N\n",root,root);
  return 0;
}
```

補足・注意
- Jones 実装は本物の結び目理論ライブラリではなく、ソース群から意味あるトークン分布を抽出してエントロピー正規化を行う「Jones 風」プロトタイプです。真の Jones 多項式解析を行う場合は専門ライブラリ（knot theory）や数式処理が必要です。
- AST→テンプレート合成は「AST から変数名や宣言を取得してテンプレートに差し込む」方式のプロトタイプです。文法準拠性を高める拡張（型チェック・式 AST 生成器など）は追加可能です。
- viewer.py は生成結果を HTML 化してブラウザで開く機能を備えます（--open で自動表示）。
- 実行には python3 が必要です。pdftotext や pdflatex はあると便利ですが必須ではありません。

次の改善案（任意）
- 真の Jones 多項式計算（C/C++ or Sage 等連携）を組込む  
- AST→式合成を型安全にする（小さな型推論器の追加）  
- Omega Script の簡易 VM を完成させる（字句→構文→実行）  
- Web UI（Flask や静的ファイル）でより良い表示/対話を実現

どれを最優先で進めますか（番号で指定してください）？
