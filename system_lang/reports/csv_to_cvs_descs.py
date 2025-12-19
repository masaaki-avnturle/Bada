#!/usr/bin/env python3
# use: ./csv_to_cvs_descs.py all_file_history_tex.csv
import csv
import os
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: csv_to_cvs_descs.py input.csv", file=sys.stderr)
    sys.exit(2)

inp = sys.argv[1]
outdir = Path(".cvs_descriptions")
outdir.mkdir(exist_ok=True)

with open(inp, newline='', encoding='utf-8') as fin:
    reader = csv.DictReader(fin)
    for row in reader:
        path = row.get('path') or row.get('file') or row.get('filename')
        if not path:
            continue
        # 変換: スラッシュを __ にしてファイル名化（既出の方式に合わせる）
        safe = path.replace("/", "__")
        descfile = outdir / (safe + ".desc")
        # レコード書式（CVS風: commit, author, date, message）
        commit = row.get('commit','')
        author = row.get('author','')
        date = row.get('date','')
        message = row.get('message','').replace('\r','')
        # 多行メッセージを整形（改行を \n のまま残すか、エスケープするか選べます）
        with open(descfile, "a", encoding='utf-8') as fout:
            fout.write(f"Commit: {commit}\n")
            fout.write(f"Author: {author}\n")
            fout.write(f"Date: {date}\n")
            fout.write("Message:\n")
            fout.write(message.rstrip() + "\n")
            fout.write("-" * 40 + "\n")
