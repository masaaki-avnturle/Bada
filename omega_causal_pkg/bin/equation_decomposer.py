#!/usr/bin/env python3
import sys,re,json
def simple_split(expr):
    # naive splitting by top-level + and - (not inside parentheses)
    parts=[]; buf=''; depth=0
    for i,ch in enumerate(expr):
        if ch=='(':
            depth+=1; buf+=ch
        elif ch==')': depth=max(0,depth-1); buf+=ch
        elif depth==0 and ch in ['+','-']:
            if buf.strip(): parts.append(buf.strip()); parts.append(ch); buf=''
        else:
            buf+=ch
    if buf.strip(): parts.append(buf.strip())
    # merge operator tokens into neighboring parts to make subexpressions
    merged=[]; i=0
    while i<len(parts):
        if parts[i] in ['+','-'] and merged:
            merged[-1]+= ' ' + parts[i] + ' ' + (parts[i+1] if i+1<len(parts) else '')
            i+=2
        else:
            merged.append(parts[i]); i+=1
    return [p for p in merged if p]
def extract_subterms(expr):
    sub=set()
    # tokens by parentheses groups and function calls
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\([^\)]*\)|\([^\)]+\)|[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\.[0-9]+)?', expr):
        sub.add(m.group(0).strip())
    # top-level splits
    for p in simple_split(expr): sub.add(p)
    return sorted([s for s in sub if len(s)>0])
def main():
    if len(sys.argv)<3: print('Usage: equation_decomposer.py in.jsonl out_decomposed.jsonl'); return 2
    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]
    outs=[]
    for o in objs:
        raw=o.get('raw','')
        subs=extract_subterms(raw)
        outs.append({'id':o.get('id'),'raw':raw,'subterms':subs,'tokens':o.get('tokens',[]), 'latex': o.get('latex', False)})
    open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(json.dumps(o,ensure_ascii=False) for o in outs))
    print('Wrote', sys.argv[2], 'entries=', len(outs))
if __name__=='__main__': sys.exit(main())
