#!/usr/bin/env python3
"""contact_blueprint.txt (PDF のテキスト抽出) → equations.json

PDF 「CONTACT TRANSPORTER 異次元への輸送機 3 次元設計図書」 の
第 4 章「全方程式レジストリ (2111 本)」を 1 本ずつの JSON レコードに変換する。

  {"id": "UFO.19", "status": "calc", "tags": ["TRANSPORT"],
   "expr": "a = (L − 1)·g_eff, ...", "value": "11.047"}

status: symb (記号式) / calc (数値評価) / holds (等式成立) / differs (不成立)

テキストの再生成 (任意 / PyMuPDF が必要):
  python3 -c "import fitz; d=fitz.open('contact_blueprint.pdf'); ..."
"""
import json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "contact_blueprint.txt")
DST = os.path.join(HERE, "..", "data", "equations.json")

ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*\.[0-9]+$")
STATUS = {"symb", "calc", "holds", "differs"}


def main():
    lines = open(SRC, encoding="utf-8").read().splitlines()
    recs, cur = [], None
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if ID_RE.match(ln) and nxt in STATUS:
            cur = {"id": ln, "status": nxt, "tags": [], "body": []}
            recs.append(cur)
            i += 2
            continue
        if ln.startswith("=== PAGE") or ln.startswith("4. 全方程式レジストリ"):
            i += 1
            continue
        if cur is not None and ln:
            if not cur["tags"] and not cur["body"] and ln.startswith("["):
                cur["tags"] = [t.strip() for t in ln.strip("[]").split(",") if t.strip()]
            else:
                cur["body"].append(ln)
        i += 1

    out = []
    for r in recs:
        text = " ".join(r["body"])
        m = re.search(r"^(.*)\s{4}=\s(.*)$", text)
        expr, value = (m.group(1), m.group(2)) if (m and r["status"] != "symb") else (text, "")
        out.append({"id": r["id"], "status": r["status"], "tags": r["tags"],
                    "expr": expr.strip(), "value": value.strip()})

    json.dump(out, open(DST, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    cnt = {s: sum(1 for o in out if o["status"] == s) for s in STATUS}
    print(f"{len(out)} equations -> {DST}  {cnt}")
    if len(out) != 2111:
        sys.exit("expected 2111 equations")


if __name__ == "__main__":
    main()
