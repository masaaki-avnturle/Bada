/*
 * pkginstallgen.c
 *
 * Generate two fixed packages:
 *  - omega_registry_pkg    (keybinds / registry simulator)
 *  - omega_brain_asr_pkg   (ASR prototype)
 *
 * Both packages produce C sources that compile without the earlier stray '\' /
 * unterminated string / sscanf bracket errors. The omegascript.c implementation
 * avoids problematic sscanf [] scans and uses safe parsing.
 *
 * Build and run:
 *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
 *   ./pkginstallgen
 *
 * After run:
 *   make -C omega_registry_pkg all
 *   make -C omega_brain_asr_pkg all
 *
 * This is a generator only; produced code is small prototypes.
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
        tmp[sizeof(tmp)-1] = 0;
        char *p = strrchr(tmp, '/');
        if (p && p != tmp) { *p = 0; if (ensure_dir(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1; }
    }
    return -1;
}

static int write_file(const char *path, const char *data, int mode) {
    char dir[4096];
    strncpy(dir, path, sizeof(dir)-1);
    dir[sizeof(dir)-1] = 0;
    char *p = strrchr(dir, '/');
    if (p) { *p = 0; ensure_dir(dir); }
    FILE *f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
    if (data && fputs(data, f) == EOF) { fclose(f); return -1; }
    fclose(f);
    if (mode) chmod(path, (mode_t)mode);
    return 0;
}

/* Write omega_registry_pkg */
static void gen_registry_pkg(void) {
    const char *root = "omega_registry_pkg";
    ensure_dir(root);
    write_file("omega_registry_pkg/README.md",
"# omega_registry_pkg\n\nPrototype registry/keybind package.\n", 0644);

    write_file("omega_registry_pkg/Makefile",
"CC ?= gcc\nCFLAGS ?= -O2 -std=c11 -Wall -Wextra\nTOOLS_DIR := usr/tools\nLANG_DIR := usr/lang\nTOOLS_SRCS := $(wildcard $(TOOLS_DIR)/*.c)\nTOOLS_BINS := $(patsubst $(TOOLS_DIR)/%.c,$(TOOLS_DIR)/%,$(TOOLS_SRCS))\nLANG_SRCS := $(wildcard $(LANG_DIR)/*.c)\nLANG_BINS := $(patsubst $(LANG_DIR)/%.c,$(LANG_DIR)/%,$(LANG_SRCS))\n.PHONY: all tools lang clean\nall: tools lang\ntools: $(TOOLS_BINS)\n$(TOOLS_DIR)/%: $(TOOLS_DIR)/%.c\n\t@mkdir -p $(TOOLS_DIR)\n\t$(CC) $(CFLAGS) -o $@ $<\nlang: $(LANG_BINS)\n$(LANG_DIR)/%: $(LANG_DIR)/%.c\n\t@mkdir -p $(LANG_DIR)\n\t$(CC) $(CFLAGS) -o $@ $<\nclean:\n\t-@rm -f $(TOOLS_BINS) $(LANG_BINS)\n", 0644);

    ensure_dir("omega_registry_pkg/usr/tools");
    ensure_dir("omega_registry_pkg/usr/lang");
    ensure_dir("omega_registry_pkg/etc");

    write_file("omega_registry_pkg/etc/emacs_bindings.conf",
"# app:keys => action\neditor:Ctrl-x Ctrl-s => save\neditor:Ctrl-x Ctrl-c => quit\n", 0644);

    /* registry_sim.c - safe, no problematic escapes */
    write_file("omega_registry_pkg/usr/tools/registry_sim.c",
"/* registry_sim.c - simple file-backed key=value store */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nstatic const char *DB = \"omega_registry.json\";\nstatic void ensure_db(void) { FILE*f = fopen(DB,\"a\"); if(f) fclose(f); }\nstatic void show_db(void) { ensure_db(); FILE*f=fopen(DB,\"r\"); if(!f){perror(\"open\");return;} char b[4096]; puts(\"-- registry --\"); while(fgets(b,sizeof(b),f)) fputs(b,stdout); fclose(f); }\nstatic void get_key(const char*k){ ensure_db(); FILE*f=fopen(DB,\"r\"); if(!f){perror(\"open\");return;} char b[4096]; size_t L=strlen(k); while(fgets(b,sizeof(b),f)){ if(strncmp(b,k,L)==0 && b[L]=='='){ printf(\"%s\", b+L+1); fclose(f); return; } } fclose(f); printf(\"(null)\\n\"); }\nstatic void set_key(const char*k,const char*v){ ensure_db(); FILE*f=fopen(DB,\"r\"); if(!f){ FILE*w=fopen(DB,\"w\"); if(!w){perror(\"open w\");return;} fprintf(w,\"%s=%s\\n\",k,v); fclose(w); printf(\"set %s\\n\",k); return;} char tmp[512]; snprintf(tmp,sizeof(tmp),\"%s.tmp\",DB); FILE*t=fopen(tmp,\"w\"); if(!t){perror(\"open tmp\"); fclose(f); return;} char b[4096]; size_t L=strlen(k); int found=0; while(fgets(b,sizeof(b),f)){ if(strncmp(b,k,L)==0 && b[L]=='='){ fprintf(t,\"%s=%s\\n\",k,v); found=1;} else fputs(b,t); } if(!found) fprintf(t,\"%s=%s\\n\",k,v); fclose(f); fclose(t); remove(DB); rename(tmp,DB); printf(\"set %s\\n\",k); }\nstatic void del_key(const char*k){ ensure_db(); FILE*f=fopen(DB,\"r\"); if(!f){perror(\"open r\");return;} char tmp[512]; snprintf(tmp,sizeof(tmp),\"%s.tmp\",DB); FILE*t=fopen(tmp,\"w\"); if(!t){perror(\"open tmp\"); fclose(f); return;} char b[4096]; size_t L=strlen(k); while(fgets(b,sizeof(b),f)){ if(strncmp(b,k,L)==0 && b[L]=='=') continue; fputs(b,t); } fclose(f); fclose(t); remove(DB); rename(tmp,DB); printf(\"del %s\\n\",k); }\nint main(int argc,char**argv){ if(argc<2){ fprintf(stderr,\"usage: registry_sim --get KEY | --set KEY VALUE | --del KEY | --show\\n\"); return 1;} if(strcmp(argv[1],\"--show\")==0){ show_db(); return 0;} if(strcmp(argv[1],\"--get\")==0 && argc>=3){ get_key(argv[2]); return 0;} if(strcmp(argv[1],\"--set\")==0 && argc>=4){ set_key(argv[2],argv[3]); return 0;} if(strcmp(argv[1],\"--del\")==0 && argc>=3){ del_key(argv[2]); return 0;} fprintf(stderr,\"invalid args\\n\"); return 2; }\n", 0644);

    /* emacs_bindings.c - safe parsing, no escapes in C literal content */
    write_file("omega_registry_pkg/usr/tools/emacs_bindings.c",
"/* emacs_bindings.c - apply Emacs-like keybindings (prototype) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <sys/stat.h>\nstatic void ensure_dir(const char *p){ struct stat st; if(stat(p,&st)!=0) mkdir(p,0755); }\nstatic void rtrim(char *s){ size_t L=strlen(s); while(L>0){ char c=s[L-1]; if(c=='\\n'||c=='\\r'||c==' '||c=='\\t'){ s[--L]='\\0'; } else break;} }\nint main(int argc,char**argv){ const char*conf=\"etc/emacs_bindings.conf\"; int apply=0; for(int i=1;i<argc;i++){ if(strcmp(argv[i],\"--config\")==0 && i+1<argc) conf=argv[++i]; if(strcmp(argv[i],\"--apply\")==0) apply=1; }\n FILE*f=fopen(conf,\"r\"); if(!f){ fprintf(stderr,\"cannot open %s\\n\",conf); return 1; }\n ensure_dir(\"generated\"); ensure_dir(\"generated/app_configs\"); char line[1024]; while(fgets(line,sizeof(line),f)){ rtrim(line); if(line[0]=='#' || strlen(line)<3) continue; char*col=strchr(line,':'); if(!col) continue; *col='\\0'; char*app=line; char*rest=col+1; char*arr=strstr(rest,\"=>\"); if(!arr) continue; *arr='\\0'; char*keys=rest; char*action=arr+2; while(*keys==' '||*keys=='\\t') ++keys; while(*action==' '||*action=='\\t') ++action; rtrim(keys); rtrim(action); char out[1024]; snprintf(out,sizeof(out),\"generated/app_configs/%s.conf\",app); FILE*o=fopen(out,\"a\"); if(!o) continue; fprintf(o,\"%s => %s\\n\", keys, action); fclose(o); if(apply) printf(\"applied %s: %s => %s\\n\", app, keys, action); }\n fclose(f); printf(\"wrote generated/app_configs/\\n\"); return 0; }\n", 0644);

    /* omegascript.c - safe, avoids scanf with bracket patterns */
    write_file("omega_registry_pkg/usr/lang/omegascript.c",
"/* omegascript.c - minimal Omega Script interpreter (safe parsing) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\nstatic void trimnl(char*s){ char*p=s+strlen(s)-1; while(p>=s && (*p=='\\n'||*p=='\\r')) *p--='\\0'; }\nint main(int argc,char**argv){ const char*script=\"usr/lang/demo.os\"; for(int i=1;i<argc;i++) if(strcmp(argv[i],\"--run\")==0 && i+1<argc) script=argv[++i]; FILE*f=fopen(script,\"r\"); if(!f){ fprintf(stderr,\"no script %s\\n\",script); return 1; } char line[1024]; while(fgets(line,sizeof(line),f)){ trimnl(line); if(strncmp(line,\"print \",6)==0){ char*p=strchr(line,'\"'); if(p){ char*q=strrchr(line,'\"'); if(q && q>p){ *q='\\0'; puts(p+1); } } } else if(strncmp(line,\"set \",4)==0){ char *tok=strtok(line+4,\" \\t\"); char *val=NULL; if(tok) val=strtok(NULL,\"\"); if(tok) printf(\"set %s=%s\\n\",tok, val?val:\"\\0\"); } else if(strncmp(line,\"reg_set \",8)==0){ char *rest=line+8; char *k=strtok(rest,\" \\t\"); char *v=strtok(NULL,\"\"); if(k){ char cmd[1024]; snprintf(cmd,sizeof(cmd),\"./usr/tools/registry_sim --set %s '%s'\", k, v?v:\"\" ); system(cmd); } } else if(strncmp(line,\"reg_get \",8)==0){ char *k=line+8; while(*k==' '||*k=='\\t')++k; char tmp[256]; sscanf(k,\"%255s\",tmp); char cmd[512]; snprintf(cmd,sizeof(cmd),\"./usr/tools/registry_sim --get %s\", tmp); system(cmd); } }\n fclose(f); return 0; }\n", 0644);

    /* demo.os with single backslashes in content */
    write_file("omega_registry_pkg/usr/lang/demo.os",
"print \"Omega Script demo: registry set/get\"\nreg_set HKEY_LOCAL_MACHINE\\Software\\MyApp\\Setting 42\nreg_get HKEY_LOCAL_MACHINE\\Software\\MyApp\\Setting\n", 0644);

    /* initial registry file */
    write_file("omega_registry.json",
"# initial registry\nHKEY_LOCAL_MACHINE\\Software\\MyApp\\Setting=1\n", 0644);
}

/* Write omega_brain_asr_pkg */
static void gen_brain_asr_pkg(void) {
    const char *root = "omega_brain_asr_pkg";
    ensure_dir(root);
    write_file("omega_brain_asr_pkg/README.md",
"# omega_brain_asr_pkg\n\nPrototype ASR package.\n", 0644);

    write_file("omega_brain_asr_pkg/Makefile",
"CC ?= gcc\nCFLAGS ?= -O2 -std=c11 -Wall -Wextra\nTOOLS_DIR := usr/tools\nLANG_DIR := usr/lang\nASR_SRC := $(TOOLS_DIR)/asr_engine.c\nASR_BIN := $(TOOLS_DIR)/asr_engine\nOMEGA_SRC := $(LANG_DIR)/omegascript.c\nOMEGA_BIN := $(LANG_DIR)/omegascript\n.PHONY: all asr omega clean\nall: asr omega\nasr: $(ASR_BIN)\n$(ASR_BIN): $(ASR_SRC)\n\t@mkdir -p $(TOOLS_DIR)\n\t$(CC) $(CFLAGS) -o $@ $<\nomega: $(OMEGA_BIN)\n$(OMEGA_BIN): $(OMEGA_SRC)\n\t@mkdir -p $(LANG_DIR)\n\t$(CC) $(CFLAGS) -o $@ $<\nclean:\n\t-@rm -f $(ASR_BIN) $(OMEGA_BIN)\n", 0644);

    ensure_dir("omega_brain_asr_pkg/usr/tools");
    ensure_dir("omega_brain_asr_pkg/usr/lang");

    /* simple audio_preprocess.py (keeps simple behavior) */
    write_file("omega_brain_asr_pkg/usr/tools/audio_preprocess.py",
"#!/usr/bin/env python3\nimport sys, json\n# Writes a small fake feature file if run\nif __name__=='__main__': out='generated/feat.json'; import os; os.makedirs('generated', exist_ok=True); json.dump({'energy':[1,2,3,2,1]}, open(out,'w')); print('wrote',out)\n", 0755);

    /* biomodel.py simple */
    write_file("omega_brain_asr_pkg/usr/tools/biomodel.py",
"#!/usr/bin/env python3\nimport json\njson.dump({'templates':[{'id':'t01','node':'striatum','dop':0.9}]}, open('generated/templates.json','w'))\nprint('wrote generated/templates.json')\n", 0755);

    /* asr_engine.c - small, safe parsing */
    write_file("omega_brain_asr_pkg/usr/tools/asr_engine.c",
"/* asr_engine.c - prototype */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nstatic char *readf(const char*p){ FILE*f=fopen(p,\"rb\"); if(!f) return NULL; fseek(f,0,SEEK_END); long s=ftell(f); fseek(f,0,SEEK_SET); char*b=malloc(s+1); if(!b){fclose(f);return NULL;} fread(b,1,s,f); b[s]=0; fclose(f); return b; }\nint main(int argc,char**argv){ const char*feat=\"generated/feat.json\"; const char*out=\"generated/transcripts.txt\"; for(int i=1;i<argc;i++){ if(strcmp(argv[i],\"--feat\")==0 && i+1<argc) feat=argv[++i]; if(strcmp(argv[i],\"--out\")==0 && i+1<argc) out=argv[++i]; }\n char *f=readf(feat); if(!f){ fprintf(stderr,\"no feat\\n\"); return 1; }\n FILE*o=fopen(out,\"w\"); if(!o){ free(f); return 1; }\n fprintf(o,\"utt_01: vowel_like\\n\"); fclose(o); free(f); printf(\"wrote %s\\n\", out); return 0; }\n", 0644);

    /* omegascript.c - safe preview */
    write_file("omega_brain_asr_pkg/usr/lang/omegascript.c",
"/* omegascript.c - preview transcripts (safe parsing) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nstatic char*rf(const char*p){ FILE*f=fopen(p,\"rb\"); if(!f)return NULL; fseek(f,0,SEEK_END); long s=ftell(f); fseek(f,0,SEEK_SET); char*b=malloc(s+1); if(!b){fclose(f);return NULL;} fread(b,1,s,f); b[s]=0; fclose(f); return b; }\nint main(int argc,char**argv){ const char*dir=\"generated\"; if(argc>1) dir=argv[1]; char path[512]; snprintf(path,sizeof(path),\"%s/transcripts.txt\",dir); char*p=rf(path); if(p){ printf(\"=== transcripts ===\\n%s\\n\",p); free(p);} else printf(\"no transcripts\\n\"); return 0; }\n", 0644);

    /* viewer.py */
    write_file("omega_brain_asr_pkg/usr/tools/viewer.py",
"#!/usr/bin/env python3\nimport os,sys,webbrowser\nd='generated' if len(sys.argv)<=1 else sys.argv[1]\nout=os.path.join(d,'report.html'); os.makedirs(d,exist_ok=True)\nwith open(out,'w',encoding='utf-8') as f:\n    f.write('<html><body><h1>ASR Report</h1>');\n    for fn in sorted(os.listdir(d)):\n        if fn.endswith('.txt') or fn.endswith('.json'):\n            f.write('<h2>'+fn+'</h2><pre>'+open(os.path.join(d,fn),'r',encoding='utf-8',errors='ignore').read()[:10000]+'</pre>')\n    f.write('</body></html>')\nprint('wrote',out)\n", 0755);
}

int main(void) {
    gen_registry_pkg();
    gen_brain_asr_pkg();
    printf("Both packages generated. Run 'make all' in each package directory.\n");
    return 0;
}
