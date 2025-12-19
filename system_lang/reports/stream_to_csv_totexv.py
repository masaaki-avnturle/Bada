#!/usr/bin/env python3
import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

def run(cmd, cwd=None, env=None, check=True):
    res = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and res.returncode != 0:
        print("Command failed:", " ".join(cmd))
        print("stdout:", res.stdout)
        print("stderr:", res.stderr)
        raise SystemExit(res.returncode)
    return res

def parse_csv(csv_path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            if not r: 
                continue
            filename = r[0].strip()
            comment = r[1].strip() if len(r) > 1 else ""
            if filename:
                rows.append((filename, comment))
    return rows

def ensure_module_imported_dummy(cvsroot, module):
    # noop: assume module exists. If not, checkout will fail -> user should import beforehand.
    return

def append_comment_to_tex(tex_path, comment, timestamp=True):
    if not comment:
        return
    ts = ""
    if timestamp:
        ts = datetime.utcnow().isoformat() + "Z"
    # normalize comment to single-line with \n escapes
    c = comment.replace("\r\n", "\n").replace("\n", "\\n")
    block = "\n\n% ----- appended from comment.csv {} -----\n% {}\n".format(ts, c)
    with open(tex_path, "a", encoding="utf-8") as f:
        f.write(block)

def cvs_checkout(cvsroot, module, dest_dir):
    env = os.environ.copy()
    env["CVSROOT"] = cvsroot
    run(["cvs", "-d", cvsroot, "checkout", module], cwd=dest_dir, env=env)
    return Path(dest_dir) / module

def cvs_add_if_needed(work_mod_path, filepath):
    # filepath is Path inside work_mod_path
    env = os.environ.copy()
    env["CVSROOT"] = os.environ.get("CVSROOT", "")
    # check status
    rel = str(filepath.relative_to(work_mod_path))
    res = run(["cvs", "status", rel], cwd=work_mod_path, env=env, check=False)
    if "Status: Unknown" in res.stdout or "Status: ?" in res.stdout:
        run(["cvs", "add", rel], cwd=work_mod_path, env=env)

def cvs_commit(work_mod_path, message):
    env = os.environ.copy()
    env["CVSROOT"] = os.environ.get("CVSROOT", "")
    run(["cvs", "commit", "-m", message], cwd=work_mod_path, env=env)

def main():
    p = argparse.ArgumentParser(description="Append comments from CSV to .tex files in CVS module (checkout->edit->commit).")
    p.add_argument("-cvs", action="store_true", help="use cvs mode (ignored flag, kept for compatibility)")
    p.add_argument("-d", "--cvsroot", required=True, help="CVSROOT directory (e.g. /srv/cvsroot)")
    p.add_argument("module_path", help="Module path to operate on, e.g. tuplenetwork/tex/")
    p.add_argument("-m", "--csv", required=True, help="comment CSV file (filename,comment)")
    p.add_argument("-out", "--outdir", required=True, help="output working dir (module will be checked out here or target path relative to checkout)")
    p.add_argument("-renew", action="store_true", help="(noop) keep for compatibility; not used")
    p.add_argument("-repo", "--repo", help="local repo path (not used for writing, optional)")
    p.add_argument("-attachment", help="(ignored) pattern placeholder")
    args = p.parse_args()

    cvsroot = args.cvsroot
    module_path = args.module_path.strip("/")
    csv_path = args.csv
    outdir = Path(args.outdir).resolve()
    if not Path(csv_path).is_file():
        print("CSV not found:", csv_path); sys.exit(1)
    # ensure outdir exists
    outdir.mkdir(parents=True, exist_ok=True)

    # set CVSROOT env for subprocesses
    os.environ["CVSROOT"] = str(cvsroot)

    # parse CSV
    rows = parse_csv(csv_path)
    if not rows:
        print("No entries in CSV"); sys.exit(0)

    # checkout module
    tmpdir = tempfile.mkdtemp(prefix="cvs_work_")
    try:
        work_mod = cvs_checkout(cvsroot, module_path.split("/")[0], tmpdir)
        # if module_path includes subdirs, descend
        subpath_parts = module_path.split("/")[1:]
        for ppart in subpath_parts:
            if ppart == "": 
                continue
            work_mod = work_mod / ppart
        work_mod_path = work_mod
        work_mod_path.mkdir(parents=True, exist_ok=True)

        # For each CSV row: map pdf -> tex and append comment
        modified_any = False
        for fname, comment in rows:
            # map filename: replace .pdf with .tex if present, else add .tex
            base = fname
            if base.lower().endswith(".pdf"):
                texname = base[:-4] + ".tex"
            else:
                texname = base + ".tex"
            # target path relative to module tex dir: use basename or preserve subdirs if present in CSV
            target_rel = Path(texname)
            target_abs = work_mod_path / target_rel
            # ensure parent dirs exist
            target_abs.parent.mkdir(parents=True, exist_ok=True)
            # if file does not exist in checkout, create empty file first (so cvs can add it)
            if not target_abs.exists():
                target_abs.write_text("% auto-created .tex\n", encoding="utf-8")
            # append comment
            append_comment_to_tex(target_abs, comment)
            modified_any = True
            # cvs add if needed (paths relative to module root)
            module_root = Path(tmpdir) / module_path.split("/")[0]
            cvs_add_if_needed(module_root, target_abs)

        if modified_any:
            # commit with message
            commit_msg = "Append comments from {}".format(Path(csv_path).name)
            module_root = Path(tmpdir) / module_path.split("/")[0]
            cvs_commit(module_root, commit_msg)
            # copy resulting module tree to outdir (optional)
            dest = outdir / module_path.split("/")[0]
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(module_root, dest)
            print("Committed changes and copied working module to:", dest)
        else:
            print("No modifications made.")

        finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
