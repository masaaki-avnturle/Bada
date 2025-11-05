  // fictional_molecule_demo.c
  // Educational demo: generate fictional molecules and compute mock "spectra" and "zeta-like" scores.
  // Safe: uses artificial alphabet and toy math only.

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

  typedef struct {
  char *id;
  char *formula; // fictional string like "A-B-C"
  int length;
  double topo_index;
  double zeta_score_re;
  double zeta_score_im;
} FictionMol;

/* RNG helper */
static unsigned long rng_state=1;
static void rng_seed(unsigned long s){ rng_state = s ? s : 1; }
static double rng_double(){ rng_state = rng_state * 1664525 + 1013904223u; return (double)(rng_state & 0xFFFFFFFFu) / 4294967296.0; }

/* Generate fictional molecule string using letters A..G, with optional connectors '-' */
static char *gen_fictional_string(int len){
  const char letters[] = "ABCDEFG";
  int L = len>0?len:6;
  char *s = malloc(L*2 + 4);
  int p=0;
  for(int i=0;i<L;i++){
    s[p++] = letters[(int)(rng_double() * 7.0) % 7];
    if(i < L-1 && rng_double() > 0.3) s[p++] = '-';
  }
  s[p] = '\0';
  return s;
}

/* Toy topology index: count distinct letters weighted by adjacency */
static double compute_topo(const char *f){
  int seen[7] = {0};
  const char letters[] = "ABCDEFG";
  double score = 0.0;
  for(size_t i=0;i<strlen(f);i++){
    char c = f[i];
    for(int j=0;j<7;j++) if(c==letters[j]) { seen[j]=1; break; }
  }
  int distinct=0;
  for(int j=0;j<7;j++) if(seen[j]) distinct++;
  // adjacency bonus (count "pairs" ignoring '-')
  int pairs = 0;
  char prev = 0;
  for(size_t i=0;i<strlen(f);i++){
    char c = f[i];
    if(c=='-') continue;
    if(prev!=0){ if(prev!=c) pairs++; }
    prev = c;
  }
  score = distinct + pairs*0.5;
  return score;
}

/* Simple in-place FFT (radix-2 Cooley-Tukey). input: arrays re[], im[], n power of two */
static void fft(double *re, double *im, int n){
  // bit-reverse
  for(int i=1,j=0;i<n;i++){
    int bit = n>>1;
    for(; j & bit; bit >>=1) j ^= bit;
    j ^= bit;
    if(i<j){
      double tr=re[i], ti=im[i];
      re[i]=re[j]; im[i]=im[j];
      re[j]=tr; im[j]=ti;
    }
  }
  for(int len=2; len<=n; len<<=1){
    double ang = -2.0*M_PI/len;
    double wlen_re = cos(ang), wlen_im = sin(ang);
    for(int i=0;i<n;i+=len){
      double wr=1.0, wi=0.0;
      for(int j=0;j<len/2;j++){
	int u = i+j;
	int v = i+j+len/2;
	double xr = re[v]*wr - im[v]*wi;
	double xi = re[v]*wi + im[v]*wr;
	re[v] = re[u] - xr; im[v] = im[u] - xi;
	re[u] = re[u] + xr; im[u] = im[u] + xi;
	double nxt_wr = wr*wlen_re - wi*wlen_im;
	double nxt_wi = wr*wlen_im + wi*wlen_re;
	wr = nxt_wr; wi = nxt_wi;
      }
    }
  }
}

/* Produce toy time-series from molecule string: combine letter codes into amplitudes */
static int produce_timeseries(const char *f, int win, double dt, double **out_t, double **out_sig){
  int N = 1;
  while(N < win) N <<= 1;
  double *t = malloc(sizeof(double)*N);
  double *sig = malloc(sizeof(double)*N);
  // map letters to base frequencies
  for(int i=0;i<N;i++){
    t[i] = i * dt;
    // build pseudo-signal: sum of sinusoids determined by letters and some randomness
    double s = 0.0;
    int idx=0;
    for(size_t j=0;j<strlen(f);j++){
      char c = f[j];
      if(c=='-') continue;
      int code = (int)(c - 'A') + 1; // 1..7
      double freq = 0.5 + 0.3*code + 0.1*idx; // arbitrary
      s += (0.2 + 0.1*code) * sin(2*M_PI*freq*t[i] + rng_double()*2*M_PI);
      idx++;
    }
    // add low-amplitude noise
    s += 0.05 * (rng_double()*2.0 - 1.0);
    sig[i] = s;
  }
  *out_t = t; *out_sig = sig; return N;
}

/* Compute power spectrum and evaluate toy zeta-like sum: sum_k P_k * f_k^{-s} where s = sigma + i*tau
   (here we compute a complex accumulator using exp(-s*ln f) weighting).
   Returns re,im via pointers.
*/
static void compute_zeta_like(double *sig, int N, double dt, double sigma, double tau, double *out_re, double *out_im){
  double *re = malloc(sizeof(double)*N);
  double *im = malloc(sizeof(double)*N);
  for(int i=0;i<N;i++){ re[i]=sig[i]; im[i]=0.0; }
  fft(re,im,N);
  int L = N/2;
  double acc_re=0.0, acc_im=0.0;
  for(int k=1;k<L;k++){
    double freq = (double)k / (dt * N);
    if(freq <= 0) continue;
    double P = re[k]*re[k] + im[k]*im[k];
    double ln = log(freq);
    double a = -sigma * ln;
    double b = -tau * ln;
    double weight = exp(a);
    acc_re += P * weight * cos(b);
    acc_im += P * weight * sin(b);
  }
  free(re); free(im);
  *out_re = acc_re; *out_im = acc_im;
}

/* Main demo: generate n fictional molecules and analyze */
int main(int argc, char **argv){
  int n = 3;
  int len = 6;
  unsigned long seed = (unsigned long)time(NULL);
  double sigma = 1.0, tau = 0.5;
  for(int i=1;i<argc;i++){
    if(strcmp(argv[i],"-n")==0 && i+1<argc) n = atoi(argv[++i]);
    else if(strcmp(argv[i],"-l")==0 && i+1<argc) len = atoi(argv[++i]);
    else if(strcmp(argv[i],"-s")==0 && i+1<argc) seed = (unsigned long)atoi(argv[++i]);
    else if(strcmp(argv[i],"-sr")==0 && i+1<argc) sigma = atof(argv[++i]);
    else if(strcmp(argv[i],"-si")==0 && i+1<argc) tau = atof(argv[++i]);
  }
  rng_seed(seed);
  printf("# Fictional molecule demo (seed=%lu)\n", seed);
  for(int i=0;i<n;i++){
    FictionMol m = {0};
    char idbuf[64]; snprintf(idbuf,sizeof(idbuf),"mol_%02d", i+1);
    m.id = strdup(idbuf);
    m.formula = gen_fictional_string(len);
    m.length = (int)strlen(m.formula);
    m.topo_index = compute_topo(m.formula);
    // produce timeseries and compute zeta-like score
    double *t=NULL,*sig=NULL;
    int N = produce_timeseries(m.formula, 1024, 0.01, &t,&sig);
    compute_zeta_like(sig,N,0.01,sigma,tau,&m.zeta_score_re,&m.zeta_score_im);
    // output summary
    printf("ID: %s\n  formula: %s\n  topo_index: %.3f\n  zeta_re: %.6g zeta_im: %.6g\n",
	   m.id, m.formula, m.topo_index, m.zeta_score_re, m.zeta_score_im);
    free(m.id); free(m.formula); free(t); free(sig);
  }
  return 0;
}
