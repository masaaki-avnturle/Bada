/*
 * bada.c — Bada language in C: interpreter + compiler (emits native executables).
 *
 * Design pattern: the cons-list IS the universal structure. Source is parsed
 * into cons-list AST (homoiconic); classes, objects and the object-class
 * network are all cons-lists too. The central "trigger" of the language is the
 * gamma-function global-partial-integral-manifold ENTROPY INVARIANT, computed
 * in the runtime (via tgamma) and usable for object dispatch / scheduling.
 *
 * Build the toolchain:   cc bada.c -lm -o bada
 * Interpret:             ./bada run prog.bada
 * Compile to a native exe: ./bada build prog.bada -o prog   (transpiles to C+cc)
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <unistd.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ----------------------------------------------------------------- values */
typedef enum { T_NIL, T_NUM, T_STR, T_SYM, T_BOOL, T_CONS, T_FUN, T_BUILTIN } Tag;
typedef struct Val Val;
typedef struct Env Env;
typedef Val* (*Builtin)(Val** args, int n);

struct Val {
  Tag tag;
  union {
    double num;
    char*  str;                 /* STR / SYM */
    int    boolean;
    struct { Val* car; Val* cdr; } cons;
    struct { Val* params; Val* body; Env* env; } fun;  /* params,body are lists */
    Builtin builtin;
  };
};

static Val NIL_V = { T_NIL };
#define NIL (&NIL_V)

static Val* alloc(Tag t){ Val* v = (Val*)calloc(1,sizeof(Val)); v->tag=t; return v; }
static Val* mk_num(double d){ Val* v=alloc(T_NUM); v->num=d; return v; }
static Val* mk_str(const char* s){ Val* v=alloc(T_STR); v->str=strdup(s); return v; }
static Val* mk_sym(const char* s){ Val* v=alloc(T_SYM); v->str=strdup(s); return v; }
static Val* mk_bool(int b){ Val* v=alloc(T_BOOL); v->boolean=b?1:0; return v; }
static Val* cons(Val* a, Val* d){ Val* v=alloc(T_CONS); v->cons.car=a; v->cons.cdr=d; return v; }
#define CAR(x) ((x)->cons.car)
#define CDR(x) ((x)->cons.cdr)
static int is_cons(Val* v){ return v->tag==T_CONS; }
static int is_sym(Val* v){ return v->tag==T_SYM; }
static int sym_is(Val* v, const char* s){ return is_sym(v) && strcmp(v->str,s)==0; }

static int list_len(Val* v){ int n=0; while(is_cons(v)){ n++; v=CDR(v);} return n; }
static Val* nth(Val* v, int i){ while(i-- > 0 && is_cons(v)) v=CDR(v); return is_cons(v)?CAR(v):NIL; }

static void die(const char* msg){ fprintf(stderr,"Bada error: %s\n", msg); exit(1); }

/* ----------------------------------------------------------------- env */
struct Env { Val* vars; Env* parent; };  /* vars = alist of (sym . val) */
static Env* env_new(Env* parent){ Env* e=(Env*)calloc(1,sizeof(Env)); e->vars=NIL; e->parent=parent; return e; }
static void env_define(Env* e, const char* name, Val* val){
  e->vars = cons(cons(mk_sym(name), val), e->vars);
}
static Val* env_lookup_cell(Env* e, const char* name){
  for(; e; e=e->parent){
    for(Val* p=e->vars; is_cons(p); p=CDR(p))
      if(sym_is(CAR(CAR(p)), name)) return CAR(p);
  }
  return NULL;
}
static Val* env_get(Env* e, const char* name){
  Val* c = env_lookup_cell(e,name);
  if(!c){ fprintf(stderr,"Bada: undefined '%s'\n", name); exit(1);}
  return CDR(c);
}
static void env_set(Env* e, const char* name, Val* val){
  Val* c = env_lookup_cell(e,name);
  if(c){ c->cons.cdr = val; return; }
  env_define(e, name, val);   /* define in current scope if new */
}

/* ----------------------------------------------------------------- lexer */
typedef enum { TK_NUM, TK_STR, TK_IDENT, TK_KW, TK_OP, TK_NL, TK_EOF } TKind;
typedef struct { TKind k; char* s; double num; } Tok;

static const char* KEYWORDS[] = {"let","def","end","if","elsif","else","while",
  "print","return","true","false","nil","and","or","not",0};

static Tok* g_toks; static int g_ntok, g_capt;
static void push_tok(TKind k, const char* s, double num){
  if(g_ntok>=g_capt){ g_capt = g_capt? g_capt*2:256; g_toks=realloc(g_toks,g_capt*sizeof(Tok)); }
  g_toks[g_ntok].k=k; g_toks[g_ntok].s = s?strdup(s):NULL; g_toks[g_ntok].num=num; g_ntok++;
}
static int is_kw(const char* s){ for(int i=0;KEYWORDS[i];i++) if(!strcmp(s,KEYWORDS[i])) return 1; return 0; }

static void lex(const char* src){
  g_toks=NULL; g_ntok=0; g_capt=0;
  int i=0, len=strlen(src);
  while(i<len){
    char c=src[i];
    if(c=='#'){ while(i<len && src[i]!='\n') i++; continue; }
    if(c=='\n'){ push_tok(TK_NL,0,0); i++; continue; }
    if(c==' '||c=='\t'||c=='\r'){ i++; continue; }
    if(c=='"'){
      i++; char buf[4096]; int b=0;
      while(i<len && src[i]!='"'){
        char d=src[i];
        if(d=='\\'){ i++; d=src[i]; if(d=='n')d='\n'; else if(d=='t')d='\t'; }
        buf[b++]=d; i++;
      }
      i++; buf[b]=0; push_tok(TK_STR,buf,0); continue;
    }
    if(isdigit((unsigned char)c)){
      char buf[128]; int b=0;
      while(i<len && (isdigit((unsigned char)src[i])||src[i]=='.')) buf[b++]=src[i++];
      if(i<len && (src[i]=='e'||src[i]=='E')){ buf[b++]=src[i++]; if(src[i]=='+'||src[i]=='-')buf[b++]=src[i++];
        while(i<len && isdigit((unsigned char)src[i])) buf[b++]=src[i++]; }
      buf[b]=0; push_tok(TK_NUM,0,atof(buf)); continue;
    }
    if(isalpha((unsigned char)c)||c=='_'){
      char buf[256]; int b=0;
      while(i<len && (isalnum((unsigned char)src[i])||src[i]=='_')) buf[b++]=src[i++];
      buf[b]=0; push_tok(is_kw(buf)?TK_KW:TK_IDENT, buf, 0); continue;
    }
    /* operators */
    char two[3]={c, (i+1<len)?src[i+1]:0, 0};
    if(!strcmp(two,"==")||!strcmp(two,"!=")||!strcmp(two,"<=")||!strcmp(two,">=")||
       !strcmp(two,"<-")||!strcmp(two,"-<")||!strcmp(two,">-")){  /* directive ops */
      push_tok(TK_OP,two,0); i+=2; continue;
    }
    char one[2]={c,0};
    if(strchr("+-*/()[],=<>.", c)){ push_tok(TK_OP,one,0); i++; continue; }
    fprintf(stderr,"Bada lex: unexpected '%c'\n", c); exit(1);
  }
  push_tok(TK_EOF,0,0);
}

/* ----------------------------------------------------------------- parser */
static int P; /* token cursor */
static Tok* cur(){ return &g_toks[P]; }
static int at_kind(TKind k){ return cur()->k==k; }
static int at_kw(const char* s){ return cur()->k==TK_KW && !strcmp(cur()->s,s); }
static int at_op(const char* s){ return cur()->k==TK_OP && !strcmp(cur()->s,s); }
static void adv(){ if(cur()->k!=TK_EOF) P++; }
static void skip_nl(){ while(at_kind(TK_NL)) adv(); }
static void expect_op(const char* s){ if(!at_op(s)){ fprintf(stderr,"Bada parse: expected '%s'\n",s); exit(1);} adv(); }

static Val* parse_expr();
static Val* parse_stmt();

/* block: statements until one of the terminator keywords */
static int at_terminator(){
  return at_kw("end")||at_kw("elsif")||at_kw("else")||at_kind(TK_EOF);
}
static Val* parse_block(){
  Val* head=NIL; Val* tail=NIL;
  skip_nl();
  while(!at_terminator()){
    Val* s = parse_stmt();
    Val* cell = cons(s, NIL);
    if(head==NIL){ head=tail=cell; } else { tail->cons.cdr=cell; tail=cell; }
    while(at_kind(TK_NL)) adv();
  }
  return head;
}

static Val* parse_block();
static Val* parse_params();
static Val* parse_primary(){
  Tok* t=cur();
  if(at_kw("def")){ /* anonymous function expression: def(params) body end */
    adv(); Val* ps=parse_params(); Val* body=parse_block(); if(at_kw("end")) adv();
    return cons(mk_sym("lambda"), cons(ps, cons(body,NIL))); }
  if(t->k==TK_NUM){ adv(); return mk_num(t->num); }
  if(t->k==TK_STR){ adv(); return cons(mk_sym("quote"), cons(mk_str(t->s),NIL)); }
  if(at_kw("true")){ adv(); return mk_bool(1); }
  if(at_kw("false")){ adv(); return mk_bool(0); }
  if(at_kw("nil")){ adv(); return NIL; }
  if(t->k==TK_IDENT){ adv(); return mk_sym(t->s); }
  if(at_op("(")){ adv(); Val* e=parse_expr(); expect_op(")"); return e; }
  if(at_op("[")){
    adv(); Val* head=NIL; Val* tail=NIL;
    while(!at_op("]")){
      Val* e=parse_expr(); Val* cell=cons(e,NIL);
      if(head==NIL){head=tail=cell;} else {tail->cons.cdr=cell; tail=cell;}
      if(at_op(",")) adv(); else break;
    }
    expect_op("]");
    return cons(mk_sym("list"), head);
  }
  fprintf(stderr,"Bada parse: unexpected token near '%s'\n", t->s?t->s:"?"); exit(1);
}

/* postfix: calls f(args) and member A.b(args) */
static Val* parse_postfix(){
  Val* e=parse_primary();
  for(;;){
    if(at_op(".")){
      adv(); Tok* m=cur();
      if(m->k!=TK_IDENT){ die("expected member name after '.'"); }
      char* name=strdup(m->s); adv();
      /* A.b(args) -> (send A "b" args...) */
      Val* args=NIL; Val* tail=NIL;
      expect_op("(");
      while(!at_op(")")){
        Val* a=parse_expr(); Val* cell=cons(a,NIL);
        if(args==NIL){args=tail=cell;} else {tail->cons.cdr=cell; tail=cell;}
        if(at_op(",")) adv(); else break;
      }
      expect_op(")");
      e = cons(mk_sym("send"), cons(e, cons(cons(mk_sym("quote"),cons(mk_str(name),NIL)), args)));
    } else if(at_op("(")){
      adv(); Val* args=NIL; Val* tail=NIL;
      while(!at_op(")")){
        Val* a=parse_expr(); Val* cell=cons(a,NIL);
        if(args==NIL){args=tail=cell;} else {tail->cons.cdr=cell; tail=cell;}
        if(at_op(",")) adv(); else break;
      }
      expect_op(")");
      e = cons(mk_sym("call"), cons(e, args));
    } else break;
  }
  return e;
}

static Val* parse_unary(){
  if(at_op("-")){ adv(); return cons(mk_sym("neg"), cons(parse_unary(),NIL)); }
  if(at_kw("not")){ adv(); return cons(mk_sym("not"), cons(parse_unary(),NIL)); }
  return parse_postfix();
}
static Val* binop(const char* op, Val* a, Val* b){
  return cons(mk_sym("binop"), cons(mk_str(op), cons(a, cons(b,NIL))));
}
static Val* parse_mul(){ Val* l=parse_unary();
  while(at_op("*")||at_op("/")){ char* o=strdup(cur()->s); adv(); l=binop(o,l,parse_unary()); } return l; }
static Val* parse_add(){ Val* l=parse_mul();
  while(at_op("+")||at_op("-")){ char* o=strdup(cur()->s); adv(); l=binop(o,l,parse_mul()); } return l; }
/* directive-oriented operators: <- 代入, -< 分岐, >- 合流 (between cmp and add) */
static Val* parse_dir(){ Val* l=parse_add();
  while(at_op("<-")||at_op("-<")||at_op(">-")){ char* o=strdup(cur()->s); adv(); l=binop(o,l,parse_add()); } return l; }
static Val* parse_cmp(){ Val* l=parse_dir();
  while(at_op("<")||at_op(">")||at_op("<=")||at_op(">=")){ char* o=strdup(cur()->s); adv(); l=binop(o,l,parse_dir()); } return l; }
static Val* parse_eq(){ Val* l=parse_cmp();
  while(at_op("==")||at_op("!=")){ char* o=strdup(cur()->s); adv(); l=binop(o,l,parse_cmp()); } return l; }
static Val* parse_and(){ Val* l=parse_eq();
  while(at_kw("and")){ adv(); l=cons(mk_sym("and"),cons(l,cons(parse_eq(),NIL))); } return l; }
static Val* parse_or(){ Val* l=parse_and();
  while(at_kw("or")){ adv(); l=cons(mk_sym("or"),cons(l,cons(parse_and(),NIL))); } return l; }
static Val* parse_expr(){ return parse_or(); }

static Val* parse_params(){
  expect_op("("); Val* head=NIL; Val* tail=NIL;
  while(!at_op(")")){
    Tok* t=cur(); if(t->k!=TK_IDENT) die("expected param name");
    Val* cell=cons(mk_sym(t->s),NIL); adv();
    if(head==NIL){head=tail=cell;} else {tail->cons.cdr=cell; tail=cell;}
    if(at_op(",")) adv(); else break;
  }
  expect_op(")"); return head;
}

static Val* parse_if(){
  adv(); /* if */
  Val* cond=parse_expr();
  Val* then_b=parse_block();
  Val* else_b=NIL;
  if(at_kw("elsif")){ else_b = cons(parse_if(), NIL); /* nested if as single-stmt block */
    return cons(mk_sym("if"), cons(cond, cons(then_b, cons(else_b,NIL)))); }
  if(at_kw("else")){ adv(); else_b=parse_block(); }
  if(at_kw("end")) adv();
  return cons(mk_sym("if"), cons(cond, cons(then_b, cons(else_b,NIL))));
}

static Val* parse_stmt(){
  if(at_kw("let")){ adv(); Tok* t=cur(); if(t->k!=TK_IDENT) die("let needs name");
    char* n=strdup(t->s); adv(); expect_op("=");
    return cons(mk_sym("let"), cons(mk_sym(n), cons(parse_expr(),NIL))); }
  if(at_kw("def")){ adv(); Tok* t=cur(); if(t->k!=TK_IDENT) die("def needs name");
    char* n=strdup(t->s); adv(); Val* ps=parse_params(); Val* body=parse_block(); if(at_kw("end")) adv();
    return cons(mk_sym("def"), cons(mk_sym(n), cons(ps, cons(body,NIL)))); }
  if(at_kw("if")) return parse_if();
  if(at_kw("while")){ adv(); Val* c=parse_expr(); Val* b=parse_block(); if(at_kw("end")) adv();
    return cons(mk_sym("while"), cons(c, cons(b,NIL))); }
  if(at_kw("print")){ adv(); return cons(mk_sym("print"), cons(parse_expr(),NIL)); }
  if(at_kw("return")){ adv();
    Val* e = (at_kind(TK_NL)||at_terminator()) ? NIL : parse_expr();
    return cons(mk_sym("return"), cons(e,NIL)); }
  /* expression or assignment */
  Val* e = parse_expr();
  if(is_sym(e) && at_op("=")){ adv(); return cons(mk_sym("set"), cons(e, cons(parse_expr(),NIL))); }
  return cons(mk_sym("do"), cons(e,NIL));
}

static Val* parse_program(const char* src){
  lex(src); P=0; skip_nl();
  Val* head=NIL; Val* tail=NIL;
  while(!at_kind(TK_EOF)){
    Val* s=parse_stmt(); Val* cell=cons(s,NIL);
    if(head==NIL){head=tail=cell;} else {tail->cons.cdr=cell; tail=cell;}
    while(at_kind(TK_NL)) adv();
  }
  return head;
}

/* ----------------------------------------------------------------- eval */
static int g_returning=0; static Val* g_retval=NIL;
static Val* eval(Val* node, Env* env);

static int truthy(Val* v){ return !(v->tag==T_NIL || (v->tag==T_BOOL && !v->boolean)); }

static Val* eval_block(Val* block, Env* env){
  Val* last=NIL;
  for(Val* p=block; is_cons(p); p=CDR(p)){
    last = eval(CAR(p), env);
    if(g_returning) return last;
  }
  return last;
}

static Val* call_fun(Val* fn, Val** args, int n){
  if(fn->tag==T_BUILTIN) return fn->builtin(args,n);
  if(fn->tag!=T_FUN) die("not callable");
  Env* local=env_new(fn->fun.env);
  int i=0;
  for(Val* p=fn->fun.params; is_cons(p); p=CDR(p), i++)
    env_define(local, CAR(p)->str, i<n?args[i]:NIL);
  g_returning=0;
  Val* r=eval_block(fn->fun.body, local);
  if(g_returning){ g_returning=0; return g_retval; }
  return r;
}

static double as_num(Val* v){ return v->tag==T_NUM? v->num : 0; }
static void val_print(Val* v, FILE* f);

/* Render any value to a fresh heap C-string (grows dynamically; no overflow). */
static char* val_to_cstr(Val* v){
  char* buf=NULL; size_t sz=0;
  FILE* f=open_memstream(&buf,&sz);
  val_print(v,f); fclose(f);
  return buf; /* caller owns; leaked like all Bada values (no GC) */
}

/* ---- directive-oriented objects (built on the cons-list structure) ----
 * A directive is the list  (directive lane1 lane2 ...) — homoiconic. */
static int is_directive(Val* v){ return is_cons(v) && sym_is(CAR(v),"directive"); }
static Val* mk_directive(Val* lanes){ return cons(mk_sym("directive"), lanes); }
static Val* dir_lanes(Val* v){ return is_directive(v)? CDR(v) : cons(v,NIL); }
static int all_funcs(Val* lst){ if(!is_cons(lst)) return 0;
  for(Val* p=lst; is_cons(p); p=CDR(p)){ Tag t=CAR(p)->tag; if(t!=T_FUN&&t!=T_BUILTIN) return 0; } return 1; }
static Val* lane_append(Val* out, Val** tail, Val* x){ Val* c=cons(x,NIL);
  if(out==NIL){ *tail=c; return c; } (*tail)->cons.cdr=c; *tail=c; return out; }

static Val* eval_binop(const char* op, Val* a, Val* b){
  /* <- 代入: load b into a directive object */
  if(!strcmp(op,"<-")) return mk_directive(cons(b,NIL));
  /* -< 分岐: split each lane through the branch directive(s) */
  if(!strcmp(op,"-<")){
    Val* lanes=dir_lanes(a); Val* out=NIL; Val* tail=NIL;
    if(b->tag==T_FUN||b->tag==T_BUILTIN){
      for(Val* p=lanes; is_cons(p); p=CDR(p)){ Val* arg=CAR(p); out=lane_append(out,&tail,call_fun(b,&arg,1)); }
    } else if(is_cons(b)&&!is_directive(b)&&all_funcs(b)){
      for(Val* p=lanes; is_cons(p); p=CDR(p)){ Val* arg=CAR(p);
        for(Val* f=b; is_cons(f); f=CDR(f)){ Val* fn=CAR(f); out=lane_append(out,&tail,call_fun(fn,&arg,1)); } }
    } else if(is_cons(b)&&!is_directive(b)){
      for(Val* p=b; is_cons(p); p=CDR(p)) out=lane_append(out,&tail,CAR(p));
    } else if(b->tag==T_NUM){
      int k=(int)b->num;
      for(Val* p=lanes; is_cons(p); p=CDR(p)) for(int i=0;i<k;i++) out=lane_append(out,&tail,CAR(p));
    } else {
      for(Val* p=lanes; is_cons(p); p=CDR(p)) out=lane_append(out,&tail,b);
    }
    return mk_directive(out);
  }
  /* >- 合流: merge the lanes back into one value via a 2-arg combiner */
  if(!strcmp(op,">-")){
    Val* lanes=dir_lanes(a);
    if(!is_cons(lanes)) return NIL;
    if(!(b->tag==T_FUN||b->tag==T_BUILTIN)) die(">- needs a 2-arg merge directive");
    Val* acc=CAR(lanes);
    for(Val* p=CDR(lanes); is_cons(p); p=CDR(p)){ Val* args[2]={acc,CAR(p)}; acc=call_fun(b,args,2); }
    return acc;
  }
  if(!strcmp(op,"+")){
    if(a->tag==T_STR||b->tag==T_STR){
      char* l=val_to_cstr(a); char* r=val_to_cstr(b);
      size_t n=strlen(l)+strlen(r)+1; char* buf=malloc(n);
      snprintf(buf,n,"%s%s",l,r); free(l); free(r);
      Val* res=mk_str(buf); free(buf); return res; }
    return mk_num(as_num(a)+as_num(b)); }
  if(!strcmp(op,"-")) return mk_num(as_num(a)-as_num(b));
  if(!strcmp(op,"*")) return mk_num(as_num(a)*as_num(b));
  if(!strcmp(op,"/")) return mk_num(as_num(a)/as_num(b));
  if(!strcmp(op,"==")){
    if(a->tag==T_STR&&b->tag==T_STR) return mk_bool(!strcmp(a->str,b->str));
    return mk_bool(as_num(a)==as_num(b)); }
  if(!strcmp(op,"!=")){
    if(a->tag==T_STR&&b->tag==T_STR) return mk_bool(strcmp(a->str,b->str)!=0);
    return mk_bool(as_num(a)!=as_num(b)); }
  if(!strcmp(op,"<"))  return mk_bool(as_num(a)<as_num(b));
  if(!strcmp(op,">"))  return mk_bool(as_num(a)>as_num(b));
  if(!strcmp(op,"<=")) return mk_bool(as_num(a)<=as_num(b));
  if(!strcmp(op,">=")) return mk_bool(as_num(a)>=as_num(b));
  die("bad binop"); return NIL;
}

static Val* eval(Val* node, Env* env){
  switch(node->tag){
    case T_NUM: case T_STR: case T_BOOL: case T_NIL: case T_FUN: case T_BUILTIN: return node;
    case T_SYM: return env_get(env, node->str);
    case T_CONS: break;
  }
  Val* head=CAR(node);
  const char* h = is_sym(head)? head->str : "";
  if(!strcmp(h,"quote")) return nth(node,1);
  if(!strcmp(h,"let")){ Val* v=eval(nth(node,2),env); env_define(env, CAR(CDR(node))->str, v); return v; }
  if(!strcmp(h,"set")){ Val* v=eval(nth(node,2),env); env_set(env, CAR(CDR(node))->str, v); return v; }
  if(!strcmp(h,"def")){ Val* f=alloc(T_FUN); f->fun.params=nth(node,2); f->fun.body=nth(node,3); f->fun.env=env;
    env_define(env, CAR(CDR(node))->str, f); return f; }
  if(!strcmp(h,"lambda")){ Val* f=alloc(T_FUN); f->fun.params=nth(node,1); f->fun.body=nth(node,2); f->fun.env=env; return f; }
  if(!strcmp(h,"if")){ if(truthy(eval(nth(node,1),env))) return eval_block(nth(node,2),env);
    return eval_block(nth(node,3),env); }
  if(!strcmp(h,"while")){ Val* last=NIL;
    while(truthy(eval(nth(node,1),env))){ last=eval_block(nth(node,2),env); if(g_returning) break; } return last; }
  if(!strcmp(h,"print")){ Val* v=eval(nth(node,1),env); val_print(v,stdout); fputc('\n',stdout); return v; }
  if(!strcmp(h,"return")){ g_retval=eval(nth(node,1),env); g_returning=1; return g_retval; }
  if(!strcmp(h,"do")) return eval(nth(node,1),env);
  if(!strcmp(h,"neg")) return mk_num(-as_num(eval(nth(node,1),env)));
  if(!strcmp(h,"not")) return mk_bool(!truthy(eval(nth(node,1),env)));
  if(!strcmp(h,"and")){ Val* a=eval(nth(node,1),env); if(!truthy(a)) return mk_bool(0); return eval(nth(node,2),env); }
  if(!strcmp(h,"or")){ Val* a=eval(nth(node,1),env); if(truthy(a)) return a; return eval(nth(node,2),env); }
  if(!strcmp(h,"binop")){ const char* op=nth(node,1)->str;
    return eval_binop(op, eval(nth(node,2),env), eval(nth(node,3),env)); }
  if(!strcmp(h,"list")){ Val* head2=NIL; Val* tail=NIL;
    for(Val* p=CDR(node); is_cons(p); p=CDR(p)){ Val* cell=cons(eval(CAR(p),env),NIL);
      if(head2==NIL){head2=tail=cell;} else {tail->cons.cdr=cell; tail=cell;} } return head2; }
  if(!strcmp(h,"call")){
    Val* fn=eval(nth(node,1),env);
    Val* argl=CDR(CDR(node)); int n=list_len(argl);
    Val** args=malloc(sizeof(Val*)*(n>0?n:1)); int i=0;
    for(Val* p=argl; is_cons(p); p=CDR(p)) args[i++]=eval(CAR(p),env);
    Val* r=call_fun(fn,args,n); free(args); return r;
  }
  if(!strcmp(h,"send")){
    /* (send obj "method" args...) -> dispatch via class method list */
    Val* obj=eval(nth(node,1),env);
    Val* mname=eval(nth(node,2),env);
    Val* argl=CDR(CDR(CDR(node))); int n=list_len(argl);
    Val** args=malloc(sizeof(Val*)*(n+1)); args[0]=obj; int i=1;
    for(Val* p=argl; is_cons(p); p=CDR(p)) args[i++]=eval(CAR(p),env);
    /* obj = ("object" class . slots); class = ("class" name parent methods) */
    Val* klass = nth(obj,1);
    Val* methods = nth(klass,3);
    Val* m=NIL;
    for(Val* p=methods; is_cons(p); p=CDR(p))
      if(!strcmp(CAR(CAR(p))->str, mname->str)){ m=CDR(CAR(p)); break; }
    if(m==NIL){ fprintf(stderr,"Bada: no method '%s'\n", mname->str); exit(1); }
    Val* r=call_fun(m,args,n+1); free(args); return r;
  }
  die("cannot eval form"); return NIL;
}

/* ----------------------------------------------------------------- print */
static void val_print(Val* v, FILE* f){
  switch(v->tag){
    case T_NIL: fputs("nil",f); break;
    case T_BOOL: fputs(v->boolean?"true":"false",f); break;
    case T_STR: fputs(v->str,f); break;
    case T_SYM: fputs(v->str,f); break;
    case T_NUM: {
      double d=v->num;
      if(d==floor(d) && fabs(d)<1e15) fprintf(f,"%lld",(long long)d);
      else fprintf(f,"%.6g",d);
    } break;
    case T_CONS: {
      if(is_directive(v)){ fputs("<| ",f); int first=1;
        for(Val* p=CDR(v); is_cons(p); p=CDR(p)){ if(!first) fputs(", ",f); first=0; val_print(CAR(p),f);} fputs(" |>",f); break; }
      fputc('[',f); int first=1;
      for(Val* p=v; is_cons(p); p=CDR(p)){ if(!first) fputs(", ",f); first=0; val_print(CAR(p),f);} fputc(']',f);
    } break;
    default: fputs("<fn>",f);
  }
}

/* ----------------------------------------------------------------- builtins */
static Val* bi_str(Val** a,int n){ (void)n; char* s=val_to_cstr(a[0]); Val* v=mk_str(s); free(s); return v; }
static Val* bi_len(Val** a,int n){ (void)n; Val* v=a[0]; if(v->tag==T_STR) return mk_num(strlen(v->str)); return mk_num(list_len(v)); }
static Val* bi_at(Val** a,int n){ (void)n; return nth(a[0], (int)as_num(a[1])); }
static Val* bi_cons(Val** a,int n){ (void)n; return cons(a[0],a[1]); }
static Val* bi_car(Val** a,int n){ (void)n; return is_cons(a[0])?CAR(a[0]):NIL; }
static Val* bi_cdr(Val** a,int n){ (void)n; return is_cons(a[0])?CDR(a[0]):NIL; }
static Val* bi_list(Val** a,int n){ Val* h=NIL; for(int i=n-1;i>=0;i--) h=cons(a[i],h); return h; }
static Val* bi_append(Val** a,int n){ (void)n; /* append item to end -> new list */
  Val* h=NIL; Val* t=NIL; for(Val* p=a[0]; is_cons(p); p=CDR(p)){ Val* c=cons(CAR(p),NIL); if(h==NIL){h=t=c;}else{t->cons.cdr=c;t=c;} }
  Val* c=cons(a[1],NIL); if(h==NIL) return c; t->cons.cdr=c; return h; }
static Val* bi_directive(Val** a,int n){ (void)n; return mk_directive(cons(a[0],NIL)); }
static Val* bi_lanes(Val** a,int n){ (void)n; return dir_lanes(a[0]); }

/* math / manifold */
static Val* bi_gamma(Val** a,int n){ (void)n; return mk_num(tgamma(as_num(a[0]))); }
static Val* bi_beta (Val** a,int n){ (void)n; double p=as_num(a[0]),q=as_num(a[1]); return mk_num(tgamma(p)*tgamma(q)/tgamma(p+q)); }
static double xlogx(double x){ return x<=0?0:x*log(x); }
static Val* bi_xlogx(Val** a,int n){ (void)n; return mk_num(xlogx(as_num(a[0]))); }
static double manifold_element(double x){ if(x<=1) return 1; double xl=xlogx(x); if(fabs(xl)<1e-9) return 1; return 1.0/(xl*xl); }
static Val* bi_element(Val** a,int n){ (void)n; return mk_num(manifold_element(as_num(a[0]))); }
static Val* bi_zeta_gauge(Val** a,int n){ (void)n; double p=as_num(a[0]),q=as_num(a[1]),x=as_num(a[2]);
  return mk_num(tgamma(p)*tgamma(q)/tgamma(p+q)/log(x)); }
static double shannon(Val* ps){ double h=0; for(Val* p=ps; is_cons(p); p=CDR(p)){ double pr=as_num(CAR(p)); if(pr>0) h-=pr*log2(pr);} return h; }
static Val* bi_entropy(Val** a,int n){ (void)n; return mk_num(shannon(a[0])); }
/* the central TRIGGER: global partial integral manifold entropy invariant Xi */
static Val* bi_xi(Val** a,int n){ (void)n; Val* ps=a[0];
  double h=shannon(ps); double m=0; int i=0;
  for(Val* p=ps; is_cons(p); p=CDR(p),i++){ double x=i+2.0; m += as_num(CAR(p))*manifold_element(x); }
  int N=list_len(ps);
  double p1=h+1, q1=m+1, x1=N+1;
  return mk_num(tgamma(p1)*tgamma(q1)/tgamma(p1+q1)/log(x1));
}
/* thermal entropy of a class network: invariant over the per-class weights */
static Val* bi_thermal(Val** a,int n){ (void)n; Val* weights=a[0]; double s=0;
  for(Val* p=weights; is_cons(p); p=CDR(p)) s+=as_num(CAR(p));
  if(s<=0) return mk_num(0);
  Val* ps=NIL; Val* t=NIL;
  for(Val* p=weights; is_cons(p); p=CDR(p)){ Val* c=cons(mk_num(as_num(CAR(p))/s),NIL); if(ps==NIL){ps=t=c;}else{t->cons.cdr=c;t=c;} }
  Val* args[1]={ps}; return bi_xi(args,1);
}

static Val* bi_exp(Val** a,int n){(void)n;return mk_num(exp(as_num(a[0])));}
static Val* bi_log(Val** a,int n){(void)n;return mk_num(log(as_num(a[0])));}
static Val* bi_sqrt(Val** a,int n){(void)n;return mk_num(sqrt(as_num(a[0])));}
static Val* bi_sin(Val** a,int n){(void)n;return mk_num(sin(as_num(a[0])));}
static Val* bi_cos(Val** a,int n){(void)n;return mk_num(cos(as_num(a[0])));}
static Val* bi_pow(Val** a,int n){(void)n;return mk_num(pow(as_num(a[0]),as_num(a[1])));}
static Val* bi_mod(Val** a,int n){(void)n;return mk_num((double)(((long long)as_num(a[0]))%((long long)as_num(a[1]))));}
static Val* bi_floor(Val** a,int n){(void)n;return mk_num(floor(as_num(a[0])));}
static Val* bi_abs(Val** a,int n){(void)n;return mk_num(fabs(as_num(a[0])));}
static Val* bi_pi(Val** a,int n){(void)a;(void)n;return mk_num(M_PI);}

/* object system — classes and objects ARE cons-lists */
static Val* bi_class(Val** a,int n){ (void)n; /* class(name) -> ("class" name nil ()) */
  return cons(mk_sym("class"), cons(a[0], cons(NIL, cons(NIL,NIL)))); }
static Val* bi_method(Val** a,int n){ (void)n; /* method(class, name, fn) : push (name . fn) */
  Val* klass=a[0];
  /* klass = (class name parent methods); mutate the methods slot (4th) */
  Val* methods_holder = CDR(CDR(CDR(klass)));      /* (methods) */
  Val* methods = CAR(methods_holder);
  methods = cons(cons(a[1], a[2]), methods);
  methods_holder->cons.car = methods;
  return klass; }
static Val* bi_new(Val** a,int n){ (void)n; /* new(class) -> ("object" class) ; slots appended */
  return cons(mk_sym("object"), cons(a[0], NIL)); }
static Val* bi_set_slot(Val** a,int n){ (void)n; /* set_slot(obj,name,val) */
  Val* obj=a[0]; Val* slots_holder=CDR(obj); /* (class . slots) ; slots = CDR(CDR(obj)) */
  Val* tail=CDR(obj); /* (class . slots) -> we store slots after class */
  /* obj = (object class slot1 slot2 ...) where slotk = (name . val) */
  /* find existing */
  for(Val* p=CDR(CDR(obj)); is_cons(p); p=CDR(p))
    if(!strcmp(CAR(CAR(p))->str, a[1]->str)){ CAR(p)->cons.cdr=a[2]; return obj; }
  /* prepend new slot after class */
  Val* rest=CDR(CDR(obj));
  CDR(obj)->cons.cdr = cons(cons(a[1],a[2]), rest);
  (void)slots_holder;(void)tail; return obj; }
static Val* bi_get_slot(Val** a,int n){ (void)n;
  for(Val* p=CDR(CDR(a[0])); is_cons(p); p=CDR(p))
    if(!strcmp(CAR(CAR(p))->str, a[1]->str)) return CDR(CAR(p));
  return NIL; }
static Val* bi_class_name(Val** a,int n){(void)n; return nth(a[0],1);}

/* IO for self-evolution */
static char* read_all(const char* path){
  FILE* f=fopen(path,"rb"); if(!f) return NULL;
  fseek(f,0,SEEK_END); long sz=ftell(f); fseek(f,0,SEEK_SET);
  char* b=malloc(sz+1); fread(b,1,sz,f); b[sz]=0; fclose(f); return b; }
static Val* bi_read_file(Val** a,int n){ (void)n; char* s=read_all(a[0]->str); return s?mk_str(s):NIL; }
static Val* bi_write_file(Val** a,int n){ (void)n; FILE* f=fopen(a[0]->str,"wb"); if(!f) return mk_bool(0);
  fputs(a[1]->str,f); fclose(f); return mk_bool(1); }

static void def_bi(Env* e, const char* name, Builtin fn){ Val* v=alloc(T_BUILTIN); v->builtin=fn; env_define(e,name,v); }
static Env* global_env(){
  Env* g=env_new(NULL);
  def_bi(g,"str",bi_str); def_bi(g,"len",bi_len); def_bi(g,"at",bi_at);
  def_bi(g,"cons",bi_cons); def_bi(g,"car",bi_car); def_bi(g,"cdr",bi_cdr);
  def_bi(g,"list",bi_list); def_bi(g,"append",bi_append);
  def_bi(g,"directive",bi_directive); def_bi(g,"lanes",bi_lanes);
  def_bi(g,"gamma",bi_gamma); def_bi(g,"beta",bi_beta); def_bi(g,"xlogx",bi_xlogx);
  def_bi(g,"element",bi_element); def_bi(g,"zeta_gauge",bi_zeta_gauge);
  def_bi(g,"entropy",bi_entropy); def_bi(g,"xi",bi_xi); def_bi(g,"thermal",bi_thermal);
  def_bi(g,"exp",bi_exp); def_bi(g,"log",bi_log); def_bi(g,"sqrt",bi_sqrt);
  def_bi(g,"sin",bi_sin); def_bi(g,"cos",bi_cos); def_bi(g,"pow",bi_pow);
  def_bi(g,"mod",bi_mod); def_bi(g,"floor",bi_floor); def_bi(g,"abs",bi_abs); def_bi(g,"pi",bi_pi);
  def_bi(g,"class",bi_class); def_bi(g,"method",bi_method); def_bi(g,"new",bi_new);
  def_bi(g,"set_slot",bi_set_slot); def_bi(g,"get_slot",bi_get_slot); def_bi(g,"class_name",bi_class_name);
  def_bi(g,"read_file",bi_read_file); def_bi(g,"write_file",bi_write_file);
  return g;
}

/* ----------------------------------------------------------------- run API */
int bada_run_source(const char* src){
  Val* prog=parse_program(src);
  Env* g=global_env();
  eval_block(prog, g);
  return 0;
}

#ifndef BADA_LIB
/* ----------------------------------------------------------------- compiler */
/* Compile a .bada file to a native executable by embedding the source and
 * linking this runtime (compiled with -DBADA_LIB).  bada build f.bada -o out */
static int resolve_abs(const char* cand, char* out, int cap){
  if(access(cand,R_OK)!=0) return 0;
  char abs[4096];
  if(realpath(cand, abs)){ snprintf(out,cap,"%s",abs); return 1; }
  snprintf(out,cap,"%s",cand); return 1;
}
static int self_path(char* out, int cap, const char* argv0){
  const char* home=getenv("BADA_HOME");
  char cand[4096];
  if(home){ snprintf(cand,sizeof cand,"%s/bada.c",home); if(resolve_abs(cand,out,cap)) return 1; }
  char buf[4096]; strncpy(buf,argv0,sizeof buf-1); buf[sizeof buf-1]=0;
  char* slash=strrchr(buf,'/');
  if(slash){ *slash=0; snprintf(cand,sizeof cand,"%s/bada.c",buf); if(resolve_abs(cand,out,cap)) return 1; }
  if(resolve_abs("bada.c",out,cap)) return 1;
  return 0;
}
static int build_exe(const char* srcfile, const char* outfile, const char* argv0){
  char* src=read_all(srcfile);
  if(!src){ fprintf(stderr,"cannot read %s\n",srcfile); return 1; }
  char rt[4096]; if(!self_path(rt,sizeof rt,argv0)){ fprintf(stderr,"cannot locate bada.c runtime (set BADA_HOME)\n"); return 1; }
  char mainc[]="/tmp/bada_build_XXXXXX.c"; int fd=mkstemps(mainc,2); if(fd<0){perror("mkstemps");return 1;}
  FILE* f=fdopen(fd,"w");
  fprintf(f,"#define BADA_LIB\n#include \"%s\"\n", rt);
  fprintf(f,"static const unsigned char SRC[]={");
  for(unsigned char* p=(unsigned char*)src; *p; p++) fprintf(f,"%u,", *p);
  fprintf(f,"0};\nint main(){return bada_run_source((const char*)SRC);}\n");
  fclose(f);
  char cmd[8192]; snprintf(cmd,sizeof cmd,"cc -O2 \"%s\" -lm -o \"%s\"", mainc, outfile);
  int rc=system(cmd);
  unlink(mainc);
  if(rc==0) fprintf(stderr,"compiled -> %s (native executable)\n", outfile);
  return rc?1:0;
}

static void repl(){
  Env* g=global_env(); char line[4096];
  fputs("Bada-C REPL. Ctrl-D to exit.\n",stdout);
  while(fputs("bada> ",stdout), fgets(line,sizeof line,stdin)){
    Val* prog=parse_program(line); Val* r=eval_block(prog,g);
    val_print(r,stdout); fputc('\n',stdout);
  }
}

int main(int argc, char** argv){
  if(argc<2){ fprintf(stderr,"usage: bada run|build|eval|repl|version ...\n"); return 1; }
  const char* cmd=argv[1];
  if(!strcmp(cmd,"version")){ puts("bada-c 0.1.0"); return 0; }
  if(!strcmp(cmd,"repl")){ repl(); return 0; }
  if(!strcmp(cmd,"run")){ if(argc<3){fprintf(stderr,"usage: bada run f.bada\n");return 1;}
    char* s=read_all(argv[2]); if(!s){fprintf(stderr,"cannot read %s\n",argv[2]);return 1;} return bada_run_source(s); }
  if(!strcmp(cmd,"eval")){ if(argc<3){fprintf(stderr,"usage: bada eval \"...\"\n");return 1;} return bada_run_source(argv[2]); }
  if(!strcmp(cmd,"build")){
    const char* src=NULL; const char* out="a.out";
    for(int i=2;i<argc;i++){ if(!strcmp(argv[i],"-o")&&i+1<argc) out=argv[++i]; else src=argv[i]; }
    if(!src){ fprintf(stderr,"usage: bada build f.bada -o out\n"); return 1; }
    return build_exe(src,out,argv[0]);
  }
  fprintf(stderr,"unknown command: %s\n",cmd); return 1;
}
#endif
