#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega.h"
static char *read_all(const char *p){ if(!p) return NULL; FILE *f = fopen(p, "rb"); if(!f) return NULL; if(fseek(f,0,SEEK_END) != 0){ fclose(f); return NULL; } long s = ftell(f); if(s < 0){ fclose(f); return NULL; } rewind(f); char *b = malloc((size_t)s + 1); if(!b){ fclose(f); return NULL; } size_t r = fread(b, 1, (size_t)s, f); b[r] = '\0'; fclose(f); return b; }
int parse_and_run(const char *path){ char *c = read_all(path); if(!c){ fprintf(stderr, "[parser] cannot read %s\n", path); return 1; } printf("[parser] read %zu bytes from %s\n", strlen(c), path); int rc = omega_eval_content(c); free(c); return rc; }
