#!/usr/bin/env python3
"""NCBI から十二支の動物 + ヒトの参照ミトコンドリアゲノムを取得し www/refs.js を生成する。

各種について、まず既知の RefSeq アクセッションを取得し、FASTA ヘッダの学名で検証する。
無い/一致しない場合は候補学名で "mitochondrion complete genome" を検索して取得する。
辰 (竜) は伝説上の生物で DNA が存在しないため対象外。

CI (GitHub Actions) のビルド前に実行する。ネットワークが無い環境では
既存の refs.js (参照なし) のまま残し、アプリ側で参照 FASTA を手動読み込みできる。
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

# key: (表示名, [(アクセッション or None, 学名)...])  先頭から順に試す
SPECIES = {
    "human":   ("ヒト",     [("NC_012920.1", "Homo sapiens")]),
    "ne":      ("ネズミ",   [("NC_005089.1", "Mus musculus")]),
    "ushi":    ("ウシ",     [("NC_006853.1", "Bos taurus")]),
    "tora":    ("トラ",     [("NC_010642.1", "Panthera tigris")]),
    "u":       ("ウサギ",   [("NC_001913.1", "Oryctolagus cuniculus")]),
    "mi":      ("ヘビ",     [("NC_001945.1", "Dinodon semicarinatus"), (None, "Elaphe climacophora"),
                             (None, "Python bivittatus")]),
    "uma":     ("ウマ",     [("NC_001640.1", "Equus caballus")]),
    "hitsuji": ("ヒツジ",   [("NC_001941.1", "Ovis aries")]),
    "saru":    ("サル",     [(None, "Macaca fuscata"), (None, "Macaca mulatta")]),
    "tori":    ("ニワトリ", [("NC_053523.1", "Gallus gallus"), (None, "Gallus gallus")]),
    "inu":     ("イヌ",     [("NC_002008.4", "Canis lupus familiaris")]),
    "i":       ("イノシシ", [("NC_000845.1", "Sus scrofa")]),
}
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
OUT = pathlib.Path(__file__).resolve().parent.parent / "www" / "refs.js"


def get(url):
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read().decode()
        except Exception as e:  # noqa: BLE001 - retry any network error
            last = e
            time.sleep(2 ** (attempt + 1))
    raise last


def efetch(acc):
    time.sleep(0.4)  # NCBI: 3 req/s without API key
    text = get(EUTILS + "efetch.fcgi?db=nuccore&rettype=fasta&retmode=text&id=" + urllib.parse.quote(acc))
    lines = text.splitlines()
    header = lines[0] if lines and lines[0].startswith(">") else ""
    seq = "".join(l.strip() for l in lines if not l.startswith(">")).upper()
    return header, seq


def esearch(species):
    time.sleep(0.4)
    term = f'"{species}"[Organism] AND mitochondrion[Title] AND "complete genome"[Title]'
    q = urllib.parse.urlencode({"db": "nuccore", "term": term, "retmax": 5, "retmode": "json"})
    return json.loads(get(EUTILS + "esearch.fcgi?" + q))["esearchresult"]["idlist"]


def valid(header, seq, species):
    return header and species.split()[0].lower() in header.lower() and 14000 <= len(seq) <= 25000 \
        and not set(seq) - set("ACGTNRYKMSWBDHV")


def fetch_species(candidates):
    for acc, species in candidates:
        # 既知アクセッション → 学名で検索 の順に試す (アクセッション誤り・改版への保険)
        for ids in ([acc] if acc else [], None):
            for i in ids if ids is not None else esearch(species):
                header, seq = efetch(i)
                if valid(header, seq, species):
                    return header[1:].strip(), seq
    return None, None


def main():
    refs, meta, missing = {}, {}, []
    for key, (label, cands) in SPECIES.items():
        try:
            title, seq = fetch_species(cands)
        except Exception as e:  # noqa: BLE001
            print(f"{key}: error {e}", file=sys.stderr)
            title, seq = None, None
        if seq:
            refs[key], meta[key] = seq, title
            print(f"{key} ({label}): {len(seq)} bp — {title}")
        else:
            missing.append(key)
            print(f"{key} ({label}): NOT FOUND", file=sys.stderr)
    if "human" not in refs or len(refs) < 6:
        raise SystemExit(f"too few references fetched (missing: {missing})")
    OUT.write_text(
        "/* 自動生成: tools/fetch_refs.py (NCBI nuccore) */\n"
        "window.JUNISHI_REFS = " + json.dumps(refs) + ";\n"
        "window.JUNISHI_REFS_META = " + json.dumps(meta, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({len(refs)} species; missing: {missing or 'none'})")


if __name__ == "__main__":
    main()
