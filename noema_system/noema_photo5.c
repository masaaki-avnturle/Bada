/*以下は、関数名の競合（誤記 "resolve_if_indent" 等）を修正した完全な単一ファイル C ソースコードです。関数名は一貫して `resolve_if_ident` を使用し、宣言を適切に行っています。コンパイル方法と簡単なデモも末尾に含みます。

ビルド:
gcc -std=c11 -O2 -Wall -o noema_oop noema_oop.c -pthread -lm

  ソースコード:

```c
*/
  /*
noema_oop.c
Single-file interpreter / simple compiler with:
 - semi-static type declarations: "math x <- expr", "array x <- [ ... ]", "hash x <- { ... }"
 - arithmetic + - * / with precedence, unary +/-
 - parentheses grouping: (expr) parsed first so (a + b)/2 works
 - array/hash literals, indexing: arr[0], hash["k"]
 - native math functions: sin, cos, tan, exp, log, pow, add
 - reviser, regex, manifold, simple GC-like tracked allocations
 - class & method support:
     class C
       def add(a,b)
         math x <- a + b;
         x
       end
     end
     c <- C.new();
     c.add(2,3);  # => 5
 - CLI:
     ./noema_oop interpret inputfile
     ./noema_oop -c inputfile outputfile
Build:
 gcc -std=c11 -O2 -Wall -o noema_oop noema_oop.c -pthread -lm
  */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <regex.h>
#include <math.h>
#include <time.h>
#include <pthread.h>
#include <unistd.h>
#include <termios.h>
#include <sys/ioctl.h>
#include <errno.h>
#include <curl/curl.h>

static char *extract_block_between_positions(src,start);
static void cleanup_all(void);
  /* ---------- Value model ---------- */
  typedef struct Value Value;
typedef struct List List;
typedef struct Hash Hash;
typedef Value* (*NativeFn)(int argc, Value **argv);

typedef enum { T_NULL, T_NUMBER, T_STRING, T_LIST, T_HASH, T_FUNC, T_REVISER, T_REGEX, T_MANIFOLD, T_GC } ValType;

struct List { int len, cap; Value **items; };

typedef struct HashEntry { char *key; Value *val; struct HashEntry *next; } HashEntry;
struct Hash { int buckets; HashEntry **table; };

struct Value {
  ValType type;
  union {
    double num;
    char *str;
    List *list;
    Hash *hash;
    struct { NativeFn fn; int arity; } func;
    struct { List *rules; } reviser;
    struct { regex_t rex; char *pattern; int valid; } regex;
    struct { int nx, ny; double *grid; } manifold;
    struct { List *tracked; pthread_mutex_t lock; } gc;
  } v;
};

/* ---------- Allocation tracking ---------- */
static List *global_allocs = NULL;
static pthread_mutex_t global_allocs_lock = PTHREAD_MUTEX_INITIALIZER;
static void *xmalloc(size_t n){ void *p = malloc(n); if(!p){ fprintf(stderr,"out of memory\n"); exit(1);} return p; }
static char *xstrdup(const char *s){ return strdup(s?s:""); }
static void track_alloc(Value *v){
  if(!v) return;
  pthread_mutex_lock(&global_allocs_lock);
  if(!global_allocs){
    global_allocs = xmalloc(sizeof(List));
    global_allocs->len = 0;
    global_allocs->cap = 32;
    global_allocs->items = xmalloc(sizeof(Value*) * global_allocs->cap);
  }
  if(global_allocs->len == global_allocs->cap){
    global_allocs->cap *= 2;
    global_allocs->items = realloc(global_allocs->items, sizeof(Value*) * global_allocs->cap);
  }
  global_allocs->items[global_allocs->len++] = v;
  pthread_mutex_unlock(&global_allocs_lock);
}

/* ---------- Constructors ---------- */
static List *list_new(){ List *l = xmalloc(sizeof(List)); l->len=0; l->cap=4; l->items=xmalloc(sizeof(Value*)*l->cap); return l; }
static void list_push(List *l, Value *v){ if(l->len==l->cap){ l->cap*=2; l->items=realloc(l->items, sizeof(Value*)*l->cap); } l->items[l->len++] = v; }
static Value *list_pop(List *l){ if(l->len==0) return NULL; return l->items[--l->len]; }

static Hash *hash_new(){ Hash *h = xmalloc(sizeof(Hash)); h->buckets = 97; h->table = calloc(h->buckets, sizeof(HashEntry*)); return h; }
static unsigned hash_str(const char *s){ unsigned h=5381; while(*s) h = ((h<<5)+h) + (unsigned char)*s++; return h; }
static void hash_set(Hash *h, const char *k, Value *v){ unsigned idx = hash_str(k) % h->buckets; HashEntry *e = h->table[idx]; while(e){ if(strcmp(e->key,k)==0){ e->val = v; return; } e = e->next; } HashEntry *ne = xmalloc(sizeof(HashEntry)); ne->key = xstrdup(k); ne->val = v; ne->next = h->table[idx]; h->table[idx] = ne; }
static Value *hash_get(Hash *h, const char *k){ unsigned idx = hash_str(k) % h->buckets; HashEntry *e = h->table[idx]; while(e){ if(strcmp(e->key,k)==0) return e->val; e = e->next; } return NULL; }

static Value *val_null(){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_NULL; track_alloc(v); return v; }
static Value *val_number(double n){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_NUMBER; v->v.num = n; track_alloc(v); return v; }
static Value *val_string(const char *s){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_STRING; v->v.str = xstrdup(s? s : ""); track_alloc(v); return v; }
static Value *val_list(){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_LIST; v->v.list = list_new(); track_alloc(v); return v; }
static Value *val_hash(){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_HASH; v->v.hash = hash_new(); track_alloc(v); return v; }
static Value *val_func(NativeFn f, int arity){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_FUNC; v->v.func.fn = f; v->v.func.arity = arity; track_alloc(v); return v; }
static Value *val_reviser(){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_REVISER; v->v.reviser.rules = list_new(); track_alloc(v); return v; }
static Value *val_regex(const char *pat){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_REGEX; v->v.regex.pattern = xstrdup(pat?pat:""); int rc = regcomp(&v->v.regex.rex, pat?pat:"", REG_EXTENDED); v->v.regex.valid = (rc==0); track_alloc(v); return v; }
static Value *val_manifold(int nx, int ny){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_MANIFOLD; v->v.manifold.nx = nx; v->v.manifold.ny = ny; v->v.manifold.grid = xmalloc(sizeof(double)*nx*ny); for(int i=0;i<nx*ny;i++) v->v.manifold.grid[i]=0.0; track_alloc(v); return v; }
static Value *val_gc(){ Value *v = xmalloc(sizeof(Value)); memset(v,0,sizeof(Value)); v->type = T_GC; v->v.gc.tracked = list_new(); pthread_mutex_init(&v->v.gc.lock,NULL); track_alloc(v); return v; }
/* Forward declarations of interpreter convenience creators (already in interpreter) */ /* Value *val_string(const char*); Value *val_number(double); Value *val_list(); Value *val_hash(); */ /* Utility: run pdftotext and capture stdout into allocated string (caller frees) */ static char *run_pdftotext_capture(const char *path) { if(!path) return NULL; /* pdftotext -layout path - */ char cmd[1024]; snprintf(cmd, sizeof(cmd), "pdftotext -layout \"%s\" - 2>/dev/null", path); FILE *fp = popen(cmd, "r"); if(!fp) return NULL;
  size_t cap = 4096;
  size_t len = 0;
  char *buf = malloc(cap);
  if(!buf){ pclose(fp); return NULL; }
  while(!feof(fp)){
    size_t r = fread(buf + len, 1, cap - len - 1, fp);
    len += r;
    if(len + 128 >= cap){
      cap *= 2;
      buf = realloc(buf, cap);
      if(!buf){ pclose(fp); return NULL; }
    }
  }
  buf[len] = '\0';
  pclose(fp);
  return buf;
}

/* Native: pdf_load(path) -> opaque string representing path (we'll return path string as handle) */
static Value *native_pdf_load(int argc, Value **argv){
  if(argc < 1) return val_null();
  if(argv[0]->type != T_STRING) return val_null();
  /* just return the path string as a "pdf object" handle */
  return val_string(argv[0]->v.str);
}

/* Native: pdf_extract_text(pdf_obj) -> string */
static Value *native_pdf_extract_text(int argc, Value **argv){
  if(argc < 1) return val_string("");
  if(argv[0]->type != T_STRING) return val_string("");
  const char *path = argv[0]->v.str;
  char *txt = run_pdftotext_capture(path);
  if(!txt) return val_string("");
  Value *v = val_string(txt);
  free(txt);
  return v;
}

/* Simple lowercase copy */
static void strlower_inplace(char *s){
  for(char *p=s; *p; ++p) *p = (char)tolower((unsigned char)*p);
}

/* Tokenize: split on non-alphanumeric (simple) -> returns Value* list of strings */
static Value *native_tokenize_for_lang_model(int argc, Value **argv){
  if(argc < 1) return val_list();
  if(argv[0]->type != T_STRING) return val_list();
  const char *s = argv[0]->v.str;
  Value *out = val_list();
  int L = strlen(s);
  char *tmp = malloc(L+1);
  int ti = 0;
  for(int i=0;i<=L;i++){
    char c = s[i];
    if(isalnum((unsigned char)c) || (unsigned char)c >= 0x80){
      tmp[ti++] = c;
    } else {
      if(ti>0){
	tmp[ti] = '\0';
	/* lowercase */
	strlower_inplace(tmp);
	list_push(out->v.list, val_string(tmp));
	ti = 0;
      }
    }
  }
  free(tmp);
  return out;
}

/* Compute word frequency map from text; returns list of pairs as a hash-like list:
   we'll return a hash where keys are words and values are counts (Value* hash) */
static Value *word_freq_hash_from_text(const char *text){
  Value *h = val_hash();
  if(!text) return h;
  int L = strlen(text);
  char *buf = malloc(L+1);
  int bi = 0;
  for(int i=0;i<=L;i++){
    char c = text[i];
    if(isalnum((unsigned char)c) || (unsigned char)c >= 0x80){
      buf[bi++] = (char)tolower((unsigned char)c);
    } else {
      if(bi>0){
	buf[bi] = 0;
	Value *existing = hash_get(h->v.hash, buf);
	if(existing && existing->type==T_NUMBER){
	  double n = existing->v.num;
	  hash_set(h->v.hash, buf, val_number(n+1));
	} else {
	  hash_set(h->v.hash, buf, val_number(1));
	}
	bi = 0;
      }
    }
  }
  free(buf);
  return h;
}

/* Native: shannon_entropy(text) -> number (word-frequency based) */
static Value *native_shannon_entropy(int argc, Value **argv){
  if(argc < 1) return val_number(0.0);
  if(argv[0]->type != T_STRING) return val_number(0.0);
  Value *hf = word_freq_hash_from_text(argv[0]->v.str);
  /* sum counts */
  double total = 0;
  for(int b=0;b<hf->v.hash->buckets;b++){
    HashEntry *e = hf->v.hash->table[b];
    while(e){
      if(e->val && e->val->type==T_NUMBER) total += e->val->v.num;
      e = e->next;
    }
  }
  double H = 0.0;
  if(total <= 0){ /* cleanup */ cleanup_all(); return val_number(0.0); }
  for(int b=0;b<hf->v.hash->buckets;b++){
    HashEntry *e = hf->v.hash->table[b];
    while(e){
      if(e->val && e->val->type==T_NUMBER){
	double c = e->val->v.num;
	double p = c / total;
	if(p > 0) H += -p * log(p);
      }
      e = e->next;
    }
  }
  return val_number(H);
}

/* Native: zeta_entropy_invariant(text) -> number
   A heuristic: compute frequencies sorted by rank and compute sum_{k} p_k * k^{-s}
   with s = 1.1 (tunable), then normalize. This is a pseudo-"zeta-weighted" entropy measure.
*/
static Value *native_zeta_entropy_invariant(int argc, Value **argv){
  if(argc < 1) return val_number(0.0);
  if(argv[0]->type != T_STRING) return val_number(0.0);
  Value *hf = word_freq_hash_from_text(argv[0]->v.str);
  /* collect counts into array */
  int cap = 128;
  int n = 0;
  double *counts = malloc(sizeof(double)*cap);
  for(int b=0;b<hf->v.hash->buckets;b++){
    HashEntry *e = hf->v.hash->table[b];
    while(e){
      if(e->val && e->val->type==T_NUMBER){
	if(n==cap){ cap*=2; counts = realloc(counts, sizeof(double)*cap); }
	counts[n++] = e->val->v.num;
      }
      e = e->next;
    }
  }
  if(n==0){ free(counts); return val_number(0.0); }
  /* sort descending */
  for(int i=0;i<n;i++) for(int j=i+1;j<n;j++) if(counts[j] > counts[i]){ double t = counts[i]; counts[i]=counts[j]; counts[j]=t; }
  double total = 0; for(int i=0;i<n;i++) total += counts[i];
  double s = 1.1;
  double zsum = 0;
  for(int k=0;k<n;k++){
    double p = counts[k] / total;
    double wk = pow((double)(k+1), -s);
    zsum += p * wk;
  }
  free(counts);
  /* normalize by approximate zeta(s) ~ sum_{k=1..inf} k^{-s}; use truncated harmonic */
  double zeta_approx = 0.0;
  int M = 1000;
  for(int k=1;k<=M;k++) zeta_approx += pow((double)k, -s);
  double inv = zeta_approx > 0 ? (zsum / zeta_approx) : zsum;
  /* return -log(invariant) as "entropy-like" quantity, avoid negative/inf */
  double out = inv > 0 ? -log(inv) : 0.0;
  return val_number(out);
}

/* Native: language_entropy_of_text(text) -> number (char-based Shannon) */
static Value *native_language_entropy_of_text(int argc, Value **argv){
  if(argc < 1) return val_number(0.0);
  if(argv[0]->type != T_STRING) return val_number(0.0);
  const char *s = argv[0]->v.str;
  int cnt[256] = {0};
  int total = 0;
  for(const unsigned char *p=(const unsigned char*)s; *p; ++p){
    cnt[*p]++; total++;
  }
  if(total == 0) return val_number(0.0);
  double H = 0.0;
  for(int i=0;i<256;i++){
    if(cnt[i]>0){
      double p = (double)cnt[i] / total;
      H += -p * log(p);
    }
  }
  return val_number(H);
}

/* Native: semantic_vector(text) -> list(number)
   Build vector of top-K term frequencies normalized (bag-of-words).
   We'll choose K = 64.
*/
static Value *native_semantic_vector(int argc, Value **argv){
  if(argc < 1) return val_list();
  if(argv[0]->type != T_STRING) return val_list();
  Value *hf = word_freq_hash_from_text(argv[0]->v.str);
  /* collect into array of (word,count) */
  int cap = 256;
  int n = 0;
  char **words = malloc(sizeof(char*) * cap);
  double *counts = malloc(sizeof(double) * cap);
  for(int b=0;b<hf->v.hash->buckets;b++){
    HashEntry *e = hf->v.hash->table[b];
    while(e){
      if(e->val && e->val->type==T_NUMBER){
	if(n==cap){ cap*=2; words = realloc(words, sizeof(char*)*cap); counts=realloc(counts,sizeof(double)*cap); }
	words[n] = e->key ? xstrdup(e->key) : xstrdup("");
	counts[n] = e->val->v.num;
	n++;
      }
      e = e->next;
    }
  }
  /* sort by counts desc (simple selection sort for small n) */
  for(int i=0;i<n;i++){
    int best=i;
    for(int j=i+1;j<n;j++) if(counts[j] > counts[best]) best=j;
    if(best!=i){
      double t = counts[i]; counts[i]=counts[best]; counts[best]=t;
      char *ts = words[i]; words[i]=words[best]; words[best]=ts;
    }
  }
  int K = 64;
  Value *vec = val_list();
  double norm = 0.0;
  for(int i=0;i<K;i++){
    double v = (i < n) ? counts[i] : 0.0;
    list_push(vec->v.list, val_number(v));
    norm += v * v;
  }
  /* normalize to unit length */
  norm = sqrt(norm) + 1e-12;
  for(int i=0;i<vec->v.list->len;i++){
    Value *old = vec->v.list->items[i];
    double orig = 0.0;
    if(old && old->type==T_NUMBER) orig = old->v.num;
      vec->v.list->items[i]  = val_number(orig / norm);
  }
  for(int i=0;i<n;i++) if(words[i]) free(words[i]);
  free(words); free(counts);
  return vec;
}

/* Native: cosine_similarity(vecA, vecB) -> number
   Both vec* are lists of numbers (Value* lists).
*/
static Value *native_cosine_similarity(int argc, Value **argv){
  if(argc < 2) return val_number(0.0);
  if(argv[0]->type!=T_LIST || argv[1]->type!=T_LIST) return val_number(0.0);
  int n = argv[0]->v.list->len < argv[1]->v.list->len ? argv[0]->v.list->len : argv[1]->v.list->len;
  double dot = 0.0;
  for(int i=0;i<n;i++){
    Value *a = argv[0]->v.list->items[i];
    Value *b = argv[1]->v.list->items[i];
    double av = (a && a->type==T_NUMBER) ? a->v.num : 0.0;
    double bv = (b && b->type==T_NUMBER) ? b->v.num : 0.0;
    dot += av * bv;
  }
  return val_number(dot);
}

/* Native random_seed(n) and rand() wrapper -> rand() returns number in [0,1) */
static Value *native_random_seed(int argc, Value **argv){
  if(argc < 1) { srand((unsigned)time(NULL)); return val_null(); }
  if(argv[0]->type != T_NUMBER) { srand((unsigned)time(NULL)); return val_null(); }
  unsigned seed = (unsigned)(argv[0]->v.num);
  srand(seed);
  return val_null();
}
static Value *native_rand01(int argc, Value **argv){
  double r = (double)rand() / ((double)RAND_MAX + 1.0);
  return val_number(r);
}

/* Native: text_split_sections(text) -> hash of sections (heuristic) */
static Value *native_text_split_sections(int argc, Value **argv){
  Value *out = val_hash();
  if(argc < 1) return out;
  if(argv[0]->type != T_STRING) return out;
  const char *txt = argv[0]->v.str;
  char *work = xstrdup(txt);
  strlower_inplace(work);
  /* search patterns and extract approximate spans */
  const char *keys[] = {"abstract","introduction","theorem","proof","conclusion","conjecture","discussion"};
  int K = sizeof(keys)/sizeof(keys[0]);
  int L = strlen(work);
  /* find positions */
  int *pos = calloc(K, sizeof(int));
  for(int i=0;i<K;i++) pos[i] = -1;
  for(int i=0;i<K;i++){
    char *p = strstr(work, keys[i]);
    if(p) pos[i] = (int)(p - work);
  }
  /* For each found key, extract until next found or end; return original-case substring by mapping into original text */
  for(int i=0;i<K;i++){
    if(pos[i] >= 0){
      int start = pos[i];
      int end = L;
      for(int j=i+1;j<K;j++) if(pos[j] >= 0 && pos[j] > start){ end = pos[j]; break; }
      /* Map to original text offsets: approximate by searching the same lowercased substring in original */
      char *needle = keys[i];
      char *orig = argv[0]->v.str;
      char *found = NULL;
      /* find first occurrence of needle in original, case-insensitive search */
      for(char *q = (char*)orig; *q; ++q){
	int match = 1;
	for(int m=0; needle[m]; ++m){
	  char c1 = q[m];
	  char c2 = needle[m];
	  if(!c1 || tolower((unsigned char)c1) != c2){ match = 0; break; }
	}
	if(match){ found = q; break; }
      }
      if(!found) continue;
      /* Now find end by searching next key in original; to keep it simple, extract from found up to min(found+ (end-start) , end of original) */
      int orig_start = (int)(found - argv[0]->v.str);
      int span = end - start;
      if(orig_start + span > (int)strlen(argv[0]->v.str)) span = (int)strlen(argv[0]->v.str) - orig_start;
      char *sub = extract_block_between_positions(orig_start, orig_start + span);
      hash_set(out->v.hash, keys[i], val_string(sub));
      free(sub);
    }
  }
  free(work);
  free(pos);
  return out;
}

/* Native: trim(s) and substring(s,start,end) - helpers */
static Value *native_trim(int argc, Value **argv){
  if(argc < 1) return val_string("");
  if(argv[0]->type != T_STRING) return val_string("");
  const char *s = argv[0]->v.str;
  int L = strlen(s);
  int a = 0;
  while(a < L && isspace((unsigned char)s[a])) a++;
  int b = L - 1;
  while(b >= 0 && isspace((unsigned char)s[b])) b--;
  if(b < a) return val_string("");
  int len = b - a + 1;
  char *t = strndup(s + a, len);
  Value *v = val_string(t);
  free(t);
  return v;
}
static Value *native_substring(int argc, Value **argv){
  if(argc < 3) return val_string("");
  if(argv[0]->type != T_STRING || argv[1]->type != T_NUMBER || argv[2]->type != T_NUMBER) return val_string("");
  const char *s = argv[0]->v.str;
  int start = (int)argv[1]->v.num;
  int end   = (int)argv[2]->v.num;
  int L = strlen(s);
  if(start < 0) start = 0;
  if(end > L) end = L;
  if(end <= start) return val_string("");
  char *t = strndup(s + start, end - start);
  Value *v = val_string(t);
  free(t);
  return v;
}


/* ---------- Printing ---------- */
static void val_print_nolf(Value *v);
static void val_print(Value *v){ val_print_nolf(v); printf("\n"); }
static void val_print_nolf(Value *v){
  if(!v){ printf("null"); return; }
  switch(v->type){
  case T_NULL: printf("null"); break;
  case T_NUMBER: if((double)(long)v->v.num == v->v.num) printf("%.0f", v->v.num); else printf("%g", v->v.num); break;
  case T_STRING: printf("\"%s\"", v->v.str? v->v.str : ""); break;
  case T_LIST: {
    printf("[");
    for(int i=0;i<v->v.list->len;i++){ if(i) printf(", "); val_print_nolf(v->v.list->items[i]); }
    printf("]"); break;
  }
  case T_HASH: {
    printf("{");
    int first=1;
    for(int b=0;b<v->v.hash->buckets;b++){ HashEntry *e=v->v.hash->table[b]; while(e){ if(!first) printf(", "); printf("\"%s\": ", e->key); val_print_nolf(e->val); first=0; e=e->next; } }
    printf("}"); break;
  }
  case T_FUNC: printf("<native:%d>", v->v.func.arity); break;
  case T_REVISER: printf("<reviser rules=%d>", v->v.reviser.rules->len); break;
  case T_REGEX: printf("<regex:%s valid=%d>", v->v.regex.pattern?v->v.regex.pattern:"", v->v.regex.valid); break;
  case T_MANIFOLD: printf("<manifold %dx%d>", v->v.manifold.nx, v->v.manifold.ny); break;
  case T_GC: printf("<gc tracked=%d>", v->v.gc.tracked->len); break;
  }
}

/* ---------- Environment (with local stack) ---------- */
typedef struct EnvEntry { char *name; Value *val; struct EnvEntry *next; } EnvEntry;
static EnvEntry *global_env = NULL;

/* local env stack: each element is a linked list of EnvEntry representing a frame */
typedef struct LocalFrame { EnvEntry *entries; struct LocalFrame *next; } LocalFrame;
static LocalFrame *local_stack = NULL;

static void env_set_global(const char *name, Value *v){ EnvEntry *e = global_env; while(e){ if(strcmp(e->name,name)==0){ e->val = v; return; } e = e->next; } EnvEntry *n = xmalloc(sizeof(EnvEntry)); n->name = xstrdup(name); n->val = v; n->next = global_env; global_env = n; }
static void env_set_local(const char *name, Value *v){
  if(!local_stack){ /* create frame if not exists */ local_stack = xmalloc(sizeof(LocalFrame)); local_stack->entries = NULL; local_stack->next = NULL; }
  EnvEntry *e = local_stack->entries; while(e){ if(strcmp(e->name,name)==0){ e->val = v; return; } e = e->next; }
  EnvEntry *n = xmalloc(sizeof(EnvEntry)); n->name = xstrdup(name); n->val = v; n->next = local_stack->entries; local_stack->entries = n;
}
static Value *env_get_any(const char *name){
  /* check local stack top-down */
  LocalFrame *f = local_stack;
  while(f){
    EnvEntry *e = f->entries;
    while(e){ if(strcmp(e->name,name)==0) return e->val; e = e->next; }
    f = f->next;
  }
  /* fallback to global */
  EnvEntry *g = global_env;
  while(g){ if(strcmp(g->name,name)==0) return g->val; g = g->next; }
  return NULL;
}
static void push_local_frame(){ LocalFrame *f = xmalloc(sizeof(LocalFrame)); f->entries = NULL; f->next = local_stack; local_stack = f; }
static void pop_local_frame(){
  if(!local_stack) return;
  EnvEntry *e = local_stack->entries;
  while(e){ EnvEntry *n = e->next; free(e->name); free(e); e = n; }
  LocalFrame *nf = local_stack->next;
  free(local_stack);
  local_stack = nf;
}
static void env_set_type(const char *name, const char *type){ char buf[256]; snprintf(buf,sizeof(buf),"__type:%s", name); env_set_global(buf, val_string(type)); }
static const char *env_get_type(const char *name){ char buf[256]; snprintf(buf,sizeof(buf),"__type:%s", name); Value *v = env_get_any(buf); if(!v || v->type!=T_STRING) return NULL; return v->v.str; }

/* convenience wrappers naming consistent with previous code */
#define env_set env_set_global
#define env_get env_get_any

/* ---------- Lexer ---------- */
typedef enum { TK_EOF, TK_NUM, TK_STR, TK_IDENT, TK_LBRACK, TK_RBRACK, TK_LPAREN, TK_RPAREN, TK_LBRACE, TK_RBRACE, TK_COMMA, TK_COLON, TK_SEMI, TK_ARROW, TK_OTHER } Tok;
typedef struct { Tok t; char *lex; double num; } Token;
static char *src = NULL; static int srcpos = 0; static Token curtok = {TK_EOF, NULL, 0};
static void tok_free(Token *t){ if(t->lex) free(t->lex); t->lex = NULL; t->t = TK_EOF; t->num = 0; }
static void lex_init(const char *s){ if(src) free(src); src = xstrdup(s?s:""); srcpos = 0; tok_free(&curtok); }
static void lex_skip_ws(){ while(src[srcpos] && isspace((unsigned char)src[srcpos])) srcpos++; }
static int startswith(const char *p){ return strncmp(src+srcpos, p, strlen(p))==0; }

static void lex_next(){
  tok_free(&curtok);
  lex_skip_ws();
  if(!src[srcpos]){ curtok.t = TK_EOF; return; }
  char c = src[srcpos];
  if(isdigit((unsigned char)c) || (c=='.' && isdigit((unsigned char)src[srcpos+1]))){
    char *end; double n = strtod(src+srcpos, &end);
    int len = end - (src+srcpos);
    curtok.lex = strndup(src+srcpos, len); curtok.t = TK_NUM; curtok.num = n;
    srcpos += len; return;
  }
  if(c=='"'){
    srcpos++; int start = srcpos;
    while(src[srcpos] && src[srcpos]!='"'){ if(src[srcpos]=='\\' && src[srcpos+1]) srcpos += 2; else srcpos++; }
    int len = srcpos - start; curtok.lex = strndup(src+start, len); curtok.t = TK_STR; if(src[srcpos] == '"') srcpos++; return;
  }
  if(startswith("<-")){ curtok.t = TK_ARROW; curtok.lex = xstrdup("<-"); srcpos += 2; return; }
  switch(c){
  case '[': curtok.t = TK_LBRACK; curtok.lex = xstrdup("["); srcpos++; return;
  case ']': curtok.t = TK_RBRACK; curtok.lex = xstrdup("]"); srcpos++; return;
  case '(': curtok.t = TK_LPAREN; curtok.lex = xstrdup("("); srcpos++; return;
  case ')': curtok.t = TK_RPAREN; curtok.lex = xstrdup(")"); srcpos++; return;
  case '{': curtok.t = TK_LBRACE; curtok.lex = xstrdup("{"); srcpos++; return;
  case '}': curtok.t = TK_RBRACE; curtok.lex = xstrdup("}"); srcpos++; return;
  case ',': curtok.t = TK_COMMA; curtok.lex = xstrdup(","); srcpos++; return;
  case ':': curtok.t = TK_COLON; curtok.lex = xstrdup(":"); srcpos++; return;
  case ';': curtok.t = TK_SEMI; curtok.lex = xstrdup(";"); srcpos++; return;
  default:
    if(isalpha((unsigned char)c) || c=='_'){
      int start = srcpos;
      while(src[srcpos] && (isalnum((unsigned char)src[srcpos]) || src[srcpos]=='_')) srcpos++;
      int len = srcpos - start;
      curtok.lex = strndup(src+start, len);
      curtok.t = TK_IDENT;
      return;
    }
    curtok.t = TK_OTHER;
    curtok.lex = strndup(src+srcpos,1);
    srcpos++;
    return;
  }
}

/* lookahead save/restore */
typedef struct { Token tok; int pos; } LexState;
static LexState lex_save(){ LexState s; s.pos = srcpos; s.tok.t = curtok.t; s.tok.num = curtok.num; s.tok.lex = curtok.lex ? xstrdup(curtok.lex) : NULL; return s; }
static void lex_restore(LexState *s){ tok_free(&curtok); curtok.t = s->tok.t; curtok.num = s->tok.num; curtok.lex = s->tok.lex ? xstrdup(s->tok.lex) : NULL; srcpos = s->pos; if(s->tok.lex) free(s->tok.lex); }

/* ---------- Parser/Evaluator (with class support) ---------- */
static Value *parse_expression(); /* forward */
static Value *resolve_if_ident(Value *v); /* forward */
static char *extract_block_between_positions(int start_pos, int end_pos){
  if(!src) return xstrdup("");
  if(end_pos <= start_pos) return xstrdup("");
  int len = end_pos - start_pos;
  char *out = xmalloc(len + 1);
  memcpy(out, src + start_pos, len);
  out[len] = '\0';
  return out;
}

/* primary: numbers, strings, identifiers, constructors, list, hash, function calls, and GROUPING (parentheses) */
static Value *parse_primary(){
  if(curtok.t == TK_NUM){ Value *v = val_number(curtok.num); lex_next(); return v; }
  if(curtok.t == TK_STR){ Value *v = val_string(curtok.lex); lex_next(); return v; }
  if(curtok.t == TK_LPAREN){
    lex_next();
    Value *inner = parse_expression();
    if(curtok.t == TK_RPAREN) lex_next();
    return inner;
  }
  if(curtok.t == TK_IDENT){
    /* detect class literal, constructor, method calls, function calls */
    char *id = xstrdup(curtok.lex);
    lex_next();

    /* class constructor: IDENT . new ( ... ) or IDENT.new */
    if(curtok.t == TK_OTHER && curtok.lex && strcmp(curtok.lex,".")==0){
      lex_next();
      if(curtok.t == TK_IDENT && strcmp(curtok.lex,"new")==0){
	/* create instance of class id */
	lex_next();
	/* consume optional parentheses */
	if(curtok.t == TK_LPAREN){
	  /* skip args for now (no ctor args implemented) */
	  while(curtok.t != TK_RPAREN && curtok.t != TK_EOF) lex_next();
	  if(curtok.t == TK_RPAREN) lex_next();
	}
	/* class object stored in env as hash */
	Value *class_obj = env_get(id);
	Value *inst = val_hash();
	/* store class pointer */
	if(class_obj) hash_set(inst->v.hash, "__class", class_obj);
	else hash_set(inst->v.hash, "__class_name", val_string(id));
	free(id);
	return inst;
      }
      /* method call style: IDENT . IDENT ( ... ) - handled below by falling through */
      Value *left = val_string(id);
      if(curtok.t == TK_IDENT){
	char *mname = xstrdup(curtok.lex);
	lex_next();
	if(curtok.t == TK_LPAREN){
	  lex_next();
	  Value **args = NULL; int argcnt = 0;
	  while(curtok.t != TK_RPAREN && curtok.t != TK_EOF){
	    Value *a = parse_expression();
	    args = realloc(args, sizeof(Value*)*(argcnt+1));
	    args[argcnt++] = a;
	    if(curtok.t == TK_COMMA) lex_next();
	    else break;
	  }
	  if(curtok.t == TK_RPAREN) lex_next();
	  Value *leftv = resolve_if_ident(left);
	  Value *result = val_null();
	  if(leftv && leftv->type == T_HASH){
	    Value *cobj = hash_get(leftv->v.hash, "__class");
	    if(!cobj){
	      Value *cn = hash_get(leftv->v.hash, "__class_name");
	      if(cn && cn->type==T_STRING) cobj = env_get(cn->v.str);
	    }
	    if(cobj && cobj->type==T_HASH){
	      Value *method = hash_get(cobj->v.hash, mname);
	      if(method && method->type==T_LIST && method->v.list->len>=2){
		Value *params = method->v.list->items[0];
		Value *body = method->v.list->items[1];
		push_local_frame();
		env_set_local("self", leftv);
		int plen = params->v.list->len;
		for(int i=0;i<plen && i<argcnt;i++){
		  Value *pn = params->v.list->items[i];
		  if(pn->type==T_STRING) env_set_local(pn->v.str, args[i]);
		}
		Value *ret = val_null();
		char *saved_src = src;
		int saved_pos = srcpos;
		Token saved_tok = {curtok.t, curtok.lex ? xstrdup(curtok.lex) : NULL, curtok.num};
		lex_init(body->type==T_STRING?body->v.str:"");
		lex_next();
		while(curtok.t != TK_EOF){
		  Value *r = parse_expression();
		  if(r) ret = r;
		  if(curtok.t == TK_SEMI) lex_next();
		  else if(curtok.t == TK_EOF) break;
		  else lex_next();
		}
		tok_free(&curtok);
		curtok = saved_tok;
		src = saved_src;
		srcpos = saved_pos;
		pop_local_frame();
		result = ret;
	      }
	    }
	  } else {
	    Value *class_obj = NULL;
	    if(leftv && leftv->type==T_STRING) class_obj = env_get(leftv->v.str);
	    else if(leftv && leftv->type==T_HASH) class_obj = leftv;
	    if(class_obj && class_obj->type==T_HASH){
	      Value *method = hash_get(class_obj->v.hash, mname);
	      if(method && method->type==T_LIST && method->v.list->len>=2){
		Value *params = method->v.list->items[0];
		Value *body = method->v.list->items[1];
		push_local_frame();
		int plen = params->v.list->len;
		for(int i=0;i<plen && i<argcnt;i++){
		  Value *pn = params->v.list->items[i];
		  if(pn->type==T_STRING) env_set_local(pn->v.str, args[i]);
		}
		Value *ret = val_null();
		char *saved_src = src;
		int saved_pos = srcpos;
		Token saved_tok = {curtok.t, curtok.lex ? xstrdup(curtok.lex) : NULL, curtok.num};
		lex_init(body->type==T_STRING?body->v.str:"");
		lex_next();
		while(curtok.t != TK_EOF){
		  Value *r = parse_expression();
		  if(r) ret = r;
		  if(curtok.t == TK_SEMI) lex_next();
		  else if(curtok.t == TK_EOF) break;
		  else lex_next();
		}
		tok_free(&curtok);
		curtok = saved_tok;
		src = saved_src;
		srcpos = saved_pos;
		pop_local_frame();
		result = ret;
	      }
	    }
	  }
	  if(args) free(args);
	  free(left->v.str); free(left);
	  free(mname);
	  return result;
	} else {
	  Value *leftv = resolve_if_ident(left);
	  Value *out = val_null();
	  if(leftv && leftv->type == T_HASH){
	    Value *prop = hash_get(leftv->v.hash, mname);
	    if(prop) out = prop;
	    else out = val_null();
	  } else {
	    out = val_null();
	  }
	  free(left->v.str); free(left);
	  free(mname);
	  return out;
	}
      } else {
	return left;
      }
    }

    /* function call: id ( args ) */
    if(curtok.t == TK_LPAREN){
      Value *fnv = env_get(id);
      lex_next();
      Value **argv = NULL; int argcnt = 0;
      while(curtok.t != TK_RPAREN && curtok.t != TK_EOF){
	Value *arg = parse_expression();
	argv = realloc(argv, sizeof(Value*) * (argcnt+1));
	argv[argcnt++] = arg;
	if(curtok.t == TK_COMMA) lex_next();
	else break;
      }
      if(curtok.t == TK_RPAREN) lex_next();
      Value *res = val_null();
      if(fnv && fnv->type == T_FUNC) res = fnv->v.func.fn(argcnt, argv);
      else res = val_null();
      if(argv) free(argv);
      free(id);
      return res;
    }

    /* otherwise identifier value (variable/class) */
    Value *s = val_string(id);
    free(id);
    return s;
  }
  if(curtok.t == TK_LBRACK){
    lex_next();
    Value *L = val_list();
    while(curtok.t != TK_RBRACK && curtok.t != TK_EOF){
      Value *e = parse_expression();
      list_push(L->v.list, e);
      if(curtok.t == TK_COMMA) lex_next();
      else break;
    }
    if(curtok.t == TK_RBRACK) lex_next();
    return L;
  }
  if(curtok.t == TK_LBRACE){
    lex_next();
    Value *H = val_hash();
    while(curtok.t != TK_RBRACE && curtok.t != TK_EOF){
      if(curtok.t == TK_STR){
	char *key = xstrdup(curtok.lex);
	lex_next();
	if(curtok.t == TK_COLON) lex_next();
	Value *val = parse_expression();
	hash_set(H->v.hash, key, val);
	free(key);
      } else lex_next();
      if(curtok.t == TK_COMMA) lex_next();
      else break;
    }
    if(curtok.t == TK_RBRACE) lex_next();
    return H;
  }
  return val_null();
}

/* resolve identifier-like string values to environment values (prefers local) */
static Value *resolve_if_ident(Value *v){
  if(!v) return v;
  if(v->type == T_STRING){
    Value *found = env_get(v->v.str);
    if(found) return found;
  }
  return v;
}

/* arithmetic parsing */
static Value *parse_unary();
static Value *parse_muldiv();
static Value *parse_addsub();

static Value *parse_unary(){
  if(curtok.t == TK_OTHER && curtok.lex && strcmp(curtok.lex,"+") == 0){ lex_next(); return parse_unary(); }
  if(curtok.t == TK_OTHER && curtok.lex && strcmp(curtok.lex,"-") == 0){ lex_next(); Value *v = parse_unary(); if(v->type==T_NUMBER) return val_number(-v->v.num); return val_null(); }
  return parse_primary();
}

static Value *parse_muldiv(){
  Value *left = parse_unary();
  while(curtok.t == TK_OTHER && curtok.lex && (strcmp(curtok.lex,"*")==0 || strcmp(curtok.lex,"/")==0)){
    char op = curtok.lex[0];
    lex_next();
    Value *right = parse_unary();
    left = resolve_if_ident(left);
    right = resolve_if_ident(right);
    if(left->type == T_NUMBER && right->type == T_NUMBER){
      if(op == '*') left = val_number(left->v.num * right->v.num);
      else left = val_number(left->v.num / right->v.num);
    } else left = val_null();
  }
  return left;
}

static Value *parse_addsub(){
  Value *left = parse_muldiv();
  while(curtok.t == TK_OTHER && curtok.lex && (strcmp(curtok.lex,"+")==0 || strcmp(curtok.lex,"-")==0)){
    char op = curtok.lex[0];
    lex_next();
    Value *right = parse_muldiv();
    left = resolve_if_ident(left);
    right = resolve_if_ident(right);
    if(left->type == T_NUMBER && right->type == T_NUMBER){
      if(op == '+') left = val_number(left->v.num + right->v.num);
      else left = val_number(left->v.num - right->v.num);
    } else left = val_null();
  }
  return left;
}

/* parse_expression: supports optional leading type declaration and indexing/assignment and class/def parsing */
static Value *parse_expression(){
  /* class and def handling: if current token is 'class' */
  if(curtok.t == TK_IDENT && strcmp(curtok.lex,"class")==0){
    lex_next();
    if(curtok.t != TK_IDENT) return val_null();
    char *classname = xstrdup(curtok.lex);
    lex_next();
    Value *class_obj = val_hash();
    while(!(curtok.t == TK_IDENT && strcmp(curtok.lex,"end")==0) && curtok.t != TK_EOF){
      if(curtok.t == TK_IDENT && strcmp(curtok.lex,"def")==0){
	lex_next();
	if(curtok.t != TK_IDENT) { while(curtok.t!=TK_IDENT && curtok.t!=TK_EOF) lex_next(); continue; }
	char *mname = xstrdup(curtok.lex);
	lex_next();
	List *params = list_new();
	if(curtok.t == TK_LPAREN){
	  lex_next();
	  while(curtok.t != TK_RPAREN && curtok.t != TK_EOF){
	    if(curtok.t == TK_IDENT){
	      Value *pn = val_string(curtok.lex);
	      list_push(params, pn);
	      lex_next();
	    } else lex_next();
	    if(curtok.t == TK_COMMA) lex_next();
	  }
	  if(curtok.t == TK_RPAREN) lex_next();
	}
	int body_start = srcpos;
	int depth = 0;
	while(curtok.t != TK_EOF){
	  if(curtok.t == TK_IDENT && strcmp(curtok.lex,"def")==0) depth++;
	  if(curtok.t == TK_IDENT && strcmp(curtok.lex,"end")==0){
	    if(depth==0) break;
	    else depth--;
	  }
	  lex_next();
	}
	int body_end_pos = srcpos;
	char *body_src = extract_block_between_positions(body_start, body_end_pos);
	if(curtok.t == TK_IDENT && strcmp(curtok.lex,"end")==0) lex_next();
	Value *method_val = val_list();
	Value *params_val = val_list();
	for(int i=0;i<params->len;i++) list_push(params_val->v.list, params->items[i]);
	list_push(method_val->v.list, params_val);
	list_push(method_val->v.list, val_string(body_src));
	hash_set(class_obj->v.hash, mname, method_val);
	free(body_src);
	free(mname);
	free(params);
	continue;
      } else {
	lex_next();
      }
    }
    if(curtok.t == TK_IDENT && strcmp(curtok.lex,"end")==0) lex_next();
    env_set(classname, class_obj);
    free(classname);
    return class_obj;
  }

  /* variable type declaration e.g. math x <- expr or array/hash etc. */
  if(curtok.t == TK_IDENT){
    LexState s = lex_save();
    char *type_tok = curtok.lex ? xstrdup(curtok.lex) : NULL;
    lex_next();
    if(curtok.t == TK_IDENT){
      char *name_tok = curtok.lex ? xstrdup(curtok.lex) : NULL;
      lex_next();
      if(curtok.t == TK_ARROW){
	lex_restore(&s);
	char *type_name = xstrdup(curtok.lex);
	lex_next();
	char *varname = xstrdup(curtok.lex);
	lex_next();
	if(curtok.t == TK_ARROW) lex_next();
	Value *rhs = parse_expression();
	if(strcmp(type_name,"array")==0){
	  if(rhs->type != T_LIST){ Value *L = val_list(); list_push(L->v.list, rhs); rhs = L; }
	  env_set_type(varname, "array");
	} else if(strcmp(type_name,"hash")==0){ env_set_type(varname, "hash"); }
	else { env_set_type(varname, type_name); }
	env_set(varname, rhs);
	free(type_name); free(varname);
	if(type_tok) free(type_tok);
	if(name_tok) free(name_tok);
	return rhs;
      }
      if(type_tok) free(type_tok);
      if(name_tok) free(name_tok);
    } else { if(type_tok) free(type_tok); }
    lex_restore(&s);
  }

  Value *left = parse_addsub();

  for(;;){
    if(curtok.t == TK_LBRACK){
      lex_next();
      Value *idx = parse_expression();
      if(curtok.t == TK_RBRACK) lex_next();
      Value *base = left;
      base = resolve_if_ident(base);
      Value *out = val_list();
      if(base && base->type == T_LIST){
	int i = -1;
	if(idx->type == T_NUMBER) i = (int)idx->v.num;
	else if(idx->type == T_STRING) i = atoi(idx->v.str);
	if(i >= 0 && i < base->v.list->len) list_push(out->v.list, base->v.list->items[i]);
      } else if(base && base->type == T_HASH){
	if(idx->type == T_STRING){
	  Value *hv = hash_get(base->v.hash, idx->v.str);
	  if(hv) list_push(out->v.list, hv);
	}
      }
      left = out;
      continue;
    }
	  if(curtok.t == TK_ARROW){
            lex_next();
            Value *right = parse_expression();
            if(left && left->type == T_STRING){
	      env_set(left->v.str, right);
	      left = right;
            } else left = right;
            continue;
	  }
        break;
  }
  return left;
}

/* ---------- Reviser application ---------- */
static char *apply_single_rule_from_vals(char *input, Value *patv, Value *repv){
  if(!input) return xstrdup("");
  if(!patv || !repv) return xstrdup(input);
  if(patv->type == T_STRING){
    const char *pat = patv->v.str;
    const char *rep = repv->type==T_STRING ? repv->v.str : "";
    if(strlen(pat)==0) return xstrdup(input);
    char *out = malloc(1); out[0]=0;
    const char *p = input;
    while(1){
      char *found = strstr(p, pat);
      if(!found){
	out = realloc(out, strlen(out) + strlen(p) + 1);
	strcat(out, p);
	break;
      }
      size_t pre = found - p;
      out = realloc(out, strlen(out) + pre + strlen(rep) + 1);
      strncat(out, p, pre);
      strcat(out, rep);
      p = found + strlen(pat);
    }
    return out;
  } else if(patv->type == T_REGEX && patv->v.regex.valid){
    regex_t *r = &patv->v.regex.rex;
    const char *s = input;
    regmatch_t m;
    size_t pos = 0;
    char *acc = xstrdup("");
    while(regexec(r, s+pos, 1, &m, 0) == 0){
      size_t pre = m.rm_so;
      acc = realloc(acc, strlen(acc) + pre + (repv->type==T_STRING?strlen(repv->v.str):0) + 2);
      strncat(acc, s+pos, pre);
      if(repv->type==T_STRING) strcat(acc, repv->v.str);
      pos += m.rm_eo;
      if(pos >= strlen(s)) break;
    }
    if(pos < strlen(s)){ acc = realloc(acc, strlen(acc) + strlen(s+pos) + 2); strcat(acc, s+pos); }
    if(strlen(acc)==0){ free(acc); return xstrdup(input); }
    return acc;
  }
  return xstrdup(input);
}

static char *apply_reviser(Value *r, const char *input){
  if(!r || r->type!=T_REVISER) return xstrdup(input);
  char *cur = xstrdup(input);
  for(int i=0;i<r->v.reviser.rules->len;i++){
    Value *rule = r->v.reviser.rules->items[i];
    if(!rule || rule->type != T_LIST || rule->v.list->len < 2) continue;
    Value *pat = rule->v.list->items[0];
    Value *rep = rule->v.list->items[1];
    char *next = apply_single_rule_from_vals(cur, pat, rep);
    free(cur);
    cur = next;
  }
  return cur;
}

/* ---------- Native functions ---------- */
static Value *native_print(int argc, Value **argv){ for(int i=0;i<argc;i++){ val_print_nolf(argv[i]); if(i+1<argc) printf(" "); } return val_null(); }
static Value *native_len(int argc, Value **argv){ if(argc<1) return val_number(0); if(argv[0]->type==T_LIST) return val_number(argv[0]->v.list->len); if(argv[0]->type==T_STRING) return val_number(strlen(argv[0]->v.str)); return val_number(0); }
static Value *native_push(int argc, Value **argv){ if(argc<2) return val_null(); if(argv[0]->type==T_LIST){ list_push(argv[0]->v.list, argv[1]); return argv[0]; } return val_null(); }
static Value *native_pop(int argc, Value **argv){ if(argc<1) return val_null(); if(argv[0]->type==T_LIST) return list_pop(argv[0]->v.list); return val_null(); }
static Value *native_hash_set(int argc, Value **argv){ if(argc<3) return val_null(); if(argv[0]->type!=T_HASH||argv[1]->type!=T_STRING) return val_null(); hash_set(argv[0]->v.hash, argv[1]->v.str, argv[2]); return val_null(); }
static Value *native_hash_get(int argc, Value **argv){ if(argc<2) return val_null(); if(argv[0]->type!=T_HASH||argv[1]->type!=T_STRING) return val_null(); Value *r = hash_get(argv[0]->v.hash, argv[1]->v.str); return r? r : val_null(); }
static Value *reviser_add_rule(int argc, Value **argv){ if(argc<3) return val_null(); if(argv[0]->type!=T_REVISER) return val_null(); Value *rule = val_list(); list_push(rule->v.list, argv[1]); list_push(rule->v.list, argv[2]); list_push(argv[0]->v.reviser.rules, rule); return val_null(); }
static Value *native_regex_match(int argc, Value **argv){ if(argc<2) return val_number(0); if(argv[0]->type!=T_REGEX||argv[1]->type!=T_STRING) return val_number(0); if(!argv[0]->v.regex.valid) return val_number(0); regmatch_t m; int rc = regexec(&argv[0]->v.regex.rex, argv[1]->v.str, 1, &m, 0); return val_number(rc==0?1:0); }
static Value *native_regex_replace(int argc, Value **argv){ if(argc<3) return val_string(""); if(argv[0]->type!=T_REGEX||argv[1]->type!=T_STRING) return val_string(""); char *res = apply_single_rule_from_vals(argv[1]->v.str, argv[0], argv[2]); Value *r = val_string(res); free(res); return r; }

/* manifold natives */
static Value *native_manifold_set(int argc, Value **argv){ if(argc<2) return val_null(); if(argv[0]->type!=T_MANIFOLD||argv[1]->type!=T_LIST) return val_null(); Value *m=argv[0], *lst=argv[1]; int nx=m->v.manifold.nx, ny=m->v.manifold.ny, n=nx*ny; for(int i=0;i<n;i++) m->v.manifold.grid[i] = (i<lst->v.list->len && lst->v.list->items[i]->type==T_NUMBER) ? lst->v.list->items[i]->v.num : 0.0; return m; }
static Value *native_manifold_diff(int argc, Value **argv){ if(argc<1) return val_null(); if(argv[0]->type!=T_MANIFOLD) return val_null(); Value *m=argv[0]; int nx=m->v.manifold.nx, ny=m->v.manifold.ny; Value *out = val_list(); for(int y=0;y<ny;y++){ for(int x=0;x<nx;x++){ int i=y*nx+x; double c=m->v.manifold.grid[i]; double sum=0; int cnt=0; if(x>0){ sum+=m->v.manifold.grid[i-1]; cnt++; } if(x<nx-1){ sum+=m->v.manifold.grid[i+1]; cnt++; } if(y>0){ sum+=m->v.manifold.grid[i-nx]; cnt++; } if(y<ny-1){ sum+=m->v.manifold.grid[i+nx]; cnt++; } double lap = (cnt>0)?(sum/cnt - c):0.0; list_push(out->v.list, val_number(lap)); } } return out; }
static Value *native_manifold_integrate(int argc, Value **argv){ if(argc<1) return val_null(); if(argv[0]->type!=T_MANIFOLD) return val_null(); Value *m=argv[0]; int n=m->v.manifold.nx*m->v.manifold.ny; double s=0; for(int i=0;i<n;i++) s+=m->v.manifold.grid[i]; return val_number(s); }

/* gc natives */
static Value *native_gc_alloc(int argc, Value **argv){ if(argc<2) return val_null(); if(argv[0]->type!=T_GC) return val_null(); int size = (int)(argv[1]->type==T_NUMBER? argv[1]->v.num : 0); void *mem = malloc(size>0?size:1); char buf[64]; snprintf(buf,sizeof(buf),"%p",mem); Value *s = val_string(buf); list_push(argv[0]->v.gc.tracked, s); return s; }
static Value *native_gc_collect(int argc, Value **argv){ if(argc<1) return val_null(); if(argv[0]->type!=T_GC) return val_null(); Value *g = argv[0]; for(int i=0;i<g->v.gc.tracked->len;i++){ Value *tv = g->v.gc.tracked->items[i]; if(tv->type==T_STRING && tv->v.str) free(tv->v.str); free(tv); } g->v.gc.tracked->len = 0; return val_null(); }

/* souzal attach */
static Value *native_sousal(int argc, Value **argv){ if(argc<2) return val_null(); if(argv[0]->type!=T_LIST||argv[1]->type!=T_LIST) return val_null(); List *src = argv[0]->v.list; List *dst = argv[1]->v.list; Value *errlist = env_get("__errors"); if(!errlist){ errlist = val_list(); env_set("__errors", errlist); } for(int i=0;i<src->len;i++){ Value *it = src->items[i]; if(it->type==T_STRING && strncmp(it->v.str,"ERR:",4)==0) list_push(errlist->v.list, it); else list_push(dst, it); } src->len = 0; return val_null(); }

/* math natives */
static Value *native_sin(int argc, Value **argv){ if(argc<1 || argv[0]->type!=T_NUMBER) return val_null(); return val_number(sin(argv[0]->v.num)); }
static Value *native_cos(int argc, Value **argv){ if(argc<1 || argv[0]->type!=T_NUMBER) return val_null(); return val_number(cos(argv[0]->v.num)); }
static Value *native_tan(int argc, Value **argv){ if(argc<1 || argv[0]->type!=T_NUMBER) return val_null(); return val_number(tan(argv[0]->v.num)); }
static Value *native_exp(int argc, Value **argv){ if(argc<1 || argv[0]->type!=T_NUMBER) return val_null(); return val_number(exp(argv[0]->v.num)); }
static Value *native_log(int argc, Value **argv){ if(argc<1 || argv[0]->type!=T_NUMBER) return val_null(); return val_number(log(argv[0]->v.num)); }
static Value *native_powv(int argc, Value **argv){ if(argc<2 || argv[0]->type!=T_NUMBER || argv[1]->type!=T_NUMBER) return val_null(); return val_number(pow(argv[0]->v.num, argv[1]->v.num)); }
static Value *native_add(int argc, Value **argv){ if(argc<2) return val_null(); if(argv[0]->type!=T_NUMBER || argv[1]->type!=T_NUMBER) return val_null(); return val_number(argv[0]->v.num + argv[1]->v.num); }
/* native readline: prints prompt (if given) and reads a line from stdin, returns Value* string */
static Value *native_readline(int argc, Value **argv){
  const char *prompt = NULL;
  if (argc >= 1 && argv[0]->type == T_STRING) prompt = argv[0]->v.str;

  /* print prompt (without newline) and flush */
  if (prompt && prompt[0] != '\0') {
    fputs(prompt, stdout);
    fflush(stdout);
  }

  char *line = NULL;
  size_t len = 0;
  ssize_t read = getline(&line, &len, stdin);
  if (read == -1) {
    if (line) free(line);
    return val_null(); /* EOF or error */
  }

  /* remove trailing CR/LF */
  while (read > 0 && (line[read-1] == '\n' || line[read-1] == '\r')) {
    line[--read] = '\0';
  }

  /* Create Value string and free buffer if val_string copies it; adapt if your val_string takes ownership */
  Value *ret = val_string(line);

  /* If val_string duplicates the content, free original; otherwise, if val_string takes ownership, do not free */
  /* Assume val_string clones the input, so free here: */
  free(line);

  return ret;
}
/* VM 側の Value 生成関数プロトタイプ（実装に合わせて置換） */
Value *val_string(const char *s);
Value *val_null(void);

/* 書き込みコールバックで受け取るバッファ */
struct membuf {
	    char *buf;
	        size_t len;
};

static size_t write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
	    size_t realsz = size * nmemb;
	        struct membuf *m = (struct membuf*)userdata;
		    char *newbuf = realloc(m->buf, m->len + realsz + 1);
		        if (!newbuf) return 0;
			    m->buf = newbuf;
			        memcpy(m->buf + m->len, ptr, realsz);
				    m->len += realsz;
				        m->buf[m->len] = '\0';
					    return realsz;
}


/* native llm_query(prompt, opts_json_string_or_null) */
static Value *native_llm_query(int argc, Value **argv) {
	    const char *prompt = NULL;
	        const char *opts_json = NULL;

		    if (argc >= 1 && argv[0]->type == T_STRING) prompt = argv[0]->v.str;
		        if (argc >= 2 && argv[1]->type == T_STRING) opts_json = argv[1]->v.str;

			    if (!prompt) return val_null();

			        const char *endpoint = getenv("LLM_ENDPOINT");
				    const char *api_key  = getenv("LLM_API_KEY");
				        if (!endpoint) return val_null();

					    CURL *curl = curl_easy_init();
					        if (!curl) return val_null();

						    struct membuf resp;
						        resp.buf = malloc(1);
							    resp.len = 0;

							        /* build JSON body: {"prompt":"...","opts":{...}} or opts omitted */
							        /* naive JSON escaping for prompt (handles quotes and backslashes) */
							        size_t plen = strlen(prompt);
								    size_t esc_cap = plen * 2 + 1;
								        char *prompt_esc = malloc(esc_cap);
									    size_t pi = 0;
									        for (size_t i = 0; i < plen; ++i) {
											        char c = prompt[i];
												        if (c == '\\' || c == '"') { prompt_esc[pi++] = '\\'; prompt_esc[pi++] = c; }
													        else if (c == '\n') { prompt_esc[pi++] = '\\'; prompt_esc[pi++] = 'n'; }
														        else prompt_esc[pi++] = c;
															    }
										    prompt_esc[pi] = '\0';

										        const char *template_noopts = "{\"prompt\":\"%s\"}";
											    const char *template_withopts = "{\"prompt\":\"%s\",\"opts\":%s}";
											        size_t body_cap = strlen(template_withopts) + pi + (opts_json? strlen(opts_json):0) + 32;
												    char *body = malloc(body_cap);
												        if (opts_json && opts_json[0] != '\0') {
														        snprintf(body, body_cap, template_withopts, prompt_esc, opts_json);
															    } else {
																            snprintf(body, body_cap, template_noopts, prompt_esc);
																	        }

													    struct curl_slist *hdrs = NULL;
													        hdrs = curl_slist_append(hdrs, "Content-Type: application/json");
														    if (api_key) {
															            size_t authlen = strlen("Authorization: Bearer ") + strlen(api_key) + 1;
																            char *auth = malloc(authlen);
																	            snprintf(auth, authlen, "Authorization: Bearer %s", api_key);
																		            hdrs = curl_slist_append(hdrs, auth);
																			            free(auth);
																				        }

														        curl_easy_setopt(curl, CURLOPT_URL, endpoint);
															    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, hdrs);
															        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body);
																    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
																        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &resp);
																	    /* optional: timeout */
																	    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

																	        CURLcode res = curl_easy_perform(curl);

																		    Value *ret = NULL;
																		        if (res != CURLE_OK) {
																				        ret = val_null();
																					    } else {
																						            /* resp.buf contains response body (assumed text). Return as VM string. */
																						            ret = val_string(resp.buf ? resp.buf : "");
																							        }

																			    /* cleanup */
																			    curl_slist_free_all(hdrs);
																			        curl_easy_cleanup(curl);
																				    free(resp.buf);
																				        free(prompt_esc);
																					    free(body);

																					        return ret;
}



/* ---------- Bootstrap env ---------- */
static void bootstrap_env(){
  env_set("print", val_func(native_print, -1));
  env_set("len", val_func(native_len, 1));
  env_set("push", val_func(native_push, 2));
  env_set("pop", val_func(native_pop, 1));
  env_set("hash_set", val_func(native_hash_set, 3));
  env_set("hash_get", val_func(native_hash_get, 2));
  env_set("__reviser", val_reviser());
  env_set("reviser_add", val_func(reviser_add_rule, 3));
  env_set("regex_match", val_func(native_regex_match, 2));
  env_set("regex_replace", val_func(native_regex_replace, 3));
  env_set("manifold_set", val_func(native_manifold_set, 2));
  env_set("manifold_diff", val_func(native_manifold_diff, 1));
  env_set("manifold_integrate", val_func(native_manifold_integrate, 1));
  env_set("gc_alloc", val_func(native_gc_alloc, 2));
  env_set("gc_collect", val_func(native_gc_collect, 1));
  env_set("__errors", val_list());
  env_set("sousal_attach", val_func(native_sousal, 2));
  env_set("sin", val_func(native_sin, 1));
  env_set("cos", val_func(native_cos, 1));
  env_set("tan", val_func(native_tan, 1));
  env_set("exp", val_func(native_exp, 1));
  env_set("log", val_func(native_log, 1));
  env_set("pow", val_func(native_powv, 2));
  env_set("add", val_func(native_add, 2));
   env_set("pdf_load", val_func(native_pdf_load, 1));
   env_set("pdf_extract_text", val_func(native_pdf_extract_text, 1));
   env_set("text_split_sections", val_func(native_text_split_sections, 1));
   env_set("shannon_entropy", val_func(native_shannon_entropy, 1));
   env_set("zeta_entropy_invariant", val_func(native_zeta_entropy_invariant, 1));
   env_set("language_entropy_of_text", val_func(native_language_entropy_of_text, 1));
   env_set("semantic_vector", val_func(native_semantic_vector, 1));
   env_set("cosine_similarity", val_func(native_cosine_similarity, 2));
   env_set("tokenize_for_lang_model", val_func(native_tokenize_for_lang_model, 1));
   env_set("random_seed", val_func(native_random_seed, 1));
   env_set("rand", val_func(native_rand01, 0));
   env_set("trim", val_func(native_trim, 1));
   env_set("substring", val_func(native_substring, 3));
   env_set("readline", val_func(native_readline, 1)); 
    env_set("llm_query", val_func(native_llm_query, 2));

}

/* ---------- Execution / compile ---------- */
static void execute_source(const char *source_in){
  Value *rev = env_get("__reviser");
  char *src2 = (char*)source_in;
  char *tmp = NULL;
  if(rev && rev->type==T_REVISER){
    tmp = apply_reviser(rev, source_in);
    src2 = tmp;
  }
  lex_init(src2);
  lex_next();
  while(curtok.t != TK_EOF){
    Value *res = parse_expression();
    if(res && res->type != T_NULL){
      val_print(res);
    }
    if(curtok.t == TK_SEMI) lex_next();
    else if(curtok.t == TK_EOF) break;
    else lex_next();
  }
  if(tmp) free(tmp);
}

static int compile_to_file(const char *input_src, const char *outpath){
  Value *rev = env_get("__reviser");
  char *trans = (char*)input_src;
  char *tmp = NULL;
  if(rev && rev->type==T_REVISER){
    tmp = apply_reviser(rev, input_src);
    trans = tmp;
  }
  FILE *f = fopen(outpath,"wb");
  if(!f){ if(tmp) free(tmp); return 1; }
  fwrite(trans,1,strlen(trans),f);
  fclose(f);
  if(tmp) free(tmp);
  return 0;
}

/* ---------- Cleanup ---------- */
static void cleanup_all(){
  if(global_allocs){
    for(int i=0;i<global_allocs->len;i++){
      Value *v = global_allocs->items[i];
      if(!v) continue;
      switch(v->type){
      case T_STRING: if(v->v.str) free(v->v.str); break;
      case T_LIST:
	if(v->v.list){
	  if(v->v.list->items) free(v->v.list->items);
	  free(v->v.list);
	}
	break;
      case T_HASH:
	if(v->v.hash){
	  for(int b=0;b<v->v.hash->buckets;b++){
	    HashEntry *e = v->v.hash->table[b];
	    while(e){ HashEntry *n = e->next; free(e->key); free(e); e = n; }
	  }
	  free(v->v.hash->table);
	  free(v->v.hash);
	}
	break;
      case T_REGEX:
	if(v->v.regex.valid) regfree(&v->v.regex.rex);
	if(v->v.regex.pattern) free(v->v.regex.pattern);
	break;
      case T_MANIFOLD:
	if(v->v.manifold.grid) free(v->v.manifold.grid);
	break;
      case T_REVISER:
	if(v->v.reviser.rules){
	  if(v->v.reviser.rules->items) free(v->v.reviser.rules->items);
	  free(v->v.reviser.rules);
	}
	break;
      case T_GC:
	if(v->v.gc.tracked){
	  for(int k=0;k<v->v.gc.tracked->len;k++){
	    Value *tv = v->v.gc.tracked->items[k];
	    if(tv->type==T_STRING && tv->v.str) free(tv->v.str);
	    free(tv);
	  }
	  if(v->v.gc.tracked->items) free(v->v.gc.tracked->items);
	  free(v->v.gc.tracked);
	}
	pthread_mutex_destroy(&v->v.gc.lock);
	break;
      default: break;
      }
      free(v);
    }
    if(global_allocs->items) free(global_allocs->items);
    free(global_allocs);
    global_allocs = NULL;
  }
  while(local_stack) pop_local_frame();
  EnvEntry *e = global_env;
  while(e){ EnvEntry *n = e->next; free(e->name); free(e); e = n; }
  global_env = NULL;
  if(src){ free(src); src = NULL; }
}

/* ---------- Utility: read file ---------- */
static char *read_file_to_str(const char *path){
  FILE *f = fopen(path,"rb"); if(!f) return NULL;
  fseek(f,0,SEEK_END); long sz = ftell(f); fseek(f,0,SEEK_SET);
  char *buf = xmalloc(sz+1); fread(buf,1,sz,f); buf[sz]=0; fclose(f); return buf;
}

/* ---------- Main ---------- */
int main(int argc, char **argv){
  bootstrap_env();

  if(argc < 3){
    fprintf(stderr, "Usage:\n  %s interpret inputfile\n  %s -c inputfile outputfile\n", argv[0], argv[0]);
        const char *demo =
            "class calculate\n"
            "  def add(a,b)\n"
            "    math x <- a + b;\n"
            "    x\n"
            "  end\n"
            "end\n"
            "c <- calculate.new();\n"
	  "print(c.add(2,3));\n";
        execute_source(demo);
        cleanup_all();
        return 1;
  }

  if(strcmp(argv[1], "interpret") == 0){
    char *inp = read_file_to_str(argv[2]);
    if(!inp){ fprintf(stderr, "cannot open %s\n", argv[2]); cleanup_all(); return 1; }
    execute_source(inp);
    free(inp);
    cleanup_all();
    return 0;
  } else if(strcmp(argv[1], "-c") == 0){
    if(argc < 4){ fprintf(stderr, "Usage: %s -c inputfile outputfile\n", argv[0]); cleanup_all(); return 1; }
    char *inp = read_file_to_str(argv[2]);
    if(!inp){ fprintf(stderr, "cannot open %s\n", argv[2]); cleanup_all(); return 1; }
    int rc = compile_to_file(inp, argv[3]);
    free(inp);
    if(rc != 0){ fprintf(stderr, "failed to write %s\n", argv[3]); cleanup_all(); return 1; }
    printf("compiled -> %s\n", argv[3]);
    cleanup_all();
    return 0;
  } else {
    fprintf(stderr, "Unknown command: %s\n", argv[1]);
    cleanup_all();
    return 1;
  }
}
