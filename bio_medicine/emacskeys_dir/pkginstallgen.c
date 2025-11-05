/*以下は、要求どおり「bin, lib, include, usr 等のディレクトリ構成を含むパッケージ一式」をカレントディレクトリに生成する `pkginstallgen.c` です。Linux 上のネイティブ `gcc` でコンパイル & 実行すると、Windows 用リマッパ（窓使いの憂鬱風／Emacs・Vim風キーバインドを含むソース群）とビルドランナー類を出力します。Makefile は mingw-w64 クロスコンパイラを想定し、簡単な存在チェックを行うためエラーになりにくい構成にしています。

使い方
1. 保存: pkginstallgen.c
2. コンパイル: gcc pkginstallgen.c -o pkginstallgen
3. 実行: ./pkginstallgen
4. 出力されるファイル群を確認。クロスビルドは README の手順参照。

注意
- 生成される `remapper.c` は教育的サンプルです。Windows 実行や管理者権限、アンチウイルスによる制約に注意してください。
- 実運用では ToUnicodeEx を用いたキー→文字判定や、より堅牢なコマンドモード実装、targets の動的再読み込み等を推奨します。

pkginstallgen.c — そのまま保存してコンパイルしてください。

```c
*/
	   /*
 pkginstallgen.c
 Generates a packaged set of files and directories implementing a
 Windows remapper demo (窓使いの憂鬱風) with Emacs / Vim style bindings.
 Output includes directory tree: bin/, lib/, include/, usr/, and files:
  - src/remapper.c, src/emacs_bindings.c/h, src/vim_bindings.c/h, src/keymap.h
  - targets.txt, build-win.sh, emacskeys.runner, emacskeys.runner.bat, Makefile, README.txt
 Build on Linux (to produce package files):
   gcc pkginstallgen.c -o pkginstallgen
   ./pkginstallgen
	   */
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static int write_file(const char *path, const char *data) {
  FILE *f = fopen(path, "wb");
    if (!f) return 0;
    fwrite(data, 1, strlen(data), f);
    fclose(f);
    return 1;
}

static int make_dir(const char *path) {
#ifdef _WIN32
    return _mkdir(path) == 0 || errno == EEXIST;
#else
    return mkdir(path, 0755) == 0 || errno == EEXIST;
#endif
}

/* ===== contents ===== */

/* remapper.c: main hook + dispatcher using emacs/vim binding modules */
static const char *remapper_c =
"/* remapper.c - main entry for remapper (educational demo)\n   Uses emacs_bindings and vim_bindings modules. Loads targets.txt for process filtering.\n*/\n#define UNICODE\n#define _UNICODE\n#include <windows.h>\n#include <stdio.h>\n#include <wchar.h>\n#include \"keymap.h\"\n#include \"emacs_bindings.h\"\n#include \"vim_bindings.h\"\n\nstatic HHOOK g_hHook = NULL;\nstatic int g_mode = MODE_INSERT; /* MODE_INSERT / MODE_NORMAL / MODE_COMMAND */\n\n/* dynamic targets (simple, same as other sample) */\n#define MAX_TARGETS 128\nstatic wchar_t *g_targets[MAX_TARGETS]; static int g_target_count = 0;\nstatic void free_targets(void){ for(int i=0;i<g_target_count;i++){ free(g_targets[i]); g_targets[i]=NULL; } g_target_count=0; }\nstatic void load_targets(void){ FILE *f = _wfopen(L\"targets.txt\", L\"r, ccs=UTF-8\"); if(!f) return; wchar_t line[512]; while(fgetws(line, 512, f)){ wchar_t *p=line; while(*p==L' '||*p==L'\\t') p++; wchar_t *e=p+wcslen(p)-1; while(e>=p && (*e==L'\\n'||*e==L'\\r'||*e==L' '||*e==L'\\t')) *e--=L'\\0'; if(*p==L'#'||*p==L'\\0') continue; if(g_target_count<MAX_TARGETS) g_targets[g_target_count++]=_wcsdup(p); } fclose(f); }\nstatic wchar_t *get_foreground_proc(void){ HWND hwnd=GetForegroundWindow(); if(!hwnd) return NULL; DWORD pid=0; GetWindowThreadProcessId(hwnd,&pid); if(!pid) return NULL; HANDLE h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ,FALSE,pid); if(!h) return NULL; wchar_t path[MAX_PATH]; DWORD sz=MAX_PATH; if(QueryFullProcessImageNameW(h,0,path,&sz)){ wchar_t *b=wcsrchr(path,L'\\\\'); wchar_t *name=b?_wcsdup(b+1):_wcsdup(path); CloseHandle(h); return name; } CloseHandle(h); return NULL; }\nstatic int is_target_foreground(void){ if(g_target_count==0) return 0; wchar_t *name=get_foreground_proc(); if(!name) return 0; int ok=0; for(int i=0;i<g_target_count;i++){ if(_wcsicmp(name,g_targets[i])==0){ ok=1; break; } } free(name); return ok; }\n\nLRESULT CALLBACK LowLevelProc(int nCode, WPARAM wParam, LPARAM lParam){ if(nCode==HC_ACTION){ KBDLLHOOKSTRUCT *p=(KBDLLHOOKSTRUCT*)lParam; int down=(wParam==WM_KEYDOWN||wParam==WM_SYSKEYDOWN); if(down){ if(!is_target_foreground()) return CallNextHookEx(g_hHook,nCode,wParam,lParam);\n            /* dispatch to binding modules based on mode */\n            if(g_mode==MODE_INSERT){ if(emacs_handle_key(p->vkCode)) return 1; /* allow Emacs keys in insert */ }\n            else if(g_mode==MODE_NORMAL){ if(vim_handle_key(p->vkCode)) return 1; }\n            /* mode toggles */\n            if(p->vkCode==VK_ESCAPE){ g_mode=MODE_NORMAL; return 1; }\n            if(p->vkCode==0x49){ g_mode=MODE_INSERT; return 1; } /* 'i' */\n            if(p->vkCode==VK_OEM_1){ g_mode=MODE_COMMAND; return 1; }\n        } }\n    return CallNextHookEx(g_hHook,nCode,wParam,lParam); }\n\nint wmain(int argc, wchar_t **argv){ load_targets(); if(g_target_count==0){ g_targets[0]=_wcsdup(L\"notepad.exe\"); g_target_count=1; }\n    wprintf(L\"remapper: starting. targets:\\n\"); for(int i=0;i<g_target_count;i++) wprintf(L\"  %ls\\n\", g_targets[i]);\n    g_hHook = SetWindowsHookExW(WH_KEYBOARD_LL, LowLevelProc, GetModuleHandleW(NULL), 0);\n    if(!g_hHook){ fwprintf(stderr,L\"failed to install hook (%lu)\\n\", GetLastError()); free_targets(); return 1; }\n    MSG msg; while(GetMessage(&msg,NULL,0,0)){ TranslateMessage(&msg); DispatchMessage(&msg); }\n    UnhookWindowsHookEx(g_hHook); free_targets(); return 0; }\n";

		  /* emacs_bindings.h / c: basic Emacs-like key handlers */
static const char *emacs_bindings_h =
		  "/* emacs_bindings.h */\n#ifndef EMACS_BINDINGS_H\n#define EMACS_BINDINGS_H\nint emacs_handle_key(unsigned int vk);\n#endif\n";

static const char *emacs_bindings_c =
		  "/* emacs_bindings.c - simple Emacs-like handlers (Ctrl-A/E/B/F etc.) */\n#include <windows.h>\n#include \"emacs_bindings.h\"\n\nstatic void send_vk(WORD vk){ INPUT in[2]; ZeroMemory(in,sizeof(in)); in[0].type=INPUT_KEYBOARD; in[0].ki.wVk=vk; in[1].type=INPUT_KEYBOARD; in[1].ki.wVk=vk; in[1].ki.dwFlags=KEYEVENTF_KEYUP; SendInput(2,in,sizeof(INPUT)); }\n\nint emacs_handle_key(unsigned int vk){ SHORT ctrl = GetAsyncKeyState(VK_CONTROL); if(!(ctrl & 0x8000)) return 0; switch(vk){ case 0x41: send_vk(VK_HOME); return 1; case 0x45: send_vk(VK_END); return 1; case 0x42: send_vk(VK_LEFT); return 1; case 0x46: send_vk(VK_RIGHT); return 1; default: return 0; } }\n";

		  /* vim_bindings.h / c: basic Vim-like handlers (h/j/k/l, dd, yy, numeric prefix) */
static const char *vim_bindings_h =
		  "/* vim_bindings.h */\n#ifndef VIM_BINDINGS_H\n#define VIM_BINDINGS_H\nint vim_handle_key(unsigned int vk);\n#endif\n";

static const char *vim_bindings_c =
		  "/* vim_bindings.c - simple Vim-like handlers with numeric prefix and dd/yy */\n#include <windows.h>\n#include <wchar.h>\n#include \"vim_bindings.h\"\n\nstatic int numeric_prefix = 0; static DWORD last_time = 0; static WORD buf[4]; static int blen = 0;\nstatic void send_vk(WORD vk){ INPUT in[2]; ZeroMemory(in,sizeof(in)); in[0].type=INPUT_KEYBOARD; in[0].ki.wVk=vk; in[1].type=INPUT_KEYBOARD; in[1].ki.wVk=vk; in[1].ki.dwFlags=KEYEVENTF_KEYUP; SendInput(2,in,sizeof(INPUT)); }\nstatic void do_dd(void){ send_vk(VK_HOME); /* shift+end */ INPUT a[2]; ZeroMemory(a,sizeof(a)); a[0].type=INPUT_KEYBOARD; a[0].ki.wVk=VK_SHIFT; a[1].type=INPUT_KEYBOARD; a[1].ki.wVk=VK_END; SendInput(2,a,sizeof(INPUT)); INPUT b[2]; ZeroMemory(b,sizeof(b)); b[0].type=INPUT_KEYBOARD; b[0].ki.wVk=VK_END; b[0].ki.dwFlags=KEYEVENTF_KEYUP; b[1].type=INPUT_KEYBOARD; b[1].ki.wVk=VK_SHIFT; b[1].ki.dwFlags=KEYEVENTF_KEYUP; SendInput(2,b,sizeof(INPUT)); send_vk(VK_DELETE); }\nstatic void do_yy(void){ send_vk(VK_HOME); INPUT a[2]; ZeroMemory(a,sizeof(a)); a[0].type=INPUT_KEYBOARD; a[0].ki.wVk=VK_SHIFT; a[1].type=INPUT_KEYBOARD; a[1].ki.wVk=VK_END; SendInput(2,a,sizeof(INPUT)); INPUT b[2]; ZeroMemory(b,sizeof(b)); b[0].type=INPUT_KEYBOARD; b[0].ki.wVk=VK_END; b[0].ki.dwFlags=KEYEVENTF_KEYUP; b[1].type=INPUT_KEYBOARD; b[1].ki.wVk=VK_SHIFT; b[1].ki.dwFlags=KEYEVENTF_KEYUP; SendInput(2,b,sizeof(INPUT)); /* Ctrl+C */ INPUT c[4]; ZeroMemory(c,sizeof(c)); c[0].type=INPUT_KEYBOARD; c[0].ki.wVk=VK_CONTROL; c[1].type=INPUT_KEYBOARD; c[1].ki.wVk=0x43; c[2].type=INPUT_KEYBOARD; c[2].ki.wVk=0x43; c[2].ki.dwFlags=KEYEVENTF_KEYUP; c[3].type=INPUT_KEYBOARD; c[3].ki.wVk=VK_CONTROL; c[3].ki.dwFlags=KEYEVENTF_KEYUP; SendInput(4,c,sizeof(INPUT)); }\n\nint vim_handle_key(unsigned int vk){ DWORD now = GetTickCount(); if(now - last_time > 800){ blen = 0; numeric_prefix = 0; } last_time = now; if(vk >= 0x30 && vk <= 0x39){ numeric_prefix = numeric_prefix*10 + (vk - 0x30); return 1; } if(blen < 4) buf[blen++] = (WORD)vk; else blen = 0; if(blen >= 2){ if(buf[blen-2]==0x44 && buf[blen-1]==0x44){ int cnt = numeric_prefix?numeric_prefix:1; for(int i=0;i<cnt;i++) do_dd(); numeric_prefix=0; blen=0; return 1; } if(buf[blen-2]==0x59 && buf[blen-1]==0x59){ int cnt = numeric_prefix?numeric_prefix:1; for(int i=0;i<cnt;i++) do_yy(); numeric_prefix=0; blen=0; return 1; } }\n    int times = numeric_prefix?numeric_prefix:1; switch(vk){ case 0x48: for(int i=0;i<times;i++) send_vk(VK_LEFT); numeric_prefix=0; blen=0; return 1; case 0x4A: for(int i=0;i<times;i++) send_vk(VK_DOWN); numeric_prefix=0; blen=0; return 1; case 0x4B: for(int i=0;i<times;i++) send_vk(VK_UP); numeric_prefix=0; blen=0; return 1; case 0x4C: for(int i=0;i<times;i++) send_vk(VK_RIGHT); numeric_prefix=0; blen=0; return 1; default: return 0; } }\n";

		  /* keymap.h */
static const char *keymap_h =
		  "/* keymap.h */\n#ifndef KEYMAP_H\n#define KEYMAP_H\nenum { MODE_INSERT = 0, MODE_NORMAL = 1, MODE_COMMAND = 2 };\n#endif\n";

		  /* simple targets.txt */
static const char *targets_txt =
		  "# targets.txt: one process name per line (case-insensitive)\nnotepad.exe\nwordpad.exe\n";

		  /* build-win.sh */
static const char *build_sh =
		  "#!/bin/sh\n# build-win.sh - cross-build Windows remapper (x86_64 by default)\nTARGET=${1:-x86_64}\ncase \"$TARGET\" in\n  x86_64) CC=x86_64-w64-mingw32-gcc ;; i686) CC=i686-w64-mingw32-gcc ;; *) echo \"Unknown target\"; exit 2 ;;\nesac\ncommand -v \"$CC\" >/dev/null 2>&1 || (echo \"$CC not found. Install mingw-w64.\" && exit 3)\nmkdir -p bin lib include usr || true\nSRC_DIR=src\nOUT=remapper.exe\nif [ ! -f \"$SRC_DIR/remapper.c\" ]; then echo \"Source not found: $SRC_DIR/remapper.c\"; exit 4; fi\n$CC -O2 -municode $SRC_DIR/remapper.c $SRC_DIR/emacs_bindings.c $SRC_DIR/vim_bindings.c -o $OUT -luser32 -lpsapi || exit $?\necho \"Built $OUT\"\n";

/* emacskeys.runner (Linux) */
static const char *runner_sh =
  "#!/bin/sh\nCMD=${1:-run}\nrun_via_wine(){ command -v wine >/dev/null 2>&1 || return 1; wine ./remapper.exe; }\ncase \"$CMD\" in\n  build) ./build-win.sh || exit $? ;; \n  run) if [ -f ./remapper.exe ]; then run_via_wine || echo \"wine missing or failed\"; else echo \"remapper.exe not found. Run './emacskeys.runner build'\"; fi ;; \n  build-and-run) ./build-win.sh && run_via_wine ;; \n  *) echo \"Usage: $0 [build|run|build-and-run]\"; exit 1 ;;\nesac\n";

/* emacskeys.runner.bat (Windows) */
static const char *runner_bat =
  "@echo off\r\nSET CMD=%1\r\nIF \"%CMD%\"==\"\" SET CMD=run\r\nIF /I \"%CMD%\"==\"build\" (\r\n  IF EXIST src\\remapper.c (\r\n    gcc -O2 -municode src\\remapper.c src\\emacs_bindings.c src\\vim_bindings.c -o remapper.exe -luser32 -lpsapi\r\n    IF %ERRORLEVEL% NEQ 0 ( echo Build failed & exit /b %ERRORLEVEL% ) ELSE ( echo Build succeeded )\r\n  ) ELSE ( echo src\\remapper.c not found & exit /b 2 )\r\n) ELSE IF /I \"%CMD%\"==\"run\" (\r\n  IF EXIST remapper.exe ( remapper.exe ) ELSE ( echo remapper.exe not found. Run \"%~nx0 build\" first. exit /b 3 )\r\n) ELSE ( echo Usage: %~nx0 [build^|run^|build-and-run] & exit /b 1 )\r\n";

/* Makefile: checks compiler, builds remapper.exe from src */
static const char *makefile =
  "CC := x86_64-w64-mingw32-gcc\nCFLAGS := -O2 -municode\nSRC := src/remapper.c src/emacs_bindings.c src/vim_bindings.c\nOUT := remapper.exe\nall: check_compiler $(OUT)\n$(OUT): $(SRC)\t$(CC) $(CFLAGS) $(SRC) -o $(OUT) -luser32 -lpsapi\ncheck_compiler:\n\t@command -v $(CC) >/dev/null 2>&1 || (echo \"$(CC) not found. Install mingw-w64.\" && exit 1)\nclean:\n\trm -f remapper.exe\n.PHONY: all clean check_compiler\n";

/* README */
static const char *readme =
  "Windows remapper package (窓使いの憂鬱風)\n\nContents:\n - src/remapper.c                 : main\n - src/emacs_bindings.c/.h        : Emacs-like handlers\n - src/vim_bindings.c/.h          : Vim-like handlers\n - src/keymap.h                   : mode enum\n - targets.txt                     : target process list\n - build-win.sh                    : cross-build (mingw-w64)\n - emacskeys.runner                : linux helper (wine/build)\n - emacskeys.runner.bat            : windows helper\n - Makefile                        : cross-build Makefile\n - directories: bin/, lib/, include/, usr/ (created empty)\n\nBuild (Linux cross-compile):\n 1) sudo apt install mingw-w64\n 2) ./build-win.sh x86_64\n\nBuild (Windows):\n 1) With MinGW (gcc) in PATH: emacskeys.runner.bat build\n\nRun (Linux):\n ./emacskeys.runner run    # requires wine and remapper.exe\n\nNotes:\n - This is an educational demo. Use responsibly. Some behavior is approximate.\n";

/* ===== end contents ===== */

int main(void) {
/* create directories */
make_dir("bin"); make_dir("lib"); make_dir("include"); make_dir("usr");
make_dir("src");

/* write src files */
if (!write_file("src/remapper.c", remapper_c)) { perror("src/remapper.c"); return 1; }
if (!write_file("src/emacs_bindings.h", emacs_bindings_h)) { perror("src/emacs_bindings.h"); return 1; }
if (!write_file("src/emacs_bindings.c", emacs_bindings_c)) { perror("src/emacs_bindings.c"); return 1; }
if (!write_file("src/vim_bindings.h", vim_bindings_h)) { perror("src/vim_bindings.h"); return 1; }
if (!write_file("src/vim_bindings.c", vim_bindings_c)) { perror("src/vim_bindings.c"); return 1; }
if (!write_file("src/keymap.h", keymap_h)) { perror("src/keymap.h"); return 1; }

/* other package files */
if (!write_file("targets.txt", targets_txt)) { perror("targets.txt"); return 1; }
if (!write_file("build-win.sh", build_sh)) { perror("build-win.sh"); return 1; }
if (!write_file("emacskeys.runner", runner_sh)) { perror("emacskeys.runner"); return 1; }
if (!write_file("emacskeys.runner.bat", runner_bat)) { perror("emacskeys.runner.bat"); return 1; }
if (!write_file("Makefile", makefile)) { perror("Makefile"); return 1; }
if (!write_file("README.txt", readme)) { perror("README.txt"); return 1; }

/* make runner scripts executable (best effort) */
system("chmod +x build-win.sh emacskeys.runner 2>/dev/null || true");

printf("Generated package tree: bin/ lib/ include/ usr/ src/ and files (see README.txt)\n");
return 0;
}
/*
```

必要なら次の拡張を行います（選択してください）：
- ToUnicodeEx によるロケール依存の強化
- targets.txt の実行時監視（ファイル変更時に自動再読み込み）
- コマンドモード（:）の完全実装（別スレッドのコンソール入出力）
*/
