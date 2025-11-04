/* bnf_codegen - stub */
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv){ if(argc<3){ fprintf(stderr,"Usage: %s <bnf> <out.c>\n",argv[0]); return 1;} FILE *f=fopen(argv[1],"rb"); if(!f){ perror("open"); return 2; } fseek(f,0,SEEK_END); long s=ftell(f); rewind(f); char *b=malloc(s+1); fread(b,1,s,f); b[s]=0; fclose(f); FILE *o=fopen(argv[2],"wb"); if(!o){ free(b); return 3; } fprintf(o,"/* parser stub generated from %s */\n", argv[1]); fprintf(o,"/* grammar:\n%s\n*/\n", b); fclose(o); free(b); printf("generated %s\n", argv[2]); return 0; }
