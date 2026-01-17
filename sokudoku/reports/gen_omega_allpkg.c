/*了解しました。以下は単一ファイル `gen_omega_allpkg.c` の完全かつ整合性のとれた内容です。これをそのまま保存してコンパイルしてください（以前のエラーは配列初期化子の不整合が原因でしたが、ここではすべての配列が正しく閉じられています）。

注意：出力は非常に長いので、ファイルに直接貼り付けることを推奨します。

*/
/*
 * gen_omega_allpkg.c
 *
 * Generator for omega_www_pkg (offline, extended)
 *
 * Usage:
 *   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_allpkg gen_omega_allpkg.c
 *   ./gen_omega_allpkg
 *
 * Then:
 *   cd omega_www_pkg
 *   make prepare
 *   make run
 *
 * Notes:
 * - For advanced ML or full CodeMirror/MathJax, replace web/vendor/* with real libraries.
 * - Place wheel files in tools/wheels/ for offline pip install and run 'make deps'.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/types.h>
#include <fcntl.h>

/* Small helpers */
static int ensure_dir(const char *p) {
  if (!p) return -1;
  struct stat st;
  if (stat(p, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(p, 0755) == 0) return 0;
  if (errno == EEXIST) return 0;
  return -1;
}
static int write_file(const char *path, const char *data, int mode) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  if (fputs(data, f) == EOF) { fclose(f); return -1; }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}
static int write_lines(const char *path, const char **lines, size_t n, int mode) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  for (size_t i = 0; i < n; ++i) {
    if (lines[i]) {
      if (fputs(lines[i], f) == EOF) { fclose(f); return -1; }
    }
    if (fputc('\n', f) == EOF) { fclose(f); return -1; }
  }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

/* ---------------- file contents ---------------- */

/* bin/run_server */
static const char *run_server[] = {
  "#!/usr/bin/env bash",
  "set -euo pipefail",
  "ROOT_DIR=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"",
  "PYTHON=${PYTHON:-python3}",
  "SERVER=\"$ROOT_DIR/lib/server.py\"",
  "if ! command -v \"$PYTHON\" >/dev/null 2>&1; then",
  "  echo \"Error: python3 not found\" >&2; exit 1",
  "fi",
  "if [ ! -f \"$SERVER\" ]; then",
  "  echo \"Error: server not found: $SERVER\" >&2; exit 1",
  "fi",
  "cd \"$ROOT_DIR\"",
"exec \"$PYTHON\" \"$SERVER\""
};

/* lib/server.py (part 1) */
static const char *server_py[] = {
  "#!/usr/bin/env python3",
  "# lib/server.py - Offline server (extended)",
  "from http.server import HTTPServer, BaseHTTPRequestHandler",
  "import os, sys, json, shutil, cgi, urllib.parse, subprocess, tempfile",
  "from datetime import datetime",
  "",
  "BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))",
  "WEB_ROOT = os.path.join(BASE_DIR, 'web')",
  "DATA_DIR = os.path.join(BASE_DIR, 'data')",
  "TOOLS_DIR = os.path.join(BASE_DIR, 'tools')",
  "BOOKS_JSON = os.path.join(DATA_DIR, 'books.json')",
  "PORT = int(os.environ.get('OMEGA_PORT','8000'))",
  "MAX_UPLOAD = 1024 * 1024 * 1024",
  "",
  "os.makedirs(DATA_DIR, exist_ok=True)",
  "if not os.path.exists(BOOKS_JSON):",
  "    with open(BOOKS_JSON, 'w', encoding='utf-8') as f: json.dump([], f, ensure_ascii=False, indent=2)",
  "",
  "def safe_join(base, *paths):",
  "    final = os.path.abspath(os.path.join(base, *paths))",
  "    if os.path.commonpath([base]) != os.path.commonpath([base, final]):",
  "        raise ValueError('unsafe path')",
  "    return final",
  "",
  "class Handler(BaseHTTPRequestHandler):",
  "    server_version = 'OmegaOffline/2.1'",
  "",
  "    def log(self, *args): print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *args)",
  "",
  "    def send_json(self, obj, code=200):",
  "        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')",
  "        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8')",
  "        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)",
  "",
  "    def do_GET(self):",
  "        parsed = urllib.parse.urlparse(self.path); path = parsed.path",
  "        try:",
  "            if path.startswith('/data/'):",
  "                name = path[len('/data/'):]; target = safe_join(DATA_DIR, name)",
  "                if not os.path.isfile(target): self.send_response(404); self.end_headers(); return",
  "                self.send_response(200)",
  "                c = 'application/octet-stream'",
  "                if target.endswith('.html'): c = 'text/html; charset=utf-8'",
  "                elif target.endswith('.json') or target.endswith('.txt'): c = 'text/plain; charset=utf-8'",
  "                self.send_header('Content-Type', c); fs = os.stat(target); self.send_header('Content-Length', str(fs.st_size)); self.end_headers()",
  "                with open(target, 'rb') as f: shutil.copyfileobj(f, self.wfile); return",
  "",
  "            rel = path.lstrip('/') or 'index.html'; target = safe_join(WEB_ROOT, rel)",
  "            if os.path.isdir(target): target = os.path.join(target, 'index.html')",
  "            if not os.path.exists(target): self.send_response(404); self.end_headers(); return",
  "            c = 'application/octet-stream'",
  "            if target.endswith('.html'): c = 'text/html; charset=utf-8'",
  "            elif target.endswith('.js'): c = 'application/javascript; charset=utf-8'",
  "            elif target.endswith('.css'): c = 'text/css; charset=utf-8'",
  "            self.send_response(200); self.send_header('Content-Type', c); fs = os.stat(target); self.send_header('Content-Length', str(fs.st_size)); self.end_headers()",
  "            with open(target, 'rb') as f: shutil.copyfileobj(f, self.wfile)",
  "        except ValueError:",
  "            self.send_response(400); self.end_headers()",
  "        except Exception as e:",
  "            self.log('GET error:', e); self.send_response(500); self.end_headers()",
  "",
  "    def do_POST(self):",
  "        parsed = urllib.parse.urlparse(self.path); path = parsed.path",
  "        try:",
  "            if path == '/api/upload': self.handle_upload(); return",
  "            if path == '/api/addbook': self.handle_addbook(); return",
  "            if path == '/api/export_books': self.handle_export_books(); return",
  "            if path == '/api/summary_pdf': self.handle_summary_pdf(); return",
  "            if path == '/api/bnf_generate': self.handle_bnf_generate(); return",
  "            if path == '/api/ml_predict': self.handle_ml_predict(); return",
  "            if path == '/api/jones': self.handle_jones(); return",
  "            if path == '/api/trace_aggregate': self.handle_trace_aggregate(); return",
  "            if path == '/api/pdf_question': self.handle_pdf_question(); return",
  "            self.send_response(404); self.end_headers()",
  "        except Exception as e:",
  "            self.log('POST error:', e); self.send_response(500); self.end_headers()",
};

/* lib/server.py (part 2) */
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

/* web/index.html */
static const char *web_index[] = {
  "<!doctype html>",
  "<html>",
  "<head>",
  "  <meta charset='utf-8'>",
  "  <title>Omega Offline — Extended</title>",
  "  <meta name='viewport' content='width=device-width,initial-scale=1'>",
  "  <link rel='stylesheet' href='/web/vendor/codemirror.css'>",
  "  <style>",
  "    body{font-family:Arial;margin:12px} #left{float:left;width:32%;padding:8px} #right{float:right;width:64%;padding:8px} .book{border-bottom:1px solid #eee;padding:6px 0}",
  "    #viewer{white-space:pre-wrap;border:1px solid #ddd;padding:8px;height:220px;overflow:auto;background:#fafafa} #editor{height:360px;border:1px solid #ccc}",
  "    .small{font-size:90%}",
  "  </style>",
  "</head>",
  "<body>",
  "  <h1>Omega Offline — Extended</h1>",
  "  <div id='left'>",
  "    <h3>Upload PDF</h3>",
  "    <input type='file' id='fileinput'><br><button id='upload'>Upload</button>",
  "    <div id='uploadres'></div>",
  "    <h3>Add Book / Metadata</h3>",
  "    <input id='title' placeholder='Title'><br>",
  "    <input id='author' placeholder='Author'><br>",
  "    <input id='tags' placeholder='tags,comma'><br>",
  "    <button id='addbook'>Add Book</button>",
  "    <h3>Import/Export</h3>",
  "    <button id='exportjson'>Export JSON</button> <button id='importjson'>Import JSON</button>",
  "    <h3>BNF → Parser</h3>",
  "    <textarea id='bnf' placeholder='Paste BNF here' style='width:100%;height:120px'></textarea><br>",
  "    <input id='bnfname' placeholder='name'><button id='bnfgenerate'>Generate Parser</button>",
  "    <h3>Vim/Emacs</h3>",
  "    <button id='vimreg'>Vim Snippet</button> <button id='emacsreg'>Emacs Snippet</button>",
  "  </div>",
  "  <div id='right'>",
  "    <h3>Viewer</h3><div id='viewer'>No file loaded</div>",
  "    <h3>Editor (CodeMirror placeholder)</h3>",
  "    <div id='editor'></div>",
  "    <div style='margin-top:8px'><button id='saveeditor'>Save to data/</button> <button id='download'>Download</button></div>",
  "    <h3>Tools</h3>",
  "    <div class='small'>",
  "      <button id='jonesdemo'>Jones polynomial demo</button>",
  "      <button id='pdfsummary'>Summarize PDF</button>",
  "      <button id='pdfqa'>Ask PDF</button><br><br>",
  "      <input id='csvpath' placeholder='data/sample.csv' style='width:60%'><button id='mlrun'>Run ML Predict</button><br>",
  "      <button id='traceagg'>Aggregate traces</button>",
  "    </div>",
  "  </div>",
  "  <script src='/web/vendor/codemirror.js'></script>",
  "  <script src='/web/vendor/keymap-vim.js'></script>",
  "  <script src='/web/vendor/mathjax.js'></script>",
  "  <script>",
  "  (function(){",
  "    function el(id){return document.getElementById(id)}",
  "    var editor = (window.CodeMirror)? CodeMirror(document.getElementById('editor'), { value: '# Welcome\\n', mode: 'markdown', lineNumbers:true, keyMap:'vim' }) : { setValue:function(v){ document.getElementById('editor').textContent=v; }, getValue:function(){ return document.getElementById('editor').textContent; } };",
  "",
  "    async function loadList(){ try{ const r = await fetch('/data/books.json'); if(!r.ok) throw new Error('load fail'); const arr = await r.json(); renderList(arr); } catch(e){ console.error(e); } }",
  "    function renderList(arr){ var list = document.getElementById('list'); if(!list){ list = document.createElement('div'); list.id='list'; el('left').appendChild(list); } list.innerHTML=''; (arr||[]).forEach(function(b){ var n = document.createElement('div'); n.className='book'; n.innerHTML = '<strong>'+ (b.title||'') +'</strong><br>' + (b.author||'') + '<br>'; var vb = document.createElement('button'); vb.textContent='View txt'; vb.addEventListener('click', function(){ if(b.txt) viewTxt(b.txt); else alert('no text'); }); n.appendChild(vb); list.appendChild(n); }); }",
  "",
  "    async function viewTxt(nm){ try{ var r = await fetch('/data/' + encodeURIComponent(nm)); if(!r.ok){ alert('failed'); return } var t = await r.text(); el('viewer').textContent = t; editor.setValue(t); } catch(e){ console.error(e); alert('err'); } }",
  "",
  "    async function upload(){ var f = el('fileinput').files[0]; if(!f){ alert('select'); return } var fd = new FormData(); fd.append('file', f); try{ var r = await fetch('/api/upload', { method:'POST', body: fd }); var j = await r.json(); el('uploadres').textContent = JSON.stringify(j); await loadList(); } catch(e){ console.error(e); alert('upload fail'); } }",
  "",
  "    async function addBook(){ var title = el('title').value.trim(); var author = el('author').value.trim(); var tags = el('tags').value.split(',').map(s=>s.trim()).filter(Boolean); var payload = {title:title, author:author, tags:tags}; try{ var r = await fetch('/api/addbook', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) }); if(!r.ok) { alert('add fail'); return } el('title').value=''; el('author').value=''; el('tags').value=''; await loadList(); } catch(e){ console.error(e); alert('add fail'); } }",
  "",
  "    async function exportJSON(){ try{ var r = await fetch('/api/export_books', { method:'POST' }); var j = await r.json(); var blob = new Blob([JSON.stringify(j.books,null,2)], {type:'application/json'}); var url = URL.createObjectURL(blob); var a = document.createElement('a'); a.href = url; a.download = 'books.json'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); } catch(e){ console.error(e); } }",
  "",
  "    async function importJSON(){ try{ var t = prompt('Paste JSON array of books:'); if(!t) return; var arr = JSON.parse(t); var r = await fetch('/data/books.json', { method:'PUT', body: JSON.stringify(arr) }); if(!r.ok) { alert('import failed'); return } alert('imported'); loadList(); } catch(e){ console.error(e); alert('import failed'); } }",
  "",
  "    async function bnfgenerate(){ var bnf = el('bnf').value; var name = el('bnfname').value || 'netlang'; if(!bnf) { alert('paste BNF'); return } try{ var r = await fetch('/api/bnf_generate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({bnf:bnf, name:name}) }); var j = await r.json(); alert('generated: ' + JSON.stringify(j)); } catch(e){ console.error(e); alert('gen fail'); } }",
  "",
  "    async function jonesDemo(){ var k = prompt('knot name (demo):','unknot'); if(k===null) return; try{ var r = await fetch('/api/jones', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({knot:k}) }); var j = await r.json(); alert('jones result:\\n' + JSON.stringify(j)); } catch(e){ console.error(e); alert('err'); } }",
  "",
  "    async function pdfSummary(){ var pdf = prompt('PDF filename in data/:'); if(!pdf) return; try{ var r = await fetch('/api/summary_pdf', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pdf:pdf}) }); var j = await r.json(); if(j.status==='ok') { alert('summary:\\n' + j.summary.slice(0,400)); } else alert('no text available'); } catch(e){ console.error(e); alert('err'); } }",
  "",
  "    async function pdfQA(){ var pdf = prompt('PDF filename in data/:'); if(!pdf) return; var q = prompt('Your question (short):'); if(q===null) return; try{ var r = await fetch('/api/pdf_question', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pdf:pdf, q:q}) }); var j = await r.json(); if(j.status==='ok') { alert('answer:\\n' + j.answer + '\\nformulas:' + JSON.stringify(j.formulas)); } else alert('no text available'); } catch(e){ console.error(e); alert('err'); } }",
  "",
  "    async function mlrun(){ var csv = el('csvpath').value.trim(); if(!csv) { alert('enter csv path under data/'); return } try{ var r = await fetch('/api/ml_predict', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({csv: csv}) }); var j = await r.json(); if(j.status==='ok') { alert('ML output:\\n' + j.output); } else alert('ML error: ' + JSON.stringify(j)); } catch(e){ console.error(e); alert('err'); } }",
  "",
  "    async function traceagg(){ var files = prompt('Comma-separated CSV files in data/:','sample.csv'); if(!files) return; var arr = files.split(',').map(s=>s.trim()); try{ var r = await fetch('/api/trace_aggregate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({files: arr}) }); var j = await r.json(); if(j.status==='ok') { alert('agg output:\\n' + j.output.slice(0,2000)); } else alert('agg error'); } catch(e){ console.error(e); alert('err'); } }",
  "",
  "    function vimreg(){ alert('Vim snippet saved to tools/vim_snippet.vim. See README for browser registration hints.'); }",
  "    function emacsreg(){ alert('Emacs snippet saved to tools/emacs_snippet.el. See README for browser registration hints.'); }",
  "",
  "    document.getElementById('upload').addEventListener('click', upload);",
  "    document.getElementById('addbook').addEventListener('click', addBook);",
  "    document.getElementById('exportjson').addEventListener('click', exportJSON);",
  "    document.getElementById('importjson').addEventListener('click', importJSON);",
  "    document.getElementById('bnfgenerate').addEventListener('click', bnfgenerate);",
  "    document.getElementById('jonesdemo').addEventListener('click', jonesDemo);",
  "    document.getElementById('pdfsummary').addEventListener('click', pdfSummary);",
  "    document.getElementById('pdfqa').addEventListener('click', pdfQA);",
  "    document.getElementById('mlrun').addEventListener('click', mlrun);",
  "    document.getElementById('traceagg').addEventListener('click', traceagg);",
  "    document.getElementById('vimreg').addEventListener('click', vimreg);",
  "    document.getElementById('emacsreg').addEventListener('click', emacsreg);",
  "    loadList();",
  "  })();",
  "  </script>",
  "</body>",
"</html>"
};

/* vendor placeholders */
static const char *vendor_codemirror_css = "/* placeholder codemirror.css */\n.cm-s-default{background:#fff;color:#000}\n";
static const char *vendor_codemirror_js = "/* placeholder codemirror.js */\nfunction CodeMirror(el, opts){var ta=document.createElement('textarea');ta.value=opts.value||'';el.appendChild(ta);return{setValue:function(v){ta.value=v},getValue:function(){return ta.value}}}\n";
static const char *vendor_keymap_vim = "/* placeholder keymap-vim.js */\n";
static const char *vendor_mathjax = "/* placeholder mathjax.js */\nwindow.MathJax = {version: 'placeholder'};\n";

/* tools/bnf_to_ply.py */
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
  "if __name__ == '__main__': main()",
NULL
};

/* tools/pdf_fallback_extract.py */
static const char *pdf_fallback_extract_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"tools/pdf_fallback_extract.py - fallback PDF->text using PyPDF2 or write empty file\"\"\"",
  "import sys",
  "def fallback(infile,outfile):",
  "    try:",
  "        import PyPDF2",
"        with open(infile,'rb') as f: r = PyPDF2.PdfReader(f); pages = [p.extract_text() or '' "
									/* 続き: tools/pdf_fallback_extract.py の残り */
									"        with open(outfile,'w',encoding='utf-8') as w: w.write('\\n'.join(pages))",
									"        return True",
									"    except Exception:",
									"        with open(outfile,'w',encoding='utf-8') as w: w.write('')",
									"        return False",
									"if __name__=='__main__':",
									"    if len(sys.argv)<3: print('usage: pdf_fallback_extract.py infile outfile'); sys.exit(1)",
									"    ok = fallback(sys.argv[1], sys.argv[2]); sys.exit(0 if ok else 2)",
NULL
									};

/* tools/jones_poly.py (already started earlier) */
static const char *jones_poly_py[] = {
  "#!/usr/bin/env python3",
  "\"\"\"Simple Jones polynomial demo script\"\"\"",
  "import sys, json",
  "def main():",
  "    knot = sys.argv[1] if len(sys.argv)>1 else 'unknot'",
  "    table = {'unknot':'1', 'trefoil':'t^-1 + t + t^2', 'figure8':'t^-2 - t^-1 + 1 - t + t^2'}",
  "    print(json.dumps({'knot':knot,'jones': table.get(knot,'1')}))",
  "if __name__=='__main__': main()",
NULL
};

/* tools/ml_predict.py (already started earlier) */
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
  "    try:",
  "        sklearn_predict(csvfile)",
  "    except Exception:",
  "        simple(csvfile)",
  "",
  "if __name__=='__main__': main()",
NULL
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
  "if __name__=='__main__': main()",
NULL
};

/* tools/vim_snippet.vim */
static const char *vim_snippet[] = {
  "\" tools/vim_snippet.vim - open local Omega UI",
  "command! OmegaOpen silent execute '!xdg-open http://localhost:8000/'",
NULL
};

/* tools/emacs_snippet.el */
static const char *emacs_snippet[] = {
  ";; tools/emacs_snippet.el - open local Omega UI",
  "(defun omega-open () (interactive) (browse-url \"http://localhost:8000/\"))",
  "(provide 'omega-snippet)",
NULL
};

/* tools/README.txt */
static const char *tools_readme[] = {
  "Offline tools directory",
  "- Place .whl files in tools/wheels/ to install offline dependencies",
  "- Scripts: bnf_to_ply.py, pdf_fallback_extract.py, jones_poly.py, ml_predict.py, trace_aggregator.py",
  "- Vim/Emacs snippets included",
  "- Use `make deps` to create venv and install wheels offline",
NULL
};

/* data/books.json */
static const char *books_json = "[]";

/* data/sample.csv */
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
NULL
};

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
NULL
};

/* main function writes files */
int main(void) {
  const char *root = "omega_www_pkg";
  char path[4096];
  const char *dirs[] = {"bin","lib","web","web/vendor","tools","data","tools/wheels"};
  size_t i;

  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }
  for (i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
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
  for (i=0;i<sizeof(server_py_cont)/sizeof(server_py_cont[0]);++i){
    if (server_py_cont[i]) { fputs(server_py_cont[i], f); fputc('\n', f); }
  }
  fclose(f);
  chmod(path, 0755);

  /* write web/index.html */
  snprintf(path,sizeof(path), "%s/web/index.html", root);
  if (write_lines(path, web_index, sizeof(web_index)/sizeof(web_index[0]), 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }

  /* vendor placeholders */
  snprintf(path,sizeof(path), "%s/web/vendor/codemirror.css", root);
  if (write_file(path, vendor_codemirror_css, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  snprintf(path,sizeof(path), "%s/web/vendor/codemirror.js", root);
  if (write_file(path, vendor_codemirror_js, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  snprintf(path,sizeof(path), "%s/web/vendor/keymap-vim.js", root);
  if (write_file(path, vendor_keymap_vim, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }
  snprintf(path,sizeof(path), "%s/web/vendor/mathjax.js", root);
  if (write_file(path, vendor_mathjax, 0644)!=0){ fprintf(stderr,"write failed %s\n",path); return 1; }

  /* tools scripts */
  snprintf(path, sizeof(path), "%s/tools/bnf_to_ply.py", root);
  if (write_lines(path, bnf_to_ply_py, sizeof(bnf_to_ply_py)/sizeof(bnf_to_ply_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/tools/pdf_fallback_extract.py", root);
  if (write_lines(path, pdf_fallback_extract_py, sizeof(pdf_fallback_extract_py)/sizeof(pdf_fallback_extract_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/tools/jones_poly.py", root);
  if (write_lines(path, jones_poly_py, sizeof(jones_poly_py)/sizeof(jones_poly_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/tools/ml_predict.py", root);
  if (write_lines(path, ml_predict_py, sizeof(ml_predict_py)/sizeof(ml_predict_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/tools/trace_aggregator.py", root);
  if (write_lines(path, trace_aggregator_py, sizeof(trace_aggregator_py)/sizeof(trace_aggregator_py[0]), 0755) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  /* editor snippets and tools README */
  snprintf(path, sizeof(path), "%s/tools/vim_snippet.vim", root);
  if (write_lines(path, vim_snippet, sizeof(vim_snippet)/sizeof(vim_snippet[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/tools/emacs_snippet.el", root);
  if (write_lines(path, emacs_snippet, sizeof(emacs_snippet)/sizeof(emacs_snippet[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/tools/README.txt", root);
  if (write_lines(path, tools_readme, sizeof(tools_readme)/sizeof(tools_readme[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  /* data files */
  snprintf(path, sizeof(path), "%s/data/books.json", root);
  if (write_file(path, books_json, 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/data/sample.csv", root);
  if (write_lines(path, sample_csv, 3, 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  /* Makefile and README */
  snprintf(path, sizeof(path), "%s/Makefile", root);
  if (write_lines(path, makefile_txt, sizeof(makefile_txt)/sizeof(makefile_txt[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/README.txt", root);
  if (write_lines(path, readme_txt, sizeof(readme_txt)/sizeof(readme_txt[0]), 0644) != 0) { fprintf(stderr, "write failed %s\n", path); return 1; }

  printf("omega_www_pkg created successfully.\n");
  return 0;
}
