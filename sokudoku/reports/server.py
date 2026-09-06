了解しました。まずは問題の原因となっているであろう Python のインデント／1行に複数文を詰めた箇所をすべて修正した、完全な `omega_www_pkg/lib/server.py` を提示します。これを既存の `omega_www_pkg/lib/server.py` に上書きしてください（実行前にバックアップを推奨します）。

ファイル全体（正しいインデント、長い1行を複数行に展開、文字列やエスケープの修正済み）：

```python
#!/usr/bin/env python3
# lib/server.py - Offline server (extended)

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys
import json
import shutil
import cgi
import urllib.parse
import subprocess
import tempfile
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB_ROOT = os.path.join(BASE_DIR, 'web')
DATA_DIR = os.path.join(BASE_DIR, 'data')
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')
BOOKS_JSON = os.path.join(DATA_DIR, 'books.json')
PORT = int(os.environ.get('OMEGA_PORT', '8000'))
MAX_UPLOAD = 1024 * 1024 * 1024

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(BOOKS_JSON):
    with open(BOOKS_JSON, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def safe_join(base, *paths):
    final = os.path.abspath(os.path.join(base, *paths))
    if os.path.commonpath([base]) != os.path.commonpath([base, final]):
        raise ValueError('unsafe path')
    return final


class Handler(BaseHTTPRequestHandler):
    server_version = 'OmegaOffline/2.1'

    def log(self, *args):
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *args)

    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            if path.startswith('/data/'):
                name = path[len('/data/'):]
                target = safe_join(DATA_DIR, name)
                if not os.path.isfile(target):
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                c = 'application/octet-stream'
                if target.endswith('.html'):
                    c = 'text/html; charset=utf-8'
                elif target.endswith('.json') or target.endswith('.txt'):
                    c = 'text/plain; charset=utf-8'
                self.send_header('Content-Type', c)
                fs = os.stat(target)
                self.send_header('Content-Length', str(fs.st_size))
                self.end_headers()
                with open(target, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)
                return

            rel = path.lstrip('/') or 'index.html'
            target = safe_join(WEB_ROOT, rel)
            if os.path.isdir(target):
                target = os.path.join(target, 'index.html')
            if not os.path.exists(target):
                self.send_response(404)
                self.end_headers()
                return
            c = 'application/octet-stream'
            if target.endswith('.html'):
                c = 'text/html; charset=utf-8'
            elif target.endswith('.js'):
                c = 'application/javascript; charset=utf-8'
            elif target.endswith('.css'):
                c = 'text/css; charset=utf-8'
            self.send_response(200)
            self.send_header('Content-Type', c)
            fs = os.stat(target)
            self.send_header('Content-Length', str(fs.st_size))
            self.end_headers()
            with open(target, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        except ValueError:
            self.send_response(400)
            self.end_headers()
        except Exception as e:
            self.log('GET error:', e)
            self.send_response(500)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            if path == '/api/upload':
                self.handle_upload()
                return
            if path == '/api/addbook':
                self.handle_addbook()
                return
            if path == '/api/export_books':
                self.handle_export_books()
                return
            if path == '/api/summary_pdf':
                self.handle_summary_pdf()
                return
            if path == '/api/bnf_generate':
                self.handle_bnf_generate()
                return
            if path == '/api/ml_predict':
                self.handle_ml_predict()
                return
            if path == '/api/jones':
                self.handle_jones()
                return
            if path == '/api/trace_aggregate':
                self.handle_trace_aggregate()
                return
            if path == '/api/pdf_question':
                self.handle_pdf_question()
                return
            self.send_response(404)
            self.end_headers()
        except Exception as e:
            self.log('POST error:', e)
            self.send_response(500)
            self.end_headers()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if not path.startswith('/data/'):
            self.send_response(403)
            self.end_headers()
            return
        name = path[len('/data/'):]
        target = safe_join(DATA_DIR, name)
        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_UPLOAD:
            self.send_response(413)
            self.end_headers()
            return
        with open(target, 'wb') as f:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def handle_addbook(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'invalid json')
            return
        try:
            with open(BOOKS_JSON, 'r+', encoding='utf-8') as f:
                arr = json.load(f)
                arr.insert(0, obj)
                f.seek(0)
                f.truncate()
                json.dump(arr, f, ensure_ascii=False, indent=2)
            self.send_json({'status': 'ok'})
        except Exception as e:
            self.log('addbook error', e)
            self.send_response(500)
            self.end_headers()

    def handle_export_books(self):
        try:
            with open(BOOKS_JSON, 'r', encoding='utf-8') as f:
                arr = json.load(f)
            self.send_json({'status': 'ok', 'books': arr})
        except Exception as e:
            self.log('export error', e)
            self.send_response(500)
            self.end_headers()

    def handle_upload(self):
        ctype, pdict = cgi.parse_header(self.headers.get('Content-Type', ''))
        if ctype != 'multipart/form-data':
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'expected multipart/form-data')
            return

        fs = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'},
            keep_blank_values=True
        )
        if 'file' not in fs:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'no file field')
            return
        fileitem = fs['file']
        if not fileitem.filename:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'no filename')
            return

        filename = os.path.basename(fileitem.filename)
        try:
            target = safe_join(DATA_DIR, filename)
        except ValueError:
            self.send_response(400)
            self.end_headers()
            return

        try:
            with open(target, 'wb') as out:
                while True:
                    chunk = fileitem.file.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
        except Exception as e:
            self.log('upload write error', e)
            self.send_response(500)
            self.end_headers()
            return

        txtname = filename + '.txt'
        txtpath = os.path.join(DATA_DIR, txtname)
        pdftok = False

        try:
            subprocess.run(
                ['pdftotext', target, txtpath],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            pdftok = True
        except Exception:
            fallback = os.path.join(TOOLS_DIR, 'pdf_fallback_extract.py')
            if os.path.exists(fallback):
                try:
                    subprocess.run([sys.executable, fallback, target, txtpath], check=True)
                except Exception:
                    pass

        self.send_json({
            'pdf': filename,
            'txt': txtname if os.path.exists(txtpath) else None,
            'pdftotext': pdftok
        })

    def handle_summary_pdf(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
            fname = obj.get('pdf')
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        try:
            txtpath = os.path.join(DATA_DIR, fname + '.txt')
            if not os.path.exists(txtpath):
                self.send_json({'status': 'no_text'})
                return
            with open(txtpath, 'r', encoding='utf-8', errors='ignore') as f:
                chunk = ''.join([f.readline() for _ in range(200)])
            words = [w.lower().strip('.,()[]\"\\\'') for w in chunk.split()]
            freq = {}
            for w in words:
                freq[w] = freq.get(w, 0) + 1
            top = sorted(freq.items(), key=lambda x: -x[1])[:15]
            self.send_json({
                'status': 'ok',
                'summary': chunk[:5000],
                'keywords': [k for k, _ in top]
            })
        except Exception as e:
            self.log('summary error', e)
            self.send_response(500)
            self.end_headers()

    def handle_bnf_generate(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
            bnf = obj.get('bnf', '')
            name = obj.get('name', 'netlang')
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        try:
            os.makedirs(TOOLS_DIR, exist_ok=True)
            out = os.path.join(TOOLS_DIR, name + '_parser.py')
            script = os.path.join(TOOLS_DIR, 'bnf_to_ply.py')
            if os.path.exists(script):
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.bnf', encoding='utf-8') as tf:
                    tf.write(bnf)
                    tmpname = tf.name
                proc = subprocess.run(
                    [sys.executable, script, tmpname, out],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                try:
                    os.unlink(tmpname)
                except Exception:
                    pass
                if proc.returncode == 0 and os.path.exists(out):
                    self.send_json({'status': 'ok', 'out': 'tools/' + os.path.basename(out)})
                    return

            with open(out, 'w', encoding='utf-8') as f:
                f.write('# Auto-generated parser skeleton for %s\n' % name)
                f.write('from ply import lex, yacc\n\n')
                f.write('tokens = []\n\n')
                f.write('def p_error(p):\n    pass\n')
            self.send_json({'status': 'ok', 'out': 'tools/' + os.path.basename(out)})
        except Exception as e:
            self.log('bnf gen error', e)
            self.send_response(500)
            self.end_headers()

    def handle_ml_predict(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
            csvpath = obj.get('csv')
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        try:
            target = safe_join(DATA_DIR, csvpath)
            if not os.path.exists(target):
                self.send_json({'status': 'no_csv'})
                return
            script = os.path.join(TOOLS_DIR, 'ml_predict.py')
            if not os.path.exists(script):
                self.send_json({'status': 'no_script'})
                return
            proc = subprocess.run(
                [sys.executable, script, target],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180
            )
            out = proc.stdout.decode('utf-8', errors='ignore')
            self.send_json({'status': 'ok', 'output': out})
        except Exception as e:
            self.log('ml predict error', e)
            self.send_response(500)
            self.end_headers()

    def handle_jones(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
            knot = obj.get('knot', 'unknot')
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        try:
            script = os.path.join(TOOLS_DIR, 'jones_poly.py')
            if not os.path.exists(script):
                self.send_json({'status': 'no_script'})
                return
            proc = subprocess.run(
                [sys.executable, script, knot],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            out = proc.stdout.decode('utf-8', errors='ignore')
            self.send_json({'status': 'ok', 'result': out})
        except Exception as e:
            self.log('jones error', e)
            self.send_response(500)
            self.end_headers()

    def handle_trace_aggregate(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
            csvs = obj.get('files', [])
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        try:
            script = os.path.join(TOOLS_DIR, 'trace_aggregator.py')
            if not os.path.exists(script):
                self.send_json({'status': 'no_script'})
                return
            cmd = [sys.executable, script] + csvs
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180
            )
            out = proc.stdout.decode('utf-8', errors='ignore')
            self.send_json({'status': 'ok', 'output': out})
        except Exception as e:
            self.log('trace agg error', e)
            self.send_response(500)
            self.end_headers()

    def handle_pdf_question(self):
        l = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(l).decode('utf-8')
        try:
            obj = json.loads(body)
            pdf = obj.get('pdf')
            question = obj.get('q', '')
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        try:
            txtpath = os.path.join(DATA_DIR, pdf + '.txt')
            if not os.path.exists(txtpath):
                self.send_json({'status': 'no_text'})
                return
            with open(txtpath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            excerpt = text[:4000]
            import re
            formulas = re.findall(r'\$[^\$]{5,500}\$', text)[:10]
            ans = 'Excerpt provided. Found %d inline formulas.' % len(formulas)
            self.send_json({'status': 'ok', 'answer': ans, 'excerpt': excerpt, 'formulas': formulas})
        except Exception as e:
            self.log('pdf q error', e)
            self.send_response(500)
            self.end_headers()


def run():
    os.chdir(BASE_DIR)
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print('Serving at http://localhost:%d/ (root: %s)' % (PORT, WEB_ROOT))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
    finally:
        server.server_close()


if __name__ == '__main__':
    run()
```

使い方（簡潔）
- 上書き後、構文チェック：
  python3 -m py_compile omega_www_pkg/lib/server.py
- サーバ起動：
  cd omega_www_pkg
  ./bin/run_server

もし上書きしても同じエラーが出る場合：
- エラーメッセージの該当行番号とその前後 10 行を貼ってください。即座に確認して修正案を出します。
