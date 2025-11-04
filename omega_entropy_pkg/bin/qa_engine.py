#!/usr/bin/env python3
"""
qa_engine.py
Answer questions against a report by using sentence entropy and heuristics.
Usage: qa_engine.py report.txt sentences_entropy.jsonl questions.txt out_answers.txt
Notes: sentences_entropy.jsonl produced by extract_sections.py -> entropy_model.py
"""
import sys, json, re, math
from collections import Counter
if len(sys.argv)<5:
    print('Usage: qa_engine.py report.txt sentences_entropy.jsonl questions.txt out_answers.txt'); sys.exit(2)
report_file, sfile, qfile, outfile = sys.argv[1:5]
# load sentence objects
with open(sfile,'r',encoding='utf-8') as f:
    objs = [json.loads(line) for line in f if line.strip()]
# build simple indices
paras = {}
for o in objs:
    paras.setdefault(o.get('para',0),[]).append(o)
all_sents = objs
# helper: find by keyword
def find_by_keywords(keywords, top=5):
    hits = []
    for o in all_sents:
        txt = o.get('sentence','').lower()
        score = sum(txt.count(k) for k in keywords)
        if score>0:
            hits.append((score, o))
    hits.sort(key=lambda x:-x[0])
    return [h[1] for h in hits[:top]]
# helper: closest entropy
def closest_entropy(target_H, top=5):
    arr = []
    for o in all_sents:
        H = o.get('entropy',0.0)
        arr.append((abs(H - target_H), H, o))
    arr.sort(key=lambda x: x[0])
    return [a[2] for a in arr[:top]]
# read questions
qs = [l.strip() for l in open(qfile,'r',encoding='utf-8') if l.strip()]
outs = []
for q in qs:
    ql = q.lower()
    if '何ができる' in q or 'what can be done' in ql:
        # find methods/results
        candidates = find_by_keywords(['method','methods','approach','we propose','we show','結果','方法','結果は','手法','示す','示した','propose','result'])
        if candidates:
            ans = 'このレポートから可能なこと（根拠付き）:\n'
            for c in candidates[:5]:
                ans += '- ' + c.get('sentence','')[:400].replace('\n',' ') + '\n'
        else:
            ans = '明確な methods/results の記述は見つかりませんでした。本文冒頭や末尾の段落を確認してください。'
        outs.append({'q':q,'a':ans})
        continue
    if '低エントロピー' in q or 'low-entropy' in ql:
        # low entropy = H small
        ranked = sorted(all_sents, key=lambda o: o.get('entropy',0.0))[:5]
        ans = '低エントロピー文（要約的/繰り返しが多い）例:\n'
        for r in ranked: ans += '- H=%.3f: %s\n' % (r.get('entropy',0.0), r.get('sentence','')[:300].replace('\n',' '))
        outs.append({'q':q,'a':ans}); continue
    if '中程度' in q or 'medium-entropy' in ql:
        # medium ~ median
        Hs = sorted(o.get('entropy',0.0) for o in all_sents)
        if Hs:
            med = Hs[len(Hs)//2]
        else:
            med = 0.0
        ranked = closest_entropy(med, top=5)
        ans = '中程度エントロピー文（説明的）例:\n'
        for r in ranked: ans += '- H=%.3f: %s\n' % (r.get('entropy',0.0), r.get('sentence','')[:300].replace('\n',' '))
        outs.append({'q':q,'a':ans}); continue
    if '高エントロピー' in q or 'high-entropy' in ql:
        ranked = sorted(all_sents, key=lambda o: -o.get('entropy',0.0))[:5]
        ans = '高エントロピー文（式・新情報多）例:\n'
        for r in ranked: ans += '- H=%.3f: %s\n' % (r.get('entropy',0.0), r.get('sentence','')[:400].replace('\n',' '))
        outs.append({'q':q,'a':ans}); continue
    # entropy-specified pattern: e.g. H=2.0
    m = re.search(r'H\s*=\s*([0-9]*\.?[0-9]+)', q)
    if m:
        target = float(m.group(1))
        found = closest_entropy(target, top=5)
        ans = '指定エントロピー H=%.3f に近い文:\n' % target
        for f in found:
            ans += '- H=%.3f: %s\n' % (f.get('entropy',0.0), f.get('sentence','')[:400].replace('\n',' '))
        outs.append({'q':q,'a':ans}); continue
    # fallback: try to match keywords and return best snippet
    qtokens = re.findall(r"[\w\u4e00-\u9fff]+", q)
    best = None; best_score = 0
    for o in all_sents:
        txt = o.get('sentence','')
        score = sum(1 for t in qtokens if t and t in txt)
        if score > best_score:
            best_score = score; best = o
    if best_score>0 and best:
        ans = '関連箇所:\n- H=%.3f: %s\n' % (best.get('entropy',0.0), best.get('sentence','')[:600].replace('\n',' '))
    else:
        ans = '自動応答で該当箇所が見つかりませんでした。質問を具体化してください。'
    outs.append({'q':q,'a':ans})
# write answers file
with open(outfile,'w',encoding='utf-8') as fw:
    for item in outs:
        fw.write('Q: ' + item['q'] + '\n')
        fw.write('A: ' + item['a'] + '\n\n')
print('Wrote answers to', outfile)
