/* lib/db.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_finance.h"

int ensure_dir_local(const char *d){ char cmd[1024]; snprintf(cmd,sizeof cmd,"mkdir -p %s", d); return system(cmd); }
int db_store_day(const char *date, const char *json_line){ if(!date||!json_line) return -1; ensure_dir_local("data/db"); char path[1024]; snprintf(path,sizeof path,"data/db/%s.jsonl", date); FILE *f = fopen(path, "a"); if(!f) return -1; fprintf(f, "%s\n", json_line); fclose(f); return 0; }
