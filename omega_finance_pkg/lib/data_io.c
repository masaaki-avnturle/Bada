/* lib/data_io.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_finance.h"

/* Very small in-memory store: a flat file in data/raw.csv is appended */
int load_prices_csv(const char *csv_path){
    if(!csv_path) return -1;
    FILE *in = fopen(csv_path, "r"); if(!in) return -1;
    FILE *out = fopen("data/raw.csv", "a"); if(!out){ fclose(in); return -1; }
    char line[1024]; while(fgets(line, sizeof line, in)){
        fputs(line, out);
    }
    fclose(in); fclose(out);
    return 0;
}
