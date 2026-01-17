以下は、BNF（簡易形式）ファイルを入力として受け取り、Vim 用（syntax/indent/ftplugin/omnifunc）と Emacs 用（mylang-mode.el：font-lock/indent/company）ソースコードを自動生成する Python スクリプトです。

特徴
- 入力 BNF からキーワード（ターミナルのうち識別子風トークン）を抽出してシンタックスハイライト候補にする。
- 非端末（非終端記号）は無視して、簡易にキーワード／型／関数名候補を生成。
- 生成物：
  - Vim: ftdetect, syntax, indent, ftplugin, autoload（簡易 omnifunc）
  - Emacs: mylang-mode.el（font-lock-keyワード、indent関数、company backend）
- 実用的な完全パーサではなく「BNF 文字列からキーワード等を抽出してテンプレートに埋める」ジェネレータです。BNFの形に若干の自由度があります（下記の入力フォーマット参照）。

入力 BNF フォーマット（簡易）
- コメント行は `#` で始まる。
- 生成対象の終端（token）として扱うのは、ダブルクオートで囲まれたリテラル（例: "if"）および、識別子風で大文字小文字混在の単語リスト（例: IDENTIFIER のような非端末は無視）。
- 例:
  # sample.bnf
  <program> ::= <stmt>*
  <stmt> ::= "if" "(" <expr> ")" "{" <stmt>* "}" | "return" <expr> ";"
  <expr> ::= <number> | <ident> | <expr> "+" <expr>

使い方
- 保存: `bnf_to_editor_support.py`
- 実行例:
  python3 bnf_to_editor_support.py sample.bnf --lang mylang --outdir ./generated

出力ファイル（outdir）
- vim/ftdetect/mylang.vim
- vim/syntax/mylang.vim
- vim/indent/mylang.vim
- vim/ftplugin/mylang.vim
- vim/autoload/mylang_complete.vim
- emacs/mylang-mode.el

スクリプト（bnf_to_editor_support.py）
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple generator: BNF -> Vim/Emacs support (syntax, indent, completion).

Usage:
  python3 bnf_to_editor_support.py grammar.bnf --lang mylang --outdir ./generated
"""
from __future__ import annotations
import argparse
import os
import re
from pathlib import Path
from typing import List, Set

BNF_LITERAL_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
BNF_WORD_RE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\b')

VIM_SYNTAX_TMPL = """\" Auto-generated syntax for {lang}
if exists("b:current_syntax")
  finish
endif

" Keywords (from BNF)
syn keyword {lang}Keyword {keywords}

" Types (heuristic: tokens that look like TYPE_*)
syn keyword {lang}Type {types}

" Comments and strings
syn match {lang}LineComment \"//.*$\"
syn region {lang}BlockComment start=\"/\\*\" end=\"\\*/\" keepend
syn region {lang}String start=+\"+ skip=+\\\\\\\\\\|\\"+ end=+\"+

syn match {lang}Number \"\\v\\<\\d+(\\.\\d+)?\\>\"
syn match {lang}Func \"\\v\\<[A-Za-z_][A-Za-z0-9_]*\\>\\ze\\s*\\(\"
syn match {lang}Identifier \"\\v\\<[A-Za-z_][A-Za-z0-9_]*\\>\"

hi def link {lang}Keyword Keyword
hi def link {lang}Type Type
hi def link {lang}LineComment Comment
hi def link {lang}BlockComment Comment
hi def link {lang}String String
hi def link {lang}Number Number
hi def link {lang}Func Function
hi def link {lang}Identifier Identifier

let b:current_syntax = "{lang}"
"""

VIM_FTDETECT_TMPL = """if exists("g:did_load_{lang}_fdetect")
  finish
endif
augroup filetypedetect_{lang}
  autocmd! BufRead,BufNewFile *.{ext} setfiletype {lang}
augroup END
let g:did_load_{lang}_fdetect = 1
"""

VIM_FTPLUGIN_TMPL = """\" ftplugin for {lang}
setlocal tabstop=4
setlocal shiftwidth=4
setlocal expandtab
setlocal omnifunc={lang}#complete#omnifunc
"""

VIM_INDENT_TMPL = """\" indent for {lang}
if exists("b:did_indent_{lang}")
  finish
endif
let b:did_indent_{lang} = 1

function! Get{Lang}Indent()
  let lnum = prevnonblank(v:lnum - 1)
  if lnum == 0
    return 0
  endif
  let line = getline(lnum)
  if getline(v:lnum) =~ '^\\s*}'
    return indent(lnum) - &shiftwidth
  endif
  if line =~ '{\\s*$' || line =~ '\\v\\<(if|while|fn)\\>'
    return indent(lnum) + &shiftwidth
  endif
  return indent(lnum)
endfunction

setlocal indentexpr=Get{Lang}Indent()
setlocal indentkeys=0{{,0}},:,0#,!^F
"""

VIM_OMNIFUNC_TMPL = """\" autoload {lang}_complete.vim
function! {lang}#complete#omnifunc(findstart, base) abort
  if a:findstart
    let line = getline('.')
    let col = col('.') - 1
    while col > 0 && line[col - 1] =~ '\\k'
      let col -= 1
    endwhile
    return col
  else
    let res = []
    let kw = [{kw_list}]
    for k in kw
      if k =~ '^' . a:base
        call add(res, k)
      endif
    endfor
    \" collect identifiers in buffer
    let pat = '\\<[A-Za-z_][A-Za-z0-9_]*\\>'
    for l in range(1, line('$'))
      let line = getline(l)
      let idx = 0
      while 1
        let s = matchstr(line, pat, idx)
        if s == ''
          break
        endif
        if s =~ '^' . a:base && index(res, s) < 0
          call add(res, s)
        endif
        let pos = match(line, pat, idx)
        if pos < 0
          break
        endif
        let idx = pos + strlen(s)
      endwhile
    endfor
    return res
  endif
endfunction
"""

EMACS_MODE_TMPL = """;;; {lang}-mode.el --- major mode for {lang} -*- lexical-binding: t; -*-

(defvar {lang}-mode-hook nil)
(defvar {lang}-mode-map (let ((map (make-sparse-keymap))) map))

(defvar {lang}-syntax-table
  (let ((st (make-syntax-table)))
    (modify-syntax-entry ?/ \". 124b\" st)
    (modify-syntax-entry ?\\n \"> b\" st)
    (modify-syntax-entry ?* \". 23\" st)
    (modify-syntax-entry ?\" '\" st)
    st))

(defconst {lang}-keywords
  '({kw_list_unquoted}))

(defconst {lang}-types
  '({types_list_unquoted}))

(defvar {lang}-font-lock-keywords
  `((,(regexp-opt {lang}-keywords 'words) . font-lock-keyword-face)
    (,(regexp-opt {lang}-types 'words) . font-lock-type-face)
    (\"\\\\<[A-Za-z_][A-Za-z0-9_]*\\\\s-*\\(\" . (0 font-lock-function-name-face))
    (\"\\\\<[A-Za-z_][A-Za-z0-9_]*\\\\>\" . font-lock-variable-name-face)
    (\"\\\"\\\\(\\\\\\\\.\\\\|[^\\\"\\\\]\\)*\\\"\" . font-lock-string-face)
    (\"\\\\<[0-9]+\\\\(\\\\.[0-9]+\\\\)?\\\\>\" . font-lock-constant-face)))

(defun {lang}--compute-indent ()
  (save-excursion
    (beginning-of-line)
    (let ((cur (point)) (indent 0) (shift 4))
      (if (= (point) (point-min))
          0
        (forward-line -1)
        (while (and (not (bobp)) (looking-at-p \"^[ \\t]*$\"))
          (forward-line -1))
        (let ((prev (string-trim (buffer-substring-no-properties (line-beginning-position) (line-end-position)))))
          (setq indent (current-indentation))
          (when (looking-at-p \"^[ \\t]*}\")
            (setq indent (max 0 (- indent shift))))
          (when (or (string-match-p \"{\\\\s-*$\" prev)
                    (string-match-p \"\\\\<\\(if\\\\|while\\\\|fn\\)\\\\>.*\\\\(<.*\\\\|$\\)\" prev))
            (setq indent (+ indent shift)))))
      indent)))

(defun {lang}-indent-line ()
  (interactive)
  (let ((savep (point)) (indent ({lang}--compute-indent)))
    (beginning-of-line)
    (delete-horizontal-space)
    (indent-to indent)
    (when (> savep (point))
      (goto-char savep))))

(with-eval-after-load 'company
  (defun company-{lang}-backend (command &optional arg &rest _ignored)
    (interactive (list 'interactive))
    (cl-case command
      (interactive (company-begin-backend 'company-{lang}-backend))
      (prefix (and (derived-mode-p '{lang}-mode)
                   (company-grab-symbol)))
      (candidates
       (let ((sym (or arg \"\")))
         (all-completions sym (append {kw_list_el} {types_list_el} (mylang--collect-symbols)))))
      (meta (format \"This value is %s\" arg)))))

(defun {lang}--collect-symbols ()
  (let (res)
    (save-excursion
      (goto-char (point-min))
      (while (re-search-forward \"\\\\<[A-Za-z_][A-Za-z0-9_]*\\\\>\" nil t)
        (let ((s (match-string-no-properties 0)))
          (unless (member s res)
            (push s res)))))
    (nreverse res)))

(define-derived-mode {lang}-mode prog-mode \"{Lang}\"
  \"Major mode for {lang}.\"
  :syntax-table {lang}-syntax-table
  (setq-local font-lock-defaults '({lang}-font-lock-keywords))
  (setq-local indent-line-function '{lang}-indent-line)
  (setq-local comment-start \"// \")
  (setq-local comment-end \"\"))

(add-to-list 'auto-mode-alist '(\"\\.{ext}$\" . {lang}-mode))
(provide '{lang}-mode)
;;; {lang}-mode.el ends here
"""

def extract_literals_and_words(bnf_text: str) -> (Set[str], Set[str]):
    lits = set(m.group(1) for m in BNF_LITERAL_RE.finditer(bnf_text))
    # collect word-like terminals that are lowercase keywords (heuristic)
    words = set()
    for m in BNF_WORD_RE.finditer(bnf_text):
        w = m.group(1)
        # ignore non-terminal forms like <expr> etc (they include <> in BNF so were not matched)
        if w.isalpha() and w.lower() == w:
            # treat short lower-case words as keywords
            if len(w) <= 20 and w.isalpha():
                words.add(w)
    return lits, words

def sanitize_for_vim_kwlist(items: Set[str]) -> str:
    # join with spaces, quote if necessary
    esc = []
    for it in sorted(items):
        if re.search(r'\\|\"|\'| ', it):
            esc.append("'" + it.replace("'", "''") + "'")
        else:
            esc.append(it)
    return " ".join(esc)

def main():
    p = argparse.ArgumentParser(description="Generate Vim/Emacs support from BNF")
    p.add_argument("bnf", help="BNF input file")
    p.add_argument("--lang", default="mylang", help="language name (identifier)")
    p.add_argument("--ext", default="myl", help="file extension")
    p.add_argument("--outdir", default="generated", help="output directory")
    args = p.parse_args()

    bnf_text = Path(args.bnf).read_text(encoding="utf-8")
    lits, words = extract_literals_and_words(bnf_text)
    # treat literals that look like keywords (letters only) as keywords
    kw_candidates = set()
    types = set()
    for t in lits:
        s = t.strip()
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', s):
            if s.islower():
                kw_candidates.add(s)
            elif s.isupper() or s[0].isupper():
                types.add(s)
            else:
            # if literal contains letters, extract words
            for w in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', s):
                if w.islower():
                    kw_candidates.add(w)
                else:
                    types.add(w)

    # also include words found in BNF (heuristic)
    for w in words:
        if w.islower():
            kw_candidates.add(w)
        else:
            types.add(w)

    lang = args.lang
    Lang = lang.capitalize()
    out = Path(args.outdir)
    vim_dir = out / "vim"
    emacs_dir = out / "emacs"
    (vim_dir / "syntax").mkdir(parents=True, exist_ok=True)
    (vim_dir / "ftdetect").mkdir(parents=True, exist_ok=True)
    (vim_dir / "indent").mkdir(parents=True, exist_ok=True)
    (vim_dir / "autoload").mkdir(parents=True, exist_ok=True)
    emacs_dir.mkdir(parents=True, exist_ok=True)

    # prepare lists
    keywords = " ".join(sorted(kw_candidates))
    types_list = " ".join(sorted(types))
    kw_list = ", ".join("'" + k + "'" for k in sorted(kw_candidates))
    types_list_unquoted = " ".join("'" + t + "'" for t in sorted(types))
    kw_list_unquoted = " ".join("'" + k + "'" for k in sorted(kw_candidates))
    kw_list_el = "[" + " ".join("'" + k + "'" for k in sorted(kw_candidates)) + "]"
    types_list_el = "[" + " ".join("'" + t + "'" for t in sorted(types)) + "]"

    # write files
    ftdetect_path = vim_dir / "ftdetect" / f"{lang}.vim"
    ftdetect_path.write_text(VIM_FTDETECT_TMPL.format(lang=lang, ext=args.ext), encoding="utf-8")

    syntax_path = vim_dir / "syntax" / f"{lang}.vim"
    syntax_path.write_text(VIM_SYNTAX_TMPL.format(lang=lang, keywords=keywords or "if else while return fn", types=types_list or "int float"), encoding="utf-8")

    indent_path = vim_dir / "indent" / f"{lang}.vim"
    indent_path.write_text(VIM_INDENT_TMPL.format(lang=lang, Lang=Lang), encoding="utf-8")

    ftplugin_path = vim_dir / "ftplugin" / f"{lang}.vim"
    ftplugin_path.write_text(VIM_FTPLUGIN_TMPL.format(lang=lang), encoding="utf-8")

    autoload_path = vim_dir / "autoload" / f"{lang}_complete.vim"
    autoload_path.write_text(VIM_OMNIFUNC_TMPL.format(lang=lang, kw_list=kw_list), encoding="utf-8")

    emacs_path = emacs_dir / f"{lang}-mode.el"
    emacs_path.write_text(EMACS_MODE_TMPL.format(lang=lang, Lang=Lang, kw_list_unquoted=kw_list_unquoted, types_list_unquoted=types_list_unquoted, kw_list_el=kw_list_el, types_list_el=types_list_el, ext=args.ext), encoding="utf-8")

    print("Generated in", out.resolve())

if __name__ == "__main__":
    main()
```

注意事項・拡張案
- これは簡易ジェネレータです。BNF を完全に解析して正確なキーワード／構文木を得るには専用パーサ（ANTLR 等）を使い、AST を元により精密なハイライト／インデント／補完を作る必要があります。
- 実務では LSP（Language Server Protocol）を生成する方が補完・シンボル参照・インデント等を統一的に提供できるため推奨です。BNF→AST→LSP サーバの雛形を生成する方向にも拡張できます。
- 生成後は Vim/Emacs 側でファイルを所定の場所（~/.vim/... や ~/.emacs.d/lisp/）に置くか、プラグインとして読み込んでください。

必要なら
- あなたの具体的な BNF（ファイルを貼るか例を示す）を元に、実際に生成した Vim/Emacs ファイルを返します。
- さらに高度な出力（Neovim Lua、Tree-sitter 文法、LSP サーバ雛形、詳細なパーサ）を生成するバージョンを作成します。どれを優先しますか？
