#!/usr/bin/env python3
# use: ./replace_pdf_in_csv.py input.csv output.csv
import csv
import sys
import re

if len(sys.argv) != 3:
    print("Usage: replace_pdf_in_csv.py input.csv output.csv", file=sys.stderr)
    sys.exit(2)

inp, outp = sys.argv[1], sys.argv[2]

pattern = re.compile(r"\.pdf\b", flags=re.IGNORECASE)  # 単語境界で .pdf を置換

with open(inp, newline='', encoding='utf-8') as fin, open(outp, 'w', newline='', encoding='utf-8') as fout:
    reader = csv.DictReader(fin)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(fout, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in reader:
        if 'message' in row and row['message']:
            row['message'] = pattern.sub('.tex', row['message'])
        writer.writerow(row)
