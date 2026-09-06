  // omega_zeta_pipeline.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <math.h>
#include <curl/curl.h>

  /* ---------- small I/O helpers ---------- */
  static char *slurp(const char *path){
  FILE *f = fopen(path,"r"); if(!f) return NULL;
  fseek(f,0,SEEK_END); long s = ftell(f); fseek(f,0,SEEK_SET);
  char *b = malloc(s+1); if(!b){ fclose(f); return NULL; }
  fread(b,1,s,f); b[s]=0; fclose(f); return b;
}

/* ---------- Step1: tokenize, keywords, templates ---------- */
  static char **tokenize(const char *txt, size_t *out_n){
    size_t cap=128, n=0; char **arr = malloc(cap*sizeof(char*));
    const char *p=txt; while(*p){
      while(*p && !isalpha((unsigned char)*p)) p++;
      if(!*p) break;
      const char *q=p; while(*q && isalpha((unsigned char)*q)) q++;
      size_t len=q-p; char *w = malloc(len+1);
      for(size_t i=0;i<len;i++) w[i]=tolower((unsigned char)p[i]); w[len]=0;
      if(n==cap){ cap*=2; arr = realloc(arr, cap*sizeof(char*)); }
      arr[n++]=w; p=q;
    }
    *out_n = n; return arr;
  }
static void free_tokens(char **t, size_t n){ for(size_t i=0;i<n;i++) free(t[i]); free(t); }

typedef struct { char *w; int cnt; } Unigram;
static Unigram *build_unigrams(char **t, size_t n, size_t *out_m){
  size_t cap = n? n:1; Unigram *u = malloc(cap*sizeof(Unigram)); size_t m=0;
  for(size_t i=0;i<n;i++){
    int found=0;
    for(size_t j=0;j<m;j++) if(strcmp(u[j].w,t[i])==0){ u[j].cnt++; found=1; break; }
    if(!found){ u[m].w = strdup(t[i]); u[m].cnt=1; m++; if(m==cap){ cap*=2; u=realloc(u,cap*sizeof(Unigram)); } }
  }
  *out_m = m; return u;
}
static void free_unigrams(Unigram *u, size_t m){ for(size_t i=0;i<m;i++) free(u[i].w); free(u); }
static int is_stop(const char *w){
  const char *stoplist[] = {"the","and","of","in","to","a","is","for","on","with","by","as","an","that",NULL};
  for(int i=0; stoplist[i]; ++i) if(strcmp(w, stoplist[i])==0) return 1;
  return 0;
}
static char **top_keywords(Unigram *u, size_t m, size_t K, size_t *out_k){
  char **out = malloc(K * sizeof(char*)); size_t k=0;
  for(size_t iter=0; iter<m && k<K; ++iter){
    int best_i=-1; int best_v=-1;
    for(size_t i=0;i<m;i++){
      if(u[i].cnt > best_v && !is_stop(u[i].w)){
	int already=0; for(size_t j=0;j<k;j++) if(strcmp(out[j],u[i].w)==0){ already=1; break; }
	if(!already){ best_v = u[i].cnt; best_i = (int)i; }
      }
    }
    if(best_i<0) break;
    out[k++]=strdup(u[best_i].w);
  }
  *out_k = k; return out;
}
static void free_kw(char **k, size_t n){ for(size_t i=0;i<n;i++) free(k[i]); free(k); }

static const char *templates[] = {
  "The report links {{A}} with {{B}} via spectral topology.",
  "We observe that {{A}} and {{B}} contribute to an entropy invariant in knot theory.",
  "A proposed mapping: topology -> Hamiltonian terms influenced by {{A}}.",
  "Evidence suggests Euler-type products of {{A}} yield corrections to {{B}}.",
    "Local quantum operators appear from decomposition of {{A}} and interactions with {{B}}."
};
static const size_t N_TEMPL = sizeof(templates)/sizeof(templates[0]);

static char *fill_template(const char *tpl, char **kw, size_t kn){
  const char *p = tpl; char buf[1024]; buf[0]=0;
  while(*p){
    if(p[0]=='{' && p[1]=='{'){
      const char *q = strstr(p,"}}"); if(!q) break;
      size_t len = q - (p+2);
      char slot[len+1]; memcpy(slot, p+2, len); slot[len]=0;
      const char *choice = NULL;
      if(strstr(slot,"A")) choice = (kn>0? kw[rand()%kn] : "zeta");
      else if(strstr(slot,"B")) choice = (kn>1? kw[rand()%kn] : "Gamma");
      else choice = "X";
      strncat(buf, choice, sizeof(buf)-strlen(buf)-1);
      p = q + 2;
    } else {
      size_t l = 1;
      strncat(buf, p, l);
      p += l;
    }
    if(strlen(buf) > sizeof(buf)-200) break;
  }
  return strdup(buf);
}

/* ---------- Step2: AST ---------- */
typedef enum { NODE_CONST, NODE_VAR, NODE_ADD, NODE_MUL, NODE_POW, NODE_FUNC } NodeKind;
typedef struct Node {
  NodeKind kind; double val; char *name; struct Node *left; struct Node *right;
} Node;
static Node *node_const(double v){ Node *n=calloc(1,sizeof(Node)); n->kind=NODE_CONST; n->val=v; return n; }
static Node *node_var(const char *s){ Node *n=calloc(1,sizeof(Node)); n->kind=NODE_VAR; n->name=strdup(s); return n; }
static Node *node_bin(NodeKind k, Node *a, Node *b){ Node *n=calloc(1,sizeof(Node)); n->kind=k; n->left=a; n->right=b; return n; }
static Node *node_func(const char *fname, Node *arg){ Node *n=calloc(1,sizeof(Node)); n->kind=NODE_FUNC; n->name=strdup(fname); n->left=arg; return n; }
static void free_node(Node *n){ if(!n) return; if(n->name) free(n->name); free_node(n->left); free_node(n->right); free(n); }

static void print_node_rec(Node *n, FILE *out){
  if(!n) return;
  switch(n->kind){
  case NODE_CONST: fprintf(out, "%.6g", n->val); break;
  case NODE_VAR: fprintf(out, "%s", n->name); break;
  case NODE_ADD: fprintf(out,"("); print_node_rec(n->left,out); fprintf(out," + "); print_node_rec(n->right,out); fprintf(out,")"); break;
  case NODE_MUL: fprintf(out,"("); print_node_rec(n->left,out); fprintf(out," * "); print_node_rec(n->right,out); fprintf(out,")"); break;
  case NODE_POW: fprintf(out,"{"); print_node_rec(n->left,out); fprintf(out,"}^{"); print_node_rec(n->right,out); fprintf(out,"}"); break;
  case NODE_FUNC: fprintf(out,"%s(", n->name); print_node_rec(n->left,out); fprintf(out,")"); break;
  }
}
static void print_node(Node *n){ print_node_rec(n, stdout); printf("\n"); }

static void tolow(char *s){ for(;*s;++s) *s = (char)tolower((unsigned char)*s); }

static Node *synthesize_from_sentence(const char *sentence){
  if(!sentence) return NULL;
  char buf[1024]; strncpy(buf, sentence, sizeof(buf)-1); buf[sizeof(buf)-1]=0;
  tolow(buf);
  int has_zeta = strstr(buf,"zeta") || strstr(buf,"ゼータ");
  int has_gamma = strstr(buf,"gamma") || strstr(buf,"ガンマ");
  int has_jones = strstr(buf,"jones") || strstr(buf,"ジョーンズ") || strstr(buf,"多項式");
  int has_entropy = strstr(buf,"entropy") || strstr(buf,"エントロピー");
  int has_ham = strstr(buf,"hamilton") || strstr(buf,"ハミルトン");
  int has_beta = strstr(buf,"beta") || strstr(buf,"ベータ");
  if(has_zeta && has_gamma){
    Node *Z = node_func("Z", node_var("s"));
    Node *G = node_func("Gamma", node_var("s"));
    return node_bin(NODE_ADD, Z, G);
  }
  if(has_jones && has_entropy){
    Node *p_k = node_var("p_k");
    Node *logpk = node_func("log", node_var("p_k"));
    Node *term = node_bin(NODE_MUL, node_const(-1.0), node_bin(NODE_MUL, p_k, logpk));
    return term;
  }
  if(has_ham){
    Node *sumT = node_var("sum_i_T_i");
    Node *V = node_func("V", node_var("Top"));
    return node_bin(NODE_ADD, sumT, V);
  }
  if(has_beta){
    Node *G_p = node_func("Gamma", node_var("p"));
    Node *G_q = node_func("Gamma", node_var("q"));
    Node *num = node_bin(NODE_MUL, G_p, G_q);
    Node *den = node_func("Gamma", node_bin(NODE_ADD, node_var("p"), node_var("q")));
    Node *inv_den = node_bin(NODE_POW, den, node_const(-1.0));
    return node_bin(NODE_MUL, num, inv_den);
  }
  /* fallback: pick a first substantive token */
  const char *p = buf; char token[64] = {0};
  while(*p){
    while(*p && !isalpha((unsigned char)*p)) p++;
    if(!*p) break;
    const char *q = p; int len=0;
    while(*q && isalpha((unsigned char)*q) && len<63){ token[len++]=*q; q++; }
    token[len]=0;
    if(len>2) break;
    p = q;
  }
  if(token[0]) return node_func("F", node_var(token));
  return node_var("E");
}

/* ---------- Step3: optional LLM (OpenAI Chat) ---------- */
/* tiny curl write callback */
struct mem { char *ptr; size_t len; };
static size_t write_cb(void *data, size_t size, size_t nmemb, void *userp){
  size_t realsz = size * nmemb;
  struct mem *m = (struct mem*)userp;
  char *nptr = realloc(m->ptr, m->len + realsz + 1);
  if(!nptr) return 0;
  m->ptr = nptr;
  memcpy(m->ptr + m->len, data, realsz);
  m->len += realsz;
  m->ptr[m->len]=0;
  return realsz;
}

/* call OpenAI Chat (expects OPENAI_API_KEY in env). Simple prompt asking two-line output:
   SENTENCE: <short sentence>
   FORMULA: <short formula/expression or LaTeX>
*/
static char *call_openai_chat(const char *report_excerpt){
  const char *key = getenv("OPENAI_API_KEY");
  if(!key) return NULL;
  CURL *curl = curl_easy_init();
  if(!curl) return NULL;
  struct mem chunk = { malloc(1), 0 };
  const char *url = "https://api.openai.com/v1/chat/completions";
  curl_easy_setopt(curl, CURLOPT_URL, url);
  struct curl_slist *hdr = NULL;
  char auth[512]; snprintf(auth, sizeof(auth), "Authorization: Bearer %s", key);
  hdr = curl_slist_append(hdr, "Content-Type: application/json");
  hdr = curl_slist_append(hdr, auth);
  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, hdr);
  /* craft a concise prompt */
  char prompt[2048];
  snprintf(prompt, sizeof(prompt),
      "You are an assistant. Given the following scientific report excerpt, produce exactly two lines:\n"
      "SENTENCE: a single concise, coherent English sentence summarizing a relation (max 140 chars)\n"
      "FORMULA: a short textual/LaTeX-like math expression or named formulas related to the sentence (no more than one line)\n\n"
      "Report excerpt:\n%s\n\n"
	   "Return only the two lines starting with 'SENTENCE:' and 'FORMULA:' respectively.", report_excerpt?report_excerpt:"");
  /* build JSON body with basic escaping */
  char esc[4096]; char *d=esc; const char *s=prompt;
  *d++ = '\"';
  while(*s && (d - esc) < (int)(sizeof(esc)-10)){
    if(*s == '\\' || *s == '\"'){ *d++='\\'; *d++ = *s; }
    else if(*s == '\n'){ *d++='\\'; *d++ = 'n'; }
    else *d++ = *s;
    s++;
  }
  *d++ = '\"'; *d=0;
  char body[8192];
  snprintf(body, sizeof(body),
	   "{\"model\":\"gpt-4o-mini\",\"messages\":[{\"role\":\"user\",\"content\":%s}],\"max_tokens\":300}", esc);

  curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body);
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
  curl_easy_setopt(curl, CURLOPT_TIMEOUT, 20L);
  CURLcode res = curl_easy_perform(curl);
  curl_slist_free_all(hdr);
  curl_easy_cleanup(curl);
  if(res != CURLE_OK){ free(chunk.ptr); return NULL; }
  /* crude extraction: find first "content": value */
  char *p = strstr(chunk.ptr, "\"content\":");
  if(!p){ free(chunk.ptr); return NULL; }
  p = strchr(p, ':'); if(!p){ free(chunk.ptr); return NULL; } p++;
  while(*p && *p!='"') p++; if(!*p){ free(chunk.ptr); return NULL; } p++;
  char *q = p; char outbuf[2000]; char *o = outbuf;
  while(*q && *q!='"' && (o - outbuf) < (int)(sizeof(outbuf)-1)){
    if(*q == '\\' && *(q+1)){ q++; if(*q=='n'){ *o++='\n'; } else *o++ = *q; q++; continue; }
    *o++ = *q++;
  }
  *o = 0;
  char *ret = strdup(outbuf);
  free(chunk.ptr);
  return ret;
}

/* parse LLM two-line response */
static void parse_llm_response(const char *resp, char **out_sentence, char **out_formula){
  *out_sentence = NULL; *out_formula = NULL;
  if(!resp) return;
  const char *s = resp;
  const char *ln = strstr(s, "SENTENCE:");
  if(ln){
    ln += strlen("SENTENCE:");
    while(*ln == ' ' || *ln == '\t') ln++;
    const char *e = strchr(ln, '\n');
    size_t len = e? (size_t)(e - ln) : strlen(ln);
    *out_sentence = malloc(len+1); strncpy(*out_sentence, ln, len); (*out_sentence)[len]=0;
  }
  const char *fm = strstr(s, "FORMULA:");
  if(fm){
    fm += strlen("FORMULA:");
    while(*fm == ' ' || *fm == '\t') fm++;
    const char *e = strchr(fm, '\n');
    size_t len = e? (size_t)(e - fm) : strlen(fm);
    *out_formula = malloc(len+1); strncpy(*out_formula, fm, len); (*out_formula)[len]=0;
  }
}

/* ---------- main pipeline ---------- */
int main(int argc, char **argv){
  if(argc<2){ fprintf(stderr,"usage: %s explorerfiles.txt\n", argv[0]); return 1; }
  char *txt = slurp(argv[1]); if(!txt){ fprintf(stderr,"cannot read %s\n", argv[1]); return 1; }
  srand((unsigned)time(NULL));

  size_t tn; char **tokens = tokenize(txt, &tn);
  size_t um; Unigram *u = build_unigrams(tokens, tn, &um);
  size_t K=6, kn; char **kw = top_keywords(u, um, K, &kn);
  printf("Top keywords:");
  for(size_t i=0;i<kn;i++) printf(" %s", kw[i]); printf("\n\n");

  /* generate candidates (Step1) */
  size_t candidates = 5;
  char *cands[candidates];
  for(size_t i=0;i<candidates;i++){
    int tid = rand()%N_TEMPL;
    cands[i] = fill_template(templates[tid], kw, kn);
  }
  printf("Local generated sentences:\n");
  for(size_t i=0;i<candidates;i++){ printf("%zu: %s\n", i+1, cands[i]); }
  printf("\n");

  /* for each candidate produce AST (Step2) */
  printf("Synthesized ASTs (from local rules):\n");
  for(size_t i=0;i<candidates;i++){
    Node *ast = synthesize_from_sentence(cands[i]);
    printf("%zu: \"%s\" => ", i+1, cands[i]);
    print_node(ast);
    free_node(ast);
  }
  printf("\n");

  /* Step3: call LLM on a short excerpt (first 2000 chars) */
  const char *api_key = getenv("OPENAI_API_KEY");
  if(api_key){
    char excerpt[2001]; strncpy(excerpt, txt, 2000); excerpt[2000]=0;
    printf("Calling LLM (OpenAI) to refine one sentence/formula...\n");
    curl_global_init(CURL_GLOBAL_DEFAULT);
    char *resp = call_openai_chat(excerpt);
    if(resp){
      char *llm_sent=NULL, *llm_form=NULL;
      parse_llm_response(resp, &llm_sent, &llm_form);
      printf("LLM response raw:\n%s\n\n", resp);
      if(llm_sent) printf("LLM Sentence: %s\n", llm_sent);
      if(llm_form)  printf("LLM Formula: %s\n", llm_form);
      if(llm_sent){
	Node *ast2 = synthesize_from_sentence(llm_sent);
	printf("Mapped AST from LLM sentence:\n");
	print_node(ast2);
	free_node(ast2);
      }
      free(llm_sent); free(llm_form);
      free(resp);
    } else {
      printf("LLM call failed or returned empty.\n");
    }
    curl_global_cleanup();
  } else {
    printf("OPENAI_API_KEY not set — skipping Step3 (LLM).\n");
  }

  /* cleanup */
  for(size_t i=0;i<candidates;i++) free(cands[i]);
  free_kw(kw, kn); free_unigrams(u, um); free_tokens(tokens, tn); free(txt);
  return 0;
}
