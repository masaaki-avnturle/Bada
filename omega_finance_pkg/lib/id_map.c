/* lib/id_map.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "../include/omega_finance.h"

static unsigned long long fnv1a_64(const unsigned char *s){
    unsigned long long h = 1469598103934665603ULL;
    while(*s){ h ^= (unsigned long long)(*s++); h *= 1099511628211ULL; }
    return h;
}
char *text_to_id(const char *text){ if(!text) return NULL; unsigned long long h = fnv1a_64((const unsigned char*)text); char *out = malloc(32); if(!out) return NULL; snprintf(out,32,"ID-%016llx", (unsigned long long)h); return out; }
