/* lib/predict.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_finance.h"

/* Very small loader: read last N prices for symbol from data/raw.csv scanning file (inefficient but simple) */
static int load_last_prices(const char *symbol, double *out, int maxn){ FILE *f = fopen("data/raw.csv","r"); if(!f) return 0; char line[1024]; double tmp[1024]; int cnt=0; while(fgets(line,sizeof line,f)){ char date[64], sym[128]; double price; if(sscanf(line, "%63[^,],%127[^,],%lf", date, sym, &price) != 3) continue; if(strcmp(sym, symbol)==0){ if(cnt<1024) tmp[cnt++]=price; } }
    fclose(f);
    int n = cnt<maxn?cnt:maxn; for(int i=0;i<n;i++) out[i]= tmp[cnt - n + i]; return n; }

/* simple linear regression on last n points (x=0..n-1), predict days_ahead ahead */
double predict_next_linear(const char *symbol, int days_ahead){ if(!symbol) return 0.0; int MAX=30; double buf[30]; int n = load_last_prices(symbol, buf, MAX); if(n<2) return (n==1)?buf[0]:0.0; double sx=0, sy=0, sxx=0, sxy=0; for(int i=0;i<n;i++){ double x=i; sx+=x; sy+=buf[i]; sxx+=x*x; sxy+=x*buf[i]; }
    double denom = n*sxx - sx*sx; if(fabs(denom) < 1e-12) return buf[n-1]; double a = (n*sxy - sx*sy)/denom; double b = (sy - a*sx)/n; double pred = a*(n-1 + days_ahead) + b; return pred; }

/* moving average predictor */
double predict_ma(const char *symbol, int window){ double buf[30]; int n = load_last_prices(symbol, buf, window); if(n==0) return 0.0; double s=0; for(int i=0;i<n;i++) s+=buf[i]; return s/n; }
