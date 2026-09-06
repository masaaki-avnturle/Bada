```c
/* pkginstallgen.c
 * Generate a complete package for entropy-based equation matching and causal inference.
 *
 * Build:
 *   gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c
 *
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
  size_t len;
  if (!path) return;
  snprintf(tmp, sizeof(tmp), "%s", path);
  len = strlen(tmp);
  if (len == 0) return;
  if (tmp[len-1] == '/' || tmp[len-1] == '\\') tmp[len-1] = '\0';
  for (p = tmp + 1; *p; ++p) {
    if (*p == '/' || *p == '\\') {
      *p = '\0';
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
  const char *out = "omega_causal_pkg";
  if (argc > 1) out = argv[1];
  char buf[8192];

  printf("Creating Omega Causal Entropy Package at: %s\n", out);

  /* create directories */
  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/examples", out); mkdir_p(buf);

  /* bin/extract_equations.py */
    const char *extract_equations_py =
"#!/usr/bin/env python3\n"
"import sys, re, json\n"
"if len(sys.argv) < 3:\n"
"    print('Usage: extract_equations.py input.txt out_eqs.jsonl')\n"
"    sys.exit(2)\n"
"text = open(sys.argv[1], 'r', encoding='utf-8', errors='ignore').read()\n"
"math_re = re.compile(r'\\\\\\\\\\[(.+?)\\\\\\\\\\]|\\\\\\\\\\((.+?)\\\\\\\\\\)|\\$\\$(.+?)\\$\\$|\\$(.+?)\\$', re.S)\n"
"line_re = re.compile(r'^[^\\n]*[=<>≈∼]+[^\\n]*$', re.M)\n"
"out = open(sys.argv[2], 'w', encoding='utf-8')\n"
"seen = 0\n"
"for m in math_re.findall(text):\n"
"    content = ''.join(m).strip()\n"
"    if content and len(content) > 2:\n"
"        tokens = re.findall(r'[A-Za-z0-9_\\\\\\\\]+|[\\u4e00-\\u9fff]+|\\\\S', content)\n"
"        obj = {'id': 'M%d' % seen, 'raw': content, 'tokens': tokens, 'latex': True}\n"
"        out.write(json.dumps(obj, ensure_ascii=False) + '\\n')\n"
"        seen += 1\n"
"for ln in line_re.findall(text):\n"
"    s = ln.strip()\n"
"    if len(s) > 5:\n"
"        tokens = re.findall(r'[A-Za-z0-9_]+|[\\u4e00-\\u9fff]+|\\\\S', s)\n"
"        obj = {'id': 'L%d' % seen, 'raw': s, 'tokens': tokens, 'latex': False}\n"
"        out.write(json.dumps(obj, ensure_ascii=False) + '\\n')\n"
"        seen += 1\n"
"out.close()\n"
      "print('Extracted %d equations to %s' % (seen, sys.argv[2]))\n";

    snprintf(buf, sizeof(buf), "%s/bin/extract_equations.py", out);
    write_file(buf, extract_equations_py);

    /* bin/equation_entropy.py */
    const char *equation_entropy_py =
"#!/usr/bin/env python3\n"
"import sys, math, json, re\n"
"from collections import Counter\n"
"if len(sys.argv) < 3:\n"
"    print('Usage: equation_entropy.py eqs.jsonl out_eqs_entropy.jsonl')\n"
"    sys.exit(2)\n"
"objs = [json.loads(l) for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]\n"
"keywords = ['gamma', 'beta', 'zeta', 'shannon', 'entropy', 'noncomm', 'agm', 'higgs', 'manifold', 'integral']\n"
"def shannon_entropy(tokens):\n"
"    if not tokens: return 0.0\n"
"    c = Counter(tokens)\n"
"    total = len(tokens)\n"
"    H = 0.0\n"
"    for v in c.values():\n"
"        p = v / total\n"
"        H -= p * math.log2(p)\n"
"    return H\n"
"out = []\n"
"for o in objs:\n"
"    toks = o.get('tokens', [])\n"
"    H = shannon_entropy(toks)\n"
"    math_density = sum(1 for t in toks if re.match(r'^[^\\\\w\\\\u4e00-\\\\u9fff]+$|^\\\\\\\\[A-Za-z]+', t)) / max(1, len(toks))\n"
"    uniq = len(set(toks))\n"
"    structural = len(toks) * uniq\n"
"    kw_vec = {k: int(any(k.lower() in str(t).lower() for t in toks)) for k in keywords}\n"
"    o.update({'entropy': H, 'math_density': math_density, 'uniq_symbols': uniq, 'structural': structural, 'keywords': kw_vec})\n"
"    out.append(o)\n"
"Hs = [o['entropy'] for o in out]\n"
"if Hs:\n"
"    mn = min(Hs); mx = max(Hs)\n"
"    for o in out:\n"
"        o['entropy_norm'] = (o['entropy'] - mn) / (mx - mn) if mx > mn else 0.0\n"
"open(sys.argv[2], 'w', encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in out))\n"
      "print('Wrote', sys.argv[2])\n";

    snprintf(buf, sizeof(buf), "%s/bin/equation_entropy.py", out);
    write_file(buf, equation_entropy_py);

    /* bin/value_substitute.py */
    const char *value_substitute_py =
"#!/usr/bin/env python3\n"
"import sys, json, re, math\n"
"if len(sys.argv) < 4:\n"
"    print('Usage: value_substitute.py eqs_entropy.jsonl values.json out_values.jsonl')\n"
"    sys.exit(2)\n"
"try:\n"
"    import mpmath as mp\n"
"    MP = True\n"
"except ImportError:\n"
"    MP = False\n"
"def safe_eval(expr, vals):\n"
"    s = expr\n"
"    for k, v in vals.items():\n"
"        s = re.sub(r'\\\\b' + re.escape(k) + r'\\\\b', '(%r)' % v, s)\n"
"    s = s.replace('\\\\Gamma', 'gamma').replace('\\\\gamma', 'gamma')\n"
"    s = s.replace('\\\\zeta', 'zeta').replace('^', '**')\n"
"    s = re.sub(r'\\\\\\\\[a-zA-Z]+', '', s)\n"
      "    if re.search(r'[^0-9\\.\\+\\-\\*/\\(\\)\\*\\*eEgG, a-zA-Z:_]', s):\n"
"        return None\n"
"    gl = {'pi': math.pi, 'e': math.e}\n"
"    if MP:\n"
"        gl['gamma'] = lambda x: float(mp.gamma(x)) if x > 0 else float('nan')\n"
"        gl['zeta'] = lambda x: float(mp.zeta(x)) if x != 1 else float('nan')\n"
"    else:\n"
"        gl['gamma'] = lambda x: float(math.gamma(x)) if x > 0 else float('nan')\n"
"        gl['zeta'] = lambda x: float('nan')\n"
"    try:\n"
"        val = eval(s, {'__builtins__': {}}, gl)\n"
"        return float(val) if val is not None else None\n"
"    except Exception:\n"
"        return None\n"
"objs = [json.loads(l) for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]\n"
"vals = json.load(open(sys.argv[2], 'r', encoding='utf-8'))\n"
"outs = []\n"
"success = 0\n"
"for o in objs:\n"
"    raw = o.get('raw', '')\n"
"    num = safe_eval(raw, vals)\n"
"    features = {}\n"
"    if num is None or (isinstance(num, float) and (not math.isfinite(num))):\n"
"        features['numeric_value'] = None\n"
"        features['log_abs'] = None\n"
"        features['amgm_ratio'] = None\n"
"        features['proxy_entropy'] = o.get('entropy', 0.0)\n"
"        features['evaluation_success'] = False\n"
"    else:\n"
"        success += 1\n"
"        features['numeric_value'] = num\n"
"        features['log_abs'] = math.log(abs(num)) if num != 0 else float('-inf')\n"
"        if num > 0:\n"
"            am = (num + 1.0) / 2.0\n"
"            gm = math.sqrt(num * 1.0)\n"
"            features['amgm_ratio'] = gm / am if am > 0 else 0.0\n"
"        else:\n"
"            features['amgm_ratio'] = None\n"
"        features['proxy_entropy'] = math.log2(1 + abs(num))\n"
"        features['evaluation_success'] = True\n"
"    o['sub_features'] = features\n"
"    outs.append(o)\n"
"open(sys.argv[3], 'w', encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in outs))\n"
      "print('Evaluated %d/%d equations, wrote %s' % (success, len(outs), sys.argv[3]))\n";

    snprintf(buf, sizeof(buf), "%s/bin/value_substitute.py", out);
    write_file(buf, value_substitute_py);

    /* bin/causal_infer.py */
    const char *causal_infer_py =
"#!/usr/bin/env python3\n"
"import sys, json, math\n"
"if len(sys.argv) < 5:\n"
"    print('Usage: causal_infer.py substituted_eqs.jsonl target_H out_matches.json out_readable.txt')\n"
"    sys.exit(2)\n"
"objs = [json.loads(l) for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]\n"
"Hq = float(sys.argv[2])\n"
"matches = []\n"
"for o in objs:\n"
"    fid = o.get('id')\n"
"    sf = o.get('sub_features', {})\n"
"    ent = o.get('entropy', 0.0)\n"
"    proxy = sf.get('proxy_entropy')\n"
"    amgm = sf.get('amgm_ratio')\n"
"    score = 0.0\n"
"    reasons = []\n"
"    if proxy is not None and isinstance(proxy, (int, float)) and math.isfinite(proxy):\n"
"        d = abs(proxy - Hq)\n"
"        score += max(0, (1.0 - d / (1.0 + abs(Hq))))\n"
"        reasons.append(('proxy_entropy', proxy, d))\n"
"    ent_d = abs(ent - Hq)\n"
"    score += max(0, (0.5 - ent_d / (1.0 + abs(Hq))))\n"
"    reasons.append(('symbolic_entropy', ent, ent_d))\n"
"    if amgm is not None and isinstance(amgm, (int, float)) and math.isfinite(amgm):\n"
"        score += max(0, 0.2 * (1.0 - abs(amgm - 1.0)))\n"
"        reasons.append(('amgm', amgm))\n"
"    raw = o.get('raw', '').lower()\n"
"    for k in ['gamma', 'zeta', 'manifold', 'higgs', 'entropy']:\n"
"        if k in raw or o.get('keywords', {}).get(k, 0):\n"
"            score += 0.15\n"
"            reasons.append(('kw', k))\n"
"    matches.append({'id': fid, 'score': score, 'reasons': reasons, 'raw': o.get('raw', '')})\n"
"matches.sort(key=lambda x: -x['score'])\n"
"open(sys.argv[3], 'w', encoding='utf-8').write(json.dumps(matches, ensure_ascii=False, indent=2))\n"
"with open(sys.argv[4], 'w', encoding='utf-8') as fo:\n"
"    fo.write('Target H_q = %.6f\\n\\n' % Hq)\n"
"    for m in matches[:10]:\n"
"        fo.write('- id=%s score=%.4f\\n  snippet=%s\\n  reasons=%s\\n\\n' % (m['id'], m['score'], m['raw'][:300], str(m['reasons'])))\n"
      "print('Wrote', sys.argv[3], 'and', sys.argv[4])\n";

    snprintf(buf, sizeof(buf), "%s/bin/causal_infer.py", out);
    write_file(buf, causal_infer_py);

    /* bin/run_pipeline.py */
    const char *run_pipeline_py =
"#!/usr/bin/env python3\n"
"import sys, subprocess\n"
"if len(sys.argv) < 4:\n"
"    print('Usage: run_pipeline.py input.txt values.json target_entropy')\n"
"    sys.exit(2)\n"
"input_file = sys.argv[1]\n"
"values_file = sys.argv[2]\n"
"target_h = sys.argv[3]\n"
"subprocess.run([sys.executable, 'extract_equations.py', input_file, 'equations.jsonl'])\n"
"subprocess.run([sys.executable, 'equation_entropy.py', 'equations.jsonl', 'equations_entropy.jsonl'])\n"
"subprocess.run([sys.executable, 'value_substitute.py', 'equations_entropy.jsonl', values_file, 'equations_substituted.jsonl'])\n"
"subprocess.run([sys.executable, 'causal_infer.py', 'equations_substituted.jsonl', target_h, 'causal_matches.json', 'analysis_report.txt'])\n"
      "print('Pipeline finished. See causal_matches.json and analysis_report.txt')\n";

    snprintf(buf, sizeof(buf), "%s/bin/run_pipeline.py", out);
    write_file(buf, run_pipeline_py);

    /* etc/config */
    const char *etc_conf =
"# omega_causal_pkg configuration\n"
      "# For better special-function support, install mpmath: pip install mpmath\n";
    snprintf(buf, sizeof(buf), "%s/etc/config", out);
    write_file(buf, etc_conf);

    /* usr/share/omega/README.md */
    const char *usr_readme =
"# Omega Causal Entropy Match Package\n\n"
"Usage examples (from package/bin):\n"
"  python3 extract_equations.py report.txt equations.jsonl\n"
"  python3 equation_entropy.py equations.jsonl equations_entropy.jsonl\n"
"  python3 value_substitute.py equations_entropy.jsonl examples/sample_values.json equations_substituted.jsonl\n"
      "  python3 causal_infer.py equations_substituted.jsonl 1.75 causal_matches.json analysis_report.txt\n";
    snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
    write_file(buf, usr_readme);

    /* examples/sample_values.json */
    const char *sample_values =
"{\n"
"  \"x\": 1.618,\n"
"  \"t\": 0.5,\n"
"  \"gamma\": 2.678,\n"
"  \"pi\": 3.14159,\n"
"  \"e\": 2.71828,\n"
"  \"alpha\": 0.007297,\n"
"  \"beta\": 1.0,\n"
"  \"sigma\": 1.414\n"
      "}\n";
    snprintf(buf, sizeof(buf), "%s/examples/sample_values.json", out);
    write_file(buf, sample_values);

    /* examples/sample_text.txt */
    const char *sample_text =
"Sample Mathematical Report\n\n"
"Shannon entropy: H(X) = -sum p(x) log p(x)\n\n"
"Gamma function: Gamma(z) = integral t^(z-1) exp(-t) dt\n\n"
"Riemann zeta: zeta(s) = sum 1/n^s\n\n"
"Einstein eq: G_{mu nu} + Lambda g_{mu nu} = 8 pi T_{mu nu}\n\n"
"Simple equations:\n"
"F = m a\n"
"v = u + a t\n"
"s = u t + (1/2) a t^2\n\n"
"Some LaTeX:\n"
"$$ E = m c^2 $$\n"
      "$$ \\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi} $$\n";
    snprintf(buf, sizeof(buf), "%s/examples/sample_text.txt", out);
    write_file(buf, sample_text);

#ifndef _WIN32
    {
      char cmd[8192];
      snprintf(cmd, sizeof(cmd),
	       "chmod +x \"%s/bin/extract_equations.py\" \"%s/bin/equation_entropy.py\" \"%s/bin/value_substitute.py\" \"%s/bin/causal_infer.py\" \"%s/bin/run_pipeline.py\" 2>/dev/null || true",
	       out, out, out, out, out);
      system(cmd);
    }
#endif

    printf("Package files written. Basic layout:\n");
    printf("  %s/bin/*.py\n  %s/etc/config\n  %s/usr/share/omega/README.md\n  %s/examples/\n", out, out, out, out);
    printf("Done.\n");
    return 0;
}
```
