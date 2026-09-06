以下は、`tuplenotwork/pdf/` から抽出した CSV（CSV のパス列は `.tex` を含む）にある説明文（デフォルト列名 `commitment`）を、対応する CVS リポジトリ内の RCS ファイル（`.tex,v`）へ書き込む Python スクリプトです。

主な仕様
- CSV はヘッダあり。CSV のパス列は `.tex`（例: `tuplenotwork/pdf/dir/file.tex` または `dir/file.tex` または `file.tex`）を想定。
- CSV 中の説明文カラム名はデフォルト `commitment`（オプションで変更可）。
- CSV のパスから `.tex,v` へマップする優先順:
  1. CSV の正規化した相対パスに対して該当する `.../file.tex,v` が存在するか確認
  2. 同ディレクトリの sibling `file.tex,v`
  3. 相対パスのサフィックス一致（ユニークなら採用）
  4. ベース名一意マッチ（`file.tex,v`）
  5. オプション `--allow-search` で CVS ルート配下を再帰検索
- 安全措置: `--dry-run`、`--backup`（既存ファイルを .bak にコピー）
- エンコーディング指定可（デフォルト UTF-8）
- ログは `--verbose`

保存例: `write_commitment_to_texv.py`

```python
#!/usr/bin/env python3
# write_commitment_to_texv.py
# Write CSV commitment text into corresponding CVS .tex,v files.
from __future__ import annotations
import argparse
import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_GITHUB_ROOT = "/home/masaaki/tuplenotwork/pdf"
DEFAULT_CVS_ROOT = "/srv/cvsroot/pdf"

def parse_args():
    p = argparse.ArgumentParser(description="Map CSV (paths .tex) -> CVS .tex,v and write commitment text.")
    p.add_argument("csv", help="Input CSV file (header).")
    p.add_argument("--github-root", default=DEFAULT_GITHUB_ROOT, help="Local tuplenotwork/pdf root used in CSV paths.")
    p.add_argument("--cvs-root", default=DEFAULT_CVS_ROOT, help="CVS repository root (where .tex,v live).")
    p.add_argument("--path-col", default="path", help="CSV column name that contains the file path (.tex).")
    p.add_argument("--msg-col", default="commitment", help="CSV column name that contains the message to write.")
    p.add_argument("--encoding", default="utf-8", help="CSV and file encoding.")
    p.add_argument("--dry-run", action="store_true", help="Do not actually write files; show actions only.")
    p.add_argument("--backup", action="store_true", help="Make .bak copy of target before writing.")
    p.add_argument("--allow-search", action="store_true", help="If mapping fails, search cvs-root for basename (may be slow).")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()

def build_index(cvs_root: str, verbose: bool=False) -> Tuple[Dict[str, Path], Dict[str, List[Path]]]:
    rel_index: Dict[str, Path] = {}
    base_index: Dict[str, List[Path]] = {}
    for root, _, files in os.walk(cvs_root):
        for fn in files:
            full = Path(root) / fn
            try:
                rel = str(full.relative_to(cvs_root))
            except Exception:
                rel = os.path.join(os.path.relpath(root, cvs_root), fn)
            rel_index[rel] = full
            base_index.setdefault(fn, []).append(full)
    if verbose:
        print(f"[index] indexed {len(rel_index)} files under {cvs_root}")
    return rel_index, base_index

def normalize_csv_path(raw: str, github_root: str, verbose: bool=False) -> str:
    if raw is None:
        return ""
    s = raw.strip()
    if s.startswith("\ufeff"):
        s = s.lstrip("\ufeff")
        if verbose: print("[norm] removed BOM")
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
        if verbose: print("[norm] stripped quotes")
    s = s.replace("\r", "")
    # remove trailing commas or fullwidth comma
    s = s.rstrip(",，")
    # strip github root or known prefixes if present
    gr = str(Path(github_root))
    if gr and s.startswith(gr):
        s = s[len(gr):].lstrip("/\\")
        if verbose: print(f"[norm] stripped github_root -> {s!r}")
    for prefix in ("tuplenotwork/pdf/", "tuplenotwork/", "pdf/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            if verbose: print(f"[norm] stripped prefix {prefix} -> {s!r}")
            break
    return s.lstrip("/\\")

def find_texv_target(rel_index: Dict[str, Path], base_index: Dict[str, List[Path]],
                     normalized: str, cvs_root: str, allow_search: bool, verbose: bool=False) -> Optional[Path]:
    """
    Map normalized CSV path (ends with .tex or basename) -> Path to .tex,v file in CVS.
    """
    if normalized.endswith(",v"):
        normalized_no_v = normalized[:-2]
    else:
        normalized_no_v = normalized

    # 1) exact relative .tex,v
    rel_v = normalized_no_v + ",v"
    if rel_v in rel_index:
        if verbose: print(f"[match] exact rel .tex,v -> {rel_index[rel_v]}")
        return rel_index[rel_v]

    # 2) if normalized_no_v exists in index, check for sibling .tex,v
    if normalized_no_v in rel_index:
        p = rel_index[normalized_no_v]
        sibling_v = p.with_name(p.name + ",v") if not p.name.endswith(",v") else p
        if sibling_v.exists():
            if verbose: print(f"[match] sibling .tex,v -> {sibling_v}")
            return sibling_v
        if str(p).endswith(",v"):
            if verbose: print(f"[match] rel entry is .tex,v -> {p}")
            return p

    # 3) suffix match for normalized_no_v + ",v"
    suffix_candidates = [p for rel, p in rel_index.items() if rel.endswith(normalized_no_v + ",v")]
    if len(suffix_candidates) == 1:
        if verbose: print(f"[match] unique suffix -> {suffix_candidates[0]}")
        return suffix_candidates[0]
    if len(suffix_candidates) > 1:
        if verbose:
            print("[match] ambiguous suffix candidates:")
            for c in suffix_candidates: print("  ", c)
        return None

    # 4) basename matching
    base = Path(normalized_no_v).name
    base_v = base + ",v"
    if base_v in base_index and len(base_index[base_v]) == 1:
        if verbose: print(f"[match] basename .tex,v unique -> {base_index[base_v][0]}")
        return base_index[base_v][0]

    if base in base_index:
        if len(base_index[base]) == 1:
            candidate = base_index[base][0]
            sibling_v = candidate.with_name(candidate.name + ",v")
            if sibling_v.exists():
                if verbose: print(f"[match] basename file.tex -> sibling .tex,v -> {sibling_v}")
                return sibling_v
            if str(candidate).endswith(",v"):
                if verbose: print(f"[match] basename candidate is .tex,v -> {candidate}")
                return candidate
            else:
            # multiple candidates: try to pick one whose rel endswith normalized_no_v
            for p in base_index[base]:
                try:
                    relp = str(p.relative_to(Path(cvs_root)))
                except Exception:
                    relp = str(p)
                if relp.endswith(normalized_no_v):
                    sibling_v = p.with_name(p.name + ",v")
                    if sibling_v.exists():
                        if verbose: print(f"[match] chosen among baselist -> {sibling_v}")
                        return sibling_v

    # 5) optional full search under cvs_root
    if allow_search:
        if verbose: print(f"[search] walking {cvs_root} for {base_v} or {base} ...")
        for root, _, files in os.walk(cvs_root):
            if base_v in files:
                return Path(root) / base_v
            if base in files:
                candidate = Path(root) / base
                sibling_v = candidate.with_name(candidate.name + ",v")
                if sibling_v.exists():
                    return sibling_v
        if verbose: print("[search] none found")

    if verbose: print(f"[match] no candidate for normalized='{normalized}'")
    return None

def atomic_write(path: Path, text: str, encoding: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_write_", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
        Path(tmp).replace(path)
    finally:
        try:
            if Path(tmp).exists():
                Path(tmp).unlink()
        except Exception:
            pass

def main():
    args = parse_args()
    csv_p = Path(args.csv)
    if not csv_p.exists():
        print("CSV not found:", csv_p, file=sys.stderr); sys.exit(2)

    rel_index, base_index = build_index(args.cvs_root, verbose=args.verbose)

    with csv_p.open(newline="", encoding=args.encoding) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header", file=sys.stderr); sys.exit(3)

        for i, row in enumerate(reader, start=1):
            if args.path_col not in row or args.msg_col not in row:
                print(f"row {i}: missing columns ('{args.path_col}'/'{args.msg_col}'), skipping", file=sys.stderr)
                continue
            raw = row[args.path_col]
            msg = row[args.msg_col] or ""
            if not raw or raw.strip() == "":
                if args.verbose: print(f"row {i}: empty path, skipping")
                continue

            normalized = normalize_csv_path(raw, args.github_root, verbose=args.verbose)
            if normalized.endswith(",v"):
                normalized = normalized[:-2]

            target = find_texv_target(rel_index, base_index, normalized, args.cvs_root, args.allow_search, args.verbose)
            if target is None:
                print(f"row {i}: mapping target not found for '{raw}' -> '{normalized}', skipping", file=sys.stderr)
                continue

            if args.backup and target.exists():
                bak = Path(str(target) + ".bak")
                try:
                    shutil.copy2(target, bak)
                    if args.verbose: print(f"[backup] {target} -> {bak}")
                except Exception as e:
                    print(f"row {i}: backup failed: {e}", file=sys.stderr)

            content = msg.replace("\r\n", "\n").replace("\r", "\n")
            if args.dry_run:
                print(f"[dry-run] would write to {target} (len={len(content)})")
            else:
                try:
                    atomic_write(target, content, encoding=args.encoding)
                    print(f"WROTE: {target}")
                except Exception as e:
                    print(f"row {i}: write failed for {target}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
```

使い方例
- まず dry-run で動作確認:
  python3 write_commitment_to_texv.py input.csv --dry-run --verbose
- 問題なければ実書き込み（バックアップ付き）:
  python3 write_commitment_to_texv.py input.csv --backup

注意
- RCS（`.tex,v`）ファイルの直接編集はリスクがあります。可能ならワーキングコピー（`.tex`）に書き込み + 通常の CVS コマンドでコミットする運用を推奨します。どうしても `.tex,v` を直接編集する場合は必ずバックアップを取ってください。
- CSV のパスやエンコーディングにより正規化が必要なら、実際のサンプル行を貼っていただければ normalize ロジックを調整します。

必要なら、CSV のサンプル（該当行）や実際の CVS パスを貼ってください。マッチングロジックをさらに調整します。
