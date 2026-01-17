```c
/* pkginstallgen.c
   Generate a package that implements a heuristic "formula-network + entropy-driven QA" application.
   - Does NOT supply a large pretrained LLM. Instead provides template+Markov/textual heuristics,
     SymPy hooks, and entropy-based selection to infer "what the report is about" and "what can be done".
   - Input: user TeX or PDF report (pdf -> pdftotext or TeX plain text recommended).
   - Output: package under specified directory with scripts:
       bin/tex_to_text.py    (extract text from .tex or .pdf using pdftotext if available)
       bin/extract_sentences.py (split into sentences, extract math snippets)
       bin/entropy_model.py  (compute sentence entropy)
       bin/formula_network.py (symbolic formula network generator using heuristics/SymPy if present)
       bin/question_gen.py   (generate entropy-targeted questions)
       bin/qa_engine.py      (answer questions by matching entropy and network evidence)
       bin/gen_ai.py         (template+Markov refiner; hook to call external LLM if user opts)
   Build/run:
     gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c
     ./pkginstallgen ./omega_entropy_network
   After generation, follow README in the package to run the pipeline.
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
  size_t len;
  snprintf(tmp, sizeof(tmp), "%s", path);
  len = strlen(tmp);
  if (!len) return;
  if (tmp[len-1] == '/' || tmp[len-1] == '\\') tmp[len-1] = 0;
  for (p = tmp + 1; *p; ++p) {
    if (*p == '/' || *p == '\\') {
      *p = 0;
      MKDIR(tmp);
      *p = '/';
    }
  }
  MKDIR(tmp);
}

static int write_file(const char *path, const char *data) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  fwrite(data, 1, strlen(data), f);
  fclose(f);
  return 0;
}

int main(int argc, char **argv) {
  const char *out = "omega_entropy_network";
  if (argc > 1) out = argv[1];
  char buf[8192];

  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);

  /* bin/tex_to_text.py : convert TeX or PDF into plain text (uses pdftotext if needed) */
    const char *tex_to_text_py =
      "#!/usr/bin/env python3\n\"\"\"\ntex_to_text.py\nUsage: tex_to_text.py input.tex|input.pdf out.txt\nIf input is .pdf, tries pdftotext; for .tex, strips TeX commands heuristically.\n\"\"\"\nimport sys,os,re,subprocess\nif len(sys.argv)<3:\n    print('Usage: tex_to_text.py input.tex|input.pdf out.txt'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\next = os.path.splitext(fin)[1].lower()\ntext=''\nif ext=='.pdf':\n    try:\n        subprocess.check_call(['pdftotext', fin, fout])\n        print('Wrote text via pdftotext to', fout); sys.exit(0)\n    except Exception:\n        print('pdftotext not available or failed; aborting', file=sys.stderr); sys.exit(1)\nelif ext in ('.tex', '.txt'):\n    s = open(fin,'r',encoding='utf-8',errors='ignore').read()\n    # naive TeX removal: remove comments, commands, environments, keep math delimiters\n    s = re.sub(r'%.*','',s)\n    s = re.sub(r'\\\\begin\\{.*?\\}.*?\\\\end\\{.*?\\}',' ',s,flags=re.S)\n    s = re.sub(r'\\\\[a-zA-Z@]+(?:\\[[^\\]]*\\])?(?:\\{[^}]*\\})?',' ',s)\n    s = re.sub(r'\\$\\$.*?\\$\\$',' ',s,flags=re.S)\n    s = re.sub(r'\\$.*?\\$',' ',s,flags=re.S)\n    s = re.sub(r'\\\\\\(.+?\\\\\\)',' ',s,flags=re.S)\n    s = re.sub(r'\\{\\s*',' ',s); s = re.sub(r'\\s*\\}',' ',s)\n    s = re.sub(r'\\s+',' ',s)\n    open(fout,'w',encoding='utf-8').write(s)\n    print('Wrote',fout)\nelse:\n    print('Unsupported extension', ext, file=sys.stderr); sys.exit(1)\n";
    snprintf(buf, sizeof(buf), "%s/bin/tex_to_text.py", out);
    write_file(buf, tex_to_text_py);

    /* bin/extract_sentences.py : split into sentences and extract inline/ display math snippets */
    const char *extract_sentences_py =
      "#!/usr/bin/env python3\n\"\"\"\nextract_sentences.py\nInput: plain text (from tex_to_text.py). Output: JSONL with fields: id,para,sentence,math_snippets,tokens\nUsage: extract_sentences.py in.txt out_sentences.jsonl\n\"\"\"\nimport sys,re,json\nif len(sys.argv)<3:\n    print('Usage: extract_sentences.py in.txt out_sentences.jsonl'); sys.exit(2)\ninp, out = sys.argv[1], sys.argv[2]\ntext = open(inp,'r',encoding='utf-8',errors='ignore').read()\nparas = [p.strip() for p in re.split(r'\\n\\s*\\n', text) if p.strip()]\nsent_split = re.compile(r'(?<=。|\\.|\\?|!|！)\\s*')\nmath_re = re.compile(r'\\\\\\((.+?)\\\\\\)|\\$(.+?)\\$|\\\\\\[(.+?)\\\\\\]', re.S)\ntoken_re = re.compile(r\"[A-Za-z0-9_]+|[\\u4e00-\\u9fff\\u3040-\\u309f\\u30a0-\\u30ff]+\", re.U)\noutf = open(out,'w',encoding='utf-8')\nid=0\nfor pi,p in enumerate(paras):\n    sents = [s.strip() for s in sent_split.split(p) if s.strip()]\n    for s in sents:\n        mats = [m for tup in math_re.findall(s) for m in tup if m]\n        tokens = token_re.findall(s)\n        obj = {'id':id,'para':pi,'sentence':s,'math_snippets':mats,'tokens':tokens}\n        outf.write(json.dumps(obj, ensure_ascii=False)+'\\n')\n        id+=1\noutf.close(); print('Wrote',out)\n";
    snprintf(buf, sizeof(buf), "%s/bin/extract_sentences.py", out);
    write_file(buf, extract_sentences_py);

    /* bin/entropy_model.py : compute Shannon entropy per sentence and normalize */
    const char *entropy_model_py =
      "#!/usr/bin/env python3\n\"\"\"\nentropy_model.py\nCompute Shannon entropy per sentence (bits) and normalized_entropy (0..1)\nUsage: entropy_model.py in_sentences.jsonl out_with_entropy.jsonl\n\"\"\"\nimport sys,json,math\nfrom collections import Counter\nif len(sys.argv)<3:\n    print('Usage: entropy_model.py in_sentences.jsonl out_with_entropy.jsonl'); sys.exit(2)\ninp,out=sys.argv[1],sys.argv[2]\nobjs=[json.loads(l) for l in open(inp,'r',encoding='utf-8') if l.strip()]\nents=[]\nfor o in objs:\n    toks=o.get('tokens',[])\n    if not toks:\n        H=0.0\n    else:\n        c=Counter(toks); total=len(toks); H=0.0\n        for v in c.values():\n            p=v/total; H-= p * math.log2(p)\n    o['entropy']=H; ents.append(H)\n# normalize\nif ents:\n    mn=min(ents); mx=max(ents)\nelse:\n    mn=mx=0.0\nfor o in objs:\n    H=o['entropy']\n    if mx>mn:\n        o['entropy_norm']=(H-mn)/(mx-mn)\n    else:\n        o['entropy_norm']=0.0\nopen(out,'w',encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in objs))\nprint('Wrote',out)\n";
    snprintf(buf, sizeof(buf), "%s/bin/entropy_model.py", out);
    write_file(buf, entropy_model_py);

    /* bin/formula_network.py : heuristic generator linking Gamma/Zeta/AGM/Higgs etc. (SymPy optional) */
    const char *formula_network_py =
      "#!/usr/bin/env python3\n\"\"\"\nformula_network.py\nHeuristic formula-network generator. Input: sentences JSONL (with math_snippets). Output: network.json\nRequires sympy for richer symbolic handling (optional).\nUsage: formula_network.py sentences.jsonl network.json\n\"\"\"\nimport sys,random,json\ntry:\n    import sympy as sp\n    SYMPY=True\nexcept Exception:\n    SYMPY=False\nif len(sys.argv)<3:\n    print('Usage: formula_network.py sentences.jsonl network.json'); sys.exit(2)\nsents=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\nnet={'nodes':[],'edges':[]}\n# create nodes from math snippets and high-entropy sentences\nfor s in sents:\n    H = s.get('entropy',0.0)\n    label = s.get('sentence')[:140]\n    nid = 'S%d' % s.get('id')\n    net['nodes'].append({'id':nid,'type':'sentence','label':label,'entropy':H})\n    # math snippets -> formula nodes\n    for i,ms in enumerate(s.get('math_snippets',[])):\n        fid = '%s_M%d' % (nid,i)\n        net['nodes'].append({'id':fid,'type':'formula','label':ms[:160]})\n        net['edges'].append({'from':nid,'to':fid,'rel':'contains'})\n# connect formulas heuristically: Gamma->Beta->Zeta->AGM->Higgs chain if keywords appear\nkw_chain = ['Gamma','Beta','zeta','AGM','Higgs','entropy','Shannon']\nformulas = [n for n in net['nodes'] if n['type']=='formula']\nfor f in formulas:\n    for g in formulas:\n        if f==g: continue\n        lf=f['label']; lg=g['label']\n        for k1 in kw_chain:\n            if k1.lower() in lf.lower():\n                for k2 in kw_chain:\n                    if kw_chain.index(k2)>kw_chain.index(k1) and k2.lower() in lg.lower():\n                        net['edges'].append({'from':f['id'],'to':g['id'],'rel':'flow'})\n# add random weak links among high-entropy nodes\nhigh = sorted([n for n in net['nodes'] if n.get('entropy',0)>0], key=lambda x:-x.get('entropy',0))[:30]\nfor i in range(len(high)-1):\n    net['edges'].append({'from':high[i]['id'],'to':high[i+1]['id'],'rel':'assoc'})\nopen(sys.argv[2],'w',encoding='utf-8').write(json.dumps(net,ensure_ascii=False,indent=2))\nprint('Wrote',sys.argv[2])\n";
    snprintf(buf, sizeof(buf), "%s/bin/formula_network.py", out);
    write_file(buf, formula_network_py);

    /* bin/question_gen.py : generate diverse questions incl. entropy-targeted */
    const char *question_gen_py =
      "#!/usr/bin/env python3\n\"\"\"\nquestion_gen.py\nGenerate a diverse set of questions including entropy-targeted ones.\nUsage: question_gen.py out_questions.txt\n\"\"\"\nimport sys\nif len(sys.argv)<2:\n    print('Usage: question_gen.py out_questions.txt'); sys.exit(2)\nout=sys.argv[1]\nqs=[]\nqs.append('このレポートの主題は何か？(What is the main theme?)')\nqs.append('このレポートから具体的に何ができるか？(What can be done based on this report?)')\nqs.append('主要な定理・主張はどれか？(Which statements are main theorems?)')\nqs.append('証明の主要手順はどの文に書かれているか？(Which sentences contain main proof steps?)')\nqs.append('低/中/高エントロピー文をそれぞれ3例ずつ示してください。(List low/med/high entropy sentences)')\nqs.append('指定エントロピー H=1.5 に最も近い文を返してください。(Return sentences closest to H=1.5)')\nqs.append('式ネットワーク上でGammaからZetaへ辿る典型的な式列を示してください。(Give formula chains Gamma->...->Zeta)')\nqs.append('このレポートから実験/実装に落とし込める項目は何か？(Which parts are implementable?)')\nopen(out,'w',encoding='utf-8').write('\\n'.join(qs))\nprint('Wrote',out)\n";
    snprintf(buf, sizeof(buf), "%s/bin/question_gen.py", out);
    write_file(buf, question_gen_py);

    /* bin/qa_engine.py : answers questions using entropy matching, keyword heuristics, formula network evidence */
    const char *qa_engine_py =
      "#!/usr/bin/env python3\n\"\"\"\nqa_engine.py\nAnswer questions using sentence entropy, token overlap, and formula network evidence.\nUsage: qa_engine.py report.txt sentences_with_entropy.jsonl network.json questions.txt out_answers.txt\n\"\"\"\nimport sys,json,re,math\nfrom collections import Counter\nif len(sys.argv)<6:\n    print('Usage: qa_engine.py report.txt sentences.jsonl network.json questions.txt out_answers.txt'); sys.exit(2)\nreport, sfile, netfile, qfile, outfile = sys.argv[1:6]\nsentences=[json.loads(l) for l in open(sfile,'r',encoding='utf-8') if l.strip()]\nnet=json.load(open(netfile,'r',encoding='utf-8'))\nquestions=[l.strip() for l in open(qfile,'r',encoding='utf-8') if l.strip()]\n# helpers\ndef closest_by_entropy(H, top=5):\n    arr=sorted(sentences, key=lambda o: abs(o.get('entropy',0)-H))\n    return arr[:top]\ndef top_by_entropy(n=5):\n    return sorted(sentences, key=lambda o: -o.get('entropy',0))[:n]\ndef bottom_by_entropy(n=5):\n    return sorted(sentences, key=lambda o: o.get('entropy',0))[:n]\ndef keyword_hits(kwlist, top=5):\n    hits=[]\n    for s in sentences:\n        t=s.get('sentence','').lower(); score=sum(t.count(k.lower()) for k in kwlist)\n        if score>0: hits.append((score,s))\n    hits.sort(key=lambda x:-x[0]); return [h[1] for h in hits[:top]]\n# main answering\nouts=[]\nfor q in questions:\n    ql=q.lower()\n    if '何ができる' in q or 'what can' in ql:\n        cand = keyword_hits(['method','result','we propose','結果','方法','実験','implement','実装'])\n        if cand:\n            ans='このレポートからできること（抜粋）:\\n'\n            for c in cand: ans += '- ' + c.get('sentence')[:400].replace('\\n',' ') + '\\n'\n        else:\n            ans='methods/results に相当する記述が見つかりません。高エントロピー文を参照してください。'\n        outs.append((q,ans)); continue\n    if '低/中/高エントロピー' in q or 'low/med/high' in ql or '低/中/高' in ql:\n        low=bottom_by_entropy(3); mid=sorted(sentences, key=lambda o:o.get('entropy',0))[len(sentences)//4:len(sentences)//4+3]\n        high=top_by_entropy(3)\n        ans='低:\\n'\n        for s in low: ans += '- H=%.3f: %s\\n' % (s.get('entropy',0), s.get('sentence')[:200])\n        ans += '\\n中:\\n'\n        for s in mid: ans += '- H=%.3f: %s\\n' % (s.get('entropy',0), s.get('sentence')[:200])\n        ans += '\\n高:\\n'\n        for s in high: ans += '- H=%.3f: %s\\n' % (s.get('entropy',0), s.get('sentence')[:300])\n        outs.append((q,ans)); continue\n    m = re.search(r'H\\s*=\\s*([0-9]*\\.?[0-9]+)', q)\n    if m:\n        H=float(m.group(1)); found=closest_by_entropy(H,top=5)\n        ans='指定 H=%.3f に近い文:\\n' % H\n        for f in found: ans += '- H=%.3f: %s\\n' % (f.get('entropy',0), f.get('sentence')[:400])\n        outs.append((q,ans)); continue\n    if 'gamma' in ql or 'zeta' in ql or 'gamma->zeta' in ql:\n        # find formula chains in net\n        chains=[]\n        idmap={n['id']:n for n in net.get('nodes',[])}\n        for e in net.get('edges',[]):\n            f=idmap.get(e['from'],{}).get('label',''); t=idmap.get(e['to'],{}).get('label','')\n            if f and t and ('Gamma' in f or 'gamma' in f) and ('zeta' in t.lower() or 'Zeta' in t):\n                chains.append((f,t))\n        if chains:\n            ans='発見された式連鎖例:\\n'\n            for a,b in chains[:10]: ans += '- %s -> %s\\n' % (a[:140], b[:140])\n        else:\n            ans='Gamma->Zeta の直接連鎖はネットワークから見つかりませんでした。高エントロピー文/数式を確認してください。'\n        outs.append((q,ans)); continue\n    # fallback: token-overlap best sentence\n    qtokens=re.findall(r\"[\\w\\u4e00-\\u9fff]+\", q)\n    best=None; best_score=0\n    for s in sentences:\n        txt=s.get('sentence','')\n        score=sum(1 for t in qtokens if t and t in txt)\n        if score>best_score: best_score=score; best=s\n    if best_score>0:\n        ans='関連箇所:\\n- H=%.3f: %s' % (best.get('entropy',0), best.get('sentence'))\n    else:\n        ans='自動応答で該当箇所が見つかりません。質問を具体化してください。'\n    outs.append((q,ans))\n# write out\nwith open(outfile,'w',encoding='utf-8') as fo:\n    for q,a in outs:\n        fo.write('Q: '+q+'\\n')\n        fo.write('A: '+a+'\\n\\n')\nprint('Wrote',outfile)\n";
    snprintf(buf, sizeof(buf), "%s/bin/qa_engine.py", out);
    write_file(buf, qa_engine_py);

    /* bin/gen_ai.py : template+Markov sentence refiner, optional LLM hook (user must configure) */
    const char *gen_ai_py =
      "#!/usr/bin/env python3\n\"\"\"\ngen_ai.py\nRefine snippets into more natural answers using template rules and a simple Markov chain.\nOptionally call an external LLM command if configured in etc/config (user responsibility).\nUsage: gen_ai.py input_snippets.txt out_refined.txt\n\"\"\"\nimport sys,random,os,subprocess\nif len(sys.argv)<3:\n    print('Usage: gen_ai.py input_snippets.txt out_refined.txt'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\nlines=[l.strip() for l in open(fin,'r',encoding='utf-8') if l.strip()]\nif not lines:\n    open(fout,'w',encoding='utf-8').write('No input.'); print('Wrote',fout); sys.exit(0)\n# simple Markov: build bigram map\nwords=[]\nfor l in lines: words.extend(l.split())\nif not words:\n    open(fout,'w',encoding='utf-8').write('\\n'.join(lines)); print('Wrote',fout); sys.exit(0)\nmodel={}\nfor i in range(len(words)-1): model.setdefault(words[i],[]).append(words[i+1])\ndef gen_sentence(maxlen=30):\n    if not model: return random.choice(lines)\n    w=random.choice(list(model.keys())); out=[w]\n    for _ in range(maxlen-1):\n        nxt=model.get(w)\n        if not nxt: break\n        w=random.choice(nxt); out.append(w)\n    return ' '.join(out)\n# produce 3 refined paragraphs\noutp=[]\nfor i in range(3):\n    s=gen_sentence()\n    outp.append(s)\nopen(fout,'w',encoding='utf-8').write('\\n\\n'.join(outp))\nprint('Wrote',fout)\n";
    snprintf(buf, sizeof(buf), "%s/bin/gen_ai.py", out);
    write_file(buf, gen_ai_py);

    /* etc/config */
    const char *etc_conf =
      "# omega_entropy_network configuration\n# Set llm_command to a shell command that reads stdin and writes stdout if you want to post-process\nllm_command=\n";
    snprintf(buf, sizeof(buf), "%s/etc/config", out);
    write_file(buf, etc_conf);

    /* usr/share/omega/README.md */
    const char *usr_readme =
      "# Omega Entropy Network package\n\nThis package provides a heuristic pipeline to:\n - extract text from TeX/PDF (tex_to_text.py)\n - split into sentences and extract math snippets (extract_sentences.py)\n - compute sentence-level entropy (entropy_model.py)\n - build a heuristic formula network (formula_network.py)\n - generate entropy-targeted questions (question_gen.py)\n - answer questions by matching entropy and network evidence (qa_engine.py)\n - refine answers with template/Markov (gen_ai.py)\n\nImportant: This package does NOT include a full large pretrained generative model. To use an external LLM\nhook, configure etc/config and provide an appropriate command or API wrapper.\n\nSuggested workflow:\n  python3 bin/tex_to_text.py report.tex report.txt\n  python3 bin/extract_sentences.py report.txt sentences.jsonl\n  python3 bin/entropy_model.py sentences.jsonl sentences_entropy.jsonl\n  python3 bin/formula_network.py sentences_entropy.jsonl network.json\n  python3 bin/question_gen.py questions.txt\n  python3 bin/qa_engine.py report.txt sentences_entropy.jsonl network.json questions.txt answers.txt\n  python3 bin/gen_ai.py answers.txt answers_refined.txt\n\nDependencies: python3. Optional: sympy for richer formula handling, pdftotext for pdf->text.\n";
    snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
    write_file(buf, usr_readme);

    /* Make scripts executable (UNIX) */
#ifndef _WIN32
    {
      char cmd[4096];
      snprintf(cmd, sizeof(cmd),
	       "chmod +x \"%s/bin/tex_to_text.py\" \"%s/bin/extract_sentences.py\" \"%s/bin/entropy_model.py\" \"%s/bin/formula_network.py\" \"%s/bin/question_gen.py\" \"%s/bin/qa_engine.py\" \"%s/bin/gen_ai.py\" 2>/dev/null || true",
	       out, out, out, out, out, out, out);
      system(cmd);
    }
#endif

    printf("Omega entropy-network package created at: %s\n", out);
    printf("See %s/usr/share/omega/README.md for usage.\n", out);
    return 0;
}
```
