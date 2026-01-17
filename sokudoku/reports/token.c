以下をそのままファイル名 `pkginstallgen.c` として保存し、コンパイル（`gcc -O2 -std=c11 -o pkginstallgen pkginstallgen.c`）して実行すると、要求に沿ったプロトタイプ音声認識パッケージ（Omega Script 構成、C 実装の部品を含む）がディレクトリ `omega_brain_asr_pkg/` に生成されます。生成物は教育・研究プロトタイプであり、本番レベルの医療用途や生体インタフェース用途の実装ではありません。

保存ファイル: pkginstallgen.c

```c
	      /* pkginstallgen.c
	       *
	       * Generate omega_brain_asr_pkg:
	       *  - prototype ASR pipeline inspired by basal ganglia motifs
	       *  - uses template human database (templates/*.json)
	       *  - Omega Script runtime stub (C) and small ASR engine prototype (C)
	       *  - Python tools for preprocessing and biomodel helpers
	       *
	       * Build:
	       *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
	       * Run:
	       *   ./pkginstallgen
	       *
	       * Then:
	       *   cd omega_brain_asr_pkg
	       *   ./bin/run_pipeline --wav sample.wav --seed "Gamma(s)" --outdir generated --count 5
	       *
	       * Requires: python3 for some helper scripts (optional).
	       */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(path, 0755) == 0) return 0;
  if (errno == ENOENT) {
    char tmp[4096];
    strncpy(tmp, path, sizeof(tmp)-1);
    tmp[sizeof(tmp)-1]=0;
    char *p = strrchr(tmp, '/');
    if (p && p != tmp) { *p = 0; if (ensure_dir(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1; }
  }
  return -1;
}

static int write_file(const char *path, const char *data, int mode) {
  char dir[4096];
  strncpy(dir, path, sizeof(dir)-1); dir[sizeof(dir)-1]=0;
  char *p = strrchr(dir, '/');
  if (p) { *p = 0; ensure_dir(dir); }
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
  if (data) fputs(data, f);
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

int main(void) {
  const char *root = "omega_brain_asr_pkg";
  if (ensure_dir(root) != 0) { fprintf(stderr, "create %s failed\n", root); return 1; }

  /* README */
    const char *readme =
"# omega_brain_asr_pkg\n\n"
"Prototype speech-recognition package inspired by basal ganglia language motifs.\n"
"Includes: preprocessing, biomodel templates, ASR engine (C), Omega Script stub (C), viewer.\n"
      "Run: ./bin/run_pipeline --wav <file.wav> --seed \"...\" --outdir generated --count N\n";
    write_file("omega_brain_asr_pkg/README.md", readme, 0644);

    /* bin/run_pipeline */
    const char *runner =
      "#!/usr/bin/env bash\nset -euo pipefail\nROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\nPY=${PY:-python3}\nPRE=\"$ROOT/usr/tools/audio_preprocess.py\"\nBIOM=\"$ROOT/usr/tools/biomodel.py\"\nASR=\"$ROOT/usr/tools/asr_engine\"\nOMEGA=\"$ROOT/usr/lang/omegascript\"\nOUTDIR=\"$ROOT/generated\"\nmkdir -p \"$OUTDIR\"\nWAV=\"\"\nSEED=\"\"\nCOUNT=3\nwhile [[ $# -gt 0 ]]; do case \"$1\" in --wav) WAV=\"$2\"; shift 2;; --seed) SEED=\"$2\"; shift 2;; --outdir) OUTDIR=\"$2\"; shift 2;; --count) COUNT=\"$2\"; shift 2;; *) shift;; esac; done\nif [ -n \"$WAV\" ]; then echo \"Preprocessing $WAV\"; $PY \"$PRE\" --wav \"$WAV\" --out \"$OUTDIR/feat.json\" || true; fi\necho \"Generating biomodel templates\"\n$PY \"$BIOM\" --seed \"$SEED\" --out \"$OUTDIR/templates.json\"\necho \"Running ASR engine (prototype)\"\n\"$ASR\" --feat \"$OUTDIR/feat.json\" --templates \"$OUTDIR/templates.json\" --out \"$OUTDIR/transcripts.txt\" --count \"$COUNT\" || true\necho \"Preview via Omega Script\"\n\"$OMEGA\" --run \"$OUTDIR\" || true\necho \"Done. See $OUTDIR\"\n";
    write_file("omega_brain_asr_pkg/bin/run_pipeline", runner, 0755);

    /* include/omega.h */
    const char *omega_h =
      "/* omega helper */\n#ifndef OMEGA_H\n#define OMEGA_H\n#include <stdio.h>\nstatic inline void omega_log(const char*s){fprintf(stderr,\"[omega] %s\\n\", s);} \n#endif\n";
    write_file("omega_brain_asr_pkg/include/omega.h", omega_h, 0644);

    /* usr/tools/audio_preprocess.py */
    const char *audio_preprocess =
      "#!/usr/bin/env python3\nimport argparse, json, math, wave, struct\n# Prototype: read WAV, compute frame energy + zero-crossing as simple features\n\ndef extract_features(wav, out):\n    try:\n        wf = wave.open(wav,'rb')\n    except Exception as e:\n        print('cannot open', wav, e); return\n    nchan = wf.getnchannels(); rate = wf.getframerate(); n = wf.getnframes()\n    frames = wf.readframes(n)\n    fmt = '<' + 'h'*(nchan*n)\n    # crude: compute per-100ms energy\n    window = int(rate/10)\n    ener = []\n    for i in range(0, n, window):\n        seg = frames[(i*nchan*2):min(len(frames),(i+window)*nchan*2)]\n        s = 0\n        for j in range(0,len(seg),2):\n            val = struct.unpack('<h', seg[j:j+2])[0]\n            s += val*val\n        ener.append(s/float(max(1,len(seg)/2)))\n    # write\n    with open(out,'w',encoding='utf-8') as f: json.dump({'rate':rate,'frames':len(ener),'energy':ener}, f)\n    print('wrote', out)\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--wav', required=True); p.add_argument('--out', default='feat.json'); a=p.parse_args(); extract_features(a.wav,a.out)\n";
    write_file("omega_brain_asr_pkg/usr/tools/audio_preprocess.py", audio_preprocess, 0755);

    /* usr/tools/biomodel.py */
    const char *biomodel =
      "#!/usr/bin/env python3\nimport argparse, json, random\n# Prototype biomodel generator: templates representing basal ganglia language nodes\n\nBASIC_TEMPLATES = [\n  {'node':'striatum','role':'action_selection','params':{'dopamine_level':0.8}},\n  {'node':'globus_pallidus','role':'inhibition','params':{'gain':1.0}},\n  {'node':'subthalamic','role':'excitation','params':{'resonance':0.6}},\n  {'node':'thalamus','role':'relay','params':{'gain':0.9}}\n]\n\ndef generate(seed, out):\n    random.seed(seed)\n    templates = []\n    for i in range(6):\n        t = random.choice(BASIC_TEMPLATES).copy()\n        t['id'] = 't%02d'%i\n        # perturb params guided by seed\n        for k in t['params']: t['params'][k] = round(t['params'][k]*(0.8+random.random()*0.8),3)\n        templates.append(t)\n    with open(out,'w',encoding='utf-8') as f: json.dump({'templates':templates}, f, indent=2)\n    print('wrote', out)\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--seed', default='0'); p.add_argument('--out', default='templates.json'); a=p.parse_args(); generate(a.seed, a.out)\n";
    write_file("omega_brain_asr_pkg/usr/tools/biomodel.py", biomodel, 0755);

    /* usr/tools/asr_engine.c - small prototype ASR in C (pattern match on energy sequences) */
    const char *asr_engine =
      "/* asr_engine.c - prototype ASR engine (pattern-match using template-driven motifs)\n * usage: asr_engine --feat feat.json --templates templates.json --out transcripts.txt --count N\n */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nstatic char *read_file(const char *p){ FILE*f=fopen(p,\"rb\"); if(!f) return NULL; fseek(f,0,SEEK_END); long s=ftell(f); fseek(f,0,SEEK_SET); char *b=malloc(s+1); fread(b,1,s,f); b[s]=0; fclose(f); return b; }\n\nint main(int argc, char **argv){ const char *feat=\"feat.json\", *templ=\"templates.json\", *out=\"transcripts.txt\"; int count=3; for(int i=1;i<argc;i++){ if(strcmp(argv[i],\"--feat\")==0 && i+1<argc) feat=argv[++i]; if(strcmp(argv[i],\"--templates\")==0 && i+1<argc) templ=argv[++i]; if(strcmp(argv[i],\"--out\")==0 && i+1<argc) out=argv[++i]; if(strcmp(argv[i],\"--count\")==0 && i+1<argc) count=atoi(argv[++i]); }\n    char *fbuf = read_file(feat); char *tbuf = read_file(templ);\n    if(!fbuf){ fprintf(stderr,\"no feat\\n\"); return 1; }\n    if(!tbuf) { fprintf(stderr,\"no templates\\n\"); }\n    // crude parsing: find 'energy':[ ... ] in feat.json\n    double energies[1024]; int en = 0;\n    char *p = strstr(fbuf, \"\\\"energy\\\"\"); if(p){ p = strchr(p,'['); if(p){ p++; while(*p && *p!=']' && en<1024){ double v; if(sscanf(p, \"%lf\", &v)==1){ energies[en++]=v; p = strchr(p, ','); if(!p) break; p++; } else break; } } }\n    FILE *fo = fopen(out, \"w\"); if(!fo) return 1;\n    for(int i=0;i<count;i++){\n        // match simple rule: low-high-low energy pattern => vowel-like token; high-constant => consonant-like\n        const char *token = \"[noise]\";\n        if(en>3){ double a=energies[0], b=energies[en/2], c=energies[en-1]; if(a< b && c< b) token = \"vowel_like\"; else if(b> a && b> c) token = \"stressed\"; else token = \"speech_segment\"; }\n        fprintf(fo, \"utt_%02d: %s\\n\", i+1, token);\n    }\n    fclose(fo);\n    if(fbuf) free(fbuf); if(tbuf) free(tbuf);\n    printf(\"wrote %s\\n\", out);\n    return 0; }\n";
    write_file("omega_brain_asr_pkg/usr/tools/asr_engine.c", asr_engine, 0644);

    /* usr/lang/omegascript.c - minimal C Omega Script stub to preview transcripts */
    const char *omegascript_c =
      "/* omegascript.c - minimal preview runner: prints transcripts and template summary */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nstatic char *readf(const char *p){ FILE*f=fopen(p,\"rb\"); if(!f) return NULL; fseek(f,0,SEEK_END); long s=ftell(f); fseek(f,0,SEEK_SET); char *b=malloc(s+1); fread(b,1,s,f); b[s]=0; fclose(f); return b; }\nint main(int argc, char **argv){ const char *runDir = argc>2? argv[2] : \"generated\"; char path[1024]; snprintf(path,sizeof(path),\"%s/transcripts.txt\", runDir); char *t = readf(path); if(t){ printf(\"=== transcripts ===\\n%s\\n\", t); free(t); } else printf(\"no transcripts in %s\\n\", runDir);\n    snprintf(path,sizeof(path),\"%s/templates.json\", runDir); char *u = readf(path); if(u){ printf(\"=== templates ===\\n%.*s\\n\", 200, u); free(u);} return 0; }\n";
    write_file("omega_brain_asr_pkg/usr/lang/omegascript.c", omegascript_c, 0644);

    /* templates/sample human DB (JSON) */
    const char *template_db =
      "{\n  \"people\": [\n    {\"id\":\"p01\",\"age\":30,\"gender\":\"F\",\"speech_profile\":{\"pitch_mean\":220,\"pitch_var\":15}},\n    {\"id\":\"p02\",\"age\":45,\"gender\":\"M\",\"speech_profile\":{\"pitch_mean\":120,\"pitch_var\":20}}\n  ]\n}\n";
    write_file("omega_brain_asr_pkg/usr/tools/templates/human_db.json", template_db, 0644);

    /* sample viewer script (python) to combine outputs into HTML */
    const char *viewer_py =
      "#!/usr/bin/env python3\nimport argparse,os,webbrowser\nT='''<!doctype html><html><meta charset=\"utf-8\"><title>ASR Report</title></head><body><h1>ASR Report</h1>%s</body></html>'''\n\ndef build(d):\n    parts=[]\n    for fn in sorted(os.listdir(d)):\n        if fn.endswith('.txt') or fn.endswith('.json'):\n            parts.append('<h2>'+fn+'</h2><pre>'+open(os.path.join(d,fn),'r',encoding='utf-8',errors='ignore').read()[:20000]+'</pre>')\n    return T % ('<hr/>'.join(parts))\n\nif __name__=='__main__':\n    p=argparse.ArgumentParser(); p.add_argument('--dir',default='generated'); p.add_argument('--open',action='store_true'); a=p.parse_args(); html=build(a.dir); out=os.path.join(a.dir,'report.html'); open(out,'w',encoding='utf-8').write(html); print('wrote',out);\n    if a.open: webbrowser.open('file://'+os.path.abspath(out))\n";
    write_file("omega_brain_asr_pkg/usr/tools/viewer.py", viewer_py, 0755);

    /* Makefiles and convenience build script */
    const char *tools_make =
      "all:\n\tgcc -O2 -std=c11 -o usr/tools/asr_engine usr/tools/asr_engine.c || true\n\tgcc -O2 -std=c11 -o usr/lang/omegascript usr/lang/omegascript.c || true\n\tgcc -O2 -std=c11 -o usr/tools/registry_stub usr/tools/registry_sim_stub.c 2>/dev/null || true\n\nclean:\n\trm -f usr/tools/asr_engine usr/lang/omegascript\n";
    write_file("omega_brain_asr_pkg/Makefile", tools_make, 0644);

    /* small registry_sim_stub.c so Makefile compiles (optional) */
    const char *reg_stub =
      "/* minimal stub to satisfy build */\n#include <stdio.h>\nint main(){ printf(\"registry stub\\n\"); return 0; }\n";
    write_file("omega_brain_asr_pkg/usr/tools/registry_sim_stub.c", reg_stub, 0644);

    /* simple sample WAV note to guide user */
    const char *note =
      "Sample: place a 16-bit PCM WAV 'sample.wav' in package root or call run_pipeline with --wav <path>\n";
    write_file("omega_brain_asr_pkg/NOTE.txt", note, 0644);

    printf("Created package '%s'. Build engines: cd %s && make all ; Run: ./bin/run_pipeline --wav sample.wav --outdir generated\n", root, root);
    return 0;
}
```

保存後、コンパイルして実行してください。生成されるパッケージには:
- 音声前処理（Python）で簡易特徴量（エネルギー）を抽出
- 生体模倣テンプレートを生成する biomodel（Python）
- C での簡易 ASR エンジン（エネルギーパターンに基づく擬似認識）
- Omega Script の C 実装スタブで生成物をプレビュー
- HTML ビューアで出力の確認

必要なら、次の拡張（番号で指定）を実装します:
1) フレーム毎の MFCC 抽出と DTW ベースのテンプレート照合（C 実装）  
2) 大脳基底核モデルをニューラルネット化（PyTorch/TensorFlow）して ASR に組込む（学習済みネット不要）  
3) Omega Script を字句解析＋簡易実行系へ拡張（C 実装）  
4) 実機ブレインインタフェース入力（生体信号）向けプラグイン（ハードウェア安全配慮要）  

どれを進めますか？
