/* include/omega_finance.h */
#ifndef OMEGA_FINANCE_H
#define OMEGA_FINANCE_H

/* Data IO */
int load_prices_csv(const char *csv_path);

/* Transform */
double zeta_like_transform(double x); /* z(x) = i*sin(i*x*log(x)) -> numeric (real part handled via identity) */

/* ID mapping */
char *text_to_id(const char *text); /* caller frees */

/* DB */
int db_store_day(const char *date, const char *json_line);

/* Predict */
double predict_next_linear(const char *symbol, int days_ahead);

/* Interpreter */
int omega_interp(const char *script);

#endif
