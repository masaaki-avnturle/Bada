#!/usr/bin/env python3
# apply_github_csv_to_cvs.py
# Read a CSV (header) extracted from GitHub commits and overwrite corresponding CVS working files.
# Maps GitHub local repo prefix (default "tuplenotwork/pdfde/") -> CVS filesystem root (default "/srv/cvsroot/pdf").
# CSV must contain columns for path and message (defaults: "path","message").
# Usage:
#   python3 apply_github_csv_to_cvs.py input.csv [--repo-prefix tuplenotwork/pdfde/] [--cvs-root /srv/cvsroot/pdf]
#       [--path-col path] [--msg-col message] [--backup] [--cvs-commit] [--encoding utf-8]

import csv
import argparse
import sys
import shutil
import tempfile
import subprocess
from typing import Optional
from pathlib import Path

ALLOWED_EXT = {'.tex', '.v'}

def parse_args():
    p = argparse.ArgumentParser(description="Map GitHub CSV rows to CVS working files and overwrite with message text.")
    p.add_argument("csv", help="Input CSV file (with header).")
    p.add_argument("--repo-prefix", default="tuplenotwork/pdfde/", help="Prefix in CSV paths to strip (default: 'tuplenotwork/pdfde/').")
    p.add_argument("--cvs-root", default="/srv/cvsroot/pdf", help="Filesystem path to CVS target directory (default: /srv/cvsroot/pdf).")
    p.add_argument("--path-col", default="path", help="CSV column name for file path (default: path).")
    p.add_argument("--msg-col", default="message", help="CSV column name for message (default: message).")
    p.add_argument("--encoding", default="utf-8", help="CSV and file encoding (default: utf-8).")
    p.add_argument("--backup", action="store_true", help="Create .bak backup of each target before overwrite.")
    p.add_argument("--cvs-commit", action="store_true", help="Run `cvs commit -m <msg> <file>` after overwrite.")
    p.add_argument("--commit-template", default="Update from CSV for {file}", help="Template for cvs commit message; use {file}.")
    return p.parse_args()

def atomic_write_text(path: Path, text: str, encoding: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_write_", dir=str(path.parent))
    try:
        with open(fd, "w", encoding=encoding) as f:
            f.write(text)
        Path(tmp).replace(path)
    finally:
        if Path(tmp).exists():
            try: Path(tmp).unlink()
            except: pass

def cvs_commit(path: Path, msg: str):
    try:
        subprocess.run(["cvs", "commit", "-m", msg, str(path)], check=True)
    except FileNotFoundError:
        print("cvs command not found; skipping commit for", path, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print("cvs commit failed for", path, ":", e, file=sys.stderr)

def map_csv_path_to_target(raw_path: str, repo_prefix: str, cvs_root: str) -> Optional[Path]:
    if raw_path is None:
        return None
    p = raw_path.strip()
    if not p:
        return None
    # remove trailing ",v" if present (RCS notation)
    if p.endswith(",v"):
        p = p[:-2]
    # strip configured repo prefix if present
    if repo_prefix and p.startswith(repo_prefix):
        p = p[len(repo_prefix):]
    # remove leading slash if any
    if p.startswith("/"):
        p = p[1:]
    return Path(cvs_root) / Path(p)

def main():
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print("CSV not found:", csv_path, file=sys.stderr)
        sys.exit(2)

    with csv_path.open(newline="", encoding=args.encoding) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header", file=sys.stderr)
            sys.exit(3)

        for i, row in enumerate(reader, start=1):
            if args.path_col not in row:
                print(f"row {i}: missing path column '{args.path_col}', skipping", file=sys.stderr)
                continue
            if args.msg_col not in row:
                print(f"row {i}: missing message column '{args.msg_col}', skipping", file=sys.stderr)
                continue

            raw = row[args.path_col]
            message = row[args.msg_col] or ""
            if raw is None or raw.strip() == "":
                print(f"row {i}: empty path, skipping", file=sys.stderr)
                continue

            target = map_csv_path_to_target(raw, args.repo_prefix, args.cvs_root)
            if target is None:
                print(f"row {i}: cannot map path '{raw}', skipping", file=sys.stderr)
                continue

            if not target.exists():
                print(f"row {i}: mapped target not found: {target}, skipping", file=sys.stderr)
                continue
            if not target.is_file():
                print(f"row {i}: mapped target not a file: {target}, skipping", file=sys.stderr)
                continue
            if target.suffix.lower() not in ALLOWED_EXT:
                print(f"row {i}: skipping due to extension not in {ALLOWED_EXT}: {target}", file=sys.stderr)
                continue

            if args.backup:
                bak = target.with_suffix(target.suffix + ".bak")
                try:
                    shutil.copy2(target, bak)
                except Exception as e:
                    print(f"row {i}: backup failed for {target}: {e}", file=sys.stderr)

            # normalize line endings to LF
            content = message.replace("\r\n", "\n").replace("\r", "\n")
            try:
                atomic_write_text(target, content, encoding=args.encoding)
                print(f"WROTE: {target}")
            except Exception as e:
                print(f"row {i}: write failed for {target}: {e}", file=sys.stderr)
                continue

            if args.cvs_commit:
                commit_msg = args.commit_template.format(file=str(target))
                cvs_commit(target, commit_msg)

if __name__ == "__main__":
    main()
