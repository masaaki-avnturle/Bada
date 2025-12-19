#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ---- 設定（ここを編集）----
SOURCE_ROOT = Path.cwd() # CSV が置かれているローカルディレクトリ
LOCAL_CVS_WORKDIR = Path("/srv/cvsroot/tuplenetst")   # CVS の作業コピー（module のルート）
COMMIT_MESSAGE = "Update CSV files from local tuplenotwork/pdf"
CSV_GLOB = "*.csv"
DRY_RUN = False   # True: cvs コマンドは実行せず表示のみ
# ----------------------------

def run(cmd, cwd=None, check=True):
    print("RUN:", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)

def is_managed_by_cvs(path: Path, cvs_workdir: Path) -> bool:
    # cvs status が成功かつ "Status:" を含む出力があれば管理下とみなす
    try:
        res = subprocess.run(["cvs", "status", str(path)], cwd=cvs_workdir,
                             capture_output=True, text=True, check=False)
        out = (res.stdout or "") + (res.stderr or "")
        return "Status:" in out and "No entry for" not in out
    except Exception:
        return False

def main():
    src = Path(SOURCE_ROOT)
    dst_root = Path(LOCAL_CVS_WORKDIR)

    if not src.exists() or not src.is_dir():
        print("Error: SOURCE_ROOT not found:", src, file=sys.stderr)
        sys.exit(1)
    if not dst_root.exists() or not dst_root.is_dir():
        print("Error: LOCAL_CVS_WORKDIR not found:", dst_root, file=sys.stderr)
        sys.exit(1)

    csv_files = list(src.rglob(CSV_GLOB))
    if not csv_files:
        print("No CSV files found in", src)
        return

    files_to_commit = []

    for s in csv_files:
        rel = s.relative_to(src)  # pdf 以下の相対パスを保持
        dst = dst_root.joinpath(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"Copy: {s} -> {dst}")
        shutil.copy2(s, dst)
        files_to_commit.append(dst)

    # cvs add 必要なものを追加
    for f in files_to_commit:
        managed = is_managed_by_cvs(f, dst_root)
        if not managed:
            print(f"cvs add {f}")
            if not DRY_RUN:
                try:
                    run(["cvs", "add", str(f)], cwd=dst_root)
                except subprocess.CalledProcessError as e:
                    print("cvs add failed for", f, ":", e, file=sys.stderr)
                    # 続行

    # commit
    commit_cmd = ["cvs", "commit", "-m", COMMIT_MESSAGE] + [str(p) for p in files_to_commit]
    if DRY_RUN:
        print("DRY RUN:", " ".join(commit_cmd))
    else:
        try:
            run(commit_cmd, cwd=dst_root)
            print("Commit finished.")
        except subprocess.CalledProcessError as e:
            print("cvs commit failed:", e, file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
