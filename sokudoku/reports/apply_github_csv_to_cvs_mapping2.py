#!/usr/bin/env python3
# apply_github_csv_to_cvs_mapping.py
# Map CSV rows (from GitHub commits) to CVS working files and overwrite them with CSV message text.
# Tailored paths:
#   GitHub local repo root: /home/masaaki/tuplenotwork/pdf/
#   CVS local repo root:    /srv/cvsroot/pdf/
#
# CSV must have a header and columns (defaults): "path" and "message".
# Usage example:
#   python3 apply_github_csv_to_cvs_mapping.py input.csv --dry-run --backup
#
# Features:
# - Normalize CSV path (strip leading repo prefix if present, drop trailing ",v")
# - Build index of CVS files (relative path -> fullpath, basename -> [paths])
# - Match by: exact relative path, suffix match, unique basename, content-hash match (optional)
# - Options: --dry-run, --backup, --cvs-commit, --allow-search (expensive)
# - Safe atomic write, optional cvs commit

from __future__ import annotations
import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

GITHUB_ROOT_DEFAULT = "/home/masaaki/tuplenetwork/tex"
CVS_ROOT_DEFAULT = "/srv/cvsroot/tuplenetwork"
ALLOWED_EXT = {".tex", ".v"}

def parse_args():
    p = argparse.ArgumentParser(description="Apply GitHub CSV messages to CVS files (mapping).")
    p.add_argument("csv", help="Input CSV file (with header).")
    p.add_argument("--github-root", default=GITHUB_ROOT_DEFAULT, help="GitHub local root (default as provided).")
    p.add_argument("--cvs-root", default=CVS_ROOT_DEFAULT, help="CVS local root (default as provided).")
    p.add_argument("--path-col", default="path", help="CSV column name for path (default: path).")
    p.add_argument("--msg-col", default="message", help="CSV column name for message (default: message).")
    p.add_argument("--encoding", default="utf-8", help="CSV and file encoding.")
    p.add_argument("--backup", action="store_true", help="Create .bak copy before overwrite.")
    p.add_argument("--dry-run", action="store_true", help="Don't write files; only show planned actions.")
    p.add_argument("--cvs-commit", action="store_true", help="Run `cvs commit` after writing (requires cvs client).")
    p.add_argument("--commit-template", default="Update from CSV for {file}", help="Template for cvs commit message.")
    p.add_argument("--allow-search", action="store_true", help="Allow expensive search/fuzzy matching under cvs-root.")
    p.add_argument("--verbose", action="store_true", help="Verbose logging.")
    return p.parse_args()

def build_cvs_index(cvs_root: str, verbose: bool=False) -> Tuple[Dict[str, Path], Dict[str, List[Path]]]:
    rel_index: Dict[str, Path] = {}
    base_index: Dict[str, List[Path]] = {}
    cvs_root_p = Path(cvs_root)
    if verbose: print(f"[index] walking cvs root: {cvs_root_p}")
    for root, _, files in os.walk(cvs_root):
        for fn in files:
            full = Path(root) / fn
            try:
                rel = str(full.relative_to(cvs_root_p))
            except Exception:
                rel = os.path.join(os.path.relpath(root, cvs_root), fn)
            rel_index[rel] = full
            base_index.setdefault(fn, []).append(full)
    if verbose:
        print(f"[index] built: {len(rel_index)} files, unique basenames: {len(base_index)}")
    return rel_index, base_index

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def normalize_csv_path(raw: str, github_root: str, verbose: bool=False) -> str:
    # raw may be like: "tuplenotwork/pdf/some/dir/file.tex" or "pdf/some/file.tex,v" or "some/file.tex"
    s = (raw or "").strip()
    if verbose: print(f"[norm] raw: {raw!r} -> strip -> {s!r}")
    if s.endswith(",v"):
        s = s[:-2]
        if verbose: print(f"[norm] removed ,v -> {s!r}")
    # If path is absolute or starts with github_root, make it relative to github_root
    gr = str(Path(github_root))
    if s.startswith(gr):
        s = s[len(gr):].lstrip("/\\")
        if verbose: print(f"[norm] stripped github_root prefix -> {s!r}")
    # If path starts with "tuplenotwork/" or "tuplenotwork/pdf/" strip common prefixes
    for prefix in ("tuplenetwork/tex/", "tuplenetwork/", ""):
        if s.startswith(prefix):
            s = s[len(prefix):]
            if verbose: print(f"[norm] stripped known prefix '{prefix}' -> {s!r}")
            break
    s = s.lstrip("/\\")
    return s

def find_target_for_csv_path(rel_index: Dict[str, Path], base_index: Dict[str, List[Path]],
                             normalized: str, cvs_root: str, allow_search: bool, verbose: bool=False) -> Optional[Path]:
    # 1) exact relative match
    if normalized in rel_index:
        if verbose: print(f"[match] exact rel match: {normalized} -> {rel_index[normalized]}")
        return rel_index[normalized]
    # 2) suffix match: some CSV paths include extra intermediate directories; prefer path endswith normalized
    candidates = []
    for rel, full in rel_index.items():
        if rel.endswith(normalized):
            candidates.append(full)
    if len(candidates) == 1:
        if verbose: print(f"[match] suffix unique match: {candidates[0]}")
        return candidates[0]
    if len(candidates) > 1:
        if verbose:
            print(f"[match] suffix ambiguous ({len(candidates)}): choosing none (log candidates).")
            for c in candidates: print(f"  cand: {c}")
        return None
    # 3) basename unique match
    base = Path(normalized).name
    baselist = base_index.get(base, [])
    if len(baselist) == 1:
        if verbose: print(f"[match] unique basename match: {baselist[0]}")
        return baselist[0]
    if len(baselist) > 1:
        # try suffix among them
        for p in baselist:
            if str(p).endswith(normalized):
                if verbose: print(f"[match] basename candidates -> suffix pick: {p}")
                return p
        if verbose:
            print(f"[match] basename ambiguous ({len(baselist)}), candidates:")
            for p in baselist: print(f"  {p}")
        return None
    # 4) optional search (walk) - expensive
    if allow_search:
        if verbose: print(f"[match] allow_search enabled, searching for basename {base} under {cvs_root} ...")
        for root, _, files in os.walk(cvs_root):
            if base in files:
                candidate = Path(root) / base
                if verbose: print(f"[match] found by search: {candidate}")
                return candidate
    if verbose: print("[match] no match found")
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

def cvs_commit(path: Path, msg: str, verbose: bool=False):
    try:
        subprocess.run(["cvs", "commit", "-m", msg, str(path)], check=True)
        if verbose: print(f"[cvs] committed {path}")
    except FileNotFoundError:
        print("[cvs] cvs command not found; skipping commit", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[cvs] cvs commit failed for {path}: {e}", file=sys.stderr)

def main():
    args = parse_args()
    csv_p = Path(args.csv)
    if not csv_p.exists():
        print("CSV not found:", csv_p, file=sys.stderr); sys.exit(2)

    rel_index, base_index = build_cvs_index(args.cvs_root, verbose=args.verbose)

    with csv_p.open(newline="", encoding=args.encoding) as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header", file=sys.stderr); sys.exit(3)

        for i, row in enumerate(reader, start=1):
            if args.path_col not in row or args.msg_col not in row:
                print(f"row {i}: missing required columns, skipping", file=sys.stderr)
                continue
            raw = row[args.path_col]
            msg = row[args.msg_col] or ""
            if not raw or raw.strip() == "":
                if args.verbose: print(f"row {i}: empty path, skipping")
                continue

            normalized = normalize_csv_path(raw, args.github_root, verbose=args.verbose)
            if normalized == "":
                if args.verbose: print(f"row {i}: normalized path empty, skipping")
                continue

            target = find_target_for_csv_path(rel_index, base_index, normalized, args.cvs_root, args.allow_search, args.verbose)
            if target is None:
                print(f"row {i}: no unique mapping for CSV path '{raw}' -> normalized '{normalized}', skipping", file=sys.stderr)
                continue

            if not target.exists() or not target.is_file():
                print(f"row {i}: target path resolved but missing or not a file: {target}, skipping", file=sys.stderr)
                continue

            if target.suffix.lower() not in ALLOWED_EXT:
                print(f"row {i}: target extension not allowed ({target.suffix}), skipping: {target}", file=sys.stderr)
                continue

            if args.backup and target.exists():
                bak = target.with_suffix(target.suffix + ".bak")
                try:
                    shutil.copy2(target, bak)
                    if args.verbose: print(f"[backup] {target} -> {bak}")
                except Exception as e:
                    print(f"row {i}: backup failed for {target}: {e}", file=sys.stderr)

            content = msg.replace("\r\n", "\n").replace("\r", "\n")
            if args.dry_run:
                print(f"[dry-run] would write to {target} (len={len(content)} bytes)")
            else:
                try:
                    atomic_write(target, content, encoding=args.encoding)
                    print(f"WROTE: {target}")
                except Exception as e:
                    print(f"row {i}: write failed for {target}: {e}", file=sys.stderr)
                    continue

                if args.cvs_commit:
                    commit_msg = args.commit_template.format(file=str(target))
                    cvs_commit(target, commit_msg, verbose=args.verbose)

if __name__ == "__main__":
    main()
