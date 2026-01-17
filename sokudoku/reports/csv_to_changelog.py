#!/usr/bin/env python3
# csv_to_changelog.py input.csv > cvs_changelog.txt
import csv, sys
if len(sys.argv)!=2: sys.exit("Usage: csv_to_changelog.py input.csv")
with open(sys.argv[1], newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        print(f"{row.get('date','')}  {row.get('author','')}")
        print(f"\t{row.get('message','').replace(chr(10),' ')}")
        print(f"\tFiles: {row.get('path','')}\n")
