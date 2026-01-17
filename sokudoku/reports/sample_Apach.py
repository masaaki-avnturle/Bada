以下に「完全な」実装例を示します。2つのファイルを作成してください。

1) `simple_apache.py` — IPv4/IPv6 両対応のスレッド化簡易サーバ、CGI サポート、接続元の IP プロトコル（IPv4/IPv6）をログ出力し、CGI 実行時に環境変数 `REMOTE_IP_PROTOCOL` を設定します。  
2) `cgi-bin/hello.py` — 動作確認用の CGI スクリプト（実行可能にすること）。

simple_apache.py
```python
#!/usr/bin/env python3
"""
simple_apache.py
簡易 Apache 風サーバ（CGI サポート + クライアントの IP プロトコル判定）
起動: python3 simple_apache.py [port]
デフォルトポート: 8080
"""

import os
import sys
import socket
import threading
from http.server import CGIHTTPRequestHandler, ThreadingHTTPServer

CGI_DIR = "cgi-bin"
DEFAULT_PORT = 8080

class ProtoCGIHandler(CGIHTTPRequestHandler):
    cgi_directories = ['/' + CGI_DIR]

    def address_family_of_client(self):
        # Try to use the underlying socket family if available
        try:
            fam = getattr(self.request, "family", None)
            if fam is not None:
                if fam == socket.AF_INET6:
                    return "IPv6"
                elif fam == socket.AF_INET:
                    return "IPv4"
            # Fallback: peername tuple length (IPv4 -> 2, IPv6 -> 4)
            peer = self.request.getpeername()
            if isinstance(peer, tuple):
                if len(peer) == 4:
                    return "IPv6"
                else:
                    return "IPv4"
        except Exception:
            pass
        # Final fallback: inspect textual IP
        ip = self.client_address[0]
        return "IPv6" if ':' in ip else "IPv4"

    def log_message(self, format, *args):
        proto = self.address_family_of_client()
        client_ip = self.client_address[0]
        entry = "[%s] %s - %s\n" % (proto, client_ip, format % args)
        sys.stderr.write(entry)

    def run_cgi(self):
        # Inject REMOTE_IP_PROTOCOL into environment for the CGI process
        proto = self.address_family_of_client()
        # Preserve os.environ and restore later to avoid polluting global env
        old_env = os.environ.copy()
        os.environ['REMOTE_IP_PROTOCOL'] = proto
        try:
            super().run_cgi()
        finally:
            os.environ.clear()
            os.environ.update(old_env)

class DualThreadingHTTPServer(ThreadingHTTPServer):
    # address_family will be set per-instance if needed
    pass

def make_server(bind_addr, port, family):
    class CustomHTTPServer(DualThreadingHTTPServer):
        pass
    CustomHTTPServer.address_family = family
    server = CustomHTTPServer((bind_addr, port), ProtoCGIHandler)
    return server

def ensure_cgi_dir():
    if not os.path.isdir(CGI_DIR):
        os.makedirs(CGI_DIR, exist_ok=True)
        print("Created directory:", CGI_DIR)

def start_server_if_possible(bind_addr, port, family, servers):
    try:
        srv = make_server(bind_addr, port, family)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        servers.append((srv, th))
        print(f"Serving on {bind_addr}:{port} (family={family})")
    except Exception as e:
        print(f"Failed to bind {bind_addr}:{port} (family={family}): {e}")

def main(port=DEFAULT_PORT):
    ensure_cgi_dir()
    servers = []

    # Try IPv6 wildcard
    try:
        start_server_if_possible("::", port, socket.AF_INET6, servers)
    except Exception:
        pass

    # IPv4 wildcard
    start_server_if_possible("0.0.0.0", port, socket.AF_INET, servers)

    if not servers:
        print("No servers started. Exiting.")
        return

    print("Press Ctrl+C to stop.")
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        for srv, _ in servers:
            try:
                srv.shutdown()
                srv.server_close()
            except Exception:
                pass
        print("Stopped.")

if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass
    main(port)
```

cgi-bin/hello.py
```python
#!/usr/bin/env python3
# Example CGI script. Put this file in the "cgi-bin" directory and make it executable.
import os
import sys

def main():
    proto = os.environ.get('REMOTE_IP_PROTOCOL', 'unknown')
    remote_addr = os.environ.get('REMOTE_ADDR', 'unknown')
    print("Content-Type: text/plain")
    print()
    print("Hello from CGI!")
    print("REMOTE_ADDR =", remote_addr)
    print("REMOTE_IP_PROTOCOL =", proto)

if __name__ == '__main__':
    main()
```

使い方（簡単）:
- 保存:
  - `simple_apache.py` を任意の場所に置く。
  - 同じディレクトリに `cgi-bin` フォルダを作るか、サーバ起動時に自動作成されます。
  - `cgi-bin/hello.py` を `cgi-bin` に置き、実行権を付与: `chmod +x cgi-bin/hello.py`
- 起動: `python3 simple_apache.py 8080`
- アクセス:
  - IPv4: http://127.0.0.1:8080/cgi-bin/hello.py
  - IPv6 (環境が対応していれば): http://[::1]:8080/cgi-bin/hello.py

ログは標準エラーに出力され、各リクエストでクライアント IP とプロトコル（IPv4/IPv6）が表示されます。
