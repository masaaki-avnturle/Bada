#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Append commitment text from comment.csv into .tex,v files without overwriting.

Expect input CSV (comment.csv) with header containing at least:
  path,commitment

"path" may be relative to --repo (default: current dir). Only rows whose path endswith
".tex,v" (configurable) will be processed.

Options:
  --repo        : repository root to resolve relative paths (optional)
  --csv         : input CSV file (required)
  --backup-dir  : if provided, original files are copied there before append
  --ext         : target extension (default ".tex,v")
  --dry-run     : don't write files, just print actions
  --encoding    : CSV encoding (default utf-8)
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
    "%% original_path: {path}\n"
    "%% git_commit: {git_commit}\n"
    "%%==== CONTENT START ====\n"
)
APPEND_FOOTER = "\n%%==== APPENDED COMMITMENT END ====\n"

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def backup_file(src: Path, backup_root: Path, repo_root: Optional[Path], verbose: bool=False):
    if repo_root:
        try:
            rel = src.relative_to(repo_root)
        except Exception:
            rel = src.name
        else:
            rel = src.name
    dest = backup_root / rel
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    if verbose:
        print(f"Backed up {src} -> {dest}")
    return dest

def append_commitment_to_file(target: Path, commitment: str, csv_name: str, git_commit: str,
                              dry_run: bool=False, verbose: bool=False):
    ts = datetime.utcnow().isoformat() + "Z"
    header = APPEND_HEADER.format(ts=ts, csv=csv_name, path=str(target), git_commit=(git_commit or ""))
    footer = APPEND_FOOTER
    content = commitment if isinstance(commitment, str) else str(commitment)
    if not content.endswith("\n"):
        content += "\n"
    block = (header + content + footer).encode("utf-8", errors="replace")
    if dry_run:
        print(f"[DRY-RUN] Would append {len(block)} bytes to {target}")
        return
    with open(target, "ab") as f:
        f.write(block)
    if verbose:
        print(f"Appended commitment to {target} ({len(block)} bytes)")

def process_csv(csv_path: Path, repo_root: Optional[Path], ext: str,
                backup_dir: Optional[Path], dry_run: bool=False, encoding: str="utf-8", verbose: bool=False):
    if backup_dir:
        ensure_dir(backup_dir)
    with csv_path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("Input CSV has no header")
        if "path" not in reader.fieldnames or "commitment" not in reader.fieldnames:
            raise SystemExit("CSV must contain 'path' and 'commitment' columns")
        # optional git_commit column (from which commit was pushed)
        has_git = "git_commit" in reader.fieldnames
        count = 0
        for row in reader:
            pathval = row.get("path", "").strip()
            if not pathval:
                if verbose:
                    print("Skipping empty path row")
                continue
            commitment = row.get("commitment", "")
            git_commit = row.get("git_commit", "") if has_git else ""
            p = Path(pathval)
            if not p.is_absolute() and repo_root:
                p = (repo_root / p).resolve()
            else:
                p = p.resolve()
            if not p.exists():
                print(f"Warning: target not found: {p}", file=sys.stderr)
                continue
            if not p.name.endswith(ext):
                if verbose:
                    print(f"Skipping {p}: does not end with {ext}")
                continue
            if backup_dir:
                try:
                    backup_file(p, backup_dir, repo_root, verbose=verbose)
                except Exception as e:
                    print(f"Backup failed for {p}: {e}", file=sys.stderr)
            try:
                append_commitment_to_file(p, commitment, csv_name=str(csv_path), git_commit=git_commit, dry_run=dry_run, verbose=verbose)
                count += 1
            except Exception as e:
                print(f"Error appending to {p}: {e}", file=sys.stderr)
        if verbose:
            print(f"Processed {count} files from {csv_path}")

def parse_args():
    p = argparse.ArgumentParser(description="Append commitments from CSV into .tex,v files without overwriting.")
    p.add_argument("--repo", help="repo root to resolve relative paths (optional)", default=None)
    p.add_argument("--csv", required=True, help="input CSV file (must have path and commitment columns)")
    p.add_argument("--backup-dir", help="directory to copy backups before appending (optional)", default=None)
    p.add_argument("--ext", default=".tex,v", help="target extension to process (default .tex,v)")
    p.add_argument("--dry-run", action="store_true", help="do not write files, only print actions")
    p.add_argument("--encoding", default="utf-8", help="CSV encoding")
    p.add_argument("--verbose", action="store_true", help="verbose output")
    return p.parse_args()

def main():
    args = parse_args()
    repo_root = Path(args.repo).resolve() if args.repo else None
    if repo_root and not repo_root.exists():
        print(f"Repo root not found: {repo_root}", file=sys.stderr)
        sys.exit(2)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)
    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else None
    process_csv(csv_path, repo_root, args.ext, backup_dir, dry_run=args.dry_run, encoding=args.encoding, verbose=args.verbose)

if __name__ == "__main__":
    main()
