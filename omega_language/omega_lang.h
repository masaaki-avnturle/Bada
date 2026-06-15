#ifndef OMEGA_LANG_H
#define OMEGA_LANG_H
/*
 * omega_lang.h — lexer/parser surface shared with the standalone lex_lang.c
 * source. The full implementation lives in t.c; this header declares just the
 * types and helper functions that the extracted lex_next / parse_primary
 * routines depend on, so they can be compiled on their own.
 */
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

typedef enum {
    TK_EOF, TK_NUM, TK_STR, TK_IDENT,
    TK_PLUS, TK_MINUS, TK_MUL, TK_DIV,
    TK_LP, TK_RP, TK_COMMA, TK_ASSIGN
} TokType;

typedef struct { TokType type; char *s; double num; } Token;
typedef struct { const char *src; int pos; Token cur; } Lexer;

typedef enum { EX_NUM, EX_STR, EX_IDENT, EX_BIN, EX_CALL, EX_ASSIGN } ExType;
typedef struct Ex Ex;            /* opaque expression node */

typedef struct { Lexer *lx; } Parser;

/* Memory + lexer helpers implemented by the host interpreter (t.c). */
void *xmalloc(size_t n);
void *xrealloc(void *p, size_t n);
char *xstrdup_safe(const char *s);
int   is_ident_char(int c);
void  token_set_str(Token *t, TokType ty, const char *s);

/* Parser entry point + expression-node constructors. */
Ex *parse_expr(Parser *p);
Ex *ex_new_num(double n);
Ex *ex_new_str(const char *s);
Ex *ex_new_ident(const char *name);
Ex *ex_new_assign(const char *name, Ex *rhs);
Ex *ex_new_call(Ex *fn, Ex **args, int nargs);

#endif /* OMEGA_LANG_H */
