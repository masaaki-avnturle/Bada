#!/usr/bin/env python3
"""NCBI から参照ミトコンドリアゲノムを取得し www/refs.js を生成する。

  イヌ  Canis lupus familiaris  NC_002008.4  (mtDNA 全長 約16.7kb)
  ヒト  Homo sapiens            NC_012920.1  (rCRS, mtDNA 全長 約16.6kb)

CI (GitHub Actions) のビルド前に実行する。ネットワークが無い環境では
既存の refs.js (参照なし) のまま残し、アプリ側で参照 FASTA を手動読み込みできる。
"""
import json
import pathlib
import sys
import time
import urllib.request

REFS = {
    "イヌ (Canis lupus familiaris) mtDNA NC_002008.4": "NC_002008.4",
    "ヒト (Homo sapiens) mtDNA NC_012920.1": "NC_012920.1",
}
URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={}&rettype=fasta&retmode=text"
OUT = pathlib.Path(__file__).resolve().parent.parent / "www" / "refs.js"


def fetch(acc):
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(URL.format(acc), timeout=60) as r:
                text = r.read().decode()
            seq = "".join(l.strip() for l in text.splitlines() if not l.startswith(">")).upper()
            if len(seq) < 15000 or set(seq) - set("ACGTNRYKMSWBDHV"):
                raise ValueError(f"{acc}: unexpected response ({len(seq)} bp)")
            return seq
        except Exception as e:  # noqa: BLE001 - retry any network error
            last = e
            time.sleep(2 ** (attempt + 1))
    raise last


def main():
    refs = {}
    for name, acc in REFS.items():
        refs[name] = fetch(acc)
        print(f"{acc}: {len(refs[name])} bp")
    OUT.write_text(
        "/* 自動生成: tools/fetch_refs.py (NCBI nuccore) */\n"
        "window.CANIS_REFS = " + json.dumps(refs, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"reference fetch failed: {e}", file=sys.stderr)
        sys.exit(1)
