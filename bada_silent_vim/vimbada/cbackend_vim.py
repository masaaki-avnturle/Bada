"""C backend for the Bada vim: emit the *receiver* + *class-method* binaries.

The Bada vim (``lib/vim.bada``) edits a buffer by sending class-method messages
(insert / delete / newline / open-line / delete-line / show) to a line buffer.
This backend mirrors those class methods as **real C executables**:

* a tiny shared runtime ``bufrt.c`` — load / save / edit a line buffer file,
* one **class-method** executable per editing message (``vim_insert`` …), and
* a **receiver** executable ``bada_vim`` that takes a method name and dispatches
  the message to the matching class-method binary (``execv``).

Together with the reserved-word binaries produced by ``cbackend/gen.py`` these
are the "Cで作った実行形式ファイル … 予約語、クラスメソッド、レシーバーの
バイナリーファイル" — Bada's editor expressed as compiled executables.
"""

from __future__ import annotations

import os
import subprocess

# class-method messages the receiver dispatches (mirrors vim.bada)
METHODS = [
    "vim_insert",      # insert text into a line at a column
    "vim_delete",      # delete the char at a column
    "vim_newline",     # split a line at a column (RET in insert mode)
    "vim_appendline",  # open an empty line below (o)
    "vim_deleteline",  # delete a whole line (dd)
    "vim_show",        # print the buffer
]

BUFRT_H = """\
#ifndef BADA_BUFRT_H
#define BADA_BUFRT_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUF_MAXLINES 1000000

typedef struct { char **line; int n; } Buf;

void buf_load(Buf *b, const char *path);
void buf_save(const Buf *b, const char *path);
void buf_show(const Buf *b);
void buf_insert(Buf *b, int row, int col, const char *text);
void buf_delete(Buf *b, int row, int col);
void buf_newline(Buf *b, int row, int col);
void buf_appendline(Buf *b, int row);
void buf_deleteline(Buf *b, int row);
#endif
"""

BUFRT_C = """\
#include "bufrt.h"

static char *ba_dup(const char *s) {
  char *p = malloc(strlen(s) + 1);
  if (!p) { perror("malloc"); exit(1); }
  strcpy(p, s);
  return p;
}

static void buf_set(Buf *b, int row, char *s) {
  free(b->line[row]);
  b->line[row] = s;
}

static int clampi(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

void buf_load(Buf *b, const char *path) {
  b->line = calloc(BUF_MAXLINES, sizeof(char *));
  if (!b->line) { perror("calloc"); exit(1); }
  b->n = 0;
  FILE *f = fopen(path, "rb");
  if (!f) { b->line[0] = ba_dup(""); b->n = 1; return; }
  char *ln = NULL; size_t cap = 0; ssize_t got;
  while ((got = getline(&ln, &cap, f)) != -1) {
    if (got > 0 && ln[got - 1] == '\\n') ln[got - 1] = '\\0';
    if (b->n < BUF_MAXLINES) b->line[b->n++] = ba_dup(ln);
  }
  free(ln);
  fclose(f);
  if (b->n == 0) { b->line[0] = ba_dup(""); b->n = 1; }
}

void buf_save(const Buf *b, const char *path) {
  FILE *f = fopen(path, "wb");
  if (!f) { perror("fopen"); exit(1); }
  for (int i = 0; i < b->n; i++) fprintf(f, "%s\\n", b->line[i]);
  fclose(f);
}

void buf_show(const Buf *b) {
  for (int i = 0; i < b->n; i++) {
    fputs(b->line[i], stdout);
    if (i + 1 < b->n) fputc('\\n', stdout);
  }
  fputc('\\n', stdout);
}

void buf_insert(Buf *b, int row, int col, const char *text) {
  row = clampi(row, 0, b->n - 1);
  const char *s = b->line[row];
  int slen = (int)strlen(s);
  col = clampi(col, 0, slen);
  int tlen = (int)strlen(text);
  char *out = malloc(slen + tlen + 1);
  if (!out) { perror("malloc"); exit(1); }
  memcpy(out, s, col);
  memcpy(out + col, text, tlen);
  memcpy(out + col + tlen, s + col, slen - col);
  out[slen + tlen] = '\\0';
  buf_set(b, row, out);
}

void buf_delete(Buf *b, int row, int col) {
  row = clampi(row, 0, b->n - 1);
  const char *s = b->line[row];
  int slen = (int)strlen(s);
  if (col < 0 || col >= slen) return;
  char *out = malloc(slen);
  if (!out) { perror("malloc"); exit(1); }
  memcpy(out, s, col);
  memcpy(out + col, s + col + 1, slen - col - 1);
  out[slen - 1] = '\\0';
  buf_set(b, row, out);
}

static void buf_insert_line(Buf *b, int at, char *s) {
  if (b->n >= BUF_MAXLINES) { free(s); return; }
  for (int i = b->n; i > at; i--) b->line[i] = b->line[i - 1];
  b->line[at] = s;
  b->n++;
}

void buf_newline(Buf *b, int row, int col) {
  row = clampi(row, 0, b->n - 1);
  const char *s = b->line[row];
  int slen = (int)strlen(s);
  col = clampi(col, 0, slen);
  char *left = malloc(col + 1);
  char *right = ba_dup(s + col);
  if (!left) { perror("malloc"); exit(1); }
  memcpy(left, s, col);
  left[col] = '\\0';
  buf_set(b, row, left);
  buf_insert_line(b, row + 1, right);
}

void buf_appendline(Buf *b, int row) {
  row = clampi(row, 0, b->n - 1);
  buf_insert_line(b, row + 1, ba_dup(""));
}

void buf_deleteline(Buf *b, int row) {
  row = clampi(row, 0, b->n - 1);
  free(b->line[row]);
  for (int i = row; i + 1 < b->n; i++) b->line[i] = b->line[i + 1];
  b->n--;
  if (b->n == 0) { b->line[0] = ba_dup(""); b->n = 1; }
}
"""

# class-method bodies: (argc check, call). argv[1] is always the buffer file.
_METHOD_BODY = {
    "vim_insert": (
        5, "<buf> <row> <col> <text>",
        "buf_insert(&b, atoi(argv[2]), atoi(argv[3]), argv[4]);\n"
        "  buf_save(&b, argv[1]);\n"),
    "vim_delete": (
        4, "<buf> <row> <col>",
        "buf_delete(&b, atoi(argv[2]), atoi(argv[3]));\n"
        "  buf_save(&b, argv[1]);\n"),
    "vim_newline": (
        4, "<buf> <row> <col>",
        "buf_newline(&b, atoi(argv[2]), atoi(argv[3]));\n"
        "  buf_save(&b, argv[1]);\n"),
    "vim_appendline": (
        3, "<buf> <row>",
        "buf_appendline(&b, atoi(argv[2]));\n"
        "  buf_save(&b, argv[1]);\n"),
    "vim_deleteline": (
        3, "<buf> <row>",
        "buf_deleteline(&b, atoi(argv[2]));\n"
        "  buf_save(&b, argv[1]);\n"),
    "vim_show": (
        2, "<buf>",
        "buf_show(&b);\n"),
}


def _method_source(name: str) -> str:
    argc, usage, call = _METHOD_BODY[name]
    return (
        f"/* {name}.c -- Bada vim class method: {name} */\n"
        '#include "bufrt.h"\n'
        "int main(int argc, char **argv) {\n"
        f"  if (argc < {argc}) {{\n"
        f'    fprintf(stderr, "usage: {name} {usage}\\n");\n'
        "    return 1;\n  }\n"
        "  Buf b;\n"
        "  buf_load(&b, argv[1]);\n"
        f"  {call}"
        "  return 0;\n}\n")


def _receiver_source() -> str:
    methods = " ".join(METHODS)
    return (
        '/* bada_vim.c -- Bada vim *receiver*: dispatch a class-method message\n'
        '   to the matching class-method binary (in the receiver\'s own dir). */\n'
        "#include <stdio.h>\n"
        "#include <stdlib.h>\n"
        "#include <string.h>\n"
        "#include <unistd.h>\n"
        "#include <libgen.h>\n\n"
        "static const char *METHODS[] = {\n"
        + "".join(f'  "{m}",\n' for m in METHODS)
        + "  0\n};\n\n"
        "static int known(const char *m) {\n"
        "  for (int i = 0; METHODS[i]; i++)\n"
        "    if (strcmp(METHODS[i], m) == 0) return 1;\n"
        "  return 0;\n}\n\n"
        "/* directory holding this receiver executable */\n"
        "static void self_dir(char *out, size_t cap, const char *argv0) {\n"
        "  char buf[4096];\n"
        "  ssize_t n = readlink(\"/proc/self/exe\", buf, sizeof(buf) - 1);\n"
        "  if (n > 0) { buf[n] = '\\0'; }\n"
        "  else { strncpy(buf, argv0, sizeof(buf) - 1); buf[sizeof(buf)-1]=0; }\n"
        "  char *d = dirname(buf);\n"
        "  strncpy(out, d, cap - 1); out[cap - 1] = '\\0';\n"
        "}\n\n"
        "int main(int argc, char **argv) {\n"
        '  if (argc < 3) {\n'
        '    fprintf(stderr, "usage: bada_vim <buf> <method> [args...]\\n");\n'
        f'    fprintf(stderr, "methods: {methods}\\n");\n'
        "    return 2;\n  }\n"
        "  const char *buf = argv[1];\n"
        "  const char *method = argv[2];\n"
        "  if (!known(method)) {\n"
        '    fprintf(stderr, "bada_vim: unknown method: %s\\n", method);\n'
        "    return 2;\n  }\n"
        "  char dir[4096];\n"
        "  self_dir(dir, sizeof(dir), argv[0]);\n"
        "  char path[8192];\n"
        '  snprintf(path, sizeof(path), "%s/%s", dir, method);\n'
        "  /* method binary argv: <method> <buf> [extra args from argv[3..]] */\n"
        "  char **margv = calloc(argc, sizeof(char *));\n"
        "  if (!margv) { perror(\"calloc\"); return 1; }\n"
        "  int k = 0;\n"
        "  margv[k++] = (char *)method;\n"
        "  margv[k++] = (char *)buf;\n"
        "  for (int i = 3; i < argc; i++) margv[k++] = argv[i];\n"
        "  margv[k] = 0;\n"
        "  execv(path, margv);\n"
        '  perror("execv");\n'
        "  return 1;\n}\n")


def _makefile() -> str:
    methods = " ".join(f"bin/{m}" for m in METHODS)
    return (
        "CC ?= cc\n"
        "CFLAGS ?= -O2 -Wall\n"
        f"METHODS = {methods}\n"
        "RECEIVER = bin/bada_vim\n\n"
        "all: $(METHODS) $(RECEIVER)\n\n"
        "bin/%: %.c bufrt.c bufrt.h\n"
        "\t@mkdir -p bin\n"
        "\t$(CC) $(CFLAGS) -o $@ $< bufrt.c\n\n"
        "$(RECEIVER): bada_vim.c\n"
        "\t@mkdir -p bin\n"
        "\t$(CC) $(CFLAGS) -o $@ bada_vim.c\n\n"
        "clean:\n"
        "\trm -rf bin\n")


def generate(out_dir: str) -> dict:
    """Write the runtime, class-method sources, receiver source and Makefile."""
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "bufrt.h"), "w") as f:
        f.write(BUFRT_H)
    with open(os.path.join(out_dir, "bufrt.c"), "w") as f:
        f.write(BUFRT_C)
    for name in METHODS:
        with open(os.path.join(out_dir, f"{name}.c"), "w") as f:
            f.write(_method_source(name))
    with open(os.path.join(out_dir, "bada_vim.c"), "w") as f:
        f.write(_receiver_source())
    with open(os.path.join(out_dir, "Makefile"), "w") as f:
        f.write(_makefile())
    return {"methods": list(METHODS), "receiver": "bada_vim"}


def build(out_dir: str) -> list[str]:
    """Compile everything with make; return the names of the built binaries."""
    subprocess.run(["make", "-s"], cwd=out_dir, check=True,
                   capture_output=True, text=True)
    bindir = os.path.join(out_dir, "bin")
    return sorted(os.listdir(bindir)) if os.path.isdir(bindir) else []


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        prog="bada-cbackend-vim",
        description="Generate C receiver + class-method binaries for the vim.")
    p.add_argument("--out", default="generated/vimbada")
    p.add_argument("--build", action="store_true", help="compile with make")
    args = p.parse_args(argv)
    info = generate(args.out)
    print(f"generated {len(info['methods'])} class methods + receiver "
          f"'{info['receiver']}' in {args.out}")
    if args.build:
        bins = build(args.out)
        print(f"built {len(bins)} executables in {args.out}/bin: "
              + " ".join(bins))


if __name__ == "__main__":
    main()
