#!/usr/bin/env python3
import sys,re,json
def tokenize(s):
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\.[0-9]+)?|\\\\[A-Za-z]+|\\S", s)
def extract(text):
    math_re = re.compile(r'\\\\\[(.+?)\\\\\]|\\\\\((.+?)\\\\\)|\$\$(.+?)\$\$|\$(.+?)\$', re.S)
    line_re = re.compile(r'^[^\\n]*[=<>≈∼\\+\\-\\^\\*\\/:]+[^\\n]*$', re.M)
    out=[]; seen=0
    for m in math_re.findall(text):
        c=''.join(m).strip()
        if c and len(c)>2:
            out.append({'id':f'M{seen}','raw':c,'tokens':tokenize(c),'latex':True}); seen+=1
    for ln in line_re.findall(text):
        s=ln.strip()
        if len(s)>4:
            out.append({'id':f'L{seen}','raw':s,'tokens':tokenize(s),'latex':False}); seen+=1
    return out
def main():
    if len(sys.argv)<3: print('Usage: extract_equations.py in.txt out.jsonl'); return 2
    txt=open(sys.argv[1],'r',encoding='utf-8',errors='ignore').read()
    recs=extract(txt)
    with open(sys.argv[2],'w',encoding='utf-8') as fo:
        for r in recs: fo.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('Extracted',len(recs),'records')
if __name__=='__main__': sys.exit(main())
