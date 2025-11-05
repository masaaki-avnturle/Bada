/* bin/tools.c - demo CLI */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_langnet.h"

int main(int argc,char **argv){
    printf("omega_langnet tools prototype\n");
    if (argc>1 && strcmp(argv[1],"--entropy")==0) {
        if (argc<3) { fprintf(stderr, "usage: %s --entropy TEXT\n", argv[0]); return 1; }
        double H = compute_entropy_from_text(argv[2]); printf("Entropy: %f\n", H); return 0;
    }
    if (argc>1 && strcmp(argv[1],"--bnf-parse")==0) {
        if (argc<4) { fprintf(stderr, "usage: %s --bnf-parse INFILE OUTJSON\n", argv[0]); return 1; }
        if (bnf_parse_file(argv[2], argv[3]) == 0) printf("bnf parsed -> %s\n", argv[3]); else printf("bnf parse failed\n"); return 0;
    }
    printf("Usage: %s [--entropy TEXT] [--bnf-parse INFILE OUTJSON]\n", argv[0]);
    return 0;
}
