#!/usr/bin/env python3
# coding: utf-8

import csv
import argparse
import os
import shutil
from datetime import datetime

DEFAULT_CSV = "/home/masaaki/tuplenetwork/pdf/data.csv"
TARGET_ROOT = "/srv/cvsroot/tuplenetwork"

def ensure_dir_for(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def backup_file(path, backup_root):
    if not os.path.exists(path):
        return
    os.makedirs(backup_root, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base = os.path.basename(path)
    shutil.copy2(path, os.path.join(backup_root, f"{base}.{stamp}.bak"))

def append_text(path, text):
    ensure_dir_for(path)
    # バイナリで扱わずテキスト追記（必要ならバイナリモードに変更）
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)

def process(csv_path, target_root, create_missing=False, backup=False,
            backup_root="/tmp/tuplenetwork_backups", filename_col="filename", content_col="content"):
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=1):
            if filename_col not in row or content_col not in row:
                raise ValueError(f"CSV must contain columns '{filename_col}' and '{content_col}'")
            name = row[filename_col].strip()
            content = row[content_col]
            if not name:
                print(f"[warn] row {i}: empty filename — skipped")
                continue

            # ターゲットは "ファイル名.tex,v"
            target = os.path.join(target_root, name + ".tex,v")
            if os.path.exists(target):
                if backup:
                    backup_file(target, backup_root)
                append_text(target, content)
                print(f"[ok] appended to {target}")
            else:
                if create_missing:
                    append_text(target, content)
                    print(f"[created] {target} and appended")
                else:
                    print(f"[skip] not found: {target}")

def main():
    p = argparse.ArgumentParser(description="Append CSV content to files named 'filename.tex,v' under target root")
    p.add_argument("--csv", default=DEFAULT_CSV, help="入力CSVファイル (default: %(default)s)")
    p.add_argument("--target-root", default=TARGET_ROOT, help="ターゲットルート (default: %(default)s)")
    p.add_argument("--create-missing", action="store_true", help="対象ファイルがなければ新規作成して追記する")
    p.add_argument("--backup", action="store_true", help="追記前にバックアップを作る")
    p.add_argument("--backup-root", default="/tmp/tuplenetwork_backups", help="バックアップ保存先")
    p.add_argument("--filename-col", default="filename", help="CSV のファイル名カラム (default: filename)")
    p.add_argument("--content-col", default="content", help="CSV の内容カラム (default: content)")
    args = p.parse_args()

    process(
        csv_path=args.csv,
        target_root=args.target_root,
        create_missing=args.create_missing,
        backup=args.backup,
        backup_root=args.backup_root,
        filename_col=args.filename_col,
        content_col=args.content_col
    )

if __name__ == "__main__":
    main()
