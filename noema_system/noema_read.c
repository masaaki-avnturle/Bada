/*
 noema_full_with_llm_pdf.c

 Extended Noema-like language core (single-file prototype).
 - Interpreter mode:
     ./noema                 -> REPL
     ./noema inputfile       -> execute script file
 - Compile-to-C mode:
     ./noema -c inputfile outputfile.c
     Produces a C source file `outputfile.c` that embeds the script and
     uses the Noema runtime to execute it on startup.
 
 Build (Ubuntu/Debian):
   sudo apt-get install -y build-essential libcurl4-openssl-dev poppler-utils
   gcc -std=c11 -O2 -Wall noema_full_with_llm_pdf.c -o noema_full -lcurl -lm -pthread

 Notes:
  - OpenAI-style HTTP uses environment variable OPENAI_API_KEY and endpoint (default https://api.openai.com/v1/chat/completions).
  - Local llama.cpp wrapper expects an executable (default "./llama") and optional env LLM_MODEL_PATH.
  - PDF extraction uses `pdftotext` command (poppler-utils).
  - This is a prototype with minimal error handling; for production, improve JSON parsing, escaping, memory management, and security.
*/

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <regex.h>
#include <pthread.h>
#include <curl/curl.h>
#include <unistd.h>
#include <sys/wait.h>

/* -----------------------
   Value type definitions
   ----------------------- */

typedef enum {
	      VAL_NULL,
	      VAL_NUMBER,
	      VAL_STRING,
	      VAL_BOOL,
	      VAL_LIST,
	      VAL_HASH,
	      VAL_OBJECT,
	      VAL_FUNCTION,
    VAL_NATIVE_FN
} ValType;

struct Class;
struct Env;
struct Function;

typedef struct Value {
  ValType type;
  union {
    double number;
    char *string;
    int boolean;
    struct { struct Value **items; int len; } list;
    struct { char **keys; struct Value **vals; int len; } hash;
    struct { struct Class *klass; struct Value **fields; char **fkeys; int flen; } object;
    struct Function *fun;
    struct Value *(*native)(int, struct Value **);
  } as;
} Value;

/* Forward declarations */
typedef struct Token Token;
typedef struct ASTNode ASTNode;
static void value_free(Value *v);
static void value_print(Value *v);
static Value *make_null(void);
static Value *make_string(const char *s);

/* -----------------------
   Utility
   ----------------------- */
static char *xstrdup(const char *s) { if (!s) return NULL; char *r = malloc(strlen(s)+1); strcpy(r, s); return r; }

/* -----------------------
   Value constructors
   ----------------------- */
static Value *make_null() { Value *v = calloc(1, sizeof(Value)); v->type = VAL_NULL; return v; }
static Value *make_number(double d) { Value *v = calloc(1, sizeof(Value)); v->type = VAL_NUMBER; v->as.number = d; return v; }
static Value *make_bool(int b) { Value *v = calloc(1, sizeof(Value)); v->type = VAL_BOOL; v->as.boolean = b ? 1 : 0; return v; }
static Value *make_string(const char *s) { Value *v = calloc(1, sizeof(Value)); v->type = VAL_STRING; v->as.string = xstrdup(s ? s : ""); return v; }
static Value *make_list_empty() { Value *v = calloc(1, sizeof(Value)); v->type = VAL_LIST; v->as.list.items = NULL; v->as.list.len = 0; return v; }
static Value *make_hash_empty() { Value *v = calloc(1, sizeof(Value)); v->type = VAL_HASH; v->as.hash.keys = NULL; v->as.hash.vals = NULL; v->as.hash.len = 0; return v; }
static Value *make_native(Value *(*fn)(int, Value**)) { Value *v = calloc(1, sizeof(Value)); v->type = VAL_NATIVE_FN; v->as.native = fn; return v; }

/* -----------------------
   Collections helpers
   ----------------------- */
static void list_append(Value *lst, Value *item) {
  if (!lst || lst->type != VAL_LIST) return;
  int n = lst->as.list.len;
  lst->as.list.items = realloc(lst->as.list.items, sizeof(Value*)*(n+1));
  lst->as.list.items[n] = item;
  lst->as.list.len = n+1;
}
static void hash_set(Value *h, const char *key, Value *val) {
  if (!h || h->type != VAL_HASH) return;
  for (int i=0;i<h->as.hash.len;++i) if (strcmp(h->as.hash.keys[i], key) == 0) { value_free(h->as.hash.vals[i]); h->as.hash.vals[i] = val; return; }
  int n = h->as.hash.len;
  h->as.hash.keys = realloc(h->as.hash.keys, sizeof(char*)*(n+1));
  h->as.hash.vals = realloc(h->as.hash.vals, sizeof(Value*)*(n+1));
  h->as.hash.keys[n] = xstrdup(key);
  h->as.hash.vals[n] = val;
  h->as.hash.len = n+1;
}
static Value *hash_get(Value *h, const char *key) {
  if (!h || h->type != VAL_HASH) return NULL;
  for (int i=0;i<h->as.hash.len;++i) if (strcmp(h->as.hash.keys[i], key) == 0) return h->as.hash.vals[i];
  return NULL;
}

/* -----------------------
   Class & Object
   ----------------------- */
typedef struct Class {
  char *name;
  Value *methods; /* hash */
  struct Class *super;
} Class;

static Class *class_new(const char *name) {
  Class *c = malloc(sizeof(Class));
  c->name = xstrdup(name);
  c->methods = make_hash_empty();
  c->super = NULL;
  return c;
}

static Value *object_new(Class *klass) {
  Value *o = calloc(1, sizeof(Value));
  o->type = VAL_OBJECT;
  o->as.object.klass = klass;
  o->as.object.flen = 0;
  o->as.object.fields = NULL;
  o->as.object.fkeys = NULL;
  return o;
}

static void object_set_field(Value *obj, const char *k, Value *v) {
  if (!obj || obj->type != VAL_OBJECT) return;
  for (int i=0;i<obj->as.object.flen;++i) if (strcmp(obj->as.object.fkeys[i], k) == 0) { value_free(obj->as.object.fields[i]); obj->as.object.fields[i] = v; return; }
  int n = obj->as.object.flen;
  obj->as.object.fkeys = realloc(obj->as.object.fkeys, sizeof(char*)*(n+1));
  obj->as.object.fields = realloc(obj->as.object.fields, sizeof(Value*)*(n+1));
  obj->as.object.fkeys[n] = xstrdup(k);
  obj->as.object.fields[n] = v;
  obj->as.object.flen = n+1;
}

static Value *object_get_field(Value *obj, const char *k) {
  if (!obj || obj->type != VAL_OBJECT) return NULL;
  for (int i=0;i<obj->as.object.flen;++i) if (strcmp(obj->as.object.fkeys[i], k) == 0) return obj->as.object.fields[i];
  return NULL;
}
static Value *class_get_method(Class *c, const char *name) { if (!c) return NULL; return hash_get(c->methods, name); }

/* simple C map for classes */
typedef struct CClassMap { char *name; Class *klass; struct CClassMap *next; } CClassMap;
static CClassMap *class_map_head = NULL;
static void register_class_cmap(const char *name, Class *k) { CClassMap *n = malloc(sizeof(CClassMap)); n->name = xstrdup(name); n->klass = k; n->next = class_map_head; class_map_head = n; }
static Class *find_class_cmap(const char *name) { for (CClassMap *it=class_map_head; it; it=it->next) if (strcmp(it->name,name)==0) return it->klass; return NULL; }

/* -----------------------
   Function representation
   ----------------------- */
typedef struct Function {
  char *name;
  char **params;
  int param_count;
  ASTNode *body;
  struct Env *closure;
} Function;
static Value *make_function(Function *f) { Value *v = calloc(1,sizeof(Value)); v->type = VAL_FUNCTION; v->as.fun = f; return v; }

/* -----------------------
   Environment
   ----------------------- */
typedef struct Binding { char *name; Value *value; struct Binding *next; } Binding;
typedef struct Env { Binding *head; struct Env *parent; } Env;
static Env *env_new(Env *parent) { Env *e = calloc(1,sizeof(Env)); e->head = NULL; e->parent = parent; return e; }
static void env_set_local(Env *e, const char *name, Value *v) {
  for (Binding *b=e->head;b;b=b->next) if (strcmp(b->name,name)==0) { value_free(b->value); b->value = v; return; }
  Binding *nb = malloc(sizeof(Binding)); nb->name = xstrdup(name); nb->value = v; nb->next = e->head; e->head = nb;
}
static void env_set(Env *e, const char *name, Value *v) {
  for (Env *cur=e; cur; cur=cur->parent) for (Binding *b=cur->head;b;b=b->next) if (strcmp(b->name,name)==0) { value_free(b->value); b->value=v; return; }
  env_set_local(e, name, v);
}
static Value *env_get(Env *e, const char *name) { for (Env *cur=e; cur; cur=cur->parent) for (Binding *b=cur->head;b;b=b->next) if (strcmp(b->name,name)==0) return b->value; return NULL; }

/* -----------------------
   Lexer / Parser (compact)
   ----------------------- */

typedef enum { TOK_EOF, TOK_NUMBER, TOK_STRING, TOK_IDENT, TOK_KW_CLASS, TOK_KW_DEF, TOK_KW_RETURN, TOK_KW_IF, TOK_KW_ELSE, TOK_KW_WHILE, TOK_KW_NEW, TOK_TRUE, TOK_FALSE, TOK_NULL, TOK_SYMBOL } TokType;
struct Token { TokType type; char *text; };

typedef struct Lexer { const char *src; size_t pos; Token cur; } Lexer;
static void token_free(Token *t) { if (t && t->text) free(t->text); t->text = NULL; }
static int is_ident_start(char c) { return isalpha((unsigned char)c) || c == '_'; }
static int is_ident_part(char c) { return isalnum((unsigned char)c) || c == '_'; }
static void lexer_init(Lexer *lx, const char *s) { lx->src = s; lx->pos = 0; lx->cur.type = TOK_EOF; lx->cur.text = NULL; }
static void lexer_skip_ws(Lexer *lx) { const char *s = lx->src; while (s[lx->pos] && isspace((unsigned char)s[lx->pos])) lx->pos++; }

static Token lexer_next_token(Lexer *lx) {
  token_free(&lx->cur);
  lexer_skip_ws(lx);
  const char *s = lx->src;
  size_t p = lx->pos;
  if (!s[p]) { lx->cur.type = TOK_EOF; lx->cur.text = xstrdup(""); return lx->cur; }
  char c = s[p];
  if (isdigit((unsigned char)c) || (c=='.' && isdigit((unsigned char)s[p+1]))) {
    size_t start = p; while (isdigit((unsigned char)s[p])) p++; if (s[p]=='.') { p++; while (isdigit((unsigned char)s[p])) p++; }
    size_t len = p - start; char *num = malloc(len+1); memcpy(num, s+start, len); num[len]=0; lx->pos = p; lx->cur.type = TOK_NUMBER; lx->cur.text = num; return lx->cur;
  }
  if (c == '"' || c == '\'') {
    char q = c; p++; size_t bi = 0; char *buf = malloc(strlen(s)+1);
    while (s[p] && s[p] != q) {
      if (s[p]=='\\' && s[p+1]) { p++; char esc = s[p++]; if (esc=='n') buf[bi++]='\n'; else if (esc=='t') buf[bi++]='\t'; else buf[bi++]=esc; }
      else buf[bi++]=s[p++];
    }
    buf[bi]=0; if (s[p]==q) p++; lx->pos = p; lx->cur.type = TOK_STRING; lx->cur.text = buf; return lx->cur;
  }
  if (is_ident_start(c)) {
    size_t start=p; p++; while (is_ident_part(s[p])) p++; size_t len = p-start; char *id = malloc(len+1); memcpy(id, s+start, len); id[len]=0; lx->pos = p;
    if (strcmp(id,"class")==0) { free(id); lx->cur.type=TOK_KW_CLASS; lx->cur.text=xstrdup("class"); return lx->cur; }
    if (strcmp(id,"def")==0) { free(id); lx->cur.type=TOK_KW_DEF; lx->cur.text=xstrdup("def"); return lx->cur; }
    if (strcmp(id,"return")==0) { free(id); lx->cur.type=TOK_KW_RETURN; lx->cur.text=xstrdup("return"); return lx->cur; }
    if (strcmp(id,"if")==0) { free(id); lx->cur.type=TOK_KW_IF; lx->cur.text=xstrdup("if"); return lx->cur; }
    if (strcmp(id,"else")==0) { free(id); lx->cur.type=TOK_KW_ELSE; lx->cur.text=xstrdup("else"); return lx->cur; }
    if (strcmp(id,"while")==0) { free(id); lx->cur.type=TOK_KW_WHILE; lx->cur.text=xstrdup("while"); return lx->cur; }
    if (strcmp(id,"new")==0) { free(id); lx->cur.type=TOK_KW_NEW; lx->cur.text=xstrdup("new"); return lx->cur; }
    if (strcmp(id,"true")==0) { free(id); lx->cur.type=TOK_TRUE; lx->cur.text=xstrdup("true"); return lx->cur; }
    if (strcmp(id,"false")==0) { free(id); lx->cur.type=TOK_FALSE; lx->cur.text=xstrdup("false"); return lx->cur; }
    if (strcmp(id,"null")==0) { free(id); lx->cur.type=TOK_NULL; lx->cur.text=xstrdup("null"); return lx->cur; }
    lx->cur.type = TOK_IDENT; lx->cur.text = id; return lx->cur;
  }
  if ((c=='=' && s[p+1]=='=') || (c=='!' && s[p+1]=='=') || (c=='<' && s[p+1]=='=') || (c=='>' && s[p+1]=='=') || (c=='&' && s[p+1]=='&') || (c=='|' && s[p+1]=='|')) {
    char tmp[3] = {s[p], s[p+1], 0}; lx->pos = p+2; lx->cur.type = TOK_SYMBOL; lx->cur.text = xstrdup(tmp); return lx->cur;
  }
  char tmp[2] = {c,0}; lx->pos = p+1; lx->cur.type = TOK_SYMBOL; lx->cur.text = xstrdup(tmp); return lx->cur;
}

/* -----------------------
   AST
   ----------------------- */
typedef enum {
	      AST_STMT_BLOCK, AST_STMT_EXPR, AST_STMT_RETURN, AST_STMT_IF, AST_STMT_WHILE, AST_STMT_CLASS, AST_STMT_FUNCDEF,
	      AST_EXPR_NUMBER, AST_EXPR_STRING, AST_EXPR_BOOL, AST_EXPR_NULL, AST_EXPR_IDENT, AST_EXPR_LIST, AST_EXPR_HASH,
	      AST_EXPR_CALL, AST_EXPR_MEMBER, AST_EXPR_ASSIGN, AST_EXPR_BINARY, AST_EXPR_UNARY, AST_EXPR_NEW
} ASTKind;

struct ASTNode {
  ASTKind kind;
  char *name;
  ASTNode *left;
  ASTNode *right;
  ASTNode **items; int items_len;
  ASTNode *body;
  char **params; int param_count;
  ASTNode **stmts; int stmts_len;
  double number; char *string; int boolean; char *op;
};

static ASTNode *ast_new(ASTKind k) { ASTNode *n = calloc(1,sizeof(ASTNode)); n->kind = k; return n; }
static void ast_free(ASTNode *n) {
  if (!n) return;
  if (n->name) free(n->name);
  if (n->string) free(n->string);
  if (n->op) free(n->op);
  if (n->params) { for (int i=0;i<n->param_count;++i) free(n->params[i]); free(n->params); }
  if (n->items) { for (int i=0;i<n->items_len;++i) ast_free(n->items[i]); free(n->items); }
  if (n->stmts) { for (int i=0;i<n->stmts_len;++i) ast_free(n->stmts[i]); free(n->stmts); }
  if (n->body) ast_free(n->body);
  if (n->left) ast_free(n->left);
  if (n->right) ast_free(n->right);
  free(n);
}

/* -----------------------
   Parser (recursive descent minimal)
   ----------------------- */
typedef struct Parser { Lexer lx; Token cur; int have_cur; } Parser;
static void parser_init(Parser *p, const char *src) { lexer_init(&p->lx, src); p->have_cur = 0; p->cur.type = TOK_EOF; p->cur.text = NULL; }
static Token curtok(Parser *p) { if (p->have_cur) return p->cur; p->cur = lexer_next_token(&p->lx); p->have_cur = 1; return p->cur; }
static Token consume(Parser *p) { Token t = curtok(p); p->have_cur = 0; return t; }
static int match_symbol(Parser *p, const char *s) { Token t = curtok(p); if (t.type==TOK_SYMBOL && strcmp(t.text,s)==0) { consume(p); return 1; } return 0; }

static ASTNode *parse_program(Parser *p);
static ASTNode *parse_statement(Parser *p);
static ASTNode *parse_block(Parser *p);
static ASTNode *parse_expression(Parser *p);
static ASTNode *parse_assignment(Parser *p);
static ASTNode *parse_logic_or(Parser *p);
static ASTNode *parse_logic_and(Parser *p);
static ASTNode *parse_equality(Parser *p);
static ASTNode *parse_comparison(Parser *p);
static ASTNode *parse_term(Parser *p);
static ASTNode *parse_factor(Parser *p);
static ASTNode *parse_unary(Parser *p);
static ASTNode *parse_call(Parser *p);
static ASTNode *parse_primary(Parser *p);

static ASTNode *parse_program(Parser *p) {
  ASTNode *block = ast_new(AST_STMT_BLOCK); block->stmts = NULL; block->stmts_len = 0;
  while (1) {
    Token t = curtok(p);
    if (t.type == TOK_EOF) break;
    ASTNode *st = parse_statement(p);
    if (!st) break;
    block->stmts = realloc(block->stmts, sizeof(ASTNode*)*(block->stmts_len+1));
    block->stmts[block->stmts_len++] = st;
  }
  return block;
}

static ASTNode *parse_statement(Parser *p) {
  Token t = curtok(p);
  if (t.type == TOK_KW_CLASS) {
    consume(p);
    Token name = curtok(p); if (name.type != TOK_IDENT) { fprintf(stderr,"Expected class name\n"); return NULL; } consume(p);
    ASTNode *node = ast_new(AST_STMT_CLASS); node->name = xstrdup(name.text); Token b = curtok(p);
    if (!(b.type==TOK_SYMBOL && strcmp(b.text,"{")==0)) { fprintf(stderr,"Expected '{'\n"); return NULL; } consume(p);
    node->body = ast_new(AST_STMT_BLOCK); node->body->stmts = NULL; node->body->stmts_len = 0;
    while (1) {
      Token tt = curtok(p);
      if (tt.type==TOK_SYMBOL && strcmp(tt.text,"}")==0) { consume(p); break; }
      if (tt.type==TOK_KW_DEF) {
	consume(p);
	Token mname = curtok(p); if (mname.type!=TOK_IDENT) { fprintf(stderr,"Expected method name\n"); return NULL; } consume(p);
	Token l = curtok(p); if (!(l.type==TOK_SYMBOL && strcmp(l.text,"(")==0)) { fprintf(stderr,"Expected (\n"); return NULL; } consume(p);
	char **params = NULL; int pcount = 0; Token nx = curtok(p);
	while (!(nx.type==TOK_SYMBOL && strcmp(nx.text,")")==0)) {
	  if (nx.type==TOK_IDENT) { params = realloc(params,sizeof(char*)*(pcount+1)); params[pcount++]=xstrdup(nx.text); consume(p); nx=curtok(p); if (nx.type==TOK_SYMBOL && strcmp(nx.text,",")==0) { consume(p); nx=curtok(p); continue; } else continue; }
	  else { fprintf(stderr,"Expected param or )\n"); return NULL; }
	}
	consume(p);
	ASTNode *mbody = parse_block(p);
	ASTNode *fnode = ast_new(AST_STMT_FUNCDEF); fnode->name = xstrdup(mname.text); fnode->params = params; fnode->param_count = pcount; fnode->body = mbody;
	node->body->stmts = realloc(node->body->stmts, sizeof(ASTNode*)*(node->body->stmts_len+1));
	node->body->stmts[node->body->stmts_len++] = fnode;
	continue;
      } else { fprintf(stderr,"Unexpected token in class body: %s\n", tt.text?tt.text:"(null)"); consume(p); }
    }
    return node;
  } else if (t.type == TOK_KW_DEF) {
    consume(p);
    Token fname = curtok(p); if (fname.type != TOK_IDENT) { fprintf(stderr,"Expected function name\n"); return NULL; } consume(p);
    Token l = curtok(p); if (!(l.type==TOK_SYMBOL && strcmp(l.text,"(")==0)) { fprintf(stderr,"Expected (\n"); return NULL; } consume(p);
    char **params = NULL; int pcount = 0; Token nx = curtok(p);
    while (!(nx.type==TOK_SYMBOL && strcmp(nx.text,")")==0)) {
      if (nx.type==TOK_IDENT) { params = realloc(params,sizeof(char*)*(pcount+1)); params[pcount++]=xstrdup(nx.text); consume(p); nx=curtok(p); if (nx.type==TOK_SYMBOL && strcmp(nx.text,",")==0) { consume(p); nx=curtok(p); continue; } else continue; }
      else { fprintf(stderr,"Expected param or )\n"); return NULL; }
    }
    consume(p);
    ASTNode *body = parse_block(p);
    ASTNode *fn = ast_new(AST_STMT_FUNCDEF); fn->name = xstrdup(fname.text); fn->params = params; fn->param_count = pcount; fn->body = body;
    return fn;
  } else if (t.type == TOK_KW_RETURN) {
    consume(p); ASTNode *n = ast_new(AST_STMT_RETURN); n->left = parse_expression(p); Token s = curtok(p); if (s.type==TOK_SYMBOL && strcmp(s.text,";")==0) consume(p); return n;
  } else if (t.type == TOK_KW_IF) {
    consume(p); Token lp = curtok(p); if (!(lp.type==TOK_SYMBOL && strcmp(lp.text,"(")==0)) { fprintf(stderr,"Expected (\n"); return NULL; } consume(p);
    ASTNode *cond = parse_expression(p); Token rp = curtok(p); if (!(rp.type==TOK_SYMBOL && strcmp(rp.text,")")==0)) { fprintf(stderr,"Expected )\n"); return NULL; } consume(p);
    ASTNode *thenb = parse_block(p); ASTNode *n = ast_new(AST_STMT_IF); n->left = cond; n->body = thenb;
    Token el = curtok(p); if (el.type==TOK_KW_ELSE) { consume(p); ASTNode *elseb = parse_block(p); n->right = elseb; }
    return n;
  } else if (t.type == TOK_KW_WHILE) {
    consume(p); Token lp = curtok(p); if (!(lp.type==TOK_SYMBOL && strcmp(lp.text,"(")==0)) { fprintf(stderr,"Expected (\n"); return NULL; } consume(p);
    ASTNode *cond = parse_expression(p); Token rp = curtok(p); if (!(rp.type==TOK_SYMBOL && strcmp(rp.text,")")==0)) { fprintf(stderr,"Expected )\n"); return NULL; } consume(p);
    ASTNode *body = parse_block(p); ASTNode *n = ast_new(AST_STMT_WHILE); n->left = cond; n->body = body; return n;
  } else {
    ASTNode *e = parse_expression(p); Token s = curtok(p); if (s.type==TOK_SYMBOL && strcmp(s.text,";")==0) consume(p); ASTNode *stmt = ast_new(AST_STMT_EXPR); stmt->left = e; return stmt;
  }
}

static ASTNode *parse_block(Parser *p) {
  Token b = curtok(p); if (!(b.type==TOK_SYMBOL && strcmp(b.text,"{")==0)) { fprintf(stderr,"Expected '{'\n"); return NULL; } consume(p);
  ASTNode *blk = ast_new(AST_STMT_BLOCK); blk->stmts = NULL; blk->stmts_len = 0;
  while (1) {
    Token t = curtok(p); if (t.type==TOK_SYMBOL && strcmp(t.text,"}")==0) { consume(p); break; }
    ASTNode *st = parse_statement(p); if (!st) break;
    blk->stmts = realloc(blk->stmts, sizeof(ASTNode*)*(blk->stmts_len+1)); blk->stmts[blk->stmts_len++] = st;
  }
  return blk;
}

/* expression parsing (precedence) */
static ASTNode *parse_expression(Parser *p) { return parse_assignment(p); }

static ASTNode *parse_assignment(Parser *p) {
  ASTNode *lhs = parse_logic_or(p);
  Token t = curtok(p);
  if (t.type==TOK_SYMBOL && strcmp(t.text,"=")==0) { consume(p); ASTNode *rhs = parse_assignment(p); ASTNode *n = ast_new(AST_EXPR_ASSIGN); n->left = lhs; n->right = rhs; return n; }
  return lhs;
}

static ASTNode *parse_logic_or(Parser *p) {
  ASTNode *left = parse_logic_and(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && strcmp(t.text,"||")==0) { consume(p); ASTNode *r = parse_logic_and(p); ASTNode *n = ast_new(AST_EXPR_BINARY); n->op = xstrdup("||"); n->left = left; n->right = r; left = n; continue; }
    break;
  }
  return left;
}
static ASTNode *parse_logic_and(Parser *p) {
  ASTNode *left = parse_equality(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && strcmp(t.text,"&&")==0) { consume(p); ASTNode *r = parse_equality(p); ASTNode *n = ast_new(AST_EXPR_BINARY); n->op = xstrdup("&&"); n->left = left; n->right = r; left = n; continue; }
    break;
  }
  return left;
}
static ASTNode *parse_equality(Parser *p) {
  ASTNode *left = parse_comparison(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && (strcmp(t.text,"==")==0 || strcmp(t.text,"!=")==0)) { char *op=xstrdup(t.text); consume(p); ASTNode *r=parse_comparison(p); ASTNode *n=ast_new(AST_EXPR_BINARY); n->op=op; n->left=left; n->right=r; left=n; continue; }
    break;
  }
  return left;
}
static ASTNode *parse_comparison(Parser *p) {
  ASTNode *left = parse_term(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && (strcmp(t.text,"<")==0 || strcmp(t.text,">")==0 || strcmp(t.text,"<=")==0 || strcmp(t.text,">=")==0)) { char *op=xstrdup(t.text); consume(p); ASTNode *r=parse_term(p); ASTNode *n=ast_new(AST_EXPR_BINARY); n->op=op; n->left=left; n->right=r; left=n; continue; }
    break;
  }
  return left;
}
static ASTNode *parse_term(Parser *p) {
  ASTNode *left = parse_factor(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && (strcmp(t.text,"+")==0 || strcmp(t.text,"-")==0)) { char *op=xstrdup(t.text); consume(p); ASTNode *r=parse_factor(p); ASTNode *n=ast_new(AST_EXPR_BINARY); n->op=op; n->left=left; n->right=r; left=n; continue; }
    break;
  }
  return left;
}
static ASTNode *parse_factor(Parser *p) {
  ASTNode *left = parse_unary(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && (strcmp(t.text,"*")==0 || strcmp(t.text,"/")==0 || strcmp(t.text,"%")==0)) { char *op=xstrdup(t.text); consume(p); ASTNode *r=parse_unary(p); ASTNode *n=ast_new(AST_EXPR_BINARY); n->op=op; n->left=left; n->right=r; left=n; continue; }
    break;
  }
  return left;
}
static ASTNode *parse_unary(Parser *p) {
  Token t = curtok(p);
  if (t.type==TOK_SYMBOL && (strcmp(t.text,"!")==0 || strcmp(t.text,"-")==0)) { char *op=xstrdup(t.text); consume(p); ASTNode *r=parse_unary(p); ASTNode *n=ast_new(AST_EXPR_UNARY); n->op=op; n->left=r; return n; }
  return parse_call(p);
}
static ASTNode *parse_call(Parser *p) {
  ASTNode *primary = parse_primary(p);
  while (1) {
    Token t = curtok(p);
    if (t.type==TOK_SYMBOL && strcmp(t.text,"(")==0) {
      consume(p);
      ASTNode *call = ast_new(AST_EXPR_CALL); call->left = primary; call->items = NULL; call->items_len = 0;
      Token nx = curtok(p);
      while (!(nx.type==TOK_SYMBOL && strcmp(nx.text,")")==0)) {
	ASTNode *arg = parse_expression(p);
	call->items = realloc(call->items, sizeof(ASTNode*)*(call->items_len+1));
	call->items[call->items_len++] = arg;
	nx = curtok(p);
	if (nx.type==TOK_SYMBOL && strcmp(nx.text,",")==0) { consume(p); nx = curtok(p); continue; } else break;
      }
      Token rp = curtok(p); if (rp.type==TOK_SYMBOL && strcmp(rp.text,")")==0) consume(p);
      primary = call; continue;
    } else if (t.type==TOK_SYMBOL && strcmp(t.text,".")==0) {
      consume(p); Token id = curtok(p); if (id.type != TOK_IDENT) { fprintf(stderr,"Expected member ident\n"); return NULL; } consume(p);
      ASTNode *m = ast_new(AST_EXPR_MEMBER); m->left = primary; m->name = xstrdup(id.text); primary = m; continue;
    }
    break;
  }
  return primary;
}
static ASTNode *parse_primary(Parser *p) {
  Token t = curtok(p);
  if (t.type==TOK_NUMBER) { ASTNode *n=ast_new(AST_EXPR_NUMBER); n->number = atof(t.text); consume(p); return n; }
  if (t.type==TOK_STRING) { ASTNode *n=ast_new(AST_EXPR_STRING); n->string = xstrdup(t.text); consume(p); return n; }
  if (t.type==TOK_TRUE) { consume(p); ASTNode *n=ast_new(AST_EXPR_BOOL); n->boolean = 1; return n; }
  if (t.type==TOK_FALSE) { consume(p); ASTNode *n=ast_new(AST_EXPR_BOOL); n->boolean = 0; return n; }
  if (t.type==TOK_NULL) { consume(p); ASTNode *n=ast_new(AST_EXPR_NULL); return n; }
  if (t.type==TOK_IDENT) { ASTNode *n=ast_new(AST_EXPR_IDENT); n->name = xstrdup(t.text); consume(p); return n; }
  if (t.type==TOK_SYMBOL && strcmp(t.text,"[")==0) {
    consume(p); ASTNode *n=ast_new(AST_EXPR_LIST); n->items = NULL; n->items_len=0; Token nx = curtok(p);
    while (!(nx.type==TOK_SYMBOL && strcmp(nx.text,"]")==0)) {
      ASTNode *e = parse_expression(p);
      n->items = realloc(n->items, sizeof(ASTNode*)*(n->items_len+1)); n->items[n->items_len++] = e;
      nx = curtok(p); if (nx.type==TOK_SYMBOL && strcmp(nx.text,",")==0) { consume(p); nx = curtok(p); continue; }
	Token rb = curtok(p); if (rb.type==TOK_SYMBOL && strcmp(rb.text,"]")==0) consume(p);
      return n;
    }
    if (t.type==TOK_SYMBOL && strcmp(t.text,"{")==0) {
      consume(p);
      ASTNode *n = ast_new(AST_EXPR_HASH); n->items = NULL; n->items_len = 0;
      Token nx = curtok(p);
      while (!(nx.type==TOK_SYMBOL && strcmp(nx.text,"}")==0)) {
	Token key = curtok(p);
	if (!(key.type==TOK_STRING || key.type==TOK_IDENT)) { fprintf(stderr,"Expected key in hash\n"); return NULL; }
	consume(p);
	Token colon = curtok(p); if (!(colon.type==TOK_SYMBOL && strcmp(colon.text,":")==0)) { fprintf(stderr,"Expected : in hash\n"); return NULL; }
	consume(p);
	ASTNode *val = parse_expression(p);
	ASTNode *pair = ast_new(AST_STMT_EXPR); pair->name = xstrdup(key.text); pair->left = val;
	n->items = realloc(n->items, sizeof(ASTNode*)*(n->items_len+1)); n->items[n->items_len++] = pair;
	nx = curtok(p);
	if (nx.type==TOK_SYMBOL && strcmp(nx.text,",")==0) { consume(p); nx = curtok(p); continue; } else break;
      }
      Token rb = curtok(p); if (rb.type==TOK_SYMBOL && strcmp(rb.text,"}")==0) consume(p);
      return n;
    }
    if (t.type==TOK_SYMBOL && strcmp(t.text,"(")==0) { consume(p); ASTNode *n = parse_expression(p); Token r = curtok(p); if (r.type==TOK_SYMBOL && strcmp(r.text,")")==0) consume(p); return n; }
    if (t.type==TOK_KW_NEW) {
      consume(p);
      Token cname = curtok(p); if (cname.type!=TOK_IDENT) { fprintf(stderr,"Expected class name after new\n"); return NULL; } consume(p);
      Token l = curtok(p); if (!(l.type==TOK_SYMBOL && strcmp(l.text,"(")==0)) { fprintf(stderr,"Expected (\n"); return NULL; } consume(p);
      ASTNode *n = ast_new(AST_EXPR_NEW); n->name = xstrdup(cname.text); n->items = NULL; n->items_len = 0;
      Token nx = curtok(p);
      while (!(nx.type==TOK_SYMBOL && strcmp(nx.text,")")==0)) {
	ASTNode *a = parse_expression(p);
	n->items = realloc(n->items, sizeof(ASTNode*)*(n->items_len+1)); n->items[n->items_len++] = a;
	nx = curtok(p);
	if (nx.type==TOK_SYMBOL && strcmp(nx.text,",")==0) { consume(p); nx = curtok(p); continue; } else break;
      }
      Token rp = curtok(p); if (rp.type==TOK_SYMBOL && strcmp(rp.text,")")==0) consume(p);
      return n;
    }
    fprintf(stderr,"Unexpected token in primary: %s\n", t.text? t.text:"(null)");
    return NULL;
  }

  /* -----------------------
   評価器 / インタプリタ
   ----------------------- */

  /* 前方参照 (一部は上部で定義済み) */
  static Value *eval_node(ASTNode *n, Env *env);
  static Value **eval_args_from_nodes(ASTNode **items, int n, Env *env);
  static Env *root_env;

  /* call_function, eval_args_from_nodes, eval_binary, eval_unary, eval_node の実装
   — 前出と同一のロジックをここに含めます。長文のため主要部分を要約せずそのまま記述します。
  */

  static Value *call_function(Value *fnval, Value **args, int argc, Env *env_call) {
    if (!fnval) return make_null();
    if (fnval->type == VAL_NATIVE_FN) {
      return fnval->as.native(argc, args);
    } else if (fnval->type == VAL_FUNCTION) {
      Function *f = fnval->as.fun;
      Env *loc = env_new(f->closure ? f->closure : env_call);
      for (int i=0;i<f->param_count;++i) {
	Value *a = (i < argc) ? args[i] : make_null();
	env_set_local(loc, f->params[i], a);
      }
      Value *ret = make_null();
      if (!f->body) return ret;
      for (int i=0;i<f->body->stmts_len;++i) {
	ASTNode *st = f->body->stmts[i];
	Value *r = eval_node(st, loc);
	if (st->kind == AST_STMT_RETURN) { value_free(ret); ret = r; return ret; }
	value_free(r);
      }
      return ret;
    }
    return make_null();
  }

  static Value **eval_args_from_nodes(ASTNode **items, int n, Env *env) {
    if (n == 0) return NULL;
    Value **arr = malloc(sizeof(Value*) * n);
    for (int i = 0;i<n;++i) arr[i] = eval_node(items[i], env);
    return arr;
  }

  static Value *eval_binary(ASTNode *n, Env *env) {
    Value *l = eval_node(n->left, env);
    Value *r = eval_node(n->right, env);
    if (!l || !r) { if (l) value_free(l); if (r) value_free(r); return make_null(); }
    Value *res = make_null();
    if (strcmp(n->op, "+")==0) {
      if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_number(l->as.number + r->as.number);
      else {
	char tmpa[64], tmpb[64];
	const char *sa = (l->type==VAL_STRING)?l->as.string: (l->type==VAL_NUMBER?(snprintf(tmpa,sizeof(tmpa),"%g",l->as.number), tmpa):"");
	const char *sb = (r->type==VAL_STRING)?r->as.string: (r->type==VAL_NUMBER?(snprintf(tmpb,sizeof(tmpb),"%g",r->as.number), tmpb):"");
	size_t len = strlen(sa)+strlen(sb)+1;
	char *s = malloc(len+1); strcpy(s, sa); strcat(s, sb);
	res = make_string(s); free(s);
      }
    } else if (strcmp(n->op,"-")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_number(l->as.number - r->as.number); }
    else if (strcmp(n->op,"*")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_number(l->as.number * r->as.number); }
    else if (strcmp(n->op,"/")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_number(l->as.number / r->as.number); }
    else if (strcmp(n->op,"%")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_number(fmod(l->as.number, r->as.number)); }
    else if (strcmp(n->op,"==")==0) {
      int eq = 0;
      if (l->type == r->type) {
	if (l->type==VAL_NUMBER) eq = (l->as.number == r->as.number);
	else if (l->type==VAL_STRING) eq = (strcmp(l->as.string, r->as.string)==0);
	else if (l->type==VAL_BOOL) eq = (l->as.boolean == r->as.boolean);
	else eq = (l == r);
      }
      res = make_bool(eq);
    } else if (strcmp(n->op,"!=")==0) {
      int eq = 0;
      if (l->type == r->type) {
	if (l->type==VAL_NUMBER) eq = (l->as.number == r->as.number);
	else if (l->type==VAL_STRING) eq = (strcmp(l->as.string, r->as.string)==0);
	else if (l->type==VAL_BOOL) eq = (l->as.boolean == r->as.boolean);
	else eq = (l == r);
      }
      res = make_bool(!eq);
    } else if (strcmp(n->op,"<")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_bool(l->as.number < r->as.number); }
    else if (strcmp(n->op,">")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_bool(l->as.number > r->as.number); }
    else if (strcmp(n->op,"<=")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_bool(l->as.number <= r->as.number); }
    else if (strcmp(n->op,">=")==0) { if (l->type==VAL_NUMBER && r->type==VAL_NUMBER) res = make_bool(l->as.number >= r->as.number); }
    else if (strcmp(n->op,"&&")==0) {
      int a = (l->type==VAL_BOOL)?l->as.boolean:1;
      int b = (r->type==VAL_BOOL)?r->as.boolean:1;
      res = make_bool(a && b);
    } else if (strcmp(n->op,"||")==0) {
      int a = (l->type==VAL_BOOL)?l->as.boolean:0;
      int b = (r->type==VAL_BOOL)?r->as.boolean:0;
      res = make_bool(a || b);
    }
    value_free(l); value_free(r);
    return res;
  }

  static Value *eval_unary(ASTNode *n, Env *env) {
    Value *v = eval_node(n->left, env);
    if (!v) return make_null();
    Value *res = make_null();
    if (strcmp(n->op, "-")==0) { if (v->type==VAL_NUMBER) res = make_number(-v->as.number); }
    else if (strcmp(n->op, "!")==0) {
      int truth = 1;
      if (v->type==VAL_BOOL) truth = v->as.boolean;
      else if (v->type==VAL_NULL) truth = 0;
      res = make_bool(!truth);
    }
    value_free(v);
    return res;
  }

  static Value *eval_node(ASTNode *n, Env *env) {
    if (!n) return make_null();
    switch (n->kind) {
    case AST_STMT_BLOCK: {
      Value *last = make_null();
      for (int i=0;i<n->stmts_len;++i) { value_free(last); last = eval_node(n->stmts[i], env); }
      return last;
    }
    case AST_STMT_EXPR: return eval_node(n->left, env);
    case AST_STMT_RETURN: return eval_node(n->left, env);
    case AST_STMT_IF: {
      Value *cond = eval_node(n->left, env);
      int yes = 0;
      if (cond->type==VAL_BOOL) yes = cond->as.boolean;
      else if (cond->type==VAL_NUMBER) yes = (cond->as.number != 0);
      value_free(cond);
      if (yes) return eval_node(n->body, env);
      else if (n->right) return eval_node(n->right, env);
      else return make_null();
    }
    case AST_STMT_WHILE: {
      while (1) {
	Value *cond = eval_node(n->left, env);
	int yes = 0;
	if (cond->type==VAL_BOOL) yes = cond->as.boolean;
	else if (cond->type==VAL_NUMBER) yes = (cond->as.number != 0);
	value_free(cond);
	if (!yes) break;
	Value *r = eval_node(n->body, env); value_free(r);
      }
      return make_null();
    }
    case AST_STMT_CLASS: {
      Class *c = class_new(n->name);
      for (int i=0;i<n->body->stmts_len;++i) {
	ASTNode *m = n->body->stmts[i];
	if (m->kind == AST_STMT_FUNCDEF) {
	  Function *fn = malloc(sizeof(Function));
	  fn->name = xstrdup(m->name);
	  fn->param_count = m->param_count;
	  fn->params = malloc(sizeof(char*)*fn->param_count);
	  for (int k=0;k<fn->param_count;++k) fn->params[k] = xstrdup(m->params[k]);
	  fn->body = m->body; fn->closure = NULL;
	  Value *fv = make_function(fn);
	  hash_set(c->methods, fn->name, fv);
	}
      }
      register_class_cmap(n->name, c);
      env_set(root_env, n->name, make_string(n->name));
      return make_null();
    }
    case AST_STMT_FUNCDEF: {
      Function *f = malloc(sizeof(Function));
      f->name = xstrdup(n->name);
      f->param_count = n->param_count;
      f->params = malloc(sizeof(char*)*f->param_count);
      for (int i=0;i<f->param_count;++i) f->params[i] = xstrdup(n->params[i]);
      f->body = n->body; f->closure = env;
      Value *fv = make_function(f);
      env_set(root_env, n->name, fv);
      return make_null();
    }
    case AST_EXPR_NUMBER: return make_number(n->number);
    case AST_EXPR_STRING: return make_string(n->string);
    case AST_EXPR_BOOL: return make_bool(n->boolean);
    case AST_EXPR_NULL: return make_null();
    case AST_EXPR_IDENT: {
      Value *v = env_get(env, n->name);
      if (!v) return make_null();
      return v;
    }
    case AST_EXPR_LIST: {
      Value *lst = make_list_empty();
      for (int i=0;i<n->items_len;++i) list_append(lst, eval_node(n->items[i], env));
      return lst;
    }
    case AST_EXPR_HASH: {
      Value *h = make_hash_empty();
      for (int i=0;i<n->items_len;++i) {
	ASTNode *pair = n->items[i];
	Value *val = eval_node(pair->left, env);
	hash_set(h, pair->name, val);
      }
      return h;
    }
    case AST_EXPR_MEMBER: {
      Value *obj = eval_node(n->left, env);
      if (!obj) return make_null();
      if (obj->type == VAL_OBJECT) {
	Value *f = object_get_field(obj, n->name);
	if (f) return f;
	Value *m = class_get_method(obj->as.object.klass, n->name);
	if (m) return m;
      } else if (obj->type == VAL_HASH) {
	Value *v = hash_get(obj, n->name);
	if (v) return v;
      }
      return make_null();
    }
    case AST_EXPR_CALL: {
      if (n->left->kind == AST_EXPR_MEMBER) {
	ASTNode *member = n->left;
	Value *obj = eval_node(member->left, env);
	if (!obj) return make_null();
	Value *method = NULL;
	if (obj->type == VAL_OBJECT) {
	  method = object_get_field(obj, member->name);
	  if (!method) method = class_get_method(obj->as.object.klass, member->name);
	} else if (obj->type == VAL_HASH) {
	  method = hash_get(obj, member->name);
	}
	if (!method) {
	  Value **tmpa = eval_args_from_nodes(n->items, n->items_len, env);
	  for (int i=0;i<n->items_len;++i) value_free(tmpa[i]);
	  free(tmpa);
	  value_free(obj);
	  return make_null();
	}
	Value **args = eval_args_from_nodes(n->items, n->items_len, env);
	Value **with_self = malloc(sizeof(Value*) * (n->items_len + 1));
	with_self[0] = obj;
	for (int i=0;i<n->items_len;++i) with_self[i+1] = args[i];
	int total_args = n->items_len + 1;
	Value *res = make_null();
	if (method->type == VAL_NATIVE_FN) res = method->as.native(total_args, with_self);
	else if (method->type == VAL_FUNCTION) res = call_function(method, with_self, total_args, env);
	for (int i=1;i<total_args;++i) value_free(with_self[i]);
	free(with_self);
	free(args);
	return res;
      } else {
	Value *callee = eval_node(n->left, env);
	Value **args = eval_args_from_nodes(n->items, n->items_len, env);
	Value *res = call_function(callee, args, n->items_len, env);
	for (int i=0;i<n->items_len;++i) value_free(args[i]);
	free(args);
	return res;
      }
    }
    case AST_EXPR_ASSIGN: {
      if (n->left->kind == AST_EXPR_IDENT) {
	Value *r = eval_node(n->right, env);
	env_set(env, n->left->name, r);
	return r;
      } else if (n->left->kind == AST_EXPR_MEMBER) {
	Value *o = eval_node(n->left->left, env);
	Value *r = eval_node(n->right, env);
	if (o->type == VAL_OBJECT) { object_set_field(o, n->left->name, r); return r; }
	else if (o->type == VAL_HASH) { hash_set(o, n->left->name, r); return r; }
	else { value_free(r); return make_null(); }
      } else return make_null();
    }
    case AST_EXPR_BINARY: return eval_binary(n, env);
    case AST_EXPR_UNARY: return eval_unary(n, env);
    case AST_EXPR_NEW: {
      Class *c = find_class_cmap(n->name);
      if (!c) { fprintf(stderr,"Unknown class %s\n", n->name); return make_null(); }
      Value *obj = object_new(c);
      Value *initm = class_get_method(c, "init");
      if (initm) {
	Value **args = eval_args_from_nodes(n->items, n->items_len, env);
	Value **with_self = malloc(sizeof(Value*) * (n->items_len + 1));
	with_self[0] = obj;
	for (int i=0;i<n->items_len;++i) with_self[i+1] = args[i];
	int total_args = n->items_len + 1;
	if (initm->type == VAL_NATIVE_FN) initm->as.native(total_args, with_self);
	else if (initm->type == VAL_FUNCTION) call_function(initm, with_self, total_args, env);
	for (int i=1;i<total_args;++i) value_free(with_self[i]);
	free(with_self);
	free(args);
      }
      return obj;
    }
    default: return make_null();
    }
  }

  /* -----------------------
   Value print/free
   ----------------------- */
  static void value_print(Value *v) {
    if (!v) { printf("null"); return; }
    switch (v->type) {
    case VAL_NULL: printf("null"); break;
    case VAL_NUMBER: printf("%g", v->as.number); break;
    case VAL_STRING: printf("%s", v->as.string); break;
    case VAL_BOOL: printf(v->as.boolean ? "true" : "false"); break;
    case VAL_LIST: {
      printf("[");
      for (int i=0;i<v->as.list.len;++i) { value_print(v->as.list.items[i]); if (i+1<v->as.list.len) printf(", "); }
      printf("]"); break;
    }
    case VAL_HASH: {
      printf("{");
      for (int i=0;i<v->as.hash.len;++i) { printf("%s: ", v->as.hash.keys[i]); value_print(v->as.hash.vals[i]); if (i+1<v->as.hash.len) printf(", "); }
      printf("}"); break;
    }
    case VAL_OBJECT: printf("<%s object>", v->as.object.klass ? v->as.object.klass->name : "anon"); break;
    case VAL_FUNCTION: printf("<function %s>", v->as.fun->name?v->as.fun->name:"(anon)"); break;
    case VAL_NATIVE_FN: printf("<native_fn>"); break;
    }
  }

  static void value_free(Value *v) {
    if (!v) return;
    switch (v->type) {
    case VAL_STRING: free(v->as.string); break;
    case VAL_LIST:
      for (int i=0;i<v->as.list.len;++i) value_free(v->as.list.items[i]);
      free(v->as.list.items); break;
    case VAL_HASH:
      for (int i=0;i<v->as.hash.len;++i) { free(v->as.hash.keys[i]); value_free(v->as.hash.vals[i]); }
      free(v->as.hash.keys); free(v->as.hash.vals); break;
    case VAL_OBJECT:
      for (int i=0;i<v->as.object.flen;++i) { free(v->as.object.fkeys[i]); value_free(v->as.object.fields[i]); }
      free(v->as.object.fkeys); free(v->as.object.fields); break;
    case VAL_FUNCTION:
      if (v->as.fun) {
	free(v->as.fun->name);
	for (int i=0;i<v->as.fun->param_count;++i) free(v->as.fun->params[i]);
	free(v->as.fun->params);
	free(v->as.fun);
      }
      break;
    default: break;
    }
    free(v);
  }

  /* -----------------------
   Helpers for external processes and HTTP (libcurl)
   ----------------------- */

  static char *popen_capture(const char *cmd) {
    FILE *fp = popen(cmd, "r");
    if (!fp) return NULL;
    size_t cap = 4096;
    char *buf = malloc(cap); size_t used = 0;
    char tmp[1024];
    while (fgets(tmp, sizeof(tmp), fp)) {
      size_t l = strlen(tmp);
      if (used + l + 1 > cap) { cap = cap * 2 + l; buf = realloc(buf, cap); }
      memcpy(buf + used, tmp, l); used += l;
    }
    buf[used] = '\0';
    pclose(fp);
    return buf;
  }

  static char *read_file_all(const char *path) {
    FILE *f = fopen(path, "rb"); if (!f) return NULL;
    fseek(f,0,SEEK_END); long sz = ftell(f); fseek(f,0,SEEK_SET);
    char *buf = malloc(sz+1); fread(buf,1,sz,f); buf[sz]=0; fclose(f);
    return buf;
  }

  struct mem_chunk { char *mem; size_t size; };
  static size_t curl_write_cb(void *data, size_t size, size_t nmemb, void *userp) {
    size_t realsz = size * nmemb;
    struct mem_chunk *mc = (struct mem_chunk*)userp;
    mc->mem = realloc(mc->mem, mc->size + realsz + 1);
    memcpy(&(mc->mem[mc->size]), data, realsz);
    mc->size += realsz;
    mc->mem[mc->size] = 0;
    return realsz;
  }

  static char *http_post_json(const char *url, const char *bearer, const char *json_body) {
    CURL *curl = curl_easy_init();
    if (!curl) return NULL;
    struct mem_chunk chunk = { malloc(1), 0 };
    struct curl_slist *headers = NULL;
    char auth[1024];
    if (bearer) { snprintf(auth, sizeof(auth), "Authorization: Bearer %s", bearer); headers = curl_slist_append(headers, auth); }
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_body);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curl_write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)&chunk);
    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
      curl_slist_free_all(headers);
      curl_easy_cleanup(curl);
      free(chunk.mem);
      return NULL;
    }
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return chunk.mem;
  }

  /* -----------------------
   Native functions: PDF & LLM
   ----------------------- */

  static Value *native_pdf_extract_text(int argc, Value **argv) {
    if (argc==0 || argv[0]->type!=VAL_STRING) return make_string("");
    const char *path = argv[0]->as.string;
    char cmd[4096];
    snprintf(cmd, sizeof(cmd), "pdftotext -layout %s - 2>/dev/null", path);
    char *out = popen_capture(cmd);
    if (!out) return make_string("");
    Value *v = make_string(out);
    free(out);
    return v;
  }

  static Value *native_pdf_extract_pages(int argc, Value **argv) {
    if (argc==0 || argv[0]->type!=VAL_STRING) return make_list_empty();
    const char *path = argv[0]->as.string;
    char cmd[4096];
    snprintf(cmd, sizeof(cmd), "pdftotext -layout %s - 2>/dev/null", path);
    char *out = popen_capture(cmd);
    Value *lst = make_list_empty();
    if (!out) return lst;
    char *p = out;
    char *start = p;
    while (*p) {
      if (*p == '\f') {
	*p = '\0';
	list_append(lst, make_string(start));
	start = p + 1;
      }
      p++;
    }
    if (*start) list_append(lst, make_string(start));
    free(out);
    return lst;
  }

  static Value *native_llm_call_local(int argc, Value **argv) {
    const char *llama_exe = "./llama";
    const char *model_path = getenv("LLM_MODEL_PATH");
    const char *prompt = NULL;
    if (argc == 1 && argv[0]->type == VAL_STRING) { prompt = argv[0]->as.string; }
    else if (argc >= 2) {
      if (argv[0]->type == VAL_STRING) llama_exe = argv[0]->as.string;
      if (argv[1]->type == VAL_STRING) model_path = argv[1]->as.string;
      if (argc >= 3 && argv[2]->type == VAL_STRING) prompt = argv[2]->as.string;
    }
    if (!prompt) return make_string("");
    char cmd[8192];
    if (model_path) snprintf(cmd, sizeof(cmd), "%s --model %s --prompt \"%s\" --color 0 2>/dev/null", llama_exe, model_path, prompt);
    else snprintf(cmd, sizeof(cmd), "%s --prompt \"%s\" --color 0 2>/dev/null", llama_exe, prompt);
    char *out = popen_capture(cmd);
    if (!out) return make_string("");
    Value *v = make_string(out);
    free(out);
    return v;
  }

  static char *json_escape(const char *s) {
    size_t len = strlen(s);
    char *out = malloc(len*2 + 1);
    char *w = out;
    for (const char *p = s; *p; ++p) {
      if (*p == '"') { *w++ = '\\'; *w++ = '"'; }
      else if (*p == '\\') { *w++ = '\\'; *w++ = '\\'; }
      else if (*p == '\n') { *w++ = '\\'; *w++ = 'n'; }
      else *w++ = *p;
    }
    *w = '\0';
    return out;
  }

  static Value *native_llm_call_openai(int argc, Value **argv) {
    if (argc == 0 || argv[0]->type != VAL_STRING) return make_string("");
    const char *key = getenv("OPENAI_API_KEY");
    if (!key) return make_string("[no OPENAI_API_KEY]");
    const char *base = getenv("OPENAI_API_BASE");
    if (!base) base = "https://api.openai.com/v1";
    const char *model = getenv("OPENAI_MODEL");
    if (!model) model = "gpt-3.5-turbo";
    const char *prompt = argv[0]->as.string;
    char *esc = json_escape(prompt);
    char json_body[65536];
    snprintf(json_body, sizeof(json_body),
	     "{ \"model\": \"%s\", \"messages\": [{\"role\": \"user\", \"content\": \"%s\"}], \"max_tokens\": 800 }",
	     model, esc);
    free(esc);
    char url[1024];
    snprintf(url, sizeof(url), "%s/chat/completions", base);
    char *resp = http_post_json(url, key, json_body);
    if (!resp) return make_string("[http error]");
    /* naive extraction */
    char *p = strstr(resp, "\"content\":");
    char *result = NULL;
    if (p) {
      p = strstr(p, "\"content\":");
      if (p) {
	p = strchr(p, ':');
	if (p) {
	  p++;
	  while (*p && isspace((unsigned char)*p)) p++;
	  if (*p == '"') {
	    p++;
	    char *q = p;
	    while (*q && *q != '"') {
	      if (*q == '\\' && q[1]) q += 2;
	      else q++;
	    }
	    size_t len = q - p;
	    result = malloc(len+1);
	    strncpy(result, p, len); result[len]=0;
	  }
	}
      }
    }
    if (!result) result = xstrdup(resp);
    free(resp);
    Value *v = make_string(result);
    free(result);
    return v;
  }

  /* -----------------------
   Other native utilities
   ----------------------- */

  static Value *native_print(int argc, Value **argv) {
    for (int i=0;i<argc;++i) {
      value_print(argv[i]);
      if (i+1<argc) printf(" ");
    }
    printf("\n");
    return make_null();
  }
  static Value *native_str(int argc, Value **argv) {
    if (argc==0) return make_string("");
    Value *v = argv[0];
    char buf[256];
    if (v->type==VAL_STRING) return make_string(v->as.string);
    if (v->type==VAL_NUMBER) { snprintf(buf,sizeof(buf), "%g", v->as.number); return make_string(buf); }
    if (v->type==VAL_BOOL) return make_string(v->as.boolean ? "true":"false");
    return make_string("");
  }
  static Value *native_tokenize(int argc, Value **argv) {
    Value *res = make_list_empty();
    if (argc==0 || argv[0]->type!=VAL_STRING) return res;
    const char *s = argv[0]->as.string;
    const char *p = s;
    char buf[256]; int bi=0;
    while (*p) {
      if (isalnum((unsigned char)*p)) { buf[bi++]=*p; }
      else {
	if (bi>0) { buf[bi]=0; list_append(res, make_string(buf)); bi=0; }
	if (ispunct((unsigned char)*p)) { char t[2] = {*p,0}; list_append(res, make_string(t)); }
      }
      p++;
    }
    if (bi>0) { buf[bi]=0; list_append(res, make_string(buf)); }
    return res;
  }
  static Value *native_shannon_entropy(int argc, Value **argv) {
    if (argc==0 || argv[0]->type!=VAL_STRING) return make_number(0.0);
    char *s = argv[0]->as.string;
    int counts[256] = {0}; int total=0;
    for (char *p=s; *p; ++p) { unsigned char c = (unsigned char)*p; counts[c]++; total++; }
    double H = 0.0;
    for (int i=0;i<256;++i) if (counts[i]) { double p = (double)counts[i] / total; H -= p * log2(p); }
    return make_number(H);
  }
  static Value *native_semantic_vector(int argc, Value **argv) {
    Value *vec = make_list_empty();
    if (argc==0 || argv[0]->type!=VAL_STRING) return vec;
    const char *s = argv[0]->as.string;
    const int dim = 32;
    double acc[dim]; for (int i=0;i<dim;++i) acc[i]=0.0;
    for (const char *p=s; *p; ++p) {
      unsigned char c = (unsigned char)*p;
      for (int k=0;k<dim;++k) acc[k] += ((c + k) % 7) * 0.001;
    }
    for (int i=0;i<dim;++i) list_append(vec, make_number(acc[i]));
    return vec;
  }
  static Value *native_cosine_similarity(int argc, Value **argv) {
    if (argc<2) return make_number(0.0);
    if (argv[0]->type!=VAL_LIST || argv[1]->type!=VAL_LIST) return make_number(0.0);
    int n = argv[0]->as.list.len;
    if (n != argv[1]->as.list.len) return make_number(0.0);
    double dot=0, na=0, nb=0;
    for (int i=0;i<n;++i) {
      double a = (argv[0]->as.list.items[i]->type==VAL_NUMBER)?argv[0]->as.list.items[i]->as.number:0.0;
      double b = (argv[1]->as.list.items[i]->type==VAL_NUMBER)?argv[1]->as.list.items[i]->as.number:0.0;
      dot += a*b; na += a*a; nb += b*b;
    }
    double denom = sqrt(na)*sqrt(nb);
  if (denom == 0.0) return make_number(0.0);
 return make_number(dot/denom);
  }
                
  static Value *native_regex_match(int argc, Value **argv) {
    if (argc<2 || argv[0]->type!=VAL_STRING || argv[1]->type!=VAL_STRING) return make_bool(0);
    regex_t re; int rc = regcomp(&re, argv[0]->as.string, REG_EXTENDED|REG_NOSUB);
    if (rc) return make_bool(0);
    int m = regexec(&re, argv[1]->as.string, 0, NULL, 0) == 0;
    regfree(&re);
    return make_bool(m);
  }

  static Value *native_sanitize_noema_code(int argc, Value **argv) {
    if (argc==0 || argv[0]->type!=VAL_STRING) return make_string("");
    const char *s = argv[0]->as.string;
    char *out = malloc(strlen(s)+1);
    char *w = out;
    for (const char *p=s; *p; ++p) {
      if (*p == ';' || *p == '`') continue;
      *w++ = *p;
    }
    *w = 0;
    Value *res = make_string(out);
    free(out);
    return res;
  }

  /* -----------------------
   Native registry + registration
   ----------------------- */
  typedef Value *(*NativeFn)(int, Value **);
  typedef struct NativeReg { char *name; NativeFn fn; struct NativeReg *next; } NativeReg;
  static NativeReg *native_registry = NULL;
  void register_native_function(const char *name, NativeFn fn) {
    NativeReg *n = malloc(sizeof(NativeReg)); n->name = xstrdup(name); n->fn = fn; n->next = native_registry; native_registry = n;
    env_set(root_env, name, make_native(fn));
  }

  /* -----------------------
   REPL / script execution / compile mode
   ----------------------- */
  static void repl() {
    char line[8192];
    printf("Noema prototype REPL. Type 'exit' to quit.\n");
    for (;;) {
      printf(">>> ");
      if (!fgets(line, sizeof(line), stdin)) break;
      if (strncmp(line, "exit", 4) == 0) break;
      Parser p; parser_init(&p, line);
      ASTNode *prog = parse_program(&p);
      if (!prog) continue;
      Value *res = eval_node(prog, root_env);
      value_print(res); printf("\n");
      value_free(res);
      ast_free(prog);
    }
  }

  static int run_script_file(const char *path) {
    char *src = read_file_all(path);
    if (!src) { fprintf(stderr,"Cannot read %s\n", path); return 1; }
    Parser p; parser_init(&p, src);
    ASTNode *prog = parse_program(&p);
    if (!prog) { free(src); return 1; }
    Value *res = eval_node(prog, root_env);
    value_print(res); printf("\n");
    value_free(res);
    ast_free(prog);
    free(src);
    return 0;
  }

  /* compile: produce a C source that embeds runtime init + script string and runs it */
  static int compile_to_c(const char *inpath, const char *outpath) {
    char *src = read_file_all(inpath);
    if (!src) { fprintf(stderr,"Cannot read %s\n", inpath); return 1; }
    FILE *f = fopen(outpath, "w");
    if (!f) { fprintf(stderr,"Cannot write %s\n", outpath); free(src); return 1; }
    /* Emit a minimal program that includes this runtime as an embedded string.
       For simplicity we emit a C program that writes the script to a temp file and execs the current binary in script mode.
       A fully standalone compiler would embed runtime; here we output a small wrapper that requires the runtime binary.
    */
    fprintf(f,
	    "/* Autogenerated wrapper for %s */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <unistd.h>\n"
"int main(int argc, char **argv) {\n"
	    "  const char *script =\n", inpath);
    /* write script as C string literals */
    const char *p = src;
    while (*p) {
      int chunk = 256;
      char buf[257]; int i=0;
      while (*p && i < chunk) {
	char c = *p++;
	if (c == '\\') { buf[i++] = '\\'; buf[i++] = '\\'; }
	else if (c == '\"') { buf[i++] = '\\'; buf[i++] = '\"'; }
	else if (c == '\n') { buf[i++] = '\\'; buf[i++] = 'n'; }
	else buf[i++] = c;
      }
      buf[i] = 0;
      fprintf(f, "    \"%s\"\n", buf);
    }
    fprintf(f,
"    ;\n"
"  char tmpname[] = \"/tmp/noema_script_XXXXXX\";\n"
"  int fd = mkstemp(tmpname);\n"
"  if (fd == -1) { perror(\"mkstemp\"); return 1; }\n"
"  FILE *tf = fdopen(fd, \"w\"); if (!tf) { perror(\"fdopen\"); return 1; }\n" 
"  fputs(script, tf); fclose(tf);\n" 
	    "  /* exec the runtime (assumes 'noema' in PATH or same dir). */\n"
"  execlp(\"./noema\", \"noema\", tmpname, (char*)NULL);\n"
	    "  perror(\"execlp\"); return 1;\n}\n");
    fclose(f);
    free(src);
    printf("Wrote wrapper C to %s\n", outpath);
    return 0;
  }

  /* -----------------------
   main
   ----------------------- */
  int main(int argc, char **argv) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
    root_env = env_new(NULL);

    /* register natives */
    register_native_function("print", native_print);
    register_native_function("str", native_str);
    register_native_function("shannon_entropy", native_shannon_entropy);
    register_native_function("tokenize", native_tokenize);
    register_native_function("semantic_vector", native_semantic_vector);
    register_native_function("cosine_similarity", native_cosine_similarity);
    register_native_function("regex_match", native_regex_match);
    register_native_function("sanitize_noema_code", native_sanitize_noema_code);
    register_native_function("pdf_extract_text", native_pdf_extract_text);
    register_native_function("pdf_extract_pages", native_pdf_extract_pages);
    register_native_function("llm_call_openai", native_llm_call_openai);
    register_native_function("llm_call_local", native_llm_call_local);

    /* preload example */
    const char *startup =
        "def add(a,b) { return a + b; }\n"
      "class Point { def init(self,x,y) { self.x = x; self.y = y; } def mag(self) { return (self.x * self.x + self.y * self.y); } }\n";
    Parser p; parser_init(&p, startup);
    ASTNode *prog = parse_program(&p);
    if (prog) { eval_node(prog, root_env); ast_free(prog); }

    if (argc == 1) {
      repl();
    } else if (argc == 2) {
      /* run script file */
      run_script_file(argv[1]);
    } else if (argc == 4 && strcmp(argv[1], "-c") == 0) {
      compile_to_c(argv[2], argv[3]);
    } else {
      fprintf(stderr, "Usage:\n  %s           # REPL\n  %s script    # run script\n  %s -c in out  # generate wrapper C\n", argv[0], argv[0], argv[0]);
    }

    curl_global_cleanup();
    return 0;
  }

  /*
  注意:
- ここでのコンパイル生成（-c）は簡易ラッパー生成で、完全にスタンドアロン化はしていません（ランタイムを ./noema として実行します）。完全に自己完結するCを生成するにはランタイムの全コードを埋め込む必要があります（可能ですが長大）。
  - ビルド手順:
  - sudo apt-get install -y build-essential libcurl4-openssl-dev poppler-utils
  - gcc -std=c11 -O2 -Wall noema_full_with_llm_pdf.c -o noema -lcurl -lm -pthread
    - 実行例:
  - ./noema                 （REPL）
  - ./noema script.noema    （スクリプト実行）
  - ./noema -c script.noema wrapper.c  （Cラッパー生成）
```
*/
