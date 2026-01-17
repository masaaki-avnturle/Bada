```c
/*
 * pkginstallgen.c
 *
 * Generate Omega Script editor files for Vim and Emacs and optionally install to user home.
 * Adds completion support for common languages (C, Python, JavaScript) so Omega editor
 * can offer reserved-word completion for those languages as well.
 * Installation is idempotent (won't duplicate appended blocks).
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

static int write_file(const char *path, const char *data) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  size_t L = strlen(data);
  if (L && fwrite(data,1,L,f) != L) { fclose(f); return -1; }
  fclose(f);
  return 0;
}

static int append_string_to_file(const char *path, const char *data) {
  FILE *f = fopen(path, "ab");
  if (!f) return -1;
  size_t L = strlen(data);
  if (L && fwrite(data,1,L,f) != L) { fclose(f); return -1; }
  fclose(f);
  return 0;
}

static char *read_entire_file(const char *path) {
  FILE *f = fopen(path, "rb");
  if (!f) return NULL;
  if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
  long sz = ftell(f);
  if (sz < 0) { fclose(f); return NULL; }
  rewind(f);
  char *buf = malloc((size_t)sz + 1);
  if (!buf) { fclose(f); return NULL; }
  size_t r = fread(buf, 1, (size_t)sz, f);
  fclose(f);
  buf[r] = '\0';
  return buf;
}

static int file_contains_string(const char *path, const char *needle) {
  char *content = read_entire_file(path);
  if (!content) return 0;
  int found = strstr(content, needle) != NULL;
  free(content);
  return found;
}

static int append_file_if_missing(const char *dst, const char *src, const char *fallback_text, const char *sentinel) {
  if (sentinel && file_contains_string(dst, sentinel)) return 0;

  if (src) {
    char *src_content = read_entire_file(src);
    if (!src_content) {
      if (fallback_text) return append_string_to_file(dst, fallback_text);
      return -1;
    }
    int rc = append_string_to_file(dst, src_content);
    free(src_content);
    return rc;
  } else if (fallback_text) {
    return append_string_to_file(dst, fallback_text);
  }
  return -1;
}

/* Extended completion blocks that include common-language reserved words.
   Each block wrapped with sentinel markers for idempotence. */

/* Vim autoload: omega_complete provides completion lists for Omega plus C/Python/JS */
static const char *vim_autoload =
"\" >>> OMEGA-AUTOLOAD-BEGIN >>>\n"
"\" omega_complete omnifunc (Omega + common languages)\n"
"function! omega#Complete(findstart, base) abort\n"
"  if a:findstart\n"
"    let line = getline('.')\n" 
"    let col = col('.') - 1\n" 
"    while col > 0 && line[col - 1] =~ '\\k'\n" 
"      let col -= 1\n" 
"    endwhile\n" 
"    return col\n" 
"  else\n"
"    let res = []\n"
"    \" Omega reserved words\n"
"    let omega = ['function','var','let','const','if','else','for','while','return','import','from','as','break','continue','true','false','nil','and','or','not','switch','case','default']\n"
"    \" C keywords\n"
"    let c_kw = ['auto','break','case','char','const','continue','default','do','double','else','enum','extern','float','for','goto','if','inline','int','long','register','restrict','return','short','signed','sizeof','static','struct','switch','typedef','union','unsigned','void','volatile','while','_Alignas','_Alignof','_Atomic','_Bool','_Complex','_Generic','_Noreturn','_Static_assert','_Thread_local']\n"
"    \" Python keywords\n"
"    let py_kw = ['False','None','True','and','as','assert','async','await','break','class','continue','def','del','elif','else','except','finally','for','from','global','if','import','in','is','lambda','nonlocal','not','or','pass','raise','return','try','while','with','yield']\n"
"    \" JavaScript keywords\n"
"    let js_kw = ['break','case','catch','class','const','continue','debugger','default','delete','do','else','export','extends','finally','for','function','if','import','in','instanceof','let','new','return','super','switch','this','throw','try','typeof','var','void','while','with','yield']\n"
"    \" choose which sets to include based on filetype hint (if available)\n"
"    let ft = &filetype\n"
"    call extend(res, omega)\n"
"    if ft ==# 'c' || ft ==# 'cpp' || ft ==# 'h'\n" 
"      call extend(res, c_kw)\n"
"    endif\n"
"    if ft ==# 'python'\n"
"      call extend(res, py_kw)\n"
"    endif\n"
"    if ft ==# 'javascript' || ft ==# 'js'\n"
"      call extend(res, js_kw)\n"
"    endif\n"
"    \" also offer all lists as fallback\n"
"    call extend(res, c_kw)\n"
"    call extend(res, py_kw)\n"
"    call extend(res, js_kw)\n"
"    \" include simple buffer identifiers\n"
"    let idlist = []\n"
"    for lnum in range(1, line('$'))\n"
"      let s = getline(lnum)\n"
"      let start = 0\n"
"      let pat = '\\v([A-Za-z_][A-Za-z0-9_]*)'\n"
"      while 1\n" 
"        let m = matchstrpos(s, pat, start)\n" 
"        if m[0] == -1\n" 
"          break\n"
"        endif\n"
"        let tok = m[0]\n"
"        if tok =~ '^' . a:base && index(idlist, tok) < 0\n"
"          call add(idlist, tok)\n"
"        endif\n"
"        let start = m[1]\n"
"      endwhile\n"
"    endfor\n" 
"    call extend(res, idlist)\n"
"    call uniqsort(res)\n" 
"    return res\n"
"  endif\n"
"endfunction\n"
  "\" <<< OMEGA-AUTOLOAD-END <<<\n";

/* Vim syntax, ftplugin, indent and Emacs mode (concise). Other files include sentinel markers. */
static const char *vim_syntax =
"\" >>> OMEGA-SYNTAX-BEGIN >>>\n"
"let s:omega_keywords = ['function','var','let','const','if','else','for','while','return']\n"
"execute 'syntax keyword omegaKeyword ' . join(s:omega_keywords)\n" 
"hi def link omegaKeyword Keyword\n"
"let b:current_syntax = \"omega\"\n"
  "\" <<< OMEGA-SYNTAX-END <<<\n";

static const char *vim_ftplugin =
"\" >>> OMEGA-FTPLUGIN-BEGIN >>>\n"
"setlocal tabstop=4 shiftwidth=4 softtabstop=4 expandtab autoindent\n" 
"setlocal omnifunc=omega#Complete\n" 
  "\" <<< OMEGA-FTPLUGIN-END <<<\n";

static const char *vim_indent =
"\" >>> OMEGA-INDENT-BEGIN >>>\n"
"function! GetOmegaIndent()\n"
"  let lnum = prevnonblank(v:lnum - 1)\n"
"  if lnum == 0\n    return 0\n  endif\n"
  "  let line = getline(lnum)\n  let indent = indent(lnum)\n  if line =~ '{\\s*$' || line =~ '\\v\\<(function|if|for|while|switch)\\>.*'\n    return indent + &shiftwidth\n  endif\n  if getline(v:lnum) =~ '^\\s*}'\n    return max([0, indent - &shiftwidth])\n  endif\n  return indent\nendfunction\nsetlocal indentexpr=GetOmegaIndent()\n\" <<< OMEGA-INDENT-END <<<\n";

static const char *emacs_mode =
";; >>> OMEGA-EMACS-BEGIN >>>\n"
";; omega-mode with cross-language completion support\n"
"(require 'cl-lib)\n"
"(defvar omega-reserved-words '(\"function\" \"var\" \"let\" \"const\" \"if\" \"else\" \"for\" \"while\" \"return\"))\n"
"(defvar omega-c-words '(\"int\" \"char\" \"if\" \"else\" \"for\" \"while\" \"return\"))\n"
"(defvar omega-py-words '(\"def\" \"class\" \"if\" \"else\" \"for\" \"while\" \"return\"))\n"
"(defvar omega-js-words '(\"function\" \"var\" \"let\" \"const\" \"if\" \"else\" \"for\" \"while\"))\n"
"(defun omega-completion-at-point ()\n"
"  (let* ((bounds (bounds-of-thing-at-point 'symbol)) (start (car bounds)) (end (cdr bounds)))\n"
"    (when start\n"
"      (let ((prefix (buffer-substring-no-properties start end))\n"
"            (cands (cl-remove-duplicates (append omega-reserved-words omega-c-words omega-py-words omega-js-words) :test #'string=)))\n"
"        (list start end cands)))))\n"
"(define-derived-mode omega-mode prog-mode \"Omega\"\n"
"  (setq-local font-lock-defaults '( (cons (regexp-opt omega-reserved-words 'words) font-lock-keyword-face) ))\n"
"  (add-hook 'completion-at-point-functions #'omega-completion-at-point nil t))\n"
"(add-to-list 'auto-mode-alist '(\"\\\\.omega\\\\'\" . omega-mode))\n"
"(provide 'omega-mode)\n"
  ";; <<< OMEGA-EMACS-END <<<\n";

/* .vimrc and .emacs additions (idempotent blocks) */
static const char *vimrc_add =
  "\n\" >>> OMEGA-VIMRC-BEGIN >>>\n\" ensure our autoload available for omnifunc\nif filereadable(expand('~/.vim/autoload/omega_complete.vim'))\n  autocmd FileType omega,c,cpp,python,javascript setlocal omnifunc=omega#Complete\nendif\n\" <<< OMEGA-VIMRC-END <<<\n";

static const char *emacs_add =
  "\n;; >>> OMEGA-EMACSRC-BEGIN >>>\n(when (file-exists-p \"~/.emacs.d/lisp/omega-mode.el\")\n  (add-to-list 'load-path \"~/.emacs.d/lisp\")\n  (unless (featurep 'omega-mode) (require 'omega-mode)))\n;; <<< OMEGA-EMACSRC-END <<<\n";

int main(int argc, char **argv) {
  const char *root = "omega_editor_pkg";
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "failed to create '%s'\n", root); return 1; }
  snprintf(path, sizeof(path), "%s/%s", root, "vim/syntax"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "vim/ftplugin"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "vim/indent"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "vim/autoload"); ensure_dir(path);
  snprintf(path, sizeof(path), "%s/%s", root, "emacs"); ensure_dir(path);

  /* write package files (overwrite inside package) */
  snprintf(path, sizeof(path), "%s/vim/autoload/omega_complete.vim", root);
  if (write_file(path, vim_autoload) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/vim/syntax/omega.vim", root);
  if (write_file(path, vim_syntax) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/vim/ftplugin/omega.vim", root);
  if (write_file(path, vim_ftplugin) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/vim/indent/omega.vim", root);
  if (write_file(path, vim_indent) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/emacs/omega-mode.el", root);
  if (write_file(path, emacs_mode) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  printf("Generated package '%s' with cross-language completion support.\n", root);

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

    /* Append only if sentinel not present */
    snprintf(src, sizeof(src), "%s/vim/autoload/omega_complete.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega_complete.vim", vim_autoload_dir);
    if (append_file_if_missing(dst, src, vim_autoload, "OMEGA-AUTOLOAD-BEGIN") != 0)
      fprintf(stderr, "warning: could not append autoload to %s\n", dst);

    snprintf(src, sizeof(src), "%s/vim/syntax/omega.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega.vim", vim_syntax_dir);
    if (append_file_if_missing(dst, src, vim_syntax, "OMEGA-SYNTAX-BEGIN") != 0)
      fprintf(stderr, "warning: could not append syntax to %s\n", dst);

    snprintf(src, sizeof(src), "%s/vim/ftplugin/omega.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega.vim", vim_ftplugin_dir);
    if (append_file_if_missing(dst, src, vim_ftplugin, "OMEGA-FTPLUGIN-BEGIN") != 0)
      fprintf(stderr, "warning: could not append ftplugin to %s\n", dst);

    snprintf(src, sizeof(src), "%s/vim/indent/omega.vim", root);
    snprintf(dst, sizeof(dst), "%s/omega.vim", vim_indent_dir);
    if (append_file_if_missing(dst, src, vim_indent, "OMEGA-INDENT-BEGIN") != 0)
      fprintf(stderr, "warning: could not append indent to %s\n", dst);

    snprintf(src, sizeof(src), "%s/emacs/omega-mode.el", root);
    snprintf(dst, sizeof(dst), "%s/omega-mode.el", emacs_dir);
    if (append_file_if_missing(dst, src, emacs_mode, "OMEGA-EMACS-BEGIN") != 0)
      fprintf(stderr, "warning: could not append emacs mode to %s\n", dst);

    /* Update ~/.vimrc and ~/.emacs idempotently */
    char vimrc[1024], emacsrc[1024];
    snprintf(vimrc, sizeof(vimrc), "%s/.vimrc", home);
    snprintf(emacsrc, sizeof(emacsrc), "%s/.emacs", home);

    if (append_file_if_missing(vimrc, NULL, vimrc_add, "OMEGA-VIMRC-BEGIN") != 0)
      fprintf(stderr, "warning: could not update %s\n", vimrc);
    if (append_file_if_missing(emacsrc, NULL, emacs_add, "OMEGA-EMACSRC-BEGIN") != 0)
      fprintf(stderr, "warning: could not update %s\n", emacsrc);

    printf("Installed (idempotent) into %s/.vim/... and %s/.emacs.d/lisp/ and updated %s and %s\n", home, home, vimrc, emacsrc);
  } else {
    printf("To install into your home directories (idempotent append), run: %s --install\n", argv[0]);
  }

  return 0;
}
```
