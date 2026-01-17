こちらは、CVS の `.tex,v` ファイルを「上書きせずに追記（append）」するための Python スクリプトです。想定するユースケースは、既に抽出済みの CSV（各行に `path` と `commitment` 列がある）を読み、該当する `.tex,v` ファイルの末尾に「追記ブロック」を付け加えることで情報を保存するものです。ファイル全体を上書きせず、追記のみ行います。

注意
- `.tex,v` は RCS のリビジョンファイル形式です。直接追記することは RCS フォーマットを破壊する可能性があります。本スクリプトは単純にファイル末尾に追記ブロックを追加しますが、RCS の整合性が必要な場合は RCS コマンド（ci/co rcsコマンド等）を用いて適切に管理してください。
- 追記は「コメントブロック」として日時・ユーザー情報を付与します。必要に応じてフォーマットを変更してください。
- 実行前にリポジトリのバックアップを取ることを強く推奨します。

保存例: append_to_texv.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Append 'commitment' text into .tex,v files listed by CSV without overwriting.

CSV format: header line contains at least 'path' and 'commitment' columns.
'path' can be absolute or relative to --repo. Only rows whose path endswith '.tex,v'
(or user-specified ext) will be processed.

Usage:
  python3 append_to_texv.py --repo /path/to/repo --csv extracted.csv --outdir-backup backups
  python3 append_to_texv.py --csv extracted.csv --dry-run

Options:
  --repo            repository root to resolve relative paths (optional)
  --csv             input CSV (required)
  --encoding        csv encoding (default utf-8)
  --ext             target extension (default ".tex,v")
  --backup-dir      if provided, make backups (copy original files) under this dir before appending
  --dry-run         print actions without writing
  --verbose         show progress
"""
from __future__ import annotations
import argparse
import csv
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

APPEND_HEADER_TPL = (
    "\n%==== APPENDED COMMITMENT START ====\n"
    "% appended_at: {ts}\n"
    "% source_csv: {csv}\n"
    "% original_path: {path}\n"
    "%==== CONTENT START ====\n"
)
APPEND_FOOTER = "\n%==== APPENDED COMMITMENT END ====\n"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def backup_file(src: Path, backup_root: Path, repo_root: Optional[Path], verbose: bool=False):
    # recreate directory structure under backup_root
    rel = src if (not repo_root) else src.relative_to(repo_root)
    dest = backup_root / rel
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    if verbose:
        print(f"Backed up {src} -> {dest}")
    return dest

def append_to_file(texv_path: Path, content: str, csv_name: str, dry_run: bool=False, verbose: bool=False):
    ts = datetime.utcnow().isoformat() + "Z"
    header = APPEND_HEADER_TPL.format(ts=ts, csv=csv_name, path=str(texv_path))
    footer = APPEND_FOOTER
    # Wrap content to ensure no binary issues; convert to bytes using utf-8
    to_write = (header + content + footer).encode("utf-8", errors="replace")
    if dry_run:
        if verbose:
            print(f"[DRY-RUN] Would append {len(to_write)} bytes to {texv_path}")
        return
    # open in binary append mode
    try:
        with open(texv_path, "ab") as f:
            f.write(to_write)
        if verbose:
            print(f"Appended {len(to_write)} bytes to {texv_path}")
    except Exception as e:
        print(f"Error appending to {texv_path}: {e}", file=sys.stderr)

def process_csv(csv_path: Path, repo_root: Optional[Path], ext: str, backup_dir: Optional[Path],
                dry_run: bool=False, encoding: str="utf-8", verbose: bool=False):
    if backup_dir:
        ensure_dir(backup_dir)
    with csv_path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("Input CSV has no header")
        if "path" not in reader.fieldnames or "commitment" not in reader.fieldnames:
            raise SystemExit("CSV must contain 'path' and 'commitment' columns")
        rows_processed = 0
        for row in reader:
            pathval = row.get("path", "").strip()
            commitment = row.get("commitment", "")
            if not pathval:
                if verbose:
                    print("Skipping row with empty path")
                continue
            # resolve path
            p = Path(pathval)
            if not p.is_absolute() and repo_root:
                p = (repo_root / p).resolve()
            else:
                p = p.resolve()
            # filter by extension
            if not p.name.endswith(ext):
                if verbose:
                    print(f"Skipping {p} because it does not end with {ext}")
                continue
            if not p.exists():
                print(f"Warning: target file not found: {p}", file=sys.stderr)
                continue
            # backup if requested
            if backup_dir:
                try:
                    backup_file(p, backup_dir, repo_root, verbose=verbose)
                except Exception as e:
                    print(f"Backup failed for {p}: {e}", file=sys.stderr)
                    # continue anyway
            # prepare appended content (you may change formatting if desired)
            # ensure commitment ends with newline
            content = str(commitment)
            if not content.endswith("\n"):
                content = content + "\n"
            append_to_file(p, content, csv_name=str(csv_path), dry_run=dry_run, verbose=verbose)
            rows_processed += 1
    if verbose:
        print(f"Processed {rows_processed} rows from {csv_path}")

def parse_args():
    p = argparse.ArgumentParser(description="Append commitment values into .tex,v files (no overwrite).")
    p.add_argument("--repo", help="repo root to resolve relative paths", default=None)
    p.add_argument("--csv", required=True, help="input CSV path (must contain path and commitment columns)")
    p.add_argument("--encoding", default="utf-8", help="CSV encoding")
    p.add_argument("--ext", default=".tex,v", help="target extension to process (default .tex,v)")
    p.add_argument("--backup-dir", default=None, help="directory to store backups before appending")
    p.add_argument("--dry-run", action="store_true", help="do not write files, only print actions")
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
    if backup_dir and repo_root and not str(backup_dir).startswith(str(repo_root)):
        # allow backup dir outside repo, but just ensure it exists
        ensure_dir(backup_dir)
    process_csv(csv_path, repo_root, args.ext, backup_dir, dry_run=args.dry_run, encoding=args.encoding, verbose=args.verbose)

if __name__ == "__main__":
    main()
```

使い方例
- 実行（バックアップ付き）:
  python3 append_to_texv.py --repo /path/to/repo --csv extracted.csv --backup-dir /path/to/backups --verbose
- ドライラン（変更を加えない）:
  python3 append_to_texv.py --csv extracted.csv --dry-run --verbose

必要なら
- RCS（.tex,v）形式を壊さない形で「新しいリビジョン」を作る方法（RCS/ci コマンドを使う自動化スクリプト）を作成します。こちらは推奨される方法で、安全に履歴管理できます。希望しますか？
