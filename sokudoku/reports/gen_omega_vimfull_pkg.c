 /*
   * gen_omega_vimfull_pkg.c
   *
   * Generates 'omega_vimfull_pkg' with:
   *  - bin/editor (terminal vim-like editor)
   *  - lib/editor.c  (improved modal editor implementation)
   *  - include/omega_vimfull.h
   *  - etc/config.sample
   *  - examples/sample.txt
   *  - Makefile
   *
   * Target: Unix-like (POSIX). Uses termios.
   *
   * Educational, extensible implementation.
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) _mkdir(p)
# define PATH_SEP '\\'
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) mkdir((p), 0755)
# define PATH_SEP '/'
#endif

  static int ensure_dir(const char *p){
  int r = MKDIR(p);
  if(r==0) return 0;
  if(errno==EEXIST) return 0;
  return -1;
}
static int write_file(const char *path, const char *data){
  FILE *f = fopen(path, "wb");
  if(!f) return -1;
  size_t n = strlen(data);
  if(fwrite(data,1,n,f) != n){ fclose(f); return -1; }
  fclose(f);
  return 0;
}

int main(void){
  const char *root = "omega_vimfull_pkg";
  char path[1024];
  const char *dirs[] = {"bin","lib","include","etc","usr","examples"};
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path, sizeof path, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(path) != 0){ fprintf(stderr, "mkdir failed: %s (%s)\n", path, strerror(errno)); return 1; }
  }

  /* include header */
    const char *hdr =
      "/* include/omega_vimfull.h */\n#ifndef OMEGA_VIMFULL_H\n#define OMEGA_VIMFULL_H\n\nint editor_main(int argc, char **argv);\n\n#endif\n";
    snprintf(path, sizeof path, "%s%cinclude%comega_vimfull.h", root, PATH_SEP, PATH_SEP);
    if(write_file(path, hdr) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/editor.c : improved editor */
    const char *editor_c =
      "/* lib/editor.c - improved vim-like modal editor (terminal)\n * Features:\n *  - Normal/Insert/Visual modes\n *  - Motions: h,j,k,l, w, b, e, 0, $\n *  - Scrolling and window with line numbers\n *  - yy/Y, p/P, dd, x, v (visual), y (yank), d (delete)\n *  - Search: /pattern (Enter)  (forward)\n *  - Replace on line: :s/old/new/g\n *  - Ctrl-S to save, q to quit (asks if unsaved)\n *  - Status line and messages\n *\n * Note: educational implementation, not fully optimized.\n */\n\n#define _POSIX_C_SOURCE 200809L\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n#include <termios.h>\n#include <sys/ioctl.h>\n#include <ctype.h>\n#include \"../include/omega_vimfull.h\"\n\n#define MAX_LINES 20000\n#define MAX_LINE_LEN 4096\n\nstatic char *lines[MAX_LINES]; static int nlines=0;\nstatic int cx=0, cy=0; /* cursor col, row */\nstatic int row_offset=0; /* top row shown */\nstatic int col_offset=0; /* left column offset (not heavily used) */\nstatic int screen_rows=24, screen_cols=80;\nstatic int dirty = 0;\nstatic struct termios orig_term;\nstatic char *clipboard = NULL; /* simple register */\n\n/* Utility */\nstatic void die(const char *s){ perror(s); exit(1); }\nstatic void disable_raw(){ tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_term); }\nstatic void enable_raw(){ struct termios raw; if(tcgetattr(STDIN_FILENO, &orig_term) == -1) die(\"tcgetattr\"); atexit(disable_raw); raw = orig_term; raw.c_lflag &= ~(ECHO | ICANON | ISIG); raw.c_iflag &= ~(IXON | ICRNL); raw.c_oflag &= ~(OPOST); raw.c_cc[VMIN] = 1; raw.c_cc[VTIME] = 0; if(tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) die(\"tcsetattr\"); }\nstatic void get_window_size(){ struct winsize ws; if(ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws)==-1) { screen_rows = 24; screen_cols = 80; } else { screen_rows = ws.ws_row; screen_cols = ws.ws_col; } }\n\n/* File IO */\nstatic void load_file(const char *path){ FILE *f = NULL; if(path) f = fopen(path, \"r\"); if(!f){ nlines=0; lines[0]=strdup(\"\"); nlines=1; return; } char buf[MAX_LINE_LEN]; nlines=0; while(fgets(buf, sizeof buf, f) && nlines < MAX_LINES){ size_t L = strcspn(buf, \"\\r\\n\"); buf[L]='\\0'; lines[nlines++]=strdup(buf); } if(nlines==0){ lines[0]=strdup(\"\"); nlines=1; } fclose(f); }\nstatic int save_file(const char *path){ if(!path) path = \"out.txt\"; FILE *f = fopen(path, \"w\"); if(!f) return -1; for(int i=0;i<nlines;i++) fprintf(f, \"%s\\n\", lines[i]); dirty = 0; fclose(f); return 0; }\n\n/* Buffer ops */\nstatic void ensure_cursor_in_bounds(){ if(cy < 0) cy = 0; if(cy >= nlines) cy = nlines - 1; int L = strlen(lines[cy]); if(cx < 0) cx = 0; if(cx > L) cx = L; }\nstatic void row_insert_char(int row, int col, char ch){ char *ln = lines[row]; int L = strlen(ln); if(L + 2 >= MAX_LINE_LEN) return; char *buf = malloc(L + 2); memcpy(buf, ln, col); buf[col] = ch; memcpy(buf+col+1, ln+col, L-col+1); free(lines[row]); lines[row] = buf; dirty = 1; }\nstatic void row_delete_char(int row, int col){ char *ln = lines[row]; int L = strlen(ln); if(col < 0 || col >= L) return; char *buf = malloc(L); memcpy(buf, ln, col); memcpy(buf+col, ln+col+1, L-col); buf[L-1] = '\\0'; free(lines[row]); lines[row] = buf; dirty = 1; }\nstatic void row_split(int row, int col){ char *ln = lines[row]; int L = strlen(ln); char *after = strdup(ln + col); ln[col] = '\\0'; lines[row] = strdup(ln); if(nlines+1 < MAX_LINES){ for(int i=nlines;i>row+1;i--) lines[i] = lines[i-1]; lines[row+1] = after; nlines++; } dirty = 1; }\nstatic void row_join(int row){ if(row+1 >= nlines) return; char *a = lines[row]; char *b = lines[row+1]; size_t na = strlen(a), nb = strlen(b); if(na + nb + 1 >= MAX_LINE_LEN) return; char *buf = malloc(na + nb + 1); memcpy(buf, a, na); memcpy(buf+na, b, nb+1); free(lines[row]); free(lines[row+1]); lines[row] = buf; for(int i=row+1;i<nlines-1;i++) lines[i] = lines[i+1]; nlines--; dirty = 1; }\nstatic void delete_line(int row){ if(row < 0 || row >= nlines) return; free(lines[row]); for(int i=row;i<nlines-1;i++) lines[i] = lines[i+1]; nlines--; if(nlines==0){ lines[0] = strdup(\"\"); nlines = 1; } dirty = 1; }\nstatic void insert_line_after(int row, const char *txt){ if(nlines+1 >= MAX_LINES) return; for(int i=nlines;i>row+1;i--) lines[i]=lines[i-1]; lines[row+1] = strdup(txt?txt:\"\"); nlines++; dirty = 1; }\n\n/* Yank/paste */\nstatic void yank_line_to_clipboard(int row){ if(row<0||row>=nlines) return; free(clipboard); clipboard = strdup(lines[row]); }\nstatic void yank_range_to_clipboard(int a, int b){ if(a<0) a=0; if(b>=nlines) b=nlines-1; size_t cap = 1024; char *buf = malloc(cap); buf[0] = '\\0'; for(int i=a;i<=b;i++){ size_t need = strlen(buf) + strlen(lines[i]) + 2; if(need > cap){ cap = need*2; buf = realloc(buf, cap); } strcat(buf, lines[i]); strcat(buf, \"\\n\"); } free(clipboard); clipboard = buf; }\nstatic void paste_after_line(int row){ if(!clipboard) return; /* insert lines of clipboard after row */ char *s = strdup(clipboard); char *p = s; char *line; int ins = 0; while((line = strsep(&p, \"\\n\"))){ insert_line_after(row + ins, line); ins++; } free(s); }\n\n/* Search simple forward, returns found row and col via pointers or -1 if not found */\nstatic int search_forward(const char *pat, int *out_row, int *out_col){ if(!pat) return -1; for(int r=cy; r<nlines; r++){ char *pos = strstr(lines[r], pat); if(pos){ *out_row = r; *out_col = pos - lines[r]; return 0; } } return -1; }\n\n/* Replace in current line: s/old/new/g (naive) */\nstatic void replace_in_line(int row, const char *old, const char *nw){ if(!old || !nw) return; char *s = lines[row]; size_t L = strlen(s); char *out = malloc(MAX_LINE_LEN); out[0]=0; char *cur = s; while(1){ char *p = strstr(cur, old); if(!p){ strncat(out, cur, MAX_LINE_LEN - strlen(out) - 1); break; } strncat(out, cur, p - cur); strncat(out, nw, MAX_LINE_LEN - strlen(out) - 1); cur = p + strlen(old); } free(lines[row]); lines[row] = out; dirty = 1; }\n\n/* Screen drawing */\nstatic void draw_rows(){ int num_width = 4; int available_cols = screen_cols - num_width - 2; int maxrow = row_offset + screen_rows - 2; if(maxrow > nlines-1) maxrow = nlines-1; for(int y=0;y<screen_rows-1;y++){\n        int filerow = row_offset + y;\n        if(filerow >= nlines){ printf(\"~\\n\"); continue; }\n        char lineno[16]; snprintf(lineno, sizeof lineno, \"%*d \", num_width, filerow+1);\n        printf(\"%s\", lineno);\n        int linelen = strlen(lines[filerow]); int startcol = col_offset; int toprint = linelen - startcol; if(toprint < 0) toprint = 0; if(toprint > available_cols) toprint = available_cols; if(toprint > 0) printf(\"%.*s\", toprint, lines[filerow]+startcol);\n        printf(\"\\x1b[K\\n\");\n    }\n}\nstatic void draw_status(const char *msg, const char *mode){ printf(\"\\x1b[7m\"); char status[256]; snprintf(status, sizeof status, \" %s - %s %s %s \", \"omega_vimfull\", mode, msg?msg:\"\", dirty?\"[+]\":\"\"); int len = strlen(status); if(len > screen_cols) status[screen_cols] = 0; printf(\"%s\", status); while((int)strlen(status) < screen_cols){ putchar(' '); status[strlen(status)] = '\\0'; }\n    printf(\"\\x1b[m\\n\"); }\n\n/* Input helpers: read char, handle escape sequences */\nstatic int read_key(){ char c; if(read(STDIN_FILENO, &c, 1) != 1) return -1; return (unsigned char)c; }\n\n/* Motion helpers */\nstatic void move_left(){ if(cx>0) cx--; else if(cy>0){ cy--; cx = strlen(lines[cy]); } }\nstatic void move_right(){ if(cx < (int)strlen(lines[cy])) cx++; else if(cy < nlines-1){ cy++; cx = 0; } }\nstatic void move_up(){ if(cy>0) cy--; if(cx > (int)strlen(lines[cy])) cx = strlen(lines[cy]); }\nstatic void move_down(){ if(cy < nlines-1) cy++; if(cx > (int)strlen(lines[cy])) cx = strlen(lines[cy]); }\nstatic void move_word_forward(){ int r = cy; int c = cx; char *s = lines[r]; int L = strlen(s); while(1){ while(c < L && !isalnum((unsigned char)s[c])) c++; while(c < L && isalnum((unsigned char)s[c])) c++; if(c < L){ cx = c; return; } if(r < nlines-1){ r++; c = 0; s = lines[r]; L = strlen(s); } else { cx = strlen(lines[cy]); return; } }\n}\nstatic void move_word_backward(){ int r = cy; int c = cx; char *s = lines[r]; while(1){ if(c <= 0){ if(r==0){ cx = 0; return; } r--; c = strlen(lines[r]); s = lines[r]; }\n        c--; while(c>0 && !isalnum((unsigned char)s[c])) c--; while(c>0 && isalnum((unsigned char)s[c-1])) c--; cx = c; cy = r; if(1) return; }\n}\nstatic void move_word_end(){ int r = cy; int c = cx; while(r < nlines){ char *s = lines[r]; int L = strlen(s); int i = c; while(i < L && !isalnum((unsigned char)s[i])) i++; if(i==L){ r++; c = 0; continue; } while(i < L && isalnum((unsigned char)s[i])) i++; cx = i-1; cy = r; return; } cx = strlen(lines[cy]); }\n\n/* Main editor loop */\nint editor_main(int argc, char **argv){ const char *path = (argc>=2)?argv[1]:NULL; load_file(path); enable_raw(); get_window_size(); int mode = 0; /* 0=normal,1=insert,2=visual */ int visual_start_row = -1, visual_start_col = -1; char msg[128] = \"\";\n    while(1){ ensure_cursor_in_bounds(); if(cy < row_offset) row_offset = cy; if(cy >= row_offset + screen_rows - 2) row_offset = cy - (screen_rows - 2) + 1; printf(\"\\x1b[?25l\"); printf(\"\\x1b[2J\\x1b[H\"); draw_rows(); const char *mstr = mode==0?\"NORMAL\":(mode==1?\"INSERT\":\"VISUAL\"); draw_status(msg, mstr); /* place cursor */ int curscrrow = cy - row_offset + 1; int curscrcol = cx + 1 + 5; printf(\"\\x1b[%d;%dH\", curscrrow, curscrcol); fflush(stdout);\n        int c = read_key(); if(c == -1) break; if(mode == 1){ /* INSERT */ if(c == 27){ mode = 0; snprintf(msg, sizeof msg, \"\"); continue; } if(c==127 || c==8){ if(cx>0){ cx--; row_delete_char(cy, cx); } else if(cx==0 && cy>0){ int prevlen = strlen(lines[cy-1]); row_join(cy-1); cy--; cx = prevlen; } continue; } if(c == '\\r' || c == '\\n'){ row_split(cy, cx); cy++; cx = 0; continue; } row_insert_char(cy, cx, (char)c); cx++; continue; }\n        /* NORMAL or VISUAL */ if(c==':'){ /* command line: read until \\n */ printf(\"\\x1b[%d;1H\\x1b[K:\", screen_rows); fflush(stdout); char cmdbuf[512]; int i=0; while(1){ int cc = read_key(); if(cc==10 || cc==13) break; if(cc==127 || cc==8){ if(i>0) { i--; printf(\"\\b \\b\"); fflush(stdout); } continue; } if(i < (int)sizeof(cmdbuf)-1) { cmdbuf[i++] = (char)cc; putchar((char)cc); fflush(stdout); } } cmdbuf[i]=0; /* parse simple :s/old/new/g or :w or :q */ if(strncmp(cmdbuf, \"w\", 1) == 0){ if(save_file(path)==0) snprintf(msg,sizeof msg,\"Saved %s\", path?path:\"out.txt\"); else snprintf(msg,sizeof msg,\"Save failed\"); } else if(strncmp(cmdbuf, \"q\",1)==0){ if(dirty){ snprintf(msg,sizeof msg,\"Unsaved changes! Use :q! to force\"); if(strcmp(cmdbuf, \"q!\")==0) { disable_raw(); return 0; } } else { disable_raw(); return 0; } } else if(cmdbuf[0]=='s' && cmdbuf[1]=='/'){ /* s/old/new/g */ char *p = cmdbuf+2; char *old = strsep(&p, \"/\"); char *nw = p?strsep(&p, \"/\"):NULL; if(old && nw){ replace_in_line(cy, old, nw); snprintf(msg,sizeof msg,\":\" \"s executed\"); } } else snprintf(msg,sizeof msg,\"Unknown cmd: %s\", cmdbuf);\n            continue; }\n        if(c == '/'){ /* search: read pattern */ printf(\"\\x1b[%d;1H\\x1b[K/\", screen_rows); fflush(stdout); char pat[256]; int i=0; while(1){ int cc = read_key(); if(cc==10||cc==13) break; if(cc==127||cc==8){ if(i>0){ i--; printf(\"\\b \\b\"); fflush(stdout); } continue;} if(i < (int)sizeof(pat)-1){ pat[i++] = (char)cc; putchar((char)cc); fflush(stdout); } } pat[i]=0; int rr, rc; if(search_forward(pat, &rr, &rc)==0){ cy = rr; cx = rc; row_offset = rr; snprintf(msg,sizeof msg, \"Found: %s\", pat); } else snprintf(msg,sizeof msg, \"Not found: %s\", pat); continue; }\n        if(c == 17){ /* Ctrl-Q - also quit */ if(dirty){ snprintf(msg,sizeof msg, \"Unsaved. Use :q to quit or :w to save\"); } else { disable_raw(); return 0; } continue; }\n        if(c == 19){ /* Ctrl-S */ if(save_file(path)==0) snprintf(msg,sizeof msg, \"Saved\"); else snprintf(msg,sizeof msg, \"Save failed\"); continue; }\n        if(c == 'i'){ mode = 1; snprintf(msg,sizeof msg, \"INSERT\"); continue; }\n        if(c == 'a'){ /* move right if possible then insert */ move_right(); mode = 1; snprintf(msg,sizeof msg, \"INSERT\"); continue; }\n        if(c == 'o'){ insert_line_after(cy, \"\"); cy++; cx = 0; mode = 1; continue; }\n        if(c == 'v'){ if(mode==2){ mode = 0; snprintf(msg,sizeof msg, \"\"); } else { mode = 2; visual_start_row = cy; visual_start_col = cx; snprintf(msg,sizeof msg, \"VISUAL\"); } continue; }\n        /* 2-char ops state */ static int lastc = 0; if(lastc == 0){ if(c=='y' || c=='d'){ lastc = c; continue; } }\n        else { if(lastc == 'y' && c=='y'){ /* yank line */ yank_line_to_clipboard(cy); snprintf(msg,sizeof msg, \"yanked line\"); lastc = 0; continue; } if(lastc=='d' && c=='d'){ yank_line_to_clipboard(cy); delete_line(cy); if(cy >= nlines) cy = nlines-1; snprintf(msg,sizeof msg, \"deleted line\"); lastc = 0; continue; } /* fallback */ lastc = 0; }\n        /* single-key cmds */ switch(c){ case 'h': move_left(); break; case 'l': move_right(); break; case 'k': move_up(); break; case 'j': move_down(); break; case 'g': cx = 0; break; case '0': cx = 0; break; case '$': cx = strlen(lines[cy]); break; case 'w': move_word_forward(); break; case 'b': move_word_backward(); break; case 'e': move_word_end(); break; case 'p': paste_after_line(cy); break; case 'P': paste_after_line(cy-1); break; case 'x': row_delete_char(cy, cx); break; case 'Y': yank_line_to_clipboard(cy); break; case 'y': /* single y: wait for next handled above */ break; case 'd': /* single d: wait */ break; case 'q': if(dirty){ snprintf(msg,sizeof msg, \"Unsaved changes! Use :q to quit\"); } else { disable_raw(); return 0; } break; default: break; }\n        /* Visual mode yank/delete */ if(mode==2){ if(c=='y'){ int a = visual_start_row, b = cy; if(a>b){ int t=a;a=b;b=t; } yank_range_to_clipboard(a,b); mode = 0; snprintf(msg,sizeof msg, \"yanked region %d..%d\", a+1, b+1); } if(c=='d'){ int a=visual_start_row,b=cy; if(a>b){ int t=a;a=b;b=t; } /* delete from a..b */ for(int i=0;i<=b-a;i++) delete_line(a); mode = 0; snprintf(msg,sizeof msg, \"deleted region\"); } }\n    }\n    disable_raw(); return 0; }\n";
    snprintf(path, sizeof path, "%s%clib%ceditor.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, editor_c) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/launcher.c */
    const char *launcher =
      "#include <stdio.h>\n#include <stdlib.h>\nint editor_main(int argc, char **argv);\nint main(int argc, char **argv){ return editor_main(argc, argv); }\n";
    snprintf(path, sizeof path, "%s% cbin%clauncher.c", root, PATH_SEP, PATH_SEP); /* placeholder then fix */ 
    snprintf(path, sizeof path, "%s%cbin%clauncher.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, launcher) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* Makefile */
    const char *makefile =
      "CC=gcc\nCFLAGS=-O2 -Iinclude\n\nall: bin/editor\n\nbin/editor: bin/launcher.c lib/editor.c\n\t$(CC) $(CFLAGS) -o bin/editor bin/launcher.c lib/editor.c\n\nclean:\n\trm -f bin/editor\n";
    snprintf(path, sizeof path, "%s%cMakefile", root, PATH_SEP);
    if(write_file(path, makefile) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* etc/config.sample */
    const char *config =
      "# Sample config for omega_vimfull (not parsed in this prototype)\n# preferred_line_length=80\n# show_line_numbers=true\n";
    snprintf(path, sizeof path, "%s%cetc%cconfig.sample", root, PATH_SEP, PATH_SEP);
    if(write_file(path, config) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* examples/sample.txt */
    const char *sample =
      "This is a sample file for omega_vimfull.\n\nCommands:\n - i / a / o : enter insert mode\n - Esc : return to normal mode\n - h j k l : move\n - w b e : motions (word)\n - 0 $ g : line motions\n - v : visual mode (select), then y to yank or d to delete\n - yy / dd : line yank / delete\n - p / P : paste after/before\n - /pattern : search forward\n - :s/old/new/g : replace on current line\n - Ctrl-S : save\n - :w : save, :q : quit\n\nTry editing this file.\n";
    snprintf(path, sizeof path, "%s%cexamples%csample.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, sample) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* README */
    const char *readme =
      "omega_vimfull_pkg\n\nA tiny Vim-like editor prototype (terminal) with modal editing,\nmotions, visual selection, yank/paste, search/replace, and status line.\n\nBuild:\n  make\n\nRun:\n  ./bin/editor examples/sample.txt\n\nControls (summary):\n  Normal: h j k l w b e 0 $ g\n  i a o -> Insert\n  v -> Visual\n  yy, dd, p, P, x\n  /pattern -> search\n  :s/old/new/g -> replace current line\n  Ctrl-S -> save, :w -> save, :q -> quit\n";
    snprintf(path, sizeof path, "%s%creadme.txt", root, PATH_SEP);
    if(write_file(path, readme) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    printf("Package '%s' created.\n", root);
    printf("Build & run:\n  cd %s\n  make\n  ./bin/editor examples/sample.txt\n", root);
    return 0;
}
