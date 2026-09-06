#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Append commitments from CSV into CVS .te,v files (matching .pdf basename).

Assumptions / defaults:
 - Local PDFs: /home/masaaki/tuplenetwork/pdf/*.pdf
 - CVS tex,v dir: /srv/cvsroot/textfile/     (files named basename + ".te,v")
 - Input CSV must have header and contain at least columns "path" and "commitment".
   - "path" may be a path to a PDF (absolute or relative). If relative, it's resolved against cwd.
   - Only rows whose path ends with ".pdf" are processed.
Options:
  --csv         : input CSV path (required)
  --pdf-dir     : directory where PDFs live (default /home/masaaki/tuplenetwork/pdf)
  --cvs-dir     : directory where .te,v files live (default /srv/cvsroot/textfile)
  --backup-dir  : where to copy original .te,v before appending (optional)
  --dry-run     : do not write, only show actions
  --encoding    : csv encoding (default utf-8)
  --verbose
"""
from __future__ import annotations
import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

APPEND_HEADER = (
    "\n%%==== APPENDED COMMITMENT START ====\n"
    "%% appended_at: {ts}\n"
    "%% source_csv: {csv}\n"
    "%% source_pdf: {pdf}\n"
    "%%==== CONTENT START ====\n"
)
APPEND_FOOTER = "\n%%==== APPENDED COMMITMENT END ====\n"

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def backup_file(src: Path, backup_root: Path, verbose: bool=False):
    rel = src.name
    dest = backup_root / rel
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    if verbose:
        print(f"Backed up {src} -> {dest}")
    return dest

def append_to_texv(texv: Path, commitment: str, csv_name: str, pdf_path: str, dry_run: bool=False, verbose: bool=False):
    ts = datetime.utcnow().isoformat() + "Z"
    header = APPEND_HEADER.format(ts=ts, csv=csv_name, pdf=pdf_path)
    footer = APPEND_FOOTER
    content = commitment if isinstance(commitment, str) else str(commitment)
    if not content.endswith("\n"):
        content += "\n"
    block = (header + content + footer).encode("utf-8", errors="replace")
    if dry_run:
        if verbose:
            print(f"[DRY-RUN] Would append {len(block)} bytes to {texv}")
        return
    with open(texv, "ab") as f:
        f.write(block)
    if verbose:
        print(f"Appended to {texv} ({len(block)} bytes)")

def process_csv(csv_path: Path, pdf_dir: Path, cvs_dir: Path, backup_dir: Optional[Path],
                dry_run: bool, encoding: str, verbose: bool):
    if backup_dir:
        ensure_dir(backup_dir)
    with csv_path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise SystemExit("Input CSV has no header")
        if "path" not in reader.fieldnames or "commitment" not in reader.fieldnames:
            raise SystemExit("CSV must contain 'path' and 'commitment' columns")
        count = 0
        for row in reader:
            pdf_path_raw = row.get("path", "").strip()
            if not pdf_path_raw:
                if verbose:
                    print("Skipping row with empty path")
                continue
            if not pdf_path_raw.lower().endswith(".pdf"):
                if verbose:
                    print(f"Skipping {pdf_path_raw}: not a .pdf")
                continue
            commitment = row.get("commitment", "")
            # Resolve pdf path: if absolute use it, else try to find under pdf_dir or as given
            pdf_p = Path(pdf_path_raw)
            if not pdf_p.is_absolute():
                candidate = pdf_dir / pdf_p.name
                if candidate.exists():
                    pdf_p = candidate
                else:
                    # try relative to cwd
                    pdf_p = pdf_p.resolve()
            if not pdf_p.exists():
                print(f"Warning: PDF not found: {pdf_p}", file=sys.stderr)
                # still attempt mapping by basename to cvs
            basename = pdf_p.stem  # removes final .pdf
            # Map to cvs tex,v path
            texv_name = basename + ".te,v"
            texv_path = cvs_dir / texv_name
            if not texv_path.exists():
                print(f"Warning: target .te,v not found for PDF {pdf_p} -> {texv_path}", file=sys.stderr)
                continue
            # backup if requested
            if backup_dir:
                try:
                    backup_file(texv_path, backup_dir, verbose=verbose)
                except Exception as e:
                    print(f"Backup failed for {texv_path}: {e}", file=sys.stderr)
            try:
                append_to_texv(texv_path, commitment, csv_name=str(csv_path), pdf_path=str(pdf_p), dry_run=dry_run, verbose=verbose)
                count += 1
            except Exception as e:
                print(f"Error appending to {texv_path}: {e}", file=sys.stderr)
        if verbose:
            print(f"Processed {count} files from {csv_path}")

def parse_args():
    p = argparse.ArgumentParser(description="Append commitments from CSV into matching CVS .te,v files (basename of pdf -> .te,v).")
    p.add_argument("--csv", required=True, help="input CSV file (must have path and commitment columns)")
    p.add_argument("--pdf-dir", default="/home/masaaki/tuplenetwork/pdf", help="directory containing PDFs (default as requested)")
    p.add_argument("--cvs-dir", default="/srv/cvsroot/texlive", help="directory containing .te,v files (default as requested)")
    p.add_argument("--backup-dir", default=None, help="optional backup directory to copy original .te,v files")
    p.add_argument("--dry-run", action="store_true", help="do not write files, only print actions")
    p.add_argument("--encoding", default="utf-8", help="CSV encoding")
    p.add_argument("--verbose", action="store_true", help="verbose output")
    return p.parse_args()

def main():
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)
    pdf_dir = Path(args.pdf_dir)
    cvs_dir = Path(args.cvs_dir)
    backup_dir = Path(args.backup_dir) if args.backup_dir else None
    if not pdf_dir.exists() and args.verbose:
        print(f"Warning: PDF dir does not exist: {pdf_dir}", file=sys.stderr)
    if not cvs_dir.exists():
        print(f"CVS dir not found: {cvs_dir}", file=sys.stderr)
        sys.exit(2)
    process_csv(csv_path, pdf_dir, cvs_dir, backup_dir, dry_run=args.dry_run, encoding=args.encoding, verbose=args.verbose)

if __name__ == "__main__":
    main()
