/* lib/bnf.c - minimal BNF parser stub */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_langnet.h"

int bnf_parse_file(const char *path,const char *out_json){
  if(!path||!out_json) return -1;
  FILE *f=fopen(path,"r"); if(!f) return -1;
  FILE *o=fopen(out_json,"w"); if(!o){ fclose(f); return -1; }
  fprintf(o,"{\"bnf_file\":\"%s\",\"rules_preview\":[",path);
  char line[1024]; int first=1;
  while(fgets(line,sizeof(line),f)){
    char *p=line; while(*p && (*p==' '||*p=='\t')) ++p;
    if(*p=='\0' || *p=='#') continue;
    if(!first) fprintf(o,","); first=0;
    for(char *q=p; *q && *q!='\n' && *q!='\r'; ++q){ if(*q=='\"') fputc('\\', o); fputc(*q, o); }
  }
  fprintf(o,"]}\n"); fclose(f); fclose(o); return 0;
}
