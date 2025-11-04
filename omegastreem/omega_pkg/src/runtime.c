/* runtime.c - extended runtime with builtins */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "../include/omega.h"
#if !defined(_WIN32) && !defined(_WIN64)
#include <time.h>
#include <regex.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <unistd.h>
#endif

typedef struct StrNode { char *s; struct StrNode *next; } StrNode;
typedef struct ArrayObj { char *name; StrNode *items; struct ArrayObj *next; } ArrayObj;
typedef struct ListObj  { char *name; StrNode *items; struct ListObj *next; } ListObj;
typedef struct FuncObj  { char *name; long data; struct FuncObj *next; } FuncObj;
typedef struct HashPair { char *k; long v; struct HashPair *next; } HashPair;
typedef struct HashObj  { char *name; HashPair *pairs; struct HashObj *next; } HashObj;

static ArrayObj *arrays = NULL; static ListObj *lists = NULL; static FuncObj *funcs = NULL; static HashObj *hashes = NULL;
static int report_mode = 0;
int omega_report_only(void) { report_mode = 1; return 0; }

static char *dupstr(const char *s){ if(!s) return NULL; size_t n=strlen(s)+1; char *r=malloc(n); if(r) memcpy(r,s,n); return r; }
static void push_str(StrNode **root, char *s){ StrNode *n=malloc(sizeof(*n)); if(!n) return; n->s=s; n->next=*root; *root=n; }
static void reverse_strlist(StrNode **root){ StrNode *r=NULL; StrNode *it=*root; while(it){ StrNode *nx=it->next; it->next=r; r=it; it=nx; } *root=r; }

static void add_array(const char *name, char **items, size_t n){ ArrayObj *a=malloc(sizeof(*a)); if(!a) return; a->name=dupstr(name); a->items=NULL; a->next=arrays; arrays=a; for(size_t i=0;i<n;i++) push_str(&a->items, dupstr(items[i])); reverse_strlist(&a->items); }
static void add_list(const char *name, char **items, size_t n){ ListObj *l=malloc(sizeof(*l)); if(!l) return; l->name=dupstr(name); l->items=NULL; l->next=lists; lists=l; for(size_t i=0;i<n;i++) push_str(&l->items, dupstr(items[i])); reverse_strlist(&l->items); }
static void add_func(const char *name, long v){ FuncObj *f=malloc(sizeof(*f)); if(!f) return; f->name=dupstr(name); f->data=v; f->next=funcs; funcs=f; }
static void add_hash(const char *name, char **keys, long *vals, size_t n){ HashObj *h=malloc(sizeof(*h)); if(!h) return; h->name=dupstr(name); h->pairs=NULL; h->next=hashes; hashes=h; for(size_t i=0;i<n;i++){ HashPair *p=malloc(sizeof(*p)); if(!p) continue; p->k=dupstr(keys[i]); p->v=vals[i]; p->next=h->pairs; h->pairs=p; } /* preserve order */ HashPair *rev=NULL; HashPair *it=h->pairs; while(it){ HashPair *nx=it->next; it->next=rev; rev=it; it=nx; } h->pairs=rev; }

/* builtins */
static char *builtin_read_file(const char *path){ FILE *f=fopen(path,"rb"); if(!f) return NULL; if(fseek(f,0,SEEK_END)!=0){ fclose(f); return NULL; } long s=ftell(f); if(s<0){ fclose(f); return NULL; } rewind(f); char *b=malloc((size_t)s+1); if(!b){ fclose(f); return NULL; } size_t r=fread(b,1,(size_t)s,f); b[r]='\0'; fclose(f); return b; }
static int builtin_write_file(const char *path, const char *data){ FILE *f=fopen(path,"wb"); if(!f) return -1; size_t w=fwrite(data,1,strlen(data),f); fclose(f); return (w==strlen(data))?0: -1; }
#if !defined(_WIN32) && !defined(_WIN64)
static int builtin_regex_match(const char *pat, const char *s){ regex_t re; if(regcomp(&re, pat, REG_EXTENDED)!=0) return 0; int rc = (regexec(&re, s, 0, NULL, 0) == 0); regfree(&re); return rc; }
static int builtin_exec_cmd(const char *cmd){ int rc = system(cmd); return rc; }
static long builtin_now_seconds(void){ return (long)time(NULL); }
/* simple TCP connect/send/recv, returning socket fd or -1 */
static int builtin_net_connect(const char *host, const char *port){ struct addrinfo hints, *res, *rp; memset(&hints,0,sizeof(hints)); hints.ai_family=AF_INET; hints.ai_socktype=SOCK_STREAM; if(getaddrinfo(host, port, &hints, &res)!=0) return -1; int s=-1; for(rp=res; rp; rp=rp->ai_next){ s = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol); if(s==-1) continue; if(connect(s, rp->ai_addr, rp->ai_addrlen)==0) break; close(s); s=-1; } freeaddrinfo(res); return s; }
static int builtin_net_send(int fd, const char *data){ ssize_t n = send(fd, data, strlen(data), 0); return (n>=0)?(int)n:-1; }
static char *builtin_net_recv(int fd, size_t maxlen){ char *buf = malloc(maxlen+1); if(!buf) return NULL; ssize_t n = recv(fd, buf, maxlen, 0); if(n<=0){ free(buf); return NULL; } buf[n]='\0'; return buf; }
#endif

/* read quoted string starting at '"' and advance p */static char *read_quoted(const char **pp){ const char *p=*pp; while(*p && *p!='"' ) ++p; if(!*p) return NULL; p++; size_t cap=64; char *buf=malloc(cap); if(!buf) return NULL; size_t n=0; while(*p && *p!='"'){ char c=*p++; if(c=='\\' && *p){ char e=*p++; if(e=='n') c='\n'; else if(e=='t') c='\t'; else c=e; } if(n+1>=cap){ cap*=2; char *t=realloc(buf,cap); if(!t){ free(buf); return NULL; } buf=t; } buf[n++]=c; } buf[n]=0; if(*p=='"') ++p; *pp=p; return buf; }
/* print object specified by name only */
static int print_object_by_name(const char *name){ for(ArrayObj *a=arrays;a;a=a->next){ if(a->name && strcmp(a->name,name)==0){ putchar('['); StrNode *it=a->items; int first=1; while(it){ if(!first) putchar(','); printf("\"%s\"", it->s); first=0; it=it->next; } puts("]"); return 1; } }
 for(HashObj *h=hashes;h;h=h->next){ if(h->name && strcmp(h->name,name)==0){ putchar('{'); HashPair *hp=h->pairs; int first=1; while(hp){ if(!first) putchar(','); printf("\"%s\":%ld", hp->k, hp->v); first=0; hp=hp->next; } puts("}"); return 1; } }
 for(ListObj *l=lists;l;l=l->next){ if(l->name && strcmp(l->name,name)==0){ putchar('('); StrNode *it=l->items; int first=1; while(it){ if(!first) putchar(','); printf("\"%s\"", it->s); first=0; it=it->next; } puts(")"); return 1; } }
 for(FuncObj *f=funcs;f;f=f->next){ if(f->name && strcmp(f->name,name)==0){ printf("%ld\n", f->data); return 1; } }
 return 0; }

/* parse minimal script (very simple; statements end with ';') */
static void parse_build(const char *content){ const char *p=content; while(*p){ const char *semi=strchr(p,';'); if(!semi) break; size_t len = (size_t)(semi - p); char *line = malloc(len+1); if(!line) break; memcpy(line,p,len); line[len]=0; char *s=line; while(*s==' '||*s=='\t'||*s=='\n'||*s=='\r') ++s;
    if (strncmp(s, "let", 3)==0 || strncmp(s, "array",5)==0 || strncmp(s, "list",4)==0 || strncmp(s, "hash",4)==0 || strncmp(s, "func",4)==0){
        /* handle declarations */
        if (strncmp(s, "array",5)==0){ /* array NAME = [ "a","b" ] */ char name[128]={0}; const char *q=s+5; while(*q==' '||*q=='\t')++q; size_t i=0; while(*q && *q!=' '&&*q!='='&&*q!='['&&i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *lb=strchr(s,'['); const char *rb=strchr(s,']'); if(lb&&rb&&rb>lb){ const char *t=lb+1; char *items[64]; size_t in=0; while(t<rb&&in<64){ while(*t==' '||*t==','||*t=='\t')++t; if(*t=='"'){ char *v=read_quoted(&t); if(v) items[in++]=v; } else break; } if(in>0){ char **ci=malloc(sizeof(char*)*in); for(size_t ii=0;ii<in;++ii) ci[ii]=items[ii]; add_array(name,ci,in); free(ci); } } }
        else if (strncmp(s, "list",4)==0){ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\t')++q; size_t i=0; while(*q && *q!=' '&&*q!='='&&*q!='('&&i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char *items[64]; size_t in=0; while(t<cp&&in<64){ while(*t==' '||*t==','||*t=='\t')++t; if(*t=='"'){ char *v=read_quoted(&t); if(v) items[in++]=v; } else break; } if(in>0){ char **ci=malloc(sizeof(char*)*in); for(size_t ii=0;ii<in;++ii) ci[ii]=items[ii]; add_list(name,ci,in); free(ci); } } }
        else if (strncmp(s, "func",4)==0){ /* func NAME = func(NUM) or let F = func(100) */ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\t')++q; size_t i=0; while(*q && *q!=' '&&*q!='='&&*q!='('&&i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ char numbuf[64]={0}; size_t ln=(size_t)(cp-op-1); if(ln<sizeof(numbuf)){ memcpy(numbuf, op+1, ln); numbuf[ln]=0; long v = atol(numbuf); add_func(name, v); } } }
        else if (strncmp(s, "hash",4)==0){ /* hash NAME = { "k":1, "k2":2 } */ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\t')++q; size_t i=0; while(*q && *q!=' '&&*q!='='&&*q!='{'&&i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *lb=strchr(s,'{'); const char *rb=strchr(s,'}'); if(lb&&rb&&rb>lb){ const char *t=lb+1; char *keys[64]; long vals[64]; size_t kn=0; while(t<rb&&kn<64){ while(*t==' '||*t==','||*t=='\t')++t; if(*t=='"'){ char *k=read_quoted(&t); while(*t==' '||*t=='\t')++t; if(*t==':') ++t; while(*t==' '||*t=='\t')++t; char num[64]={0}; size_t ni=0; while(*t && *t!=',' && *t!='}') { if(ni+1<sizeof(num)) num[ni++]=*t; ++t; } num[ni]=0; long v=atol(num); keys[kn]=k; vals[kn]=v; kn++; } else break; } if(kn>0){ char **ck=malloc(sizeof(char*)*kn); for(size_t ii=0;ii<kn;++ii) ck[ii]=keys[ii]; add_hash(name, ck, vals, kn); free(ck); for(size_t ii=0;ii<kn;++ii) free(keys[ii]); } } }
    }
    else {
        /* calls and builtins: puts(NAME); read_file(path); write_file(path, data); regex_match(pat,s); exec_cmd(cmd); now(); net_connect(host,port); net_send(fd,data); net_recv(fd,max) */
        if (strncmp(s, "puts", 4)==0){ const char *op = strchr(s,'('); const char *cp = strchr(s,')'); if(op&&cp&&cp>op){ const char *t = op+1; while(*t==' '||*t=='\t') ++t; char id[128]={0}; size_t ii=0; while(*t && (( *t>='a'&&*t<='z')||(*t>='A'&&*t<='Z')||*t=='_'||(*t>='0'&&*t<='9')) && ii+1<sizeof(id)) id[ii++]=*t++; id[ii]=0; if(ii>0) print_object_by_name(id); } }
        else if (strncmp(s, "read_file",9)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; while(*t==' '||*t=='\t')++t; char *p = read_quoted(&t); if(p){ char *r=builtin_read_file(p); if(r){ puts(r); free(r); } free(p); } } }
        else if (strncmp(s, "write_file",10)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; while(*t==' '||*t=='\t')++t; char *p = read_quoted(&t); while(*t==','||*t==' '||*t=='\t')++t; char *d = read_quoted(&t); if(p&&d){ builtin_write_file(p,d); free(p); free(d); } } }
        else if (strncmp(s, "regex_match",11)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char *p = read_quoted(&t); while(*t==','||*t==' '||*t=='\t')++t; char *s2 = read_quoted(&t); if(p&&s2){ int m = builtin_regex_match(p,s2); printf("%d\n", m); free(p); free(s2); } } }
        else if (strncmp(s, "exec_cmd",8)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char *p = read_quoted(&t); if(p){ int rc=builtin_exec_cmd(p); printf("%d\n", rc); free(p); } } }
        else if (strncmp(s, "now",3)==0){ long v = builtin_now_seconds(); printf("%ld\n", v); }
        else if (strncmp(s, "net_connect",11)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char *h = read_quoted(&t); while(*t==','||*t==' '||*t=='\t')++t; char *pr = read_quoted(&t); if(h&&pr){ int fd = builtin_net_connect(h, pr); printf("%d\n", fd); if(h) free(h); if(pr) free(pr); } } }
        else if (strncmp(s, "net_send",8)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char numbuf[64]={0}; size_t ni=0; while(*t && (*t>='0'&&*t<='9') && ni+1<sizeof(numbuf)) numbuf[ni++]=*t++; numbuf[ni]=0; int fd = atoi(numbuf); while(*t==','||*t==' '||*t=='\t')++t; char *d = read_quoted(&t); if(d){ int snt = builtin_net_send(fd,d); printf("%d\n", snt); free(d); } } }
        else if (strncmp(s, "net_recv",8)==0){ const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char numbuf[64]={0}; size_t ni=0; while(*t && (*t>='0'&&*t<='9') && ni+1<sizeof(numbuf)) numbuf[ni++]=*t++; numbuf[ni]=0; int fd = atoi(numbuf); while(*t==','||*t==' '||*t=='\t')++t; char num2[32]={0}; size_t nj=0; while(*t && (*t>='0'&&*t<='9') && nj+1<sizeof(num2)) num2[nj++]=*t++; num2[nj]=0; size_t max = (size_t)atoi(num2); if(max==0) max=1024; char *r = builtin_net_recv(fd, max); if(r){ puts(r); free(r); } } }
    }
    free(line); p = semi + 1; } }

int omega_eval_content(const char *content){ if(!content) return 1; parse_build(content); return 0; }

