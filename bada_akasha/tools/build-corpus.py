#!/usr/bin/env python3
"""build-corpus.py — 論文集 PDF から BadaGPT の検索コーパス (src/corpus.json) を作る

    python3 bada_akasha/tools/build-corpus.py <pdf> [<pdf> ...]

各ページのテキストを約 480 文字の段落に切り、[文書番号, ページ, 本文] で保存します。
アプリはこの JSON を index.html に埋め込み、オフラインで検索します。
(要 pypdf。生成済みの corpus.json はリポジトリに同梱しています)
"""
import json, os, re, sys, unicodedata
sys.modules.setdefault("cryptography", None)   # 暗号化されていない PDF には不要
import pypdf

CHUNK = 480

def clean(t):
    t = unicodedata.normalize("NFKC", t)             # ⾯ (部首) → 面 など
    t = "\n".join(l for l in t.split("\n") if not re.fullmatch(r"\s*\d{1,4}\s*", l))  # コード行番号
    t = t.replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()

def chunks(text):
    lines, buf, out = text.split("\n"), "", []
    for ln in lines:
        if len(buf) + len(ln) + 1 > CHUNK and buf:
            out.append(buf.strip()); buf = ""
        buf += ln + "\n"
    if buf.strip():
        out.append(buf.strip())
    return [c for c in out if len(c) >= 40]

def main(paths):
    docs, passages = [], []
    for path in sorted(paths, key=lambda p: re.sub(r"^[0-9a-f]{8}-", "", os.path.basename(p)).lower()):
        name = re.sub(r"^[0-9a-f]{8}-", "", os.path.basename(path))[:-4]
        r = pypdf.PdfReader(path)
        pages = [clean(p.extract_text() or "") for p in r.pages]
        first = next((l for l in pages[0].split("\n") if len(l.strip()) > 3), name) if pages else name
        di = len(docs)
        docs.append({"file": name, "title": first.strip()[:90], "pages": len(pages)})
        for pi, pg in enumerate(pages):
            for c in chunks(pg):
                passages.append([di, pi + 1, c])
    out = os.path.join(os.path.dirname(__file__), "..", "src", "corpus.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"docs": docs, "passages": passages}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(docs)} docs, {len(passages)} passages -> {os.path.normpath(out)} ({os.path.getsize(out)} bytes)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1:])
