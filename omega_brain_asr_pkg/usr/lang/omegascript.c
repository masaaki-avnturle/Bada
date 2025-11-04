/* omegascript.c - preview transcripts (safe parsing) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static char*rf(const char*p){ FILE*f=fopen(p,"rb"); if(!f)return NULL; fseek(f,0,SEEK_END); long s=ftell(f); fseek(f,0,SEEK_SET); char*b=malloc(s+1); if(!b){fclose(f);return NULL;} fread(b,1,s,f); b[s]=0; fclose(f); return b; }
int main(int argc,char**argv){ const char*dir="generated"; if(argc>1) dir=argv[1]; char path[512]; snprintf(path,sizeof(path),"%s/transcripts.txt",dir); char*p=rf(path); if(p){ printf("=== transcripts ===\n%s\n",p); free(p);} else printf("no transcripts\n"); return 0; }
