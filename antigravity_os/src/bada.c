/* ============================================================================
 * bada.c -- The Unknown-Prior Engine reference implementation (stage-0)
 * EXTENDED EDITION: revisers that actually rewrite syntax.
 * (transcribed for the Anti-Gravity OS Bada sources)
 * ==========================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <complex.h>
#include <ctype.h>
#include <stdint.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static void *xmalloc(size_t n){ void *p = malloc(n); if(!p){fprintf(stderr,"OOM\n");exit(1);} return p; }
static void *xrealloc(void *q, size_t n){ void *p = realloc(q,n); if(!p){fprintf(stderr,"OOM\n");exit(1);} return p; }
static char *xstrdup(const char *s){ size_t n=strlen(s)+1; char *p=xmalloc(n); memcpy(p,s,n); return p; }

typedef enum {
  T_INT, T_FLOAT, T_STRING, T_IDENT,
  T_OMEGA, T_DATABASE, T_TUPLESPACE, T_TUPLESPACE_C, T_ASPERAL, T_STRUCT,
  T_DEF, T_TYPEDEF, T_RETURN, T_IF, T_ELSE, T_WHILE,
  T_FOR, T_IN, T_STATIC, T_DYNAMIC, T_REFINE, T_STAR,
  T_TRUE, T_FALSE, T_NIL, T_LET, T_PRINT, T_EACH,
  T_REVISER,
  T_BIND, T_ASSIGN, T_COMMIT, T_QUERY, T_ARROW, T_DEFARROW,
  T_APPEND, T_TILDE, T_SCOPE, T_PIPE,
  T_PLUS, T_MINUS, T_STARC, T_SLASH, T_PCT,
  T_LT, T_LE, T_GT, T_GE, T_EQ, T_NE,
  T_AND, T_OR, T_NOT,
  T_LPAREN, T_RPAREN, T_LBRACE, T_RBRACE, T_LBRACK, T_RBRACK,
  T_COMMA, T_DOT, T_COLON, T_SEMI,
  T_AT,
  T_EOF
} TokKind;

typedef struct { TokKind kind; char *lex; double num; int line; } Token;
typedef struct { const char *src; size_t pos, len; int line; Token *toks; size_t ntok, captok; } Lexer;

static void push_tok(Lexer *L, TokKind k, const char *lex, double num){
  if(L->ntok==L->captok){ L->captok = L->captok? L->captok*2 : 64;
    L->toks = xrealloc(L->toks, L->captok*sizeof(Token)); }
  Token t; t.kind=k; t.lex= lex? xstrdup(lex):NULL; t.num=num; t.line=L->line;
  L->toks[L->ntok++]=t;
}

typedef struct { const char *w; TokKind k; } KW;
static KW KEYWORDS[] = {
  {"Omega",T_OMEGA},{"DATABASE",T_DATABASE},{"tuplespace",T_TUPLESPACE},
  {"TupleSpace",T_TUPLESPACE_C},{"asperal",T_ASPERAL},{"struct",T_STRUCT},
  {"def",T_DEF},{"typedef",T_TYPEDEF},{"return",T_RETURN},{"if",T_IF},
  {"else",T_ELSE},{"while",T_WHILE},{"for",T_FOR},{"in",T_IN},
  {"static",T_STATIC},{"dynamic",T_DYNAMIC},{"refine",T_REFINE},{"star",T_STAR},
  {"true",T_TRUE},{"false",T_FALSE},{"nil",T_NIL},{"let",T_LET},
  {"print",T_PRINT},{"each",T_EACH},
  {NULL,0}
};

static TokKind kw_lookup(const char *s){
  for(int i=0; KEYWORDS[i].w; i++) if(!strcmp(KEYWORDS[i].w,s)) return KEYWORDS[i].k;
  return T_IDENT;
}

static int peek(Lexer *L){ return L->pos<L->len ? L->src[L->pos] : -1; }
static int peek2(Lexer *L){ return L->pos+1<L->len ? L->src[L->pos+1] : -1; }
static int peek3(Lexer *L){ return L->pos+2<L->len ? L->src[L->pos+2] : -1; }
static int adv(Lexer *L){ int c = peek(L); L->pos++; if(c=='\n') L->line++; return c; }

static void lex_all(Lexer *L){
  while(L->pos < L->len){
    int c = peek(L);
    if(c=='\n'){ adv(L); continue; }
    if(isspace(c)){ adv(L); continue; }
    if(c=='#'){ while(peek(L)!=-1 && peek(L)!='\n') adv(L); continue; }
    if(c=='/' && peek2(L)=='/'){ while(peek(L)!=-1 && peek(L)!='\n') adv(L); continue; }
    if(c=='@'){
      size_t save=L->pos; adv(L);
      char buf[32]; int n=0;
      while(isalpha(peek(L)) && n<31) buf[n++]=adv(L);
      buf[n]=0;
      if(!strcmp(buf,"reviser")) push_tok(L,T_REVISER,"@reviser",0);
      else { L->pos=save; adv(L); push_tok(L,T_AT,"@",0); }
      continue;
    }
    if(isdigit(c) || (c=='.' && isdigit(peek2(L)))){
      size_t s=L->pos; int isf=0;
      while(isdigit(peek(L))) adv(L);
      if(peek(L)=='.' && isdigit(peek2(L))){ isf=1; adv(L); while(isdigit(peek(L))) adv(L); }
      if(peek(L)=='e'||peek(L)=='E'){ isf=1; adv(L); if(peek(L)=='+'||peek(L)=='-') adv(L);
        while(isdigit(peek(L))) adv(L); }
      size_t len=L->pos-s; char *t=xmalloc(len+1); memcpy(t,L->src+s,len); t[len]=0;
      push_tok(L, isf?T_FLOAT:T_INT, t, atof(t)); free(t); continue;
    }
    if(isalpha(c)||c=='_'){
      size_t s=L->pos;
      while(isalnum(peek(L))||peek(L)=='_') adv(L);
      size_t len=L->pos-s; char *t=xmalloc(len+1); memcpy(t,L->src+s,len); t[len]=0;
      push_tok(L, kw_lookup(t), t, 0); free(t); continue;
    }
    if(c=='"'){
      adv(L); size_t cap=16,n=0; char *b=xmalloc(cap);
      while(peek(L)!=-1 && peek(L)!='"'){
        int ch=adv(L);
        if(ch=='\\'){ int e=adv(L);
          switch(e){case 'n':ch='\n';break;case 't':ch='\t';break;
            case '\\':ch='\\';break;case '"':ch='"';break;default:ch=e;} }
        if(n+1>=cap){cap*=2;b=xrealloc(b,cap);} b[n++]=ch;
      }
      adv(L); b[n]=0; push_tok(L,T_STRING,b,0); free(b); continue;
    }
#define M3(a,b,cc,K) if(c==a&&peek2(L)==b&&peek3(L)==cc){adv(L);adv(L);adv(L);push_tok(L,K,NULL,0);continue;}
#define M2(a,b,K) if(c==a&&peek2(L)==b){adv(L);adv(L);push_tok(L,K,NULL,0);continue;}
#define M1(a,K) if(c==a){adv(L);push_tok(L,K,NULL,0);continue;}
    M3(':','=','>',T_DEFARROW)
    M2(':','=',T_BIND)
    M2('>','>',T_COMMIT)
    M2('=','>',T_QUERY)
    M2('-','>',T_ARROW)
    M2('<','-',T_APPEND)
    M2(':',':',T_SCOPE)
    M2('<','=',T_LE)
    M2('>','=',T_GE)
    M2('=','=',T_EQ)
    M2('!','=',T_NE)
    M2('&','&',T_AND)
    M2('|','|',T_OR)
    M1('=',T_ASSIGN)
    M1('+',T_PLUS) M1('-',T_MINUS) M1('*',T_STARC) M1('/',T_SLASH) M1('%',T_PCT)
    M1('<',T_LT) M1('>',T_GT) M1('~',T_TILDE) M1('!',T_NOT)
    M1('(',T_LPAREN) M1(')',T_RPAREN) M1('{',T_LBRACE) M1('}',T_RBRACE)
    M1('[',T_LBRACK) M1(']',T_RBRACK)
    M1(',',T_COMMA) M1('.',T_DOT) M1(':',T_COLON) M1(';',T_SEMI)
    M1('|',T_PIPE)
#undef M3
#undef M2
#undef M1
    fprintf(stderr,"lex error: unexpected '%c' (line %d)\n", c, L->line);
    adv(L);
  }
  push_tok(L,T_EOF,NULL,0);
}

static const char *tok_name(TokKind k){
  switch(k){
    case T_INT:return"INT";case T_FLOAT:return"FLOAT";case T_STRING:return"STRING";
    case T_IDENT:return"IDENT";case T_OMEGA:return"OMEGA";case T_DATABASE:return"DATABASE";
    case T_TUPLESPACE:return"TUPLESPACE";case T_TUPLESPACE_C:return"TUPLESPACE";
    case T_ASPERAL:return"ASPERAL";case T_STRUCT:return"STRUCT";case T_DEF:return"DEF";
    case T_TYPEDEF:return"TYPEDEF";case T_RETURN:return"RETURN";case T_IF:return"IF";
    case T_ELSE:return"ELSE";case T_WHILE:return"WHILE";case T_FOR:return"FOR";
    case T_IN:return"IN";case T_STATIC:return"STATIC";case T_DYNAMIC:return"DYNAMIC";
    case T_REFINE:return"REFINE";case T_STAR:return"STAR";case T_TRUE:return"TRUE";
    case T_FALSE:return"FALSE";case T_NIL:return"NIL";case T_LET:return"LET";
    case T_PRINT:return"PRINT";case T_EACH:return"EACH";case T_REVISER:return"REVISER";
    case T_BIND:return"BIND";case T_ASSIGN:return"ASSIGN";case T_COMMIT:return"COMMIT";
    case T_QUERY:return"QUERY";case T_ARROW:return"ARROW";case T_DEFARROW:return"DEFARROW";
    case T_APPEND:return"APPEND";case T_TILDE:return"TILDE";case T_SCOPE:return"SCOPE";
    case T_PIPE:return"PIPE";case T_PLUS:return"PLUS";case T_MINUS:return"MINUS";
    case T_STARC:return"STARC";case T_SLASH:return"SLASH";case T_PCT:return"PCT";
    case T_LT:return"LT";case T_LE:return"LE";case T_GT:return"GT";case T_GE:return"GE";
    case T_EQ:return"EQ";case T_NE:return"NE";case T_AND:return"AND";case T_OR:return"OR";
    case T_NOT:return"NOT";case T_LPAREN:return"LPAREN";case T_RPAREN:return"RPAREN";
    case T_LBRACE:return"LBRACE";case T_RBRACE:return"RBRACE";case T_LBRACK:return"LBRACK";
    case T_RBRACK:return"RBRACK";case T_COMMA:return"COMMA";case T_DOT:return"DOT";
    case T_COLON:return"COLON";case T_SEMI:return"SEMI";case T_AT:return"AT";
    case T_EOF:return"EOF";default:return"?";
  }
}

typedef enum {
  N_INT, N_FLOAT, N_STR, N_BOOL, N_NIL, N_STARLIT,
  N_IDENT, N_OMEGA, N_TUPLESPACE,
  N_ARRAY, N_LAMBDA,
  N_BIND, N_ASSIGN, N_CALL, N_INDEX, N_MEMBER, N_SCOPE,
  N_UNARY, N_BINARY,
  N_COMMIT, N_APPEND, N_QUERY,
  N_IF, N_WHILE, N_FOR, N_RETURN, N_PRINT, N_BLOCK,
  N_FUNC, N_ASPERAL, N_TYPEDEF, N_OMEGABLOCK,
  N_EACH,
  N_REVISER,
  N_RULE,
  N_EXTENDED,
  N_PROGRAM
} NodeKind;

typedef struct Node Node;
struct Node {
  NodeKind kind; double num; char *str;
  Node **kids; int nkid;
  char **params; int nparam;
  int line;
};

static Node *mknode(NodeKind k){ Node *n=xmalloc(sizeof(Node)); memset(n,0,sizeof(Node)); n->kind=k; return n; }
static void addkid(Node *n, Node *c){ n->kids = xrealloc(n->kids,(n->nkid+1)*sizeof(Node*)); n->kids[n->nkid++]=c; }
static void addparam(Node *n, const char *p){ n->params = xrealloc(n->params,(n->nparam+1)*sizeof(char*)); n->params[n->nparam++]=xstrdup(p); }

typedef struct { Token *t; size_t i, n; } Parser;
static Token *cur(Parser *P){ return &P->t[P->i]; }
static TokKind curk(Parser *P){ return P->t[P->i].kind; }
static Token *padv(Parser *P){ return &P->t[P->i++]; }
static int accept(Parser *P, TokKind k){ if(curk(P)==k){P->i++;return 1;} return 0; }
static void expect(Parser *P, TokKind k, const char *what){
  if(curk(P)!=k){ fprintf(stderr,"parse error: expected %s but got %s (line %d)\n",
    what, tok_name(curk(P)), cur(P)->line); exit(1); }
  P->i++;
}

static Node *parse_expr(Parser *P);
static Node *parse_block(Parser *P);
static Node *parse_decl(Parser *P);
static Node *parse_stmt(Parser *P);

static void parse_pipe_params(Parser *P, Node *fn){
  expect(P,T_PIPE,"|");
  if(curk(P)!=T_PIPE){
    do { if(curk(P)==T_IDENT){ addparam(fn, cur(P)->lex); padv(P); } else break; } while(accept(P,T_COMMA));
  }
  expect(P,T_PIPE,"|");
}

static Node *parse_do_or_expr(Parser *P){
  if(curk(P)==T_IDENT && !strcmp(cur(P)->lex,"do")){
    padv(P);
    Node *blk = mknode(N_BLOCK);
    while(!(curk(P)==T_IDENT && !strcmp(cur(P)->lex,"end")) && curk(P)!=T_EOF) addkid(blk, parse_stmt(P));
    if(curk(P)==T_IDENT && !strcmp(cur(P)->lex,"end")) padv(P);
    return blk;
  }
  return parse_expr(P);
}

static Node *parse_array(Parser *P){
  expect(P,T_LBRACK,"[");
  Node *a=mknode(N_ARRAY);
  if(curk(P)!=T_RBRACK){ do { addkid(a, parse_expr(P)); } while(accept(P,T_COMMA)); }
  expect(P,T_RBRACK,"]");
  return a;
}

static Node *parse_lambda(Parser *P){
  Node *fn=mknode(N_LAMBDA);
  parse_pipe_params(P,fn);
  addkid(fn, parse_do_or_expr(P));
  return fn;
}

typedef struct { char **words; int n, cap; } WordSet;
static WordSet POSTFIX_WORDS = {0,0,0};
static WordSet STMT_WORDS = {0,0,0};
static void wordset_add(WordSet *w, const char *s){
  for(int i=0;i<w->n;i++) if(!strcmp(w->words[i],s)) return;
  if(w->n==w->cap){ w->cap=w->cap?w->cap*2:8; w->words=xrealloc(w->words,w->cap*sizeof(char*)); }
  w->words[w->n++]=xstrdup(s);
}
static int wordset_has(WordSet *w, const char *s){
  for(int i=0;i<w->n;i++) if(!strcmp(w->words[i],s)) return 1;
  return 0;
}

static Node *parse_primary(Parser *P){
  Token *t=cur(P);
  switch(t->kind){
    case T_INT: { Node*n=mknode(N_INT); n->num=t->num; padv(P); return n; }
    case T_FLOAT: { Node*n=mknode(N_FLOAT); n->num=t->num; padv(P); return n; }
    case T_STRING:{ Node*n=mknode(N_STR); n->str=xstrdup(t->lex); padv(P); return n; }
    case T_TRUE: { Node*n=mknode(N_BOOL); n->num=1; padv(P); return n; }
    case T_FALSE: { Node*n=mknode(N_BOOL); n->num=0; padv(P); return n; }
    case T_NIL: { padv(P); return mknode(N_NIL); }
    case T_STAR: { padv(P); return mknode(N_STARLIT); }
    case T_OMEGA: { padv(P); return mknode(N_OMEGA); }
    case T_TUPLESPACE: case T_TUPLESPACE_C: { padv(P); return mknode(N_TUPLESPACE); }
    case T_IDENT: {
      if(wordset_has(&POSTFIX_WORDS, t->lex)){
        char *w = xstrdup(t->lex); padv(P);
        Node *ex = mknode(N_EXTENDED); ex->str = w;
        addkid(ex, parse_primary(P));
        return ex;
      }
      Node*n=mknode(N_IDENT); n->str=xstrdup(t->lex); padv(P); return n;
    }
    case T_LBRACK: return parse_array(P);
    case T_PIPE: return parse_lambda(P);
    case T_LPAREN: { padv(P); Node*e=parse_expr(P); expect(P,T_RPAREN,")"); return e; }
    default:
      fprintf(stderr,"parse error: unexpected %s in expression (line %d)\n", tok_name(t->kind), t->line);
      exit(1);
  }
}

static Node *parse_postfix(Parser *P){
  Node *e=parse_primary(P);
  for(;;){
    if(curk(P)==T_LPAREN){
      padv(P);
      Node *c=mknode(N_CALL); addkid(c,e);
      if(curk(P)!=T_RPAREN){ do { addkid(c, parse_expr(P)); } while(accept(P,T_COMMA)); }
      expect(P,T_RPAREN,")"); e=c;
    } else if(curk(P)==T_LBRACK){
      padv(P);
      Node *ix=mknode(N_INDEX); addkid(ix,e); addkid(ix,parse_expr(P));
      expect(P,T_RBRACK,"]"); e=ix;
    } else if(curk(P)==T_DOT){
      padv(P);
      if(curk(P)==T_EACH){
        padv(P);
        Node *ea=mknode(N_EACH); addkid(ea,e);
        Node *fn=mknode(N_LAMBDA);
        if(curk(P)==T_PIPE) parse_pipe_params(P,fn);
        addkid(fn, parse_do_or_expr(P));
        addkid(ea,fn); e=ea;
      } else {
        Node *m=mknode(N_MEMBER); addkid(m,e);
        m->str=xstrdup(cur(P)->lex); expect(P,T_IDENT,"member name");
        if(curk(P)==T_LPAREN){
          padv(P);
          Node *c=mknode(N_CALL); addkid(c,m);
          if(curk(P)!=T_RPAREN){ do{ addkid(c,parse_expr(P)); }while(accept(P,T_COMMA)); }
          expect(P,T_RPAREN,")"); e=c;
        } else e=m;
      }
    } else if(curk(P)==T_SCOPE){
      padv(P);
      Node *s=mknode(N_SCOPE); addkid(s,e);
      if(curk(P)==T_DATABASE){ s->str=xstrdup("DATABASE"); padv(P); }
      else if(curk(P)==T_TUPLESPACE||curk(P)==T_TUPLESPACE_C){ s->str=xstrdup("tuplespace"); padv(P); }
      else { s->str=xstrdup(cur(P)->lex); expect(P,T_IDENT,"scope name"); }
      if(curk(P)==T_LBRACK){ padv(P);
        Node *region=mknode(N_STR);
        region->str = xstrdup(cur(P)->lex?cur(P)->lex:"region");
        padv(P); expect(P,T_RBRACK,"]");
        addkid(s,region);
      }
      e=s;
    } else break;
  }
  return e;
}

static Node *parse_unary(Parser *P){
  if(curk(P)==T_MINUS||curk(P)==T_NOT){
    Node *u=mknode(N_UNARY); u->str=xstrdup(curk(P)==T_MINUS?"-":"!");
    padv(P); addkid(u,parse_unary(P)); return u;
  }
  return parse_postfix(P);
}
static Node *bin(const char*op,Node*a,Node*b){ Node*n=mknode(N_BINARY); n->str=xstrdup(op); addkid(n,a); addkid(n,b); return n; }
static Node *parse_mul(Parser *P){
  Node*e=parse_unary(P);
  while(curk(P)==T_STARC||curk(P)==T_SLASH||curk(P)==T_PCT){
    const char*o=curk(P)==T_STARC?"*":curk(P)==T_SLASH?"/":"%"; padv(P); e=bin(o,e,parse_unary(P));
  } return e;
}
static Node *parse_add(Parser *P){
  Node*e=parse_mul(P);
  while(curk(P)==T_PLUS||curk(P)==T_MINUS){ const char*o=curk(P)==T_PLUS?"+":"-"; padv(P); e=bin(o,e,parse_mul(P)); } return e;
}
static Node *parse_cmp(Parser *P){
  Node*e=parse_add(P);
  while(curk(P)==T_LT||curk(P)==T_LE||curk(P)==T_GT||curk(P)==T_GE){
    const char*o=curk(P)==T_LT?"<":curk(P)==T_LE?"<=":curk(P)==T_GT?">":">="; padv(P); e=bin(o,e,parse_add(P));
  } return e;
}
static Node *parse_eq(Parser *P){
  Node*e=parse_cmp(P);
  while(curk(P)==T_EQ||curk(P)==T_NE||curk(P)==T_TILDE){
    const char*o=curk(P)==T_EQ?"==":curk(P)==T_NE?"!=":"~"; padv(P); e=bin(o,e,parse_cmp(P));
  } return e;
}
static Node *parse_and(Parser *P){ Node*e=parse_eq(P); while(curk(P)==T_AND){ padv(P); e=bin("&&",e,parse_eq(P)); } return e; }
static Node *parse_or(Parser *P){ Node*e=parse_and(P); while(curk(P)==T_OR){ padv(P); e=bin("||",e,parse_and(P)); } return e; }
static Node *parse_query(Parser *P){
  Node*e=parse_or(P);
  while(curk(P)==T_QUERY||curk(P)==T_ARROW){ padv(P); Node*q=mknode(N_QUERY); addkid(q,e); addkid(q,parse_or(P)); e=q; } return e;
}
static Node *parse_commit(Parser *P){
  Node*e=parse_query(P);
  while(curk(P)==T_COMMIT||curk(P)==T_APPEND){
    int isCommit = (curk(P)==T_COMMIT); padv(P);
    Node*c=mknode(isCommit?N_COMMIT:N_APPEND); addkid(c,e); addkid(c,parse_query(P)); e=c;
  } return e;
}
static Node *parse_expr(Parser *P){ return parse_commit(P); }

static Node *parse_block(Parser *P){
  expect(P,T_LBRACE,"{");
  Node *b=mknode(N_BLOCK);
  while(curk(P)!=T_RBRACE && curk(P)!=T_EOF) addkid(b, parse_decl(P));
  expect(P,T_RBRACE,"}");
  return b;
}

static Node *parse_if(Parser *P){
  expect(P,T_IF,"if");
  int par=accept(P,T_LPAREN);
  Node *n=mknode(N_IF); addkid(n,parse_expr(P));
  if(par) expect(P,T_RPAREN,")");
  addkid(n,parse_block(P));
  if(accept(P,T_ELSE)){
    if(curk(P)==T_IF) addkid(n,parse_if(P));
    else addkid(n,parse_block(P));
  }
  return n;
}
static Node *parse_while(Parser *P){
  expect(P,T_WHILE,"while");
  int par=accept(P,T_LPAREN);
  Node *n=mknode(N_WHILE); addkid(n,parse_expr(P));
  if(par) expect(P,T_RPAREN,")");
  addkid(n,parse_block(P));
  return n;
}
static Node *parse_for(Parser *P){
  expect(P,T_FOR,"for");
  Node *n=mknode(N_FOR);
  n->str=xstrdup(cur(P)->lex); expect(P,T_IDENT,"loop var");
  expect(P,T_IN,"in");
  addkid(n,parse_expr(P));
  addkid(n,parse_block(P));
  return n;
}
static Node *parse_print(Parser *P){
  expect(P,T_PRINT,"print");
  int par=accept(P,T_LPAREN);
  Node *n=mknode(N_PRINT);
  if(curk(P)!=T_RPAREN && curk(P)!=T_SEMI && curk(P)!=T_RBRACE){
    do { addkid(n,parse_expr(P)); } while(accept(P,T_COMMA));
  }
  if(par) expect(P,T_RPAREN,")");
  return n;
}

static Node *parse_stmt(Parser *P){
  switch(curk(P)){
    case T_IF: return parse_if(P);
    case T_WHILE: return parse_while(P);
    case T_FOR: return parse_for(P);
    case T_PRINT: { Node*n=parse_print(P); accept(P,T_SEMI); return n; }
    case T_RETURN:{ padv(P); Node*n=mknode(N_RETURN);
      if(curk(P)!=T_RBRACE&&curk(P)!=T_SEMI&&!(curk(P)==T_IDENT&&!strcmp(cur(P)->lex,"end")))
        addkid(n,parse_expr(P));
      accept(P,T_SEMI); return n; }
    default: break;
  }
  if(curk(P)==T_IDENT && wordset_has(&STMT_WORDS, cur(P)->lex)
     && P->t[P->i+1].kind!=T_BIND && P->t[P->i+1].kind!=T_ASSIGN){
    char *w=xstrdup(cur(P)->lex); padv(P);
    Node *ex=mknode(N_EXTENDED); ex->str=w;
    addkid(ex, parse_primary(P));
    accept(P,T_SEMI);
    return ex;
  }
  if(curk(P)==T_IDENT && P->t[P->i+1].kind==T_BIND){
    Node*n=mknode(N_BIND); n->str=xstrdup(cur(P)->lex); padv(P); padv(P);
    addkid(n,parse_expr(P)); accept(P,T_SEMI); return n;
  }
  {
    size_t save=P->i;
    Node *lhs=parse_expr(P);
    if(curk(P)==T_ASSIGN){
      padv(P);
      Node*n=mknode(N_ASSIGN); addkid(n,lhs); addkid(n,parse_expr(P));
      accept(P,T_SEMI); return n;
    }
    (void)save;
    accept(P,T_SEMI);
    return lhs;
  }
}

static Node *parse_func(Parser *P){
  expect(P,T_DEF,"def");
  Node *fn=mknode(N_FUNC);
  fn->str=xstrdup(cur(P)->lex); expect(P,T_IDENT,"function name");
  if(curk(P)==T_PIPE) parse_pipe_params(P,fn);
  else if(curk(P)==T_LPAREN){ padv(P);
    if(curk(P)!=T_RPAREN){ do{ addparam(fn,cur(P)->lex); expect(P,T_IDENT,"param"); }while(accept(P,T_COMMA)); }
    expect(P,T_RPAREN,")");
  }
  if(curk(P)==T_LBRACE){ addkid(fn,parse_block(P)); }
  else {
    if(curk(P)==T_COMMIT||curk(P)==T_QUERY||curk(P)==T_DEFARROW||curk(P)==T_ASSIGN) padv(P);
    Node *ret=mknode(N_RETURN); addkid(ret,parse_expr(P));
    Node *blk=mknode(N_BLOCK); addkid(blk,ret);
    addkid(fn,blk);
    accept(P,T_SEMI);
  }
  return fn;
}

static Node *parse_asperal(Parser *P){
  expect(P,T_ASPERAL,"asperal");
  Node *a=mknode(N_ASPERAL);
  if(curk(P)==T_PIPE){
    parse_pipe_params(P,a);
    accept(P,T_DEFARROW);
    addkid(a, parse_block(P));
  } else {
    a->str = xstrdup(cur(P)->lex?cur(P)->lex:"anon");
    if(curk(P)==T_IDENT||curk(P)==T_TUPLESPACE_C||curk(P)==T_TUPLESPACE) padv(P);
    accept(P,T_COLON);
    accept(P,T_STRUCT);
    while(curk(P)!=T_LBRACE && curk(P)!=T_EOF) padv(P);
    addkid(a, parse_block(P));
  }
  return a;
}

static Node *parse_typedef(Parser *P){
  expect(P,T_TYPEDEF,"typedef");
  Node *n=mknode(N_TYPEDEF);
  while(curk(P)!=T_LBRACE && curk(P)!=T_EOF) padv(P);
  addkid(n,parse_block(P));
  return n;
}

static Node *parse_omega_block(Parser *P){
  expect(P,T_OMEGA,"Omega");
  expect(P,T_SCOPE,"::");
  Node *n=mknode(N_OMEGABLOCK);
  if(curk(P)==T_DATABASE){ n->str=xstrdup("DATABASE"); padv(P); }
  else if(curk(P)==T_TUPLESPACE||curk(P)==T_TUPLESPACE_C){ n->str=xstrdup("tuplespace"); padv(P); }
  else { n->str=xstrdup("DATABASE"); }
  if(curk(P)==T_LBRACK){ padv(P);
    if(curk(P)!=T_RBRACK) padv(P);
    expect(P,T_RBRACK,"]"); }
  if(curk(P)==T_LT){ padv(P); if(curk(P)==T_IDENT||curk(P)==T_DATABASE) padv(P); }
  addkid(n,parse_block(P));
  return n;
}

static Node *parse_rule(Parser *P);
static Node *parse_reviser(Parser *P){
  expect(P,T_REVISER,"@reviser");
  Node *n=mknode(N_REVISER);
  while(curk(P)!=T_LBRACE && curk(P)!=T_EOF) padv(P);
  expect(P,T_LBRACE,"{");
  while(curk(P)!=T_RBRACE && curk(P)!=T_EOF){
    if(curk(P)==T_IDENT && !strcmp(cur(P)->lex,"rule")) addkid(n,parse_rule(P));
    else addkid(n,parse_decl(P));
  }
  expect(P,T_RBRACE,"}");
  return n;
}

static Node *parse_rule(Parser *P){
  padv(P);
  Node *r=mknode(N_RULE);
  r->str = xstrdup(cur(P)->lex?cur(P)->lex:"r");
  padv(P);
  Node *head=mknode(N_STR); head->str=xstrdup(cur(P)->lex?cur(P)->lex:"stmt"); padv(P);
  addkid(r,head);
  Node *pat=mknode(N_ARRAY);
  expect(P,T_LBRACK,"[");
  while(curk(P)!=T_RBRACK && curk(P)!=T_EOF){
    Node *tk=mknode(N_STR);
    if(curk(P)==T_STRING) tk->str=xstrdup(cur(P)->lex);
    else if(cur(P)->lex) tk->str=xstrdup(cur(P)->lex);
    else tk->str=xstrdup(tok_name(curk(P)));
    padv(P);
    addkid(pat,tk);
  }
  expect(P,T_RBRACK,"]");
  addkid(r,pat);
  accept(P,T_QUERY); accept(P,T_ARROW); accept(P,T_DEFARROW);
  addkid(r, parse_expr(P));
  accept(P,T_SEMI);
  if(pat->nkid>0 && pat->kids[0]->str){
    const char *trigger = pat->kids[0]->str;
    if(!strcmp(head->str,"postfix")) wordset_add(&POSTFIX_WORDS, trigger);
    else if(!strcmp(head->str,"stmt")) wordset_add(&STMT_WORDS, trigger);
  }
  return r;
}

static Node *parse_decl(Parser *P){
  switch(curk(P)){
    case T_OMEGA:
      if(P->t[P->i+1].kind==T_SCOPE &&
         (P->t[P->i+2].kind==T_DATABASE||P->t[P->i+2].kind==T_TUPLESPACE||P->t[P->i+2].kind==T_TUPLESPACE_C))
        return parse_omega_block(P);
      break;
    case T_TUPLESPACE_C: case T_TUPLESPACE:
      if(P->t[P->i+1].kind==T_LT){ Node*n=mknode(N_OMEGABLOCK); n->str=xstrdup("tuplespace");
        padv(P); padv(P); if(curk(P)==T_DATABASE||curk(P)==T_IDENT) padv(P);
        addkid(n,parse_block(P)); return n; }
      break;
    case T_ASPERAL: return parse_asperal(P);
    case T_TYPEDEF: return parse_typedef(P);
    case T_DEF: return parse_func(P);
    case T_REVISER: return parse_reviser(P);
    default: break;
  }
  return parse_stmt(P);
}

static Node *parse_program(Parser *P){
  Node *prog=mknode(N_PROGRAM);
  while(curk(P)!=T_EOF) addkid(prog, parse_decl(P));
  return prog;
}

typedef enum { V_NIL, V_NUM, V_BOOL, V_STR, V_ARR, V_FUN, V_BUILTIN, V_STAR, V_LEDGER } VKind;
typedef struct Value Value;
typedef struct Env Env;
typedef struct { Value *items; int n, cap; } Arr;
struct Value { VKind kind; double num; int b; char *str; Arr *arr; Node *fn; Env *clo; int builtin; };

static Value VNIL(){ Value v; memset(&v,0,sizeof v); v.kind=V_NIL; return v; }
static Value VNUM(double x){ Value v; memset(&v,0,sizeof v); v.kind=V_NUM; v.num=x; return v; }
static Value VBOOL(int b){ Value v; memset(&v,0,sizeof v); v.kind=V_BOOL; v.b=b; return v; }
static Value VSTR(const char*s){ Value v; memset(&v,0,sizeof v); v.kind=V_STR; v.str=xstrdup(s); return v; }
static Value VSTAR(){ Value v; memset(&v,0,sizeof v); v.kind=V_STAR; return v; }

static Arr *arr_new(){ Arr*a=xmalloc(sizeof(Arr)); a->items=NULL;a->n=0;a->cap=0; return a; }
static void arr_push(Arr*a, Value v){ if(a->n==a->cap){ a->cap=a->cap?a->cap*2:8; a->items=xrealloc(a->items,a->cap*sizeof(Value)); } a->items[a->n++]=v; }
static Value VARR(Arr*a){ Value v; memset(&v,0,sizeof v); v.kind=V_ARR; v.arr=a; return v; }

typedef struct Binding { char*name; Value val; struct Binding*next; } Binding;
struct Env { Binding*head; Env*parent; };
static Env *env_new(Env*parent){ Env*e=xmalloc(sizeof(Env)); e->head=NULL; e->parent=parent; return e; }
static void env_bind(Env*e, const char*name, Value v){ Binding*b=xmalloc(sizeof(Binding)); b->name=xstrdup(name); b->val=v; b->next=e->head; e->head=b; }
static Binding *env_find(Env*e, const char*name){
  for(Env*s=e;s;s=s->parent) for(Binding*b=s->head;b;b=b->next) if(!strcmp(b->name,name)) return b;
  return NULL;
}

typedef struct { char*region; Value v; } Fact;
typedef struct { Fact*facts; int n, cap; } Ledger;
static Ledger LEDGER = {0,0,0};
static int ledger_append(const char*region, Value v){
  if(LEDGER.n==LEDGER.cap){ LEDGER.cap=LEDGER.cap?LEDGER.cap*2:16; LEDGER.facts=xrealloc(LEDGER.facts,LEDGER.cap*sizeof(Fact)); }
  LEDGER.facts[LEDGER.n].region=xstrdup(region?region:"tuplespace");
  LEDGER.facts[LEDGER.n].v=v;
  return LEDGER.n++;
}

typedef struct { char *name, *head; Node *pattern; Node *denot; } Rule;
typedef struct { Rule*rules; int n, cap; } RuleLedger;
static RuleLedger GRAMMAR = {0,0,0};
static void grammar_commit(const char*name,const char*head,Node*pat,Node*den){
  if(GRAMMAR.n==GRAMMAR.cap){ GRAMMAR.cap=GRAMMAR.cap?GRAMMAR.cap*2:8; GRAMMAR.rules=xrealloc(GRAMMAR.rules,GRAMMAR.cap*sizeof(Rule)); }
  Rule*r=&GRAMMAR.rules[GRAMMAR.n++];
  r->name=xstrdup(name); r->head=xstrdup(head); r->pattern=pat; r->denot=den;
}

static void softmax_vec(const double*z,int n,double*out){
  double mx=z[0]; for(int i=1;i<n;i++) if(z[i]>mx) mx=z[i];
  double s=0;
  for(int i=0;i<n;i++){
    if(z[i]==-INFINITY || (mx - z[i]) > 700.0) out[i]=0.0;
    else out[i]=exp(z[i]-mx);
    s+=out[i];
  }
  for(int i=0;i<n;i++) out[i]/=s;
}
static double shannon_entropy(const double*q,int n){
  double h=0; for(int i=0;i<n;i++){ double x=q[i]; if(x>1e-12) h-= x*log(x); } return h;
}
static void cognitive_system(const double*z,int V, double**qm,double**phim,double*beta,int M, double*q_hat,double*maxdiff){
  double *a=xmalloc(V*sizeof(double)); softmax_vec(z,V,a);
  double *theta=xmalloc(V*sizeof(double)); for(int i=0;i<V;i++) theta[i]=0.0;
  for(int m=0;m<M;m++){
    double H=shannon_entropy(qm[m],V);
    for(int i=0;i<V;i++) theta[i]+= beta[m]*H*phim[m][i];
  }
  double sum=0; double *mag2=xmalloc(V*sizeof(double));
  for(int i=0;i<V;i++){
    double complex psi = sqrt(a[i]) * cexp(I*theta[i]);
    mag2[i]= creal(psi*conj(psi));
    sum+=mag2[i];
  }
  double md=0;
  for(int i=0;i<V;i++){ q_hat[i]=mag2[i]/sum; double d=fabs(q_hat[i]-a[i]); if(d>md) md=d; }
  *maxdiff=md;
  free(a); free(theta); free(mag2);
}

typedef struct { int is_return; Value val; } Eval;
static Value eval_node(Node*n, Env*e);
static Eval exec_block(Node*blk, Env*e);
static Eval exec_stmt(Node*n, Env*e);

static int truthy(Value v){
  switch(v.kind){
    case V_NIL: return 0;
    case V_BOOL:return v.b;
    case V_NUM: return v.num!=0;
    case V_STR: return v.str && v.str[0];
    case V_ARR: return v.arr && v.arr->n>0;
    default: return 1;
  }
}
static int val_eq(Value a, Value b){
  if(a.kind==V_STAR||b.kind==V_STAR) return 0;
  if(a.kind!=b.kind){
    if((a.kind==V_NUM&&b.kind==V_BOOL)) return a.num==b.b;
    if((a.kind==V_BOOL&&b.kind==V_NUM)) return a.b==b.num;
    return 0;
  }
  switch(a.kind){
    case V_NUM:return a.num==b.num;
    case V_BOOL:return a.b==b.b;
    case V_STR:return !strcmp(a.str,b.str);
    case V_NIL:return 1;
    default:return 0;
  }
}
static void print_val(Value v){
  switch(v.kind){
    case V_NIL: printf("nil"); break;
    case V_BOOL:printf(v.b?"true":"false"); break;
    case V_STAR:printf("star"); break;
    case V_STR: printf("%s",v.str); break;
    case V_NUM:{ double r=v.num; if(r==(long long)r && fabs(r)<1e15) printf("%lld",(long long)r);
      else printf("%g",r); } break;
    case V_ARR:{ printf("["); for(int i=0;i<v.arr->n;i++){ if(i)printf(", "); print_val(v.arr->items[i]); } printf("]"); } break;
    case V_FUN: printf("<fn>"); break;
    case V_BUILTIN: printf("<builtin>"); break;
    case V_LEDGER: printf("<ledger>"); break;
  }
}

enum { B_SOFTMAX,B_ENTROPY,B_UNKNOWN_PRIOR,B_UPDATE,B_MANIFOLD_EMBED,B_COGNITIVE,
  B_DIST,B_ZEROS_OF,B_MAXDIFF,B_LAST_A,B_LEDGER,B_LEN,B_SQRT,B_LOG,B_EXP,
  B_ABS,B_F5,B_SCI,B_CHAR_AT,B_STRLEN,B_PHASE_UNIFORM,B_COMMIT_MEASURE,
  B_PREPARE_UNKNOWN,B_OBSERVE,B_ESTIMATE,B_FORBIDDEN,
  B_RANGE,B_FLOOR,B_F3,B_SUM,B_MAX_OF,B_MIN_OF,B_PI,B_POW,B_KL,B_PUSH,
  B_NBUILTIN };
static const char* BNAMES[B_NBUILTIN]={
  "softmax","entropy","unknown_prior","update","manifold_embed","cognitive_system",
  "dist","zeros_of","maxdiff","last_a","ledger","len","sqrt","log","exp","abs",
  "f5","sci","char_at","length","phase_uniform","commit_measurement",
  "prepare_unknown","observe","estimate","forbidden",
  "range","floor","f3","sum","max_of","min_of","pi","pow","kl_divergence","push" };

static double G_LAST_MAXDIFF = 0.0;
static Arr *G_LAST_A = NULL;

static Value num_arr_to_val(const double*x,int n){ Arr*a=arr_new(); for(int i=0;i<n;i++) arr_push(a,VNUM(x[i])); return VARR(a); }
static double* val_to_num_arr(Value v,int*n){
  if(v.kind!=V_ARR){ *n=0; return NULL; }
  *n=v.arr->n; double*x=xmalloc((*n>0?*n:1)*sizeof(double));
  for(int i=0;i<*n;i++) x[i]= v.arr->items[i].kind==V_NUM ? v.arr->items[i].num : 0.0;
  return x;
}

static Value call_builtin(int idx, Value*args, int nargs);

static Value call_function(Value fn, Value*args, int nargs){
  if(fn.kind==V_BUILTIN) return call_builtin(fn.builtin,args,nargs);
  if(fn.kind!=V_FUN){ fprintf(stderr,"runtime error: not callable\n"); exit(1); }
  Env *local=env_new(fn.clo);
  Node *node=fn.fn;
  for(int i=0;i<node->nparam;i++) env_bind(local, node->params[i], i<nargs?args[i]:VNIL());
  Node *body = node->kids[node->nkid-1];
  if(body->kind==N_BLOCK){ Eval r = exec_block(body, local); return r.is_return ? r.val : VNIL(); }
  return eval_node(body, local);
}

static void assign_lvalue(Node*lhs, Value v, Env*e){
  if(lhs->kind==N_IDENT){
    Binding*b=env_find(e,lhs->str);
    if(b) b->val=v; else env_bind(e,lhs->str,v);
    return;
  }
  if(lhs->kind==N_INDEX){
    Value base=eval_node(lhs->kids[0],e);
    Value idx =eval_node(lhs->kids[1],e);
    if(base.kind==V_ARR && idx.kind==V_NUM){ int i=(int)idx.num; if(i>=0 && i<base.arr->n) base.arr->items[i]=v; }
    return;
  }
  fprintf(stderr,"runtime error: bad assignment target\n"); exit(1);
}

static Value eval_extended(Node*n, Env*e){
  for(int r=GRAMMAR.n-1;r>=0;r--){
    Rule *R=&GRAMMAR.rules[r];
    if(R->pattern && R->pattern->nkid>0 && R->pattern->kids[0]->str
       && !strcmp(R->pattern->kids[0]->str, n->str)){
      Env*local=env_new(e);
      for(int i=0;i<n->nkid;i++){
        char hole[16]; snprintf(hole,16,"_%d",i+1);
        env_bind(local, hole, eval_node(n->kids[i],e));
      }
      return eval_node(R->denot, local);
    }
  }
  if(n->nkid>=1){
    Binding*b=env_find(e,n->str);
    if(b && (b->val.kind==V_FUN||b->val.kind==V_BUILTIN)){
      Value a=eval_node(n->kids[0],e);
      Value args[1]={a};
      return call_function(b->val,args,1);
    }
  }
  return VNIL();
}

static Value eval_node(Node*n, Env*e){
  switch(n->kind){
    case N_INT: case N_FLOAT: return VNUM(n->num);
    case N_BOOL: return VBOOL((int)n->num);
    case N_STR: return VSTR(n->str);
    case N_NIL: return VNIL();
    case N_STARLIT: return VSTAR();
    case N_OMEGA: case N_TUPLESPACE: { Value v; memset(&v,0,sizeof v); v.kind=V_LEDGER; return v; }
    case N_IDENT: {
      Binding*b=env_find(e,n->str);
      if(b) return b->val;
      for(int i=0;i<B_NBUILTIN;i++) if(!strcmp(BNAMES[i],n->str)){ Value v; memset(&v,0,sizeof v); v.kind=V_BUILTIN; v.builtin=i; return v; }
      return VNIL();
    }
    case N_ARRAY: { Arr*a=arr_new(); for(int i=0;i<n->nkid;i++) arr_push(a, eval_node(n->kids[i],e)); return VARR(a); }
    case N_LAMBDA: { Value v; memset(&v,0,sizeof v); v.kind=V_FUN; v.fn=n; v.clo=e; return v; }
    case N_BIND: { Value v=eval_node(n->kids[0],e); env_bind(e,n->str,v); return v; }
    case N_ASSIGN: { Value v=eval_node(n->kids[1],e); assign_lvalue(n->kids[0],v,e); return v; }
    case N_UNARY: {
      Value a=eval_node(n->kids[0],e);
      if(!strcmp(n->str,"-")) return VNUM(-(a.kind==V_NUM?a.num:0));
      return VBOOL(!truthy(a));
    }
    case N_BINARY: {
      const char*o=n->str;
      if(!strcmp(o,"&&")){ Value a=eval_node(n->kids[0],e); if(!truthy(a))return VBOOL(0); return VBOOL(truthy(eval_node(n->kids[1],e))); }
      if(!strcmp(o,"||")){ Value a=eval_node(n->kids[0],e); if(truthy(a))return VBOOL(1); return VBOOL(truthy(eval_node(n->kids[1],e))); }
      Value a=eval_node(n->kids[0],e), b=eval_node(n->kids[1],e);
      if(!strcmp(o,"~")){ if(a.kind==V_STAR||b.kind==V_STAR) return VBOOL(1); return VBOOL(val_eq(a,b)); }
      if(!strcmp(o,"==")) return VBOOL(val_eq(a,b));
      if(!strcmp(o,"!=")) return VBOOL(!val_eq(a,b));
      double x=a.kind==V_NUM?a.num:0, y=b.kind==V_NUM?b.num:0;
      if(!strcmp(o,"+")){
        if(a.kind==V_STR||b.kind==V_STR){ char buf[512]; char la[128],lb[128];
          if(a.kind==V_STR) snprintf(la,128,"%s",a.str); else snprintf(la,128,"%g",x);
          if(b.kind==V_STR) snprintf(lb,128,"%s",b.str); else snprintf(lb,128,"%g",y);
          snprintf(buf,512,"%s%s",la,lb); return VSTR(buf); }
        return VNUM(x+y);
      }
      if(!strcmp(o,"-")) return VNUM(x-y);
      if(!strcmp(o,"*")) return VNUM(x*y);
      if(!strcmp(o,"/")) return VNUM(y!=0?x/y:0);
      if(!strcmp(o,"%")) return VNUM(y!=0?fmod(x,y):0);
      if(!strcmp(o,"<")) return VBOOL(x<y);
      if(!strcmp(o,"<="))return VBOOL(x<=y);
      if(!strcmp(o,">")) return VBOOL(x>y);
      if(!strcmp(o,">="))return VBOOL(x>=y);
      return VNIL();
    }
    case N_QUERY: {
      Value a=eval_node(n->kids[0],e);
      Value b=eval_node(n->kids[1],e);
      if(b.kind==V_FUN||b.kind==V_BUILTIN){ Value args[1]={a}; return call_function(b,args,1); }
      Arr*pair=arr_new(); arr_push(pair,a); arr_push(pair,b); return VARR(pair);
    }
    case N_COMMIT: { Value left=eval_node(n->kids[0],e); ledger_append("tuplespace", left); return eval_node(n->kids[1],e); }
    case N_APPEND: {
      Value arrv=eval_node(n->kids[0],e);
      Value elem=eval_node(n->kids[1],e);
      if(arrv.kind==V_ARR) arr_push(arrv.arr, elem);
      return arrv;
    }
    case N_INDEX: {
      Value base=eval_node(n->kids[0],e), idx=eval_node(n->kids[1],e);
      if(base.kind==V_ARR && idx.kind==V_NUM){ int i=(int)idx.num; if(i>=0&&i<base.arr->n) return base.arr->items[i]; }
      if(base.kind==V_STR && idx.kind==V_NUM){ int i=(int)idx.num;
        if(i>=0&&i<(int)strlen(base.str)){ char s[2]={base.str[i],0}; return VSTR(s);} }
      return VNIL();
    }
    case N_MEMBER: {
      Value base=eval_node(n->kids[0],e);
      if(!strcmp(n->str,"length")||!strcmp(n->str,"len")){
        if(base.kind==V_ARR) return VNUM(base.arr->n);
        if(base.kind==V_STR) return VNUM(strlen(base.str));
      }
      if(!strcmp(n->str,"frozen")) return base;
      if(!strcmp(n->str,"normalize")||!strcmp(n->str,"normalized")){
        if(base.kind==V_ARR){ double s=0; for(int i=0;i<base.arr->n;i++) s+=base.arr->items[i].num;
          Arr*r=arr_new(); for(int i=0;i<base.arr->n;i++) arr_push(r,VNUM(s!=0?base.arr->items[i].num/s:0));
          return VARR(r);} }
      return base;
    }
    case N_SCOPE: { Value v; memset(&v,0,sizeof v); v.kind=V_LEDGER; return v; }
    case N_CALL: {
      Node*callee=n->kids[0];
      if(callee->kind==N_MEMBER){
        Value base=eval_node(callee->kids[0],e);
        const char*m=callee->str;
        int na=n->nkid-1; Value*args=na?xmalloc(na*sizeof(Value)):NULL;
        for(int i=0;i<na;i++) args[i]=eval_node(n->kids[i+1],e);
        if(!strcmp(m,"scan")||!strcmp(m,"read")){
          Arr*out=arr_new();
          if(base.kind==V_ARR && na>=1){
            for(int i=0;i<base.arr->n;i++){ Value one[1]={base.arr->items[i]};
              if(truthy(call_function(args[0],one,1))) arr_push(out,base.arr->items[i]); } }
          return VARR(out);
        }
        if(!strcmp(m,"map")){
          Arr*out=arr_new();
          if(base.kind==V_ARR && na>=1){
            for(int i=0;i<base.arr->n;i++){ Value one[1]={base.arr->items[i]};
              arr_push(out, call_function(args[0],one,1)); } }
          return VARR(out);
        }
        if(!strcmp(m,"fold")||!strcmp(m,"reduce")){
          if(base.kind==V_ARR && na>=2){
            Value acc=args[0];
            for(int i=0;i<base.arr->n;i++){ Value two[2]={acc,base.arr->items[i]}; acc=call_function(args[1],two,2); }
            return acc;
          }
        }
        if(!strcmp(m,"append")){ if(base.kind==V_ARR && na>=1){ arr_push(base.arr,args[0]); return VNUM(base.arr->n-1);} }
        if(base.kind==V_LEDGER && !strcmp(m,"append")){ if(na>=1){ int id=ledger_append("tuplespace",args[0]); return VNUM(id);} }
        for(int i=0;i<B_NBUILTIN;i++) if(!strcmp(BNAMES[i],m)) return call_builtin(i,args,na);
        return base;
      }
      Value f=eval_node(callee,e);
      int na=n->nkid-1; Value*args=na?xmalloc(na*sizeof(Value)):NULL;
      for(int i=0;i<na;i++) args[i]=eval_node(n->kids[i+1],e);
      return call_function(f,args,na);
    }
    case N_EACH: {
      Value coll=eval_node(n->kids[0],e);
      Value fn=eval_node(n->kids[1],e);
      if(coll.kind==V_ARR){
        for(int i=0;i<coll.arr->n;i++){ Value one[1]={coll.arr->items[i]}; call_function(fn,one,1); }
      }
      return coll;
    }
    case N_EXTENDED: return eval_extended(n,e);
    default: return VNIL();
  }
}

static Eval exec_stmt(Node*n, Env*e){
  Eval r={0,VNIL()};
  switch(n->kind){
    case N_RETURN: r.is_return=1; r.val = n->nkid? eval_node(n->kids[0],e):VNIL(); return r;
    case N_PRINT: {
      for(int i=0;i<n->nkid;i++){ if(i) printf(" "); print_val(eval_node(n->kids[i],e)); }
      printf("\n"); return r;
    }
    case N_IF: {
      if(truthy(eval_node(n->kids[0],e))) return exec_block(n->kids[1],e);
      else if(n->nkid>2){ if(n->kids[2]->kind==N_IF) return exec_stmt(n->kids[2],e); else return exec_block(n->kids[2],e); }
      return r;
    }
    case N_WHILE: {
      while(truthy(eval_node(n->kids[0],e))){ Eval x=exec_block(n->kids[1],e); if(x.is_return) return x; }
      return r;
    }
    case N_FOR: {
      Value coll=eval_node(n->kids[0],e);
      if(coll.kind==V_ARR){ Env*l=env_new(e);
        for(int i=0;i<coll.arr->n;i++){ env_bind(l,n->str,coll.arr->items[i]);
          Eval x=exec_block(n->kids[1],l); if(x.is_return) return x; } }
      return r;
    }
    case N_BLOCK: return exec_block(n,e);
    default: eval_node(n,e); return r;
  }
}

static Eval exec_block(Node*blk, Env*e){
  Eval r={0,VNIL()};
  for(int i=0;i<blk->nkid;i++){ r=exec_stmt(blk->kids[i],e); if(r.is_return) return r; }
  return r;
}

static Value call_builtin(int idx, Value*args, int nargs){
  switch(idx){
    case B_SOFTMAX:{ int n; double*z=val_to_num_arr(nargs?args[0]:VNIL(),&n);
      if(n==0) return VNIL(); double*o=xmalloc(n*sizeof(double)); softmax_vec(z,n,o);
      Value v=num_arr_to_val(o,n); free(z);free(o); return v; }
    case B_ENTROPY:{ int n; double*q=val_to_num_arr(nargs?args[0]:VNIL(),&n);
      double h=shannon_entropy(q,n); free(q); return VNUM(h); }
    case B_UNKNOWN_PRIOR:{ int V = nargs?(int)args[0].num:0; if(V<=0) return VNIL();
      double*o=xmalloc(V*sizeof(double)); for(int i=0;i<V;i++)o[i]=1.0/V;
      Value v=num_arr_to_val(o,V); free(o); return v; }
    case B_UPDATE:{ int n,m; double*pri=val_to_num_arr(args[0],&n); double*ev=val_to_num_arr(args[1],&m);
      double lr = nargs>2?args[2].num:0.5; if(n==0){free(pri);free(ev);return VNIL();}
      double*o=xmalloc(n*sizeof(double)); double s=0;
      for(int i=0;i<n;i++){ o[i]=(1-lr)*pri[i]+lr*(i<m?ev[i]:0); s+=o[i]; }
      for(int i=0;i<n;i++) o[i]/= (s!=0?s:1);
      Value v=num_arr_to_val(o,n); free(pri);free(ev);free(o); return v; }
    case B_MANIFOLD_EMBED:{
      int n; double*x=val_to_num_arr(nargs?args[0]:VNIL(),&n); if(n==0)return VNIL();
      double nrm=0; for(int i=0;i<n;i++) nrm+=x[i]*x[i]; nrm=sqrt(nrm)+1e-12;
      double*o=xmalloc(n*sizeof(double)); for(int i=0;i<n;i++)o[i]=x[i]/nrm;
      Value v=num_arr_to_val(o,n); free(x);free(o); return v; }
    case B_COGNITIVE:{
      int V; double*z=val_to_num_arr(args[0],&V); if(V==0)return VNIL();
      int M=0; double**qm=NULL,**phim=NULL,*beta=NULL;
      if(nargs>1 && args[1].kind==V_ARR){ M=args[1].arr->n;
        qm=xmalloc((M>0?M:1)*sizeof(double*)); phim=xmalloc((M>0?M:1)*sizeof(double*));
        for(int m=0;m<M;m++){ Value pair=args[1].arr->items[m]; int a,b;
          if(pair.kind==V_ARR && pair.arr->n>=2){
            qm[m]=val_to_num_arr(pair.arr->items[0],&a);
            phim[m]=val_to_num_arr(pair.arr->items[1],&b);
            if(a<V||b<V){ double*Q=xmalloc(V*sizeof(double)),*PH=xmalloc(V*sizeof(double));
              for(int i=0;i<V;i++){Q[i]=i<a?qm[m][i]:1.0/V; PH[i]=i<b?phim[m][i]:0;} free(qm[m]);free(phim[m]);qm[m]=Q;phim[m]=PH; }
          } else { qm[m]=xmalloc(V*sizeof(double)); phim[m]=xmalloc(V*sizeof(double));
            for(int i=0;i<V;i++){qm[m][i]=1.0/V;phim[m][i]=0;} }
        }
      }
      beta=xmalloc((M>0?M:1)*sizeof(double));
      if(nargs>2 && args[2].kind==V_ARR) for(int m=0;m<M;m++) beta[m]= m<args[2].arr->n?args[2].arr->items[m].num:1.0;
      else for(int m=0;m<M;m++) beta[m]=1.0;
      double*q_hat=xmalloc(V*sizeof(double)),md;
      cognitive_system(z,V,qm,phim,beta,M,q_hat,&md);
      G_LAST_MAXDIFF=md;
      if(!G_LAST_A) G_LAST_A=arr_new(); G_LAST_A->n=0;
      double*a=xmalloc(V*sizeof(double)); softmax_vec(z,V,a);
      for(int i=0;i<V;i++) arr_push(G_LAST_A,VNUM(a[i]));
      Value out=num_arr_to_val(q_hat,V);
      ledger_append("tuplespace", out);
      free(z);free(beta);free(q_hat);free(a);
      for(int m=0;m<M;m++){free(qm[m]);free(phim[m]);} free(qm);free(phim);
      return out;
    }
    case B_DIST:{ int n; double*z=val_to_num_arr(nargs?args[0]:VNIL(),&n); if(n==0)return VNIL();
      double*o=xmalloc(n*sizeof(double)); softmax_vec(z,n,o); Value v=num_arr_to_val(o,n); free(z);free(o); return v; }
    case B_ZEROS_OF:{ int n; double*q=val_to_num_arr(nargs?args[0]:VNIL(),&n);
      Arr*z=arr_new(); for(int i=0;i<n;i++) if(q[i]==0.0) arr_push(z,VNUM(i)); free(q); return VARR(z); }
    case B_MAXDIFF: return VNUM(G_LAST_MAXDIFF);
    case B_LAST_A: return G_LAST_A?VARR(G_LAST_A):VNIL();
    case B_LEDGER:{ Arr*a=arr_new(); for(int i=0;i<LEDGER.n;i++) arr_push(a,LEDGER.facts[i].v); return VARR(a); }
    case B_LEN:{ Value v=nargs?args[0]:VNIL(); if(v.kind==V_ARR)return VNUM(v.arr->n);
      if(v.kind==V_STR)return VNUM(strlen(v.str)); return VNUM(0); }
    case B_SQRT: return VNUM(sqrt(nargs?args[0].num:0));
    case B_LOG: return VNUM(log(nargs?args[0].num:1));
    case B_EXP: return VNUM(exp(nargs?args[0].num:0));
    case B_ABS: return VNUM(fabs(nargs?args[0].num:0));
    case B_F5:{ char b[64]; snprintf(b,64,"%.5f",nargs?args[0].num:0); return VSTR(b); }
    case B_SCI:{ char b[64]; snprintf(b,64,"%.2e",nargs?args[0].num:0); return VSTR(b); }
    case B_CHAR_AT:{ Value s=args[0]; int i=(int)args[1].num;
      if(s.kind==V_STR && i>=0 && i<(int)strlen(s.str)){ char c[2]={s.str[i],0}; return VSTR(c);} return VSTR(""); }
    case B_STRLEN: return VNUM(nargs&&args[0].kind==V_STR?strlen(args[0].str):0);
    case B_PHASE_UNIFORM:{
      int nq = nargs?(int)args[0].num:1; int V=1; for(int i=0;i<nq;i++)V*=2;
      double*z=xmalloc(V*sizeof(double)); for(int i=0;i<V;i++)z[i]=0;
      double*qm=xmalloc(V*sizeof(double)),*ph=xmalloc(V*sizeof(double));
      for(int i=0;i<V;i++){qm[i]=1.0/V; ph[i]=(i%2)?M_PI:0;}
      double*qh=xmalloc(V*sizeof(double)),md; double*Q[1]={qm};double*PH[1]={ph};double B[1]={1.0};
      cognitive_system(z,V,Q,PH,B,1,qh,&md); G_LAST_MAXDIFF=md;
      Value v=num_arr_to_val(qh,V); free(z);free(qm);free(ph);free(qh); return v; }
    case B_COMMIT_MEASURE:{ Value reg=nargs?args[0]:VNIL(); ledger_append("tuplespace",reg); return reg; }
    case B_PREPARE_UNKNOWN:{ int nq=nargs?(int)args[0].num:1; int V=1; for(int i=0;i<nq;i++)V*=2;
      double*o=xmalloc(V*sizeof(double)); for(int i=0;i<V;i++)o[i]=1.0/V; Value v=num_arr_to_val(o,V); free(o); return v; }
    case B_OBSERVE:{ Value reg=nargs?args[0]:VNIL(); ledger_append("tuplespace",reg); return reg; }
    case B_ESTIMATE:{
      int V=0; for(int i=0;i<LEDGER.n;i++) if(LEDGER.facts[i].v.kind==V_ARR && LEDGER.facts[i].v.arr->n>V) V=LEDGER.facts[i].v.arr->n;
      if(V==0) return VNIL(); double*acc=xmalloc(V*sizeof(double)); for(int i=0;i<V;i++)acc[i]=0; int cnt=0;
      for(int i=0;i<LEDGER.n;i++){ Value f=LEDGER.facts[i].v; if(f.kind==V_ARR&&f.arr->n==V){ cnt++;
        for(int j=0;j<V;j++) acc[j]+= f.arr->items[j].kind==V_NUM?f.arr->items[j].num:0; } }
      double s=0; for(int i=0;i<V;i++){ acc[i]/= (cnt?cnt:1); s+=acc[i]; }
      for(int i=0;i<V;i++) acc[i]/=(s!=0?s:1); Value v=num_arr_to_val(acc,V); free(acc); return v; }
    case B_FORBIDDEN:{ int n; double*q=val_to_num_arr(nargs?args[0]:VNIL(),&n);
      Arr*z=arr_new(); for(int i=0;i<n;i++) if(q[i]==0.0) arr_push(z,VNUM(i)); free(q); return VARR(z); }
    case B_RANGE:{ int a=0,b=0; if(nargs==1){b=(int)args[0].num;} else if(nargs>=2){a=(int)args[0].num;b=(int)args[1].num;}
      Arr*r=arr_new(); for(int i=a;i<b;i++) arr_push(r,VNUM(i)); return VARR(r); }
    case B_FLOOR: return VNUM(floor(nargs?args[0].num:0));
    case B_F3:{ char b[64]; snprintf(b,64,"%.3f",nargs?args[0].num:0); return VSTR(b); }
    case B_SUM:{ int n; double*x=val_to_num_arr(nargs?args[0]:VNIL(),&n); double s=0; for(int i=0;i<n;i++)s+=x[i]; free(x); return VNUM(s); }
    case B_MAX_OF:{ int n; double*x=val_to_num_arr(nargs?args[0]:VNIL(),&n); if(n==0)return VNIL();
      double mx=x[0]; for(int i=1;i<n;i++) if(x[i]>mx)mx=x[i]; free(x); return VNUM(mx); }
    case B_MIN_OF:{ int n; double*x=val_to_num_arr(nargs?args[0]:VNIL(),&n); if(n==0)return VNIL();
      double mn=x[0]; for(int i=1;i<n;i++) if(x[i]<mn)mn=x[i]; free(x); return VNUM(mn); }
    case B_PI: return VNUM(M_PI);
    case B_POW: return VNUM(pow(nargs?args[0].num:0, nargs>1?args[1].num:0));
    case B_KL:{ int n,m; double*p=val_to_num_arr(args[0],&n); double*q=val_to_num_arr(args[1],&m);
      double d=0; for(int i=0;i<n&&i<m;i++){ if(p[i]>1e-12 && q[i]>1e-12) d+=p[i]*log(p[i]/q[i]); }
      free(p);free(q); return VNUM(d); }
    case B_PUSH:{ if(nargs>=2 && args[0].kind==V_ARR){ arr_push(args[0].arr,args[1]); return args[0]; } return nargs?args[0]:VNIL(); }
    default: return VNIL();
  }
}

static Env *GLOBAL = NULL;
static void register_func(Node*fn, Env*e){ Value v; memset(&v,0,sizeof v); v.kind=V_FUN; v.fn=fn; v.clo=e; env_bind(e,fn->str,v); }

static void exec_reviser(Node*rev, Env*e){
  for(int i=0;i<rev->nkid;i++){
    Node*k=rev->kids[i];
    if(k->kind==N_RULE){ const char*head = k->kids[0]->str; grammar_commit(k->str, head, k->kids[1], k->kids[2]); }
  }
  for(int i=0;i<rev->nkid;i++){
    Node*k=rev->kids[i];
    if(k->kind!=N_RULE){ if(k->kind==N_FUNC) register_func(k,e); else exec_stmt(k,e); }
  }
}

static void exec_decl(Node*d, Env*e){
  switch(d->kind){
    case N_FUNC: register_func(d,e); break;
    case N_REVISER: exec_reviser(d,e); break;
    case N_OMEGABLOCK: { for(int i=0;i<d->kids[0]->nkid;i++) exec_decl(d->kids[0]->kids[i],e); break; }
    case N_ASPERAL: {
      if(d->nkid && d->kids[d->nkid-1]->kind==N_BLOCK)
        for(int i=0;i<d->kids[d->nkid-1]->nkid;i++) exec_decl(d->kids[d->nkid-1]->kids[i],e);
      break;
    }
    case N_TYPEDEF: break;
    default: exec_stmt(d,e); break;
  }
}

static void hoist_funcs(Node*scope, Env*e){
  for(int i=0;i<scope->nkid;i++){
    Node*d=scope->kids[i];
    if(d->kind==N_FUNC) register_func(d,e);
    else if(d->kind==N_OMEGABLOCK && d->nkid) hoist_funcs(d->kids[0],e);
    else if(d->kind==N_REVISER) {
      for(int j=0;j<d->nkid;j++) if(d->kids[j]->kind==N_FUNC) register_func(d->kids[j],e);
    }
  }
}

static void run_program(Node*prog){
  GLOBAL=env_new(NULL);
  for(int i=0;i<B_NBUILTIN;i++){ Value v; memset(&v,0,sizeof v); v.kind=V_BUILTIN; v.builtin=i; env_bind(GLOBAL,BNAMES[i],v); }
  for(int i=0;i<prog->nkid;i++) if(prog->kids[i]->kind==N_REVISER) exec_reviser(prog->kids[i],GLOBAL);
  hoist_funcs(prog,GLOBAL);
  for(int i=0;i<prog->nkid;i++){
    Node*d=prog->kids[i];
    if(d->kind==N_FUNC||d->kind==N_REVISER) continue;
    exec_decl(d,GLOBAL);
  }
}

static void dump_tokens(Token*t){
  for(size_t i=0;;i++){
    Token*k=&t[i];
    printf("%-12s", tok_name(k->kind));
    if(k->kind==T_INT||k->kind==T_FLOAT) printf(" %g", k->num);
    else if(k->lex) printf(" %s", k->lex);
    printf("\n");
    if(k->kind==T_EOF) break;
  }
}

static char *read_file(const char*path){
  FILE*f=fopen(path,"rb"); if(!f){ fprintf(stderr,"cannot open %s\n",path); exit(1); }
  fseek(f,0,SEEK_END); long n=ftell(f); fseek(f,0,SEEK_SET);
  char*b=xmalloc(n+1); size_t r=fread(b,1,n,f); b[r]=0; fclose(f); return b;
}

static Node* parse_source(const char*src, Token**toks_out){
  POSTFIX_WORDS.n=0; STMT_WORDS.n=0;
  Lexer L; memset(&L,0,sizeof L); L.src=src; L.len=strlen(src); L.line=1;
  lex_all(&L);
  if(toks_out) *toks_out=L.toks;
  Parser P; P.t=L.toks; P.i=0; P.n=L.ntok;
  return parse_program(&P);
}

int main(int argc, char**argv){
  if(argc<3){ fprintf(stderr,"usage: %s <run|tokens|ast> file.bada\n",argv[0]); return 1; }
  const char*cmd=argv[1];
  const char*path=argv[2];
  char*src=read_file(path);
  if(!strcmp(cmd,"tokens")){ Token*t; parse_source(src,&t); dump_tokens(t); return 0; }
  if(!strcmp(cmd,"run")){ Node*prog=parse_source(src,NULL); run_program(prog); return 0; }
  fprintf(stderr,"unknown command: %s\n",cmd);
  return 1;
}
