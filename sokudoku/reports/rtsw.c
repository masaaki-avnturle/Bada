# aspe_zeta.omega
# Omega Script (OmegaScript-JP) — ASPE シミュレータ連携とゼータ解析ワークフロー
# 前提: aspe_sim バイナリ と zeta_analysis バイナリ を同一ディレクトリに置く

# 入力データ（時間系列の原子座標ファイル、CSV: t,atom_idx,x,y,z）
SET KEY coord_file = "data/flunitrazepam_coords.csv"
SET KEY outdir = "results/zeta"
SET KEY n_qubits = 5           # ASPE シミュレータの使用（必要なら）
SET KEY trials = 1024
SET KEY noise = 0.01
SET KEY theta = 1.0

# zeta パラメータ
SET KEY s_real = 1.0
SET KEY s_imag = 0.5
SET KEY freq_min = 0.1
SET KEY freq_max = 2000.0
SET KEY fft_window = 1024

# 実行手順
  READ ${coord_file}
# 1) (任意) ASPE シミュレータで原子運動を模擬する場合（ここでは既存データを使うのでスキップ可能）
# RUN_SIM: aspe_sim -n ${n_qubits} -t ${theta} -p ${noise} -r ${trials} -o "${outdir}/aspe_sim_out.txt"

# 2) zeta 解析呼び出し（時間系列 -> 周波数スペクトル -> ゼータ関数評価）
# zeta_analysis は coord_file を読み、各原子についてスペクトルを作成し、s = s_real + i s_imag に対して
# ζ_atom(s) = Σ_k P_k * f_k^{-s} を計算。出力: ${outdir}/zeta_summary.txt と個別ファイル。
LLM DISABLE
CALL ZETA_ANALYSIS INPUT "${coord_file}" \
    OUTDIR "${outdir}" \
S_REAL ${s_real} S_IMAG ${s_imag} \
FMIN ${freq_min} FMAX ${freq_max} \
FFT_WIN ${fft_window}

EXPORT ASTS TO "${outdir}/meta_asts.txt"
RUN
```

ファイル2: zeta_analysis.c
（コンパイル: gcc -O2 -std=c11 -o zeta_analysis zeta_analysis.c -lm）
```c
// zeta_analysis.c
// 入力: CSV (t,atom_idx,x,y,z) 時系列座標
// 出力: 周波数パワースペクトル -> ゼータ関数 ζ(s) = sum_k P_k * f_k^{-s} を原子ごとに評価
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* シンプル FFT (Cooley-Tukey) 実装（実数信号用の複素配列FFTを使う） */
typedef struct { double re, im; } cplx;
static cplx cadd(cplx a,cplx b){return (cplx){a.re+b.re,a.im+b.im};}
static cplx csub(cplx a,cplx b){return (cplx){a.re-b.re,a.im-b.im};}
static cplx cmul(cplx a,cplx b){return (cplx){a.re*b.re - a.im*b.im, a.re*b.im + a.im*b.re};}

static void fft(cplx *x, int n){
  if(n<=1) return;
  int i,j,k,m;
  // bit-reverse permutation
  for(i=1,j=0;i<n;i++){
    int bit = n>>1;
    for(; j & bit; bit >>=1) j ^= bit;
    j ^= bit;
    if(i<j){ cplx t = x[i]; x[i]=x[j]; x[j]=t; }
  }
  for(m=2;m<=n;m <<=1){
    double theta = -2.0*M_PI/m;
    cplx wm = {cos(theta), sin(theta)};
    for(k=0;k<n;k+=m){
      cplx w = {1.0,0.0};
      for(int s=0;s<m/2;s++){
	cplx t = cmul(w, x[k+s+m/2]);
	cplx u = x[k+s];
	x[k+s] = cadd(u,t);
	x[k+s+m/2] = csub(u,t);
	w = cmul(w, wm);
      }
    }
  }
}

/* ユーティリティ: next pow2 */
static int next_pow2(int v){ int p=1; while(p<v) p<<=1; return p; }

/* 入出力パース: CSV -> 原子ごとの時刻順配列 */
typedef struct {
  int atom_id;
  int n;
  double *t;
  double *x;
  double *y;
  double *z;
} AtomSeries;

typedef struct {
  AtomSeries *atoms;
  int natoms;
} Dataset;

/* 単純パーサ: ファイルスキャンして atom_id の最大を見つけ、各原子に配列を作る（メモリ2パス） */
static Dataset *load_coords(const char *path){
  FILE *f = fopen(path,"r"); if(!f){ perror("open coord"); return NULL; }
  int maxid=-1;
  double t,x,y,z; int id;
  char line[512];
  // skip header if present: detect non-numeric start
  long pos;
  while(fgets(line,sizeof(line),f)){
    char *s=line;
    while(*s==' '||*s=='\t') s++;
    if(*s=='#' || *s=='\0') continue;
    // try parse
    if(sscanf(line,"%lf,%d,%lf,%lf,%lf",&t,&id,&x,&y,&z)==5){
      if(id>maxid) maxid=id;
      break;
    } else {
      // maybe header; continue
      continue;
    }
  }
  if(maxid<0){ fclose(f); return NULL; }
  // rewind and count per id
  rewind(f);
  int nids = maxid+1;
  int *counts = calloc(nids,sizeof(int));
  while(fgets(line,sizeof(line),f)){
    if(sscanf(line,"%lf,%d,%lf,%lf,%lf",&t,&id,&x,&y,&z)==5){
      if(id>=0 && id<nids) counts[id]++;
    }
  }
  // allocate Dataset
  Dataset *ds = calloc(1,sizeof(Dataset));
  ds->natoms = nids;
  ds->atoms = calloc(nids,sizeof(AtomSeries));
  for(int i=0;i<nids;i++){
    ds->atoms[i].atom_id = i;
    ds->atoms[i].n = counts[i];
    if(counts[i]>0){
      ds->atoms[i].t = malloc(sizeof(double)*counts[i]);
      ds->atoms[i].x = malloc(sizeof(double)*counts[i]);
      ds->atoms[i].y = malloc(sizeof(double)*counts[i]);
      ds->atoms[i].z = malloc(sizeof(double)*counts[i]);
    }
  }
  // fill
  int *posidx = calloc(nids,sizeof(int));
  rewind(f);
  while(fgets(line,sizeof(line),f)){
    if(sscanf(line,"%lf,%d,%lf,%lf,%lf",&t,&id,&x,&y,&z)==5){
      if(id>=0 && id<nids){
	int p = posidx[id]++;
	ds->atoms[id].t[p]=t;
	ds->atoms[id].x[p]=x;
	ds->atoms[id].y[p]=y;
	ds->atoms[id].z[p]=z;
      }
    }
  }
  free(posidx); free(counts);
  fclose(f);
  return ds;
}

static void free_dataset(Dataset *ds){
  if(!ds) return;
  for(int i=0;i<ds->natoms;i++){
    free(ds->atoms[i].t);
    free(ds->atoms[i].x);
    free(ds->atoms[i].y);
    free(ds->atoms[i].z);
  }
  free(ds->atoms);
  free(ds);
}

/* 単純パワースペクトル算出（x座標を用いる。窓長 = win; 出力: freqs[] length win/2, power[]） */
static void compute_power_spectrum(const double *signal, int n, int win, double fs, double **out_freq, double **out_power, int *out_len){
  int N = next_pow2(win);
  cplx *buf = calloc(N,sizeof(cplx));
  for(int i=0;i<win && i<n;i++) buf[i].re = signal[i];
  for(int i=win;i<N;i++) buf[i].re = 0.0;
  fft(buf, N);
  int L = N/2;
  double *freq = malloc(sizeof(double)*L);
  double *power = malloc(sizeof(double)*L);
  for(int k=0;k<L;k++){
    freq[k] = (double)k * fs / (double)N;
    power[k] = buf[k].re*buf[k].re + buf[k].im*buf[k].im;
  }
  free(buf);
  *out_freq = freq; *out_power = power; *out_len = L;
}

/* ゼータ評価: s = sigma + i t, ζ = Σ_k P_k * f_k^{-s} (ここで f_k>0). 実装: f^{-s} = exp(-s * log f) */
static double complex eval_zeta_complex(const double *freq, const double *power, int L, double sigma, double t_im, double *out_abs){
  double re=0.0, im=0.0;
  for(int k=1;k<L;k++){ // k=0 は DC, skip
    double f = freq[k];
    if(!(f>0)) continue;
    double pk = power[k];
    double ln = log(f);
    double a = -sigma * ln;
    double b = -t_im * ln;
    double cosb = cos(b), sinb = sin(b);
    double real_term = pk * exp(a) * cosb;
    double imag_term = pk * exp(a) * sinb;
    re += real_term; im += imag_term;
  }
  if(out_abs) *out_abs = sqrt(re*re + im*im);
  return re + I*im;
}

int main(int argc, char **argv){
  if(argc<2){
    fprintf(stderr,"Usage: %s -i coords.csv -o outdir -sr sigma -si t_im -fmin fmin -fmax fmax -w fftwin\n", argv[0]);
    return 1;
  }
  const char *inpath=NULL; const char *outdir="results"; double sigma=1.0, t_im=0.0;
  double fmin=0.1,fmax=2000.0; int fftwin=1024;
  for(int i=1;i<argc;i++){
    if(strcmp(argv[i],"-i")==0 && i+1<argc) inpath=argv[++i];
    else if(strcmp(argv[i],"-o")==0 && i+1<argc) outdir=argv[++i];
    else if(strcmp(argv[i],"-sr")==0 && i+1<argc) sigma = atof(argv[++i]);
    else if(strcmp(argv[i],"-si")==0 && i+1<argc) t_im = atof(argv[++i]);
    else if(strcmp(argv[i],"-fmin")==0 && i+1<argc) fmin = atof(argv[++i]);
    else if(strcmp(argv[i],"-fmax")==0 && i+1<argc) fmax = atof(argv[++i]);
    else if(strcmp(argv[i],"-w")==0 && i+1<argc) fftwin = atoi(argv[++i]);
  }
  if(!inpath){ fprintf(stderr,"no input\n"); return 1; }
  Dataset *ds = load_coords(inpath);
  if(!ds){ fprintf(stderr,"failed load\n"); return 1; }
  mkdir(outdir,0755);
  char summary[1024];
  snprintf(summary,sizeof(summary),"%s/zeta_summary.txt", outdir);
  FILE *fsum = fopen(summary,"w");
  if(!fsum) { perror("open summary"); free_dataset(ds); return 1; }
  fprintf(fsum,"# zeta summary sigma=%g t=%g fftwin=%d\n", sigma, t_im, fftwin);

  for(int a=0;a<ds->natoms;a++){
    AtomSeries *as = &ds->atoms[a];
    if(as->n < 8) continue;
    // assume uniform sampling: estimate fs from t[1]-t[0]
    double dt = as->t[1] - as->t[0];
    if(dt <= 0) dt = 1.0;
    double fsamp = 1.0 / dt;
    double *signal = malloc(sizeof(double)*as->n);
    for(int i=0;i<as->n;i++) signal[i] = as->x[i]; // use x component; could use magnitude
    double *freq = NULL, *power = NULL; int L=0;
    compute_power_spectrum(signal, as->n, fftwin, fsamp, &freq, &power, &L);
    // write per-atom spectrum
    char fout[512];
    snprintf(fout,sizeof(fout),"%s/atom_%d_spectrum.txt", outdir, as->atom_id);
    FILE *fo = fopen(fout,"w");
    if(fo){
      fprintf(fo,"# freq power\n");
      for(int k=0;k<L;k++){
	if(freq[k] < fmin || freq[k] > fmax) continue;
	fprintf(fo,"%g %g\n", freq[k], power[k]);
      }
      fclose(fo);
    }
    double absval=0.0;
    double complex z = eval_zeta_complex(freq,power,L,sigma,t_im,&absval);
    fprintf(fsum,"atom %d sigma %g t %g z_re %g z_im %g abs %g\n", as->atom_id, sigma, t_im, creal(z), cimag(z), absval);
    free(freq); free(power); free(signal);
  }
  fclose(fsum);
  free_dataset(ds);
  return 0;
}
