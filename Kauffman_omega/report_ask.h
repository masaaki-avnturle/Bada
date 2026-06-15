#ifndef REPORT_ASK_H
#define REPORT_ASK_H
/*
 * report_ask.h — declarations for the report.ask generator whose main() lives
 * in equation.c. The helper routines are provided by the host program; this
 * header supplies their prototypes and the tuning constants so equation.c can
 * be compiled on its own.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>   /* strcasecmp */

#ifndef BUF_CHUNK
#define BUF_CHUNK 4096
#endif
#ifndef MAX_PARAS
#define MAX_PARAS 256
#endif
#ifndef TOPK
#define TOPK 5
#endif

/* I/O + acquisition helpers. */
char  *read_file(const char *path);
char  *fetch_url(const char *url);
char  *pdf_to_text(const char *path);
int    file_exists(const char *path);

/* Text analysis helpers. */
double shannon_entropy(const unsigned char *data, size_t len);
double pseudo_spectral(const unsigned char *data, size_t len);
int    extract_paragraphs(const char *text, char **paras, int max);
int    is_candidate_para(const char *para);
double sim_score(double Hq, double Ht, double Sq, double St);
int    detect_concepts(const char *question, char concepts[][128], int max);

#endif /* REPORT_ASK_H */
