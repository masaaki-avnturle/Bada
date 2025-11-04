#!/usr/bin/env python3
import sys,math,json,re
from collections import Counter
def shannon(tokens):
    if not tokens: return 0.0
    c=Counter(tokens); n=float(len(tokens)); H=0.0
    for v in c.values(): p=v/n; H -= p*math.log2(p)
    return H
def feats(tokens):
    s=' '.join(str(t).lower() for t in tokens)
    return {'has_gamma':('gamma' in s or '\\gamma' in s),'has_zeta':('zeta' in s or '\\zeta' in s),'has_manifold':('manifold' in s or 'differential' in s),'has_noncomm':('noncomm' in s or 'non-comm' in s)}
def main():
    if len(sys.argv)<3: print('Usage: equation_entropy.py in.jsonl out.jsonl'); return 2
    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]
    out=[]
    for o in objs:
        toks=o.get('tokens',[]); H=shannon(toks); f=feats(toks); uniq=len(set(toks)); tc=len(toks)
        symbolc=sum(1 for t in toks if re.match(r'^[^A-Za-z0-9]+$|^\\\\[A-Za-z]+',t))
        o.update({'entropy':H,'token_count':tc,'uniq':uniq,'math_density':symbolc/max(1,tc),'structural':tc*uniq}); o.update(f); out.append(o)
    Hs=[o['entropy'] for o in out]
    if Hs:
        mn=min(Hs); mx=max(Hs)
        for o in out: o['entropy_norm']=(o['entropy']-mn)/(mx-mn) if mx>mn else 0.0
    open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(json.dumps(o,ensure_ascii=False) for o in out))
    print('Wrote',sys.argv[2])
if __name__=='__main__': sys.exit(main())
