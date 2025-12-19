from pathlib import Path
import os, hashlib

def build_index(cvs_root):
    rel_index = {}     # rel_path -> fullpath
    base_index = {}    # basename -> [fullpath,...]
    for root, _, files in os.walk(cvs_root):
        for f in files:
            full = Path(root)/f
            rel = str(full.relative_to(cvs_root))
            rel_index[rel] = full
            base_index.setdefault(f, []).append(full)
    return rel_index, base_index

def choose_target(rel_index, base_index, csv_path, cvs_root):
    # normalize
    p = csv_path.strip()
    if p.endswith(",v"): p = p[:-2]
    if p.startswith("tuplenotwork/"): p = p.split("/",1)[1]
    p = p.lstrip("/")
    # 1: exact rel path
    if p in rel_index:
        return rel_index[p]
    # 2: basename
    b = Path(p).name
    cand = base_index.get(b, [])
    if len(cand)==1:
        return cand[0]
    if len(cand)>1:
        # ambiguous: prefer suffix match (path endswith p) 
        for c in cand:
            if str(c).endswith(p):
                return c
        # otherwise ambiguous — return None to signal manual handling
        return None
    # 3: no candidate
    return None
