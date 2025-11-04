#!/usr/bin/env python3
import sys,json,math,os,subprocess
def score(o,target_H):
    ent=o.get('entropy',target_H)
    proxy=o.get('sub_features',{}).get('proxy_entropy')
    s=1.0 - abs(ent-target_H)/(1.0+abs(target_H))
    if proxy is not None:
        s += 1.2*(1.0 - abs(proxy-target_H)/(1.0+abs(target_H)))
    return s
def synth(m,target_H):
    txt=[]
    txt.append('Equation: '+m.get('raw',''))
    if m.get('generated'):
        txt.append('Generated: YES')
        if m.get('explanation'): txt.append('Explanation: '+m.get('explanation'))
    txt.append('Score: %.4f' % m.get('score',0.0))
    if m.get('features',{}).get('numeric_value') is not None:
        txt.append('Numeric eval: %.8g' % m['features']['numeric_value'])
    return '\n'.join(txt)
def main():
    if len(sys.argv)<5: print('Usage: causal_infer.py subst.jsonl question_entropy out.json out.txt'); return 2
    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]
    target_H=float(sys.argv[2])
    matches=[]
    for o in objs:
        s=score(o,target_H)
        matches.append({'id':o.get('id'),'score':s,'raw':o.get('raw'),'features':o.get('sub_features',{}),'generated':o.get('generated',False),'explanation':o.get('explanation',None)})
    matches.sort(key=lambda x:-x['score'])
    # if top score low, try to include generated candidates
    if not matches or matches[0]['score']<0.6:
        base=os.path.splitext(sys.argv[1])[0].replace('_subst','') + '.jsonl'
        genfile='generated.jsonl'
        if os.path.exists('equations_decomposed.jsonl'):
            subprocess.call([sys.executable,'equation_generator.py','equations_decomposed.jsonl',genfile,'8'])
            if os.path.exists(genfile):
                for g in [json.loads(l) for l in open(genfile,'r',encoding='utf-8') if l.strip()]:
                    g['generated']=True; g['sub_features']={'numeric_value':None,'proxy_entropy':None}; s=score(g,target_H)
                    matches.append({'id':g.get('id'),'score':s,'raw':g.get('raw'),'features':g.get('sub_features',{}),'generated':True,'explanation':g.get('explanation')})
                matches.sort(key=lambda x:-x['score'])
    for m in matches[:10]: m['answer_text']=synth(m,target_H)
    open(sys.argv[3],'w',encoding='utf-8').write(json.dumps(matches,ensure_ascii=False,indent=2))
    with open(sys.argv[4],'w',encoding='utf-8') as fo:
        fo.write('QUESTION ENTROPY: %.6f\n\n' % target_H)
        for i,m in enumerate(matches[:10],1):
            fo.write('RANK %d ID=%s SCORE=%.4f\n' % (i,m.get('id'),m.get('score')))
            fo.write(m.get('answer_text','') + '\n\n')
    print('Wrote', sys.argv[3], 'and', sys.argv[4])
if __name__=='__main__': sys.exit(main())
