#!/usr/bin/env python3
# map_tex_to_texv.py
# Map CSV rows (paths that end with .tex) to CVS RCS files (.tex,v) under /srv/cvsroot/pdf/
# and overwrite the .tex,v file contents with the CSV message text.
#
# Assumptions:
# - GitHub local root: /home/masaaki/tuplenotwork/pdf
# - CVS local root:    /srv/cvsroot/pdf
# - CSV has header and columns "path" and "message" (can be changed via args)
# - CSV path entries reference .tex (not .tex,v)
#
# Usage:
#  python3 map_tex_to_texv.py input.csv [--dry-run] [--backup] [--verbose]
#
from __future__ import annotations
import argparse
import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

GITHUB_ROOT = "/home/masaaki/tuplenotwork/pdf"
CVS_ROOT = "/srv/cvsroot/pdf"
ALLOWED_EXT = {".tex", ".v"}

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Input CSV file (with header).")
    p.add_argument("--github-root", default=GITHUB_ROOT)
    p.add_argument("--cvs-root", default=CVS_ROOT)
    p.add_argument("--path-col", default="path")
    p.add_argument("--msg-col", default="message")
    p.add_argument("--encoding", default="utf-8")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--backup", action="store_true")
    p.add_argument("--allow-search", action="store_true",
                   help="If direct mapping fails, search cvs-root for basename (may be slow).")
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
        print(f"[index] files indexed: {len(rel_index)}")
    return rel_index, base_index

def normalize_csv_path(raw: str, github_root: str, verbose: bool=False) -> str:
    if raw is None:
        return ""
    s = raw.strip()
    if s.startswith("\ufeff"):
        s = s.lstrip("\ufeff")
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    # remove trailing commas or CR
    s = s.rstrip(",，").replace("\r", "")
    # strip github_root if present
    gr = str(Path(github_root))
    if s.startswith(gr):
        s = s[len(gr):].lstrip("/\\")
    for prefix in ("tuplenotwork/pdf/", "tuplenotwork/", "pdf/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    return s.lstrip("/\\")

def find_texv_target(rel_index: Dict[str, Path], base_index: Dict[str, List[Path]],
                     normalized: str, cvs_root: str, allow_search: bool, verbose: bool=False) -> Optional[Path]:
    """
    Given normalized CSV path (typically 'dir/.../file.tex' or 'file.tex'),
    prefer to resolve to a .tex,v file in rel_index. Try order:
      1) exact relative '.../file.tex,v'
      2) same dir '.../file.tex,v' when normalized endswith .tex
      3) suffix match rel.endswith(normalized) with appended ',v'
      4) unique basename 'file.tex,v' in base_index
      5) optional search for basename 'file.tex' or 'file.tex,v' under cvs_root
    """
    candidates: List[Path] = []

    # Normalize ensures no trailing ,v. target we want is .tex,v
    if normalized.endswith(",v"):
        normalized_no_v = normalized[:-2]
    else:
        normalized_no_v = normalized

    # candidate 1: exact rel with ,v
    rel_v = normalized_no_v + ",v"
    if rel_v in rel_index:
        if verbose: print(f"[match] exact .tex,v rel -> {rel_index[rel_v]}")
        return rel_index[rel_v]

    # candidate 2: if normalized itself is present and is a .tex,v in filesystem mapping
    # (some rel entries might store "dir/file.tex" as key even though file on disk is file.tex,v)
    if normalized_no_v in rel_index:
        p = rel_index[normalized_no_v]
        # check sibling .tex,v in same directory
        sibling_v = p.with_name(p.name + ",v") if not p.name.endswith(",v") else p
        if sibling_v.exists():
            if verbose: print(f"[match] sibling .tex,v -> {sibling_v}")
            return sibling_v
        # if indexed file itself endswith ',v' accept it
        if str(p).endswith(",v"):
            if verbose: print(f"[match] rel points to .tex,v -> {p}")
            return p

    # candidate 3: suffix matches with ,v
    suffix_candidates = [p for rel, p in rel_index.items() if rel.endswith(normalized_no_v + ",v")]
    if len(suffix_candidates) == 1:
        if verbose: print(f"[match] suffix unique -> {suffix_candidates[0]}")
        return suffix_candidates[0]
    if len(suffix_candidates) > 1:
        if verbose:
            print("[match] suffix ambiguous (multiple .tex,v):")
            for c in suffix_candidates: print("  ", c)
        return None

    # candidate 4: basename -> check for file.tex,v in base_index
    base = Path(normalized_no_v).name
    # consider basename with ,v appended
    base_v = base + ",v"
    if base_v in base_index and len(base_index[base_v]) == 1:
        if verbose: print(f"[match] basename .tex,v unique -> {base_index[base_v][0]}")
        return base_index[base_v][0]
    # if base (file.tex) exists uniquely, pick its sibling .tex,v if present
    if base in base_index:
        if len(base_index[base]) == 1:
            candidate = base_index[base][0]
            sibling_v = candidate.with_name(candidate.name + ",v")
            if sibling_v.exists():
                if verbose: print(f"[match] basename file.tex -> sibling .tex,v -> {sibling_v}")
                return sibling_v
            # maybe the indexed entry itself is .tex,v
            if str(candidate).endswith(",v"):
                return candidate
            else:
            # multiple file.tex candidates: try to find one whose rel endswith normalized_no_v
            for p in base_index[base]:
                try:
                    relp = str(p.relative_to(Path(cvs_root)))
                except Exception:
                    relp = str(p)
                if relp.endswith(normalized_no_v):
                    sibling_v = p.with_name(p.name + ",v")
                    if sibling_v.exists():
                        if verbose: print(f"[match] among baselist chosen -> {sibling_v}")
                        return sibling_v

    # candidate 5: allow_search: walk cvs_root for basename + ",v"
    if allow_search:
        if verbose: print(f"[search] walking {cvs_root} for {base_v} or {base}...")
        for root, _, files in os.walk(cvs_root):
            if base_v in files:
                return Path(root) / base_v
            if base in files:
                # prefer .tex,v but record if only .tex available
                candidate = Path(root) / base
                sibling_v = candidate.with_name(candidate.name + ",v")
                if sibling_v.exists():
                    return sibling_v
        if verbose: print("[search] none found")

    if verbose: print("[match] no candidate found for", normalized)
    return None

def atomic_write(path: Path, text: str, encoding: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_write_", dir=str(path.parent))
    try:
        with open(fd, "w", encoding=encoding) as f:
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
                print(f"row {i}: missing columns, skipping", file=sys.stderr); continue
            raw = row[args.path_col]
            msg = row[args.msg_col] or ""
            if not raw or raw.strip() == "":
                if args.verbose: print(f"row {i}: empty path, skipping"); continue

            normalized = normalize_csv_path(raw, args.github_root, verbose=args.verbose)
            if normalized == "":
                if args.verbose: print(f"row {i}: normalized empty, skipping"); continue

            # We expect CSV path to be .tex (not .tex,v). Ensure normalized endswith .tex or handle.
            # Strip trailing ,v if any just in case.
            if normalized.endswith(",v"):
                normalized = normalized[:-2]

            target = find_texv_target(rel_index, base_index, normalized, args.cvs_root, args.allow_search, args.verbose)
            if target is None:
                print(f"row {i}: mapping target not found for '{raw}' -> normalized '{normalized}', skipping", file=sys.stderr)
                continue

            if args.backup and target.exists():
                bak = target.with_suffix(target.suffix + ".bak") if not target.name.endswith(",v") else Path(str(target) + ".bak")
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
                    continue

if __name__ == "__main__":
    main()
