以下は TeX ソースを処理する Python スクリプトです。目的は次の2点です。

- 数式内（既に $...$, $$...$$, \(...\), \[...\], equation系環境内にある部分）で、`sin`, `cos`, `tan`, `log`, `ln`, `exp`, `lim`, `max`, `min` などの関数名に先頭のバックスラッシュが欠けていれば自動で `\sin` のように補う。
- テキスト中に「数式らしき箇所」（関数名＋変数/括弧などのパターン）があり、まだ数式モードに入っていなければ `$$ ... $$` で囲む。

注意事項：
- 自動処理は完璧ではなく、文脈に依存します。必ず結果を確認してください。
- 必要に応じて対象関数リストや数式判定の正規表現を調整してください。

保存例: `fix_tex_math.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage: python3 fix_tex_math.py input.tex > output.tex
"""

import sys
import re

if len(sys.argv) < 2:
    print("Usage: python3 fix_tex_math.py input.tex > output.tex", file=sys.stderr)
    sys.exit(1)

text = open(sys.argv[1], encoding='utf-8').read()

# 関数名リスト（必要に応じて追加）
funcs = ["sin","cos","tan","csc","sec","cot","arcsin","arccos","arctan",
         "sinh","cosh","tanh","log","ln","exp","lim","max","min"]

# 正規表現用のパターン（先読みで既にバックスラッシュがある場合は除外）
func_pattern = re.compile(r'(?<!\\)\b(' + '|'.join(re.escape(f) for f in funcs) + r')\b')

# まず、ソースを「数式モードの領域」と「それ以外」に分割する。
# マッチ順序に注意: $$...$$ を先に、次に \[...\], \(..\), \begin{env}...\end{env}, そして単一ドル $...$。
# 簡便のため非貪欲マッチを使用。環境名の許容は基本的なもののみとする。
envs = ["equation","align","multline","gather","flalign","equation\*","align\*","math"]
# build combined pattern
patterns = []
patterns.append(r'\$\$.*?\$\$')                     # $$...$$
patterns.append(r'\\\[.*?\\\]')                     # \[...\]
patterns.append(r'\\\(.*?\\\)')                     # \(..\)
# \begin{env}...\end{env}
for e in envs:
    patterns.append(r'\\begin\{' + e + r'\}.*?\\end\{' + e + r'\}')
patterns.append(r'\$.*?\$')                         # $...$

combined = re.compile('|'.join('(' + p + ')' for p in patterns), re.DOTALL)

parts = []
last = 0
for m in combined.finditer(text):
    # テキスト領域（数式モードでない）
    if m.start() > last:
        parts.append(("text", text[last:m.start()]))
    # 数式領域
    parts.append(("math", text[m.start():m.end()]))
    last = m.end()
if last < len(text):
    parts.append(("text", text[last:]))

def fix_funcs_in_math(s):
    # math 部分の先頭と末尾の区切り記号（$$, $, \[, \], \(, \), \begin...\end...）はそのまま維持。
    # 区切り記号を除いた中身だけ置換する。
    # 簡易に前後の区切りを識別:
    if s.startswith('$$') and s.endswith('$$'):
        inner = s[2:-2]
        pre, post = '$$', '$$'
    elif s.startswith('$') and s.endswith('$'):
        inner = s[1:-1]
        pre, post = '$', '$'
    elif s.startswith('\\[') and s.endswith('\\]'):
        inner = s[2:-2]
        pre, post = '\\[', '\\]'
    elif s.startswith('\\(') and s.endswith('\\)'):
        inner = s[2:-2]
        pre, post = '\\(', '\\)'
    else:
        # \begin{...}...\end{...} などは区切りを自前で検出してそのまま中身を処理
        # 先頭の最初の '}' の位置までを prefix とし、末尾の最後の '\begin' の位置から終わりを suffix とするのは危険なので
        # 簡易に全体を inner として処理（環境名の括りは保持しないが \begin...\end はそのまま残る）
        # ここでは中身全部に置換適用して戻す
        inner = s
        pre, post = '', ''
    # 置換: 先頭にバックスラッシュが無い関数名を \func に
    def repl(m):
        return '\\\\' + m.group(1)
    new_inner = func_pattern.sub(repl, inner)
    return pre + new_inner + post

def wrap_text_math(s):
    # テキスト領域で「数式らしき」箇所を $$...$$ で囲む
    # ここでは簡易ルール：
    #  - 関数名(funcs) に続いて空白＋変数(英数字や括弧) または 関数名の直後に '(' が来る場合
    #  - すでに数式モードにあるか $ が含まれる場合は無視（この関数はテキスト領域のみ呼ばれる想定）
    pattern = re.compile(
        r'(?<!\\)\b(' + '|'.join(re.escape(f) for f in funcs) + r')\b'  # 関数名（バックスラッシュなし）
        r'(?:\s+[A-Za-z0-9_\\\(]|(?=\())'  # 関数名の後に空白＋変数/左括弧、またはすぐに'('
    )
    # 置換: マッチした位置の前後を含めて適切に囲む必要があるので、単純な方法でマッチ位置から近傍を抽出して $$...$$ を挿入する。
    # 実装は、関数名にマッチした箇所から「数式らしき終端」まで（改行や句読点で終了する想定）を取る。
    def repl(m):
        start = m.start()
        # ここではマッチ直前から文中で最長で次の句点・空行・改行2回までを数式とみなす簡易ルール:
        # 実際は文脈に依るため調整が必要。
        rest = s[start:]
        # 終端候補: 改行2回、ピリオド+空白、句読点などを終端とする
        end_match = re.search(r'(\n\s*\n|[。\.，,;:!?]|$)', rest)
        if end_match:
            end = start + end_match.start()
        else:
            end = len(s)
        inner = s[start:end].rstrip()
        return '$$' + inner + '$$' + s[end:start+0]  # 元ののこりは外部で維持されるのでここは置換結果のみ
    # 上の実装では文字列の切り出しを伴うため、単純な re.sub では不可。代わりに逐次スキャンして構築する。
    out = []
    idx = 0
    for m in pattern.finditer(s):
        if m.start() < idx:
            continue
        out.append(s[idx:m.start()])
        # decide end position
        rest = s[m.start():]
        end_match = re.search(r'(\n\s*\n|[。\.，,;:!?]|$)', rest)
        if end_match:
            end = m.start() + end_match.start()
        else:
            end = len(s)
        inner = s[m.start():end].rstrip()
        out.append('$$' + inner + '$$')
        idx = end
    out.append(s[idx:])
    return ''.join(out)

# 処理を実行
out_parts = []
for kind, chunk in parts:
    if kind == "math":
        out_parts.append(fix_funcs_in_math(chunk))
    else:
        # テキスト領域：まず既に $ または \( \[ \begin{ のような数式区切りが含まれていないかチェック
        if re.search(r'(\$|\\\(|\\\[|\\begin\{)', chunk):
            # 数式区切りを含むテキスト部分はそれらを壊さないように単純に関数名の前にバックスラッシュを挿入するだけ
            out_parts.append(func_pattern.sub(r'\\\1', chunk))
        else:
            # 区切りを含まない純テキストなら、数式らしき箇所を $$...$$ で囲む試みを行い、
            # さらに囲んだ内部の関数名にバックスラッシュを付与する
            wrapped = wrap_text_math(chunk)
            # wrapped の中の $$...$$ 内も後で処理されるわけではないのでここで補正を行う:
            # 簡易に $$...$$ 内の関数名を補正
            wrapped = re.sub(r'(\$\$)(.*?)(\$\$)',
                             lambda m: m.group(1) + func_pattern.sub(r'\\\1', m.group(2)) + m.group(3),
                             wrapped, flags=re.DOTALL)
            out_parts.append(wrapped)

result = ''.join(out_parts)
print(result, end='')
```

使い方:
- 入力ファイルを指定して実行し、出力を確認してください。
  例: `python3 fix_tex_math.py input.tex > output.tex`
- 重要: 自動置換ミスを防ぐため、差分を確認して必要に応じて関数リストや正規表現を調整してください。

必要なら、処理をより厳密にする（例えば TeX の字句解析を行う、環境名を増やす、関数リストを拡張する、単一ドルの扱いを厳密化する）改良版を作ります。どのような誤変換が出たか例を示していただければ調整します。
