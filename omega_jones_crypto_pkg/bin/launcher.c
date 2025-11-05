#include <stdio.h>
#include <stdlib.h>
int omega_interp(const char*);
int main(int argc, char **argv){ if(argc<2){ fprintf(stderr, "Usage: %s <script...>\nExample: %s \"encrypt examples/trefoil.txt secret.txt secret.enc\"\n", argv[0], argv[0]); return 1; } char script[1024]; script[0]=0; for(int i=1;i<argc;i++){ if(i>1) strcat(script, " "); strcat(script, argv[i]); } return omega_interp(script); }
