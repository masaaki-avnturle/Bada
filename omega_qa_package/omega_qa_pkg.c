  /* pkginstallgen.c
   Generate a package skeleton that provides:
    - section/formula extraction from reports
    - question generation ("何ができるか", etc.)
    - a rule-based QA engine that attempts to answer many questions
    - simple AI hooks (template + Markov) and LLM hook placeholders

   Build:
     gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c

   Run:
     ./pkginstallgen ./omega_qa_package
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
    if (len == 0) return;
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
    const char *out = "omega_qa_package";
  if (argc > 1) out = argv[1];
  char buf[8192];

  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
    snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
    snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
snprintf(buf, sizeof(buf), "%s/package/src", out); mkdir_p(buf);

    /* bin/extract_sections.py
       Extract sections, sentences, formulas and metadata from a report file.
       Output a simple YAML-like file (sections.txt) for downstream QA.
    */
    const char *extract_py =
"#!/usr/bin/env python3\n\"\"\"\nextract_sections.py\nExtract sections (topic,theorem,proof,conclusion,conjecture), sentences and inline formulas.\nUsage: extract_sections.py input.txt out_sections.txt\nOutput: plain text with keys and blocks for QA engine.\n\"\"\"\nimport sys,re\nif len(sys.argv)<3:\n    print('Usage: extract_sections.py input.txt out_sections.txt'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\ntext = open(fin,'r',encoding='utf-8').read()\n# normalize\ntext = text.replace('\\r\\n','\\n').replace('\\r','\\n')\nlines = text.split('\\n')\n# collect paragraphs\nparas=[]\nbuf=[]\nfor ln in lines:\n    if ln.strip()=='' and buf:\n        paras.append(' '.join([l.strip() for l in buf if l.strip()]))\n        buf=[]\n    else:\n        buf.append(ln)\nif buf: paras.append(' '.join([l.strip() for l in buf if l.strip()]))\n# find headings and keywords\nkeys = ['topic','theorem','proof','conclusion','conjecture','methods','results']\npatterns = {\n    'topic': [r'^(目的|主題|topic|purpose)[:：\\-]?', r'\\b(this paper|we study|we propose|the purpose)\\b'],\n    'theorem': [r'^(定理|命題|theorem|proposition)[:：\\-]?', r'\\b(Theorem|Proposition)\\b'],\n    'proof': [r'^(証明|proof)[:：\\-]?', r'\\b(proof|示す|証明)\\b'],\n    'conclusion': [r'^(結論|まとめ|conclusion)[:：\\-]?', r'\\b(conclusion|we conclude)\\b'],\n    'conjecture': [r'^(予想|conjecture|hypothesis)[:：\\-]?', r'\\b(conjecture|予想)\\b'],\n    'methods': [r'^(方法|手法|methods|approach)[:：\\-]?', r'\\b(method|approach)\\b'],\n    'results': [r'^(結果|results)[:：\\-]?', r'\\b(result|we find|we show)\\b']\n}\nresults = {k: [] for k in keys}\n# scan paragraphs for patterns\nfor p in paras:\n    ps = p.strip()\n    for k, pats in patterns.items():\n        for pat in pats:\n            if re.search(pat, ps, re.IGNORECASE):\n                results[k].append(ps)\n                break\n        if results[k]: break\n# fallback: collect top sentences by keyword frequency\nif not any(results.values()):\n    sents = re.split(r'(?<=。|\\.|\\?|!|!\\?)\\s*', text)\n    for s in sents:\n        for k,pats in patterns.items():\n            for pat in pats:\n                if re.search(pat, s, re.IGNORECASE) and len(s.strip())>10:\n                    results[k].append(s.strip())\n                    break\n            if results[k]: break\n# collect inline math snippets (LaTeX) and any lines with common function names\nmaths = re.findall(r'\\\\\\((.+?)\\\\\\)|\\$(.+?)\\$', text, re.S)\nmaths = [''.join(t).strip() for t in maths if ''.join(t).strip()]\n# write output simple form\nwith open(fout,'w',encoding='utf-8') as outp:\n    outp.write('SECTIONS:\\n')\n    for k in keys:\n        outp.write(k+':\\n')\n        if results.get(k):\n            for item in results[k]:\n                outp.write('  - '+item.replace('\\n',' ')[:1000].replace('\\n',' ')+'\\n')\n        else:\n            outp.write('  - <NOT_FOUND>\\n')\n    outp.write('\\nMATH_SNIPPETS:\\n')\n    for m in maths[:200]:\n        outp.write('  - '+m.replace('\\n',' ')+'\\n')\nprint('Wrote sections to', fout)\n";
	 snprintf(buf, sizeof(buf), "%s/bin/extract_sections.py", out);
	 write_file(buf, extract_py);

	 /* bin/question_gen.py (generates many question templates based on sections) */
    const char *question_py =
	 "#!/usr/bin/env python3\n\"\"\"\nquestion_gen.py\nGenerate question templates focusing on '何ができるか' and related queries.\nUsage: question_gen.py sections.txt out_questions.txt\n\"\"\"\nimport sys\nif len(sys.argv)<3:\n    print('Usage: question_gen.py sections.txt out_questions.txt'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\nlines = open(fin,'r',encoding='utf-8').read().splitlines()\n# parse simple sections file\nsections = {}\ncur = None\nfor ln in lines:\n    if not ln.strip(): continue\n    if not ln.startswith('  - '):\n        cur = ln.strip().rstrip(':')\n        sections[cur] = []\n    else:\n        if cur is not None:\n            sections[cur].append(ln[4:])\n# question templates\nq = []\n# high-level capability question\nq.append('このレポートから何ができるようになりますか？ (What capabilities or conclusions does this report enable?)')\nq.append('Which tasks, computations, or proofs does this report enable or facilitate?')\n# per section targeted questions\nfor sec in ['SECTIONS','SECTIONS:','topic','methods','results','theorem','proof','conclusion','conjecture']:\n    label = sec\n    q.append(f'「{label}」セクションから何が得られますか？ (What can be obtained from the {label} section?)')\n    q.append(f'In what form are the main results presented in {label}? (equation, algorithm, experiment, example)')\n    q.append(f'If {label} contains formulas, list the main functions/symbols used and their role.')\n# deeper analytical questions\nq.append('Which parts of the report can be turned into reproducible code or experiments? Provide locations and brief plan.')\nq.append('What conjectures or open problems are suggested by the report? Provide references to supporting snippets.')\nq.append('What are possible next research directions suggested by this report?')\nq.append('Which equations would you try to formalize in a proof assistant? List candidates and why.')\n# write out\nwith open(fout,'w',encoding='utf-8') as outp:\n    for item in q:\n        outp.write(item+'\\n')\nprint('Wrote questions to', fout)\n";
	 snprintf(buf, sizeof(buf), "%s/bin/question_gen.py", out);
	 write_file(buf, question_py);

	 /* bin/qa_engine.py
       Rule-based QA engine: attempts to answer many questions using extracted sections,
       keyword matching, simple entailment heuristics, and optional external-LLM hook.
							   */
    const char *qa_py =
	 "#!/usr/bin/env python3\n\"\"\"\nqa_engine.py\nAttempt to answer a set of questions from a report. Uses heuristics:\n - direct match against extracted sections\n - keyword overlap scoring\n - math-snippet evidence linking\n - fallback to template summaries or optional external LLM (hook)\nUsage: qa_engine.py report.txt questions.txt out_answers.txt\nNote: External LLM usage is optional and must be configured by user (API key, endpoint).\n\"\"\"\nimport sys,re,math\nfrom collections import Counter\nif len(sys.argv)<4:\n    print('Usage: qa_engine.py report.txt questions.txt out_answers.txt'); sys.exit(2)\nreport_file, qfile, out_file = sys.argv[1], sys.argv[2], sys.argv[3]\ntext = open(report_file,'r',encoding='utf-8').read()\n# load questions\nquestions = [l.strip() for l in open(qfile,'r',encoding='utf-8') if l.strip()]\n# simple extraction: reuse extract_sections.py logic inline to avoid dependency\nparas = []\nbuf=[]\nfor ln in text.splitlines():\n    if ln.strip()=='' and buf:\n        paras.append(' '.join([l.strip() for l in buf if l.strip()])); buf=[]\n    else:\n        buf.append(ln)\nif buf: paras.append(' '.join([l.strip() for l in buf if l.strip()]))\n# build searchable index: paragraphs and math snippets\nindex = []\nfor p in paras:\n    index.append({'type':'para','text':p, 'tokens': re.findall(r\"[\\w\\u4e00-\\u9fff]+\", p)})\nmaths = re.findall(r'\\\\\\((.+?)\\\\\\)|\\$(.+?)\\$', text, re.S)\nfor m in maths:\n    mm = ''.join(m).strip()\n    if mm:\n        index.append({'type':'math','text':mm, 'tokens': re.findall(r\"[A-Za-z0-9_\\\\]+\", mm)})\n# utility: score overlap\ndef score_overlap(qtokens, doc_tokens):\n    if not qtokens or not doc_tokens: return 0.0\n    cdoc = Counter(doc_tokens); cq = Counter(qtokens)\n    common = sum(min(cq[w], cdoc.get(w,0)) for w in cq)\n    return common / max(1, len(qtokens))\n# answer generation\nanswers = []\nfor q in questions:\n    qlow = q.lower()\n    qtokens = re.findall(r\"[\\w\\u4e00-\\u9fff]+\", qlow)\n    # direct heuristics\n    if '何ができる' in q or 'what can' in qlow:\n        # look for methods/results paragraphs\n        candidates = [d for d in index if any(k in d['text'].lower() for k in ['結果','結果は','we show','we find','we demonstrate','we present','we propose','method','approach','algorithm'])]\n        if not candidates:\n            candidates = [d for d in index if len(d['text'])<400 and len(d['text'])>40]\n        # choose top by token overlap with 'method/result' keywords\n        best = sorted(candidates, key=lambda d: score_overlap(['result','method','we','show','we find','方法','結果'],' '.join(d['tokens'])), reverse=True)[:3]\n        if best:\n            ans = 'このレポートで可能なこと（抜粋）:\\n'\n            for b in best[:3]:\n                ans += '- ' + (b['text'][:400].replace('\\n',' ')) + '\\n'\n        else:\n            ans = '明示的な methods/results セクションは見つかりませんでした。本文の以下の箇所を参照してください:\\n' + (paras[0][:400] if paras else '---')\n        answers.append({'q':q, 'a':ans})\n        continue\n    # if question asks about form/notation\n    if '何に書いて' in q or 'in what form' in qlow or 'form' in qlow:\n        # check for math snippets or equations nearby\n        math_hits = [d for d in index if d['type']=='math']\n        if math_hits:\n            ans = '主に次の記法で書かれています: 数式表現（LaTeX風のインライン/表示式）。例:\\n'\n            for m in math_hits[:5]: ans += '- ' + m['text'][:200].replace('\\n',' ') + '\\n'\n        else:\n            # look for phrases that indicate algorithm/paragraph/figure\n            forms = []\n            for d in index:\n                t = d['text'].lower()\n                if any(w in t for w in ['algorithm','アルゴリズム','figure','図','table','表']): forms.append(d['text'][:200])\n            if forms:\n                ans = '記法/形式の例:\\n' + '\\n'.join('- '+f for f in forms[:5])\n            else:\n                ans = '明確な数式や図表は検出されませんでした。本文の段落に説明があるか確認してください。'\n        answers.append({'q':q, 'a':ans})\n        continue\n    # fallback: find best matching paragraph by token overlap\n    scores = [(score_overlap(qtokens, d['tokens']), d) for d in index]\n    scores.sort(key=lambda x: x[0], reverse=True)\n    if scores and scores[0][0]>0:\n        best = scores[0][1]\n        ans = '関連箇所（スニペット）:\\n' + best['text'][:600].replace('\\n',' ') + '\\n'\n    else:\n        ans = '該当箇所が自動検出できませんでした。キーワードを明確にするか、より具体的な質問をしてください。'\n    answers.append({'q':q, 'a':ans})\n# optional: call external LLM hook if configured (placeholder)\n# write answers\nwith open(out_file,'w',encoding='utf-8') as f:\n    for item in answers:\n        f.write('Q: ' + item['q'] + '\\n')\n        f.write('A: ' + item['a'] + '\\n\\n')\nprint('Wrote answers to', out_file)\n";
	 snprintf(buf, sizeof(buf), "%s/bin/qa_engine.py", out);
	 write_file(buf, qa_py);

	 /* bin/gen_ai.py - simple template + Markov (hook for answer refinement) */
    const char *gen_ai_py =
	 "#!/usr/bin/env python3\n\"\"\"\ngen_ai.py\nSimple template/Markov generator to refine answers or produce natural-language summaries.\nUsage: gen_ai.py input_snippets.txt out_refined.txt\n\"\"\"\nimport sys,random\nif len(sys.argv)<3:\n    print('Usage: gen_ai.py input_snippets.txt out_refined.txt'); sys.exit(2)\nfin, fout = sys.argv[1], sys.argv[2]\nlines=[l.strip() for l in open(fin,'r',encoding='utf-8') if l.strip()]\nif not lines:\n    open(fout,'w',encoding='utf-8').write('No input.')\n    print('Wrote',fout); sys.exit(0)\n# naive refinement: pick sentences and stitch\nout_lines=[]\nfor i in range(min(5,len(lines))):\n    s = lines[i]\n    # make short paraphrase heuristically\n    s2 = s.replace('This paper','本稿').replace('we','we').replace('propose','提案する')\n    out_lines.append(s2[:800])\nopen(fout,'w',encoding='utf-8').write('\\n\\n'.join(out_lines))\nprint('Wrote',fout)\n";
	 snprintf(buf, sizeof(buf), "%s/bin/gen_ai.py", out);
	 write_file(buf, gen_ai_py);

	 /* etc/config */
    const char *etc_conf =
	 "# omega_qa_package configuration\nllm_hook_enabled=false\nllm_hook_command=\n";
	 snprintf(buf, sizeof(buf), "%s/etc/config", out);
	 write_file(buf, etc_conf);

	 /* usr/share/omega/README.md */
    const char *usr_readme =
	 "# Omega QA Package\n\nThis package provides scripts to extract report content and answer many useful\nquestions about capabilities, form, reproducibility, next steps, and candidate\nformalisations. The QA engine is rule-based and heuristic; it can be augmented\nwith external LLMs via hooks (user must configure API/command).\n\nExample workflow:\n  python3 bin/extract_sections.py report.txt sections.txt\n  python3 bin/question_gen.py sections.txt questions.txt\n  python3 bin/qa_engine.py report.txt questions.txt answers.txt\n\nDependencies: python3. Optional: external LLM or NLP tools for better results.\n";
	 snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
	 write_file(buf, usr_readme);

	 /* Makefile (simple) */
    const char *makefile =
	 "all:\n\t@echo 'Package contains scripts in bin/; run them with python3'\n";
	 snprintf(buf, sizeof(buf), "%s/Makefile", out);
	 write_file(buf, makefile);

	 /* make scripts executable (UNIX) */
#ifndef _WIN32
	 {
	 char cmd[8192];
	 snprintf(cmd, sizeof(cmd),
		  "chmod +x \"%s/bin/extract_sections.py\" \"%s/bin/question_gen.py\" \"%s/bin/qa_engine.py\" \"%s/bin/gen_ai.py\" 2>/dev/null || true",
		  out, out, out, out);
	 system(cmd);
	 }
#endif

	 printf("Omega QA package created at: %s\n", out);
	 printf("Examples:\n  python3 %s/bin/extract_sections.py report.txt %s/sections.txt\n", out, out);
	 printf("  python3 %s/bin/question_gen.py %s/sections.txt %s/questions.txt\n", out, out, out);
	 printf("  python3 %s/bin/qa_engine.py report.txt %s/questions.txt %s/answers.txt\n", out, out, out);
	 return 0;
	 }
