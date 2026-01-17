下記スクリプトは、指定した CSV を読み込み、各行のファイルパスに対応するチェックアウト済みワーキングコピーのファイルを「説明文（CSV の message 列）」で上書きします。既存ファイルはバックアップ（拡張子 .bak）を作成し、安全に上書き（tmp ファイル→リネーム）します。必要なら `--cvs-commit` を付けると `cvs commit -m "<commit message>" <file>` を実行します（CVS クライアントが PATH にあること、作業ディレクトリが CVS ワークツリーであることが前提）。

保存例: csv_apply_descriptions.py

使い方例:
python3 csv_apply_descriptions.py input.csv
python3 csv_apply_descriptions.py input.csv --path-col path --msg-col message --backup --cvs-commit --commit-template "update description for {file}"

スクリプト:
```python
#!/usr/bin/env python3
# csv_apply_descriptions.py
# Overwrite checked-out files with descriptions from CSV.
# Usage: python3 csv_apply_descriptions.py input.csv [--path-col PATHCOL] [--msg-col MSGCOL]
#        [--backup] [--cvs-commit] [--commit-template "msg {file}"]

import csv
import sys
import argparse
import shutil
from pathlib import Path
import tempfile
import subprocess

def parse_args():
    p = argparse.ArgumentParser(description="Apply CSV messages to working-copy files (overwrite contents).")
    p.add_argument("csv", help="Input CSV file (with header)")
    p.add_argument("--path-col", default="path", help="CSV column name for file path (default: path)")
    p.add_argument("--msg-col", default="message", help="CSV column name for message (default: message)")
    p.add_argument("--encoding", default="utf-8", help="CSV and file encoding (default: utf-8)")
    p.add_argument("--backup", action="store_true", help="Create a .bak backup of original file before overwrite")
    p.add_argument("--cvs-commit", action="store_true", help="Run `cvs commit` for each modified file")
    p.add_argument("--commit-template", default="Update file content from CSV", help="Template for cvs commit message. Use {file} placeholder.")
    return p.parse_args()

def safe_write_text(path: Path, text: str, encoding="utf-8"):
    # atomic write via temp file then rename
    dirp = path.parent
    dirp.mkdir(parents=True, exist_ok=True)
    fd, tmpname = tempfile.mkstemp(prefix=".tmp_write_", dir=str(dirp))
    try:
        with open(fd, "w", encoding=encoding) as tmpf:
            tmpf.write(text)
        tmppath = Path(tmpname)
        tmppath.replace(path)
    finally:
        # in case of exception, ensure tmp removed
        if Path(tmpname).exists():
            try:
                Path(tmpname).unlink()
            except Exception:
                pass

def cvs_commit_file(path: Path, msg: str):
    # call cvs commit -m "msg" <file>
    try:
        subprocess.run(["cvs", "commit", "-m", msg, str(path)], check=True)
        return True
    except FileNotFoundError:
        print("cvs command not found; skipping commit for", path, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print("cvs commit failed for", path, ":", e, file=sys.stderr)
    return False

def main():
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print("CSV not found:", csv_path, file=sys.stderr)
        sys.exit(2)

    with csv_path.open(newline='', encoding=args.encoding) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header", file=sys.stderr)
            sys.exit(3)

        for i, row in enumerate(reader, start=1):
            if args.path_col not in row:
                print(f"CSV row {i}: missing path column '{args.path_col}', skipping", file=sys.stderr)
                continue
            if args.msg_col not in row:
                print(f"CSV row {i}: missing message column '{args.msg_col}', skipping", file=sys.stderr)
                continue

            relpath = row[args.path_col].strip()
            message = row[args.msg_col] or ""
            if not relpath:
                print(f"CSV row {i}: empty path, skipping", file=sys.stderr)
                continue

            target = Path(relpath)
            if not target.exists():
                print(f"CSV row {i}: target file does not exist: {target}, skipping", file=sys.stderr)
                continue
            if not target.is_file():
                print(f"CSV row {i}: target is not a file: {target}, skipping", file=sys.stderr)
                continue

            # backup
            if args.backup:
                bak = target.with_suffix(target.suffix + ".bak")
                try:
                    shutil.copy2(target, bak)
                except Exception as e:
                    print(f"Failed to backup {target} -> {bak}: {e}", file=sys.stderr)
                    # continue anyway

            # write message (overwrite)
            try:
                safe_write_text(target, message, encoding=args.encoding)
                print(f"Wrote: {target}")
            except Exception as e:
                print(f"Failed writing {target}: {e}", file=sys.stderr)
                continue

            # optional cvs commit
            if args.cvs_commit:
                commit_msg = args.commit_template.format(file=str(target))
                cvs_commit_file(target, commit_msg)

if __name__ == "__main__":
    main()
```

注意点（必ず確認してください）
- このスクリプトはファイル本体を上書きします。重要ファイルは必ずバックアップフラグ（--backup）を付けるか事前に別途バックアップを取ってください。
- CVS にコミットする場合、ユーザの CVS 環境（タグ、ロック、認証）が影響します。自動コミット前に手動で動作を確認してください。
- CSV のパスはスクリプトを実行するカレントディレクトリを基準に解決します（必要なら絶対パスにしてください）。
- 改行・エンコーディングに注意してください（デフォルト UTF-8）。必要に応じて --encoding を変更してください。

必要なら:
- 「CSV の message をファイルヘッダコメントとして挿入（既存内容は保持）」など別の動作にするバージョンを作ります。
