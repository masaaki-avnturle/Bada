以下は、指定の CSV（ヘッダ行あり）を読み込み、各行のファイルパスに対応する説明ファイルを `.cvs_descriptions/` に書き換える Python スクリプトです。CSV 内の message フィールドは既に ".pdf" → ".tex" の置換済みである前提です。既存の説明ファイルは上書きされます（最新のみ保持）。

保存例: `csv_to_cvs_desc_overwrite.py`

使い方:
./csv_to_cvs_desc_overwrite.py input.csv

スクリプト:
```python
#!/usr/bin/env python3
# csv_to_cvs_desc_overwrite.py
# Usage: python3 csv_to_cvs_desc_overwrite.py input.csv

import csv
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: csv_to_cvs_desc_overwrite.py input.csv", file=sys.stderr)
    sys.exit(2)

inp = Path(sys.argv[1])
if not inp.exists():
    print(f"Input CSV not found: {inp}", file=sys.stderr)
    sys.exit(3)

outdir = Path(".cvs_descriptions")
outdir.mkdir(exist_ok=True)

# 読み込み可能な候補フィールド名
path_keys = ("path","file","filepath","filename","file_path")
commit_keys = ("commit","hash")
author_keys = ("author","author_name","author_name_email")
date_keys = ("date","datetime","commit_date")
message_keys = ("message","msg","commit_message","description","desc")

def pick(row, keys):
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return ""

with inp.open(newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    if reader.fieldnames is None:
        print("CSV has no header", file=sys.stderr)
        sys.exit(4)

    for row in reader:
        # get values with fallback
        path = pick(row, path_keys).strip()
        if not path:
            # skip rows without a path
            continue
        commit = pick(row, commit_keys)
        author = pick(row, author_keys)
        date = pick(row, date_keys)
        message = pick(row, message_keys)

        # Normalize message line endings
        if message is None:
            message = ""
        else:
            message = message.replace('\r\n', '\n').replace('\r', '\n')

        # Output filename: replace slashes to avoid nested dirs (existing scheme)
        safe_name = path.replace("/", "__")
        desc_path = outdir / (safe_name + ".desc")

        # Write/overwrite description file
        with desc_path.open("w", encoding="utf-8") as out:
            out.write(f"File: {path}\n")
            if commit:
                out.write(f"Commit: {commit}\n")
            if author:
                out.write(f"Author: {author}\n")
            if date:
                out.write(f"Date: {date}\n")
            out.write("Message:\n")
            out.write(message.rstrip() + "\n")
```

説明・注意点
- CSV のヘッダ名が異なる場合でも、スクリプト上部の `path_keys` / `message_keys` 等に候補名を追加すれば検出されます。
- 出力ファイル名は `path` 内の `/` を `__` に置換した形式（事前に示した方式に合わせています）。代わりにネストされたディレクトリ構成で保存したい場合は `safe_name` の生成を変更してください（例: `outdir / path` を使い、親ディレクトリを `mkdir(parents=True, exist_ok=True)`）。
- スクリプトは各 CSV 行ごとに上書きします（最新の行が最終的な内容となります）。履歴を追記したい場合は `open(..., "a")` に変更してください。