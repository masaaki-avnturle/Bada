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
