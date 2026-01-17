/*以下に、要求どおり「提出レポートを読み、チャットで自然文の質問を受けると、質問文を内部でエントロピー化し（シャノン等）、提出された方程式群からシャノンの公式、ゼータ関数、ガンマ関数、AM-GM（相加相乗平均）や多様体・非可換などの特徴を抽出して、任意の数値を代入・評価し、因果的・エントロピー類似性で複数の解答（数式＋説明文）を返すパッケージ一式を生成する単一ファイル pkginstallgen.c を示します。C文字列中のバックスラッシュは適切にエスケープしてありますので、通常の gcc コンパイルで "stray '\' in program" のようなエラーは出ません。ファイルを保存し、コンパイルして実行してください。

コンパイル：
  gcc -std=c99 -O2 -Wall -o pkginstallgen pkginstallgen.c

実行（生成フォルダ名は任意）：
  ./pkginstallgen ./omega_causal_pkg

生成例の実行（生成後）：
  cd omega_causal_pkg/bin
  python3 chat_assistant.py --interactive
  （load <report.txt> でレポート読み込み、ask <自然文> で質問）

注意：
- 生成される Python スクリプト群はヒューリスティック実装です。任意式評価には限定的な eval を使用します。実運用では SymPy 等の安全なパーサ／評価器や／および適切なサンドボックスが必要です。
- 高精度特殊関数評価を行うには mpmath のインストールを推奨します（pip install mpmath）。

以下が pkginstallgen.c の全文です（長いので保存してからコンパイルしてください）。

```c
*/
		    /* pkginstallgen.c
		     *
		     * Generate a package that:
		     *  - extracts equations from a submitted report,
		     *  - computes Shannon entropy and heuristic features (zeta,gamma,AM-GM,manifold,noncomm),
		     *  - substitutes arbitrary numeric values (mpmath optional) and computes proxy entropies,
		     *  - accepts natural-language chat questions, internalizes them as a target entropy (heuristic),
		     *    scores candidate equations by symbolic and numeric proxy entropy and special-function cues,
		     *    and synthesizes multiple answers (equation + textual rationale),
		     *  - writes a package layout (bin, lib, include, etc, usr, examples) and a safe Makefile.
		     *
		     * Build:
		     *   gcc -std=c99 -O2 -Wall -o pkginstallgen pkginstallgen.c
		     * Run:
		     *   ./pkginstallgen ./omega_causal_pkg
		     *
		     * Notes:
		     *  - All backslashes in C string literals are escaped to avoid stray '\\' compile errors.
		     *  - The generated Python scripts are heuristic; for production replace evals with SymPy/sandboxed evaluators.
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
		      if (!f) {
			fprintf(stderr, "Failed to open %s for writing\n", path);
			return -1;
		      }
		      size_t len = strlen(data);
		      if (fwrite(data, 1, len, f) != len) {
			fprintf(stderr, "Write error %s\n", path);
			fclose(f);
			return -1;
		      }
		      fclose(f);
		      return 0;
		    }

		    int main(int argc, char **argv) {
		      const char *out = "omega_causal_pkg";
		      if (argc > 1 && argv[1][0] != '\\0') out = argv[1];
		      char buf[16384];

		      printf("Generating package at: %s\n", out);

		      /* create directories */
		      snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
		      snprintf(buf, sizeof(buf), "%s/lib", out); mkdir_p(buf);
		      snprintf(buf, sizeof(buf), "%s/include", out); mkdir_p(buf);
		      snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
		      snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
		      snprintf(buf, sizeof(buf), "%s/examples", out); mkdir_p(buf);

		      /* bin/extract_equations.py */
    const char *extract_equations_py =
"#!/usr/bin/env python3\n"
"import sys, re, json\n"
"def tokenize(s):\n"
"    return re.findall(r\"[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\\.[0-9]+)?|[\\\\u4e00-\\\\u9fff]+|\\\\\\\\[A-Za-z]+|\\\\S\", s)\n"
"def extract(text):\n"
"    math_re = re.compile(r'\\\\\\\\\\[(.+?)\\\\\\\\\\]|\\\\\\\\\\((.+?)\\\\\\\\\\)|\\$\\$(.+?)\\$\\$|\\$(.+?)\\$', re.S)\n"
"    line_re = re.compile(r'^[^\\\\n]*[=<>≈∼\\\\+\\\\-\\\\^\\\\*\\\\/:]+[^\\\\n]*$', re.M)\n"
"    out = []\n"
"    seen = 0\n"
"    for m in math_re.findall(text):\n"
"        content = ''.join(m).strip()\n"
"        if content and len(content) > 2:\n"
"            out.append({'id':'M%d'%seen,'raw':content,'tokens':tokenize(content),'latex':True})\n"
"            seen += 1\n"
"    for ln in line_re.findall(text):\n"
"        s = ln.strip()\n"
"        if len(s) > 4:\n"
"            out.append({'id':'L%d'%seen,'raw':s,'tokens':tokenize(s),'latex':False})\n"
"            seen += 1\n"
"    return out\n"
"def main():\n"
"    if len(sys.argv) < 3:\n"
"        print('Usage: extract_equations.py input.txt out.jsonl')\n"
"        return 2\n"
"    txt = open(sys.argv[1], 'r', encoding='utf-8', errors='ignore').read()\n"
"    recs = extract(txt)\n"
"    with open(sys.argv[2], 'w', encoding='utf-8') as fo:\n"
"        for r in recs: fo.write(json.dumps(r, ensure_ascii=False) + '\\n')\n"
"    print('Extracted', len(recs), 'records to', sys.argv[2])\n"
"    return 0\n"
"if __name__ == '__main__':\n"
      "    sys.exit(main())\n";

    snprintf(buf, sizeof(buf), "%s/bin/extract_equations.py", out);
    write_file(buf, extract_equations_py);

    /* bin/equation_entropy.py */
    const char *equation_entropy_py =
"#!/usr/bin/env python3\n"
"import sys, math, json, re\n"
"from collections import Counter\n"
"def shannon_entropy(tokens):\n"
"    if not tokens: return 0.0\n"
"    c = Counter(tokens)\n"
"    total = float(len(tokens))\n"
"    H = 0.0\n"
"    for v in c.values():\n"
"        p = v/total\n"
"        if p>0: H -= p * math.log2(p)\n"
"    return H\n"
"def extract_features(tokens):\n"
"    s = ' '.join(str(t).lower() for t in tokens)\n"
"    return {\n"
"        'has_gamma': 'gamma' in s or '\\\\gamma' in s,\n"
"        'has_zeta': 'zeta' in s or '\\\\zeta' in s,\n"
"        'has_manifold': 'manifold' in s or 'differential' in s,\n"
"        'has_noncomm': 'noncomm' in s or 'non-comm' in s\n"
"    }\n"
"def main():\n"
"    if len(sys.argv) < 3:\n"
"        print('Usage: equation_entropy.py in.jsonl out.jsonl')\n"
"        return 2\n"
"    objs = [json.loads(l) for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]\n"
"    out = []\n"
"    for o in objs:\n"
"        toks = o.get('tokens', [])\n"
"        H = shannon_entropy(toks)\n"
"        feats = extract_features(toks)\n"
"        uniq = len(set(toks)); tc = len(toks)\n"
"        symbolc = sum(1 for t in toks if re.match(r'^[^A-Za-z0-9\\\\u4e00-\\\\u9fff]+$|^\\\\\\\\[A-Za-z]+', t))\n"
"        math_density = symbolc / max(1, tc)\n"
"        structural = tc * uniq\n"
"        o.update({'entropy': H, 'token_count': tc, 'uniq': uniq, 'math_density': math_density, 'structural': structural})\n"
"        o.update(feats)\n"
"        out.append(o)\n"
"    Hs = [o['entropy'] for o in out]\n"
"    if Hs:\n"
"        mn = min(Hs); mx = max(Hs)\n"
"        for o in out:\n"
"            o['entropy_norm'] = (o['entropy'] - mn) / (mx - mn) if mx>mn else 0.0\n"
"    open(sys.argv[2], 'w', encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in out))\n"
"    print('Wrote', sys.argv[2], 'entries=', len(out))\n"
"    return 0\n"
"if __name__ == '__main__':\n"
      "    sys.exit(main())\n";

    snprintf(buf, sizeof(buf), "%s/bin/equation_entropy.py", out);
    write_file(buf, equation_entropy_py);

    /* bin/value_substitute.py */
    const char *value_substitute_py =
"#!/usr/bin/env python3\n"
"import sys, json, re, math\n" 
"try:\n"
"    import mpmath as mp\n"
"    MP = True\n"
"except Exception:\n"
"    MP = False\n"
"def prepare(expr, vals):\n"
"    s = expr\n"
"    s = s.replace('\\\\Gamma','gamma').replace('\\\\gamma','gamma')\n"
"    s = s.replace('\\\\zeta','zeta').replace('^','**').replace('\\\\cdot','*')\n"
"    for k,v in vals.items():\n"
"        s = re.sub(r'\\\\b'+re.escape(k)+r'\\\\b','(%r)'%v, s)\n"
"    s = re.sub(r'\\\\\\\\[A-Za-z]+','', s)\n"
"    return s\n"
"def safe_eval(s):\n"
"    ns = {'pi': math.pi, 'e': math.e}\n"
"    if MP:\n"
"        ns['gamma'] = lambda x: float(mp.gamma(x)) if x is not None else float('nan')\n"
"        ns['zeta'] = lambda x: float(mp.zeta(x)) if x is not None else float('nan')\n"
"    else:\n"
"        try:\n"
"            ns['gamma'] = lambda x: float(math.gamma(x))\n"
"        except Exception:\n"
"            ns['gamma'] = lambda x: float('nan')\n"
"        ns['zeta'] = lambda x: float('nan')\n"
"    try:\n"
"        val = eval(s, {'__builtins__': None}, ns)\n"
"        return float(val) if val is not None else None\n"
"    except Exception:\n"
"        return None\n"
"def main():\n"
"    if len(sys.argv) < 4:\n"
"        print('Usage: value_substitute.py in_entropy.jsonl values.json out.jsonl')\n"
"        return 2\n"
"    objs = [json.loads(l) for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]\n"
"    vals = json.load(open(sys.argv[2], 'r', encoding='utf-8'))\n"
"    outs = []\n"
"    for o in objs:\n"
"        raw = o.get('raw','')\n"
"        s = prepare(raw, vals)\n"
"        num = safe_eval(s)\n"
"        features = {}\n"
"        if num is None or (isinstance(num, float) and (not math.isfinite(num))):\n"
"            features = {'numeric_value': None, 'log_abs': None, 'proxy_entropy': o.get('entropy',0.0), 'evaluation_success': False}\n"
"        else:\n"
"            try:\n"
"                log_abs = math.log(abs(num)) if num!=0 else float('-inf')\n"
"            except Exception:\n"
"                log_abs = None\n"
"            amgm = None\n"
"            if isinstance(num, (int, float)) and num>0:\n"
"                am = (num + 1.0)/2.0\n"
"                gm = math.sqrt(num*1.0)\n"
"                amgm = (gm / am) if am>0 else None\n"
"            try:\n"
"                proxy = math.log2(1.0 + abs(num))\n"
"            except Exception:\n"
"                proxy = None\n"
"            features = {'numeric_value': num, 'log_abs': log_abs, 'amgm_ratio': amgm, 'proxy_entropy': proxy, 'evaluation_success': True}\n"
"        features['has_gamma'] = bool(re.search(r'gamma|\\\\\\\\Gamma', raw, re.I))\n"
"        features['has_zeta']  = bool(re.search(r'zeta|\\\\\\\\zeta', raw, re.I))\n"
"        features['has_manifold'] = bool(re.search(r'manifold|differential', raw, re.I))\n"
"        features['has_noncomm'] = bool(re.search(r'noncomm|non-comm|noncommutative', raw, re.I))\n"
"        o['sub_features'] = features\n"
"        outs.append(o)\n"
"    open(sys.argv[3], 'w', encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in outs))\n"
"    print('Wrote', sys.argv[3], 'entries=', len(outs))\n"
"    return 0\n"
"if __name__ == '__main__':\n"
      "    sys.exit(main())\n";

    snprintf(buf, sizeof(buf), "%s/bin/value_substitute.py", out);
    write_file(buf, value_substitute_py);

    /* bin/causal_infer.py */
    const char *causal_infer_py =
"#!/usr/bin/env python3\n"
"import sys, json, math\n"
"def score_and_rationale(o, target_H):\n"
"    ent = o.get('entropy', 0.0)\n"
"    sub = o.get('sub_features', {})\n"
"    proxy = sub.get('proxy_entropy')\n"
"    score = 0.0; reasons = []\n"
"    d_sym = abs(ent - target_H)\n"
"    sym_score = max(0.0, 1.0 - d_sym / (1.0 + abs(target_H)))\n"
"    score += sym_score; reasons.append(('symbolic_entropy', ent, d_sym))\n"
"    if proxy is not None:\n"
"        d_proxy = abs(proxy - target_H)\n"
"        prox_score = max(0.0, 1.0 - d_proxy / (1.0 + abs(target_H)))\n"
"        score += prox_score * 1.6; reasons.append(('proxy_entropy', proxy, d_proxy))\n"
"    if sub.get('has_gamma'):\n"
"        score += 0.25; reasons.append(('gamma_present',))\n"
"    if sub.get('has_zeta'):\n"
"        score += 0.3; reasons.append(('zeta_present',))\n"
"    if sub.get('has_manifold'):\n"
"        score += 0.18; reasons.append(('manifold_present',))\n"
"    if sub.get('has_noncomm'):\n"
"        score += 0.14; reasons.append(('noncomm_present',))\n"
"    amgm = sub.get('amgm_ratio')\n"
"    if amgm is not None:\n"
"        score += max(0.0, 0.2 * (1.0 - abs(amgm - 1.0))); reasons.append(('amgm_ratio', amgm))\n"
"    structural = o.get('structural', 0)\n"
"    if structural > 30:\n"
"        bonus = min(0.4, structural/300.0)\n"
"        score += bonus; reasons.append(('complexity_bonus', structural, bonus))\n"
"    return score, reasons\n"
"def synthesize_answer(match, target_H):\n"
"    raw = match.get('raw', '')\n"
"    ent = match.get('entropy', 0.0)\n"
"    proxy = match.get('proxy')\n"
"    reasons = match.get('reasons', [])\n"
"    lines = []\n"
"    lines.append('Candidate equation: ' + raw)\n"
"    lines.append('Symbolic entropy = %.6f' % ent)\n"
"    if proxy is not None:\n"
"        lines.append('Numeric proxy-entropy = %.6f' % proxy)\n"
"    lines.append('Match score = %.4f' % match.get('score',0.0))\n"
"    if any(r[0]=='zeta_present' for r in reasons if isinstance(r, tuple)):\n"
"        lines.append('Rationale: presence of zeta-like structure suggests series or spectral behavior influencing entropy.')\n"
"    if any(r[0]=='gamma_present' for r in reasons if isinstance(r, tuple)):\n"
"        lines.append('Rationale: gamma/special-function indicates scaling properties; numeric substitution yields characteristic magnitudes.')\n"
"    if any(r[0]=='amgm_ratio' for r in reasons if isinstance(r, tuple)):\n"
"        lines.append('Rationale: AM-GM balance close to 1 implies arithmetic/geometric balance, linked to magnitude and proxy entropy.')\n"
"    if match.get('features',{}).get('has_manifold'):\n"
"        lines.append('Rationale: manifold/differential structure signals geometric constraints; entropy may reflect geometric complexity.')\n"
"    nv = match.get('features',{}).get('numeric_value')\n"
"    if nv is not None:\n"
"        try:\n"
"            proxy_val = math.log2(1.0 + abs(nv))\n"
"        except Exception:\n"
"            proxy_val = None\n"
"        lines.append('Numeric evaluation yields: %.8g' % nv)\n"
"        if proxy_val is not None:\n"
"            lines.append('Derived proxy-entropy from numeric value: %.6f' % proxy_val)\n"
"    closeness = abs(match.get('entropy',0.0) - target_H)\n"
"    if closeness < 0.15 or (nv is not None and abs(math.log2(1.0+abs(nv)) - target_H) < 0.15):\n"
"        lines.append('Conclusion: This equation plausibly explains the question entropy; consider as a candidate answer.')\n"
"    else:\n"
"        lines.append('Conclusion: Weak to moderate match; further numeric exploration recommended.')\n"
"    return '\\n'.join(lines)\n"
"def main():\n"
"    if len(sys.argv) < 5:\n"
"        print('Usage: causal_infer.py substituted.jsonl question_entropy out_matches.json out_report.txt')\n"
"        return 2\n"
"    objs = [json.loads(l) for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]\n"
"    target_H = float(sys.argv[2])\n"
"    matches = []\n"
"    for o in objs:\n"
"        s, reasons = score_and_rationale(o, target_H)\n"
"        matches.append({'id': o.get('id'), 'score': s, 'reasons': reasons, 'raw': o.get('raw'), 'entropy': o.get('entropy'), 'proxy': o.get('sub_features', {}).get('proxy_entropy'), 'features': o.get('sub_features', {})})\n"
"    matches.sort(key=lambda x: -x['score'])\n"
"    for m in matches[:10]:\n"
"        m['answer_text'] = synthesize_answer(m, target_H)\n"
"    open(sys.argv[3], 'w', encoding='utf-8').write(json.dumps(matches, ensure_ascii=False, indent=2))\n"
"    with open(sys.argv[4], 'w', encoding='utf-8') as fo:\n"
"        fo.write('QUESTION ENTROPY: %.6f\\n\\n' % target_H)\n"
"        fo.write('TOP CANDIDATES:\\n')\n"
"        for i,m in enumerate(matches[:10],1):\n"
"            fo.write('RANK %d\\n' % i)\n"
"            fo.write('ID: %s\\n' % m['id'])\n"
"            fo.write('SCORE: %.4f\\n' % m['score'])\n"
"            fo.write(m.get('answer_text','') + '\\n\\n')\n"
"    print('Wrote', sys.argv[3], 'and', sys.argv[4])\n"
"    return 0\n"
"if __name__ == '__main__':\n"
      "    sys.exit(main())\n";

    snprintf(buf, sizeof(buf), "%s/bin/causal_infer.py", out);
    write_file(buf, causal_infer_py);

    /* bin/chat_assistant.py */
    const char *chat_assistant_py =
"#!/usr/bin/env python3\n"
"import sys, argparse, os, json, subprocess, re\n"
"def run(cmd):\n"
"    return subprocess.call(cmd)\n"
"def load_report(path):\n"
"    if not os.path.exists(path):\n"
"        print('Report not found:', path); return False\n"
"    run([sys.executable, 'extract_equations.py', path, 'equations.jsonl'])\n"
"    run([sys.executable, 'equation_entropy.py', 'equations.jsonl', 'equations_entropy.jsonl'])\n"
"    print('Loaded and processed report -> equations_entropy.jsonl')\n"
"    return True\n"
"def question_to_entropy(question):\n"
"    # Heuristic mapping from natural-language question to a numeric target entropy.\n"
"    m = re.search(r'([0-9]+(?:\\.[0-9]+)?)', question)\n"
"    if m:\n"
"        return float(m.group(1))\n"
"    q = question.lower()\n"
"    if 'shannon' in q or 'entropy' in q:\n"
"        return 1.5\n"
"    if 'gamma' in q or 'gamma function' in q:\n"
"        return 2.0\n"
"    if 'zeta' in q or 'riemann' in q:\n"
"        return 2.2\n"
"    if 'manifold' in q or 'differential' in q:\n"
"        return 1.9\n"
"    if 'noncomm' in q or 'non-comm' in q:\n"
"        return 2.1\n"
"    return 1.6\n"
"def ask_question(question, values_file=None):\n"
"    target_H = question_to_entropy(question)\n"
"    print('Interpreted target entropy =', target_H)\n"
"    vals = values_file or '../examples/sample_values.json'\n"
"    if not os.path.exists(vals): vals = 'examples/sample_values.json'\n"
"    run([sys.executable, 'value_substitute.py', 'equations_entropy.jsonl', vals, 'equations_subst.jsonl'])\n"
"    run([sys.executable, 'causal_infer.py', 'equations_subst.jsonl', str(target_H), 'matches.json', 'analysis_report.txt'])\n"
"    if os.path.exists('matches.json'):\n"
"        j = json.load(open('matches.json','r',encoding='utf-8'))\n"
"        if j:\n"
"            print('\\n--- Top candidate answer (math + text) ---')\n"
"            print(j[0].get('answer_text','(no answer)'))\n" 
"    if os.path.exists('analysis_report.txt'):\n"
"        print('\\n--- Analysis report (brief) ---')\n"
"        with open('analysis_report.txt','r',encoding='utf-8') as f:\n"
"            for i,line in enumerate(f):\n"
"                if i>80: break\n"
"                print(line.rstrip())\n"
"def interactive():\n"
"    print('Omega causal chat assistant - commands: load <report>, ask <natural language question>, exit')\n"
"    while True:\n"
"        try: line = input('> ').strip()\n"
"        except EOFError: break\n"
"        if not line: continue\n"
"        if line.lower().startswith('load '):\n"
"            load_report(line[5:].strip())\n"
"        elif line.lower().startswith('ask '):\n"
"            q = line[4:].strip(); ask_question(q)\n"
"        elif line.lower() in ('exit','quit'):\n"
"            break\n"
"        else:\n"
"            print('Unknown command')\n"
"def main():\n"
"    p = argparse.ArgumentParser()\n"
"    p.add_argument('--load', help='Load report file')\n"
"    p.add_argument('--ask', help='Ask natural language question')\n"
"    p.add_argument('--values', help='Optional values.json for substitution')\n"
"    p.add_argument('--interactive', action='store_true')\n"
"    args = p.parse_args()\n"
"    if args.load:\n"
"        load_report(args.load)\n"
"    if args.ask:\n"
"        ask_question(args.ask, args.values)\n"
"    if args.interactive:\n"
"        interactive()\n"
"    return 0\n"
"if __name__ == '__main__':\n"
      "    sys.exit(main())\n";

    snprintf(buf, sizeof(buf), "%s/bin/chat_assistant.py", out);
    write_file(buf, chat_assistant_py);

    /* etc/config */
    const char *etc_config =
      "# omega_causal_pkg configuration\n# For improved special-function evaluation install mpmath: pip install mpmath\n";
    snprintf(buf, sizeof(buf), "%s/etc/config", out);
    write_file(buf, etc_config);

    /* usr/share/omega/README.md */
    const char *readme =
      "# Omega causal chat package\n\nUse bin/chat_assistant.py to load a report and ask natural-language questions. The assistant maps questions heuristically to an entropy value and returns candidate equations with textual rationale.\n";
    snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
    write_file(buf, readme);

    /* examples/sample_values.json */
    const char *sample_values =
"{\n"
"  \"x\": 1.618,\n"
"  \"t\": 0.5,\n"
"  \"gamma\": 2.5,\n"
"  \"pi\": 3.141592653589793,\n"
"  \"e\": 2.718281828459045\n"
"}\n";
    snprintf(buf, sizeof(buf), "%s/examples/sample_values.json", out);
    write_file(buf, sample_values);

    /* examples/sample_text.txt */
    const char *sample_text =
"Sample report with equations and LaTeX\n\n"
"Shannon entropy: H(X) = -\\\\sum p(x) log p(x)\n\n"
"Gamma function: \\\\Gamma(z) = \\\\int_0^\\\\infty t^{z-1} e^{-t} dt\n\n"
"Riemann zeta: \\\\zeta(s) = \\\\sum_{n=1}^\\\\infty 1/n^s\n\n"
"Noncommutative example: [x,y] = xy - yx\n\n"
"Manifold notes: curvature, geodesic, connection\n\n"
      "E = m c^2\n";
    snprintf(buf, sizeof(buf), "%s/examples/sample_text.txt", out);
    write_file(buf, sample_text);

    /* lib/helper.py */
    const char *lib_helper_py =
"# placeholder helper\n"
"def info():\n"
      "    return 'omega causal lib v1'\n";
    snprintf(buf, sizeof(buf), "%s/lib/helper.py", out);
    write_file(buf, lib_helper_py);

    /* include/sample.h */
    const char *include_h =
      "/* sample header */\n"
"#ifndef OMEGA_SAMPLE_H\n"
"#define OMEGA_SAMPLE_H\n"
"static const char *omega_pkg_version = \"1.0\";\n"
      "#endif\n";
    snprintf(buf, sizeof(buf), "%s/include/sample.h", out);
    write_file(buf, include_h);

    /* Top-level Makefile */
    const char *makefile =
"PKGDIR ?= omega_causal_pkg\n"
"PY = $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)\n"
"BIN = $(PKGDIR)/bin\n"
"EXAMPLES = $(PKGDIR)/examples\n"
".PHONY: all build run test clean help\n"
"all: build\n"
"build:\n"
"\t@echo \"Package skeleton created under $(PKGDIR)\"\n"
"\t@ls -1 $(PKGDIR) || true\n"
"run: build\n"
"\t@echo \"Run chat assistant interactively (example):\"\n"
"\t@cd $(BIN) && $(PY) chat_assistant.py --interactive || true\n"
"test: build\n"
"\t@echo \"Basic checks:\"\n"
"\t@if [ -d \"$(PKGDIR)\" ]; then echo \"OK: $(PKGDIR) exists\"; else echo \"MISSING: $(PKGDIR)\"; exit 1; fi\n"
"\t@if [ -f \"$(BIN)/chat_assistant.py\" ]; then echo \"OK: chat_assistant.py\"; else echo \"MISSING: chat_assistant.py\"; exit 1; fi\n"
"\t@echo \"All basic checks passed.\"\n"
"clean:\n"
"\t@echo \"remove $(PKGDIR)\"\n"
"\t@rm -rf $(PKGDIR) || true\n"
"help:\n"
      "\t@echo \"Targets: all build run test clean help\"\n";
    snprintf(buf, sizeof(buf), "%s/Makefile", out);
    write_file(buf, makefile);

#ifndef _WIN32
    {
		      char cmd[4096];
		      snprintf(cmd, sizeof(cmd),
			"chmod +x \"%s/bin/extract_equations.py\" \"%s/bin/equation_entropy.py\" \"%s/bin/value_substitute.py\" \"%s/bin/causal_infer.py\" \"%s/bin/chat_assistant.py\" 2>/dev/null || true",
			out, out, out, out, out);
		      system(cmd);
		    }
#endif

    printf("Generation finished. Created these paths:\n");
    printf("  %s/bin/\n  %s/lib/\n  %s/include/\n  %s/etc/\n  %s/usr/share/omega/\n  %s/examples/\n", out, out, out, out, out, out);
    printf("Run 'make -C %s test' to perform basic checks.\n", out);
    return 0;
		    }

/*
以上です。問題があれば、出力された具体的なエラーメッセージ（gcc の出力）や、どのスクリプトで期待どおりの動作が得られないかを教えてください。必要に応じて個別のファイル（例えば chat_assistant.py の改善や SymPy を用いた式評価、安全化）を追加して修正します。
*/
