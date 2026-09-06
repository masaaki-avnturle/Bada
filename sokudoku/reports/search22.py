以下は、Windows 11 / Ubuntu 両環境で動作する、ローカルディスク上のディレクトリを指定してテキストファイルを検索し、結果をブラウザで表示・ファイル内容を閲覧できるシンプルな Python HTTP サーバーのワンファイル実装です（外部ライブラリ不要、Python 3.7+ 推奨）。

使い方要点
- ファイルを公開するルートディレクトリをコマンド引数で指定します（例: `C:\` や `/home/username`）。
- ブラウザで http://localhost:8000/ にアクセスして検索します。
- 検索語を含むファイル一覧が表示され、クリックで内容を表示します。

保存ファイル名例: `file_search_server.py`

```python
#!/usr/bin/env python3
"""
file_search_server.py

使い方:
    python file_search_server.py /path/to/search_root

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

PORT = 8000
# 許可するテキスト拡張子の基本リスト（必要なら拡張）
TEXT_EXTS = {
    '.txt', '.py', '.md', '.csv', '.log', '.json', '.xml', '.html', '.htm',
    '.yaml', '.yml', '.ini', '.conf', '.cfg', '.tex', '.java', '.c', '.cpp', '.h', '.sh', '.bat'
}

# root will be set from argv
ROOT_DIR = None

def is_text_file(path: pathlib.Path):
    # 判断は拡張子優先、拡張子なければ小さく読み取りて試す
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return True
    try:
        # 小さく読み取ってバイナリかをチェック
        with open(path, 'rb') as f:
            sample = f.read(4096)
            if b'\0' in sample:
                return False
            # 非テキストっぽいバイトが多ければ False（簡易）
            # ここでは最低限の判定のみ
            return True
    except Exception:
        return False

def safe_join(root: pathlib.Path, target: str) -> pathlib.Path:
    # URLエンコードされたパスを解釈してroot以下に限定
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
        page = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>File Search</title></head>
<body>
<h2>File Search Server</h2>
<p>Root: {root_disp}</p>
<form action="/search" method="get">
  検索語: <input type="text" name="q" size="40" />
  <input type="submit" value="検索" />
</form>
<p>注: 指定したルート配下のテキストファイルを検索します。</p>
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
        # 再帰検索（大きいディレクトリでは時間がかかる）
        for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
            for fn in filenames:
                full = pathlib.Path(dirpath) / fn
                try:
                    if not is_text_file(full):
                        continue
                    # テキストとして読み、検索語が含まれるか
                    found = False
                    with open(full, 'rb') as f:
                        raw = f.read()
                    # try decode with utf-8, fallback to latin-1
                    try:
                        txt = raw.decode('utf-8')
                    except Exception:
                        try:
                            txt = raw.decode(sys.getdefaultencoding(), errors='replace')
                        except Exception:
                            txt = raw.decode('latin-1', errors='replace')
                    if query in txt:
                        rel = os.path.relpath(str(full), start=str(ROOT_DIR))
                        matches.append((rel, txt.count(query)))
                except Exception:
                    # 読み取りエラー等は無視して続行
                    continue

        # 結果表示
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
        try:
            with open(target, 'rb') as f:
                raw = f.read()
            try:
                txt = raw.decode('utf-8')
            except Exception:
                try:
                    txt = raw.decode(sys.getdefaultencoding(), errors='replace')
                except Exception:
                    txt = raw.decode('latin-1', errors='replace')
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
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutdown")
            httpd.server_close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python file_search_server.py /path/to/root [port]")
        sys.exit(1)
    root = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            PORT = int(sys.argv[2])
        except Exception:
            pass
    run_server(root, PORT)
```

注意と改善案（簡潔に）
- 大きなディレクトリを再帰検索すると時間がかかります。必要ならスキャンをバックグラウンドで一度行いインデックス化する等を検討してください。
- 文字コード判定は簡易です。必要なら `chardet` 等を使って精度を上げてください。
- セキュリティ: このスクリプトはあくまでローカル利用向けです。公開サーバー用途では適切な認証・アクセス制御が必要です。

必要なら検索の正規表現対応、部分一致ハイライト、非同期インデックス化、改良版（Flask 使用や静的ファイル配信追加）などの拡張を実装して差し上げます。どれを追加しますか？
