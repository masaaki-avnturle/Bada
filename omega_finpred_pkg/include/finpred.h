#ifndef FINPRED_H
#define FINPRED_H
/*
 * omega_finpred_pkg — public API.
 *
 *  - finpred_ingest_csv():   ingest a CSV (date,symbol,price), compute the
 *                            complex transform zeta(x)=i*sin(i*x*log(x)) per
 *                            price, and save a per-symbol series under
 *                            data/<symbol>.csv  (date,price,zeta_re,zeta_im).
 *  - finpred_transform_csv(): print the zeta transform of each row to stdout.
 *  - finpred_predict():      simple moving-average forecast over the last
 *                            `window` prices of data/<symbol>.csv. Returns NaN
 *                            when there is no usable data.
 */
int    finpred_ingest_csv(const char *path);
int    finpred_transform_csv(const char *path);
double finpred_predict(const char *symbol, int window);

#endif /* FINPRED_H */
