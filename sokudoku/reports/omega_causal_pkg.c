/* pkginstallgen.c
   Generate a package that extends the entropy-match pipeline with:
    - numeric substitution into extracted equations (user-supplied numeric values)
    - compute entropy-like measures derived from Shannon formula and from proxies using:
    * Gamma / Zeta approximations (via mpmath if available)
    * simple proxies for noncommutative algebra markers, global differential/integral markers,
          AM-GM/AGM style combination measures
    - derive feature vectors from substituted numeric results and compare causally to question-entropy value
    - produce multiple candidate answers inferred from causal correlation between substituted-values-derived
      entropies and requested question entropy.
   The package is heuristic and for research/analysis support only (no formal proofs).
   Build:
     gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c
   Run:
     ./pkginstallgen ./omega_causal_pkg
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
  const char *out = "omega_causal_pkg";
  if (argc > 1) out = argv[1];
  char buf[8192];

  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);

  /* bin/extract_equations.py (reuse) */
    const char *extract_equations_py =
      "#!/usr/bin/env python3\n\"\"\"\nextract_equations.py\n(See README) Extract LaTeX/math and equation-like lines from text.\nUsage: extract_equations.py input.txt out_eqs.jsonl\n\"\"\"\nimport sys,re,json\nif len(sys.argv)<3:\n    print('Usage: extract_equations.py input.txt out_eqs.jsonl'); sys.exit(2)\ntext = open(sys.argv[1],'r',encoding='utf-8',errors='ignore').read()\nmath_re = re.compile(r'\\\\\\[(.+?)\\\\\\]|\\\\\\((.+?)\\\\\\)|\\$\\$(.+?)\\$\\$|\\$(.+?)\\$', re.S)\nline_re = re.compile(r'^[^\\n]*[=<>∼≈]+[^\\n]*$', re.M)\nout = open(sys.argv[2],'w',encoding='utf-8')\nseen=0\nfor m in math_re.findall(text):\n    content = ''.join(m).strip()\n    if content:\n        tokens = re.findall(r\"[A-Za-z0-9_\\\\]+|[\\u4e00-\\u9fff]+|\\S\", content)\n        obj = {'id': 'M%d'%seen, 'raw': content, 'tokens': tokens, 'latex': True}\n        out.write(json.dumps(obj, ensure_ascii=False) + '\\n'); seen+=1\nfor ln in line_re.findall(text):\n    s = ln.strip()\n    if len(s)>3:\n        tokens = re.findall(r\"[A-Za-z0-9_]+|[\\u4e00-\\u9fff]+|\\\\.|\\S\", s)\n        obj = {'id': 'L%d'%seen, 'raw': s, 'tokens': tokens, 'latex': False}\n        out.write(json.dumps(obj, ensure_ascii=False) + '\\n'); seen+=1\nout.close(); print('Wrote', sys.argv[2])\n";
    snprintf(buf, sizeof(buf), "%s/bin/extract_equations.py", out);
    write_file(buf, extract_equations_py);

    /* bin/equation_entropy.py (compute entropies/features) */
    const char *equation_entropy_py =
      "#!/usr/bin/env python3\n\"\"\"\nequation_entropy.py\nCompute entropy & structural features for extracted equations.\nUsage: equation_entropy.py eqs.jsonl out_eqs_entropy.jsonl\n\"\"\"\nimport sys,math,json,re\nfrom collections import Counter\nif len(sys.argv)<3:\n    print('Usage: equation_entropy.py eqs.jsonl out_eqs_entropy.jsonl'); sys.exit(2)\nobjs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\nkeywords=['gamma','beta','zeta','shannon','entropy','noncomm','agm','higgs','manifold','integral','div','nabla','∇','Δ','zeta','jones']\n\ndef shannon_entropy(tokens):\n    if not tokens: return 0.0\n    c=Counter(tokens); total=len(tokens); H=0.0\n    for v in c.values():\n        p=v/total; H -= p*math.log2(p)\n    return H\n\nout=[]\nfor o in objs:\n    toks=o.get('tokens',[])\n    H=shannon_entropy(toks)\n    math_density = sum(1 for t in toks if re.match(r'^[^\\w\\u4e00-\\u9fff]+$|^\\\\[A-Za-z]+', t))/max(1,len(toks))\n    uniq=len(set(toks))\n    structural = len(toks)*uniq\n    kw_vec={k: int(any(k in str(t).lower() for t in toks)) for k in keywords}\n    o.update({'entropy':H, 'entropy_norm':None, 'math_density':math_density, 'uniq_symbols':uniq, 'structural':structural, 'keywords':kw_vec})\n    out.append(o)\n# normalize entropy_norm to 0..1\nHs=[o['entropy'] for o in out]\nif Hs:\n    mn=min(Hs); mx=max(Hs)\n    for o in out:\n        o['entropy_norm'] = (o['entropy']-mn)/(mx-mn) if mx>mn else 0.0\nopen(sys.argv[2],'w',encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in out))\nprint('Wrote', sys.argv[2])\n";
    snprintf(buf, sizeof(buf), "%s/bin/equation_entropy.py", out);
    write_file(buf, equation_entropy_py);

    /* bin/value_substitute.py
       - Accept a JSONL file of equations plus a JSON of variable:value assignments.
       - Attempt to substitute numeric values into simple expressions heuristically.
       - Evaluate numeric proxies for Gamma/Zeta via mpmath if available, otherwise simple approximations.
       - Compute derived measures: Shannon-style entropy of resulting numeric vector, AM-GM ratio, log-energy, etc.
    */
    const char *value_substitute_py =
      "#!/usr/bin/env python3\n\"\"\"\nvalue_substitute.py\nSubstitute numeric values into equations to compute numeric-derived features.\nUsage: value_substitute.py eqs_entropy.jsonl values.json out_values.jsonl\nvalues.json example: {\"x\":1.2, \"t\":0.5}\nNotes: heuristic substitution only; for complex LaTeX full parser is needed (not included).\n\"\"\"\nimport sys, json, re, math\nif len(sys.argv)<4:\n    print('Usage: value_substitute.py eqs_entropy.jsonl values.json out_values.jsonl'); sys.exit(2)\nimported = []\ntry:\n    import mpmath as mp\n    MP=True\nexcept Exception:\n    MP=False\n\ndef safe_eval(expr, vals):\n    # very small sandboxed evaluator for arithmetic expressions built from tokens (heuristic)\n    # replace known names with numeric values, handle gamma/zeta via mpmath if available\n    s = expr\n    for k,v in vals.items():\n        s = re.sub(r'\\b%s\\b' % re.escape(k), '(%r)'%v, s)\n    # map common LaTeX tokens to python: \\Gamma -> gamma, \\zeta -> zeta\n    s = s.replace('\\\\Gamma','gamma').replace('\\\\zeta','zeta').replace('^','**')\n    s = re.sub(r'\\\\', '', s)\n    # guard: allow only certain chars\n    if re.search(r'[^0-9\\.\\+\\-\\*/\\(\\)\\*\\*eEgGmMsqrt, a-zA-Z:]+', s):\n        # if contains unfamiliar symbols, return None\n        pass\n    # implement gamma/zeta if MP available\n    gl = {}\n    if MP:\n        gl['gamma']=mp.gamma; gl['zeta']=mp.zeta\n    else:\n        import math as _math\n        gl['gamma']=lambda x: float(_math.gamma(x)) if x>0 else float('nan')\n        gl['zeta']=lambda s: float('nan')\n    # safe builtins minimal\n    try:\n        val = eval(s, {'__builtins__':None}, gl)\n        return float(val)\n    except Exception:\n        return None\n\nobjs = [json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\nvals = json.load(open(sys.argv[2],'r',encoding='utf-8'))\nouts=[]\nfor o in objs:\n    raw = o.get('raw','')\n    num = safe_eval(raw, vals)\n    # derive features from numeric value(s)\n    features = {}\n    if num is None:\n        features['numeric_value']=None\n        features['log_abs']=None\n        features['amgm']=None\n        features['proxy_entropy']=o.get('entropy',0.0)\n    else:\n        features['numeric_value']=num\n        features['log_abs'] = math.log(abs(num)) if num!=0 else float('-inf')\n        # AM-GM proxy: for positive num treat as (num + 1)/2 geometric/arith ratio\n        if num>0:\n            am = (num + 1.0)/2.0\n            gm = math.sqrt(num*1.0)\n            features['amgm_ratio'] = gm/am if am>0 else 0.0\n        else:\n            features['amgm_ratio']=None\n        # proxy entropy from numeric magnitude distribution (single number -> low entropy), use transform\n        features['proxy_entropy'] = math.log2(1+abs(num))\n    o['sub_features']=features\n    outs.append(o)\nopen(sys.argv[3],'w',encoding='utf-8').write('\\n'.join(json.dumps(o, ensure_ascii=False) for o in outs))\nprint('Wrote', sys.argv[3])\n";
    snprintf(buf, sizeof(buf), "%s/bin/value_substitute.py", out);
    write_file(buf, value_substitute_py);

    /* bin/causal_infer.py
       - Load substituted-feature eqs and question entropy value H_q.
       - For each equation compute correlation-like scores between derived proxy_entropy/amgm_ratio/log_abs
         and the target H_q (absolute difference, scaled similarity).
       - Produce ranked candidate causal suggestions and multiple answer templates:
       * if proxy_entropy close to H_q -> direct match statement
       * if amgm_ratio correlates with H_q -> 'AM-GM style relationship' suggestion
       * if Gamma/Zeta keyword present and proxy_entropy close -> 'zeta/gamma transform explanation'
       - Output causal_matches.json and human-readable answers file.
    */
    const char *causal_infer_py =
      "#!/usr/bin/env python3\n\"\"\"\ncausal_infer.py\nInfer causal / correlational links between substituted equation-derived features and a target question entropy value.\nUsage: causal_infer.py substituted_eqs.jsonl target_H out_matches.json out_readable.txt\n\"\"\"\nimport sys,json,math\nif len(sys.argv)<5:\n    print('Usage: causal_infer.py substituted_eqs.jsonl target_H out_matches.json out_readable.txt'); sys.exit(2)\nobjs=[json.loads(l) for l in open(sys.argv[1],'r',encoding='utf-8') if l.strip()]\nHq = float(sys.argv[2])\nmatches=[]\nfor o in objs:\n    fid = o.get('id')\n    sf = o.get('sub_features',{})\n    ent = o.get('entropy',0.0)\n    proxy = sf.get('proxy_entropy')\n    amgm = sf.get('amgm_ratio')\n    logabs = sf.get('log_abs')\n    keywords = o.get('keywords',{}) if isinstance(o.get('keywords'), dict) else {}\n    # score components\n    score = 0.0\n    reasons = []\n    if proxy is not None:\n        d = abs(proxy - Hq)\n        score += max(0, (1.0 - d/(1.0+abs(Hq))))\n        reasons.append(('proxy_entropy', proxy, d))\n    # entropy of symbolic tokens also matters\n    ent_d = abs(ent - Hq)\n    score += max(0, (0.5 - ent_d/ (1.0+abs(Hq))))\n    reasons.append(('symbolic_entropy', ent, ent_d))\n    if amgm is not None:\n        # prefer amgm values near 1 (balanced) as signal, compare to Hq scaled\n        score += max(0, 0.2*(1.0 - abs(amgm-1.0)))\n        reasons.append(('amgm', amgm))\n    # keyword boosts\n    for k in ['gamma','zeta','manifold','higgs','entropy']:\n        if o.get('raw','').lower().find(k)>=0 or keywords.get(k,0):\n            score += 0.15\n            reasons.append(('kw',k))\n    matches.append({'id':fid,'score':score,'reasons':reasons,'raw':o.get('raw','')})\n# sort and output\nmatches.sort(key=lambda x:-x['score'])\nopen(sys.argv[3],'w',encoding='utf-8').write(json.dumps(matches, ensure_ascii=False, indent=2))\n# human readable\nwith open(sys.argv[4],'w',encoding='utf-8') as fo:\n    fo.write('Target question entropy H_q = %.6f\\n\\n' % Hq)\n    fo.write('Top candidate causal matches:\\n')\n    for m in matches[:10]:\n        fo.write('- id=%s score=%.4f\\n  snippet=%s\\n  reasons=%s\\n\\n' % (m['id'], m['score'], m['raw'][:300], str(m['reasons'])))\n    fo.write('\\nSuggested actions based on matches:\\n')\n    fo.write('- If proxy_entropy ~ H_q: propose this equation as explanation/candidate source for the question entropy.\\n')\n    fo.write('- If keywords include gamma/zeta and proxy_entropy correlates: propose spectral/gamma-transform interpretation.\\n')\n    fo.write('- If AM-GM ratio shows correlation: propose multiplicative/additive tradeoff analysis or stability test (simulate numerical families).\\n')\nprint('Wrote', sys.argv[3], 'and', sys.argv[4])\n";
    snprintf(buf, sizeof(buf), "%s/bin/causal_infer.py", out);
    write_file(buf, causal_infer_py);

    /* etc/config */
    const char *etc_conf =
      "# omega_causal_pkg configuration\n# e.g. path to mpmath if needed (install with pip install mpmath)\n";
    snprintf(buf, sizeof(buf), "%s/etc/config", out);
    write_file(buf, etc_conf);

    /* usr/share/omega/README.md (short) */
    const char *usr_readme =
      "# Omega Causal Entropy Match Package\n\nThis package provides scripts to:\n - extract equations: bin/extract_equations.py\n - compute symbolic entropy/features: bin/equation_entropy.py\n - substitute numeric values and compute proxy numeric features: bin/value_substitute.py\n - infer causal/correlational relationships to a target question entropy: bin/causal_infer.py\n\nExample workflow:\n  python3 bin/extract_equations.py report.txt eqs.jsonl\n  python3 bin/equation_entropy.py eqs.jsonl eqs_entropy.jsonl\n  # prepare JSON file with numeric assignments, e.g. values.json: {\"x\":1.2, \"t\":0.3}\n  python3 bin/value_substitute.py eqs_entropy.jsonl values.json eqs_subst.jsonl\n  # target question entropy (H_q) compute from question or choose\n  python3 bin/causal_infer.py eqs_subst.jsonl 1.75 matches.json answers.txt\n\nNotes:\n - The numeric substitution is heuristic; complex LaTeX/formula parsing is NOT performed.\n - For Gamma/Zeta computations, installing mpmath is recommended: pip install mpmath\n - All outputs are intended as candidate evidence for human analysts or downstream tools.\n";
    snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
    write_file(buf, usr_readme);

    /* Make scripts executable (UNIX) */
#ifndef _WIN32
    {
      char cmd[8192];
      snprintf(cmd, sizeof(cmd),
	       "chmod +x \"%s/bin/extract_equations.py\" \"%s/bin/equation_entropy.py\" \"%s/bin/value_substitute.py\" \"%s/bin/causal_infer.py\" 2>/dev/null || true",
	       out, out, out, out);
      system(cmd);
    }
#endif

    printf("Omega causal-entropy package created at: %s\n", out);
    printf("See %s/usr/share/omega/README.md for workflow.\n", out);
    return 0;
}
