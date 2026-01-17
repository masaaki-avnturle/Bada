危険な操作注意: 直接 `,v` ファイルを編集するとリポジトリを壊す可能性があります。実行前に必ず `/srv/cvsroot` 全体のバックアップを取り、テスト環境で確認してください。以下は指定された動作を行う Python スクリプト例です（Python 3）。CSV はヘッダ無しで各行 `filename,comment`（filename は `.pdf` 名）と想定します。各行の PDF 名を `.tex` に変換し、対応する `*.tex,v` ファイルに末尾追記します。既存ファイルはバックアップ（同じ場所に `.bak.TIMESTAMP`）を作成します。

保存名: `stream_to_csv_totexv.py`

```python
#!/usr/bin/env python3
import argparse
import csv
import os
import shutil
import sys
import time
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Append comments from CSV into CVS ,v files (dangerous!).")
    p.add_argument("-cvs", action="store_true", help="compat flag")
    p.add_argument("-d", "--cvsroot", required=True, help="CVSROOT directory (e.g. /srv/cvsroot)")
    p.add_argument("module_path", help="Module path in repo, e.g. tuplenetwork/tex/")
    p.add_argument("-m", "--csv", required=True, help="comment CSV file (filename,comment)")
    p.add_argument("-out", "--out", required=True, help="output path (ignored for direct edit, kept for compatibility)")
    p.add_argument("-renew", action="store_true", help="compat flag")
    p.add_argument("-repo", "--repo", help="local repo path (not used)")
    p.add_argument("-attachment", help="compat flag")
    return p.parse_args()

def read_csv(csvpath):
    rows = []
    with open(csvpath, newline="", encoding="utf-8") as f:
        rdr = csv.reader(f)
        for r in rdr:
            if not r: 
                continue
            fname = r[0].strip()
            comment = r[1].strip() if len(r) > 1 else ""
            if fname:
                rows.append((fname, comment))
    return rows

def make_backup(vpath: Path):
    ts = time.strftime("%Y%m%d%H%M%S")
    bak = vpath.with_suffix(vpath.suffix + f".bak.{ts}")
    shutil.copy2(vpath, bak)
    return bak

def append_to_vfile(vpath: Path, pdf_name: str, comment: str):
    marker = f"\n\n# ----- appended from comment.csv ({pdf_name}) at {time.strftime('%Y-%m-%dT%H:%M:%SZ')} -----\n"
    # escape any NULs just in case
    append_text = marker + comment.replace("\0", "") + "\n"
    # write in binary to avoid encoding issues; convert to utf-8 bytes
    with open(vpath, "ab") as f:
        f.write(append_text.encode("utf-8"))
    return True

def main():
    args = parse_args()
    cvsroot = Path(args.cvsroot)
    if not cvsroot.is_dir():
        print("CVSROOT not found or not a directory:", cvsroot, file=sys.stderr)
        sys.exit(1)

    # Normalize module path under cvsroot
    mod = args.module_path.strip("/")
    # e.g. tuplenetwork/tex -> path under cvsroot
    mod_parts = mod.split("/")
    repo_mod_path = cvsroot.joinpath(*mod_parts)
    if not repo_mod_path.exists():
        print("Module path not found in CVSROOT:", repo_mod_path, file=sys.stderr)
        sys.exit(1)

    rows = read_csv(args.csv)
    if not rows:
        print("No rows found in CSV:", args.csv, file=sys.stderr)
        sys.exit(0)

    for pdf_name, comment in rows:
        # map pdf -> tex
        base = Path(pdf_name).name
        if base.lower().endswith(".pdf"):
            texname = base[:-4] + ".tex"
        else:
            texname = base + ".tex"
        vname = texname + ",v"
        vpath = repo_mod_path / vname

        if not vpath.exists():
            print(f"Warning: target ,v not found for {pdf_name} -> {vpath}", file=sys.stderr)
            continue

        try:
            bak = make_backup(vpath)
        except Exception as e:
            print(f"Error creating backup for {vpath}: {e}", file=sys.stderr)
            continue

        try:
            append_to_vfile(vpath, pdf_name, comment)
            print(f"Appended comment for {pdf_name} -> {vpath} (backup: {bak.name})")
        except Exception as e:
            print(f"Error appending to {vpath}: {e}", file=sys.stderr)
            # attempt to restore from backup
            try:
                shutil.copy2(bak, vpath)
                print(f"Restored from backup: {bak.name}", file=sys.stderr)
            except Exception as e2:
                print(f"Failed to restore backup {bak}: {e2}", file=sys.stderr)

if __name__ == "__main__":
    main()
```

使い方例:
- 実行前にバックアップを取得:
  sudo tar -czf /root/cvsroot-backup.tgz /srv/cvsroot
- 実行（パス等は環境に合わせて）:
  sudo python3 stream_to_csv_totexv.py -cvs -d /srv/cvsroot tuplenetwork/tex/ -m comment.csv -out tuplenetwork/tex/ -renew -repo /home/masaaki/tuplenetwork/pdf/ -attachment /srv/cvsroot tuplenetwork/tex

補足:
- スクリプトは直接 `,v` ファイル末尾に UTF-8 で追記します。RCS のフォーマットに依存した改変は行いませんが、それでもリポジトリ整合性を損なう恐れがあります。
- より安全な方法は `cvs checkout` → ワーキングコピーの `.tex` を編集 → `cvs commit` です。必要ならその版も提供します。
