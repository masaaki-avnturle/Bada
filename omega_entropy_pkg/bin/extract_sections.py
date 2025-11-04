#!/usr/bin/env python3
"""
extract_sections.py
Extract sentences and math snippets from a report.
Usage: extract_sections.py input.txt out_sentences.jsonl
"""
import sys,io,re,json
from html import escape
if len(sys.argv)<3:
    print('Usage: extract_sections.py input.txt out_sentences.jsonl'); sys.exit(2)
fin, fout = sys.argv[1], sys.argv[2]
text = open(fin,'r',encoding='utf-8').read()
# Normalize newlines
text = text.replace('\r\n','\n').replace('\r','\n')
# Split into paragraphs
paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
# Simple sentence splitter tuned for Japanese/English: split on 。.!? and newlines
sent_split = re.compile(r'(?<=。|\.|\?|!|！)\s*')
math_inline = re.compile(r'\\\((.+?)\\\)|\$(.+?)\$|\\\[(.+?)\\\]', re.S)
token_re = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+", re.U)
out = open(fout,'w',encoding='utf-8')
sid = 0
for pi,p in enumerate(paras):
    sents = [s.strip() for s in sent_split.split(p) if s and s.strip()]
    for s in sents:
        mats = math_inline.findall(s)
        is_math = bool(mats)
        tokens = token_re.findall(s)
        obj = {'id':sid,'para':pi,'sentence':s,'math':is_math,'tokens':tokens}
        out.write(json.dumps(obj, ensure_ascii=False) + '\n')
        sid += 1
out.close()
print('Wrote',fout)
