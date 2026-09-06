了解しました。CSV のパスが GitHub 上のリポジトリ内パス（例: `tuplenotwork/pdf/sample.tex`）で与えられ、CVS 表示では `pdf/sample.tex` として扱いたいケースに対応するスクリプトを提示します。主な変換ルール：

- CSV のパスから先頭にあるリポジトリ名（既定: `tuplenotwork/`）を取り除く（オプションで別名指定可）。
- RCS 表示の `,v` サフィックスが付いている場合は除去してワーキングコピーの実ファイル名（`sample.tex`）にマップする。
- 対象拡張子は `.tex` と `.v` のみ許可。
- 安全な一時ファイル書き込み→置換。オプションで `.bak` バックアップ、オプションで `cvs commit` 実行。

保存例: csv_apply_map_tuplenotwork.py

```python
#!/usr/bin/env python3
# csv_apply_map_tuplenotwork.py
# Usage:
#   python3 csv_apply_map_tuplenotwork.py input.csv [--repo-prefix tuplenotwork/] [--path-col path] [--msg-col message] [--backup] [--cvs-commit]
import csv, sys, argparse, shutil, tempfile, subprocess
from pathlib import Path

ALLOWED_EXT = {'.tex', '.v'}

def parse_args():
    p = argparse.ArgumentParser(description="Apply CSV messages to .tex/.v files mapping GitHub path prefix to CVS working-copy path.")
    p.add_argument("csv", help="Input CSV file (with header)")
    p.add_argument("--repo-prefix", default="tuplenotwork/", help="Repo path prefix to strip from CSV paths (default: 'tuplenotwork/'). If empty, nothing is stripped.")
    p.add_argument("--path-col", default="path", help="CSV column name for file path (default: path)")
    p.add_argument("--msg-col", default="message", help="CSV column name for message (default: message)")
    p.add_argument("--encoding", default="utf-8", help="File/CSV encoding (default: utf-8)")
    p.add_argument("--backup", action="store_true", help="Create a .bak backup before overwrite")
    p.add_argument("--cvs-commit", action="store_true", help="Run `cvs commit` for each modified file")
    p.add_argument("--commit-template", default="Update description for {file}", help="Template for cvs commit message")
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
            try: Path(tmp).unlink()
            except: pass

def cvs_commit(path: Path, msg: str):
    try:
        subprocess.run(["cvs", "commit", "-m", msg, str(path)], check=True)
        return True
    except FileNotFoundError:
        print("cvs command not found; skipping commit for", path, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print("cvs commit failed for", path, ":", e, file=sys.stderr)
    return False

def map_csv_path_to_wc(raw: str, repo_prefix: str) -> Path:
    """
    Map CSV path (possibly like 'tuplenotwork/pdf/sample.tex' or 'pdf/sample.tex,v')
    to working-copy path 'pdf/sample.tex'.
    """
    if raw is None:
        return None
    p = raw.strip()
    if not p:
        return None
    # strip ,v suffix if present
    if p.endswith(",v"):
        p = p[:-2]
    # strip repo prefix if configured and present
    if repo_prefix and p.startswith(repo_prefix):
        p = p[len(repo_prefix):]
    return Path(p)

def main():
    args = parse_args()
    csvp = Path(args.csv)
    if not csvp.exists():
        print("CSV not found:", csvp, file=sys.stderr); sys.exit(2)

    with csvp.open(newline='', encoding=args.encoding) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header", file=sys.stderr); sys.exit(3)

        for i, row in enumerate(reader, start=1):
            if args.path_col not in row:
                print(f"row {i}: missing path column '{args.path_col}', skipping", file=sys.stderr); continue
            if args.msg_col not in row:
                print(f"row {i}: missing message column '{args.msg_col}', skipping", file=sys.stderr); continue

            raw = row[args.path_col]
            msg = row[args.msg_col] or ""
            if raw is None:
                print(f"row {i}: empty path, skipping", file=sys.stderr); continue

            target = map_csv_path_to_wc(raw, args.repo_prefix)
            if target is None:
                print(f"row {i}: cannot map path '{raw}', skipping", file=sys.stderr); continue

            if not target.exists():
                print(f"row {i}: target not found in working copy: {target}, skipping", file=sys.stderr); continue
            if not target.is_file():
                print(f"row {i}: target not a file: {target}, skipping", file=sys.stderr); continue
            if target.suffix.lower() not in ALLOWED_EXT:
                print(f"row {i}: skipped (extension not .tex/.v): {target}", file=sys.stderr); continue

            if args.backup:
                bak = target.with_suffix(target.suffix + ".bak")
                try:
                    shutil.copy2(target, bak)
                except Exception as e:
                    print(f"warning: backup failed for {target}: {e}", file=sys.stderr)

            content = msg.replace('\r\n','\n').replace('\r','\n')
            try:
                atomic_write(target, content, encoding=args.encoding)
                print(f"WROTE: {target}")
            except Exception as e:
                print(f"row {i}: write failed for {target}: {e}", file=sys.stderr)
                continue

            if args.cvs_commit:
                cvs_msg = args.commit_template.format(file=str(target))
                cvs_commit(target, cvs_msg)

if __name__ == "__main__":
    main()
```

使い方の例
- 標準（repo-prefix デフォルト tuplenotwork/ を使う）:
  python3 csv_apply_map_tuplenotwork.py input.csv --backup
- 別のプレフィックスを使う:
  python3 csv_apply_map_tuplenotwork.py input.csv --repo-prefix "otherrepo/"

注意
- CSV のパスが必ずワーキングコピー上に対応ファイルとして存在する必要があります。存在しない場合はスキップします。
- まずは少数の行で --backup を付けて動作を確認してください。自動コミットは慎重に。
