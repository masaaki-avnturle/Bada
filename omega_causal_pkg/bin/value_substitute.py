#!/usr/bin/env python3
import sys,json,re,math
try:
    import mpmath as mp; MP=True
except Exception:
    MP=False
def prepare(expr, vals):
    s = expr.replace('Gamma','gamma').replace('zeta','zeta').replace('^','**').replace('\\\n',' ')
    for k,v in vals.items(): s=re.sub(r'\\b'+re.escape(k)+r'\\b','(%r)'%v,s)
    return s
def safe_eval(s):
    ns={'pi':math.pi,'e':math.e}
    if MP:
        ns['gamma']=lambda x: float(mp.gamma(x))
        ns['zeta']=lambda x: float(mp.zeta(x))
    else:
        try: ns['gamma']=lambda x: float(math.gamma(x))
        except: ns['gamma']=lambda x: float('nan')
        ns['zeta']=lambda x: float('nan')
    try:
        return float(eval(s,{'__builtins__':None},ns))
    except Exception:
        return None
def main():
    if len(sys.argv)<4: print('Usage: value_substitute.py in_entropy.jsonl values.json out.jsonl'); return 2
    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]
    vals=json.load(open(sys.argv[2],'r',encoding='utf-8'))
    outs=[]
    for o in objs:
        raw=o.get('raw',''); s=prepare(raw,vals); num=safe_eval(s)
        f={'numeric_value':num,'proxy_entropy':(math.log2(1+abs(num)) if num is not None else None),'evaluation_success': num is not None}
        o['sub_features']=f; outs.append(o)
    open(sys.argv[3],'w',encoding='utf-8').write('\n'.join(json.dumps(o,ensure_ascii=False) for o in outs))
    print('Wrote',sys.argv[3])
if __name__=='__main__': sys.exit(main())
