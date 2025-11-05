/* include/omega_langnet.h - public headers */
#ifndef OMEGA_LANGNET_H
#define OMEGA_LANGNET_H

#include <stddef.h>

typedef struct { int degree; double *coeffs; } jones_poly_t;

jones_poly_t *jones_create(int degree);
void jones_free(jones_poly_t *p);
double jones_eval_real(const jones_poly_t *p, double x, double y);

typedef struct markov_t markov_t;
markov_t *markov_create(int n);
void markov_free(markov_t *m);
void markov_add_sequence(markov_t *m, const char *seq);
char *markov_generate(markov_t *m, int maxlen);

int bnf_parse_file(const char *path, const char *out_json);
double compute_entropy_from_text(const char *text);
int manifold_classify(const char *features_json, const char *out_label);

#endif
