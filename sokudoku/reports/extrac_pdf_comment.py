#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract comments/description from all PDFs under a directory.

Outputs CSV with columns:
  path, title, author, subject, keywords, producer, creator, annotations, matched_snippets

Usage:
  python3 extract_pdf_comments.py /path/to/cloned/repo --out comments.csv --encoding utf-8
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import pikepdf
from pathlib import Path
from typing import List, Optional
from pdfminer.high_level import extract_text

# regex to find likely "comment/description" fragments in extracted text
COMMENT_KEYWORDS = [
    "注釈", "コメント", "説明", "備考", "追記", "注記", "Note", "Comment", "Remark", "Description"
]
# build regex to capture paragraph containing keyword
KW_RE = re.compile(r'(.{0,200}(' + "|".join(re.escape(k) for k in COMMENT_KEYWORDS) + r')(.{0,200}))', flags=re.IGNORECASE | re.DOTALL)

def find_pdfs(root: Path) -> List[Path]:
    out = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                out.append(Path(dirpath) / fn)
    return out

def read_metadata(pdf_path: Path) -> dict:
    meta = {"title":"","author":"","subject":"","keywords":"","producer":"","creator":""}
    try:
        with pikepdf.Pdf.open(str(pdf_path)) as pdf:
            info = pdf.docinfo
            # pikepdf returns keys like '/Title', '/Author'
            for k,v in info.items():
                key = k.lstrip("/").lower()
                try:
                    val = str(v)
                except Exception:
                    val = repr(v)
                if key in meta:
                    meta[key] = val
                else:
                    meta[key] = val
    except Exception as e:
        meta["__meta_error"] = str(e)
    return meta

def extract_annotations(pdf_path: Path) -> List[str]:
    annos: List[str] = []
    try:
        with pikepdf.Pdf.open(str(pdf_path)) as pdf:
            for pnum, page in enumerate(pdf.pages, start=1):
                annots = page.get("/Annots")
                if not annots:
                    continue
                for a in annots:
                    try:
                        obj = a.get_object()
                        subtype = obj.get("/Subtype")
                        contents = obj.get("/Contents")
                        if contents:
                            # contents may be a pikepdf.String or other
                            annos.append(f"p{pnum}:{str(contents)}")
                        else:
                            # some annotations store /T (title) or /Contents in different form
                            t = obj.get("/T")
                            if t:
                                annos.append(f"p{pnum}:{str(t)}")
                    except Exception:
                        continue
    except Exception:
        pass
    return annos

def extract_text_comments(pdf_path: Path, max_pages_text: int = 10) -> List[str]:
    """
    Extract text (pdfminer) and search for paragraphs/lines containing keywords.
    Note: for large PDFs you may want to limit pages or extract progressively.
    """
    snippets: List[str] = []
    try:
        # extract whole text (may be slow for many large PDFs)
        text = extract_text(str(pdf_path))
        if not text:
            return snippets
        # normalize whitespace
        norm = re.sub(r'\r\n', '\n', text)
        # find all matches around keywords
        for m in KW_RE.finditer(norm):
            snip = m.group(1).strip()
            # collapse whitespace for CSV friendliness
            snip = re.sub(r'\s+', ' ', snip)
            if snip not in snippets:
                snippets.append(snip)
    except Exception:
        pass
    return snippets

def main():
    p = argparse.ArgumentParser(description="Extract comments/descriptions from PDFs recursively.")
    p.add_argument("root", help="Root directory (cloned GitHub repo)")
    p.add_argument("--out", default=None, help="Output CSV file (if omitted, print to stdout)")
    p.add_argument("--encoding", default="utf-8", help="CSV encoding")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit("root not found: " + str(root))

    pdfs = find_pdfs(root)
    rows = []
    for pdf in pdfs:
        meta = read_metadata(pdf)
        annos = extract_annotations(pdf)
        snippets = extract_text_comments(pdf)
        rows.append({
            "path": str(pdf),
            "title": meta.get("title",""),
            "author": meta.get("author",""),
            "subject": meta.get("subject",""),
            "keywords": meta.get("keywords",""),
            "producer": meta.get("producer",""),
            "creator": meta.get("creator",""),
            "meta_error": meta.get("__meta_error",""),
            "annotations": " || ".join(annos),
            "matched_snippets": " || ".join(snippets)
        })

    fieldnames = ["path","title","author","subject","keywords","producer","creator","meta_error","annotations","matched_snippets"]

    if args.out:
        outp = Path(args.out)
        with outp.open("w", encoding=args.encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"Wrote {len(rows)} records to {outp}")
    else:
        # print simple summary
        for r in rows:
            print("FILE:", r["path"])
            if r["title"]: print("  Title:", r["title"])
            if r["author"]: print("  Author:", r["author"])
            if r["annotations"]: print("  Annotations:", r["annotations"])
            if r["matched_snippets"]:
                print("  Matched snippets:")
                for s in r["matched_snippets"].split(" || "):
                    print("    -", s)
            print()

if __name__ == "__main__":
    main()
