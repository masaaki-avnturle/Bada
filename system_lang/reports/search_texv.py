#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search .tex,v files under a CVS root for phrases and LaTeX-like formulas.

Usage examples:
  # search for literal phrase "energy conservation"
  python3 search_texv.py /srv/cvsroot/pdf --phrase "energy conservation"

  # search by regex (case-insensitive)
  python3 search_texv.py /srv/cvsroot/pdf --regex "(E|e)quation\s*\d+" --ignore-case

  # search for LaTeX math markers ($...$, \[...\], \(...\) or math commands)
  python3 search_texv.py /srv/cvsroot/pdf --formula

  # combine and write matches to CSV
  python3 search_texv.py /srv/cvsroot/pdf --phrase "導入" --formula --out matches.csv
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Pattern, Tuple

DEFAULT_ENCODING = "utf-8"

# Basic LaTeX/math detection regex (common markers and commands)
DEFAULT_FORMULA_REGEX = r"(\$[^$]+\$|\\\([^\)]+\\\)|\\\[[^\]]+\\\]|\\(?:frac|sum|int|sqrt|begin\{equation\}|alpha|beta|gamma)\b|[0-9]+(?:\s?)[\+\-\*/=<>])"

def parse_args():
    p = argparse.ArgumentParser(description="Search .tex,v files for phrases and LaTeX formulas.")
    p.add_argument("cvs_root", help="Path to CVS repository root to search (recursively).")
    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument("--phrase", help="Literal phrase to search (treated literally).")
    group.add_argument("--regex", help="Regular expression to search.")
    p.add_argument("--formula", action="store_true", help="Enable LaTeX-style formula detection.")
    p.add_argument("--formula-regex", default=DEFAULT_FORMULA_REGEX, help="Regex for formula detection.")
    p.add_argument("--ignore-case", action="store_true", help="Case-insensitive search for phrase/regex.")
    p.add_argument("--ext", default=",v", help="File extension to search (default: \",v\").")
    p.add_argument("--encoding", default=DEFAULT_ENCODING, help="File encoding to read (default: utf-8).")
    p.add_argument("--out", default=None, help="Output CSV file for matches.")
    p.add_argument("--max-snippet", type=int, default=200, help="Max chars of snippet in output.")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()

def compile_pattern(phrase: Optional[str], regex: Optional[str], ignore_case: bool) -> Optional[Pattern]:
    if phrase:
        esc = re.escape(phrase)
        flags = re.IGNORECASE if ignore_case else 0
        return re.compile(esc, flags=flags)
    if regex:
        flags = re.IGNORECASE if ignore_case else 0
        return re.compile(regex, flags=flags)
    return None

def find_texv_files(root: Path, ext: str, verbose: bool=False) -> List[Path]:
    files: List[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(ext):
                files.append(Path(dirpath) / fn)
    if verbose:
        print(f"[index] found {len(files)} files with ext '{ext}' under {root}")
    return files

def read_file_text(path: Path, encoding: str) -> Optional[str]:
    try:
        # try utf-8 first, fallback to latin-1 if necessary
        return path.read_text(encoding=encoding, errors="strict")
    except Exception:
        try:
            return path.read_text(encoding="latin-1", errors="replace")
        except Exception:
            return None

def excerpt_around_match(text: str, mstart: int, mend: int, maxlen: int) -> str:
    half = maxlen // 2
    start = max(0, mstart - half)
    end = min(len(text), mend + half)
    snippet = text[start:end].replace("\n", " ")
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet[:maxlen]

def search_file(path: Path, pat: Optional[Pattern], formula_re: Optional[Pattern], encoding: str, max_snippet: int) -> List[Tuple[int,str,str]]:
    """
    Returns list of matches as tuples: (line_number, matched_text_snippet, kind)
    kind: 'phrase'|'regex'|'formula'
    """
    text = read_file_text(path, encoding)
    if text is None:
        return []
    matches: List[Tuple[int,str,str]] = []

    # If pattern provided, search all occurrences
    if pat:
        for m in pat.finditer(text):
            snippet = excerpt_around_match(text, m.start(), m.end(), max_snippet)
            # estimate line number
            lineno = text.count("\n", 0, m.start()) + 1
            matches.append((lineno, snippet, "phrase" if pat.pattern == re.escape(pat.pattern) else "regex"))

    # Formula search
    if formula_re:
        for m in formula_re.finditer(text):
            snippet = excerpt_around_match(text, m.start(), m.end(), max_snippet)
            lineno = text.count("\n", 0, m.start()) + 1
            matches.append((lineno, snippet, "formula"))

    return matches

def main():
    args = parse_args()
    cvs_root = Path(args.cvs_root)
    if not cvs_root.exists() or not cvs_root.is_dir():
        print("cvs_root not found or not a directory:", cvs_root, file=sys.stderr)
        sys.exit(2)

    pat = compile_pattern(args.phrase, args.regex, args.ignore_case)
    formula_re = re.compile(args.formula_regex) if args.formula else None

    files = find_texv_files(cvs_root, args.ext, verbose=args.verbose)

    all_matches = []
    for fp in files:
        res = search_file(fp, pat, formula_re, args.encoding, args.max_snippet)
        if res:
            for lineno, snippet, kind in res:
                all_matches.append({
                    "file": str(fp),
                    "line": lineno,
                    "kind": kind,
                    "snippet": snippet
                })
            if args.verbose:
                print(f"[match] {fp} -> {len(res)} hits")

    # Output
    if args.out:
        outp = Path(args.out)
        fieldnames = ["file","line","kind","snippet"]
        with outp.open("w", encoding=args.encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for r in all_matches:
                writer.writerow(r)
        print(f"Wrote {len(all_matches)} matches to {outp}")
    else:
        for r in all_matches:
            print(f"{r['file']}:{r['line']} [{r['kind']}] {r['snippet']}")
        print(f"Total matches: {len(all_matches)}")

if __name__ == "__main__":
    main()
