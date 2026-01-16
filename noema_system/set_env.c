以下は先の Noema スクリプトで想定しているネイティブ関数群の C 実装例です。POSIX 環境（Linux/macOS）向けで、端末制御に `termios` と `read`、ファイル I/O に `fopen`/`fread`、文字列 Value 生成に `val_string()` 等を想定しています。あなたのインタプリタの Value/メモリ管理 API に合わせて `val_string`, `val_number`, `val_null`, `val_bool`, `val_func` 等を調整してください。

注意：
- Windows で使う場合は端末制御や read の部分を置き換えてください。
- `val_string` が与えられたバッファをコピーする想定で実装しています（必要なら free を調整）。

（1）ヘッダ・ユーティリティ（ファイル先頭に追加）
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <errno.h>
#include <time.h>

/* 以下はあなたの実装する VM の Value 作成関数のプロトタイプを仮定 */
Value *val_string(const char *s);
Value *val_number(double n);
Value *val_null(void);
Value *val_bool(int b);
Value *val_func(Value *(*fn)(int, Value**), int argc);

/* readline 実装で getline を使う場合は _GNU_SOURCE 等が必要な環境もあるので注意 */
```

(2) readkey() — 1 文字（キーコード）を生で返す。ESC は 27、Enter は 10、Backspace は 127
```c
/* readkey(): returns number Value for key code, or null on EOF/error */
static Value *native_readkey(int argc, Value **argv){
	    struct termios oldt, newt;
	        int nread;
		    unsigned char c;

		        /* get current terminal attributes */
		        if (tcgetattr(STDIN_FILENO, &oldt) != 0) {
				        return val_null();
					    }
			    newt = oldt;
			        /* disable canonical mode and echo */
			        newt.c_lflag &= ~(ICANON | ECHO);
				    /* minimum number of bytes and timeout */
				    newt.c_cc[VMIN] = 1;
				        newt.c_cc[VTIME] = 0;
					    if (tcsetattr(STDIN_FILENO, TCSANOW, &newt) != 0) {
						            return val_null();
							        }

					        nread = read(STDIN_FILENO, &c, 1);

						    /* restore terminal */
						    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);

						        if (nread <= 0) return val_null();

							    return val_number((double)c);
}
```

(3) clear_screen() — 端末をクリア
```c
static Value *native_clear_screen(int argc, Value **argv){
	    /* ANSI clear screen */
	    const char *esc = "\x1b[2J\x1b[H";
	        write(STDOUT_FILENO, esc, strlen(esc));
		    return val_null();
}
```

(4) write(s) — 改行なしで文字列を出力
```c
static Value *native_write(int argc, Value **argv){
	    if (argc < 1) return val_null();
	        if (argv[0]->type != T_STRING) return val_null();
		    const char *s = argv[0]->v.str;
		        size_t L = strlen(s);
			    ssize_t w = write(STDOUT_FILENO, s, L);
			        (void)w;
				    return val_null();
}
```

(5) sleep(ms) — ミリ秒待機
```c
static Value *native_sleep(int argc, Value **argv){
	    if (argc < 1) return val_null();
	        double ms = argv[0]->v.num;
		    if (ms < 0) ms = 0;
		        struct timespec ts;
			    ts.tv_sec = (time_t)(ms / 1000);
			        ts.tv_nsec = (long)((fmod(ms, 1000.0)) * 1e6);
				    nanosleep(&ts, NULL);
				        return val_null();
}
```

(6) file_read(path) -> string or null
```c
static Value *native_file_read(int argc, Value **argv){
	    if (argc < 1 || argv[0]->type != T_STRING) return val_null();
	        const char *path = argv[0]->v.str;
		    FILE *f = fopen(path, "rb");
		        if (!f) return val_null();
			    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return val_null(); }
			        long sz = ftell(f);
				    rewind(f);
				        char *buf = malloc(sz + 1);
					    if (!buf) { fclose(f); return val_null(); }
					        size_t r = fread(buf, 1, sz, f);
						    buf[r] = '\0';
						        fclose(f);
							    Value *ret = val_string(buf);
							        free(buf); /* assume val_string copied */
								    return ret;
}
```

(7) file_write(path, content) -> bool
```c
static Value *native_file_write(int argc, Value **argv){
	    if (argc < 2) return val_bool(0);
	        if (argv[0]->type != T_STRING || argv[1]->type != T_STRING) return val_bool(0);
		    const char *path = argv[0]->v.str;
		        const char *content = argv[1]->v.str;
			    FILE *f = fopen(path, "wb");
			        if (!f) return val_bool(0);
				    size_t w = fwrite(content, 1, strlen(content), f);
				        fclose(f);
					    return val_bool(w == strlen(content));
}
```

(8) native_string_from_code(n) -> single-char string
```c
static Value *native_string_from_code(int argc, Value **argv){
	    if (argc < 1) return val_string("");
	        int code = (int)argv[0]->v.num;
		    char s[5] = {0};
		        if (code < 0 || code > 0x10FFFF) return val_string("");
			    /* simple ASCII / UTF-8 encoding for BMP */
			    if (code < 0x80) {
				            s[0] = (char)code;
					            s[1] = '\0';
						        } else if (code < 0x800) {
								        s[0] = 0xC0 | ((code >> 6) & 0x1F);
									        s[1] = 0x80 | (code & 0x3F);
										        s[2] = '\0';
											    } else if (code < 0x10000) {
												            s[0] = 0xE0 | ((code >> 12) & 0x0F);
													            s[1] = 0x80 | ((code >> 6) & 0x3F);
														            s[2] = 0x80 | (code & 0x3F);
															            s[3] = '\0';
																        } else {
																		        s[0] = 0xF0 | ((code >> 18) & 0x07);
																			        s[1] = 0x80 | ((code >> 12) & 0x3F);
																				        s[2] = 0x80 | ((code >> 6) & 0x3F);
																					        s[3] = 0x80 | (code & 0x3F);
																						        s[4] = '\0';
																							    }
			        return val_string(s);
}
```

(9) readline(prompt) — 前に示した getline ベースの実装（改めて短縮）
```c
static Value *native_readline(int argc, Value **argv){
	    const char *prompt = NULL;
	        if (argc >= 1 && argv[0]->type == T_STRING) prompt = argv[0]->v.str;
		    if (prompt && prompt[0]) {
			            write(STDOUT_FILENO, prompt, strlen(prompt));
				            fflush(stdout);
					        }
		        char *line = NULL;
			    size_t len = 0;
			        ssize_t r = getline(&line, &len, stdin);
				    if (r <= 0) { if (line) free(line); return val_null(); }
				        while (r > 0 && (line[r-1] == '\n' || line[r-1] == '\r')) { line[--r] = '\0'; }
					    Value *v = val_string(line);
					        free(line);
						    return v;
}
```

(10) 登録（bootstrap_env 内に追加する行）
```c
    env_set("readkey", val_func(native_readkey, 0));
        env_set("clear_screen", val_func(native_clear_screen, 0));
	    env_set("write", val_func(native_write, 1));
	        env_set("sleep", val_func(native_sleep, 1));
		    env_set("file_read", val_func(native_file_read, 1));
		        env_set("file_write", val_func(native_file_write, 2));
			    env_set("string_from_code", val_func(native_string_from_code, 1));
			        env_set("readline", val_func(native_readline, 1));
				```

				注意点（短く）
				- あなたの VM の Value 型名やフィールド名（例: `T_STRING`, `v.str`, `v.num`）が異なる場合は合わせてください。
				- `readkey()` では端末を raw にして 1 バイト読み、元に戻しています。複数バイトのエスケープシーケンス（矢印キーなど）を扱うには追加処理が必要です（現在は1バイト単位）。
				- セキュリティ上および移植性の観点で、Windows 対応や非 POSIX 環境では別実装が必要です。

				必要なら、あなたの Value 構造体（ヘッダ）を教えてもらえれば、細部をあなたの VM 用に合わせた完全なソース（コンパイル可能）を作成します。
