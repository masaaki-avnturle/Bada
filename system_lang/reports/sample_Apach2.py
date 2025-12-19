以下は、外部クライアント接続の「IPプロトコル（IPv4 / IPv6）」を検出してログ出力し、かつ CGI をサポートする簡易な Apache 風 Web サーバを Python で実装したサンプルです。サーバは IPv4 と IPv6 の両方で待ち受けられるようにそれぞれソケットを作り、`/cgi-bin/` に置かれたスクリプトを CGI として実行します。

使い方（簡単）:
- ファイルを `simple_apache.py` として保存
- `cgi-bin` ディレクトリを作り、実行可能なスクリプト（例: `hello.py`）を置く
- `python simple_apache.py` で起動
- IPv4: `http://localhost:8080/cgi-bin/hello.py`、IPv6: `http://[::1]:8080/cgi-bin/hello.py`

コード:

```python
#!/usr/bin/env python3
"""
簡易 Apache 風サーバ（CGI サポート + クライアントの IP プロトコル判定）
"""

import os
import sys
import socket
import threading
from http.server import CGIHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn

HOST = ''          # 空 = all interfaces
PORT = 8080
CGI_DIR = "cgi-bin"

class ProtoCGIHandler(CGIHTTPRequestHandler):
    # CGI directory name
    cgi_directories = ['/' + CGI_DIR]

    def address_family_of_client(self):
        # self.request is the socket; determine family via getpeername() tuple length or .family
        try:
            fam = getattr(self.request, "family", None)
            if fam is not None:
                if fam == socket.AF_INET6:
                    return "IPv6"
                elif fam == socket.AF_INET:
                    return "IPv4"
            # fallback: peername tuple length (IPv4 -> 2, IPv6 -> 4)
            peer = self.request.getpeername()
            if isinstance(peer, tuple):
                if len(peer) == 4:
                    return "IPv6"
                else:
                    return "IPv4"
        except Exception:
            pass
        # as final fallback, inspect textual client addr
        ip = self.client_address[0]
        return "IPv6" if ':' in ip else "IPv4"

    def log_message(self, format, *args):
        # Override to include client's IP protocol
        proto = self.address_family_of_client()
        client_ip = self.client_address[0]
        entry = "[%s] %s - %s\n" % (proto, client_ip, format % args)
        sys.stderr.write(entry)

    # Optionally expose protocol information to CGI scripts via environment variable
    def setup_cgi_env(self):
        # Called in CGIHTTPRequestHandler.run_cgi; we override by injecting before calling parent
        # But CGIHTTPRequestHandler constructs env in run_cgi; so instead set after env creation:
        pass

    # To ensure CGI scripts can see IP protocol, override run_cgi to add HTTP_ header env
    def run_cgi(self):
        # Determine protocol once
        proto = self.address_family_of_client()
        # Temporarily set an attribute that run_cgi will put into env
        # We can't easily tap into env creation without copying run_cgi; so duplicate minimal run_cgi behavior
        # We'll call parent but set an environment variable via os.environ while parent creates it.
        # To avoid affecting server env globally, patch os.environ locally
        old_env = os.environ.copy()
        os.environ['REMOTE_IP_PROTOCOL'] = proto
        try:
            super().run_cgi()
        finally:
            os.environ.clear()
            os.environ.update(old_env)

class DualServerThread(threading.Thread):
    def __init__(self, server):
        super().__init__(daemon=True)
        self.server = server

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass

def make_server(bind_addr, port, family):
    class CustomHTTPServer(ThreadingHTTPServer):
        address_family = family
    server = CustomHTTPServer((bind_addr, port), ProtoCGIHandler)
    return server

def main(port=PORT):
    # Ensure cgi dir exists
    if not os.path.isdir(CGI_DIR):
        os.makedirs(CGI_DIR, exist_ok=True)
        print("Created directory:", CGI_DIR)

    servers = []

    # Try create IPv6 server (if system supports)
    try:
        srv6 = make_server("::", port, socket.AF_INET6)
        t6 = DualServerThread(srv6)
        t6.start()
        servers.append(srv6)
        print(f"Serving IPv6 on [::]:{port}")
    except Exception as e:
        print("IPv6 bind failed:", e)

    # Create IPv4 server
    try:
        srv4 = make_server("0.0.0.0", port, socket.AF_INET)
        t4 = DualServerThread(srv4)
        t4.start()
        servers.append(srv4)
        print(f"Serving IPv4 on 0.0.0.0:{port}")
    except Exception as e:
        print("IPv4 bind failed:", e)

    if not servers:
        print("No servers could be started. Exiting.")
        return

    try:
        print("Press Ctrl+C to stop.")
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        for s in servers:
            s.shutdown()
            s.server_close()

if __name__ == "__main__":
    # optional: allow port arg
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except:
            pass
    main(PORT)
```

CGI スクリプトからクライアントの IP プロトコルを参照したい場合、上の実装は環境変数 `REMOTE_IP_PROTOCOL` を CGI 実行時に設定しています（値は "IPv4" または "IPv6"）。CGI スクリプト内で `REMOTE_IP_PROTOCOL` を参照してください。

必要なら、
- ログをファイルに出す、
- TLS を追加する、
- 仮想ホスト機能を加える
など、さらに拡張した例を作りますか？
