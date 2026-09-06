以下は、提示いただいたスクリプトの最小限の修正（Python 3.8+ 互換の型注釈調整とトークン正規表現の軽微な重複除去）を行った完全版です。保存して実行できるようにしています。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bin/omega-proof.py

Extract or infer sections (主題/目的, 結論, 定理, 証明, 予想) from plain text even when
those headings are not explicitly present. Uses keyword heuristics combined with
sentence-level Shannon entropy to pick informative candidate sentences for each section,
then writes a LaTeX file.

Usage:
    ./bin/omega-proof.py input.txt out.tex
"""
from __future__ import annotations
import sys
import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional

# --- Configuration ---------------------------------------------------------
# Keywords (Japanese + English variants) used as weak signals for sections.
SECTION_KEYWORDS: Dict[str, List[str]] = {
    "topic": ["主題", "目的", "取り組む", "this paper", "we study", "topic", "purpose", "aim"],
    "conclusion": ["結論", "まとめ", "したがって", "よって", "conclude", "we conclude", "in conclusion"],
    "theorem": ["定理", "命題", "Theorem", "Proposition", "lemma"],
    "proof": ["証明", "示す", "proof", "we prove", "demonstrate"],
    "conjecture": ["予想", "conjecture", "hypothesis", "conjectural"],
}

# How many top sentences to pick per section (tunable)
TOP_N_SENTENCES = {
    "topic": 2,
    "conclusion": 3,
    "theorem": 5,
    "proof": 6,
    "conjecture": 2,
}

# Minimum entropy threshold to consider a sentence "informative" (can be 0 to accept all)
MIN_ENTROPY = 0.0

# Weighting between keyword-match score and normalized entropy (0..1)
KEYWORD_WEIGHT = 0.6
ENTROPY_WEIGHT = 0.4

# Sentence splitting regex (simple, handles Japanese punctuation by newline/句点 also)
SENTENCE_SPLIT_RE = re.compile(r"(?<=。|\.|\?|！|!|\?|\n)\s*")

# Word tokenization: split on spaces and punctuation; keep CJK characters as tokens
TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+", re.UNICODE)


# --- Utilities -------------------------------------------------------------
def read_input_lines(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_into_sentences(text: str) -> List[str]:
    parts = SENTENCE_SPLIT_RE.split(text)
    # further strip whitespace and ignore empty
    return [p.strip() for p in parts if p and p.strip()]


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text)


def sentence_entropy(tokens: List[str]) -> float:
    """
    Compute Shannon entropy of the token frequency distribution in the sentence.
    Entropy in bits.
    """
    if not tokens:
        return 0.0
    cnt = Counter(tokens)
    total = sum(cnt.values())
    ent = 0.0
    for v in cnt.values():
        p = v / total
        ent -= p * math.log2(p)
    return ent


def normalize_scores(scores: List[float]) -> List[float]:
    if not scores:
        return []
    mn = min(scores)
    mx = max(scores)
    if math.isclose(mx, mn):
        return [0.5 for _ in scores]
    return [(s - mn) / (mx - mn) for s in scores]


def keyword_score_for_sentence(sentence: str, keywords: List[str]) -> float:
    s = sentence.lower()
    score = 0.0
    for kw in keywords:
        if kw.lower() in s:
            # basic boosting: presence increases score; multiple occurrences more
            score += s.count(kw.lower())
    return score


# --- Main extraction logic -------------------------------------------------
def analyze_sentences(sentences: List[str]) -> Tuple[List[Dict], float]:
    """
    Analyze sentences: for each sentence compute tokens, entropy, and raw keyword hits
    across all sections. Return list of per-sentence dicts and max entropy observed.
    """
    sent_data = []
    max_ent = 0.0
    for s in sentences:
        toks = tokenize(s)
        ent = sentence_entropy(toks)
        if ent > max_ent:
            max_ent = ent
        kw_hits = {k: keyword_score_for_sentence(s, kws) for k, kws in SECTION_KEYWORDS.items()}
        sent_data.append({
            "text": s,
            "tokens": toks,
            "entropy": ent,
            "kw_hits": kw_hits,
        })
    return sent_data, max_ent


def score_sentences_for_section(sent_data: List[Dict], section: str, max_entropy: float) -> List[Tuple[float, str]]:
    """
    For a given section, compute a combined score for each sentence:
    combined = KEYWORD_WEIGHT * normalized_keyword_score + ENTROPY_WEIGHT * normalized_entropy
    Only sentences with entropy >= MIN_ENTROPY are considered.
    Returns list of (score, sentence) sorted descending.
    """
    # collect raw keyword scores and entropies
    raw_kw = [d["kw_hits"].get(section, 0.0) for d in sent_data]
    entropies = [d["entropy"] for d in sent_data]
    # normalize
    norm_kw = normalize_scores(raw_kw)
    # entropy normalization relative to observed max_entropy
    if max_entropy > 0:
        norm_ent = [e / max_entropy for e in entropies]
    else:
        norm_ent = [0.0 for _ in entropies]
    scored: List[Tuple[float, str]] = []
    for i, d in enumerate(sent_data):
        if d["entropy"] < MIN_ENTROPY:
            continue
        score = KEYWORD_WEIGHT * norm_kw[i] + ENTROPY_WEIGHT * norm_ent[i]
        scored.append((score, d["text"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def pick_top_sentences(scored: List[Tuple[float, str]], n: int) -> List[str]:
    selected = []
    seen = set()
    for score, s in scored:
        norm = " ".join(s.split())
        if norm in seen:
            continue
        seen.add(norm)
        selected.append(s)
        if len(selected) >= n:
            break
    return selected


def assemble_section_text(sentences: List[str]) -> Optional[str]:
    if not sentences:
        return None
    # Try to order by original appearance if possible (they come from analysis in order)
    # Join into a paragraph, making small fixes (ensure ending punctuation)
    clean = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if s[-1] not in "。.!?!":
            s = s + "。"
        clean.append(s)
    return "\n\n".join(clean)


# --- LaTeX generation ------------------------------------------------------
def generate_latex_output(sections: Dict[str, Optional[str]], source_name: str) -> str:
    header = [
        "% Auto-generated by bin/omega-proof.py",
        f"% Source: {source_name}",
        "\\documentclass{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{amsmath,amsthm,amssymb}",
        "\\usepackage{geometry}",
        "\\geometry{margin=1in}",
        "\\begin{document}",
        ""
    ]
    body = []
    # Title: use inferred topic first sentence if exists
    if sections.get("topic"):
        body.append("\\section*{主題 / Topic}")
        body.append(sections["topic"])
        body.append("")
    if sections.get("theorem"):
        body.append("\\section*{定理 / Theorem}")
        body.append(sections["theorem"])
        body.append("")
    if sections.get("conjecture"):
        body.append("\\section*{予想 / Conjecture}")
        body.append(sections["conjecture"])
        body.append("")
    if sections.get("proof"):
        body.append("\\section*{証明 / Proof}")
        body.append(sections["proof"])
        body.append("")
    if sections.get("conclusion"):
        body.append("\\section*{結論 / Conclusion}")
        body.append(sections["conclusion"])
        body.append("")
    footer = ["\\end{document}"]
    return "\n".join(header + body + footer)


# --- Orchestration ---------------------------------------------------------
def infer_sections_from_text(text: str) -> Dict[str, Optional[str]]:
    # 1) sentence split
    sentences = split_into_sentences(text)
    if not sentences:
        return {k: None for k in SECTION_KEYWORDS.keys()}
    # 2) analyze sentences
    sent_data, max_ent = analyze_sentences(sentences)
    # 3) For each section, score sentences and pick top N
    sections_result: Dict[str, Optional[str]] = {}
    for sec in SECTION_KEYWORDS.keys():
        scored = score_sentences_for_section(sent_data, sec, max_ent)
        topn = TOP_N_SENTENCES.get(sec, 2)
        chosen = pick_top_sentences(scored, topn)
        # If nothing chosen, try a fallback: pick highest-entropy sentences not already picked
        if not chosen:
            # gather high entropy sentences
            high_ent = sorted(((d["entropy"], d["text"]) for d in sent_data), key=lambda x: x[0], reverse=True)
            chosen = [t for _, t in high_ent[:topn]]
        sections_result[sec] = assemble_section_text(chosen)
    return sections_result


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 2:
        print("Usage: bin/omega-proof.py input.txt out.tex", file=sys.stderr)
        return 2
    input_path, output_path = argv
    try:
        text = read_input_lines(input_path)
    except Exception as e:
        print(f"Error reading input file {input_path}: {e}", file=sys.stderr)
        return 1

    # First, attempt to detect explicit headings and prefer exact heading extraction
    lines = text.splitlines()
    heading_map = {}  # idx -> section key if heading found
    heading_patterns = {
        "topic": [r"^\s*(目的|主題|topic|purpose)\s*[:：\-]?\s*$"],
        "conclusion": [r"^\s*(結論|まとめ|conclusion)\s*[:：\-]?\s*$"],
        "theorem": [r"^\s*(定理|命題|theorem|proposition)\s*[:：\-]?\s*$"],
        "proof": [r"^\s*(証明|proof)\s*[:：\-]?\s*$"],
        "conjecture": [r"^\s*(予想|conjecture|hypothesis)\s*[:：\-]?\s*$"],
    }
    compiled = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in heading_patterns.items()}
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            continue
        for k, pats in compiled.items():
            for pat in pats:
                if pat.match(s):
                    heading_map[i] = k
                    break
            if i in heading_map:
                break

    # If explicit headings exist, extract blocks per heading first and use as section text (fallback to inference)
    explicit_sections: Dict[str, Optional[str]] = {k: None for k in SECTION_KEYWORDS.keys()}
    if heading_map:
        # sort headings and gather until next heading
        idxs = sorted(heading_map.keys())
        content_blocks: Dict[str, List[str]] = {k: [] for k in SECTION_KEYWORDS.keys()}
        for pos, start_idx in enumerate(idxs):
            key = heading_map[start_idx]
            end_idx = idxs[pos + 1] if pos + 1 < len(idxs) else len(lines)
            block_lines = lines[start_idx + 1:end_idx]
            # clean block
            block_text = "\n".join([l.strip() for l in block_lines if l.strip()])
            if block_text:
                content_blocks[key].append(block_text)
        for k, blks in content_blocks.items():
            if blks:
                explicit_sections[k] = "\n\n".join(blks)
    # Use inferred sections if explicit not present
    inferred = infer_sections_from_text(text)
    final_sections: Dict[str, Optional[str]] = {}
    for k in SECTION_KEYWORDS.keys():
        final_sections[k] = explicit_sections.get(k) or inferred.get(k)

    # regenerate some structure: prefer topic first, then theorem/conjecture/proof, then conclusion
    latex = generate_latex_output({
        "topic": final_sections.get("topic"),
        "theorem": final_sections.get("theorem"),
        "conjecture": final_sections.get("conjecture"),
        "proof": final_sections.get("proof"),
        "conclusion": final_sections.get("conclusion"),
    }, input_path)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(latex)
    except Exception as e:
        print(f"Error writing output file {output_path}: {e}", file=sys.stderr)
        return 1

    print(f"Wrote inferred LaTeX to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

注意:
- Python 3.8+ で動作するように `main` の型注釈を `Optional[List[str]]` に変更しました。
- トークン正規表現の重複を除去しました。
