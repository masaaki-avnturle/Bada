/* pkginstallgen.c
   Generate a package that provides tools to:
    - extract sections/sentences/formula snippets from a report
    - compute sentence-level Shannon-entropy-like scores from the report
    - infer which sentences correspond to given "question entropy" targets
    - answer questions like "このレポートから何が出来るか" by matching entropy patterns
   Usage:
     gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c
     ./pkginstallgen ./omega_entropy_pkg
   Result: creates ./omega_entropy_pkg/bin/'*.py' and supporting files.
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
  const char *out = "omega_entropy_pkg";
  if (argc > 1) out = argv[1];
  char buf[8192];

  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);

  /* bin/extract_sections.py
       - Extract paragraphs, sentences and LaTeX inline/display math snippets.
       - Produce a simple JSON-lines file: one JSON object per sentence with fields:
         id, paragraph_index, sentence, math (bool), tokens...
  */
    const char *extract_py =
      "#!/usr/bin/env python3\n\"\"\"\nextract_sections.py\nExtract sentences and math snippets from a report.\nUsage: extract_sections.py input.txt out_sentences.jsonl\n\"\"\"\nimport sys,io,re,json\nfrom html import escape\nif len(sys.argv)<3:\n    print('Usage: extract_sections.py input.txt out_sentences.jsonl'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\ntext = open(fin,'r',encoding='utf-8').read()\n# Normalize newlines\ntext = text.replace('\\r\\n','\\n').replace('\\r','\\n')\n# Split into paragraphs\nparas = [p.strip() for p in re.split(r'\\n\\s*\\n', text) if p.strip()]\n# Simple sentence splitter tuned for Japanese/English: split on 。.!? and newlines\nsent_split = re.compile(r'(?<=。|\\.|\\?|!|！)\\s*')\nmath_inline = re.compile(r'\\\\\\((.+?)\\\\\\)|\\$(.+?)\\$|\\\\\\[(.+?)\\\\\\]', re.S)\ntoken_re = re.compile(r\"[A-Za-z0-9_]+|[\\u4e00-\\u9fff\\u3040-\\u309f\\u30a0-\\u30ff]+\", re.U)\nout = open(fout,'w',encoding='utf-8')\nsid = 0\nfor pi,p in enumerate(paras):\n    sents = [s.strip() for s in sent_split.split(p) if s and s.strip()]\n    for s in sents:\n        mats = math_inline.findall(s)\n        is_math = bool(mats)\n        tokens = token_re.findall(s)\n        obj = {'id':sid,'para':pi,'sentence':s,'math':is_math,'tokens':tokens}\n        out.write(json.dumps(obj, ensure_ascii=False) + '\\n')\n        sid += 1\nout.close()\nprint('Wrote',fout)\n";
    snprintf(buf, sizeof(buf), "%s/bin/extract_sections.py", out);
    write_file(buf, extract_py);

    /* bin/entropy_model.py
       - Load sentences JSONL, compute Shannon-like entropy per sentence from token frequencies.
       - Produce sentences_with_entropy.jsonl with added 'entropy' field (bits).
    */
    const char *entropy_py =
"#!/usr/bin/env python3\n\"\"\"\nentropy_model.py\nCompute sentence-level Shannon entropy from token frequency within the sentence.\nUsage: entropy_model.py sentences.jsonl out_sentences_entropy.jsonl\n\"\"\"\nimport sys,json,math\nif len(sys.argv)<3:\n    print('Usage: entropy_model.py sentences.jsonl out_sentences_entropy.jsonl'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\nlines = [json.loads(l) for l in open(fin,'r',encoding='utf-8') if l.strip()]\ndef shannon_entropy(tokens):\n    if not tokens: return 0.0\n    freq = {}\n    for t in tokens: freq[t] = freq.get(t,0)+1\n    total = len(tokens)\n    H = 0.0\n    for v in freq.values():\n        p = v/total\n        H -= p * math.log2(p)\n    return H\n# Optionally normalize by sentence length to get per-token entropy\nfor obj in lines:\n    H = shannon_entropy(obj.get('tokens',[]))\n    obj['entropy'] = H\nopen(fout,'w',encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in lines))\nprint('Wrote',fout)\n";
    snprintf(buf, sizeof(buf), "%s/bin/entropy_model.py", out);
    write_file(buf, entropy_py);

    /* bin/question_gen.py
       - Generate a set of questions (Japanese/English) including "何が出来るか" and entropy-targeted questions.
    */
    const char *question_py =
      "#!/usr/bin/env python3\n\"\"\"\nquestion_gen.py\nGenerate question templates including entropy-targeted variations.\nUsage: question_gen.py out_questions.txt\n\"\"\"\nimport sys\nif len(sys.argv)<2:\n    print('Usage: question_gen.py out_questions.txt'); sys.exit(2)\nout = sys.argv[1]\nqs = []\nqs.append('このレポートから何ができるか？(What can be done based on this report?)')\nqs.append('このレポートの主題は何か？(What is the main topic?)')\nqs.append('定理や主要主張はどのような記法で示されているか？(In what form are theorems presented?)')\nqs.append('証明の主要な手順はどの文に書かれているか？(Which sentences contain the main proof steps?)')\nqs.append('結論はどこにあり、何を述べているか？(Where is the conclusion and what does it state?)')\n# entropy-targeted questions: low/medium/high entropy examples\nqs.append('低エントロピー(=単純/要約的)な記述はどこにあるか？(Where are low-entropy sentences?)')\nqs.append('中程度のエントロピー(=説明的)な記述はどこにあるか？(Where are medium-entropy sentences?)')\nqs.append('高エントロピー(=情報量高/式多)な記述はどこにあるか？(Where are high-entropy sentences?)')\nqs.append('指定エントロピー値 H に最も一致する文を返してください。例: H=2.0')\nopen(out,'w',encoding='utf-8').write('\\n'.join(qs))\nprint('Wrote',out)\n";
snprintf(buf, sizeof(buf), "%s/bin/question_gen.py", out);
write_file(buf, question_py);

/* bin/qa_engine.py
       - Load sentences with entropy, questions; answer by:
       * for general capability questions: find paragraphs with keywords 'method','result','we propose' etc.
       * for entropy-targeted questions: find sentences with closest entropy to requested H
       * for 'what can be done' produce short structured answer with evidence snippets.
       */
    const char *qa_py =
      "#!/usr/bin/env python3\n\"\"\"\nqa_engine.py\nAnswer questions against a report by using sentence entropy and heuristics.\nUsage: qa_engine.py report.txt sentences_entropy.jsonl questions.txt out_answers.txt\nNotes: sentences_entropy.jsonl produced by extract_sections.py -> entropy_model.py\n\"\"\"\nimport sys, json, re, math\nfrom collections import Counter\nif len(sys.argv)<5:\n    print('Usage: qa_engine.py report.txt sentences_entropy.jsonl questions.txt out_answers.txt'); sys.exit(2)\nreport_file, sfile, qfile, outfile = sys.argv[1:5]\n# load sentence objects\nwith open(sfile,'r',encoding='utf-8') as f:\n    objs = [json.loads(line) for line in f if line.strip()]\n# build simple indices\nparas = {}\nfor o in objs:\n    paras.setdefault(o.get('para',0),[]).append(o)\nall_sents = objs\n# helper: find by keyword\ndef find_by_keywords(keywords, top=5):\n    hits = []\n    for o in all_sents:\n        txt = o.get('sentence','').lower()\n        score = sum(txt.count(k) for k in keywords)\n        if score>0:\n            hits.append((score, o))\n    hits.sort(key=lambda x:-x[0])\n    return [h[1] for h in hits[:top]]\n# helper: closest entropy\ndef closest_entropy(target_H, top=5):\n    arr = []\n    for o in all_sents:\n        H = o.get('entropy',0.0)\n        arr.append((abs(H - target_H), H, o))\n    arr.sort(key=lambda x: x[0])\n    return [a[2] for a in arr[:top]]\n# read questions\nqs = [l.strip() for l in open(qfile,'r',encoding='utf-8') if l.strip()]\nouts = []\nfor q in qs:\n    ql = q.lower()\n    if '何ができる' in q or 'what can be done' in ql:\n        # find methods/results\n        candidates = find_by_keywords(['method','methods','approach','we propose','we show','結果','方法','結果は','手法','示す','示した','propose','result'])\n        if candidates:\n            ans = 'このレポートから可能なこと（根拠付き）:\\n'\n            for c in candidates[:5]:\n                ans += '- ' + c.get('sentence','')[:400].replace('\\n',' ') + '\\n'\n        else:\n            ans = '明確な methods/results の記述は見つかりませんでした。本文冒頭や末尾の段落を確認してください。'\n        outs.append({'q':q,'a':ans})\n        continue\n    if '低エントロピー' in q or 'low-entropy' in ql:\n        # low entropy = H small\n        ranked = sorted(all_sents, key=lambda o: o.get('entropy',0.0))[:5]\n        ans = '低エントロピー文（要約的/繰り返しが多い）例:\\n'\n        for r in ranked: ans += '- H=%.3f: %s\\n' % (r.get('entropy',0.0), r.get('sentence','')[:300].replace('\\n',' '))\n        outs.append({'q':q,'a':ans}); continue\n    if '中程度' in q or 'medium-entropy' in ql:\n        # medium ~ median\n        Hs = sorted(o.get('entropy',0.0) for o in all_sents)\n        if Hs:\n            med = Hs[len(Hs)//2]\n        else:\n            med = 0.0\n        ranked = closest_entropy(med, top=5)\n        ans = '中程度エントロピー文（説明的）例:\\n'\n        for r in ranked: ans += '- H=%.3f: %s\\n' % (r.get('entropy',0.0), r.get('sentence','')[:300].replace('\\n',' '))\n        outs.append({'q':q,'a':ans}); continue\n    if '高エントロピー' in q or 'high-entropy' in ql:\n        ranked = sorted(all_sents, key=lambda o: -o.get('entropy',0.0))[:5]\n        ans = '高エントロピー文（式・新情報多）例:\\n'\n        for r in ranked: ans += '- H=%.3f: %s\\n' % (r.get('entropy',0.0), r.get('sentence','')[:400].replace('\\n',' '))\n        outs.append({'q':q,'a':ans}); continue\n    # entropy-specified pattern: e.g. H=2.0\n    m = re.search(r'H\\s*=\\s*([0-9]*\\.?[0-9]+)', q)\n    if m:\n        target = float(m.group(1))\n        found = closest_entropy(target, top=5)\n        ans = '指定エントロピー H=%.3f に近い文:\\n' % target\n        for f in found:\n            ans += '- H=%.3f: %s\\n' % (f.get('entropy',0.0), f.get('sentence','')[:400].replace('\\n',' '))\n        outs.append({'q':q,'a':ans}); continue\n    # fallback: try to match keywords and return best snippet\n    qtokens = re.findall(r\"[\\w\\u4e00-\\u9fff]+\", q)\n    best = None; best_score = 0\n    for o in all_sents:\n        txt = o.get('sentence','')\n        score = sum(1 for t in qtokens if t and t in txt)\n        if score > best_score:\n            best_score = score; best = o\n    if best_score>0 and best:\n        ans = '関連箇所:\\n- H=%.3f: %s\\n' % (best.get('entropy',0.0), best.get('sentence','')[:600].replace('\\n',' '))\n    else:\n        ans = '自動応答で該当箇所が見つかりませんでした。質問を具体化してください。'\n    outs.append({'q':q,'a':ans})\n# write answers file\nwith open(outfile,'w',encoding='utf-8') as fw:\n    for item in outs:\n        fw.write('Q: ' + item['q'] + '\\n')\n        fw.write('A: ' + item['a'] + '\\n\\n')\nprint('Wrote answers to', outfile)\n";
snprintf(buf, sizeof(buf), "%s/bin/qa_engine.py", out);
write_file(buf, qa_py);

/* etc/config */
    const char *etc_conf =
      "# omega_entropy_pkg config\n# No external LLM enabled by default; users can pipe answers to their LLM if desired\nllm_hook=false\n";
snprintf(buf, sizeof(buf), "%s/etc/config", out);
write_file(buf, etc_conf);

/* usr/share/omega/README.md */
    const char *usr_readme =
      "# Omega Entropy QA Package\n\nTools generated:\n - bin/extract_sections.py : extract sentences and math snippets\n - bin/entropy_model.py   : compute sentence-level Shannon entropy\n - bin/question_gen.py    : produce question templates (including entropy-targeted)\n - bin/qa_engine.py       : answer questions by matching entropy and heuristics\n\nQuick workflow:\n  python3 bin/extract_sections.py report.txt sentences.jsonl\n  python3 bin/entropy_model.py sentences.jsonl sentences_entropy.jsonl\n  python3 bin/question_gen.py questions.txt\n  python3 bin/qa_engine.py report.txt sentences_entropy.jsonl questions.txt answers.txt\n\nThe QA engine is heuristic: it uses token overlap, keyword matching and entropy-distance to pick evidence sentences.\n";
snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
write_file(buf, usr_readme);

/* Make scripts executable (UNIX) */
#ifndef _WIN32
{
  char cmd[8192];
  snprintf(cmd, sizeof(cmd),
	   "chmod +x \"%s/bin/extract_sections.py\" \"%s/bin/entropy_model.py\" \"%s/bin/question_gen.py\" \"%s/bin/qa_engine.py\" 2>/dev/null || true",
	   out, out, out, out);
  system(cmd);
}
#endif

printf("Omega entropy QA package created at: %s\n", out);
printf("Example workflow:\\n");
printf("  python3 %s/bin/extract_sections.py explorerfiles.pdf sentences.jsonl\\n", out);
printf("  python3 %s/bin/entropy_model.py sentences.jsonl sentences_entropy.jsonl\\n", out);
printf("  python3 %s/bin/question_gen.py questions.txt\\n", out);
printf("  python3 %s/bin/qa_engine.py explorerfiles.pdf sentences_entropy.jsonl questions.txt answers.txt\\n", out);
return 0;
}
