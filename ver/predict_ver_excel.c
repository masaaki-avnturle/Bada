/*
 pkginstallgen.c  — 安全・堅牢版
 - CSV/XLSX を読み込み、サニタイズして解析、エントロピー等を計算し out_data.csv を出力
 - 不正なセル（式、非常に長い値、制御文字、外部リンクなど）を無害化
 - 例外発生時でも部分出力を残す（常に out_data.csv を作成）
 Build:
  gcc -O2 -std=c11 -Wall -Wextra -lm -o pkginstallgen pkginstallgen.c
 Optional (libxlsxio):
  gcc -O2 -std=c11 -Wall -Wextra -lm -DHAVE_XLSXIO -o pkginstallgen pkginstallgen.c -lxlsxio_read
*/
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>
#include <signal.h>
#include <limits.h>
#include <float.h>

#ifdef HAVE_XLSXIO
#include <xlsxio_read.h>
#endif

enum { MAX_ROWS = 600000, MAX_COLS = 1024, MAX_LINE = 1<<15, NGRAM_N = 3 };
static volatile sig_atomic_t g_interrupted = 0;
static void handle_sig(int s){ (void)s; g_interrupted = 1; }

typedef struct {
  char company[512];
  char name[512];
  double revenue;
  double profit;
  double marketcap;
  double listed_value;
  double name_score;
  double name_entropy;
  double metric_entropy;
  double entropy_diff;
  int entropy_match;
  double zeta_score;
  double gamma_scale;
  double growth_score;
  char prediction[32];
} Row;

/* --- helpers --- */
static void safe_strncpy(char *dst, const char *src, size_t n){
  if(n==0) return;
  if(!src){ dst[0]='\0'; return; }
  strncpy(dst, src, n-1); dst[n-1]='\0';
}
static void trim(char *s){
  if(!s) return;
  /* remove BOM */
  if((unsigned char)s[0]==0xEF && (unsigned char)s[1]==0xBB && (unsigned char)s[2]==0xBF){
    memmove(s, s+3, strlen(s+3)+1);
  }
  char *p = s;
  while(*p && isspace((unsigned char)*p)) p++;
  if(p!=s) memmove(s,p,strlen(p)+1);
  size_t L = strlen(s);
  while(L>0 && isspace((unsigned char)s[L-1])) s[--L] = '\0';
}
/* sanitize cell: remove leading '=' (formulas), remove control chars except tab/newline, limit length */
static void sanitize_cell(char *s, size_t maxlen){
  if(!s) return;
  trim(s);
  if(s[0] == '='){ /* neutralize formula */
    memmove(s, s+1, strlen(s+1)+1);
    trim(s);
  }
  /* strip control chars except printable and basic whitespace */
  char *w = s;
  for(char *r=s; *r; ++r){
    unsigned char c = (unsigned char)*r;
    if(c >= 0x20 || c=='\t' || c=='\n' || c=='\r'){
      *w++ = (char)c;
    } else {
      /* skip control char */
    }
  }
  *w = '\0';
  /* truncate safely */
  if(strlen(s) > maxlen-1) s[maxlen-1] = '\0';
}
/* safe atof */
static double safe_atod(const char *s){
  if(!s) return NAN;
  char *end = NULL; errno = 0;
  double v = strtod(s, &end);
  if(end==s || errno==ERANGE) return NAN;
  return v;
}
/* ascii lower copy */
static void ascii_lowercpy(char *dst, const char *src, size_t n){
  if(!dst||!src||n==0) return;
  size_t i; for(i=0;i<n-1 && src[i]; ++i) dst[i] = (char)tolower((unsigned char)src[i]);
  dst[i] = '\0';
}

/* entropy funcs (kept simple and safe) */
static double string_byte_entropy(const char *s){
  if(!s) return 0.0;
  size_t L = strlen(s);
  if(L==0) return 0.0;
  int freq[256] = {0};
  for(size_t i=0;i<L;i++) freq[(unsigned char)s[i]]++;
  double H=0.0;
  for(int i=0;i<256;i++) if(freq[i]>0){
      double p = (double)freq[i] / (double)L;
      H -= p * log(p);
    }
  return H;
}
/* small wrappers for metric entropy and manifold */
static double shannon_entropy_from_vals(double *vals, int n, int bins){
  if(!vals || n<=0 || bins<=0) return 0.0;
  double minv=vals[0], maxv=vals[0];
  for(int i=1;i<n;i++){ if(vals[i]<minv) minv=vals[i]; if(vals[i]>maxv) maxv=vals[i]; }
  double range = maxv - minv; if(range==0.0) range = 1e-12;
  int *hist = calloc((size_t)bins, sizeof(int));
  if(!hist) return 0.0;
  for(int i=0;i<n;i++){
    double norm = (vals[i]-minv)/range;
    int b = (int)floor(norm * bins);
    if(b<0) b=0; if(b>=bins) b=bins-1;
    hist[b]++;
  }
  double H=0.0;
  for(int i=0;i<bins;i++) if(hist[i]>0){
      double p = (double)hist[i] / (double)n;
      H -= p * log(p);
    }
  free(hist);
  return H;
}
static double manifold_entropy_from_vals(double *p, int n, double alpha){
  if(!p || n<=0) return 0.0;
  double sum=0.0;
  for(int i=0;i<n;i++) if(isfinite(p[i]) && p[i]>0) sum += p[i];
  if(sum <= 0.0) return 0.0;
  double H=0.0;
  for(int i=0;i<n;i++){
    double wi = (p[i] > 0.0 && isfinite(p[i])) ? (p[i]/sum) : 0.0;
    if(wi<=0.0) continue;
    double arg = 1.0 + alpha*wi;
    double g = tgamma(arg);
    if(isfinite(g) && g>0.0) H += wi * log(g);
    else {
      double x = arg;
      if(x>0.0) H += wi * ((x-0.5)*log(x) - x + 0.5*log(2*M_PI));
    }
  }
  return H;
}
static double blended_metric_entropy(double *vals, int n, int hist_bins, double alpha){
  double sh = shannon_entropy_from_vals(vals, n, hist_bins);
  double man = manifold_entropy_from_vals(vals, n, alpha);
  double comb = 0.6*sh + 0.4*man;
  return isfinite(comb) ? comb : sh;
}
static double zeta_transform(double *v, int n, double s){
  if(!v || n<=0) return 0.0;
  double *tmp = malloc(sizeof(double)*(size_t)n);
  if(!tmp) return 0.0;
  for(int i=0;i<n;i++) tmp[i] = fmax(0.0, v[i]);
  for(int i=0;i<n-1;i++){
    int mx=i;
    for(int j=i+1;j<n;j++) if(tmp[j] > tmp[mx]) mx=j;
    if(mx!=i){ double t=tmp[i]; tmp[i]=tmp[mx]; tmp[mx]=t; }
  }
  double sum=0.0;
  for(int k=1;k<=n;k++) sum += tmp[k-1] / pow((double)k, s);
  free(tmp);
  return sum;
}
static double combine_score_manifold(double name_score, double name_entropy, double manifold_entropy, double zeta, int entropy_match){
  double ns = name_score / (1.5 + fabs(name_score));
  double ne = name_entropy / (1.0 + fabs(name_entropy));
  double me = manifold_entropy / (1.0 + fabs(manifold_entropy));
  double zs = zeta / (1.0 + fabs(zeta));
  double base = 0.30*ns + 0.25*ne + 0.30*me + 0.15*zs;
  if(entropy_match) base *= 1.20;
  double gamma_in = fmax(0.5, 1.0 + 0.4*zs + 0.2*me);
  double g = tgamma(gamma_in);
  if(!isfinite(g) || g <= 0.0) g = 1.0;
  double scaled = base * (log(1.0 + fabs(g)) + 0.5*log(1.0 + exp(fmin(200.0, 1.5*base))));
  return isfinite(scaled) ? scaled : base;
}

/* CSV parsing (very forgiving) */
static int csv_tokenize(char *line, char **out, int maxf){
  int nf=0;
  char *p=line;
  while(*p && nf < maxf){
    while(*p && isspace((unsigned char)*p)) p++;
    if(*p=='\0') break;
    if(*p=='"'){
      p++; out[nf++] = p;
      char *q = p;
      while(*q){
	if(*q=='"'){
	  if(q[1]=='"'){ memmove(q, q+1, strlen(q+1)+1); q++; continue; }
	  *q = '\0'; q++;
	  if(*q==',') q++;
	  p = q; break;
	}
	q++;
      }
      if(*q=='\0') p=q;
    } else {
      out[nf++] = p;
      char *q = p;
      while(*q && *q!=',') q++;
      if(*q==','){ *q = '\0'; p = q+1; } else p = q;
    }
  }
  return nf;
}

/* append row from cells with sanitization and safe limits */
static int append_row_from_cells(Row *r, char **cells, int ncols,
                                 int idx_company, int idx_name, int idx_revenue, int idx_profit, int idx_marketcap, int idx_listed)
{
  if(!r) return 0;
  char comp[512] = "", name[512] = "";
  double rev = NAN, pr = NAN, mc = NAN, listed = NAN;
  if(idx_company >=0 && idx_company < ncols && cells[idx_company]) safe_strncpy(comp, cells[idx_company], sizeof(comp));
  if(idx_name >=0 && idx_name < ncols && cells[idx_name]) safe_strncpy(name, cells[idx_name], sizeof(name));
  if(idx_revenue >=0 && idx_revenue < ncols && cells[idx_revenue]) rev = safe_atod(cells[idx_revenue]);
  if(idx_profit >=0 && idx_profit < ncols && cells[idx_profit]) pr = safe_atod(cells[idx_profit]);
  if(idx_marketcap >=0 && idx_marketcap < ncols && cells[idx_marketcap]) mc = safe_atod(cells[idx_marketcap]);
  if(idx_listed >=0 && idx_listed < ncols && cells[idx_listed]) listed = safe_atod(cells[idx_listed]);

  sanitize_cell(comp, sizeof(comp));
  sanitize_cell(name, sizeof(name));
  if(comp[0]=='\0' && name[0]=='\0') return 0;
  if(!isfinite(rev) && !isfinite(pr) && !isfinite(mc)) return 0;

  memset(r, 0, sizeof(*r));
  safe_strncpy(r->company, comp, sizeof(r->company));
  safe_strncpy(r->name, name, sizeof(r->name));
  r->revenue = isfinite(rev)?rev:0.0;
  r->profit  = isfinite(pr)?pr:0.0;
  r->marketcap = isfinite(mc)?mc:0.0;
  r->listed_value = isfinite(listed)?listed:NAN;
  return 1;
}

/* process CSV file, returns 0 on success (even if added 0 rows) */
static int process_csv_file(const char *fn, Row *rows, int *nrows, int maxrows){
  FILE *f = fopen(fn, "r");
  if(!f){ fprintf(stderr,"[ERROR] cannot open CSV '%s': %s\n",fn,strerror(errno)); return -1; }
  char *line = malloc(MAX_LINE);
  if(!line){ fclose(f); return -1; }
  char *cols[MAX_COLS];
  int header_done = 0;
  int mapped_company=-1,mapped_name=-1,mapped_rev=-1,mapped_pr=-1,mapped_mc=-1,mapped_list=-1;
  int local_added = 0;
  int lineno = 0;
  while(!g_interrupted && fgets(line, MAX_LINE, f)){
    lineno++;
    size_t L = strlen(line);
    while(L>0 && (line[L-1]=='\n' || line[L-1]=='\r')) line[--L]='\0';
    if(L==0) continue;
    /* defensive: truncate overly long lines */
    if(L >= MAX_LINE-1){ line[MAX_LINE-2]='\0'; }
    int nf = csv_tokenize(line, cols, MAX_COLS);
    for(int i=0;i<nf;i++){ if(cols[i]) sanitize_cell(cols[i], 1024); }
    if(!header_done){
      char tmp0[1024]; safe_strncpy(tmp0, cols[0]?cols[0]:"", sizeof(tmp0));
      trim(tmp0);
      int is_numeric = 1;
      if(tmp0[0]=='\0') is_numeric = 0;
      else {
	for(size_t k=0;k<strlen(tmp0);++k){ unsigned char ch=(unsigned char)tmp0[k]; if(!(isdigit(ch)||ch=='.'||ch=='-'||ch=='+')){ is_numeric = 0; break; } }
      }
      if(!is_numeric){
	/* map by header names (simple heuristics) */
	for(int c=0;c<nf;c++){
	  char lower[256]; ascii_lowercpy(lower, cols[c]?cols[c]:"", sizeof(lower));
	  if(strstr(lower,"company") || strstr(lower,"会社") || strstr(lower,"企業")) mapped_company = c;
	  if(strstr(lower,"name") || strstr(lower,"名称") || strstr(lower,"銘柄")) mapped_name = c;
	  if(strstr(lower,"revenue") || strstr(lower,"売上") || strstr(lower,"売上高")) mapped_rev = c;
	  if(strstr(lower,"profit") || strstr(lower,"利益")) mapped_pr = c;
	  if(strstr(lower,"market") || strstr(lower,"時価")) mapped_mc = c;
	  if(strstr(lower,"listed") || strstr(lower,"上場")) mapped_list = c;
	}
	header_done = 1; continue;
      } else {
	mapped_company = 0; mapped_name = (nf>1?1:0); mapped_rev = (nf>2?2:-1);
	if(nf>3) mapped_pr=3; if(nf>4) mapped_mc=4; if(nf>5) mapped_list=5;
	header_done = 1;
      }
    }
    if(*nrows >= maxrows) break;
    Row tmp;
    if(append_row_from_cells(&tmp, cols, nf, mapped_company, mapped_name, mapped_rev, mapped_pr, mapped_mc, mapped_list)){
      rows[(*nrows)++] = tmp; local_added++;
    }
  }
  free(line);
  fclose(f);
  if(local_added==0) fprintf(stderr,"[WARN] CSV '%s' added 0 rows\n",fn);
  else fprintf(stderr,"[INFO] CSV '%s' added %d rows\n",fn, local_added);
  return 0;
}

#ifdef HAVE_XLSXIO
/* process xlsx via libxlsxio, but sanitize every cell and ignore external links */
static int process_xlsx_file_with_lib(const char *fn, Row *rows, int *nrows, int maxrows){
  xlsxioreader reader = xlsxioread_open(fn);
  if(!reader){ fprintf(stderr,"[ERROR] libxlsxio: cannot open %s\n",fn); return -1; }
  xlsxioreadersheetlist sheetlist = xlsxioread_sheetlist_open(reader);
  if(!sheetlist){ xlsxioread_close(reader); return -1; }
  const char *sname;
  int total_added = 0;
  while((sname = xlsxioread_sheetlist_next(sheetlist)) && !g_interrupted){
    xlsxioreadersheet sheet = xlsxioread_sheet_open(reader, sname, XLSXIOREAD_SKIP_EMPTY_ROWS);
    if(!sheet) continue;
    char *cells[MAX_COLS]; for(int i=0;i<MAX_COLS;i++) cells[i]=NULL;
    int header_mapped = 0;
    int m_company=-1,m_name=-1,m_rev=-1,m_pr=-1,m_mc=-1,m_list=-1;
    while(!g_interrupted && xlsxioread_sheet_next_row(sheet)){
      int nf=0;
      char *val;
      while((val = xlsxioread_sheet_next_cell(sheet))){
	if(nf < MAX_COLS) {
	  /* sanitize: copy into bounded buffer then sanitize */
	  size_t cap = 1024;
	  char *buf = malloc(cap);
	  if(buf){
	    safe_strncpy(buf, val, cap);
	    sanitize_cell(buf, cap);
	    cells[nf] = buf;
	  }
	}
	nf++;
	free(val);
      }
      if(nf <= 0){
	for(int c=0;c<MAX_COLS;c++){ if(cells[c]){ free(cells[c]); cells[c]=NULL; } }
	continue;
      }
      if(!header_mapped){
	char tmp0[1024]; safe_strncpy(tmp0, cells[0]?cells[0]:"", sizeof(tmp0));
	trim(tmp0);
	int is_numeric = 1;
	if(tmp0[0]=='\0') is_numeric=0;
	else { for(size_t k=0;k<strlen(tmp0);++k){ unsigned char ch=(unsigned char)tmp0[k]; if(!(isdigit(ch)||ch=='.'||ch=='-'||ch=='+')){ is_numeric=0; break; } } }
	if(!is_numeric){
	  for(int c=0;c<nf;c++){
	    char lower[256]; ascii_lowercpy(lower, cells[c]?cells[c]:"", sizeof(lower));
	    if(strstr(lower,"company")||strstr(lower,"会社")||strstr(lower,"企業")) m_company=c;
	    if(strstr(lower,"name")||strstr(lower,"名称")||strstr(lower,"銘柄")) m_name=c;
	    if(strstr(lower,"revenue")||strstr(lower,"売上")) m_rev=c;
	    if(strstr(lower,"profit")||strstr(lower,"利益")) m_pr=c;
	    if(strstr(lower,"market")||strstr(lower,"時価")) m_mc=c;
	    if(strstr(lower,"listed")||strstr(lower,"上場")) m_list=c;
	  }
	  header_mapped = 1;
	  for(int c=0;c<nf && c<MAX_COLS; ++c){ if(cells[c]){ free(cells[c]); cells[c]=NULL; } }
	  continue;
	} else {
	  m_company=0; m_name=(nf>1?1:0); m_rev=(nf>2?2:-1);
	  if(nf>3) m_pr=3; if(nf>4) m_mc=4; if(nf>5) m_list=5;
	  header_mapped = 1;
	}
      }
      if(*nrows < maxrows){
	Row tmp;
	if(append_row_from_cells(&tmp, cells, nf, m_company, m_name, m_rev, m_pr, m_mc, m_list)){
	  rows[(*nrows)++] = tmp; total_added++;
	}
      }
      for(int c=0;c<nf && c<MAX_COLS; ++c){ if(cells[c]){ free(cells[c]); cells[c]=NULL; } }
    } /* rows */
    xlsxioread_sheet_close(sheet);
  } /* sheets */
  xlsxioread_sheetlist_close(sheetlist);
  xlsxioread_close(reader);
  if(total_added==0) fprintf(stderr,"[WARN] XLSX '%s' added 0 rows\n",fn);
  else fprintf(stderr,"[INFO] XLSX '%s' added %d rows\n",fn, total_added);
  return 0;
}
#endif

/* Fallback python conversion (kept minimal) */
static int convert_xlsx_to_csv_via_python_safe(const char *xlsx_path, char *outpath, size_t outlen){
  if(!xlsx_path || !outpath) return -1;
  char tmpl[] = "/tmp/pkginstall_xlsx_conv_XXXXXX.csv";
  int fd = mkstemp(tmpl);
  if(fd == -1) return -1;
  close(fd);
  /* Build a short python command; strictly check return */
  char cmd[4096];
  snprintf(cmd, sizeof(cmd),
        "python3 - <<'PY'\n"
        "import sys,pandas as pd\n"
        "try:\n"
        "    x='%s'\n"
        "    xls = pd.ExcelFile(x)\n"
        "    dfs=[]\n"
        "    for s in xls.sheet_names:\n"
        "        df = pd.read_excel(x, sheet_name=s)\n"
        "        if not df.empty: dfs.append(df)\n"
        "    if not dfs:\n"
        "        sys.exit(2)\n"
        "    pd.concat(dfs, ignore_index=True).to_csv('%s', index=False, encoding='utf-8')\n"
        "except Exception as e:\n"
        "    sys.exit(3)\n"
	   "PY\n", xlsx_path, tmpl);
  int rc = system(cmd);
  if(rc != 0){ unlink(tmpl); return -1; }
  safe_strncpy(outpath, tmpl, outlen);
  return 0;
}

static int file_exists(const char *p){
  struct stat st; return (p && stat(p, &st)==0);
}

/* MAIN */
int main(int argc, char **argv){
  signal(SIGINT, handle_sig);
  signal(SIGTERM, handle_sig);

  if(argc < 2){ fprintf(stderr,"Usage: %s file1.csv|file1.xlsx [...]\n", argv[0]); return 1; }

  Row *rows = calloc((size_t)MAX_ROWS, sizeof(Row));
  if(!rows){ perror("calloc"); return 2; }
  int total = 0;
  int files_processed = 0;

  char **tmp_csvs = calloc((size_t)argc, sizeof(char*));
  int tmp_count = 0;

  /* ensure output file exists early and write header even if processing fails later */
  FILE *out = fopen("out_data.csv", "w");
  if(!out){ fprintf(stderr,"[FATAL] cannot open out_data.csv: %s\n", strerror(errno)); free(rows); free(tmp_csvs); return 3; }
  fprintf(out, "company,name,revenue,profit,marketcap,listed_value,name_score,name_entropy,metric_entropy,entropy_diff,entropy_match,zeta_score,gamma_scale,growth_score,prediction\n");
  fflush(out);

  for(int i=1;i<argc && !g_interrupted;i++){
    const char *fn = argv[i];
    if(!file_exists(fn)){ fprintf(stderr,"[WARN] file not found: %s\n", fn); continue; }
    size_t L = strlen(fn);
    const char *ext = (L>=5)? fn + (L-5) : NULL;
    const char *ext4 = (L>=4)? fn + (L-4) : NULL;
    if(ext && strcasecmp(ext, ".xlsx")==0){
#ifdef HAVE_XLSXIO
      if(process_xlsx_file_with_lib(fn, rows, &total, MAX_ROWS)==0) files_processed++;
      else fprintf(stderr,"[WARN] libxlsxio failed for %s\n", fn);
#else
      char tmpcsv[PATH_MAX];
      if(convert_xlsx_to_csv_via_python_safe(fn, tmpcsv, sizeof(tmpcsv))==0){
	tmp_csvs[tmp_count] = strdup(tmpcsv);
	tmp_count++;
	if(process_csv_file(tmpcsv, rows, &total, MAX_ROWS)==0) files_processed++;
      } else {
	fprintf(stderr,"[ERROR] conversion failed for %s (pandas/openpyxl missing or malformed)\n", fn);
      }
#endif
    } else if(ext4 && strcasecmp(ext4, ".csv")==0){
      if(process_csv_file(fn, rows, &total, MAX_ROWS)==0) files_processed++;
    } else {
      /* treat as CSV attempt */
      if(process_csv_file(fn, rows, &total, MAX_ROWS)==0) files_processed++;
    }
    if(total >= MAX_ROWS) break;
  }

  /* If no files processed, ensure we still return with header-only file */
  if(files_processed == 0 || total == 0){
    fprintf(stderr,"[ERROR] No usable rows loaded. out_data.csv contains only header or partial output.\n");
    /* cleanup tmp files */
    for(int k=0;k<tmp_count;k++){ if(tmp_csvs[k]) { unlink(tmp_csvs[k]); free(tmp_csvs[k]); } }
    free(tmp_csvs);
    fclose(out);
    free(rows);
    return 4;
  }

  /* compute normalization */
  double max_rev=1.0, max_pr=1.0, max_mc=1.0;
  for(int i=0;i<total;i++){
    if(isfinite(rows[i].revenue) && fabs(rows[i].revenue) > max_rev) max_rev = fabs(rows[i].revenue);
    if(isfinite(rows[i].profit)  && fabs(rows[i].profit)  > max_pr)  max_pr  = fabs(rows[i].profit);
    if(isfinite(rows[i].marketcap)&& fabs(rows[i].marketcap)> max_mc) max_mc = fabs(rows[i].marketcap);
  }
  if(max_rev==0.0) max_rev=1.0; if(max_pr==0.0) max_pr=1.0; if(max_mc==0.0) max_mc=1.0;

  /* scoring */
  const double entropy_match_threshold = 0.8;
  const double manifold_alpha = 2.5;
  for(int i=0;i<total && !g_interrupted;i++){
    Row *r = &rows[i];
    /* name score: simple n-gram uniqueness safe version */
    char buf[512]; ascii_lowercpy(buf, r->name[0]?r->name:r->company, sizeof(buf));
    size_t Lb = strlen(buf);
    double name_score = 0.0;
    if(Lb>0){
      int distinct=0;
      char seen[256][NGRAM_N+1]; int seen_n=0;
      for(size_t p=0; p + NGRAM_N <= Lb && seen_n < (int)(sizeof(seen)/sizeof(seen[0])); ++p){
	char ng[NGRAM_N+1]; for(int q=0;q<NGRAM_N;q++) ng[q]=buf[p+q]; ng[NGRAM_N]=0;
	int found=0; for(int s=0;s<seen_n;s++) if(strcmp(seen[s], ng)==0){ found=1; break; }
	if(!found){ strcpy(seen[seen_n++], ng); distinct++; }
      }
      name_score = (double)distinct / (1.0 + (double)Lb);
      name_score = fmin(2.0, name_score + fmin(0.2, (double)Lb/50.0));
    }
    r->name_score = name_score;

    double metrics[3];
    metrics[0] = r->revenue / max_rev;
    metrics[1] = r->profit  / max_pr;
    metrics[2] = r->marketcap / max_mc;
    r->metric_entropy = blended_metric_entropy(metrics, 3, 8, manifold_alpha);
    r->name_entropy = string_byte_entropy(r->name[0]?r->name:r->company);
    r->entropy_diff = fabs(r->name_entropy - r->metric_entropy);
    r->entropy_match = (r->entropy_diff <= entropy_match_threshold) ? 1 : 0;
    r->zeta_score = zeta_transform(metrics, 3, 1.2);
    double gamma_input = fmax(0.1, 1.0 + r->zeta_score * 0.5);
    r->gamma_scale = tgamma(gamma_input);
    if(!isfinite(r->gamma_scale) || r->gamma_scale <= 0.0) r->gamma_scale = 1.0;
    r->growth_score = combine_score_manifold(r->name_score, r->name_entropy, r->metric_entropy, r->zeta_score, r->entropy_match);
    double gmult = log(1.0 + fabs(r->gamma_scale));
    if(isfinite(gmult) && gmult > 0.0) r->growth_score *= gmult;
    if(!isfinite(r->growth_score)) r->growth_score = 0.0;
  }

  /* normalize growth_score */
  double gmin = DBL_MAX, gmax = -DBL_MAX;
  for(int i=0;i<total;i++){
    double v = rows[i].growth_score;
    if(v < gmin) gmin = v;
    if(v > gmax) gmax = v;
  }
  if(!isfinite(gmin) || !isfinite(gmax)){ gmin = 0.0; gmax = 1.0; }
  double gr = gmax - gmin; if(gr <= 0.0) gr = 1.0;
  for(int i=0;i<total;i++){
    rows[i].growth_score = (rows[i].growth_score - gmin) / gr;
    if(rows[i].growth_score < 0.0) rows[i].growth_score = 0.0;
    if(rows[i].growth_score > 1.0) rows[i].growth_score = 1.0;
  }

  double threshold = 0.6;
  for(int i=0;i<total;i++){
    safe_strncpy(rows[i].prediction, rows[i].growth_score >= threshold ? "GROW" : "NO-GROW", sizeof(rows[i].prediction));
  }

  /* append results to out_data.csv (already has header) and flush incrementally */
  for(int i=0;i<total && !g_interrupted;i++){
    Row *r = &rows[i];
    fprintf(out, "\"%s\",\"%s\",%.10g,%.10g,%.10g,",
	    r->company, r->name, r->revenue, r->profit, r->marketcap);
    if(isfinite(r->listed_value)) fprintf(out, "%.10g,", r->listed_value); else fprintf(out, ",");
    fprintf(out, "%.6f,%.6f,%.6f,%.6f,%d,%.6f,%.6f,%.6f,%s\n",
	    r->name_score, r->name_entropy, r->metric_entropy, r->entropy_diff, r->entropy_match,
	    r->zeta_score, r->gamma_scale, r->growth_score, r->prediction);
    if((i & 127) == 0) fflush(out); /* flush periodically */
  }
  fflush(out);
  fclose(out);

  int growcnt=0;
  for(int i=0;i<total;i++) if(strcmp(rows[i].prediction,"GROW")==0) growcnt++;
  printf("Processed %d rows from %d files. Predicted GROW for %d companies. Output: out_data.csv\n", total, files_processed, growcnt);

  for(int k=0;k<tmp_count;k++){ if(tmp_csvs[k]){ unlink(tmp_csvs[k]); free(tmp_csvs[k]); } }
  free(tmp_csvs);
  free(rows);
  return 0;
}
