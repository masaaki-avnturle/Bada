/* bin/finpred.c - small CLI to ingest CSV, compute transform, and predict */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "finpred.h"

static void usage(const char *p) {
    fprintf(stderr, "Usage: %s ingest input.csv\n", p);
    fprintf(stderr, "       %s transform input.csv\n", p);
    fprintf(stderr, "       %s predict SYMBOL window\n", p);
}

int main(int argc, char **argv) {
    if (argc < 2) { usage(argv[0]); return 1; }
    if (strcmp(argv[1], "ingest") == 0) {
        if (argc < 3) { usage(argv[0]); return 1; }
        if (finpred_ingest_csv(argv[2]) != 0) {
            fprintf(stderr, "ingest failed\n"); return 1;
        }
        return 0;
    } else if (strcmp(argv[1], "transform") == 0) {
        if (argc < 3) { usage(argv[0]); return 1; }
        if (finpred_transform_csv(argv[2]) != 0) { fprintf(stderr, "transform failed\n"); return 1; }
        return 0;
    } else if (strcmp(argv[1], "predict") == 0) {
        if (argc < 4) { usage(argv[0]); return 1; }
        const char *symbol = argv[2];
        int window = atoi(argv[3]); if (window <= 0) window = 5;
        double pred = finpred_predict(symbol, window);
        if (isnan(pred)) { fprintf(stderr, "prediction failed\n"); return 1; }
        printf("Prediction for %s (window=%d): %.6f\n", symbol, window, pred);
        return 0;
    }
    usage(argv[0]);
    return 1;
}
