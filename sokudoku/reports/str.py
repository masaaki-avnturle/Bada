以下は、GitHubから取得した `comment.csv` の各行に含まれる PDF ファイル名（例: `foo.pdf`）とコメントを読み取り、対応する CVS フォルダ `/srv/cvsroot/tuplenetwork` 内の同名ベース名で拡張子が `.tex,v` のファイルにコメントを追記する Python スクリプトです。

前提:
- `comment.csv` は少なくとも PDF のファイル名とコメントを含む。ヘッダがある場合、ヘッダ名は `filename` / `file` / `pdf`（ファイル名列）と `comment` / `message` / `note`（コメント列）のいずれかを想定。ヘッダがない場合は先頭列をファイル名、2列目をコメントとして扱います。
- 追記前に各ターゲットファイルのバックアップ（拡張子に `.bak` を付与）を作成します。

スクリプト:

```python
#!/usr/bin/env python3
# coding: utf-8

from pathlib import Path
import csv
import shutil
import sys

CSV_PATH = Path("comment.csv")                     # comment.csv のパス（変更可）
CVS_ROOT = Path("/srv/cvsroot/tuplenetwork")      # 対象 CVS フォルダ（変更可）
TARGET_EXT = ".tex,v"                              # 追加対象拡張子
BACKUP_SUFFIX = ".bak"                             # バックアップの追加 suffix
ENCODING = "utf-8"                                 # 必要に応じて変更（例: "shift_jis"）

# ヘッダ名候補
FILENAME_KEYS = {"filename", "file", "pdf", "name"}
COMMENT_KEYS = {"comment", "message", "note", "commentary"}

def detect_columns(header):
    header_l = [h.strip().lower() for h in header]
    file_idx = comment_idx = None
    for i, h in enumerate(header_l):
        if file_idx is None and h in FILENAME_KEYS:
            file_idx = i
        if comment_idx is None and h in COMMENT_KEYS:
            comment_idx = i
    return file_idx, comment_idx

def iterate_csv_rows(csv_path):
    with csv_path.open("r", encoding=ENCODING, newline='') as f:
        reader = csv.reader(f)
        try:
            first = next(reader)
        except StopIteration:
            return
        # 判定: ヘッダっぽければヘッダ扱い
        file_idx, comment_idx = detect_columns(first)
        if file_idx is None or comment_idx is None:
            # ヘッダ候補見つからない → treat first row as data: use 0 and 1
            yield first[0].strip(), (first[1].strip() if len(first) > 1 else "")
            for row in reader:
                if not row:
                    continue
                yield row[0].strip(), (row[1].strip() if len(row) > 1 else "")
            else:
            for row in reader:
                if not row:
                    continue
                fname = row[file_idx].strip() if file_idx < len(row) else ""
                comment = row[comment_idx].strip() if comment_idx < len(row) else ""
                yield fname, comment

def append_comment_to_target(basename, comment_text):
    # basename may include extension .pdf; remove extension and use stem
    name = Path(basename).stem
    target = CVS_ROOT / f"{name}{TARGET_EXT}"
    if not target.exists():
        print(f"Not found: {target}", file=sys.stderr)
        return False
    # backup
    bak = target.with_name(target.name + BACKUP_SUFFIX)
    try:
        shutil.copy2(target, bak)
    except Exception as e:
        print(f"Warning: backup failed for {target}: {e}", file=sys.stderr)
    # append with a clear separator
    separator = "\n\n# --- appended from comment.csv ---\n"
    try:
        with target.open("a", encoding=ENCODING, newline="") as tf:
            tf.write(separator)
            tf.write(comment_text)
            tf.write("\n")
        print(f"Appended to: {target}")
        return True
    except Exception as e:
        print(f"Error writing to {target}: {e}", file=sys.stderr)
        return False

def main():
    if not CSV_PATH.exists():
        print(f"CSV file not found: {CSV_PATH}", file=sys.stderr)
        return 1
    if not CVS_ROOT.exists():
        print(f"CVS root not found: {CVS_ROOT}", file=sys.stderr)
        return 1

    for pdfname, comment in iterate_csv_rows(CSV_PATH):
        if not pdfname:
            continue
        append_comment_to_target(pdfname, comment)

if __name__ == "__main__":
    sys.exit(main())
```

使い方：
- 必要なら `CSV_PATH`, `CVS_ROOT`, `ENCODING` を上部で変更してください。
- 実行前に必ずバックアップを取り、テスト環境で動作確認してください。
