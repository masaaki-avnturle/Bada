#!/usr/bin/env python3
"""Generate equations.bada (the full equation registry) from the extracted catalogs.

Inputs  (catalog dir): eq_*.md   — `- ID | equation | gloss | tags | CALC: ... / SYMB`
                       calc_*.tsv — `ID<TAB>bada-expression` (or SYMB)
                       helpers_*.bada
Output: equations.bada with helper functions and `def load_all_equations()`.
"""
import glob
import os
import re
import sys

TAGS = ["ROT", "SR", "GAMMA", "ZETA", "BETA", "JONES", "MANIFOLD",
        "QUANTUM", "TRANSPORT", "ENTROPY", "OTHER"]


def bada_str(s):
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + " ".join(s.split()) + '"'


def parse_catalog(path):
    entries = []
    paper = ""
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            paper = line[3:].strip()
            continue
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].rstrip("\n").split(" | ")]
        if len(parts) < 4:
            continue
        eid = parts[0]
        if not re.match(r"^[A-Za-z0-9_.\-]+$", eid):
            continue
        # fields are parsed from the right: `... | gloss | tags | CALC:/SYMB`
        # because an equation may itself contain " | ".
        k = len(parts) - 1
        while k > 1 and not (parts[k].startswith("CALC") or parts[k].startswith("SYMB")):
            k -= 1
        if k < 3:
            k = len(parts)  # no CALC/SYMB marker: treat all as eq/gloss/tags
        tail = parts[k] if k < len(parts) else ""
        tags_field, gloss = parts[k - 1], parts[k - 2]
        entries.append({
            "id": eid, "eq": " | ".join(parts[1:k - 2]), "gloss": gloss,
            "tags": [t for t in TAGS if re.search(r"\b" + t + r"\b", tags_field)] or ["OTHER"],
            "calc": tail.startswith("CALC"), "paper": paper,
        })
    return entries


def main(catdir, out):
    entries = []
    for f in sorted(glob.glob(os.path.join(catdir, "eq_*.md"))):
        entries += parse_catalog(f)
    calcs = {}
    for f in sorted(glob.glob(os.path.join(catdir, "calc_*.tsv"))):
        for line in open(f, encoding="utf-8"):
            if "\t" in line:
                k, v = line.rstrip("\n").split("\t", 1)
                calcs[k.strip()] = v.strip()
    helpers = []
    for f in sorted(glob.glob(os.path.join(catdir, "helpers_*.bada"))):
        helpers.append("# ---- " + os.path.basename(f) + "\n" + open(f, encoding="utf-8").read())

    seen = set()
    lines = []
    n_calc = n_symb = 0
    paper = None
    for e in entries:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        if e["paper"] != paper:
            paper = e["paper"]
            lines.append("  # ── " + paper)
        tags = "[" + ", ".join('"%s"' % t for t in e["tags"]) + "]"
        expr = calcs.get(e["id"])
        head = "%s, %s, %s, %s" % (bada_str(e["id"]), bada_str(e["eq"]), bada_str(e["gloss"]), tags)
        if e["calc"] and expr and expr != "SYMB":
            lines.append("  eq(%s, def() return %s end)" % (head, expr))
            n_calc += 1
        else:
            lines.append("  eqs(%s)" % head)
            n_symb += 1

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# ════════════════════════════════════════════════════════════════════\n")
        fh.write("#  equations.bada — 15 本の論文から抽出した全方程式のレジストリ (自動生成)\n")
        fh.write("#  生成: tools/gen_equations.py   数値評価 %d 本 / 記号 %d 本 / 計 %d 本\n" % (n_calc, n_symb, n_calc + n_symb))
        fh.write("# ════════════════════════════════════════════════════════════════════\n\n")
        fh.write("\n".join(helpers))
        fh.write("\n\ndef load_all_equations()\n")
        fh.write("\n".join(lines))
        fh.write("\nend\n")
    print("wrote %s: %d calc, %d symbolic, %d total" % (out, n_calc, n_symb, n_calc + n_symb))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
