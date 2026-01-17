#!/usr/bin/env python3
import argparse
import csv
import os
import subprocess
from pathlib import Path

def git_toplevel(path):
    try:
        res = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        return Path(res.stdout.strip())
    except subprocess.CalledProcessError:
        return None

def last_commit_message(repo_root, rel_path):
    # rel_path: path relative to repo_root
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-n", "1", "--pretty=%B", "--", str(rel_path)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def collect_files(target_dir):
    files = []
    for p in Path(target_dir).rglob("*"):
        if p.is_file():
            files.append(p)
    return sorted(files)

def main():
    parser = argparse.ArgumentParser(description="Scan git commit messages for files under a directory and output CSV (filename,comment).")
    parser.add_argument("-d", "--dir", required=True, help="Target directory to scan (must be inside a git repo).")
    parser.add_argument("-out", "--output", required=True, help="Output CSV file path.")
    args = parser.parse_args()

    target = Path(args.dir).resolve()
    if not target.exists() or not target.is_dir():
        raise SystemExit(f"Target directory not found: {target}")

    repo_root = git_toplevel(target)
    if repo_root is None:
        raise SystemExit(f"Directory is not inside a git repository: {target}")

    files = collect_files(target)
    if not files:
        print("No files found under:", target)

    with open(args.output, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        # No header to match prior examples; each row: filename, comment
        for f in files:
            rel = f.relative_to(repo_root)
            msg = last_commit_message(repo_root, rel)
            # normalize comment into single-line by replacing newlines with '\n' or space
            if msg:
                msg_one = msg.replace("\r\n", "\n").replace("\n", "\\n")
            else:
                msg_one = ""
            # Write path relative to the target directory (not repo root), to match user's likely expectation
            path_rel_to_target = str(f.relative_to(target))
            writer.writerow([path_rel_to_target, msg_one])

    print("Wrote comments to", args.output)

if __name__ == "__main__":
    main()
