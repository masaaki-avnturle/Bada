以下は、CSV のパスをリポジトリパス → 実際のファイルパス（CVS リポジトリルートが `/srv/cvsroot/pdf` の下にあるケースを想定）にマップして、対応するワーキングコピー／リポジトリ内ファイルを上書きするスクリプトです。

主な処理
- CSV の path 列に "tuplenotwork/pdf/..." や "pdf/..."、あるいは RCS 表示の "sample.tex,v" が入っている想定。
- 先頭の repo プレフィックス（例: `tuplenotwork/`）を取り除き、残りを cvs-root ディレクトリ（デフォルト: `/srv/cvsroot/pdf`）以下のパスに結合してターゲットファイルを決定します。
- `,v` サフィックスは除去してワーキングファイル名（例: `sample.tex`）にマップします。
- 上書き対象拡張子は `.tex` と `.v`（`.v` はワーキングファイル名が `.v` のファイルをそのまま上書き）に限定。
- 安全な一時書き込み→リネーム。オプションで `.bak` バックアップ、オプションで `cvs commit` 実行。

保存例: csv_apply_map_cvsroot.py

使い方例:
python3 csv_apply_map_cvsroot.py input.csv --repo-prefix tuplenotwork/ --cvs-root /srv/cvsroot/pdf --backup --cvs-commit

スクリプト:
```python
#!/usr/bin/env python3
# csv_apply_map_cvsroot.py
# Usage example:
#   python3 csv_apply_map_cvsroot.py input.csv --repo-prefix tuplenotwork/ --cvs-root /srv/cvsroot/pdf --backup --cvs-commit

import csv
import sys
import argparse
import shutil
import tempfile
import subprocess
from pathlib import Path

ALLOWED_EXT = {'.tex', '.v'}

def parse_args():
    p = argparse.ArgumentParser(description="Apply CSV messages to files mapped into a CVS root directory (e.g. /srv/cvsroot/pdf).")
    p.add_argument("csv", help="Input CSV file (with header)")
    p.add_argument("--repo-prefix", default="tuplenotwork/", help="Strip this prefix from CSV paths if present (default: 'tuplenotwork/').")
    p.add_argument("--cvs-root", default="/srv/cvsroot/pdf", help="Base filesystem path for CVS repository (default: /srv/cvsroot/pdf)")
    p.add_argument("--path-col", default="path", help="CSV column name for file path (default: path)")
    p.add_argument("--msg-col", default="message", help="CSV column name for message (default: message)")
    p.add_argument("--encoding", default="utf-8", help="CSV and file encoding (default: utf-8)")
    p.add_argument("--backup", action="store_true", help="Create a .bak backup before overwrite")
    p.add_argument("--cvs-commit", action="store_true", help="Run `cvs commit` for each modified file (requires cvs client/config)")
    p.add_argument("--commit-template", default="Update file from CSV: {file}", help="Template for cvs commit message; use {file}")
    return p.parse_args()

def atomic_write(path: Path, text: str, encoding="utf-8"):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_write_", dir=str(path.parent))
    try:
        with open(fd, "w", encoding=encoding) as f:
            f.write(text)
        Path(tmp).replace(path)
    finally:
        if Path(tmp).exists():
            try:
                Path(tmp).unlink()
            except Exception:
                pass

def cvs_commit(path: Path, msg: str):
    try:
        subprocess.run(["cvs", "commit", "-m", msg, str(path)], check=True)
        return True
    except FileNotFoundError:
        print("cvs command not found; skipping commit for", path, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print("cvs commit failed for", path, ":", e, file=sys.stderr)
    return False

def map_csv_path(raw: str, repo_prefix: str, cvs_root: str) -> Path:
    """
    Map CSV path to filesystem path under cvs_root.
    - strip trailing ',v' if present
    - strip repo_prefix if configured and present
    - join with cvs_root
    """
    if raw is None:
        return None
    p = raw.strip()
    if not p:
        return None
    # remove trailing ',v' if present
    if p.endswith(",v"):
        p = p[:-2]
    # strip repo prefix
    if repo_prefix and p.startswith(repo_prefix):
        p = p[len(repo_prefix):]
    # remove any leading slash to avoid absolute join issues
    if p.startswith("/"):
        p = p[1:]
    return Path(cvs_root) / Path(p)

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
                print(f"row {i}: missing path column '{args.path_col}', skipping", file=sys.stderr)
                continue
            if args.msg_col not in row:
                print(f"row {i}: missing message column '{args.msg_col}', skipping", file=sys.stderr)
                continue

            raw = row[args.path_col]
            msg = row[args.msg_col] or ""
            if raw is None:
                print(f"row {i}: empty path, skipping", file=sys.stderr)
                continue

            target = map_csv_path(raw, args.repo_prefix, args.cvs_root)
            if target is None:
                print(f"row {i}: cannot map path '{raw}', skipping", file=sys.stderr)
                continue

            # If target not exist, try alternate: sometimes repo stores under 'CVSROOT' layout;
            # but we keep strict mapping and skip if not found.
            if not target.exists():
                print(f"row {i}: mapped target does not exist: {target}, skipping", file=sys.stderr)
                continue
            if not target.is_file():
                print(f"row {i}: mapped target is not a file: {target}, skipping", file=sys.stderr)
                continue

            # extension check
            if target.suffix.lower() not in ALLOWED_EXT:
                print(f"row {i}: skipped (extension not allowed): {target}", file=sys.stderr)
                continue

            # backup
            if args.backup:
                bak = target.with_suffix(target.suffix + ".bak")
                try:
                    shutil.copy2(target, bak)
                except Exception as e:
                    print(f"warning: backup failed for {target}: {e}", file=sys.stderr)

            # normalize line endings and write
            content = msg.replace('\r\n', '\n').replace('\r', '\n')
            try:
                atomic_write(target, content, encoding=args.encoding)
                print(f"WROTE: {target}")
            except Exception as e:
                print(f"row {i}: write failed for {target}: {e}", file=sys.stderr)
                continue

            if args.cvs_commit:
                commit_msg = args.commit_template.format(file=str(target))
                cvs_commit(target, commit_msg)

if __name__ == "__main__":
    main()
```

注意
- デフォルトの cvs-root は `/srv/cvsroot/pdf` に設定しています。実際の配置に合わせて `--cvs-root` を指定してください。
- このスクリプトは厳密にマッピングして存在するファイルのみ上書きします。存在しない場合はスキップします。
- 実行前に必ずバックアップを取り、まず少数行で動作確認してください。自動コミットは慎重に行ってください。
