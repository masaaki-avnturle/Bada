/* lib/markov.c - tiny markov stub */
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "../include/omega_langnet.h"

struct markov_t { int n; };
markov_t *markov_create(int n){ if(n<=0) n=2; markov_t *m=(markov_t*)malloc(sizeof(markov_t)); if(!m) return NULL; m->n=n; return m; }
void markov_free(markov_t *m){ free(m); }
void markov_add_sequence(markov_t *m,const char *seq){ (void)m; (void)seq; }
char *markov_generate(markov_t *m,int maxlen){ (void)m; if(maxlen<=0) maxlen=80; char *s=(char*)malloc((size_t)maxlen+1); if(!s) return NULL; for(int i=0;i<maxlen;i++) s[i]='a'+(rand()%26); s[maxlen]='\0'; return s; }
