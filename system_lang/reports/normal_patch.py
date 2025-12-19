def normalize_csv_path(raw: str, github_root: str, verbose: bool=False) -> str:
    if raw is None:
        return ""
    s = raw.strip()
    # remove common BOM
    if s.startswith("\ufeff"):
        s = s.lstrip("\ufeff")
        if verbose: print("[norm] removed BOM")
    # strip surrounding quotes
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
        if verbose: print("[norm] stripped surrounding quotes")
    # remove trailing ',v' or trailing commas (ascii or fullwidth)
    s = s.rstrip()
    for tail in (",v", ",V", ",", "，"):
        if s.endswith(tail):
            s = s[:-len(tail)].rstrip()
            if verbose: print(f"[norm] removed trailing '{tail}' -> {s!r}")
    # remove Windows CR if present
    s = s.replace("\r", "")
    # strip absolute github_root prefix if present
    gr = str(Path(github_root))
    if s.startswith(gr):
        s = s[len(gr):].lstrip("/\\")
        if verbose: print(f"[norm] stripped github_root prefix -> {s!r}")
    # strip common repo prefixes
    for prefix in ("tuplenotwork/pdfde/", "tuplenotwork/pdf/", "tuplenotwork/", "pdf/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            if verbose: print(f"[norm] stripped known prefix '{prefix}' -> {s!r}")
            break
    return s.lstrip("/\\")
