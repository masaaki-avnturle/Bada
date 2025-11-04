/* lib/omega_interp.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_finance.h"

/* commands:
   ingest <csv_path>
   analyze_day <date>
   predict <symbol> [days]
*/
int omega_interp(const char *script){ if(!script) return -1; char cmd[128], arg1[512], arg2[128]; int got = sscanf(script, "%127s %511s %127s", cmd, arg1, arg2);
    if(got>=2 && strcmp(cmd, "ingest")==0){ if(load_prices_csv(arg1)==0){ printf("ingested %s\n", arg1); return 0; } else { printf("ingest failed\n"); return 2; } }
    if(got>=2 && strcmp(cmd, "predict")==0){ int days = (got>=3)?atoi(arg2):1; double v = predict_next_linear(arg1, days); printf("predict %s +%d -> %g\n", arg1, days, v); return 0; }
    if(got>=2 && strcmp(cmd, "analyze_day")==0){ /* build per-day db from raw.csv for this date */
        FILE *f = fopen("data/raw.csv","r"); if(!f){ printf("no data\n"); return 2; }
        char line[1024]; while(fgets(line,sizeof line,f)){
            char date[64], sym[128]; double price; if(sscanf(line, "%63[^,],%127[^,],%lf", date, sym, &price)!=3) continue; if(strcmp(date, arg1)==0){ /* compute transform & id & store */ char buf[256]; double z = zeta_like_transform(price); char txt[256]; snprintf(txt, sizeof txt, "%s,%s,%g,%g", date, sym, price, z); char *id = text_to_id(txt); snprintf(buf, sizeof buf, "{\"date\":\"%s\",\"sym\":\"%s\",\"price\":%g,\"z\":%g,\"id\":\"%s\"}", date, sym, price, z, id); db_store_day(date, buf); free(id); }
        }
        fclose(f); printf("analyze_day %s done\n", arg1); return 0; }
    printf("unknown command\n"); return -1; }
