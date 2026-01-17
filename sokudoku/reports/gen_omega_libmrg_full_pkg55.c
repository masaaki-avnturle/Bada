わかりました。vim.wasm を組み込むための変更を行った新しい生成器 `gen_omega_libmrg_full_pkg.c` を提示します。

ポイント
- 実際の `vim.wasm` バイナリは大きく・配布先が変わり得るため、生成器はバイナリを同梱しません。代わりに `web/wasm/download_vim_wasm.sh` スクリプト（ユーザーが公式ビルドの URL を指定してダウンロードする）を生成します。
- Web UI に `web/vim.html` を追加し、`web/wasm/vim.wasm` が存在すれば読み込みを試み、なければダウンロード手順を表示します。実際にブラウザ内で完全な Vim を動かすには通常「vim.wasm とそれを起動する JS ランチャー（vim.js など）」「ターミナルライブラリ（xterm.js 等）」が必要です。本生成器は最小限の起点（ファイル配置 + ダウンロードスクリプト +読み込みの枠組み）を用意します。
- 生成後にユーザーはダウンロードスクリプトで `vim.wasm` を取得するか、手動で `omega_libmrg_web_pkg/web/wasm/vim.wasm` に置いてください。その後 `./bin/server` を起動し、ブラウザで `/vim.html` にアクセスすると読み込みを試みます。

使い方（要約）
1. 保存・コンパイル:
   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_libmrg_full_pkg gen_omega_libmrg_full_pkg.c
     2. 実行（生成）:
   ./gen_omega_libmrg_full_pkg
     3. 生成ディレクトリに移動、必要なら vim.wasm をダウンロード:
   cd omega_libmrg_web_pkg
   ./web/wasm/download_vim_wasm.sh <VIM_WASM_URL>
   （または手動で web/wasm/vim.wasm を置く）
  4. ビルド・起動:
   make
   ./bin/server
  5. ブラウザで http://localhost:8080/vim.html を開く

  以下が生成器のソースコードです（そのまま保存してコンパイルしてください）:

```c
  /*
   * gen_omega_libmrg_full_pkg.c
   *
   * Generate package "omega_libmrg_web_pkg" extended with vim.wasm support.
   *
   * Build generator:
   *   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_libmrg_full_pkg gen_omega_libmrg_full_pkg.c
   * Run:
   *   ./gen_omega_libmrg_full_pkg
   *
   * Then follow instructions in the directory.
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

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
    size_t L = strlen(data);
    if (L && fwrite(data, 1, L, f) != L) { fclose(f); return -1; }
    fclose(f);
    if (mode) chmod(path, (mode_t)mode);
    return 0;
  }

/* Minimal Makefile (build server) */
static const char *makefile =
"CC = gcc\n"
"CFLAGS = -O2 -std=c11 -Wall -Wextra -Iinclude\n"
"BIN = bin/server\n"
"SRC = bin/server.c lib/db.c\n"
"\n"
"all: $(BIN)\n"
"\n"
"$(BIN): $(SRC)\n"
"\t$(CC) $(CFLAGS) -o $@ $(SRC)\n"
"\n"
"clean:\n"
"\trm -f $(BIN)\n"
"\n"
    ".PHONY: all clean\n";

/* README */
static const char *readme =
"# omega_libmrg_web_pkg (with vim.wasm support)\n\n"
  "Run generator, then optionally download vim.wasm into web/wasm/, then build and run server.\n\n";

/* web/vim.html - attempts to load vim.wasm if present, otherwise shows instructions */
static const char *web_vim_html =
"<!doctype html>\n"
"<html><head><meta charset=\"utf-8\"><title>Vim (wasm) - Embedded</title>\n"
"<style>body{font-family:Arial;margin:12px} #term{width:100%;height:600px;background:#111;color:#ddd;padding:8px;overflow:auto}</style>\n"
"</head><body>\n"
"<h1>Vim (WebAssembly) - simple launcher</h1>\n"
"<div id='msg'>このページは web/wasm/vim.wasm を探します。存在しない場合はダウンロード手順を表示します。</div>\n"<div id='term'></div>\n"
"<p>\n"
"<button id='btnRun' onclick='tryRun()'>Run Vim (if available)</button>\n"</p>\n"
"<pre id='inst' style='display:none'>Vim WASM not found.\nTo get vim.wasm, run in package root:\n  ./web/wasm/download_vim_wasm.sh <VIM_WASM_URL>\nOr place a compatible vim.wasm into web/wasm/vim.wasm.\nNote: a JS bootstrap/terminal may be required depending on the vim.wasm build.</pre>\n"
"<script>\nasync function exists(path){ try{ let r=await fetch(path, {method:'HEAD'}); return r.ok; }catch(e){return false;} }\nasync function tryRun(){ if (!await exists('web/wasm/vim.wasm')) { document.getElementById('inst').style.display='block'; return; }\n  document.getElementById('inst').style.display='none'; document.getElementById('msg').innerText='vim.wasm found; attempting to instantiate...';\n  try{\n    const res = await fetch('web/wasm/vim.wasm'); const buf = await res.arrayBuffer(); const mod = await WebAssembly.instantiate(buf, {});\n    document.getElementById('msg').innerText='WASM instantiated: exports=' + Object.keys(mod.instance.exports).join(', ');\n    document.getElementById('term').innerText='Note: This generator does not include a full JS runtime to launch Vim.\\nIf the wasm exports a main() you may need a JS launcher.\\nOtherwise integrate vim.wasm with a suitable bootstrap (emscripten or custom loader).';\n  }catch(e){ document.getElementById('msg').innerText='instantiate failed: '+e; }\n}\n// On load, show hint if wasm missing\nexists('web/wasm/vim.wasm').then(ok=>{ if(!ok) document.getElementById('inst').style.display='block'; });\n</script>\n</body></html>\n";

/* web/wasm/download_vim_wasm.sh - user supplies URL */
static const char *download_sh =
"#!/bin/sh\n# Download vim.wasm into this directory\nif [ $# -lt 1 ]; then echo \"usage: $0 <URL-to-vim.wasm>\" >&2; exit 2; fi\nURL=$1\nOUT=\"vim.wasm\"\nif command -v curl >/dev/null 2>&1; then curl -L -o \"$OUT\" \"$URL\" || exit 1; fi\nif [ -f \"$OUT\" ]; then echo \"Downloaded $OUT\"; exit 0; fi\nif command -v wget >/dev/null 2>&1; then wget -O \"$OUT\" \"$URL\" || exit 1; fi\nif [ -f \"$OUT\" ]; then echo \"Downloaded $OUT\"; exit 0; fi\necho \"failed to download\" >&2; exit 1\n";

/* web/index.html (link to vim.html) */
static const char *web_index_html =
"<!doctype html><html><head><meta charset='utf-8'><title>Library UI</title></head><body>\n"
"<h1>蔵書データベース</h1>\n"
"<p><a href='/vim.html'>Open Vim (wasm) launcher</a></p>\n"<p><a href='/'>Back to main</a></p>\n"</body></html>\n";

/* Reuse earlier minimal server source (simplified) */
static const char *bin_server_c =
"/* bin/server.c - minimal static file server and simple API placeholders */\n"
"#define _POSIX_C_SOURCE 200809L\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n#include <sys/types.h>\n#include <sys/socket.h>\n#include <netinet/in.h>\n#include <arpa/inet.h>\n#include <sys/stat.h>\n#include <fcntl.h>\n\nstatic void send_file(int fd, const char *path){ struct stat st; if(stat(path,&st)!=0){ dprintf(fd,\"HTTP/1.1 404\\r\\nContent-Type:text/plain\\r\\n\\r\\nNot found\"); return; } int rfd=open(path,O_RDONLY); if(rfd<0){ dprintf(fd,\"HTTP/1.1 500\\r\\n\\r\\nopen err\"); return; } dprintf(fd,\"HTTP/1.1 200 OK\\r\\nContent-Length: %zu\\r\\n\\r\\n\", (size_t)st.st_size); char buf[4096]; ssize_t n; while((n=read(rfd,buf,sizeof(buf)))>0) write(fd,buf,n); close(rfd); }\n\nstatic int read_req(int fd, char *buf, size_t sz){ ssize_t r = read(fd, buf, sz-1); if(r<=0) return -1; buf[r]=0; return (int)r; }\n\nint main(void){ int sock = socket(AF_INET,SOCK_STREAM,0); if(sock<0){ perror(\"socket\"); return 1; } int opt=1; setsockopt(sock,SOL_SOCKET,SO_REUSEADDR,&opt,sizeof(opt)); struct sockaddr_in a; memset(&a,0,sizeof(a)); a.sin_family=AF_INET; a.sin_addr.s_addr=INADDR_ANY; a.sin_port=htons(8080); if(bind(sock,(struct sockaddr*)&a,sizeof(a))!=0){ perror(\"bind\"); return 1; } if(listen(sock,5)!=0){ perror(\"listen\"); return 1; } printf(\"listening on http://localhost:8080/\\n\"); for(;;){ int fd=accept(sock,NULL,NULL); if(fd<0) continue; char req[4096]; if(read_req(fd,req,sizeof(req))<0){ close(fd); continue; } char method[16], path[1024]; if(sscanf(req, \"%15s %1023s\", method, path)<2){ close(fd); continue; } if(strcmp(path, \"/\")==0) { send_file(fd, \"web/index.html\"); close(fd); continue; } /* map /vim.html and web files */ if(strcmp(path, \"/vim.html\")==0) { send_file(fd, \"web/vim.html\"); close(fd); continue; } if(strncmp(path, \"/web/\",5)==0){ char p[1024]; snprintf(p,sizeof(p),\".%s\", path); send_file(fd, p+1); close(fd); continue; } /* try web root */ if(path[0]=='/') send_file(fd, path+1); else send_file(fd, path); close(fd); } close(sock); return 0; }\n";

																																																																																																																																																																		  /* Generator main */
																																																																																																																																																																		  int main(void) {
																																																																																																																																																																		    const char *root = "omega_libmrg_web_pkg";
																																																																																																																																																																		    char path[1024];

																																																																																																																																																																		    if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

																																																																																																																																																																		    const char *dirs[] = { "bin", "lib", "include", "etc", "usr", "web", "web/wasm", "data", "scripts" };
																																																																																																																																																																		    for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
																																																																																																																																																																		      snprintf(path, sizeof(path), "%s/%s", root, dirs[i]);
																																																																																																																																																																		      if (ensure_dir(path) != 0) { fprintf(stderr, "cannot create %s\n", path); return 1; }
																																																																																																																																																																		    }

																																																																																																																																																																		    /* write Makefile */
																																																																																																																																																																		    snprintf(path, sizeof(path), "%s/Makefile", root);
																																																																																																																																																																		    if (write_file(path, makefile, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

																																																																																																																																																																		    /* README */
																																																																																																																																																																		    snprintf(path, sizeof(path), "%s/README.md", root);
																																																																																																																																																																		    if (write_file(path, readme, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

																																																																																																																																																																		    /* web files */
																																																																																																																																																																		    snprintf(path, sizeof(path), "%s/web/vim.html", root);
																																																																																																																																																																		    if (write_file(path, web_vim_html, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

																																																																																																																																																																		    snprintf(path, sizeof(path), "%s/web/index.html", root);
																																																																																																																																																																		    if (write_file(path, web_index_html, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

																																																																																																																																																																		    /* wasm download script */
																																																																																																																																																																		    snprintf(path, sizeof(path), "%s/web/wasm/download_vim_wasm.sh", root);
																																																																																																																																																																		    if (write_file(path, download_sh, 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

																																																																																																																																																																		    /* server */
																																																																																																																																																																		    snprintf(path, sizeof(path), "%s/bin/server.c", root);
																																																																																																																																																																		    if (write_file(path, bin_server_c, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

																																																																																																																																																																		    printf("Generated package '%s' with vim.wasm support helper\n", root);
																																																																																																																																																																		    printf("To fetch vim.wasm: cd %s && ./web/wasm/download_vim_wasm.sh <VIM_WASM_URL>\n", root);
																																																																																																																																																																		    printf("Then: cd %s && make && ./bin/server\n", root);
																																																																																																																																																																		    printf("Open http://localhost:8080/vim.html\n");
																																																																																																																																																																		    return 0;
																																																																																																																																																																		  }
```

補足・注意
																																																																																																																																																																		  - 実際にブラウザ上で「完全な Vim」を動かすには、単に `vim.wasm` を instantiate するだけでは足りないケースが多く、Emscripten ラッパーや端末入出力（例: xterm.js）との連携、標準ライブラリの初期化を行う JS ブートストラップが必要です。本生成器は「配置と起点」を提供します。必要なら、具体的な vim.wasm ビルド（どのリポジトリ／ビルド形式か）を教えてください。対応する JS ランチャー（あるいは emscripten の glue.js）を自動生成・埋め込みする形でさらに拡張します。
