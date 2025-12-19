#!/usr/bin/env python3
"""
file_search_server_with_pdf.py

使い方:
    python file_search_server_with_pdf.py /path/to/search_root [port]

ブラウザ: http://localhost:8000/
"""
import http.server
import socketserver
import sys
import html
import os
import urllib.parse
import pathlib
import threading

# Try import PyPDF2 for PDF text extraction
try:
    import PyPDF2
    HAVE_PYPDF2 = True
except Exception:
    HAVE_PYPDF2 = False

PORT = 8000
# 許可するテキスト拡張子の基本リスト（必要なら拡張）
TEXT_EXTS = {
    '.txt', '.py', '.md', '.csv', '.log', '.json', '.xml', '.html', '.htm',
    '.yaml', '.yml', '.ini', '.conf', '.cfg', '.tex', '.java', '.c', '.cpp', '.h', '.sh', '.bat'
}
# PDF を特別扱い
PDF_EXT = '.pdf'

ROOT_DIR = None

def extract_text_from_pdf(path: pathlib.Path) -> str:
    if not HAVE_PYPDF2:
        return ""
    try:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            texts = []
            for page in reader.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:
                    texts.append("")
            return "\n".join(texts)
    except Exception:
        return ""

def is_text_file(path: pathlib.Path):
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return True
    if ext == PDF_EXT and HAVE_PYPDF2:
        return True
    # 拡張子なしの判断: バイナリ判定
    try:
        with open(path, 'rb') as f:
            sample = f.read(4096)
            if b'\0' in sample:
                return False
            return True
    except Exception:
        return False

def safe_join(root: pathlib.Path, target: str) -> pathlib.Path:
    unquoted = urllib.parse.unquote(target)
    candidate = (root / unquoted.lstrip('/')).resolve()
    if root.resolve() in candidate.parents or root.resolve() == candidate:
        return candidate
    raise ValueError("Forbidden path")

class SearchHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        try:
            if path == '/' or path == '/index.html':
                self._handle_index()
            elif path == '/search':
                self._handle_search(qs)
            elif path == '/view':
                self._handle_view(qs)
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            self.send_error(500, "Server error: {}".format(html.escape(str(e))))

    def _send_html(self, html_text, status=200):
        data = html_text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_index(self):
        root_disp = html.escape(str(ROOT_DIR))
        pdf_note = "" if HAVE_PYPDF2 else "<p><strong>注意:</strong> PyPDF2 が見つからないため PDF は検索されません。`pip install PyPDF2` を実行してください。</p>"
        page = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>File Search</title></head>
<body>
<h2>File Search Server</h2>
<p>Root: {root_disp}</p>
{pdf_note}
<form action="/search" method="get">
  検索語: <input type="text" name="q" size="40" />
  <input type="submit" value="検索" />
</form>
<p>注: 指定したルート配下のテキストファイルとPDF（PyPDF2がある場合）を検索します。</p>
</body>
</html>
"""
        self._send_html(page)

    def _handle_search(self, qs):
        if 'q' not in qs or not qs['q'][0].strip():
            self._send_html("<html><body><p>検索語を入力してください。<a href='/'>戻る</a></p></body></html>")
            return
        query = qs['q'][0]
        matches = []
        for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
            for fn in filenames:
                full = pathlib.Path(dirpath) / fn
                try:
                    if not is_text_file(full):
                        continue
                    ext = full.suffix.lower()
                    txt = ""
                    if ext == PDF_EXT:
                        txt = extract_text_from_pdf(full)
            else:
                 try:
                     raw = full.read_bytes()
                 try:
                     txt = raw.decode('utf-8')
              except Exception:
                     txt = raw.decode(sys.getdefaultencoding(), errors='replace')
              except Exception:
                        continue
              if not txt:
                        continue
              if query in txt:
                      rel = os.path.relpath(str(full), start=str(ROOT_DIR))
                      matches.append((rel, txt.count(query)))
              except Exception:
           continue

        matches.sort(key=lambda x: (-x[1], x[0]))
        list_items = []
        for rel, count in matches:
            url = '/view?file=' + urllib.parse.quote(rel)
            list_items.append(f"<li><a href=\"{url}\">{html.escape(rel)}</a> — マッチ数: {count}</li>")
        body = "<ul>" + ("\n".join(list_items) if list_items else "<li>ヒットなし</li>") + "</ul>"
        page = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Search results for {html.escape(query)}</title></head>
<body>
<h2>検索結果: {html.escape(query)}</h2>
{body}
<p><a href="/">戻る</a></p>
</body>
</html>
"""
        self._send_html(page)

    def _handle_view(self, qs):
        if 'file' not in qs or not qs['file'][0].strip():
            self.send_error(400, "file parameter required")
            return
        rel = qs['file'][0]
        try:
            target = safe_join(pathlib.Path(ROOT_DIR), rel)
        except ValueError:
            self.send_error(403, "Forbidden")
            return
        if not target.exists() or not target.is_file():
            self.send_error(404, "File not found")
            return
        if not is_text_file(target):
            self.send_error(415, "Not a text file")
            return
        ext = target.suffix.lower()
        try:
            if ext == PDF_EXT:
                if not HAVE_PYPDF2:
                    self.send_error(415, "PDF support not available (PyPDF2 missing)")
                    return
                txt = extract_text_from_pdf(target)
            else:
                raw = target.read_bytes()
                try:
                    txt = raw.decode('utf-8')
                except Exception:
                    txt = raw.decode(sys.getdefaultencoding(), errors='replace')

            safe_txt = html.escape(txt).replace('\n', '<br />').replace('  ', '&nbsp;&nbsp;')
            page = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>{html.escape(str(rel))}</title></head>
<body>
<h2>{html.escape(str(rel))}</h2>
<pre style="white-space:pre-wrap; word-wrap:break-word;">{safe_txt}</pre>
<p><a href="/search?q=">検索に戻る</a> | <a href="/">トップ</a></p>
</body>
</html>
"""
            self._send_html(page)
except Exception as e:
            self.send_error(500, "Read error: {}".format(html.escape(str(e))))

def run_server(root_dir, port=PORT):
    global ROOT_DIR
    ROOT_DIR = pathlib.Path(root_dir).resolve()
    if not ROOT_DIR.exists() or not ROOT_DIR.is_dir():
        print("指定されたルートが存在しないかディレクトリではありません:", ROOT_DIR)
        sys.exit(1)
    handler = SearchHandler
    with socketserver.ThreadingTCPServer(("", port), handler) as httpd:
        print(f"Serving HTTP on 0.0.0.0 port {port} (root: {ROOT_DIR}) ...")
        if not HAVE_PYPDF2:
            print("Warning: PyPDF2 not installed. PDF files will be skipped. Install with: pip install PyPDF2")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutdown")
            httpd.server_close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python file_search_server_with_pdf.py /path/to/root [port]")
        sys.exit(1)
    root = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            PORT = int(sys.argv[2])
        except Exception:
            pass
    run_server(root, PORT)
