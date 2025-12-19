from typing import Optional
from pathlib import Path
import os

def map_csv_path_to_target(raw_path: str, repo_prefix: str, cvs_root: str, allow_search: bool = True, verbose: bool = True) -> Optional[Path]:
    """
    Try multiple normalizations to map CSV path -> actual file under cvs_root.
    - strip trailing ',v'
    - strip repo_prefix if present
    - remove leading '/'
    - try raw, with prefix stripped, with/without leading components
    - optionally, if none match and allow_search True, walk cvs_root to find a filename match
    Returns Path if found, otherwise None.
    """
    if raw_path is None:
        if verbose: print("map: raw_path is None")
        return None

    p = raw_path.strip()
    if verbose:
        print(f"map: raw='{raw_path}' -> stripped='{p}'")

    if not p:
        if verbose: print("map: empty after strip")
        return None

    # remove trailing ",v"
    if p.endswith(",v"):
        p = p[:-2]
        if verbose: print(f"map: removed ',v' -> '{p}'")

    # helper to test candidate
    def test_candidate(candidate: str):
        # avoid absolute double slashes
        candidate = candidate.lstrip("/")
        full = Path(cvs_root) / Path(candidate)
        if verbose: print(f"map: testing candidate -> {full}")
        if full.exists() and full.is_file():
            return full
        return None

    # candidates to try in order
    candidates = []

    # 1) if starts with repo_prefix, strip it
    if repo_prefix and p.startswith(repo_prefix):
        candidates.append(p[len(repo_prefix):])
    # 2) try p as-is (relative to cvs_root)
    candidates.append(p)
    # 3) if p contains repo_prefix as a path segment anywhere, try removing first segment
    if repo_prefix:
        # also try removing only first path component if that matches repo name
        parts = p.split("/", 1)
        if len(parts) == 2 and parts[0] == repo_prefix.rstrip("/"):
            candidates.append(parts[1])

    # 4) try basename only (in case CSV path has extra dirs)
    candidates.append(Path(p).name)

    # dedupe while preserving order
    seen = set()
    uniq_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq_candidates.append(c)

    # test each candidate
    for c in uniq_candidates:
        found = test_candidate(c)
        if found:
            if verbose: print(f"map: matched {found}")
            return found

    # fallback: search cvs_root for a file with same basename (costly)
    if allow_search:
        target_basename = Path(p).name
        if verbose: print(f"map: no direct match, searching for basename '{target_basename}' under {cvs_root} (may be slow)")
        for root, dirs, files in os.walk(cvs_root):
            if target_basename in files:
                candidate = Path(root) / target_basename
                if verbose: print(f"map: found by search: {candidate}")
                return candidate

    if verbose: print("map: no match found")
    return None
