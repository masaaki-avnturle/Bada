#!/usr/bin/env python3
# append_commitment_to_texv.py
from __future__ import annotations
import argparse
import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_GITHUB_ROOT = "/home/masaaki/tuplenetwork/"
DEFAULT_CVS_ROOT = "/srv/cvsroot/tuplenetwork/"

def parse_args():
    p = argparse.ArgumentParser(description="Append CSV commitment text into CVS .tex,v files.")
    p.add_argument("csv", help="Input CSV file (header)")
    p.add_argument("--github-root", default=DEFAULT_GITHUB_ROOT, help="Local tuplenotwork/ root used in CSV paths.")
    p.add_argument("--cvs-root", default=DEFAULT_CVS_ROOT, help="CVS repository root (where .tex,v live).")
    p.add_argument("--path-col", default="path", help="CSV column name that contains the file path (.tex).")
    p.add_argument("--msg-col", default="commitment", help="CSV column name that contains the message to append.")
    p.add_argument("--encoding", default="utf-8", help="CSV and file encoding.")
    p.add_argument("--dry-run", action="store_true", help="Do not actually write files; show actions only.")
    p.add_argument("--backup", action="store_true", help="Make .bak copy of target before appending.")
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
    s = s.rstrip(",，")
    gr = str(Path(github_root))
    if gr and s.startswith(gr):
        s = s[len(gr):].lstrip("/\\")
        if verbose: print(f"[norm] stripped github_root -> {s!r}")
    for prefix in ("tuplenetwork/tuplenetst/", "tuplenetwork/", "tex/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            if verbose: print(f"[norm] stripped prefix {prefix} -> {s!r}")
            break
    return s.lstrip("/\\")

def find_texv_target(rel_index: Dict[str, Path], base_index: Dict[str, List[Path]],
                     normalized: str, cvs_root: str, allow_search: bool, verbose: bool=False) -> Optional[Path]:
    if normalized.endswith(",v"):
        normalized_no_v = normalized[:-2]
    else:
        normalized_no_v = normalized

    rel_v = normalized_no_v + ",v"
    if rel_v in rel_index:
        if verbose: print(f"[match] exact rel .tex,v -> {rel_index[rel_v]}")
        return rel_index[rel_v]

    if normalized_no_v in rel_index:
        p = rel_index[normalized_no_v]
        sibling_v = p.with_name(p.name + ",v") if not p.name.endswith(",v") else p
        if sibling_v.exists():
            if verbose: print(f"[match] sibling .tex,v -> {sibling_v}")
            return sibling_v
        if str(p).endswith(",v"):
            if verbose: print(f"[match] rel entry is .tex,v -> {p}")
            return p

    suffix_candidates = [p for rel, p in rel_index.items() if rel.endswith(normalized_no_v + ",v")]
    if len(suffix_candidates) == 1:
        if verbose: print(f"[match] unique suffix -> {suffix_candidates[0]}")
        return suffix_candidates[0]
    if len(suffix_candidates) > 1:
        if verbose:
            print("[match] ambiguous suffix candidates:")
            for c in suffix_candidates: print("  ", c)
        return None

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

def append_text(path: Path, text: str, encoding: str):
    # Ensure parent exists; open in append mode
    path.parent.mkdir(parents=True, exist_ok=True)
    # Append with a leading newline to separate from previous content
    with path.open("a", encoding=encoding, newline="") as f:
        f.write("\n")
        f.write(text)

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
                print(f"[dry-run] would append to {target} (len={len(content)})")
            else:
                try:
                    append_text(target, content, encoding=args.encoding)
                    print(f"APPENDED: {target}")
                except Exception as e:
                    print(f"row {i}: append failed for {target}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
