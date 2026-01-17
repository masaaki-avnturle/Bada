/*以下は、指定どおりパッケージ一式（ディレクトリ構成、ファイル群、Makefile）を生成する C プログラムです。生成されるファイルはローカルでそのまま実行できる形（Python サーバ、run_server スクリプト、web/index.html、Makefile、data/books.json 等）で作成します。文字列エスケープに注意してあり、コンパイル時に "stray '\\' in program" 等のエラーが出ないようにしています。

保存ファイル名: gen_omega_www_pkg.c
ビルド:
  gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_www_pkg gen_omega_www_pkg.c
  実行:
  ./gen_omega_www_pkg
  生成先ディレクトリ: omega_www_pkg/

（実行後）
  cd omega_www_pkg
  make run
  または
  ./bin/run_server
  ブラウザで http://localhost:8000/ を開く

  ソースコード（そのまま保存してコンパイルしてください）:

```c
*/
  /*
   * gen_omega_www_pkg.c
   *
   * Generate a local package "omega_www_pkg" containing:
   * - bin/run_server (bash wrapper)
   * - lib/server.py  (python3 http server)
   * - web/index.html (simple UI)
   * - data/books.json (initial empty DB)
   * - Makefile
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_www_pkg gen_omega_www_pkg.c
   * Run:
   *   ./gen_omega_www_pkg
   *
   * Then:
   *   cd omega_www_pkg
   *   make run
   *
   * Requirements at runtime:
   * - python3 (required to run server)
   * - pdftotext (optional for PDF->text conversion)
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/types.h>
#include <fcntl.h>
#include <sys/stat.h>

  static int ensure_dir(const char *p) {
  if (!p) return -1;
  struct stat st;
  if (stat(p, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(p, 0755) == 0) return 0;
  if (errno == EEXIST) return 0;
  return -1;
}

  static int write_lines(const char *path, const char **lines, size_t nlines, int mode) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    for (size_t i = 0; i < nlines; ++i) {
      if (fputs(lines[i], f) == EOF) { fclose(f); return -1; }
      if (fputc('\n', f) == EOF) { fclose(f); return -1; }
    }
    fclose(f);
    if (mode) chmod(path, (mode_t)mode);
    return 0;
  }

/* ---------- File contents ---------- */

/* bin/run_server */
static const char *run_server_lines[] = {
  "#!/usr/bin/env bash",
  "# bin/run_server - start the local python server",
  "set -euo pipefail",
  "ROOT_DIR=\"$(cd \"$(dirname \"$0\")/..\"; pwd)\"",
  "PYTHON=${PYTHON:-python3}",
  "SERVER=\"$ROOT_DIR/lib/server.py\"",
  "",
  "if ! command -v \"$PYTHON\" >/dev/null 2>&1; then",
  "  echo \"Error: python3 not found. Install python3.\" >&2",
  "  exit 1",
  "fi",
  "",
  "if [ ! -f \"$SERVER\" ]; then",
  "  echo \"Error: server script not found at $SERVER\" >&2",
  "  exit 1",
  "fi",
  "",
  "cd \"$ROOT_DIR\"",
"exec \"$PYTHON\" \"$SERVER\""
};

/* lib/server.py */
static const char *py_server_lines[] = {
  "#!/usr/bin/env python3",
  "# lib/server.py - simple local HTTP server",
  "from http.server import HTTPServer, BaseHTTPRequestHandler",
  "import os, sys, json, shutil, subprocess, urllib.parse, cgi",
  "from datetime import datetime",
  "",
  "PORT = 8000",
  "BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))",
  "WEB_ROOT = os.path.join(BASE_DIR, 'web')",
  "DATA_DIR = os.path.join(BASE_DIR, 'data')",
  "BOOKS_JSON = os.path.join(DATA_DIR, 'books.json')",
  "MAX_UPLOAD_SIZE = 200 * 1024 * 1024",
  "",
  "os.makedirs(DATA_DIR, exist_ok=True)",
  "if not os.path.exists(BOOKS_JSON):",
  "    with open(BOOKS_JSON, 'w', encoding='utf-8') as f:",
  "        json.dump([], f, ensure_ascii=False, indent=2)",
  "",
  "def safe_join(base, *paths):",
  "    final = os.path.abspath(os.path.join(base, *paths))",
  "    if os.path.commonpath([base]) != os.path.commonpath([base, final]):",
  "        raise ValueError('unsafe path')",
  "    return final",
  "",
  "class Handler(BaseHTTPRequestHandler):",
  "    server_version = 'OmegaWWW/0.1'",
  "",
  "    def log(self, *args):",
  "        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')",
  "        print(ts, *args)",
  "",
  "    def send_json(self, obj, code=200):",
  "        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')",
  "        self.send_response(code)",
  "        self.send_header('Content-Type', 'application/json; charset=utf-8')",
  "        self.send_header('Content-Length', str(len(data)))",
  "        self.end_headers()",
  "        self.wfile.write(data)",
  "",
  "    def do_GET(self):",
  "        parsed = urllib.parse.urlparse(self.path)",
  "        path = parsed.path",
  "        try:",
  "            if path.startswith('/data/'):",
  "                name = path[len('/data/'):]", 
  "                if not name:",
  "                    self.send_response(404); self.end_headers(); return",
  "                target = safe_join(DATA_DIR, name)",
  "                if not os.path.isfile(target):",
  "                    self.send_response(404); self.end_headers(); return",
  "                self.send_response(200)",
  "                ctype = 'application/octet-stream'",
  "                if target.endswith('.txt') or target.endswith('.json'):",
  "                    ctype = 'text/plain; charset=utf-8'",
  "                elif target.endswith('.html'):",
  "                    ctype = 'text/html; charset=utf-8'",
  "                elif target.endswith('.pdf'):",
  "                    ctype = 'application/pdf'",
  "                self.send_header('Content-Type', ctype)",
  "                fs = os.stat(target)",
  "                self.send_header('Content-Length', str(fs.st_size))",
  "                self.end_headers()",
  "                with open(target, 'rb') as f:",
  "                    shutil.copyfileobj(f, self.wfile)",
  "                return",
  "            rel = path.lstrip('/')",
  "            if rel == '': rel = 'index.html'",
  "            target = safe_join(WEB_ROOT, rel)",
  "            if os.path.isdir(target):",
  "                target = os.path.join(target, 'index.html')",
  "            if not os.path.exists(target):",
  "                self.send_response(404); self.end_headers(); return",
  "            ctype = 'application/octet-stream'",
  "            if target.endswith('.html'):",
  "                ctype = 'text/html; charset=utf-8'",
  "            elif target.endswith('.js'):",
  "                ctype = 'application/javascript; charset=utf-8'",
  "            elif target.endswith('.css'):",
  "                ctype = 'text/css; charset=utf-8'",
  "            elif target.endswith('.json'):",
  "                ctype = 'application/json; charset=utf-8'",
  "            elif target.endswith('.txt'):",
  "                ctype = 'text/plain; charset=utf-8'",
  "            self.send_response(200)",
  "            self.send_header('Content-Type', ctype)",
  "            fs = os.stat(target)",
  "            self.send_header('Content-Length', str(fs.st_size))",
  "            self.end_headers()",
  "            with open(target, 'rb') as f:",
  "                shutil.copyfileobj(f, self.wfile)",
  "        except ValueError:",
  "            self.send_response(400); self.end_headers()",
  "        except Exception as e:",
  "            self.log('GET error:', e)",
  "            self.send_response(500); self.end_headers()",
  "",
  "    def do_POST(self):",
  "        parsed = urllib.parse.urlparse(self.path)",
  "        path = parsed.path",
  "        try:",
  "            if path == '/api/upload':",
  "                self.handle_upload(); return",
  "            if path == '/api/addbook':",
  "                self.handle_addbook(); return",
  "            self.send_response(404); self.end_headers()",
  "        except Exception as e:",
  "            self.log('POST error:', e)",
  "            self.send_response(500); self.end_headers()",
  "",
  "    def do_PUT(self):",
  "        parsed = urllib.parse.urlparse(self.path)",
  "        path = parsed.path",
  "        if not path.startswith('/data/'):",
  "            self.send_response(403); self.end_headers(); return",
  "        name = path[len('/data/'):]", 
  "        if not name:",
  "            self.send_response(400); self.end_headers(); return",
  "        try:",
  "            target = safe_join(DATA_DIR, name)",
  "        except ValueError:",
  "            self.send_response(400); self.end_headers(); return",
  "        length = int(self.headers.get('Content-Length', 0))",
  "        if length > MAX_UPLOAD_SIZE:",
  "            self.send_response(413); self.end_headers(); return",
  "        with open(target, 'wb') as f:",
  "            remaining = length",
  "            while remaining > 0:",
  "                chunk = self.rfile.read(min(65536, remaining))",
  "                if not chunk: break",
  "                f.write(chunk)",
  "                remaining -= len(chunk)",
  "        self.send_response(200)",
  "        self.end_headers()",
  "        self.wfile.write(b'ok')",
  "",
  "    def handle_addbook(self):",
  "        length = int(self.headers.get('Content-Length', 0))",
  "        body = self.rfile.read(length).decode('utf-8')",
  "        try:",
  "            obj = json.loads(body)",
  "        except Exception:",
  "            self.send_response(400); self.end_headers(); self.wfile.write(b'invalid json'); return",
  "        try:",
  "            with open(BOOKS_JSON, 'r+', encoding='utf-8') as f:",
  "                arr = json.load(f)",
  "                arr.insert(0, obj)",
  "                f.seek(0); f.truncate(); json.dump(arr, f, ensure_ascii=False, indent=2)",
  "            self.send_json({'status': 'ok'})",
  "        except Exception as e:",
  "            self.log('addbook error:', e)",
  "            self.send_response(500); self.end_headers()",
  "",
  "    def handle_upload(self):",
  "        ctype, pdict = cgi.parse_header(self.headers.get('Content-Type', ''))",
  "        if ctype != 'multipart/form-data':",
  "            self.send_response(400); self.end_headers(); self.wfile.write(b'expected multipart/form-data'); return",
  "        length = int(self.headers.get('Content-Length', 0))",
  "        if length > MAX_UPLOAD_SIZE:",
  "            self.send_response(413); self.end_headers(); return",
  "        fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'}, keep_blank_values=True)",
  "        if 'file' not in fs:",
  "            self.send_response(400); self.end_headers(); self.wfile.write(b'no file field'); return",
  "        fileitem = fs['file']",
  "        if not fileitem.filename:",
  "            self.send_response(400); self.end_headers(); self.wfile.write(b'no filename'); return",
  "        filename = os.path.basename(fileitem.filename)",
  "        try:",
  "            safe_target = safe_join(DATA_DIR, filename)",
  "        except ValueError:",
  "            self.send_response(400); self.end_headers(); return",
  "        try:",
  "            with open(safe_target, 'wb') as out:",
  "                while True:",
  "                    chunk = fileitem.file.read(65536)",
  "                    if not chunk: break",
  "                    out.write(chunk)",
  "        except Exception as e:",
  "            self.log('write upload error:', e)",
  "            self.send_response(500); self.end_headers(); return",
  "        txtname = filename + '.txt'",
  "        txtpath = os.path.join(DATA_DIR, txtname)",
  "        pdftotext_ok = False",
  "        try:",
  "            proc = subprocess.run(['pdftotext', safe_target, txtpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)",
  "            pdftotext_ok = (proc.returncode == 0)",
  "        except FileNotFoundError:",
  "            pdftotext_ok = False",
  "        except Exception as e:",
  "            self.log('pdftotext error:', e)",
  "            pdftotext_ok = False",
  "        resp = {'pdf': filename, 'txt': txtname if pdftotext_ok else None, 'pdftotext': pdftotext_ok}",
  "        self.send_json(resp)",
  "",
  "def run():",
  "    os.chdir(BASE_DIR)",
  "    server = HTTPServer(('0.0.0.0', PORT), Handler)",
  "    print(f'Serving at http://localhost:{PORT}/ (root: {WEB_ROOT})')",
  "    try:",
  "        server.serve_forever()",
  "    except KeyboardInterrupt:",
  "        print('Shutting down')",
  "    finally:",
  "        server.server_close()",
  "",
  "if __name__ == '__main__':",
"    run()"
};

/* web/index.html */
static const char *web_index_lines[] = {
  "<!doctype html>",
  "<html>",
  "<head>",
  "  <meta charset=\"utf-8\">",
  "  <title>蔵書データベース - Omega WWW</title>",
  "  <style>",
  "    body { font-family: Arial, sans-serif; margin: 16px; }",
  "    #left { float:left; width:35%; }",
  "    #right { margin-left:37%; }",
  "    .book { border-bottom: 1px solid #ddd; padding:8px 0; }",
  "    #editor { height:400px; border:1px solid #ccc; }",
  "  </style>",
  "</head>",
  "<body>",
  "  <h1>蔵書データベース (Omega WWW)</h1>",
  "  <div id=\"left\">",
  "    <h3>Upload PDF</h3>",
  "    <input type=\"file\" id=\"fileinput\"> <button id=\"upload\">Upload</button>",
  "    <div id=\"uploadres\"></div>",
  "    <h3>Add Book Metadata</h3>",
  "    <input id=\"title\" placeholder=\"Title\"><br>",
  "    <input id=\"author\" placeholder=\"Author\"><br>",
  "    <input id=\"tags\" placeholder=\"tags (comma)\"><br>",
  "    <button id=\"addbook\">Add Book</button>",
  "    <h3>Search</h3>",
  "    <input id=\"q\" placeholder=\"search query\"><button id=\"searchbtn\">Search</button>",
  "    <div id=\"list\"></div>",
  "  </div>",
  "  <div id=\"right\">",
  "    <h3>Viewer / Editor</h3>",
  "    <div id=\"viewer\" style=\"white-space:pre-wrap; border:1px solid #ddd; padding:8px; height:200px; overflow:auto;\"></div>",
  "    <h4>Editor</h4>",
  "    <textarea id=\"editorarea\" style=\"width:100%; height:250px;\"></textarea>",
  "    <button id=\"saveeditor\">Save Text to file</button>",
  "  </div>",
  "  <script>",
  "  async function loadList(){",
  "    try{",
  "      let resp = await fetch('/data/books.json');",
  "      let arr = await resp.json();",
  "      renderList(arr);",
    "    }catch(e){ console.error(e); }",
    "  }",
    "  function renderList(arr){",
    "    const div = document.getElementById('list'); div.innerHTML='';",
    "    arr.forEach((b,idx)=>{",
    "      const el = document.createElement('div'); el.className='book';",
    "      el.innerHTML = `<strong>${escapeHtml(b.title||'')}</strong><br>by ${escapeHtml(b.author||'')}<br>tags: ${escapeHtml((b.tags||[]).join(','))}<br>`;",
    "      const viewBtn = document.createElement('button'); viewBtn.textContent='View txt';",
    "      viewBtn.onclick = ()=>{ if(b.txt) viewTxt(b.txt); else alert('No text available for this book'); };",
    "      el.appendChild(viewBtn);",
    "      div.appendChild(el);",
    "    });",
    "  }",
    "  function escapeHtml(s){ return (s||'').replace(/[&<>\"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;','\\'' :'&#39;'}[c]; }); }",
    "  async function viewTxt(name){",
    "    let resp = await fetch('/data/'+encodeURIComponent(name));",
    "    if(!resp.ok){ alert('failed to fetch txt'); return; }",
    "    let txt = await resp.text();",
    "    document.getElementById('viewer').textContent = txt;",
    "    document.getElementById('editorarea').value = txt;",
    "  }",
    "  document.getElementById('upload').onclick = async ()=>{",
    "    const f = document.getElementById('fileinput').files[0]; if(!f){ alert('select file'); return; }",
    "    const fd = new FormData(); fd.append('file', f);",
    "    const res = await fetch('/api/upload', { method:'POST', body: fd });",
    "    const j = await res.json(); document.getElementById('uploadres').textContent = JSON.stringify(j);",
    "    loadList();",
    "  };",
    "  document.getElementById('addbook').onclick = async ()=>{",
    "    const title = document.getElementById('title').value;",
    "    const author = document.getElementById('author').value;",
    "    const tags = document.getElementById('tags').value.split(',').map(s=>s.trim()).filter(Boolean);",
    "    const payload = { title, author, tags };",
    "    await fetch('/api/addbook', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });",
    "    loadList();",
    "  };",
    "  document.getElementById('searchbtn').onclick = ()=>{",
    "    const q = document.getElementById('q').value.toLowerCase();",
    "    fetch('/data/books.json').then(r=>r.json()).then(arr=>{",
    "      const f = arr.filter(b => ((b.title||'')+ ' ' + (b.author||'') + ' ' + (b.tags||[]).join(' ')).toLowerCase().includes(q));",
    "      renderList(f);",
    "    });",
    "  };",
    "  document.getElementById('saveeditor').onclick = async ()=>{",
    "    const text = document.getElementById('editorarea').value;",
    "    const name = prompt('Save as filename under data/ (e.g. myfile.txt):'); if(!name) return;",
    "    await fetch('/data/'+name, { method:'PUT', body: text });",
    "    alert('saved'); loadList();",
    "  };",
    "  loadList();",
    "  </script>",
    "</body>",
"</html>"
};

/* data/books.json */
static const char *books_json_lines[] = {
"[]"
};

/* Makefile */
static const char *makefile_lines[] = {
  "PY = python3",
  "BIN = bin/run_server",
  "LIB = lib/server.py",
  "DATA_DIR = data",
  "",
  ".PHONY: all run prepare clean",
  "",
  "all: prepare",
  "",
  "prepare: $(DATA_DIR) $(BIN)",
  "@echo \"Package prepared. Use 'make run' to start server.\"",
  "",
  "$(DATA_DIR):",
  "mkdir -p $(DATA_DIR)",
  "",
  "$(BIN):",
  "chmod +x $(BIN) || true",
  "chmod +x $(LIB) || true",
  "",
  "run: $(BIN)",
  "@echo \"Starting local server...\"",
  "$(PY) $(LIB)",
  "",
  "install: $(BIN)",
  "@echo \"No global install step defined.\"",
  "",
  "clean:",
  "@echo \"Cleaning generated runtime files...\"",
  "-find $(DATA_DIR) -name '*.tmp' -type f -delete || true",
  "",
  "help:",
  "@echo \"make        - prepare\"",
  "@echo \"make run    - start local server (requires python3)\"",
  "@echo \"make clean  - remove temporary artifacts\""
};

/* README */
static const char *readme_lines[] = {
  "Omega WWW Package",
  "",
  "Usage:",
  "  cd omega_www_pkg",
  "  ./bin/run_server",
  "  or",
  "  make run",
  "",
  "Open http://localhost:8000/ in your browser.",
"Requirements: python3 (for server) and pdftotext (optional)"
};

/* ---------- end file contents ---------- */

int main(void) {
  const char *root = "omega_www_pkg";
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  const char *dirs[] = { "bin", "lib", "web", "data", "include", "etc", "usr" };
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
    snprintf(path, sizeof(path), "%s/%s", root, dirs[i]);
    if (ensure_dir(path) != 0) { fprintf(stderr, "cannot create %s\n", path); return 1; }
  }

  /* write bin/run_server */
  snprintf(path, sizeof(path), "%s/bin/run_server", root);
  if (write_lines(path, run_server_lines, sizeof(run_server_lines)/sizeof(run_server_lines[0]), 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* write lib/server.py */
  snprintf(path, sizeof(path), "%s/lib/server.py", root);
  if (write_lines(path, py_server_lines, sizeof(py_server_lines)/sizeof(py_server_lines[0]), 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* write web/index.html */
  snprintf(path, sizeof(path), "%s/web/index.html", root);
  if (write_lines(path, web_index_lines, sizeof(web_index_lines)/sizeof(web_index_lines[0]), 0644) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* write data/books.json */
  snprintf(path, sizeof(path), "%s/data/books.json", root);
  if (write_lines(path, books_json_lines, sizeof(books_json_lines)/sizeof(books_json_lines[0]), 0644) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* write Makefile */
  snprintf(path, sizeof(path), "%s/Makefile", root);
  if (write_lines(path, makefile_lines, sizeof(makefile_lines)/sizeof(makefile_lines[0]), 0644) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* write README */
  snprintf(path, sizeof(path), "%s/README.txt", root);
  if (write_lines(path, readme_lines, sizeof(readme_lines)/sizeof(readme_lines[0]), 0644) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  printf("Generated package '%s'\n", root);
  printf("To run:\n  cd %s\n  ./bin/run_server\n", root);
  printf("or\n  make -C %s run\n", root);
  return 0;
}
/*
必要なら：
- web/index.html を CodeMirror（Vim キーマップ）などの外部ライブラリ同梱版に差し替えるパッケージ化。
- server.py に認証や詳しいログ出力、より堅牢な multipart パースを追加。
- pdftotext の有無チェックを起動時に行い、代替処理を追加。

問題があれば、コンパイル／実行時のエラーメッセージを貼ってください。修正します。
*/
