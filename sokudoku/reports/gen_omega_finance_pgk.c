  /* gen_omega_finance_pkg.c
   *
   * Generate 'omega_finance_pkg' directory with:
   *  - bin/launcher.c, bin/run_pipeline.sh
   *  - lib/data_io.c (CSV read)
   *  - lib/transform.c (zeta-like transform)
   *  - lib/id_map.c (SHA256 -> ID)
   *  - lib/db.c (simple file DB)
   *  - lib/predict.c (moving-average + linear-regression predictor)
   *  - lib/omega_interp.c (simple Omega-like interpreter)
   *  - include/omega_finance.h
   *  - Makefile, examples/
   *
   * Educational template. Not for trading use.
   */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) _mkdir(p)
# define PATH_SEP '\\'
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) mkdir((p), 0755)
# define PATH_SEP '/'
#endif

  static int ensure_dir(const char *p){
  int r = MKDIR(p);
  if(r==0) return 0;
  if(errno==EEXIST) return 0;
  return -1;
}
  static int write_file(const char *path, const char *data){
    FILE *f = fopen(path, "wb");
    if(!f) return -1;
    size_t n = strlen(data);
    if(fwrite(data,1,n,f) != n){ fclose(f); return -1; }
    fclose(f);
    return 0;
  }

int main(void){
  const char *root = "omega_finance_pkg";
  char path[1024];
  const char *dirs[] = {"bin","lib","include","etc","usr","data","examples"};
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path, sizeof path, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(path) != 0){ fprintf(stderr, "mkdir failed: %s (%s)\n", path, strerror(errno)); return 1; }
  }

  /* include/omega_finance.h */
    const char *hdr =
      "/* include/omega_finance.h */\n#ifndef OMEGA_FINANCE_H\n#define OMEGA_FINANCE_H\n\n/* Data IO */\nint load_prices_csv(const char *csv_path);\n\n/* Transform */\ndouble zeta_like_transform(double x); /* z(x) = i*sin(i*x*log(x)) -> numeric (real part handled via identity) */\n\n/* ID mapping */\nchar *text_to_id(const char *text); /* caller frees */\n\n/* DB */\nint db_store_day(const char *date, const char *json_line);\n\n/* Predict */\ndouble predict_next_linear(const char *symbol, int days_ahead);\n\n/* Interpreter */\nint omega_interp(const char *script);\n\n#endif\n";
    snprintf(path, sizeof path, "%s%cinclude%comega_finance.h", root, PATH_SEP, PATH_SEP);
    if(write_file(path, hdr) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/data_io.c - reads CSV of format: date,symbol,price */
    const char *data_io =
      "/* lib/data_io.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_finance.h\"\n\n/* Very small in-memory store: a flat file in data/raw.csv is appended */\nint load_prices_csv(const char *csv_path){\n    if(!csv_path) return -1;\n    FILE *in = fopen(csv_path, \"r\"); if(!in) return -1;\n    FILE *out = fopen(\"data/raw.csv\", \"a\"); if(!out){ fclose(in); return -1; }\n    char line[1024]; while(fgets(line, sizeof line, in)){\n        fputs(line, out);\n    }\n    fclose(in); fclose(out);\n    return 0;\n}\n";
    snprintf(path, sizeof path, "%s%clib%cdata_io.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, data_io) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/transform.c - numeric transform z(x) = i*sin(i*x*log x)
       Using identity: sin(i y) = i sinh(y) -> sin(i*x*log x) = i sinh(x log x)
       Thus i * sin(i*x*log x) = i * (i sinh(x log x)) = -sinh(x log x)
       So transform is real: -sinh(x * log x). We'll use double math.
    */
    const char *transform =
      "/* lib/transform.c */\n#include <math.h>\n#include \"../include/omega_finance.h\"\n\ndouble zeta_like_transform(double x){\n    if(x<=0.0) return 0.0; /* undefined log; treat as 0 */\n    double y = x * log(x);\n    double s = sinh(y);\n    return -s; /* as derived */\n}\n";
    snprintf(path, sizeof path, "%s%clib%ctransform.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, transform) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/id_map.c - SHA256 -> ID using simple internal implementation (no OpenSSL required)
       small SHA256 implementation (public-domain minimal) would be long; for simplicity use a tiny FNV-1a 64-bit hash to produce ID.
    */
    const char *id_map =
"/* lib/id_map.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <stdint.h>\n#include \"../include/omega_finance.h\"\n\nstatic unsigned long long fnv1a_64(const unsigned char *s){\n    unsigned long long h = 1469598103934665603ULL;\n    while(*s){ h ^= (unsigned long long)(*s++); h *= 1099511628211ULL; }\n    return h;\n}\nchar *text_to_id(const char *text){ if(!text) return NULL; unsigned long long h = fnv1a_64((const unsigned char*)text); char *out = malloc(32); if(!out) return NULL; snprintf(out,32,\"ID-%016llx\", (unsigned long long)h); return out; }\n";
    snprintf(path, sizeof path, "%s%clib%cid_map.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, id_map) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/db.c - store per-day JSON lines in data/db/<date>.jsonl */
    const char *db =
      "/* lib/db.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_finance.h\"\n\nint ensure_dir_local(const char *d){ char cmd[1024]; snprintf(cmd,sizeof cmd,\"mkdir -p %s\", d); return system(cmd); }\nint db_store_day(const char *date, const char *json_line){ if(!date||!json_line) return -1; ensure_dir_local(\"data/db\"); char path[1024]; snprintf(path,sizeof path,\"data/db/%s.jsonl\", date); FILE *f = fopen(path, \"a\"); if(!f) return -1; fprintf(f, \"%s\\n\", json_line); fclose(f); return 0; }\n";
    snprintf(path, sizeof path, "%s%clib% cdb.c", root, PATH_SEP, PATH_SEP); /* will correct */ 
    snprintf(path, sizeof path, "%s%clib%cdb.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, db) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/predict.c - simple per-symbol linear regression predictor and moving average */
    const char *predict =
      "/* lib/predict.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n#include \"../include/omega_finance.h\"\n\n/* Very small loader: read last N prices for symbol from data/raw.csv scanning file (inefficient but simple) */\nstatic int load_last_prices(const char *symbol, double *out, int maxn){ FILE *f = fopen(\"data/raw.csv\",\"r\"); if(!f) return 0; char line[1024]; double tmp[1024]; int cnt=0; while(fgets(line,sizeof line,f)){ char date[64], sym[128]; double price; if(sscanf(line, \"%63[^,],%127[^,],%lf\", date, sym, &price) != 3) continue; if(strcmp(sym, symbol)==0){ if(cnt<1024) tmp[cnt++]=price; } }\n    fclose(f);\n    int n = cnt<maxn?cnt:maxn; for(int i=0;i<n;i++) out[i]= tmp[cnt - n + i]; return n; }\n\n/* simple linear regression on last n points (x=0..n-1), predict days_ahead ahead */\ndouble predict_next_linear(const char *symbol, int days_ahead){ if(!symbol) return 0.0; int MAX=30; double buf[30]; int n = load_last_prices(symbol, buf, MAX); if(n<2) return (n==1)?buf[0]:0.0; double sx=0, sy=0, sxx=0, sxy=0; for(int i=0;i<n;i++){ double x=i; sx+=x; sy+=buf[i]; sxx+=x*x; sxy+=x*buf[i]; }\n    double denom = n*sxx - sx*sx; if(fabs(denom) < 1e-12) return buf[n-1]; double a = (n*sxy - sx*sy)/denom; double b = (sy - a*sx)/n; double pred = a*(n-1 + days_ahead) + b; return pred; }\n\n/* moving average predictor */\ndouble predict_ma(const char *symbol, int window){ double buf[30]; int n = load_last_prices(symbol, buf, window); if(n==0) return 0.0; double s=0; for(int i=0;i<n;i++) s+=buf[i]; return s/n; }\n";
    snprintf(path, sizeof path, "%s%clib%cpredict.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, predict) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/omega_interp.c - tiny interpreter exposing functions to call pipeline */
    const char *interp =
      "/* lib/omega_interp.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_finance.h\"\n\n/* commands:\n   ingest <csv_path>\n   analyze_day <date>\n   predict <symbol> [days]\n*/\nint omega_interp(const char *script){ if(!script) return -1; char cmd[128], arg1[512], arg2[128]; int got = sscanf(script, \"%127s %511s %127s\", cmd, arg1, arg2);\n    if(got>=2 && strcmp(cmd, \"ingest\")==0){ if(load_prices_csv(arg1)==0){ printf(\"ingested %s\\n\", arg1); return 0; } else { printf(\"ingest failed\\n\"); return 2; } }\n    if(got>=2 && strcmp(cmd, \"predict\")==0){ int days = (got>=3)?atoi(arg2):1; double v = predict_next_linear(arg1, days); printf(\"predict %s +%d -> %g\\n\", arg1, days, v); return 0; }\n    if(got>=2 && strcmp(cmd, \"analyze_day\")==0){ /* build per-day db from raw.csv for this date */\n        FILE *f = fopen(\"data/raw.csv\",\"r\"); if(!f){ printf(\"no data\\n\"); return 2; }\n        char line[1024]; while(fgets(line,sizeof line,f)){\n            char date[64], sym[128]; double price; if(sscanf(line, \"%63[^,],%127[^,],%lf\", date, sym, &price)!=3) continue; if(strcmp(date, arg1)==0){ /* compute transform & id & store */ char buf[256]; double z = zeta_like_transform(price); char txt[256]; snprintf(txt, sizeof txt, \"%s,%s,%g,%g\", date, sym, price, z); char *id = text_to_id(txt); snprintf(buf, sizeof buf, \"{\\\"date\\\":\\\"%s\\\",\\\"sym\\\":\\\"%s\\\",\\\"price\\\":%g,\\\"z\\\":%g,\\\"id\\\":\\\"%s\\\"}\", date, sym, price, z, id); db_store_day(date, buf); free(id); }\n        }\n        fclose(f); printf(\"analyze_day %s done\\n\", arg1); return 0; }\n    printf(\"unknown command\\n\"); return -1; }\n";
    snprintf(path, sizeof path, "%s%clib%comega_interp.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, interp) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/launcher.c */
    const char *launcher =
      "#include <stdio.h>\n#include <stdlib.h>\nint omega_interp(const char*);\nint main(int argc, char **argv){ if(argc<2){ fprintf(stderr, \"Usage: %s <command> [args]\\nExamples:\\n  ingest data/prices.csv\\n  analyze_day 2025-09-25\\n  predict AAPL 1\\\", argv[0]); return 1; } char script[1024]; int i; script[0]=0; for(i=1;i<argc;i++){ if(i>1) strcat(script, \" \"); strcat(script, argv[i]); } return omega_interp(script); }\n";
    snprintf(path, sizeof path, "%s% cbin%clauncher.c", root, PATH_SEP, PATH_SEP); /* will correct */ 
    snprintf(path, sizeof path, "%s%cbin%clauncher.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, launcher) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* examples/sample CSV */
    const char *example_csv =
      "# date,symbol,price\n2025-09-20,AAPL,150.0\n2025-09-21,AAPL,152.0\n2025-09-22,AAPL,151.0\n2025-09-23,AAPL,153.5\n2025-09-24,AAPL,154.0\n2025-09-20,MSFT,300.0\n2025-09-21,MSFT,302.0\n2025-09-22,MSFT,301.0\n2025-09-23,MSFT,305.0\n2025-09-24,MSFT,307.0\n";
    snprintf(path, sizeof path, "%s%cexamples%cprices_sample.csv", root, PATH_SEP, PATH_SEP);
    if(write_file(path, example_csv) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* Makefile */
    const char *makefile =
      "CC=gcc\nCFLAGS=-O2 -Iinclude\n\nall: bin/launcher lib/tools\n\nlib/tools: lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c lib/omega_interp.c\n\t$(CC) $(CFLAGS) -c lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c lib/omega_interp.c\n\t$(CC) $(CFLAGS) -o lib/tools data.o transform.o id_map.o db.o predict.o omega_interp.o 2>/dev/null || true\n\nbin/launcher: bin/launcher.c lib/omega_interp.c lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c\n\t$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c lib/omega_interp.c\n\nclean:\n\trm -f lib/*.o bin/launcher data/raw.csv data/db/*.jsonl\n";
    snprintf(path, sizeof path, "%s%cMakefile", root, PATH_SEP);
    if(write_file(path, makefile) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/run_pipeline.sh */
    const char *runsh =
      "#!/bin/sh\nset -e\nROOT=$(cd \"$(dirname \"$0\")/..\" && pwd)\ncd \"$ROOT\"\nmake\n# Example pipeline: ingest sample, analyze day, predict\n./bin/launcher ingest examples/prices_sample.csv\n./bin/launcher analyze_day 2025-09-24\n./bin/launcher predict AAPL 1\n";
    snprintf(path, sizeof path, "%s%cbin%crun_pipeline.sh", root, PATH_SEP, PATH_SEP);
    if(write_file(path, runsh) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }
#if !defined(_WIN32) && !defined(_WIN64)
    chmod(path, 0755);
#endif

    /* small README in etc/ */
    const char *etc_readme = "This package is a template. Review code before use. Not for trading.\n";
    snprintf(path, sizeof path, "%s%cetc%cREADME.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, etc_readme) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    printf("Package '%s' created.\n", root);
    printf("Build & example:\n  cd %s\n  make\n  ./bin/run_pipeline.sh\n\nNotes: This template performs simple transform and prediction only.\n", root);
    return 0;
}
