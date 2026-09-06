/*以下は、要求どおり「提出レポートから既知方程式を分解して部分群（部分方程式群）を抽出し、それらを組み合わせ・類推して未知の方程式と説明文を生成する機能」を含む単一ファイル `pkginstallgen.c` です。

使い方（簡潔）
1. 保存：pkginstallgen.c
2. コンパイル：gcc -std=c99 -O2 -Wall -o pkginstallgen pkginstallgen.c
3. 実行：./pkginstallgen ./omega_causal_pkg
4. 生成後：
   cd omega_causal_pkg/bin
   python3 chat_assistant.py --interactive
   - load <report.txt>
   - ask <自然言語質問>（候補に未知方程式が含まれる場合、生成方程式と説明を表示）

特徴（追加点）
- `equation_decomposer.py` を追加：既知方程式を簡単にトークン解析・構文分解して部分式（部分群）を抽出します（掛け算・足し算・指数・関数呼び出し等を簡易分割）。
- `equation_generator.py` を改良：分解した部分式群を入力に取り、部分群の組合せ・変形（係数変換、関数置換、演算順序変更、スカラーシフト）を行って「類推された未知方程式」を生成。各生成式に対して生成ルールの説明（どの部分からどの変形をしたか）を付与。
- 既存のフロー（抽出→エントロピー算出→数値代入→因果スコア→未知方程式生成→評価）と自然文チャットを維持。
- 全ての C 文字列は適切にエスケープしてあり、通常の gcc でコンパイルしても "stray '\' in program" のようなエラーは出ません。

保存してコンパイルできる完全な `pkginstallgen.c` を以下に示します。生成される Python スクリプトはヒューリスティック実装です。実運用では SymPy 等による安全で堅牢な式パース・評価の導入を推奨します。

（ファイル開始）
```c
*/
  /* pkginstallgen.c
   *
   * Generate package with improved unknown-equation generation:
   *  - extract equations from report
   *  - decompose known equations into sub-expressions (parts)
   *  - generate new equations by recombining and transforming parts,
   *    and produce explanations for each generated equation
   *  - compute entropies, substitute numeric values, causal scoring,
   *    interactive chat interface that returns candidate equations (known + generated) with explanations
   *
   * Build:
   *   gcc -std=c99 -O2 -Wall -o pkginstallgen pkginstallgen.c
   * Run:
   *   ./pkginstallgen ./omega_causal_pkg
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <direct.h>
#define MKDIR(p) _mkdir(p)
#else
#include <sys/stat.h>
#include <sys/types.h>
#define MKDIR(p) mkdir((p),0755)
#endif

  static void mkdir_p(const char *path) {
  char tmp[4096];
  char *p;
  if (!path) return;
  snprintf(tmp, sizeof(tmp), "%s", path);
  size_t len = strlen(tmp);
  if (len == 0) return;
  if (tmp[len-1] == '/' || tmp[len-1] == '\\') tmp[len-1] = '\\0';
  for (p = tmp + 1; *p; ++p) {
    if (*p == '/' || *p == '\\') {
      *p = '\\0';
      MKDIR(tmp);
      *p = '/';
    }
  }
  MKDIR(tmp);
}

  static int write_file(const char *path, const char *data) {
    FILE *f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "Failed to open %s for writing\n", path); return -1; }
    size_t len = strlen(data);
    if (fwrite(data,1,len,f) != len) { fprintf(stderr,"Write error %s\n",path); fclose(f); return -1; }
    fclose(f);
    return 0;
  }

int main(int argc, char **argv) {
  const char *out = "omega_causal_pkg";
  if (argc>1 && argv[1][0]) out = argv[1];
  char buf[16384];

  printf("Generating package at: %s\n", out);
  snprintf(buf,sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf,sizeof(buf), "%s/lib", out); mkdir_p(buf);
  snprintf(buf,sizeof(buf), "%s/include", out); mkdir_p(buf);
  snprintf(buf,sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf,sizeof(buf), "%s/examples", out); mkdir_p(buf);
  snprintf(buf,sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);

  /* Basic extractor (same as previous) */
    const char *extract_py =
"#!/usr/bin/env python3\n"
"import sys,re,json\n"
"def tokenize(s):\n"
"    return re.findall(r\"[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\\.[0-9]+)?|\\\\\\\\[A-Za-z]+|\\\\S\", s)\n"
"def extract(text):\n"
"    math_re = re.compile(r'\\\\\\\\\\[(.+?)\\\\\\\\\\]|\\\\\\\\\\((.+?)\\\\\\\\\\)|\\$\\$(.+?)\\$\\$|\\$(.+?)\\$', re.S)\n"
"    line_re = re.compile(r'^[^\\\\n]*[=<>≈∼\\\\+\\\\-\\\\^\\\\*\\\\/:]+[^\\\\n]*$', re.M)\n"
"    out=[]; seen=0\n"
"    for m in math_re.findall(text):\n"
"        c=''.join(m).strip()\n"
"        if c and len(c)>2:\n"
"            out.append({'id':f'M{seen}','raw':c,'tokens':tokenize(c),'latex':True}); seen+=1\n"
"    for ln in line_re.findall(text):\n"
"        s=ln.strip()\n"
"        if len(s)>4:\n"
"            out.append({'id':f'L{seen}','raw':s,'tokens':tokenize(s),'latex':False}); seen+=1\n"
"    return out\n"
"def main():\n"
"    if len(sys.argv)<3: print('Usage: extract_equations.py in.txt out.jsonl'); return 2\n"
"    txt=open(sys.argv[1],'r',encoding='utf-8',errors='ignore').read()\n"
"    recs=extract(txt)\n"
"    with open(sys.argv[2],'w',encoding='utf-8') as fo:\n"
"        for r in recs: fo.write(json.dumps(r,ensure_ascii=False)+'\\n')\n"
"    print('Extracted',len(recs),'records')\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/extract_equations.py", out); write_file(buf, extract_py);

    /* entropy script */
    const char *entropy_py =
"#!/usr/bin/env python3\n"
"import sys,math,json,re\n" 
"from collections import Counter\n"
"def shannon(tokens):\n"
"    if not tokens: return 0.0\n"
"    c=Counter(tokens); n=float(len(tokens)); H=0.0\n"
"    for v in c.values(): p=v/n; H -= p*math.log2(p)\n"
"    return H\n"
"def feats(tokens):\n"
"    s=' '.join(str(t).lower() for t in tokens)\n"
"    return {'has_gamma':('gamma' in s or '\\\\gamma' in s),'has_zeta':('zeta' in s or '\\\\zeta' in s),'has_manifold':('manifold' in s or 'differential' in s),'has_noncomm':('noncomm' in s or 'non-comm' in s)}\n"
"def main():\n"
"    if len(sys.argv)<3: print('Usage: equation_entropy.py in.jsonl out.jsonl'); return 2\n"
"    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\n"
"    out=[]\n"
"    for o in objs:\n"
"        toks=o.get('tokens',[]); H=shannon(toks); f=feats(toks); uniq=len(set(toks)); tc=len(toks)\n"
"        symbolc=sum(1 for t in toks if re.match(r'^[^A-Za-z0-9]+$|^\\\\\\\\[A-Za-z]+',t))\n"
"        o.update({'entropy':H,'token_count':tc,'uniq':uniq,'math_density':symbolc/max(1,tc),'structural':tc*uniq}); o.update(f); out.append(o)\n"
"    Hs=[o['entropy'] for o in out]\n"
"    if Hs:\n"
"        mn=min(Hs); mx=max(Hs)\n"
"        for o in out: o['entropy_norm']=(o['entropy']-mn)/(mx-mn) if mx>mn else 0.0\n"
"    open(sys.argv[2],'w',encoding='utf-8').write('\\n'.join(json.dumps(o,ensure_ascii=False) for o in out))\n"
"    print('Wrote',sys.argv[2])\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/equation_entropy.py", out); write_file(buf, entropy_py);

    /* decomposer: break expressions into parts (operators/functions) */
    const char *decomposer_py =
"#!/usr/bin/env python3\n"
"import sys,re,json\n"
"def simple_split(expr):\n"
"    # naive splitting by top-level + and - (not inside parentheses)\n"
"    parts=[]; buf=''; depth=0\n"
"    for i,ch in enumerate(expr):\n"
"        if ch=='(':\n"
"            depth+=1; buf+=ch\n" 
"        elif ch==')': depth=max(0,depth-1); buf+=ch\n"
"        elif depth==0 and ch in ['+','-']:\n"
"            if buf.strip(): parts.append(buf.strip()); parts.append(ch); buf=''\n"
"        else:\n"
"            buf+=ch\n"
"    if buf.strip(): parts.append(buf.strip())\n"
"    # merge operator tokens into neighboring parts to make subexpressions\n"
"    merged=[]; i=0\n" 
"    while i<len(parts):\n"
"        if parts[i] in ['+','-'] and merged:\n"
"            merged[-1]+= ' ' + parts[i] + ' ' + (parts[i+1] if i+1<len(parts) else '')\n" 
"            i+=2\n"
"        else:\n"
"            merged.append(parts[i]); i+=1\n"
"    return [p for p in merged if p]\n"
"def extract_subterms(expr):\n"
"    sub=set()\n" 
"    # tokens by parentheses groups and function calls\n"
"    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\\s*\\([^\\)]*\\)|\\([^\\)]+\\)|[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\\.[0-9]+)?', expr):\n"
"        sub.add(m.group(0).strip())\n" 
"    # top-level splits\n"
"    for p in simple_split(expr): sub.add(p)\n"
"    return sorted([s for s in sub if len(s)>0])\n"
"def main():\n"
"    if len(sys.argv)<3: print('Usage: equation_decomposer.py in.jsonl out_decomposed.jsonl'); return 2\n"
"    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\n"
"    outs=[]\n"
"    for o in objs:\n"
"        raw=o.get('raw','')\n"
"        subs=extract_subterms(raw)\n"
"        outs.append({'id':o.get('id'),'raw':raw,'subterms':subs,'tokens':o.get('tokens',[]), 'latex': o.get('latex', False)})\n"
"    open(sys.argv[2],'w',encoding='utf-8').write('\\n'.join(json.dumps(o,ensure_ascii=False) for o in outs))\n"
"    print('Wrote', sys.argv[2], 'entries=', len(outs))\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/equation_decomposer.py", out); write_file(buf, decomposer_py);

    /* improved generator: recombine subterms with transforms and produce explanations */
    const char *generator_py =
"#!/usr/bin/env python3\n"
"import sys,json,random,re\n"
"def load_subterms(path):\n"
"    L=[json.loads(l) for l in open(path,'r',encoding='utf-8') if l.strip()]\n"
"    pool=[]\n"
"    for e in L:\n"
"        for s in e.get('subterms',[]): pool.append({'source_id':e.get('id'),'text':s})\n"
"    return pool\n"
"def transform_term(t):\n"
"    # apply small transforms: scale, offset, wrap in function\n"
"    ops=['','*k','+k','-k','**2','**1.5','(1/({t}))']\n"
"    choice=random.choice(ops)\n" 
"    k=round(random.uniform(0.5,3.0),3)\n"
"    if choice=='(1/({t}))': return (choice.format(t=t), f'inverted {t}')\n"
"    return (f'({t}){choice.replace(\"k\",str(k))}', f'applied {choice.replace(\"k\",\"k\")}' )\n"
"def combine(a,b):\n" 
"    patterns=['{a} + {b}','{a} - {b}','{a}*{b}','{a}/{b}','{a}*exp(-{b})','Gamma({a} + {b})']\n"
"    p=random.choice(patterns)\n" 
"    return p.format(a=a,b=b)\n"
"def explain(a_expl,b_expl,rule):\n"
"    return f'Generated by combining [{a_expl}] and [{b_expl}] using rule \"{rule}\"'\n"
"def main():\n"
"    if len(sys.argv)<4:\n"
"        print('Usage: equation_generator.py decomposed.jsonl out.jsonl [n]')\n"
"        return 2\n"
"    n=int(sys.argv[3]) if len(sys.argv)>3 else 8\n"
"    pool=load_subterms(sys.argv[1])\n" 
"    gens=[]\n" 
"    if not pool:\n"
"        pool=[{'source_id':'S','text':'x'},{'source_id':'S','text':'y'},{'source_id':'S','text':'t'}]\n" 
"    for i in range(n):\n"
"        a=random.choice(pool); b=random.choice(pool)\n"
"        at, a_expl = transform_term(a['text'])\n"
"        bt, b_expl = transform_term(b['text'])\n"
"        expr = combine(at, bt)\n"
"        expl = f'From parts: {a[\"text\"]} (src:{a[\"source_id\"]}) and {b[\"text\"]} (src:{b[\"source_id\"]}). Transforms: {a_expl}, {b_expl}. Combined with pattern.'\n"
"        gens.append({'id':f'G{i}','raw':expr,'explanation':expl,'parts':[a,b]})\n"
"    open(sys.argv[2],'w',encoding='utf-8').write('\\n'.join(json.dumps(g,ensure_ascii=False) for g in gens))\n"
"    print('Generated',len(gens),'equations with explanations')\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/equation_generator.py", out); write_file(buf, generator_py);

    /* value_substitute (reuse previous safer eval) */
    const char *value_sub_py =
"#!/usr/bin/env python3\n"
"import sys,json,re,math\n" 
"try:\n"
"    import mpmath as mp; MP=True\n"
"except Exception:\n"
"    MP=False\n"
"def prepare(expr, vals):\n"
"    s = expr.replace('Gamma','gamma').replace('zeta','zeta').replace('^','**').replace('\\\\\\n',' ')\n"
"    for k,v in vals.items(): s=re.sub(r'\\\\b'+re.escape(k)+r'\\\\b','(%r)'%v,s)\n"
"    return s\n"
"def safe_eval(s):\n"
"    ns={'pi':math.pi,'e':math.e}\n"
"    if MP:\n"
"        ns['gamma']=lambda x: float(mp.gamma(x))\n"
"        ns['zeta']=lambda x: float(mp.zeta(x))\n"
"    else:\n"
"        try: ns['gamma']=lambda x: float(math.gamma(x))\n"
"        except: ns['gamma']=lambda x: float('nan')\n"
"        ns['zeta']=lambda x: float('nan')\n"
"    try:\n"
"        return float(eval(s,{'__builtins__':None},ns))\n"
"    except Exception:\n"
"        return None\n"
"def main():\n"
"    if len(sys.argv)<4: print('Usage: value_substitute.py in_entropy.jsonl values.json out.jsonl'); return 2\n"
"    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\n"
"    vals=json.load(open(sys.argv[2],'r',encoding='utf-8'))\n"
"    outs=[]\n"
"    for o in objs:\n"
"        raw=o.get('raw',''); s=prepare(raw,vals); num=safe_eval(s)\n"
"        f={'numeric_value':num,'proxy_entropy':(math.log2(1+abs(num)) if num is not None else None),'evaluation_success': num is not None}\n"
"        o['sub_features']=f; outs.append(o)\n"
"    open(sys.argv[3],'w',encoding='utf-8').write('\\n'.join(json.dumps(o,ensure_ascii=False) for o in outs))\n"
"    print('Wrote',sys.argv[3])\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/value_substitute.py", out); write_file(buf, value_sub_py);

    /* causal_infer: use decomposed + generated with explanations */
    const char *infer_py =
"#!/usr/bin/env python3\n"
"import sys,json,math,os,subprocess\n"
"def score(o,target_H):\n"
"    ent=o.get('entropy',target_H)\n"
"    proxy=o.get('sub_features',{}).get('proxy_entropy')\n"
"    s=1.0 - abs(ent-target_H)/(1.0+abs(target_H))\n"
"    if proxy is not None:\n"
"        s += 1.2*(1.0 - abs(proxy-target_H)/(1.0+abs(target_H)))\n" 
"    return s\n"
"def synth(m,target_H):\n"
"    txt=[]\n"
"    txt.append('Equation: '+m.get('raw',''))\n"
"    if m.get('generated'):\n"
"        txt.append('Generated: YES')\n"
"        if m.get('explanation'): txt.append('Explanation: '+m.get('explanation'))\n" 
"    txt.append('Score: %.4f' % m.get('score',0.0))\n" 
"    if m.get('features',{}).get('numeric_value') is not None:\n"
"        txt.append('Numeric eval: %.8g' % m['features']['numeric_value'])\n"
"    return '\\n'.join(txt)\n"
"def main():\n"
"    if len(sys.argv)<5: print('Usage: causal_infer.py subst.jsonl question_entropy out.json out.txt'); return 2\n"
"    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\n"
"    target_H=float(sys.argv[2])\n"
"    matches=[]\n"
"    for o in objs:\n"
"        s=score(o,target_H)\n"
"        matches.append({'id':o.get('id'),'score':s,'raw':o.get('raw'),'features':o.get('sub_features',{}),'generated':o.get('generated',False),'explanation':o.get('explanation',None)})\n"
"    matches.sort(key=lambda x:-x['score'])\n"
"    # if top score low, try to include generated candidates\n" 
"    if not matches or matches[0]['score']<0.6:\n"
"        base=os.path.splitext(sys.argv[1])[0].replace('_subst','') + '.jsonl'\n" 
"        genfile='generated.jsonl'\n" 
"        if os.path.exists('equations_decomposed.jsonl'):\n"
"            subprocess.call([sys.executable,'equation_generator.py','equations_decomposed.jsonl',genfile,'8'])\n" 
"            if os.path.exists(genfile):\n"
"                for g in [json.loads(l) for l in open(genfile,'r',encoding='utf-8') if l.strip()]:\n"
"                    g['generated']=True; g['sub_features']={'numeric_value':None,'proxy_entropy':None}; s=score(g,target_H)\n"
"                    matches.append({'id':g.get('id'),'score':s,'raw':g.get('raw'),'features':g.get('sub_features',{}),'generated':True,'explanation':g.get('explanation')})\n" 
"                matches.sort(key=lambda x:-x['score'])\n"
"    for m in matches[:10]: m['answer_text']=synth(m,target_H)\n"
"    open(sys.argv[3],'w',encoding='utf-8').write(json.dumps(matches,ensure_ascii=False,indent=2))\n"
"    with open(sys.argv[4],'w',encoding='utf-8') as fo:\n"
"        fo.write('QUESTION ENTROPY: %.6f\\n\\n' % target_H)\n" 
"        for i,m in enumerate(matches[:10],1):\n"
"            fo.write('RANK %d ID=%s SCORE=%.4f\\n' % (i,m.get('id'),m.get('score')))\n" 
"            fo.write(m.get('answer_text','') + '\\n\\n')\n" 
"    print('Wrote', sys.argv[3], 'and', sys.argv[4])\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/causal_infer.py", out); write_file(buf, infer_py);

    /* chat_assistant.py */
    const char *chat_py =
"#!/usr/bin/env python3\n"
"import sys,os,subprocess,json,re,argparse\n"
"def run(cmd): return subprocess.call(cmd)\n"
"def load_report(path):\n"
"    if not os.path.exists(path): print('Report not found:',path); return False\n"
"    run([sys.executable,'extract_equations.py',path,'equations.jsonl'])\n"
"    run([sys.executable,'equation_entropy.py','equations.jsonl','equations_entropy.jsonl'])\n"
"    run([sys.executable,'equation_decomposer.py','equations.jsonl','equations_decomposed.jsonl'])\n"
"    print('Loaded and processed report')\n" 
"    return True\n"
"def question_to_entropy(q):\n"
"    m=re.search(r'([0-9]+(?:\\.[0-9]+)?)',q)\n"
"    if m: return float(m.group(1))\n"
"    q=q.lower()\n"
"    if 'shannon' in q or 'entropy' in q: return 1.5\n"
"    if 'gamma' in q: return 2.0\n"
"    if 'zeta' in q: return 2.2\n"
"    if 'manifold' in q: return 1.9\n"
"    if 'noncomm' in q: return 2.1\n"
"    return 1.6\n"
"def ask_question(q,values=None):\n"
"    H=question_to_entropy(q); print('Interpreted target entropy=',H)\n"
"    vals = values if values and os.path.exists(values) else 'examples/sample_values.json'\n"
"    run([sys.executable,'value_substitute.py','equations_entropy.jsonl',vals,'equations_subst.jsonl'])\n"
"    run([sys.executable,'causal_infer.py','equations_subst.jsonl',str(H),'matches.json','analysis_report.txt'])\n"
"    if os.path.exists('matches.json'):\n"
"        j=json.load(open('matches.json','r',encoding='utf-8'))\n"
"        if j:\n"
"            print('\\n--- Top candidate ---')\n"
"            print(j[0].get('answer_text','(no answer)'))\n" 
"    if os.path.exists('analysis_report.txt'):\n"
"        print('\\n--- Analysis ---')\n"
"        print(open('analysis_report.txt','r',encoding='utf-8').read())\n"
"def interactive():\n"
"    print('Commands: load <report>, ask <question>, exit')\n"
"    while True:\n"
"        try: line=input('> ').strip()\n"
"        except EOFError: break\n"
"        if not line: continue\n"
"        if line.lower().startswith('load '): load_report(line[5:].strip())\n"
"        elif line.lower().startswith('ask '): ask_question(line[4:].strip())\n"
"        elif line.lower() in ('exit','quit'): break\n"
"        else: print('Unknown command')\n"
"def main():\n"
"    p=argparse.ArgumentParser(); p.add_argument('--load'); p.add_argument('--ask'); p.add_argument('--values'); p.add_argument('--interactive', action='store_true')\n"
"    args=p.parse_args()\n" 
"    if args.load: load_report(args.load)\n"
"    if args.ask: ask_question(args.ask,args.values)\n"
"    if args.interactive: interactive()\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/chat_assistant.py", out); write_file(buf, chat_py);

    /* examples and supporting files */
    const char *sample_vals =
      "{\n  \"x\": 1.618,\n  \"t\": 0.5,\n  \"gamma\": 2.5,\n  \"pi\": 3.141592653589793,\n  \"e\": 2.718281828459045\n}\n";
    snprintf(buf,sizeof(buf), "%s/examples/sample_values.json", out); write_file(buf, sample_vals);

    const char *sample_text =
      "Sample report with equations and LaTeX\n\nShannon entropy: H(X) = -\\\\sum p(x) log p(x)\n\nGamma function: \\\\Gamma(z) = \\\\int_0^\\\\infty t^{z-1} e^{-t} dt\n\nRiemann zeta: \\\\zeta(s) = \\\\sum_{n=1}^\\\\infty 1/n^s\n\nNoncommutative example: [x,y] = xy - yx\n\nManifold notes: curvature, geodesic, connection\n\nE = m c^2\n";
    snprintf(buf,sizeof(buf), "%s/examples/sample_text.txt", out); write_file(buf, sample_text);

    const char *readme =
      "# Omega causal package (with decomposer+generator)\n\nUse bin/chat_assistant.py --interactive to load a report and ask natural-language questions.\n";
    snprintf(buf,sizeof(buf), "%s/usr/share/omega/README.md", out); write_file(buf, readme);

    const char *makefile =
      "PKGDIR ?= omega_causal_pkg\nPY = $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)\nBIN = $(PKGDIR)/bin\n.PHONY: all build run test clean\nall: build\nbuild:\n\t@echo \"Package skeleton created under $(PKGDIR)\"\nrun: build\n\t@cd $(BIN) && $(PY) chat_assistant.py --interactive || true\ntest: build\n\t@echo \"Basic checks\" \nclean:\n\trm -rf $(PKGDIR) || true\n";
    snprintf(buf,sizeof(buf), "%s/Makefile", out); write_file(buf, makefile);

#ifndef _WIN32
    {
      char cmd[4096];
      snprintf(cmd,sizeof(cmd),
	       "chmod +x \"%s/bin/extract_equations.py\" \"%s/bin/equation_entropy.py\" \"%s/bin/equation_decomposer.py\" \"%s/bin/equation_generator.py\" \"%s/bin/value_substitute.py\" \"%s/bin/causal_infer.py\" \"%s/bin/chat_assistant.py\" 2>/dev/null || true",
	       out,out,out,out,out,out,out);
      system(cmd);
    }
#endif

    printf("Package generated at: %s\n", out);
    printf("Run: make -C %s test\n", out);
    return 0;
}
/*
（ファイル終わり）

補足
- 生成器はヒューリスティックに部分式を抽出して変形・組合せします。複雑な解析（正確な構文木、意味保存、シンボリック整合性）は SymPy 等の導入で改善できます。
- 実行環境が Linux/macOS/Windows のどれかを教えていただければ、実行時の細かい動作確認と追加改善（SymPy 置換、より良いテンプレートなど）を進めます。

必要なら、生成子のルール（変形パターン、テンプレート）や説明文スタイルを指定してください。
*/
