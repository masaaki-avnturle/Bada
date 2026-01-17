/* compiler.c - stub tokenizer-based compiler for Omega (generated) */
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

static void usage(const char *p){ fprintf(stderr, "Usage: %s <source.omega>\n", p); }

int main(int argc, char **argv){
    if(argc<2){ usage(argv[0]); return 1; }
    FILE *f = fopen(argv[1], "r"); if(!f){ perror("fopen"); return 2; }
    char outname[512]; snprintf(outname, sizeof(outname), "%s.bc", argv[1]);
    FILE *out = fopen(outname, "w"); if(!out){ perror("fopen out"); fclose(f); return 3; }
    int c; char tok[1024]; size_t i=0;
    while((c=fgetc(f))!=EOF){
        if(isspace(c)){
            if(i){ tok[i]=0; fprintf(out, "%s\n", tok); i=0; }
            continue;
        }
        if(i+1<sizeof(tok)) tok[i++]=(char)c;
    }
    if(i){ tok[i]=0; fprintf(out, "%s\n", tok); }
    fclose(f); fclose(out);
    printf("Compiled '%s' -> '%s'\n", argv[1], outname);
    return 0;
}

