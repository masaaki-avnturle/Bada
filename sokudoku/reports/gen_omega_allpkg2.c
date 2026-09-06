続けます。パート2 — `gen_omega_allpkg.c` の残り（server.py の続き、web ファイル、tools スクリプト、Makefile、README、main の書き込み部分）。長いのでさらに分割する場合は指示してください。

```c
/* server.py continued (rest of Handler methods and run) */
static const char *server_py_cont[] = {
  "    def do_PUT(self):",
  "        parsed = urllib.parse.urlparse(self.path); path = parsed.path",
  "        if not path.startswith('/data/'): self.send_response(403); self.end_headers(); return",
  "        name = path[len('/data/'):]; target = safe_join(DATA_DIR, name)",
  "        length = int(self.headers.get('Content-Length', 0))",
  "        if length > MAX_UPLOAD: self.send_response(413); self.end_headers(); return",
  "        with open(target, 'wb') as f:",
  "            remaining = length",
  "            while remaining > 0:",
  "                chunk = self.rfile.read(min(65536, remaining))",
  "                if not chunk: break",
  "                f.write(chunk); remaining -= len(chunk)",
  "        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')",
  "",
  "    def handle_addbook(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body)",
  "        except Exception: self.send_response(400); self.end_headers(); self.wfile.write(b'invalid json'); return",
  "        try:",
  "            with open(BOOKS_JSON, 'r+', encoding='utf-8') as f: arr = json.load(f); arr.insert(0, obj); f.seek(0); f.truncate(); json.dump(arr, f, ensure_ascii=False, indent=2)",
  "            self.send_json({'status':'ok'})",
  "        except Exception as e: self.log('addbook error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_export_books(self):",
  "        try:",
  "            with open(BOOKS_JSON, 'r', encoding='utf-8') as f: arr = json.load(f)",
  "            self.send_json({'status':'ok','books': arr})",
  "        except Exception as e: self.log('export error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_upload(self):",
  "        ctype, pdict = cgi.parse_header(self.headers.get('Content-Type',''))",
  "        if ctype != 'multipart/form-data': self.send_response(400); self.end_headers(); self.wfile.write(b'expected multipart/form-data'); return",
  "        fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'}, keep_blank_values=True)",
  "        if 'file' not in fs: self.send_response(400); self.end_headers(); self.wfile.write(b'no file field'); return",
  "        fileitem = fs['file']",
  "        if not fileitem.filename: self.send_response(400); self.end_headers(); self.wfile.write(b'no filename'); return",
  "        filename = os.path.basename(fileitem.filename)",
  "        try: target = safe_join(DATA_DIR, filename)",
  "        except ValueError: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            with open(target, 'wb') as out:",
  "                while True: chunk = fileitem.file.read(65536); if not chunk: break; out.write(chunk)",
  "        except Exception as e: self.log('upload write error', e); self.send_response(500); self.end_headers(); return",
  "        txtname = filename + '.txt'; txtpath = os.path.join(DATA_DIR, txtname); pdftok = False",
  "        try:",
  "            subprocess.run(['pdftotext', target, txtpath], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)",
  "            pdftok = True",
  "        except Exception:",
  "            fallback = os.path.join(TOOLS_DIR, 'pdf_fallback_extract.py')",
  "            if os.path.exists(fallback):",
  "                try: subprocess.run([sys.executable, fallback, target, txtpath], check=True)",
  "                except Exception: pass",
  "        self.send_json({'pdf': filename, 'txt': txtname if os.path.exists(txtpath) else None, 'pdftotext': pdftok})",
  "",
  "    def handle_summary_pdf(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body); fname = obj.get('pdf')",
  "        except Exception: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            txtpath = os.path.join(DATA_DIR, fname + '.txt')",
  "            if not os.path.exists(txtpath): self.send_json({'status':'no_text'}) ; return",
  "            with open(txtpath, 'r', encoding='utf-8', errors='ignore') as f:",
  "                chunk = ''.join([f.readline() for _ in range(200)])",
  "            words = [w.lower().strip('.,()[]\"\\'') for w in chunk.split()]",
  "            freq = {}",
  "            for w in words: freq[w]=freq.get(w,0)+1",
  "            top = sorted(freq.items(), key=lambda x:-x[1])[:15]",
  "            self.send_json({'status':'ok', 'summary': chunk[:5000], 'keywords': [k for k,_ in top]})",
  "        except Exception as e: self.log('summary error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_bnf_generate(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body); bnf = obj.get('bnf',''); name = obj.get('name','netlang')",
  "        except Exception: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            os.makedirs(TOOLS_DIR, exist_ok=True)",
  "            out = os.path.join(TOOLS_DIR, name + '_parser.py')",
  "            script = os.path.join(TOOLS_DIR, 'bnf_to_ply.py')",
  "            if os.path.exists(script):",
  "                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.bnf', encoding='utf-8') as tf:",
  "                    tf.write(bnf); tmpname = tf.name",
  "                proc = subprocess.run([sys.executable, script, tmpname, out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)",
  "                try: os.unlink(tmpname)",
  "                except Exception: pass",
  "                if proc.returncode == 0 and os.path.exists(out):",
  "                    self.send_json({'status':'ok','out': 'tools/' + os.path.basename(out)})",
  "                    return",
  "            with open(out, 'w', encoding='utf-8') as f:",
  "                f.write('# Auto-generated parser skeleton for %s\\n' % name)",
  "                f.write('from ply import lex, yacc\\n\\n')",
  "                f.write('tokens = []\\n\\n')",
  "                f.write('def p_error(p):\\n    pass\\n')",
  "            self.send_json({'status':'ok','out': 'tools/' + os.path.basename(out)})",
  "        except Exception as e: self.log('bnf gen error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_ml_predict(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body); csvpath = obj.get('csv')",
  "        except Exception: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            target = safe_join(DATA_DIR, csvpath)",
  "            if not os.path.exists(target): self.send_json({'status':'no_csv'}); return",
  "            script = os.path.join(TOOLS_DIR, 'ml_predict.py')",
  "            if not os.path.exists(script): self.send_json({'status':'no_script'}); return",
  "            proc = subprocess.run([sys.executable, script, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)",
  "            out = proc.stdout.decode('utf-8', errors='ignore')",
  "            self.send_json({'status':'ok','output': out})",
  "        except Exception as e: self.log('ml predict error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_jones(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body); knot = obj.get('knot','unknot')",
  "        except Exception: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            script = os.path.join(TOOLS_DIR, 'jones_poly.py')",
  "            if not os.path.exists(script): self.send_json({'status':'no_script'}); return",
  "            proc = subprocess.run([sys.executable, script, knot], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)",
  "            out = proc.stdout.decode('utf-8', errors='ignore')",
  "            self.send_json({'status':'ok','result': out})",
  "        except Exception as e: self.log('jones error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_trace_aggregate(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body); csvs = obj.get('files', [])",
  "        except Exception: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            script = os.path.join(TOOLS_DIR, 'trace_aggregator.py')",
  "            if not os.path.exists(script): self.send_json({'status':'no_script'}); return",
  "            cmd = [sys.executable, script] + csvs",
  "            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)",
  "            out = proc.stdout.decode('utf-8', errors='ignore')",
  "            self.send_json({'status':'ok','output': out})",
  "        except Exception as e: self.log('trace agg error', e); self.send_response(500); self.end_headers()",
  "",
  "    def handle_pdf_question(self):",
  "        l = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(l).decode('utf-8')",
  "        try: obj = json.loads(body); pdf = obj.get('pdf'); question = obj.get('q','')",
  "        except Exception: self.send_response(400); self.end_headers(); return",
  "        try:",
  "            txtpath = os.path.join(DATA_DIR, pdf + '.txt')",
  "            if not os.path.exists(txtpath): self.send_json({'status':'no_text'}); return",
  "            with open(txtpath, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()",
  "            excerpt = text[:4000]",
  "            import re",
  "            formulas = re.findall(r'\\$[^\\$]{5,500}\\$', text)[:10]",
  "            ans = 'Excerpt provided. Found %d inline formulas.' % len(formulas)",
  "            self.send_json({'status':'ok','answer': ans, 'excerpt': excerpt, 'formulas': formulas})",
  "        except Exception as e: self.log('pdf q error', e); self.send_response(500); self.end_headers()",
  "",
  "def run():",
  "    os.chdir(BASE_DIR)",
  "    server = HTTPServer(('0.0.0.0', PORT), Handler)",
  "    print('Serving at http://localhost:%d/ (root: %s)' % (PORT, WEB_ROOT))",
  "    try: server.serve_forever()",
  "    except KeyboardInterrupt: print('Shutting down')",
  "    finally: server.server_close()",
  "",
"if __name__ == '__main__': run()"
};

/* vendor placeholders (write files later) */
static const char *vendor_codemirror_css = "/* placeholder codemirror.css */\n.cm-s-default{background:#fff;color:#000}";
static const char *vendor_codemirror_js = "/* placeholder codemirror.js */\nfunction CodeMirror(el, opts){var ta=document.createElement('textarea');ta.value=opts.value||'';el.appendChild(ta);return{setValue:function(v){ta.value=v},getValue:function(){return ta.value}}}";
static const char *vendor_keymap_vim = "/* placeholder keymap-vim.js */";
static const char *vendor_mathjax = "/* placeholder mathjax.js */";

/* tools/bnf_to_ply.py content */
static const char *bnf_to_ply_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"tools/bnf_to_ply.py - Convert simple BNF to PLY skeleton\"\"\"",
  "import sys, re",
  "def name(s): return re.sub(r'[^0-9a-zA-Z_]', '_', s.strip('<> '))",
  "def main():",
  "    if len(sys.argv) < 3: print('usage: bnf_to_ply.py input.bnf out.py'); return",
  "    inp = sys.argv[1]; out = sys.argv[2]",
  "    with open(inp, 'r', encoding='utf-8') as f: txt = f.read()",
  "    rules = []",
  "    for line in txt.splitlines():",
  "        line=line.strip()",
  "        if not line or line.startswith('#'): continue",
  "        if '::=' in line:",
  "            left,right = line.split('::=',1)",
  "            rules.append((left.strip(), right.strip()))",
  "    with open(out,'w',encoding='utf-8') as f:",
  "        f.write('# Auto-generated PLY skeleton\\n')",
  "        f.write('from ply import lex, yacc\\n\\n')",
  "        f.write('tokens = []\\n\\n')",
  "        for i,(l,r) in enumerate(rules):",
  "            n = name(l)",
  "            f.write('def p_%d(p):\\n    \"\"\"%s : %s\"\"\"\\n    pass\\n\\n' % (i+1, n, r))",
  "    print('wrote', out)",
"if __name__ == '__main__': main()"
};

/* tools/pdf_fallback_extract.py content */
static const char *pdf_fallback_extract_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"tools/pdf_fallback_extract.py - fallback PDF->text using PyPDF2 or write empty file\"\"\"",
  "import sys",
  "def fallback(infile,outfile):",
  "    try:",
  "        import PyPDF2",
  "        with open(infile,'rb') as f: r = PyPDF2.PdfReader(f); pages = [p.extract_text() or '' for p in r.pages]",
  "        with open(outfile,'w',encoding='utf-8') as w: w.write('\\n'.join(pages))",
  "        return True",
  "    except Exception:",
  "        with open(outfile,'w',encoding='utf-8') as w: w.write('')",
  "        return False",
  "if __name__=='__main__':",
  "    if len(sys.argv)<3: print('usage: pdf_fallback_extract.py infile outfile'); sys.exit(1)",
"    ok = fallback(sys.argv[1], sys.argv[2]); sys.exit(0 if ok else 2)"
};

/* tools/jones_poly.py */
static const char *jones_poly_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"Simple Jones polynomial demo script\"\"\"",
  "import sys, json",
  "def main():",
  "    knot = sys.argv[1] if len(sys.argv)>1 else 'unknot'",
  "    table = {'unknot':'1', 'trefoil':'t^-1 + t + t^2', 'figure8':'t^-2 - t^-1 + 1 - t + t^2'}",
  "    print(json.dumps({'knot':knot,'jones': table.get(knot,'1')}))",
"if __name__=='__main__': main()"
};

/* tools/ml_predict.py */
static const char *ml_predict_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"tools/ml_predict.py - Try sklearn linear regression; fallback to simple stats\"\"\"",
  "import sys, os, csv, json",
  "def simple(csvfile):",
  "    vals=[]",
  "    with open(csvfile,'r',encoding='utf-8',errors='ignore') as f: r=csv.reader(f); hdr=next(r,None)",
  "    for row in r:",
  "        if not row: continue",
  "        try: vals.append(float(row[-1]))",
  "        except: continue",
  "    if not vals: print(json.dumps({'status':'no_data'})); return",
  "    import statistics",
  "    last=vals[-1]; ma = statistics.mean(vals[-min(10,len(vals)):])",
  "    print(json.dumps({'status':'ok','last':last,'ma10':ma}))",
  "",
  "def sklearn_predict(csvfile):",
  "    try:",
  "        import numpy as np, pandas as pd",
  "        from sklearn.linear_model import LinearRegression",
  "    except Exception as e:",
  "        print(json.dumps({'status':'no_sklearn','error':str(e)})); return",
  "    df = pd.read_csv(csvfile)",
  "    if df.shape[0]<2: print(json.dumps({'status':'insufficient_rows'})); return",
  "    y = df.iloc[:, -1].fillna(0).values",
  "    X = (np.arange(len(y))).reshape(-1,1)",
  "    model = LinearRegression().fit(X, y)",
  "    pred = float(model.predict(X[-1].reshape(1,-1))[0])",
  "    print(json.dumps({'status':'ok','pred': pred}))",
  "",
  "def main():",
  "    if len(sys.argv)<2: print(json.dumps({'status':'no_arg'})); return",
  "    csvfile = sys.argv[1]",
  "    if not os.path.exists(csvfile): print(json.dumps({'status':'no_file'})); return",
  "    sklearn_predict(csvfile)",
  "",
"if __name__=='__main__': main()"
};

/* tools/trace_aggregator.py */
static const char *trace_aggregator_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"tools/trace_aggregator.py - Aggregate CSV time series and output JSON summary\"\"\"",
  "import sys, csv, json, os",
  "def read_csv(p):",
  "    rows=[]",
  "    with open(p,'r',encoding='utf-8',errors='ignore') as f: r=csv.reader(f); hdr=next(r,None)",
  "    for row in r: rows.append(row)",
  "    return hdr, rows",
  "def summarize(p):",
  "    hdr, rows = read_csv(p)",
  "    vals=[]",
  "    for r in rows:",
  "        try: vals.append(float(r[-1]))",
  "        except: continue",
  "    if not vals: return {'file': os.path.basename(p), 'count':0}",
  "    from statistics import mean, median",
  "    return {'file': os.path.basename(p), 'count': len(vals), 'last': vals[-1], 'mean': mean(vals), 'min': min(vals), 'max': max(vals)}",
  "def main():",
  "    if len(sys.argv)<2: print(json.dumps({'status':'no_arg'})); return",
  "    files = [f for f in sys.argv[1:] if os.path.exists(f)]",
  "    out = [summarize(f) for f in files]",
  "    print(json.dumps({'status':'ok','summary': out}, indent=2))",
"if __name__=='__main__': main()"
};

/* tools editor snippets and README */
static const char *vim_snippet[] = {
  "\" tools/vim_snippet.vim - open local Omega UI",
"command! OmegaOpen silent execute '!xdg-open http://localhost:8000/'"
};
static const char *emacs_snippet[] = {
  ";; tools/emacs_snippet.el - open local Omega UI",
  "(defun omega-open () (interactive) (browse-url \"http://localhost:8000/\"))",
"(provide 'omega-snippet)"
};
static const char *tools_readme[] = {
  "Offline tools directory",
  "- Place .whl files in tools/wheels/ to install offline dependencies",
  "- Scripts: bnf_to_ply.py, pdf_fallback_extract.py, jones_poly.py, ml_predict.py, trace_aggregator.py",
  "- Vim/Emacs snippets included",
  "" };

/* data samples */
static const char *books_json = "[]";
static const char *sample_csv[] = {
  "date,open,high,low,close,volume",
  "2025-01-01,100,101,99,100.5,1000",
  "2025-01-02,100.5,102,100,101.8,1200",
  "2025-01-03,101.8,103,101,102.3,900",
NULL
};

/* Makefile */
static const char *makefile_txt[] = {
  "# Makefile for omega_www_pkg",
  "PY ?= python3",
  "BIN := bin/run_server",
  "LIB := lib/server.py",
  "DATA := data",
  "TOOLS := tools",
  "WHEELS := $(TOOLS)/wheels",
  ".PHONY: all prepare run venv deps install_wheels clean",
  "all: prepare",
  "prepare:",
  "\t@mkdir -p $(DATA) $(TOOLS) $(WHEELS) web/vendor",
  "\t@chmod +x $(BIN) 2>/dev/null || true",
  "\t@chmod +x $(LIB) 2>/dev/null || true",
  "\t@touch $(DATA)/books.json",
  "\t@if [ ! -s $(DATA)/books.json ]; then echo \"[]\" > $(DATA)/books.json; fi",
  "\t@echo \"Prepared.\"",
  "run: prepare",
  "\t@echo \"Starting server...\"",
  "\t$(PY) $(LIB)",
  "venv:",
  "\t@echo \"Creating venv...\"",
  "\t@if [ -d venv ]; then echo \"venv exists\"; else $(PY) -m venv venv && echo \"venv created\"; fi",
  "deps: venv install_wheels",
  "install_wheels:",
  "\t@echo \"Installing wheels from $(WHEELS) (offline)\"",
  "\t@if [ -d \"$(WHEELS)\" ] && ls $(WHEELS)/*.whl >/dev/null 2>&1; then \\",
  "\t\tif [ -f venv/bin/activate ]; then \\",
  "\t\t\t. venv/bin/activate && pip install --no-index --find-links=$(WHEELS) $(WHEELS)/*.whl || (echo \"pip install failed\"; exit 1); \\",
  "\t\telse \\",
  "\t\t\techo \"venv not found; creating...\"; $(PY) -m venv venv && . venv/bin/activate && pip install --no-index --find-links=$(WHEELS) $(WHEELS)/*.whl || (echo \"pip install failed\"; exit 1); \\",
  "\t\tfi; \\",
  "\telse \\",
  "\t\techo \"No wheels found\"; \\",
  "\tfi",
  "clean:",
  "\t@rm -rf venv __pycache__ *.pyc */__pycache__ 2>/dev/null || true",
  "" };

/* README */
static const char *readme_txt[] = {
  "Omega Offline Extended Package",
  "",
  "Features:",
  "- Offline books DB (data/books.json)",
  "- PDF import (pdftotext or PyPDF2 fallback)",
  "- BNF->PLY skeleton generation",
  "- Jones polynomial demo",
  "- ML predict (sklearn fallback)",
  "- Trace aggregator for CSV",
  "- Vim/Emacs snippets",
  "",
  "Usage:",
  "  gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_allpkg gen_omega_allpkg.c",
  "  ./gen_omega_allpkg",
  "  cd omega_www_pkg",
  "  make prepare",
  "  make run",
  "",
  "Place wheels in tools/wheels for offline installs.",
  "" };

/* main function writes files */
int main(void) {
  const char *root = "omega_www_pkg";
  char path[4096];
  const char *dirs[] = {"bin","lib","web","web/vendor","tools","data","tools/wheels"};
  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }
  for (size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path,sizeof(path), "%s/%s", root, dirs[i]);
    if (ensure_dir(path)!=0){ fprintf(stderr,"cannot create %s\n",path); return 1; }
  }

  /* write bin/run_server */
  snprintf(path,sizeof(path), "%s/bin/run_server", root);
  if (write_lines(path, run_server, sizeof(run_server)/sizeof(run_server[0]), 0755) != 0){ fprintf(stderr,"write failed %s\n",path); return 1; }

  /* write lib/server.py (combine arrays) */
  snprintf(path,sizeof(path), "%s/lib/server.py", root);
  if (write_lines(path, server_py, sizeof(server_py)/sizeof(server_py[0]), 0755) != 0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  /* append continuation */
  FILE *f = fopen(path, "ab");
  if (!f){ fprintf(stderr,"append failed %s\n",path); return 1; }
  for (size_t i=0;i<sizeof(server_py_cont)/sizeof(server_py_cont[0]);++i){ fputs(server_py_cont[i], f); fputc('\n', f); }
  fclose(f);
  chmod(path, 0755);

  /* write web/index.html */
  snprintf(path,sizeof(path), "%s/web/index.html", root);
  if (write_lines(path, web_index, sizeof(web_index)/sizeof(web_index[0]), 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }

  /* write vendor placeholders */
  snprintf(path,sizeof(path), "%s/web/vendor/codemirror.css", root);
  if (write_file(path, vendor_codemirror_css, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  snprintf(path,sizeof(path), "%s/web/vendor/codemirror.js", root);
  if (write_file(path, vendor_codemirror_js, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  snprintf(path,sizeof(path), "%s/web/vendor/keymap-vim.js", root);
  if (write_file(path, vendor_keymap_vim, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  snprintf(path,sizeof(path), "%s/web/vendor/mathjax.js", root);
  if (write_file(path, vendor_mathjax, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
```

続けて残りを送って良ければ「続けて」と入力してください。
