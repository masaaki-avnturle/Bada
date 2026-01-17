下記は、入力 CSV の各行について `message` 列の内容を `commitment` 列にコピー（上書き／追加）して、新しい CSV を出力する簡単な Python スクリプトです。BOM、エンコーディング、ヘッダ順を考慮して安全に処理します。

保存例: `message_to_commitment.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copy CSV column 'message' -> 'commitment' (overwrite or add) and write out.
Usage:
  python3 message_to_commitment.py input.csv output.csv
Options:
  --encoding ENCODING   (default: utf-8)
  --src-col NAME        (default: message)
  --dst-col NAME        (default: commitment)
  --backup              (make backup of output if exists)
"""
from __future__ import annotations
import argparse
import csv
import shutil
from pathlib import Path
import sys

def parse_args():
    p = argparse.ArgumentParser(description="Copy CSV column (message -> commitment).")
    p.add_argument("input", help="Input CSV file")
    p.add_argument("output", help="Output CSV file to write")
    p.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    p.add_argument("--src-col", default="message", help="Source column name (default: message)")
    p.add_argument("--dst-col", default="commitment", help="Destination column name (default: commitment)")
    p.add_argument("--backup", action="store_true", help="Backup output file if it exists")
    return p.parse_args()

def main():
    args = parse_args()
    inp = Path(args.input)
    out = Path(args.output)

    if not inp.exists():
        print("Input not found:", inp, file=sys.stderr)
        sys.exit(2)

    if args.backup and out.exists():
        bak = out.with_suffix(out.suffix + ".bak")
        shutil.copy2(out, bak)

    with inp.open("r", encoding=args.encoding, newline="") as inf:
        reader = csv.DictReader(inf)
        fieldnames = list(reader.fieldnames or [])
        # Ensure dst-col exists in header
        if args.dst_col not in fieldnames:
            # append after src-col if present, else at end
            if args.src_col in fieldnames:
                idx = fieldnames.index(args.src_col) + 1
                fieldnames.insert(idx, args.dst_col)
            else:
                fieldnames.append(args.dst_col)

        rows = []
        for i, row in enumerate(reader, start=1):
            src_val = row.get(args.src_col, "")
            # copy/overwrite
            row[args.dst_col] = src_val
            rows.append(row)

    # Write output preserving quoting minimal and newline handling
    with out.open("w", encoding=args.encoding, newline="") as outf:
        writer = csv.DictWriter(outf, fieldnames=fieldnames, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in rows:
            # ensure all fieldnames present
            out_row = {k: (r.get(k, "") if k in r else "") for k in fieldnames}
            writer.writerow(out_row)

if __name__ == "__main__":
    main()
```

使い方例
- 出力ファイルへ書き出す:
  python3 message_to_commitment.py input.csv output.csv
- 既存出力をバックアップ:
  python3 message_to_commitment.py input.csv output.csv --backup
- 列名が異なる場合:
  python3 message_to_commitment.py input.csv output.csv --src-col commit --dst-col commitment

必要なら
- CSV の先頭数行を貼っていただければ、スクリプトをそのファイルに合わせて微調整します。
