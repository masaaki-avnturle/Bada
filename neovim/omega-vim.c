以下に、前回のミニVim実装をエラーなくビルドできるように最初から最後まで単一ファイル `pkginstallgen.c` として書き直しました。ncurses（wide 版でなくても可）を使います。ビルド例はファイル末尾に記載しています。

注意：
- これは教育・プロトタイプ目的の簡易実装です。Vimの全機能は含みません。
- マルチバイト／Unicode やパフォーマンス向上、細かなVim挙動は未実装です。

保存してビルドしてください。

```c
/* pkginstallgen.c
 *
 * omega-vim-lite: simplified "mini-Vim" prototype (single-file).
 *
 * Build:
 *   sudo apt-get install libncursesw5-dev    # Debian/Ubuntu
 *   gcc -std=c11 -O2 -o pkginstallgen pkginstallgen.c -lncursesw
 *
 * Usage:
 *   ./pkginstallgen [file]
 *
 * License: MIT (example prototype)
 */

#define _XOPEN_SOURCE 700
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <locale.h>
#include <ncurses.h>
#include <ctype.h>
#include <stdarg.h>
#include <errno.h>

/* Config */
#define MAX_BUFFERS 16
#define LINE_GROW 128

/* Types */
typedef enum { MODE_NORMAL, MODE_INSERT, MODE_VISUAL, MODE_COMMAND } Mode;
typedef enum { OP_INSERT, OP_DELETE } OpType;

typedef struct {
  char *data;    /* bytes, no trailing '\n' */
  size_t len;
  size_t cap;
} Line;

typedef struct {
  Line *lines;
  size_t nlines;
  size_t cap;
  char *filename;
  int modified;
} Buffer;

typedef struct {
  OpType type;
  int buf_id;
  size_t line;
  size_t col;
  char *text; /* inserted or deleted text; may contain '\n' */
} EditOp;

typedef struct {
  EditOp *arr;
  size_t top;
  size_t cap;
} UndoStack;

/* Globals */
static Buffer buffers[MAX_BUFFERS];
static int buf_count = 0;
static int curbuf = 0;

static Mode mode = MODE_NORMAL;
static size_t cx = 0, cy = 0;      /* cursor column (byte offset) and line index */
static size_t view_row = 0, view_col = 0;
static int screen_rows = 24, screen_cols = 80;
static char status[256] = "";
static UndoStack undo_stack = {NULL,0,0};
static UndoStack redo_stack = {NULL,0,0};
static char *clipboard = NULL;
static size_t visual_srow = 0, visual_scol = 0;
static int visual_linewise = 0;

/* Utility */
static void die(const char *fmt, ...) {
  endwin();
  va_list ap; va_start(ap, fmt);
  vfprintf(stderr, fmt, ap);
  va_end(ap);
  fprintf(stderr, "\n");
  exit(1);
}

static void set_statusf(const char *fmt, ...) {
  va_list ap; va_start(ap, fmt);
  vsnprintf(status, sizeof(status), fmt, ap);
  va_end(ap);
}

/* Line helpers */
static Line mkline_from_cstr(const char *s) {
  Line L;
  size_t len = s ? strlen(s) : 0;
  L.cap = ((len + LINE_GROW) / LINE_GROW) * LINE_GROW;
  if (L.cap == 0) L.cap = LINE_GROW;
  L.data = malloc(L.cap + 1);
  if (!L.data) die("malloc");
  memcpy(L.data, s ? s : "", len);
  L.data[len] = '\0';
  L.len = len;
  return L;
}
static void line_free(Line *L) { if (!L) return; free(L->data); L->data = NULL; L->len = 0; L->cap = 0; }

/* Buffer management */
static void buffer_ensure(Buffer *b, size_t n) {
  if (b->cap >= n) return;
  size_t nc = (n + 16);
  Line *new = realloc(b->lines, sizeof(Line) * nc);
  if (!new) die("realloc");
  b->lines = new;
  for (size_t i = b->cap; i < nc; ++i) { b->lines[i].data = NULL; b->lines[i].len = 0; b->lines[i].cap = 0; }
  b->cap = nc;
}
static Buffer* buffer_new(const char *filename) {
  if (buf_count >= MAX_BUFFERS) return NULL;
  Buffer *b = &buffers[buf_count];
  b->lines = NULL; b->nlines = 0; b->cap = 0; b->filename = NULL; b->modified = 0;
  if (filename) b->filename = strdup(filename);
  buf_count++;
  return b;
}
static void buffer_free(Buffer *b) {
  if (!b) return;
  for (size_t i = 0; i < b->nlines; ++i) line_free(&b->lines[i]);
  free(b->lines); b->lines = NULL; b->nlines = 0; b->cap = 0;
  free(b->filename); b->filename = NULL;
}
static int buffer_load(Buffer *b, const char *filename) {
  FILE *f = fopen(filename, "rb");
  if (!f) return -1;
  if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return -1; }
  long sz = ftell(f);
  if (sz < 0) { fclose(f); return -1; }
  if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return -1; }
  char *buf = malloc((size_t)sz + 1);
  if (!buf) { fclose(f); return -1; }
  size_t r = fread(buf, 1, (size_t)sz, f);
  buf[r] = '\0';
  fclose(f);
  size_t start = 0;
  for (size_t i = 0; i < r; ++i) {
    if (buf[i] == '\n') {
      size_t len = i - start;
      buffer_ensure(b, b->nlines + 1);
      char *s = malloc(len + 1);
      if (!s) die("malloc");
      memcpy(s, buf + start, len); s[len] = '\0';
      b->lines[b->nlines++] = mkline_from_cstr(s);
      free(s);
      start = i + 1;
    }
  }
  if (start <= r) {
    size_t len = r - start;
    buffer_ensure(b, b->nlines + 1);
    char *s = malloc(len + 1);
    if (!s) die("malloc");
    memcpy(s, buf + start, len); s[len] = '\0';
    b->lines[b->nlines++] = mkline_from_cstr(s);
    free(s);
  }
  free(buf);
  free(b->filename);
  b->filename = strdup(filename);
  b->modified = 0;
  return 0;
}
static int buffer_write(Buffer *b, const char *filename) {
  FILE *f = fopen(filename, "wb");
  if (!f) return -1;
  for (size_t i = 0; i < b->nlines; ++i) {
    if (b->lines[i].len > 0) fwrite(b->lines[i].data, 1, b->lines[i].len, f);
    fputc('\n', f);
  }
  fclose(f);
  free(b->filename);
  b->filename = strdup(filename);
  b->modified = 0;
  return 0;
}
static Buffer* cur_buffer() { return &buffers[curbuf]; }
static size_t line_len(Buffer *b, size_t row) { if (row >= b->nlines) return 0; return b->lines[row].len; }

/* Cursor / viewport */
static void clamp_cursor() {
  Buffer *b = cur_buffer();
  if (b->nlines == 0) { cy = 0; cx = 0; return; }
  if (cy >= b->nlines) cy = b->nlines - 1;
  size_t llen = line_len(b, cy);
  if (cx > llen) cx = llen;
  if (cy < view_row) view_row = cy;
  if (cy >= view_row + (size_t)screen_rows - 2) view_row = cy - (screen_rows - 3);
  if (cx < view_col) view_col = cx;
  if (cx >= view_col + (size_t)screen_cols - 1) view_col = cx - (screen_cols - 2);
}

/* Undo stack */
static void undo_init(UndoStack *s) {
  s->cap = 1024;
  s->arr = calloc(s->cap, sizeof(EditOp));
  if (!s->arr) die("calloc");
  s->top = 0;
}
static void undo_push(UndoStack *s, EditOp *op) {
  if (!s->arr) undo_init(s);
  if (s->top >= s->cap) { s->cap *= 2; s->arr = realloc(s->arr, s->cap * sizeof(EditOp)); if (!s->arr) die("realloc"); }
  s->arr[s->top++] = *op;
}
static int undo_pop(UndoStack *s, EditOp *out) {
  if (!s->arr || s->top == 0) return 0;
  *out = s->arr[--s->top];
  return 1;
}
static void free_editop(EditOp *op) { free(op->text); op->text = NULL; }

/* Rebuild buffer from full string */
static void rebuild_buffer_from_string(Buffer *b, char *str, size_t len) {
  for (size_t i = 0; i < b->nlines; ++i) line_free(&b->lines[i]);
  free(b->lines); b->lines = NULL; b->nlines = 0; b->cap = 0;
  size_t start = 0;
  for (size_t i = 0; i < len; ++i) {
    if (str[i] == '\n') {
      size_t l = i - start;
      buffer_ensure(b, b->nlines + 1);
      char *s = malloc(l + 1);
      if (!s) die("malloc");
      memcpy(s, str + start, l); s[l] = '\0';
      b->lines[b->nlines++] = mkline_from_cstr(s);
      free(s);
      start = i + 1;
    }
  }
  if (start <= len) {
    size_t l = len - start;
    buffer_ensure(b, b->nlines + 1);
    char *s = malloc(l + 1);
    if (!s) die("malloc");
    memcpy(s, str + start, l); s[l] = '\0';
    b->lines[b->nlines++] = mkline_from_cstr(s);
    free(s);
  }
  b->modified = 1;
}

/* Insert text at (line,col); text may contain '\n' */
static void do_insert(Buffer *b, size_t line, size_t col, const char *text) {
  if (!b) return;
  /* build full buffer string */
  size_t total = 0;
  for (size_t i = 0; i < b->nlines; ++i) total += b->lines[i].len + 1;
  char *all = malloc(total + 1);
  if (!all) die("malloc");
  size_t p = 0;
  for (size_t i = 0; i < b->nlines; ++i) {
    if (b->lines[i].len) memcpy(all + p, b->lines[i].data, b->lines[i].len);
    p += b->lines[i].len;
    all[p++] = '\n';
  }
  all[p] = '\0';
  size_t abs = 0;
  if (line >= b->nlines) abs = total;
  else {
    for (size_t i = 0; i < line; ++i) abs += b->lines[i].len + 1;
    if (col > b->lines[line].len) col = b->lines[line].len;
    abs += col;
  }
  size_t tlen = strlen(text);
  char *newall = malloc(total + tlen + 1);
  if (!newall) die("malloc");
  memcpy(newall, all, abs);
  memcpy(newall + abs, text, tlen);
  memcpy(newall + abs + tlen, all + abs, total - abs);
  newall[total + tlen] = '\0';
  rebuild_buffer_from_string(b, newall, total + tlen);
  free(all); free(newall);
}

/* Delete range [sline,scol) .. (eline,ecol) and return deleted text (malloc'd) */
static char* do_delete_range(Buffer *b, size_t sline, size_t scol, size_t eline, size_t ecol) {
  if (!b) return NULL;
  size_t total = 0;
  for (size_t i = 0; i < b->nlines; ++i) total += b->lines[i].len + 1;
  char *all = malloc(total + 1);
  if (!all) die("malloc");
  size_t p = 0;
  for (size_t i = 0; i < b->nlines; ++i) {
    if (b->lines[i].len) memcpy(all + p, b->lines[i].data, b->lines[i].len);
    p += b->lines[i].len;
    all[p++] = '\n';
  }
  all[p] = '\0';
  size_t abs_s = 0, abs_e = 0;
  if (sline >= b->nlines) abs_s = total;
  else {
    for (size_t i = 0; i < sline; ++i) abs_s += b->lines[i].len + 1;
    abs_s += scol;
  }
  if (eline >= b->nlines) abs_e = total;
  else {
    for (size_t i = 0; i < eline; ++i) abs_e += b->lines[i].len + 1;
    abs_e += ecol;
  }
  if (abs_s > total) abs_s = total;
  if (abs_e > total) abs_e = total;
  if (abs_s >= abs_e) { free(all); return strdup(""); }
  size_t dlen = abs_e - abs_s;
  char *deleted = malloc(dlen + 1);
  if (!deleted) die("malloc");
  memcpy(deleted, all + abs_s, dlen);
  deleted[dlen] = '\0';
  char *newall = malloc(total - dlen + 1);
  if (!newall) die("malloc");
  memcpy(newall, all, abs_s);
  memcpy(newall + abs_s, all + abs_e, total - abs_e);
  newall[total - dlen] = '\0';
  rebuild_buffer_from_string(b, newall, total - dlen);
  free(all); free(newall);
  return deleted;
}

/* High-level operations with undo */
static void record_and_insert(Buffer *b, size_t line, size_t col, const char *txt) {
  EditOp op = {OP_INSERT, curbuf, line, col, strdup(txt)};
  undo_push(&undo_stack, &op);
  /* clear redo stack (simple) */
  redo_stack.top = 0;
  do_insert(b, line, col, txt);
}

static void record_and_delete_range(Buffer *b, size_t sline, size_t scol, size_t eline, size_t ecol) {
  char *deleted = do_delete_range(b, sline, scol, eline, ecol);
  EditOp op = {OP_DELETE, curbuf, sline, scol, deleted};
  undo_push(&undo_stack, &op);
  redo_stack.top = 0;
}

/* Undo / Redo */
static void do_undo() {
  EditOp op;
  if (!undo_pop(&undo_stack, &op)) { set_statusf("Nothing to undo"); return; }
  Buffer *b = &buffers[op.buf_id];
  if (op.type == OP_INSERT) {
    /* delete the inserted text */
    size_t len = strlen(op.text);
    size_t eline = op.line, ecol = op.col;
    for (size_t i = 0; i < len; ++i) {
      if (op.text[i] == '\n') { eline++; ecol = 0; }
      else ecol++;
    }
    char *deleted = do_delete_range(b, op.line, op.col, eline, ecol);
    EditOp rev = {OP_DELETE, op.buf_id, op.line, op.col, deleted};
    undo_push(&redo_stack, &rev);
    free_editop(&op);
    set_statusf("undo insert");
  } else if (op.type == OP_DELETE) {
    /* re-insert deleted text */
    do_insert(b, op.line, op.col, op.text);
    EditOp rev = {OP_INSERT, op.buf_id, op.line, op.col, strdup(op.text)};
    undo_push(&redo_stack, &rev);
    free_editop(&op);
    set_statusf("undo delete");
  } else {
    free_editop(&op);
  }
  clamp_cursor();
}

static void do_redo() {
  EditOp op;
  if (!undo_pop(&redo_stack, &op)) { set_statusf("Nothing to redo"); return; }
  Buffer *b = &buffers[op.buf_id];
  if (op.type == OP_INSERT) {
    do_insert(b, op.line, op.col, op.text);
    EditOp rev = {OP_INSERT, op.buf_id, op.line, op.col, strdup(op.text)};
    undo_push(&undo_stack, &rev);
    free_editop(&op);
    set_statusf("redo insert");
  } else if (op.type == OP_DELETE) {
    size_t len = strlen(op.text);
    size_t eline = op.line, ecol = op.col;
    for (size_t i = 0; i < len; ++i) {
      if (op.text[i] == '\n') { eline++; ecol = 0; }
      else ecol++;
    }
    char *deleted = do_delete_range(b, op.line, op.col, eline, ecol);
    EditOp rev = {OP_DELETE, op.buf_id, op.line, op.col, deleted};
    undo_push(&undo_stack, &rev);
    free_editop(&op);
    set_statusf("redo delete");
  } else {
    free_editop(&op);
  }
  clamp_cursor();
}

/* Search */
static int search_forward(const char *pat) {
  Buffer *b = cur_buffer();
  if (!pat || !*pat) return 0;
  for (size_t r = cy; r < b->nlines; ++r) {
    char *line = b->lines[r].data;
    char *found = strstr(line + (r == cy ? (int)cx : 0), pat);
    if (found) { cy = r; cx = found - line; clamp_cursor(); return 1; }
  }
  set_statusf("Not found");
  return 0;
}
static int search_backward(const char *pat) {
  Buffer *b = cur_buffer();
  if (!pat || !*pat) return 0;
  if (b->nlines == 0) return 0;
  for (int r = (int)cy; r >= 0; --r) {
    char *line = b->lines[r].data;
    char *found = NULL;
    char *p = line;
    while (1) {
      char *t = strstr(p, pat);
      if (!t) break;
      found = t; p = t + 1;
    }
    if (found) { cy = r; cx = found - line; clamp_cursor(); return 1; }
  }
  set_statusf("Not found");
  return 0;
}

/* Rendering */
static void draw_screen() {
  getmaxyx(stdscr, screen_rows, screen_cols);
  erase();
  Buffer *b = cur_buffer();
  for (int r = 0; r < screen_rows - 2; ++r) {
    size_t lineno = view_row + r;
    move(r, 0);
    clrtoeol();
    if (lineno < b->nlines) {
      char *s = b->lines[lineno].data;
      size_t len = b->lines[lineno].len;
      size_t start = view_col < len ? view_col : len;
      size_t n = len - start;
      if ((int)n > screen_cols) n = screen_cols;
      if (n > 0) addnstr(s + start, (int)n);
    } else {
      if (b->nlines == 0 && r == (screen_rows - 2) / 2) {
	const char *w = "omega-vim-lite (mini) -- press i to insert, :q to quit";
	mvaddnstr(r, (screen_cols - (int)strlen(w)) / 2, w, screen_cols);
      }
    }
  }
  attron(A_REVERSE);
  move(screen_rows - 2, 0);
  clrtoeol();
  const char *mname = (mode == MODE_INSERT) ? "-- INSERT --" : (mode == MODE_VISUAL) ? "-- VISUAL --" : (mode == MODE_COMMAND) ? "-- COMMAND --" : "-- NORMAL --";
  char fname[128] = "[No Name]";
  if (b->filename) snprintf(fname, sizeof(fname), "%s%s", b->filename, b->modified ? " [+]" : "");
  char st[512];
  snprintf(st, sizeof(st), "%s  %s  Ln %zu, Col %zu  %s", mname, fname, cy + 1, cx + 1, status);
  mvaddnstr(screen_rows - 2, 0, st, screen_cols);
  attroff(A_REVERSE);
  move(screen_rows - 1, 0); clrtoeol();
  int cursr = (int)(cy - view_row);
  int cursc = (int)(cx - view_col);
  if (cursr >= 0 && cursr < screen_rows - 2 && cursc >= 0 && cursc < screen_cols) {
    move(cursr, cursc); curs_set(1);
  } else { move(screen_rows - 2, 0); curs_set(0); }
  refresh();
}

/* Commands */
static void open_file_cmd(const char *arg) {
  Buffer *b = buffer_new(arg);
  if (!b) { set_statusf("Too many buffers"); return; }
  if (buffer_load(b, arg) != 0) {
    set_statusf("Could not open %s", arg);
    buffer_free(b); buf_count--; return;
  }
  curbuf = buf_count - 1;
  cy = cx = view_row = view_col = 0;
  set_statusf("Opened %s", arg);
}
static void save_file_cmd(const char *arg) {
  Buffer *b = cur_buffer();
  const char *fname = (arg && arg[0]) ? arg : (b->filename ? b->filename : NULL);
  if (!fname) { set_statusf("No file name"); return; }
  if (buffer_write(b, fname) != 0) set_statusf("Error writing %s: %s", fname, strerror(errno));
  else set_statusf("Wrote %s", fname);
}
static void do_substitute_current_line(const char *pat, const char *repl, int global) {
  Buffer *b = cur_buffer();
  if (cy >= b->nlines) return;
  Line *L = &b->lines[cy];
  char *out = malloc(L->len * 2 + 32);
  if (!out) die("malloc");
  out[0] = '\0';
  const char *p = L->data;
  int replaced = 0;
  while (*p) {
    const char *f = strstr(p, pat);
    if (!f) { strcat(out, p); break; }
    strncat(out, p, (size_t)(f - p));
    strcat(out, repl);
    replaced++;
    p = f + strlen(pat);
    if (!global) { strcat(out, p); break; }
  }
  if (replaced) {
    record_and_delete_range(b, cy, 0, cy + 1, 0);
    record_and_insert(b, cy, 0, out);
    set_statusf("Replaced %d occurrences", replaced);
  } else set_statusf("No match");
  free(out);
}
static int process_command(const char *cmdline) {
  if (!cmdline) return 0;
  if (cmdline[0] == '\0') return 0;
  if (strcmp(cmdline, "q") == 0) {
    if (cur_buffer()->modified) { set_statusf("No write since last change (use :q! to force)"); return 0; }
    return 1;
  } else if (strcmp(cmdline, "q!") == 0) return 1;
  else if (strncmp(cmdline, "w ", 2) == 0) { save_file_cmd(cmdline + 2); }
  else if (strcmp(cmdline, "w") == 0) { save_file_cmd(NULL); }
  else if (strncmp(cmdline, "e ", 2) == 0) { open_file_cmd(cmdline + 2); }
  else if (strcmp(cmdline, "buffers") == 0) { set_statusf("Buffers: %d", buf_count); }
  else if (strncmp(cmdline, "b ", 2) == 0) {
    int n = atoi(cmdline + 2);
    if (n < 1 || n > buf_count) set_statusf("Invalid buffer");
    else { curbuf = n - 1; cy = cx = view_row = view_col = 0; set_statusf("Switched to buffer %d", n); }
  } else if (strncmp(cmdline, "s/", 2) == 0) {
    const char *p = cmdline + 2;
    const char *next = strchr(p, '/');
    if (!next) { set_statusf("Bad substitute"); return 0; }
    char *pat = strndup(p, (size_t)(next - p));
    p = next + 1; next = strchr(p, '/');
    if (!next) { free(pat); set_statusf("Bad substitute"); return 0; }
    char *repl = strndup(p, (size_t)(next - p));
    p = next + 1;
    int global = (strchr(p, 'g') != NULL);
    do_substitute_current_line(pat, repl, global);
    free(pat); free(repl);
  } else {
    set_statusf("Unknown command: %s", cmdline);
  }
  return 0;
}

/* Input helpers */
static void cmdline_prompt(char *out, size_t outlen) {
  echo(); curs_set(1);
  move(screen_rows - 1, 0); clrtoeol(); addch(':'); refresh();
  wgetnstr(stdscr, out, (int)outlen - 1);
  noecho(); curs_set(0);
}

/* Forward declarations for handlers */
static void normal_handle(int ch);
static void insert_handle(int ch);
static void visual_handle(int ch);

/* Normal mode handler */
static void normal_handle(int ch) {
  static char prefix[32] = "";
  if (isdigit((unsigned char)ch)) {
    size_t l = strlen(prefix);
    if (l < sizeof(prefix) - 1) { prefix[l] = ch; prefix[l + 1] = '\0'; }
    return;
  }
  int count = 1;
  if (strlen(prefix)) { count = atoi(prefix); prefix[0] = '\0'; }
  Buffer *b = cur_buffer();
  switch (ch) {
  case 'h': if (cx > 0) cx--; break;
  case 'l': if (cx < line_len(b, cy)) cx++; break;
  case 'j': cy += count; break;
  case 'k': if ((int)cy - count >= 0) cy -= count; else cy = 0; break;
  case '0': cx = 0; break;
  case '$': cx = line_len(b, cy); break;
  case 'w': { char *line = b->lines[cy].data; size_t i = cx; while (line[i] && !isspace((unsigned char)line[i])) i++; while (line[i] && isspace((unsigned char)line[i])) i++; cx = i; } break;
  case 'b': { char *line = b->lines[cy].data; size_t i = cx; if (i > 0) i--; while (i > 0 && isspace((unsigned char)line[i])) i--; while (i > 0 && !isspace((unsigned char)line[i-1])) i--; cx = i; } break;
  case 'G': cy = b->nlines ? b->nlines - 1 : 0; break;
  case 'g': { int ch2 = getch(); if (ch2 == 'g') cy = 0; else ungetch(ch2); } break;
  case 'i': mode = MODE_INSERT; break;
  case 'I': cx = 0; mode = MODE_INSERT; break;
  case 'a': if (cx < line_len(b, cy)) cx++; mode = MODE_INSERT; break;
  case 'A': cx = line_len(b, cy); mode = MODE_INSERT; break;
  case 'o': record_and_insert(b, cy + 1, 0, "\n"); cy++; cx = 0; mode = MODE_INSERT; break;
  case 'O': record_and_insert(b, cy, 0, "\n"); mode = MODE_INSERT; break;
  case 'x': if (cx < line_len(b, cy)) { record_and_delete_range(b, cy, cx, cy, cx + 1); } break;
  case 'd': { int next = getch(); if (next == 'd') { record_and_delete_range(b, cy, 0, cy + 1, 0); if (cy >= b->nlines) cy = b->nlines ? b->nlines - 1 : 0; cx = 0; } else { ungetch(next); record_and_delete_range(b, cy, cx, cy, cx + 1); } } break;
  case 'y': { int nx = getch(); if (nx == 'y') { Line *L = &b->lines[cy]; free(clipboard); clipboard = malloc(L->len + 2); if (!clipboard) die("malloc"); memcpy(clipboard, L->data, L->len); clipboard[L->len] = '\n'; clipboard[L->len+1] = '\0'; set_statusf("Yanked line"); } else { ungetch(nx); set_statusf("y?"); } } break;
  case 'p': if (clipboard) { record_and_insert(b, cy + 1, 0, clipboard); set_statusf("Pasted"); } break;
  case 'u': do_undo(); break;
  case 18: do_redo(); break; /* Ctrl-R */
  case '/': { char pat[256] = ""; echo(); curs_set(1); move(screen_rows - 1, 0); clrtoeol(); addch('/'); refresh(); wgetnstr(stdscr, pat, (int)sizeof(pat)-1); noecho(); curs_set(0); search_forward(pat); } break;
  case 'n': set_statusf("n (no persistent pattern)"); break;
  case ':': { char cmd[512] = ""; mode = MODE_COMMAND; cmdline_prompt(cmd, sizeof(cmd)); int quit = process_command(cmd); mode = MODE_NORMAL; if (quit) { endwin(); exit(0); } } break;
  case 27: break;
  case 'v': mode = MODE_VISUAL; visual_srow = cy; visual_scol = cx; visual_linewise = 0; break;
  case 'V': mode = MODE_VISUAL; visual_srow = cy; visual_scol = 0; visual_linewise = 1; break;
  default: break;
  }
  clamp_cursor();
}

/* Insert mode handler */
static void insert_handle(int ch) {
  Buffer *b = cur_buffer();
  if (ch == 27) { mode = MODE_NORMAL; return; }
  if (ch == KEY_BACKSPACE || ch == 127) {
    if (cx > 0) { record_and_delete_range(b, cy, cx - 1, cy, cx); cx--; }
    else if (cy > 0) {
      size_t prevlen = b->lines[cy - 1].len;
      record_and_delete_range(b, cy - 1, prevlen, cy, 0);
      cy--; cx = prevlen;
    }
    return;
  }
  if (ch == '\n' || ch == '\r') {
    Line *L = &b->lines[cy];
    char *remain = strdup(L->data + cx);
    if (!remain) die("malloc");
    record_and_delete_range(b, cy, cx, cy + 1, 0);
    record_and_insert(b, cy + 1, 0, remain);
    cy++; cx = 0;
    free(remain);
    return;
  }
  if (ch >= 32 && ch < 256) {
    char s[2] = { (char)ch, '\0' };
    record_and_insert(b, cy, cx, s);
    cx++;
  }
  clamp_cursor();
}

/* Visual mode handler */
static void visual_handle(int ch) {
  Buffer *b = cur_buffer();
  if (ch == 27) { mode = MODE_NORMAL; return; }
  if (ch == 'h' || ch == KEY_LEFT) { if (cx > 0) cx--; }
  else if (ch == 'l' || ch == KEY_RIGHT) { if (cx < line_len(b, cy)) cx++; }
  else if (ch == 'j' || ch == KEY_DOWN) { if (cy + 1 < b->nlines) cy++; }
  else if (ch == 'k' || ch == KEY_UP) { if (cy > 0) cy--; }
  else if (ch == 'y') {
    size_t srow = visual_srow, scol = visual_scol, erow = cy, ecol = cx;
    if (srow > erow || (srow == erow && scol > ecol)) { size_t t; t = srow; srow = erow; erow = t; t = scol; scol = ecol; ecol = t; }
    if (visual_linewise) {
      size_t len = 0;
      for (size_t r = srow; r <= erow && r < b->nlines; ++r) len += b->lines[r].len + 1;
      char *acc = malloc(len + 1);
      if (!acc) die("malloc");
      size_t p = 0;
      for (size_t r = srow; r <= erow && r < b->nlines; ++r) {
	if (b->lines[r].len) memcpy(acc + p, b->lines[r].data, b->lines[r].len);
                p += b->lines[r

			      ```c
			      p += b->lines[r].len;
			      acc[p++] = '\n';
			      }
		  acc[p] = '\0';
		free(clipboard);
		clipboard = acc;
		set_statusf("Yanked");
		mode = MODE_NORMAL;
		clamp_cursor();
		return;
      } else if (ch == 'd') {
        size_t srow = visual_srow, scol = visual_scol, erow = cy, ecol = cx;
        if (srow > erow || (srow == erow && scol > ecol)) { size_t t; t = srow; srow = erow; erow = t; t = scol; scol = ecol; ecol = t; }
        if (visual_linewise) {
	  /* collect deleted lines into clipboard (linewise) */
	  size_t len = 0;
	  for (size_t r = srow; r <= erow && r < b->nlines; ++r) len += b->lines[r].len + 1;
	  char *acc = malloc(len + 1);
	  if (!acc) die("malloc");
	  size_t p = 0;
	  for (size_t r = srow; r <= erow && r < b->nlines; ++r) {
	    if (b->lines[r].len) memcpy(acc + p, b->lines[r].data, b->lines[r].len);
	    p += b->lines[r].len;
	    acc[p++] = '\n';
	  }
	  acc[p] = '\0';
	  record_and_delete_range(b, srow, 0, erow + 1, 0);
	  free(clipboard); clipboard = acc;
        } else {
	  /* extract deleted text then delete */
	  /* build full buffer string */
	  size_t total = 0;
	  for (size_t i = 0; i < b->nlines; ++i) total += b->lines[i].len + 1;
	  char *all = malloc(total + 1);
	  if (!all) die("malloc");
	  size_t pp = 0;
	  for (size_t i = 0; i < b->nlines; ++i) {
	    if (b->lines[i].len) memcpy(all + pp, b->lines[i].data, b->lines[i].len);
	    pp += b->lines[i].len;
	    all[pp++] = '\n';
	  }
	  all[pp] = '\0';
	  /* compute abs positions */
	  size_t abs_s = 0, abs_e = 0;
	  if (srow >= b->nlines) abs_s = total;
	  else {
	    for (size_t i = 0; i < srow; ++i) abs_s += b->lines[i].len + 1;
	    abs_s += scol;
	  }
	  if (erow >= b->nlines) abs_e = total;
	  else {
	    for (size_t i = 0; i < erow; ++i) abs_e += b->lines[i].len + 1;
	    abs_e += ecol;
	  }
	  if (abs_s > total) abs_s = total;
	  if (abs_e > total) abs_e = total;
	  if (abs_s >= abs_e) {
	    free(all);
	    free(clipboard); clipboard = strdup("");
	  } else {
	    size_t dlen = abs_e - abs_s;
	    char *acc = malloc(dlen + 1);
	    if (!acc) die("malloc");
	    memcpy(acc, all + abs_s, dlen);
	    acc[dlen] = '\0';
	    free(clipboard); clipboard = acc;
	    free(all);
	  }
	  /* now delete via record (which rebuilds buffer and records undo) */
	  record_and_delete_range(b, srow, scol, erow, ecol);
        }
        set_statusf("Deleted");
        mode = MODE_NORMAL;
        clamp_cursor();
        return;
      } else if (ch == 'p') {
        if (clipboard) {
	  record_and_insert(b, cy + 1, 0, clipboard);
	  set_statusf("Pasted");
        }
        mode = MODE_NORMAL;
        clamp_cursor();
        return;
      } else {
        /* other motion keys handled above; stay visual */
      }
      clamp_cursor();
    }

    /* Main entry */
    int main(int argc, char **argv) {
      setlocale(LC_ALL, "");
      /* create initial buffer */
      Buffer *b = buffer_new(NULL);
      if (!b) die("Failed to create initial buffer");
      if (argc >= 2) {
        free(b->filename);
        b->filename = strdup(argv[1]);
        if (buffer_load(b, argv[1]) != 0) {
	  /* cannot open: start empty buffer with filename */
	  buffer_free(b);
	  b = buffer_new(argv[1]);
	  if (!b) die("Failed to create buffer for %s", argv[1]);
	  buffer_ensure(b, 1);
	  b->lines[b->nlines++] = mkline_from_cstr("");
        }
      } else {
        buffer_ensure(b, 1);
        b->lines[b->nlines++] = mkline_from_cstr("");
      }
      curbuf = 0;
      cx = cy = view_row = view_col = 0;
      set_statusf("Welcome to omega-vim-lite");

      /* init curses */
      initscr();
      raw();
      noecho();
      keypad(stdscr, TRUE);
      getmaxyx(stdscr, screen_rows, screen_cols);
      curs_set(1);

      /* init undo stacks */
      undo_init(&undo_stack);
      undo_init(&redo_stack);

      /* main loop */
      while (1) {
        clamp_cursor();
        draw_screen();
        int ch = getch();
        if (mode == MODE_NORMAL) normal_handle(ch);
        else if (mode == MODE_INSERT) insert_handle(ch);
        else if (mode == MODE_VISUAL) visual_handle(ch);
        else mode = MODE_NORMAL;
      }

      /* cleanup (unreachable normally) */
      endwin();
      for (int i = 0; i < buf_count; ++i) buffer_free(&buffers[i]);
      if (undo_stack.arr) {
        for (size_t i = 0; i < undo_stack.top; ++i) free_editop(&undo_stack.arr[i]);
        free(undo_stack.arr);
      }
      if (redo_stack.arr) {
        for (size_t i = 0; i < redo_stack.top; ++i) free_editop(&redo_stack.arr[i]);
        free(redo_stack.arr);
      }
      free(clipboard);
      return 0;
    }
```
