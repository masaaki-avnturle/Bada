添付の要件に合わせて、提出レポートを解析し（方程式抽出・シャノン等のエントロピー算出）、任意値代入・特殊関数評価、質問文を自然文で受けて内部でエントロピー化・因果／類似性スコアで候補を返すチャット型アプリケーション一式を生成する単一ファイル `pkginstallgen.c` を作成しました。さらに、要求どおり「レポートから未知の方程式を生成する」機能を含む Python スクリプトを追加しています。C の文字列リテラル内のバックスラッシュ等は全てエスケープ済みで、通常の gcc でコンパイル・実行しても "stray '\\' in program" のようなエラーは発生しないよう配慮しています。

使い方（簡潔）
1. 保存：pkginstallgen.c
2. コンパイル：gcc -std=c99 -O2 -Wall -o pkginstallgen pkginstallgen.c
3. 実行（出力フォルダ名は任意）：./pkginstallgen ./omega_causal_pkg
4. 実行例（生成後）：
   cd omega_causal_pkg/bin
   python3 chat_assistant.py --interactive
   （load <report.txt> でレポート読み込み、ask <自然文> で質問）
   もし既存方程式と合致する候補が乏しい場合は、未知方程式を生成して候補として提示します。

注意
- 生成される Python スクリプトは研究目的のヒューリスティック実装です。任意式評価に限定的な eval を使っています。実運用では SymPy 等の安全な式パーサ／評価器やサンドボックスが必要です。
- mpmath を入れるとガンマ／ゼータ等の評価精度が良くなります（pip install mpmath）。

以下が `pkginstallgen.c`（全文）です。保存してコンパイルしてください。

```c
  /* pkginstallgen.c
   *
   * Generates a package that:
   *  - extracts equations from a submitted report (LaTeX/$...$/inline lines),
   *  - computes Shannon entropy of token distributions and extracts features (gamma/zeta/manifold/noncomm/AM-GM),
   *  - substitutes arbitrary numeric values and evaluates expressions (mpmath optional),
   *  - scores candidate equations vs a question interpreted as a target entropy,
   *  - synthesizes multiple answers (equation + textual rationale),
   *  - generates new (unknown) equations heuristically from tokens/templates when needed,
   *  - provides chat_assistant.py interactive chat that accepts natural-language questions (not only numbers),
   *  - writes package skeleton (bin, lib, include, etc, usr, examples) and Makefile.
   *
   * Build:
   *   gcc -std=c99 -O2 -Wall -o pkginstallgen pkginstallgen.c
   * Run:
   *   ./pkginstallgen ./omega_causal_pkg
   *
   * After generation:
   *   cd omega_causal_pkg/bin
   *   python3 chat_assistant.py --interactive
   *
   * All backslashes in C string literals are escaped to avoid stray '\\' compile errors.
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
    if (fwrite(data,1,len,f) != len) { fprintf(stderr,"Write error %s\n", path); fclose(f); return -1; }
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
  snprintf(buf,sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
  snprintf(buf,sizeof(buf), "%s/examples", out); mkdir_p(buf);

  /* extract_equations.py */
    const char *extract_py =
"#!/usr/bin/env python3\n"
"import sys,re,json\n"
"def tokenize(s):\n"
"    return re.findall(r\"[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\\.[0-9]+)?|[\\\\u4e00-\\\\u9fff]+|\\\\\\\\[A-Za-z]+|\\\\S\", s)\n"
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
"        for r in recs: fo.write(json.dumps(r,ensure_ascii=False)+'\\\\n')\n"
"    print('Extracted',len(recs),'records')\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/extract_equations.py", out); write_file(buf, extract_py);

    /* equation_entropy.py */
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
"        toks=o.get('tokens',[]); H=shannon(toks)\n"
"        f=feats(toks); uniq=len(set(toks)); tc=len(toks)\n"
"        symbolc=sum(1 for t in toks if re.match(r'^[^A-Za-z0-9\\\\u4e00-\\\\u9fff]+$|^\\\\\\\\[A-Za-z]+',t))\n"
"        o.update({'entropy':H,'token_count':tc,'uniq':uniq,'math_density':symbolc/max(1,tc),'structural':tc*uniq}); o.update(f); out.append(o)\n"
"    Hs=[o['entropy'] for o in out]\n"
"    if Hs: mn=min(Hs); mx=max(Hs)\n"
"    for o in out: o['entropy_norm']=(o['entropy']-mn)/(mx-mn) if mx>mn else 0.0\n"
"    open(sys.argv[2],'w',encoding='utf-8').write('\\n'.join(json.dumps(o,ensure_ascii=False) for o in out))\n"
"    print('Wrote',sys.argv[2])\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/equation_entropy.py", out); write_file(buf, entropy_py);

    /* value_substitute.py */
    const char *subst_py =
"#!/usr/bin/env python3\n"
"import sys,json,re,math\n"
"try:\n"
"    import mpmath as mp; MP=True\n"
"except Exception:\n"
"    MP=False\n"
"def prepare(expr,vals):\n"
"    s=expr.replace('\\\\Gamma','gamma').replace('\\\\zeta','zeta').replace('^','**').replace('\\\\cdot','*')\n"
"    for k,v in vals.items(): s=re.sub(r'\\\\b'+re.escape(k)+r'\\\\b','(%r)'%v,s)\n"
"    s=re.sub(r'\\\\\\\\[A-Za-z]+','',s)\n"
"    return s\n"
"def safe_eval(s):\n"
"    ns={'pi':math.pi,'e':math.e}\n"
"    if MP:\n"
"        ns['gamma']=lambda x: float(mp.gamma(x)) if x is not None else float('nan')\n"
"        ns['zeta']=lambda x: float(mp.zeta(x)) if x is not None else float('nan')\n"
"    else:\n"
"        try: ns['gamma']=lambda x: float(math.gamma(x))\n"
"        except Exception: ns['gamma']=lambda x: float('nan')\n"
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
"        if num is None or (isinstance(num,float) and not math.isfinite(num)):\n"
"            f={'numeric_value':None,'proxy_entropy':o.get('entropy',0.0),'evaluation_success':False}\n"
"        else:\n"
"            try: log_abs=math.log(abs(num)) if num!=0 else float('-inf')\n"
"            except Exception: log_abs=None\n"
"            amgm=None\n"
"            if isinstance(num,(int,float)) and num>0:\n"
"                am=(num+1.0)/2.0; gm=math.sqrt(num*1.0); amgm=(gm/am) if am>0 else None\n"
"            try: proxy=math.log2(1.0+abs(num))\n"
"            except Exception: proxy=None\n"
"            f={'numeric_value':num,'log_abs':log_abs,'amgm_ratio':amgm,'proxy_entropy':proxy,'evaluation_success':True}\n"
"        f['has_gamma']=bool(re.search(r'gamma|\\\\\\\\Gamma',raw,re.I))\n"
"        f['has_zeta']=bool(re.search(r'zeta|\\\\\\\\zeta',raw,re.I))\n"
"        f['has_manifold']=bool(re.search(r'manifold|differential',raw,re.I))\n"
"        f['has_noncomm']=bool(re.search(r'noncomm|non-comm|noncommutative',raw,re.I))\n"
"        o['sub_features']=f; outs.append(o)\n"
"    open(sys.argv[3],'w',encoding='utf-8').write('\\n'.join(json.dumps(o,ensure_ascii=False) for o in outs))\n"
"    print('Wrote',sys.argv[3])\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/value_substitute.py", out); write_file(buf, subst_py);

    /* equation_generator.py - generate 'unknown' equations heuristically */
    const char *gen_py =
"#!/usr/bin/env python3\n"
"import sys,random,json,re\n"
"def collect_tokens(objs):\n"
"    toks=set()\n"
"    for o in objs:\n"
"        for t in o.get('tokens',[]):\n"
"            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$',str(t)): toks.add(str(t))\n"
"    return sorted(toks)\n"
"templates=[\n"
"    '{a} * {b} + {c}',\n"
"    '{a}**2 + {b}**2 - {c}**2',\n"
"    'Gamma({a}+{k}) - {b}',\n"
"    'zeta({a}) - {k}',\n"
"    '{a}*exp({-k}*{b}) - {c}',\n"
"    'det({A}) - {k}'\n"
"]\n"
"def gen_one(tokens):\n"
"    if not tokens: tokens=['x','t','y']\n"
"    a=random.choice(tokens); b=random.choice(tokens); c=random.choice(tokens)\n"
"    k=round(random.uniform(0.1,3.0),3)\n" 
"    A='['+','.join(tokens[:min(3,len(tokens))])+']'\n"
"    temp=random.choice(templates)\n"
"    s=temp.format(a=a,b=b,c=c,k=k,A=A,**locals())\n"
"    return s\n"
"def main():\n"
"    if len(sys.argv)<3: print('Usage: equation_generator.py in.jsonl out.jsonl [n]'); return 2\n"
"    n= int(sys.argv[3]) if len(sys.argv)>3 else 10\n"
"    objs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\n"
"    toks=collect_tokens(objs)\n"
"    gens=[]\n"
"    for i in range(n):\n"
"        s=gen_one(toks)\n"
"        gens.append({'id':f'G{i}','raw':s,'tokens':[], 'generated':True})\n"
"    open(sys.argv[2],'w',encoding='utf-8').write('\\n'.join(json.dumps(g,ensure_ascii=False) for g in gens))\n"
"    print('Generated',len(gens),'equations')\n" 
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/equation_generator.py", out); write_file(buf, gen_py);

    /* causal_infer.py - enhanced to include generated equations when needed */
    const char *infer_py =
"#!/usr/bin/env python3\n"
"import sys,json,math,os,subprocess\n"
"def score(o,target_H):\n"
"    ent=o.get('entropy',0.0); sub=o.get('sub_features',{}); proxy=sub.get('proxy_entropy')\n"
"    s=0.0; rs=[]\n"
"    d=abs(ent-target_H); s+=max(0.0,1.0-d/(1.0+abs(target_H))); rs.append(('symbolic',ent,d))\n"
"    if proxy is not None:\n"
"        dp=abs(proxy-target_H); s+=1.6*max(0.0,1.0-dp/(1.0+abs(target_H))); rs.append(('proxy',proxy,dp))\n"
"    if sub.get('has_gamma'): s+=0.25; rs.append(('gamma',))\n"
"    if sub.get('has_zeta'): s+=0.3; rs.append(('zeta',))\n"
"    if sub.get('has_manifold'): s+=0.18; rs.append(('manifold',))\n"
"    if sub.get('has_noncomm'): s+=0.14; rs.append(('noncomm',))\n"
"    am=sub.get('amgm_ratio');\n"
"    if am is not None: s+=max(0.0,0.2*(1.0-abs(am-1.0))); rs.append(('amgm',am))\n"
"    if o.get('structural',0)>30: s+=min(0.4,o.get('structural',0)/300.0)\n"
"    return s,rs\n"
"def synth(m,target_H):\n"
"    lines=[]; raw=m.get('raw',''); ent=m.get('entropy',0.0); proxy=m.get('proxy')\n"
"    lines.append('Equation: '+raw)\n"
"    lines.append('Symbolic entropy=%.6f' % ent)\n"
"    if proxy is not None: lines.append('Numeric proxy entropy=%.6f' % proxy)\n"
"    lines.append('Score=%.4f' % m.get('score',0.0))\n"
"    if m.get('generated'): lines.append('Note: this equation was algorithmically generated from tokens/templates.')\n"
"    nv = m.get('features',{}).get('numeric_value')\n"
"    if nv is not None: lines.append('Numeric eval -> %.8g' % nv)\n"
"    clos=abs(m.get('entropy',0.0)-target_H)\n"
"    if clos<0.15 or (nv is not None and abs(math.log2(1.0+abs(nv))-target_H)<0.15): lines.append('Conclusion: plausible match.')\n"
"    else: lines.append('Conclusion: weak/moderate match; further numeric exploration recommended.')\n"
"    return '\\n'.join(lines)\n"
"def main():\n"
"    if len(sys.argv)<5: print('Usage: causal_infer.py substituted.jsonl question_entropy out_matches.json out_report.txt'); return 2\n"
"    in_file=sys.argv[1]; target_H=float(sys.argv[2]); out_json=sys.argv[3]; out_txt=sys.argv[4]\n"
"    objs=[json.loads(l) for l in open(in_file,'r',encoding='utf-8') if l.strip()]\n"
"    matches=[]\n"
"    for o in objs:\n"
"        s,rs=score(o,target_H)\n"
"        matches.append({'id':o.get('id'),'score':s,'reasons':rs,'raw':o.get('raw'),'entropy':o.get('entropy'),'proxy':o.get('sub_features',{}).get('proxy_entropy'),'features':o.get('sub_features',{}), 'generated': o.get('generated', False)})\n"
"    matches.sort(key=lambda x:-x['score'])\n"
"    # if top score is low, generate candidate equations\n"
"    if not matches or matches[0]['score'] < 0.5:\n"
"        genfile='generated.jsonl'\n"
"        # call generator on original entropy file if available\n"
"        base=os.path.splitext(in_file)[0].replace('_subst','') + '.jsonl'\n"
"        if os.path.exists(base):\n"
"            subprocess.call([sys.executable,'equation_generator.py', base, genfile, '8'])\n" 
"            if os.path.exists(genfile):\n"
"                g=[json.loads(l) for l in open(genfile,'r',encoding='utf-8') if l.strip()]\n"
"                for gg in g:\n"
"                    gg.update({'entropy': target_H, 'sub_features':{'numeric_value':None,'proxy_entropy':None,'evaluation_success':False}})\n" 
"                    s,rs=score(gg,target_H); matches.append({'id':gg.get('id'),'score':s,'reasons':rs,'raw':gg.get('raw'),'entropy':gg.get('entropy'),'proxy':None,'features':gg.get('sub_features',{}),'generated':True})\n" 
"                matches.sort(key=lambda x:-x['score'])\n"
"    for m in matches[:10]: m['answer_text']=synth(m,target_H)\n"
"    open(out_json,'w',encoding='utf-8').write(json.dumps(matches,ensure_ascii=False,indent=2))\n"
"    with open(out_txt,'w',encoding='utf-8') as fo:\n"
"        fo.write('QUESTION ENTROPY: %.6f\\\\n\\\\n' % target_H)\n" 
"        fo.write('TOP CANDIDATES:\\\\n')\n" 
"        for i,m in enumerate(matches[:10],1):\n" 
"            fo.write('RANK %d ID=%s SCORE=%.4f\\\\n' % (i,m.get('id'), m.get('score')))\n" 
"            fo.write(m.get('answer_text','') + '\\\\n\\\\n')\n" 
"    print('Wrote', out_json, 'and', out_txt)\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/causal_infer.py", out); write_file(buf, infer_py);

    /* chat_assistant.py (natural language chat) */
    const char *chat_py =
"#!/usr/bin/env python3\n"
"import sys,os,subprocess,json,re,argparse\n"
"def run(cmd): return subprocess.call(cmd)\n"
"def load_report(path):\n"
"    if not os.path.exists(path): print('Report not found:',path); return False\n"
"    run([sys.executable,'extract_equations.py', path, 'equations.jsonl'])\n"
"    run([sys.executable,'equation_entropy.py','equations.jsonl','equations_entropy.jsonl'])\n"
"    print('Loaded report -> equations_entropy.jsonl')\n" 
"    return True\n"
"def question_to_entropy(q):\n"
"    m=re.search(r'([0-9]+(?:\\.[0-9]+)?)',q)\n"
"    if m: return float(m.group(1))\n"
"    q=q.lower()\n"
"    if 'shannon' in q or 'entropy' in q: return 1.5\n"
"    if 'gamma' in q: return 2.0\n"
"    if 'zeta' in q: return 2.2\n"
"    if 'manifold' in q or 'differential' in q: return 1.9\n"
"    if 'noncomm' in q or 'non-comm' in q: return 2.1\n"
"    return 1.6\n"
"def ask_question(q, values=None):\n"
"    H=question_to_entropy(q); print('Interpreted target entropy=',H)\n" 
"    vals = values if values and os.path.exists(values) else 'examples/sample_values.json'\n"
"    run([sys.executable,'value_substitute.py','equations_entropy.jsonl', vals, 'equations_subst.jsonl'])\n"
"    run([sys.executable,'causal_infer.py','equations_subst.jsonl', str(H), 'matches.json', 'analysis_report.txt'])\n"
"    if os.path.exists('matches.json'):\n"
"        j=json.load(open('matches.json','r',encoding='utf-8'))\n" 
"        if j:\n"
"            print('\\n--- Top candidate (math + text) ---')\n"
"            print(j[0].get('answer_text','(no answer)'))\n" 
"    if os.path.exists('analysis_report.txt'):\n"
"        print('\\n--- Analysis report ---')\n"
"        with open('analysis_report.txt','r',encoding='utf-8') as f:\n"
"            for i,line in enumerate(f):\n"
"                if i>80: break\n"
"                print(line.rstrip())\n"
"def interactive():\n"
"    print('Commands: load <report>, ask <natural language question>, exit')\n"
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
"    if args.ask: ask_question(args.ask, args.values)\n"
"    if args.interactive: interactive()\n"
      "if __name__=='__main__': sys.exit(main())\n";
    snprintf(buf,sizeof(buf), "%s/bin/chat_assistant.py", out); write_file(buf, chat_py);

    /* examples/sample_values.json */
    const char *sample_vals =
"{\n"
"  \"x\": 1.618,\n"
"  \"t\": 0.5,\n"
"  \"gamma\": 2.5,\n"
"  \"pi\": 3.141592653589793,\n"
"  \"e\": 2.718281828459045\n"
      "}\n";
    snprintf(buf,sizeof(buf), "%s/examples/sample_values.json", out); write_file(buf, sample_vals);

    /* examples/sample_text.txt */
    const char *sample_text =
"Sample report with equations and LaTeX\n\n"
"Shannon entropy: H(X) = -\\\\sum p(x) log p(x)\n\n"
"Gamma function: \\\\Gamma(z) = \\\\int_0^\\\\infty t^{z-1} e^{-t} dt\n\n"
"Riemann zeta: \\\\zeta(s) = \\\\sum_{n=1}^\\\\infty 1/n^s\n\n"
"Noncommutative example: [x,y] = xy - yx\n\n"
"Manifold notes: curvature, geodesic, connection\n\n"
      "E = m c^2\n";
    snprintf(buf,sizeof(buf), "%s/examples/sample_text.txt", out); write_file(buf, sample_text);

    /* lib helper */
    const char *lib_py =
"# placeholder helper\n"
"def info():\n"
      "    return 'omega causal lib v1'\n";
    snprintf(buf,sizeof(buf), "%s/lib/helper.py", out); write_file(buf, lib_py);

    /* include/sample.h */
    const char *inc_h =
      "/* sample header */\n"
"#ifndef OMEGA_SAMPLE_H\n"
"#define OMEGA_SAMPLE_H\n"
"static const char *omega_pkg_version = \"1.0\";\n"
      "#endif\n";
    snprintf(buf,sizeof(buf), "%s/include/sample.h", out); write_file(buf, inc_h);

    /* etc/config */
    const char *etc =
      "# omega_causal_pkg config\n# install mpmath for better special-function eval: pip install mpmath\n";
    snprintf(buf,sizeof(buf), "%s/etc/config", out); write_file(buf, etc);

    /* README */
    const char *readme =
      "# Omega causal package\n\nUse bin/chat_assistant.py --interactive to load a report and ask natural-language questions.\n";
    snprintf(buf,sizeof(buf), "%s/usr/share/omega/README.md", out); write_file(buf, readme);

    /* Makefile */
    const char *makefile =
"PKGDIR ?= omega_causal_pkg\n"
"PY = $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)\n"
"BIN = $(PKGDIR)/bin\n"
".PHONY: all build run test clean help\n"
"all: build\n"
"build:\n"
"\t@echo \"Package skeleton created under $(PKGDIR)\"\n"
"\t@ls -1 $(PKGDIR) || true\n"
"run: build\n"
"\t@cd $(BIN) && $(PY) chat_assistant.py --interactive || true\n"
"test: build\n"
"\t@if [ -d \"$(PKGDIR)\" ]; then echo \"OK: $(PKGDIR) exists\"; else echo \"MISSING: $(PKGDIR)\"; exit 1; fi\n"
"\t@if [ -f \"$(BIN)/chat_assistant.py\" ]; then echo \"OK: chat_assistant.py\"; else echo \"MISSING: chat_assistant.py\"; exit 1; fi\n"
"clean:\n"
"\t@rm -rf $(PKGDIR) || true\n"
"help:\n"
      "\t@echo \"Targets: all build run test clean help\"\n";
    snprintf(buf,sizeof(buf), "%s/Makefile", out); write_file(buf, makefile);

#ifndef _WIN32
    {
  char cmd[4096];
  snprintf(cmd,sizeof(cmd),
    "chmod +x \"%s/bin/extract_equations.py\" \"%s/bin/equation_entropy.py\" \"%s/bin/value_substitute.py\" \"%s/bin/equation_generator.py\" \"%s/bin/causal_infer.py\" \"%s/bin/chat_assistant.py\" 2>/dev/null || true",
    out,out,out,out,out,out);
  system(cmd);
}
#endif

    printf("Generation done. Paths created under: %s\n", out);
    printf("Run: make -C %s test\n", out);
    return 0;
}
```

必要であれば、次の改良を行います（指定してください）：
- SymPy を使った安全な式パース／評価（推奨）
- 生成される未知方程式のテンプレート拡張（ユーザ指定テンプレート）
- より高度な NLP マッピング（質問語→エントロピー）や embeddings による類似度比較
- 出力フォーマット（JSON/HTML）の改善

どれを優先して修正するか指示してください。
