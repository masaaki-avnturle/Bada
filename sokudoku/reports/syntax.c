以下は、要求どおり生成した Vim/Emacs設定をユーザーのホーム配下へ「追記（追加書き込み）」でき、さらにホームの `~/.vimrc` と `~/.emacs`（存在する場合は追記、無ければ作成）へも必要な設定行を追記するようにした `pkginstallgen.c` の完全なソースです。

使い方
- ビルド:
  gcc -O2 -std=c11 -Wall -Wextra -o pkginstallgen pkginstallgen.c
    - 実行（カレントにパッケージを作る）:
  ./pkginstallgen
    - インストール（ホーム配下へ追記インストール、かつ ~/.vimrc と ~/.emacs に設定追記）:
  ./pkginstallgen --install

注意
- 既存ファイルへは追記のみ行います（上書きはしません）。
- 重複追記を避けたい場合はさらに検査ロジックを追加できます（必要なら対応可能）。

    保存ファイル: pkginstallgen.c

  ソースコード:

```c
  /*
   * pkginstallgen.c
   *
   * Generate Omega Script editor files for Vim and Emacs and optionally install to user home.
   * When installing, existing files are appended to (not overwritten). Also appends helper lines
   * into ~/.vimrc and ~/.emacs to load the installed files.
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -Wextra -o pkginstallgen pkginstallgen.c
   *
   * Run:
   *   ./pkginstallgen
   *   ./pkginstallgen --install
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

  static int write_file(const char *path, const char *data, int make_exec) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    size_t L = strlen(data);
    if (L && fwrite(data,1,L,f) != L) { fclose(f); return -1; }
    fclose(f);
    if (make_exec) chmod(path, 0755);
    return 0;
  }

static int append_string_to_file(const char *path, const char *data, int make_exec) {
  FILE *f = fopen(path, "ab");
  if (!f) return -1;
  size_t L = strlen(data);
  if (L && fwrite(data,1,L,f) != L) { fclose(f); return -1; }
  fclose(f);
  if (make_exec) chmod(path, 0644);
  return 0;
}

static int append_file_to_file(const char *src, const char *dst) {
  FILE *fs = fopen(src, "rb");
  if (!fs) return -1;
  FILE *fd = fopen(dst, "ab");
  if (!fd) { fclose(fs); return -1; }
  char buf[4096];
  size_t r;
  while ((r = fread(buf,1,sizeof(buf),fs)) > 0) {
    if (fwrite(buf,1,r,fd) != r) { fclose(fs); fclose(fd); return -1; }
  }
  fclose(fs); fclose(fd);
  return 0;
}

/* Vim and Emacs content strings (trimmed to essentials) */
static const char *vim_syntax =
"\" omega.vim - Omega Script syntax\n"
  "if exists(\"b:current_syntax\")\n  finish\nendif\nlet s:omega_keywords = ['function','var','let','const','if','else','for','while','return','import','from','as','break','continue','true','false','nil','and','or','not','switch','case','default']\nexecute 'syntax keyword omegaKeyword ' . join(s:omega_keywords)\nhi def link omegaKeyword Keyword\nlet b:current_syntax = \"omega\"\n";

static const char *vim_ftplugin =
  "\" omega ftplugin\nsetlocal tabstop=4 shiftwidth=4 softtabstop=4 expandtab autoindent\nsetlocal omnifunc=omega#Complete\nnnoremap <buffer> <leader>r :w<CR>:!omega-run %<CR>\n";

static const char *vim_indent =
  "\" omega indent\nfunction! GetOmegaIndent()\n  let lnum = prevnonblank(v:lnum - 1)\n  if lnum == 0\n    return 0\n  endif\n  let line = getline(lnum)\n  let indent = indent(lnum)\n  if line =~ '{\\s*$' || line =~ '\\v\\<(function|if|for|while|switch)\\>.*'\n    return indent + &shiftwidth\n  endif\n  if getline(v:lnum) =~ '^\\s*}'\n    return max([0, indent - &shiftwidth])\n  endif\n  return indent\nendfunction\nsetlocal indentexpr=GetOmegaIndent()\n";

static const char *vim_autoload =
  "\" omega_complete omnifunc\nfunction! omega#Complete(findstart, base) abort\n  if a:findstart\n    let line = getline('.')\n    let col = col('.') - 1\n    while col > 0 && line[col - 1] =~ '\\k'\n      let col -= 1\n    endwhile\n    return col\n  else\n    let res = ['function','var','let','const','if','else','for','while','return']\n    return res\n  endif\nendfunction\n";

static const char *emacs_mode =
  ";; omega-mode.el minimal\n(require 'cl-lib)\n(defvar omega-reserved-words '(\"function\" \"var\" \"let\" \"const\" \"if\" \"else\" \"for\" \"while\" \"return\"))\n(defvar omega-font-lock-keywords `((,(regexp-opt omega-reserved-words 'words) . font-lock-keyword-face)))\n(define-derived-mode omega-mode prog-mode \"Omega\"\n  \"Major mode for Omega Script\"\n  (setq-local font-lock-defaults '(omega-font-lock-keywords))\n  (setq-local comment-start \"// \"))\n(add-to-list 'auto-mode-alist '(\"\\\\.omega\\\\'\" . omega-mode))\n(provide 'omega-mode)\n";

int main(int argc, char **argv) {
  const char *root = "omega_editor_pkg";
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "failed to create '%s'\n", root); return 1; }
  snprintf(path, sizeof(path), "%s/%s", root, "vim/syntax"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "vim/ftplugin"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "vim/indent"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "vim/autoload"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "emacs"); ensure_dir(path);

  /* write package files */
  snprintf(path, sizeof(path), "%s/vim/syntax/omega.vim", root);
  if (write_file(path, vim_syntax, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/vim/ftplugin/omega.vim", root);
  if (write_file(path, vim_ftplugin, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/vim/indent/omega.vim", root);
  if (write_file(path, vim_indent, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/vim/autoload/omega_complete.vim", root);
  if (write_file(path, vim_autoload, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/emacs/omega-mode.el", root);
  if (write_file(path, emacs_mode, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  printf("Generated package '%s'.\n", root);

  if (argc > 1 && strcmp(argv[1], "--install") == 0) {
    const char *home = getenv("HOME");
    if (!home) { fprintf(stderr, "HOME not set; cannot install\n"); return 1; }

    char vim_syntax_dir[1024], vim_ftplugin_dir[1024], vim_indent_dir[1024], vim_autoload_dir[1024];
    snprintf(vim_syntax_dir, sizeof(vim_syntax_dir), "%s/.vim/syntax", home);
    snprintf(vim_ftplugin_dir, sizeof(vim_ftplugin_dir), "%s/.vim/ftplugin", home);
    snprintf(vim_indent_dir, sizeof(vim_indent_dir), "%s/.vim/indent", home);
    snprintf(vim_autoload_dir, sizeof(vim_autoload_dir), "%s/.vim/autoload", home);
    ensure_dir(vim_syntax_dir); ensure_dir(vim_ftplugin_dir); ensure_dir(vim_indent_dir); ensure_dir(vim_autoload_dir);

    char emacs_dir[1024];
    snprintf(emacs_dir, sizeof(emacs_dir), "%s/.emacs.d/lisp", home);
    ensure_dir(emacs_dir);

    char src[1024], dst[1024];

    /* append package files into user's vim/emacs files (create if missing) */
    snprintf(src, sizeof(src), "%s/vim/syntax/omega.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega.vim", vim_syntax_dir);
    if (append_file_to_file(src, dst) != 0) append_string_to_file(dst, vim_syntax, 0);

    snprintf(src, sizeof(src), "%s/vim/ftplugin/omega.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega.vim", vim_ftplugin_dir);
    if (append_file_to_file(src, dst) != 0) append_string_to_file(dst, vim_ftplugin, 0);

    snprintf(src, sizeof(src), "%s/vim/indent/omega.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega.vim", vim_indent_dir);
    if (append_file_to_file(src, dst) != 0) append_string_to_file(dst, vim_indent, 0);

    snprintf(src, sizeof(src), "%s/vim/autoload/omega_complete.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega_complete.vim", vim_autoload_dir);
    if (append_file_to_file(src, dst) != 0) append_string_to_file(dst, vim_autoload, 0);

    snprintf(src, sizeof(src), "%s/emacs/omega-mode.el", root);
    snprintf(dst, sizeof(dst), "%s/omega-mode.el", emacs_dir);
    if (append_file_to_file(src, dst) != 0) append_string_to_file(dst, emacs_mode, 0);

    /* Append helper lines into ~/.vimrc and ~/.emacs to load these files (idempotence not checked) */
    char vimrc[1024], emacsrc[1024];
    snprintf(vimrc, sizeof(vimrc), "%s/.vimrc", home);
    snprintf(emacsrc, sizeof(emacsrc), "%s/.emacs", home);

        const char *vimrc_add =
	  "\n\" Omega Script settings: load syntax/ftplugin/indent from user's .vim\nif filereadable(expand('~/.vim/syntax/omega.vim'))\n  autocmd! FileType omega setlocal omnifunc=omega#Complete\nendif\n";
        append_string_to_file(vimrc, vimrc_add, 0);

        const char *emacs_add =
	  "\n;; Omega mode load\n(when (file-exists-p \"~/.emacs.d/lisp/omega-mode.el\")\n  (add-to-list 'load-path \"~/.emacs.d/lisp\")\n  (require 'omega-mode))\n";
        append_string_to_file(emacsrc, emacs_add, 0);

        printf("Appended files into %s/.vim/... and %s/.emacs.d/lisp/, and updated %s and %s\n", home, home, vimrc, emacsrc);
  } else {
    printf("To install into your home directories (append mode), run: %s --install\n", argv[0]);
  }

  return 0;
}
```

必要なら、
- 追記の重複チェック（既に同じブロックがある場合はスキップ）を追加します。
- インストール先のパスをオプション化します。
ご希望があれば追記します。
