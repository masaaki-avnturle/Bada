/* lib/jones_key.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <openssl/sha.h>

typedef struct { int id; int e[4]; int sign; } Crossing;
static int load_diagram(const char *path, Crossing **out, int *n){ FILE *f=fopen(path,"r"); if(!f) return -1; Crossing *a=NULL; int cap=0,cnt=0; char buf[256]; while(fgets(buf,sizeof buf,f)){ char *s=buf; while(*s==' '||*s=='\t') s++; if(*s=='#'||*s=='\n'||*s=='\0') continue; int id,a0,a1,a2,a3,sg; if(sscanf(s,"%d %d %d %d %d %d",&id,&a0,&a1,&a2,&a3,&sg)<6) continue; if(cnt>=cap){ cap=cap?cap*2:16; a=realloc(a,sizeof(Crossing)*cap); } a[cnt].id=id; a[cnt].e[0]=a0; a[cnt].e[1]=a1; a[cnt].e[2]=a2; a[cnt].e[3]=a3; a[cnt].sign=(sg>=0)?1:-1; cnt++; } fclose(f); *out=a; *n=cnt; return 0; }

/* union-find */
typedef struct { int p; } UF;
static void uf_init(UF*u,int N){ for(int i=0;i<N;i++) u[i].p=-1; }
static int uf_find(UF*u,int a){ if(u[a].p<0) return a; u[a].p=uf_find(u,u[a].p); return u[a].p; }
static void uf_union(UF*u,int a,int b){ a=uf_find(u,a); b=uf_find(u,b); if(a==b) return; if(u[a].p < u[b].p){ u[a].p += u[b].p; u[b].p = a; } else { u[b].p += u[a].p; u[a].p = b; } }

static double compute_kauffman_bracket(Crossing *cross, int n, double A){ if(n==0) return 1.0; unsigned long long states = 1ULL<<n; double sum=0.0; int maxlbl=0; for(int i=0;i<n;i++) for(int k=0;k<4;k++) if(cross[i].e[k]>maxlbl) maxlbl=cross[i].e[k]; int U = maxlbl+1; UF *uf = malloc(sizeof(UF)*(U>0?U:1)); for(unsigned long long s=0;s<states;s++){ uf_init(uf,U); int a_cnt=0,b_cnt=0; for(int i=0;i<n;i++){ int bit=(s>>i)&1ULL; if(bit==0){ uf_union(uf,cross[i].e[0],cross[i].e[1]); uf_union(uf,cross[i].e[2],cross[i].e[3]); a_cnt++; } else { uf_union(uf,cross[i].e[1],cross[i].e[2]); uf_union(uf,cross[i].e[3],cross[i].e[0]); b_cnt++; } }
    int *seen = calloc(U,sizeof(int)); int loops=0; for(int lbl=0; lbl<U; ++lbl){ int r=uf_find(uf,lbl); if(!seen[r]){ seen[r]=1; loops++; } } free(seen);
    int exp = a_cnt - b_cnt; double weight = pow(A, exp); double d = -(A*A) - 1.0/(A*A); double loops_factor = pow(d, (loops>0?loops-1:0)); sum += weight * loops_factor; }
 free(uf); return sum; }

int derive_key_from_diagram(const char *diagram_path, unsigned char key_out[32]){
    Crossing *cs=NULL; int n=0; if(load_diagram(diagram_path,&cs,&n)!=0) return -1;
    /* Sample: evaluate bracket at several A values, collect numeric results */
    double samples[5]; double As[5] = {0.8, 1.0, 1.2, 1.5, 2.0}; for(int i=0;i<5;i++) samples[i] = compute_kauffman_bracket(cs, n, As[i]);
    free(cs);
    /* serialize doubles into buffer */
    unsigned char buf[5*32]; memset(buf,0,sizeof(buf)); for(int i=0;i<5;i++){ /* copy IEEE754 bytes */ double v = samples[i]; memcpy(buf + i*8, &v, sizeof(double)); }
    /* hash to 32 bytes */
    SHA256(buf, sizeof(buf), key_out);
    return 0; }
