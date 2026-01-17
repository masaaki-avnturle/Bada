以下は、コアダンプ原因となる可能性のある箇所（バッファオーバーフロー、NULLチェック不足、未初期化メモリ、境界チェック不足など）を徹底的に取り除き、安全に動作するように書き直した完全版 `omegascript.c` です。これをパッケージの `usr/lang/omegascript.c` に置き換え、再ビルド（make）して実行してください。

要点：
- 全てのメモリ割当・再割当・文字列操作の戻り値をチェック
- 固定長バッファを極力小さく使い、可変長は動的確保
- トークン分割は strtok_r を中心に使い安全化
- NULL や失敗時のクリーンアップを徹底
- math.h を明示的に include（log 等）
- 出力ディレクトリ存在確認を安全に実行

保存ファイル名: usr/lang/omegascript.c

コード全文（このままファイルに保存してください）:

```c
/* omegascript.c - robust analyzer (avoid segfault/core dump) */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dirent.h>
#include <sys/stat.h>
#include <errno.h>
#include <math.h>

static char *read_whole(const char *path) {
  if (!path) return NULL;
  FILE *f = fopen(path, "rb");
  if (!f) return NULL;
  if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
  long s = ftell(f);
  if (s < 0) { fclose(f); return NULL; }
  if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
  size_t sz = (size_t)s;
  char *buf = malloc(sz + 1);
  if (!buf) { fclose(f); return NULL; }
  size_t got = fread(buf, 1, sz, f);
  if (got != sz) { /* allow partial reads but handle gracefully */ }
  buf[got] = '\0';
  fclose(f);
  return buf;
}

static double safe_log(double x) {
  if (x <= 0.0) return 0.0;
  return log(x);
}

static double simple_entropy(const char *s) {
  if (!s) return 0.0;
  unsigned long freq[256] = {0};
  size_t n = 0;
  for (const unsigned char *p = (const unsigned char*)s; *p; ++p) {
    freq[*p]++; n++;
  }
  if (n == 0) return 0.0;
  double H = 0.0;
  for (int i = 0; i < 256; ++i) {
    if (freq[i]) {
      double p = (double)freq[i] / (double)n;
      H -= p * safe_log(p + 1e-30);
    }
  }
  return H;
}

static void trim_inplace(char *s) {
  if (!s) return;
  char *start = s;
  while (*start && isspace((unsigned char)*start)) start++;
  if (start != s) memmove(s, start, strlen(start) + 1);
  char *end = s + strlen(s);
  while (end > s && isspace((unsigned char)*(end - 1))) { *--end = '\0'; }
}

static char **collect_lines_with_eq(const char *dir, int *out_n) {
  if (!dir || !out_n) return NULL;
  *out_n = 0;
  DIR *d = opendir(dir);
  if (!d) return NULL;
  struct dirent *ent;
  char **arr = NULL;
  while ((ent = readdir(d)) != NULL) {
    const char *name = ent->d_name;
    if (!name) continue;
    size_t nl = strlen(name);
    if (nl < 5) continue;
    const char *ext = name + nl - 4;
    if (strcasecmp(ext, ".txt") != 0) continue;
    /* build path safely */
    size_t need = strlen(dir) + 1 + strlen(name) + 1;
    char *path = malloc(need);
    if (!path) continue;
    snprintf(path, need, "%s/%s", dir, name);
    char *txt = read_whole(path);
    free(path);
    if (!txt) continue;
    char *save = NULL;
    char *line = strtok_r(txt, "\n", &save);
    while (line) {
      char *linet = strdup(line);
      if (linet) {
	trim_inplace(linet);
	if (linet[0] != '\0' && strchr(linet, '=')) {
	  char **tmp = realloc(arr, sizeof(char*) * ((size_t)(*out_n) + 1));
	  if (tmp) {
	    arr = tmp;
	    arr[*out_n] = linet;
	    (*out_n)++;
	  } else {
	    free(linet);
	  }
	} else {
	  free(linet);
	}
      }
      line = strtok_r(NULL, "\n", &save);
    }
    free(txt);
  }
  closedir(d);
  return arr;
}

/* split by '+' into array of strings (dynamically allocated). returns count. */
static char **split_plus(const char *s, int *count) {
  if (!s || !count) return NULL;
  *count = 0;
  char *work = strdup(s);
  if (!work) return NULL;
  char *save = NULL;
  char *tok = strtok_r(work, "+", &save);
  char **arr = NULL;
  while (tok) {
    trim_inplace(tok);
    if (*tok) {
      char *piece = strdup(tok);
      if (piece) {
	char **tmp = realloc(arr, sizeof(char*) * ((size_t)(*count) + 1));
	if (!tmp) { free(piece); for (int i=0;i<*count;i++) free(arr[i]); free(arr); arr = NULL; *count = 0; break; }
	arr = tmp;
	arr[*count] = piece;
	(*count)++;
      }
    }
    tok = strtok_r(NULL, "+", &save);
  }
  free(work);
  return arr;
}

static char **generate_swapped_candidates(char **eqs, int neqs, int *out_n) {
  if (!eqs || neqs <= 0 || !out_n) { if (out_n) *out_n = 0; return NULL; }
  *out_n = 0;
  char **out = NULL;
  for (int i = 0; i < neqs; ++i) {
    char *e = eqs[i];
    if (!e) continue;
    char *eqp = strchr(e, '=');
    if (!eqp) continue;
    size_t lhs_len = (size_t)(eqp - e);
    char *lhs = malloc(lhs_len + 1);
    if (!lhs) continue;
    memcpy(lhs, e, lhs_len);
    lhs[lhs_len] = '\0';
    char *rhs = strdup(eqp + 1);
    if (!rhs) { free(lhs); continue; }
    trim_inplace(lhs); trim_inplace(rhs);
    int ln=0, rn=0;
    char **lt = split_plus(lhs, &ln);
    char **rt = split_plus(rhs, &rn);
    free(lhs); free(rhs);
    if (!lt || !rt || ln==0 || rn==0) {
      if (lt) { for (int k=0;k<ln;k++) free(lt[k]); free(lt); }
      if (rt) { for (int k=0;k<rn;k++) free(rt[k]); free(rt); }
      continue;
    }
    for (int a=0; a<ln && a<5; ++a) {
      for (int b=0; b<rn && b<5; ++b) {
	/* build candidate string safely using dynamic buffer */
	size_t bufcap = 256;
	char *buf = malloc(bufcap);
	if (!buf) continue;
	buf[0] = '\0';
	for (int u=0; u<ln; ++u) {
	  const char *piece = (u==a) ? rt[b] : lt[u];
	  if (!piece) continue;
	  size_t need = strlen(buf) + strlen(piece) + 4;
	  if (need > bufcap) {
	    char *nb = realloc(buf, need + 128);
	    if (!nb) { free(buf); buf = NULL; break; }
	    buf = nb; bufcap = need + 128;
	  }
	  if (u) strcat(buf, " + ");
	  strcat(buf, piece);
	}
	if (!buf) continue;
	size_t need = strlen(buf) + 4 + 1;
	char *tmp_rhs = malloc(need);
	if (!tmp_rhs) { free(buf); continue; }
	strcpy(tmp_rhs, " = ");
	/* append rhs side built similarly */
	size_t rcap = 256;
	char *rbuf = malloc(rcap);
	if (!rbuf) { free(buf); free(tmp_rhs); continue; }
	rbuf[0] = '\0';
	for (int v=0; v<rn; ++v) {
	  const char *piece = (v==b) ? lt[a] : rt[v];
	  if (!piece) continue;
	  size_t need2 = strlen(rbuf) + strlen(piece) + 4;
	  if (need2 > rcap) {
	    char *nb = realloc(rbuf, need2 + 128);
	    if (!nb) { free(buf); free(tmp_rhs); free(rbuf); rbuf = NULL; break; }
	    rbuf = nb; rcap = need2 + 128;
	  }
	  if (v) strcat(rbuf, " + ");
	  strcat(rbuf, piece);
	}
	if (!rbuf) continue;
	size_t full = strlen(buf) + strlen(tmp_rhs) + strlen(rbuf) + 1;
	char *fulls = malloc(full);
	if (!fulls) { free(buf); free(tmp_rhs); free(rbuf); continue; }
	strcpy(fulls, buf);
	strcat(fulls, tmp_rhs);
	strcat(fulls, rbuf);
	free(buf); free(tmp_rhs); free(rbuf);

	char **narr = realloc(out, sizeof(char*) * ((size_t)(*out_n) + 1));
	if (!narr) { free(fulls); continue; }
	out = narr;
	out[*out_n] = fulls;
	(*out_n)++;
	if (*out_n > 1000) break;
      }
      if (*out_n > 1000) break;
    }
    for (int k=0;k<ln;k++) free(lt[k]);
    for (int k=0;k<rn;k++) free(rt[k]);
    free(lt); free(rt);
  }
  return out;
}

static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) {
    return S_ISDIR(st.st_mode) ? 0 : -1;
  }
  if (mkdir(path, 0755) != 0 && errno != EEXIST) return -1;
  return 0;
}

static void write_outputs(const char *outdir, char **eqs, int neq, char **cands, int ncand) {
  if (!outdir) outdir = ".";
  char outpath[1024];
  snprintf(outpath, sizeof(outpath), "%s/output", outdir);
  ensure_dir(outpath);
  snprintf(outpath, sizeof(outpath), "%s/output/equations.txt", outdir);
  FILE *f = fopen(outpath, "wb");
  if (f) {
    for (int i=0;i<neq;i++) if (eqs && eqs[i]) fprintf(f, "%s\n", eqs[i]);
    fclose(f);
  }
  snprintf(outpath, sizeof(outpath), "%s/output/paper.tex", outdir);
  FILE *g = fopen(outpath, "wb");
  if (g) {
    fprintf(g, "\\documentclass{article}\\begin{document}\\section*{Extracted Equations}\\begin{verbatim}\n");
    for (int i=0;i<neq;i++) if (eqs && eqs[i]) fprintf(g, "%s\n", eqs[i]);
    fprintf(g, "\nGenerated candidates:\n");
    for (int j=0;j<ncand && j<200;j++) if (cands && cands[j]) fprintf(g, "%s\n", cands[j]);
    fprintf(g, "\\end{verbatim}\\end{document}\n");
    fclose(g);
  }
}

int main(int argc, char **argv) {
  if (argc < 4 || strcmp(argv[1], "analyze") != 0) {
    fprintf(stderr, "Usage: %s analyze <reports_dir> <outdir_tex>\n", argv[0]);
    return 1;
  }
  const char *rdir = argv[2];
  const char *outtex = argv[3]; (void)outtex;

  int neq = 0;
  char **eqs = collect_lines_with_eq(rdir, &neq);
  if (!eqs || neq == 0) {
    fprintf(stderr, "No equations found in %s\n", rdir);
    if (eqs) free(eqs);
    return 1;
  }

  double *ents = calloc((size_t)neq, sizeof(double));
  if (!ents) {
    fprintf(stderr, "memory allocation failure\n");
    for (int i=0;i<neq;i++) free(eqs[i]);
    free(eqs);
    return 1;
  }
  for (int i=0;i<neq;i++) ents[i] = simple_entropy(eqs[i]);

  int ncand = 0;
  char **cands = generate_swapped_candidates(eqs, neq, &ncand);

  write_outputs(".", eqs, neq, cands, ncand);

  for (int i=0;i<neq;i++) free(eqs[i]);
  free(eqs);
  if (cands) {
    for (int j=0;j<ncand;j++) free(cands[j]);
    free(cands);
  }
  free(ents);

  printf("Analysis written to ./output (equations.txt, paper.tex)\n");
  return 0;
}
```

手順：
1. パッケージ内の `usr/lang/omegascript.c` を上のファイルで置き換える（または pkginstallgen.c の埋め込み文字列を差し替えて再生成）。
2. cd <package dir>
3. make
4. ./bin/omegascript analyze reports ./output

もしこれでも core dump が発生する場合は、次を教えてください（最低限必要）：
- 実行時のコマンドライン（正確な引数）
- gdb のバックトレース（`gdb --args ./bin/omegascript analyze reports ./output` ⇒ run ⇒ backtrace）
- coreファイルがあるならその path と ulimit 情報

これらの情報があれば、どの関数で落ちているかを特定してさらに修正します。
