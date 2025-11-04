#!/usr/bin/env python3
"""
entropy_model.py
Compute sentence-level Shannon entropy from token frequency within the sentence.
Usage: entropy_model.py sentences.jsonl out_sentences_entropy.jsonl
"""
import sys,json,math
if len(sys.argv)<3:
    print('Usage: entropy_model.py sentences.jsonl out_sentences_entropy.jsonl'); sys.exit(2)
fin, fout = sys.argv[1], sys.argv[2]
lines = [json.loads(l) for l in open(fin,'r',encoding='utf-8') if l.strip()]
def shannon_entropy(tokens):
    if not tokens: return 0.0
    freq = {}
    for t in tokens: freq[t] = freq.get(t,0)+1
    total = len(tokens)
    H = 0.0
    for v in freq.values():
        p = v/total
        H -= p * math.log2(p)
    return H
# Optionally normalize by sentence length to get per-token entropy
for obj in lines:
    H = shannon_entropy(obj.get('tokens',[]))
    obj['entropy'] = H
open(fout,'w',encoding='utf-8').write('\n'.join(json.dumps(o, ensure_ascii=False) for o in lines))
print('Wrote',fout)
