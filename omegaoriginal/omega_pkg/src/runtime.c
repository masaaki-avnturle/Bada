/* runtime.c - runtime with arrays/lists/hashes/func and '=>', '>-' support */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "../include/omega.h"

typedef struct StrNode { char *s; struct StrNode *next; } StrNode;
typedef struct ArrayObj { char *name; StrNode *items; struct ArrayObj *next; } ArrayObj;
typedef struct ListObj  { char *name; StrNode *items; struct ListObj *next; } ListObj;
typedef struct FuncObj  { char *name; long data; struct FuncObj *next; } FuncObj;
typedef struct HashPair { char *k; long v; struct HashPair *next; } HashPair;
typedef struct HashObj  { char *name; HashPair *pairs; struct HashObj *next; } HashObj;

/* generic mapping for => and >- : store simple bindings (lhs -> rhs string) */
typedef struct Bind { char *lhs; char *op; char *rhs; struct Bind *next; } Bind;
static Bind *bindings = NULL;

static ArrayObj *arrays = NULL; static ListObj *lists = NULL; static FuncObj *funcs = NULL; static HashObj *hashes = NULL;

static char *dupstr(const char *s){ if(!s) return NULL; size_t n=strlen(s)+1; char *r=malloc(n); if(!r) return NULL; memcpy(r,s,n); return r; }
static void push_str(StrNode **root, char *s){ StrNode *n=malloc(sizeof(*n)); if(!n) return; n->s=s; n->next=*root; *root=n; }
static void reverse_list(StrNode **root){ StrNode *r=NULL,*it=*root; while(it){ StrNode *nx=it->next; it->next=r; r=it; it=nx; } *root=r; }

static void add_array(const char *name, char **items, size_t n){ ArrayObj *a=malloc(sizeof(*a)); if(!a) return; a->name=dupstr(name); a->items=NULL; a->next=arrays; arrays=a; for(size_t i=0;i<n;i++) push_str(&a->items, dupstr(items[i])); reverse_list(&a->items); }
static void add_list(const char *name, char **items, size_t n){ ListObj *l=malloc(sizeof(*l)); if(!l) return; l->name=dupstr(name); l->items=NULL; l->next=lists; lists=l; for(size_t i=0;i<n;i++) push_str(&l->items, dupstr(items[i])); reverse_list(&l->items); }
static void add_func(const char *name, long v){ FuncObj *f=malloc(sizeof(*f)); if(!f) return; f->name=dupstr(name); f->data=v; f->next=funcs; funcs=f; }
static void add_hash(const char *name, char **keys, long *vals, size_t n){ HashObj *h=malloc(sizeof(*h)); if(!h) return; h->name=dupstr(name); h->pairs=NULL; h->next=hashes; hashes=h; for(size_t i=0;i<n;i++){ HashPair *p=malloc(sizeof(*p)); if(!p) continue; p->k=dupstr(keys[i]); p->v=vals[i]; p->next=h->pairs; h->pairs=p; } /* reverse to preserve order */ HashPair *rev=NULL,*it=h->pairs; while(it){ HashPair *nx=it->next; it->next=rev; rev=it; it=nx; } h->pairs=rev; }

static void add_binding(const char *lhs, const char *op, const char *rhs){ Bind *b=malloc(sizeof(*b)); if(!b) return; b->lhs=dupstr(lhs); b->op=dupstr(op); b->rhs=dupstr(rhs); b->next=bindings; bindings=b; }

static int print_by_name(const char *name){ if(!name) return 0; for(ArrayObj *a=arrays;a;a=a->next){ if(a->name && strcmp(a->name,name)==0){ putchar('['); StrNode *it=a->items; int first=1; while(it){ if(!first) putchar(','); printf("\"%s\"", it->s); first=0; it=it->next; } puts("]"); return 1; } }
 for(HashObj *h=hashes;h;h=h->next){ if(h->name && strcmp(h->name,name)==0){ putchar('{'); HashPair *hp=h->pairs; int first=1; while(hp){ if(!first) putchar(','); printf("\"%s\":%ld", hp->k, hp->v); first=0; hp=hp->next; } puts("}"); return 1; } }
 for(ListObj *l=lists;l;l=l->next){ if(l->name && strcmp(l->name,name)==0){ putchar('('); StrNode *it=l->items; int first=1; while(it){ if(!first) putchar(','); printf("\"%s\"", it->s); first=0; it=it->next; } puts(")"); return 1; } }
 for(FuncObj *f=funcs; f; f=f->next){ if(f->name && strcmp(f->name,name)==0){ printf("%ld\n", f->data); return 1; } }
 /* bindings */ for(Bind *b=bindings;b;b=b->next){ if(strcmp(b->lhs,name)==0){ printf("%s %s %s\n", b->lhs, b->op, b->rhs); return 1; } }
 return 0; }

/* parse helpers */
static char *read_quoted(const char **pp){ const char *p=*pp; while(*p && *p!='\"') ++p; if(!*p) return NULL; p++; size_t cap=64; char *b=malloc(cap); if(!b) return NULL; size_t n=0; while(*p && *p!='\"'){ char c=*p++; if(c=='\\' && *p){ char e=*p++; if(e=='n') c='\n'; else if(e=='t') c='\t'; else c=e; } if(n+1>=cap){ cap*=2; char *t=realloc(b,cap); if(!t){ free(b); return NULL; } b=t; } b[n++]=c; } b[n]=0; if(*p=='\"') ++p; *pp=p; return b; }

/* very small recursive parser focusing on constructs and =>, >- */
static void parse_build(const char *content){ if(!content) return; const char *p=content; while(*p){ const char *semi = strchr(p,';'); if(!semi) break; size_t len = (size_t)(semi - p); char *line = malloc(len+1); if(!line) break; memcpy(line,p,len); line[len]=0; char *s=line; while(*s && isspace((unsigned char)*s)) s++;
    /* declarations */
    if (strncmp(s, "array", 5)==0 && (s[5]==' '||s[5]=='\t')){ char name[128]={0}; const char *q=s+5; while(*q==' '||*q=='\t') ++q; size_t i=0; while(*q && *q!=' ' && *q!='=' && *q!='[' && i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *lb=strchr(s,'['); const char *rb=strchr(s,']'); if(lb&&rb&&rb>lb){ const char *t=lb+1; char *items[128]; size_t in=0; while(t<rb && in<128){ while(*t==' '||*t==','||*t=='\t') ++t; if(*t=='\"'){ char *v = read_quoted(&t); if(v) items[in++]=v; } else break; } if(in>0){ char **ci = malloc(sizeof(char*)*in); for(size_t ii=0;ii<in;++ii) ci[ii]=items[ii]; add_array(name,ci,in); free(ci); for(size_t ii=0;ii<in;++ii) free(items[ii]); } } }

    else if (strncmp(s, "list", 4)==0 && (s[4]==' '||s[4]=='\t')){ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\t') ++q; size_t i=0; while(*q && *q!=' ' && *q!='=' && *q!='(' && i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char *items[128]; size_t in=0; while(t<cp && in<128){ while(*t==' '||*t==','||*t=='\t') ++t; if(*t=='\"'){ char *v=read_quoted(&t); if(v) items[in++]=v; } else break; } if(in>0){ char **ci=malloc(sizeof(char*)*in); for(size_t ii=0;ii<in;++ii) ci[ii]=items[ii]; add_list(name,ci,in); free(ci); for(size_t ii=0;ii<in;++ii) free(items[ii]); } } }

    else if (strncmp(s, "func",4)==0 && (s[4]==' '||s[4]=='\t')){ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\t') ++q; size_t i=0; while(*q && *q!=' ' && *q!='=' && *q!='(' && i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ char num[64]={0}; size_t ln=(size_t)(cp-op-1); if(ln<sizeof(num)){ memcpy(num, op+1, ln); num[ln]=0; long v = atol(num); add_func(name, v); } } }

    else if (strchr(s,'{')){ const char *lb=strchr(s,'{'); const char *rb=strchr(s,'}'); if(lb&&rb&&rb>lb){ const char *t=lb+1; char *keys[128]; long vals[128]; size_t kn=0; while(t<rb && kn<128){ while(*t==' '||*t==','||*t=='\t') ++t; if(*t=='\"'){ char *k=read_quoted(&t); while(*t==' '||*t=='\t') ++t; if(*t==':') ++t; while(*t==' '||*t=='\t') ++t; char num[64]={0}; size_t ni=0; while(*t && *t!=',' && *t!='}') { if(ni+1<sizeof(num)) num[ni++]=*t; ++t; } num[ni]=0; long v=atol(num); keys[kn]=k; vals[kn]=v; kn++; } else break; } if(kn>0){ char **ck = malloc(sizeof(char*)*kn); for(size_t ii=0;ii<kn;++ii) ck[ii]=keys[ii]; add_hash("H", ck, vals, kn); free(ck); for(size_t ii=0;ii<kn;++ii) free(keys[ii]); } } }

    else { /* handle assignments with => or >- */
        /* find => or >- */
        const char *p_op = strstr(s, "=>");
        const char *p_op2 = strstr(s, ">-");
        if (p_op || p_op2) {
            const char *op = p_op ? p_op : p_op2;
            size_t lhs_len = (size_t)(op - s);
            char *lhs = malloc(lhs_len+1); if(!lhs) { free(line); p = semi+1; continue; }
            memcpy(lhs, s, lhs_len); lhs[lhs_len] = 0; /* trim */
            char *ltrim = lhs; while(*ltrim && isspace((unsigned char)*ltrim)) ltrim++; char *rend = ltrim + strlen(ltrim)-1; while(rend>ltrim && isspace((unsigned char)*rend)) *rend--=0;
            const char *rstart = op + (p_op ? 2 : 2); /* both ops length 2 */
            while(*rstart && isspace((unsigned char)*rstart)) rstart++; /* extract rhs until end */
            char *rhs = strdup(rstart); if(!rhs){ free(lhs); free(line); p = semi+1; continue; } /* trim trailing spaces */
            char *r = rhs + strlen(rhs) - 1; while(r>rhs && isspace((unsigned char)*r)) *r--=0;
            const char *opstr = p_op ? "=>" : ">-";
            /* record binding */
            add_binding(ltrim, opstr, rhs);
            free(lhs); free(rhs);
        } else { /* maybe puts or other call handled below */ }
    }

    /* calls like puts(X); */
    if (strncmp(s, "puts", 4)==0){ const char *op = strchr(s, '('); const char *cp = strchr(s, ')'); if(op&&cp&&cp>op){ const char *t = op+1; while(*t && isspace((unsigned char)*t)) ++t; char id[256]={0}; size_t ii=0; while(*t && (isalnum((unsigned char)*t) || *t=='_' || *t==':' ) && ii+1<sizeof(id)) id[ii++]=*t++; id[ii]=0; if(ii>0) { if(!print_by_name(id)) printf("%s\n", id); } } }

    free(line); p = semi + 1; } }

int omega_eval_content(const char *content){ if(!content) return 1; parse_build(content); return 0; }
