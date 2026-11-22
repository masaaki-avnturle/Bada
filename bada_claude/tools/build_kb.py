#!/usr/bin/env python3
"""
build_kb.py — BadaClaude の知識ベース (src/kb.json) を sources/*.pdf から生成する。

  pip install pypdf cffi
  python3 bada_claude/tools/build_kb.py

- contact_blueprint.pdf の「全方程式レジストリ (2111 本)」を 1 行 1 方程式として
  構造化する:  ID / 判定 (symb|calc|holds|differs) / タグ / 方程式 / 数値
- それ以外の論文・ソースは段落単位 (~600 字) のチャンクにする。
生成物は Bada で書かれた頭脳 (src/brain.bada) が起動時に索引化する。
"""
import json, os, re, sys, unicodedata
import pypdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "sources")
OUT = os.path.join(ROOT, "src", "kb.json")

DOCS = [
    ("contact_blueprint.pdf", "CONTACT TRANSPORTER 3次元設計図書 (全方程式レジストリ 2111 本)"),
    ("yamaguchi_framework_papers.pdf", "山口フレームワーク論文集 (リーマン予想・深リーマン予想・量子力学・一般相対性理論)"),
    ("beta_zeta_paper-2.pdf", "ベータ関数とゼータ関数の構造的対応"),
    ("bada-quantum-reviser-paper.pdf", "Reviser-Extensible Grammars: Q# 型量子フロントエンド"),
    ("bada-source-1.pdf", "Bada — The Unknown-Prior Engine Language (全ソース)"),
    ("BadaUltraNetwork-source.pdf", "Bada UltraNetwork — 全ソースコード"),
    ("BadaUFO_OS_paper.pdf", "BadaUFO-OS — 反重力 UFO オペレーティングシステム"),
    ("caostics.pdf", "Euler product estrade from Heisenberg Non-commutative"),
    ("pnp_zeromodes.pdf", "ゼロモードの数としての充足可能性と P ≠ NP 予想"),
    ("quantum_computer4.pdf", "Quantum Computer in a certain theorem"),
]

REG = re.compile(r"^([A-Z][A-Za-z0-9_]*\.\d+) (symb|calc|holds|differs) \[([A-Z, ]+)\](.*)$")


def fix(s):
    # PDF の CJK 部首互換文字 (⼭ 等) を通常の漢字へ。数式記号には触らない。
    out = []
    for ch in s:
        o = ord(ch)
        if 0x2E80 <= o <= 0x2FDF or 0xF900 <= o <= 0xFAFF:
            ch = unicodedata.normalize("NFKC", ch)
        out.append(ch)
    return "".join(out).replace(" ", " ")


def text_of(path):
    r = pypdf.PdfReader(path)
    return [fix(p.extract_text() or "") for p in r.pages]


def registry(pages):
    lines = "\n".join(pages).split("\n")
    rows, cur = [], None
    for raw in lines:
        line = raw.strip()
        m = REG.match(line)
        if m:
            if cur: rows.append(cur)
            cur = list(m.groups())
        elif cur and line and not line.startswith("4. 全方程式レジストリ") and not re.match(r"^\d+ / \d+$", line):
            cur[3] += " " + line
    if cur: rows.append(cur)
    eqs = []
    for rid, status, tags, body in rows:
        body = body.strip()
        value = ""
        mm = re.search(r"\s{3,}= (.*)$", body)
        if mm:
            value = mm.group(1).strip()
            body = body[: mm.start()].strip()
        eqs.append({
            "id": rid, "status": status,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "eq": body, "value": value,
        })
    return eqs


def chunks(pages, limit=600):
    out, buf, page_of = [], "", 1
    for pi, p in enumerate(pages, 1):
        for line in p.split("\n"):
            s = line.strip()
            if not s or re.fullmatch(r"\d+", s) or re.fullmatch(r"\d+ / \d+", s):
                continue
            if s.startswith("Generated source listing"):
                continue
            if not buf: page_of = pi
            buf += (s if not buf else ("\n" + s))
            if len(buf) >= limit and re.search(r"[。．.!?！？」)]$", s):
                out.append((page_of, buf)); buf = ""
            elif len(buf) >= limit * 1.6:
                out.append((page_of, buf)); buf = ""
    if buf.strip(): out.append((page_of, buf))
    return out


def main():
    kb = {"sources": [], "equations": [], "chunks": [], "blueprint": ""}
    for si, (fn, title) in enumerate(DOCS):
        path = os.path.join(SRC, fn)
        pages = text_of(path)
        kb["sources"].append({"id": si, "file": fn, "title": title, "pages": len(pages)})
        if fn == "contact_blueprint.pdf":
            kb["equations"] = registry(pages)
            head = "\n".join(pages[:2])
            kb["blueprint"] = head[: head.find("3. ゼータ多様体")].strip() if "3. ゼータ多様体" in head else head[:2500]
            continue
        lim = 900 if "source" in fn.lower() else 600
        for page, c in chunks(pages, lim):
            kb["chunks"].append({"src": si, "page": page, "text": c})
    # UltraNetwork の全ソースは巨大なので先頭 (設計・コア) に絞る
    un = [i for i, d in enumerate(DOCS) if d[0].startswith("BadaUltraNetwork")][0]
    keep, n = [], 0
    for c in kb["chunks"]:
        if c["src"] == un:
            n += 1
            if n > 60: continue
        keep.append(c)
    kb["chunks"] = keep
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, separators=(",", ":"))
    st = {}
    for e in kb["equations"]: st[e["status"]] = st.get(e["status"], 0) + 1
    print("equations:", len(kb["equations"]), st, "chunks:", len(kb["chunks"]),
          "bytes:", os.path.getsize(OUT), file=sys.stderr)


if __name__ == "__main__":
    main()
