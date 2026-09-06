/* interpreter.c - stub interpreter for Omega (generated) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void usage(const char *p){ fprintf(stderr, "Usage: %s <source.omega|.bc>\n", p); }

int main(int argc, char **argv){
    if(argc<2){ usage(argv[0]); return 1; }
    FILE *f = fopen(argv[1], "r"); if(!f){ perror("fopen"); return 2; }
    char line[4096]; int ln=0;
    while(fgets(line,sizeof(line),f)){
        ln++; char *nl = strchr(line,'\n'); if(nl) *nl=0;
        if(line[0]==0) continue;
        printf("[%03d] TRACE: %s\n", ln, line);
    }
    fclose(f);
    return 0;
}

