以下は、外部から読み込んだ CSV（CVS・GitHub に投稿した各ファイルのメタや本文を含む想定）に対して、
- 数式（LaTeX 形式や典型的な数式トークン）を検索する機能、
- 言語（ISO コードや簡易判定／langdetect 利用）の検索機能、
を備えた Python コマンドラインツールです。

ポイント
- 数式検出は LaTeX のインライン/ディスプレイ構文（$...$, \(..\), \[..\]）や \frac,\sum,\int 等のコマンド検出を行います。必要に応じて正規表現を調整してください。
- 言語検索は（1）外部に言語列があればその値で絞る、（2）なければ簡易 Unicode 判定（CJK vs Latin）か、オプションで `langdetect` ライブラリを使った判定を行えます。
- 入力 CSV はヘッダあり（任意の列名）。本文やコメントが入っている列名を指定してください。

保存例: search_csv_formula_lang.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search CSV rows for mathematical content and/or language.

Usage:
  python3 search_csv_formula_lang.py input.csv --text-col content [--out out.csv] [--formula] [--formula-regex REGEX]
                               [--lang LANG] [--lang-col language] [--use-langdetect] [--encoding utf-8]

Examples:
  # find rows whose 'content' contains LaTeX math
  python3 search_csv_formula_lang.py data.csv --text-col content --formula --out matches.csv

  # find rows where language column equals 'ja'
  python3 search_csv_formula_lang.py data.csv --text-col content --lang ja --lang-col lang

  # use language detection via langdetect package (pip install langdetect)
  python3 search_csv_formula_lang.py data.csv --text-col content --use-langdetect --lang en
"""
from __future__ import annotations
import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Optional, List

# Default regex to detect LaTeX-like math or common math commands
DEFAULT_FORMULA_REGEX = r"(\$[^$]+\$|\\\([^\)]+\\\)|\\\[[^\]]+\\\]|\\(?:frac|sum|int|sqrt|begin\{equation\}|alpha|beta|gamma)\b|[0-9]+\s*[\+\-\*/=<>])"

# simple unicode-based language heuristics
def simple_language_hint(text: str) -> Optional[str]:
    if not text:
        return None
    # CJK detection
    for ch in text:
        code = ord(ch)
        # common CJK ranges
        if 0x4E00 <= code <= 0x9FFF or 0x3040 <= code <= 0x30FF or 0xAC00 <= code <= 0xD7AF:
            return "cjk"
    # if mostly ASCII letters, say 'latin'
    letters = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    if letters >= 3:
        return "latin"
    return None

def detect_lang_with_langdetect(text: str) -> Optional[str]:
    try:
        from langdetect import detect
    except Exception:
        return None
    try:
        return detect(text)
    except Exception:
        return None

def row_matches_formula(text: str, regex: re.Pattern) -> bool:
    if not text:
        return False
    return bool(regex.search(text))

def row_matches_language(text: str, desired: str, lang_col_value: Optional[str],
                         use_langdetect: bool) -> bool:
    # If CSV contains explicit language value, prefer that
    if lang_col_value:
        return lang_col_value.strip().lower() == desired.lower()
    # else try langdetect if requested
    if use_langdetect:
        det = detect_lang_with_langdetect(text or "")
        if det:
            return det.lower().startswith(desired.lower())
    # fallback simple hint mapping
    hint = simple_language_hint(text or "")
    if hint is None:
        return False
    if desired.lower() in ("ja", "japanese") and hint == "cjk":
        return True
    if desired.lower() in ("en", "eng", "english") and hint == "latin":
        return True
    # allow matching 'cjk' or 'latin' directly
    return desired.lower() == hint

def parse_args():
    p = argparse.ArgumentParser(description="Search CSV for formula and language.")
    p.add_argument("csv", help="Input CSV file (header).")
    p.add_argument("--text-col", required=True, help="Column name containing file text/body to search.")
    p.add_argument("--lang-col", default=None, help="Optional column name containing language code.")
    p.add_argument("--formula", action="store_true", help="Enable formula search.")
    p.add_argument("--formula-regex", default=DEFAULT_FORMULA_REGEX, help="Regex for formula detection.")
    p.add_argument("--lang", default=None, help="Desired language to filter (e.g. 'ja' or 'en' or 'cjk').")
    p.add_argument("--use-langdetect", action="store_true", help="Use langdetect package if available.")
    p.add_argument("--out", default=None, help="Output CSV file for matches (if omitted, print matches).")
    p.add_argument("--encoding", default="utf-8", help="File encoding (default utf-8).")
    return p.parse_args()

def main():
    args = parse_args()
    inp = Path(args.csv)
    if not inp.exists():
        print("Input CSV not found:", inp, file=sys.stderr)
        sys.exit(2)

    formula_regex = re.compile(args.formula_regex, flags=re.UNICODE)

    matches: List[dict] = []
    with inp.open("r", encoding=args.encoding, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header", file=sys.stderr); sys.exit(3)
        for i, row in enumerate(reader, start=1):
            text = row.get(args.text_col, "") or ""
            lang_col_value = row.get(args.lang_col, "") if args.lang_col else None

            ok_formula = True
            ok_lang = True

            if args.formula:
                ok_formula = row_matches_formula(text, formula_regex)

            if args.lang:
                ok_lang = row_matches_language(text, args.lang, lang_col_value, args.use_langdetect)

            if ok_formula and ok_lang:
                # annotate match reasons optionally
                row["_matched_formula"] = "1" if args.formula and ok_formula else ""
                row["_matched_lang"] = args.lang or ""
                row["_rownum"] = str(i)
                matches.append(row)

    if args.out:
        outp = Path(args.out)
        # write header merging original plus meta cols
        fieldnames = list(reader.fieldnames or [])  # type: ignore
        for extra in ("_matched_formula", "_matched_lang", "_rownum"):
            if extra not in fieldnames:
                fieldnames.append(extra)
        with outp.open("w", encoding=args.encoding, newline="") as outf:
            writer = csv.DictWriter(outf, fieldnames=fieldnames, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for r in matches:
                # ensure all fields present
                out_row = {k: r.get(k, "") for k in fieldnames}
                writer.writerow(out_row)
        print(f"Wrote {len(matches)} matches to {outp}")
    else:
        # print brief summary lines
        for r in matches:
            rn = r.get("_rownum", "?")
            path = r.get("path", r.get("file", r.get("filename", "")))
            snippet = (r.get(args.text_col, "") or "")[:200].replace("\n", " ")
            print(f"row={rn} path={path} formula={r.get('_matched_formula','')} lang={r.get('_matched_lang','')} snippet={snippet}")
        print(f"Total matches: {len(matches)}")

if __name__ == "__main__":
    main()
```

補足
- langdetect を利用する場合は `pip install langdetect`。
- 必要なら数式の検出をさらに厳密化（MathML, Unicode 数学記号検出、数式トークンの複合判定など）できます。サンプル CSV の数行を示していただければ正規表現を調整します。
