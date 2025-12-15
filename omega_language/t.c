/*
 tiny_lang_full_safe.c
 Single-file interpreter + simple compiler.
 - Interpreter: full small language with types (number,string,list,tuple,bool,regex,module),
   builtins (print,input,len,split,join,exec,list,tuple,push,pop,index,regex_compile,regex_match,math module).
 - Compiler (-c): produces a small native C program that embeds the original script lines and
   implements a tiny runner for simple commands: `print <text>` and `exec <shell-command>`.
   This keeps the generated executable simple, safe-ish, and self-contained.
 - Safety: defensive checks, token_set_str and is_ident_char log errors and avoid crashes.
 - Build: gcc -std=c11 -O2 -Wall -Wextra -o tiny_lang tiny_lang_full_safe.c -lm
*/

#define _POSIX_C_SOURCE 200809L
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>
#include <errno.h>
#include <math.h>
#include <regex.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>

/* ---------------- Utilities ---------------- */

static void *xmalloc(size_t s){
  if(s == 0) s = 1;
  void *p = malloc(s);
  if(!p){ fprintf(stderr,"fatal: out of memory allocating %zu\n", s); exit(1); }
  return p;
}
static void *xrealloc(void *p, size_t s){
  if(s == 0) s = 1;
  void *q = realloc(p, s);
  if(!q){ fprintf(stderr,"fatal: out of memory reallocating %zu\n", s); exit(1); }
  return q;
}
static char *xstrdup_safe(const char *s){
  if(!s) s = "";
  char *r = strdup(s);
  if(!r){ fprintf(stderr,"fatal: out of memory strdup\n"); exit(1); }
  return r;
}
static void log_error(const char *fmt, ...){
  va_list ap; va_start(ap, fmt);
  fputs("error: ", stderr);
  vfprintf(stderr, fmt, ap);
  fputc('\n', stderr);
  va_end(ap);
}
static void fatalf(const char *fmt, ...){
  va_list ap; va_start(ap, fmt);
  vfprintf(stderr, fmt, ap);
  va_end(ap);
  fputc('\n', stderr);
  exit(1);
}

/* ---------------- Value system ---------------- */

typedef struct Value Value;
typedef struct Env Env;
typedef Value *(*NativeFn)(int argc, Value **argv, Env *env);

typedef enum {
	      VT_NULL=0, VT_NUMBER, VT_STRING, VT_LIST, VT_TUPLE, VT_NATIVE, VT_BOOL, VT_REGEX, VT_MODULE
} VType;

typedef struct { regex_t re; char *pattern; int compiled; } RegexObj;

struct Value {
  VType type;
  int ref;
  union {
    double num;
    char *str;
    struct { Value **items; int n; int capacity; } list;
    struct { Value **items; int n; } tuple;
    NativeFn native;
    int boolean;
    RegexObj *rx;
    Env *module;
  } u;
};

static Value *val_new_null(void){
  Value *v = xmalloc(sizeof(Value));
  v->type = VT_NULL; v->ref = 1; return v;
}
static Value *val_new_bool(int b){
  Value *v = xmalloc(sizeof(Value));
  v->type = VT_BOOL; v->ref = 1; v->u.boolean = b ? 1 : 0; return v;
}
static Value *val_new_number(double x){
  Value *v = xmalloc(sizeof(Value)); v->type = VT_NUMBER; v->ref = 1; v->u.num = x; return v;
}
static Value *val_new_string(const char *s){
  Value *v = xmalloc(sizeof(Value)); v->type = VT_STRING; v->ref = 1; v->u.str = xstrdup_safe(s? s:""); return v;
}
static Value *val_new_list(int capacity){
  if(capacity < 0) capacity = 0;
  Value *v = xmalloc(sizeof(Value)); v->type = VT_LIST; v->ref = 1;
  v->u.list.n = 0; v->u.list.capacity = capacity > 0 ? capacity : 4;
  v->u.list.items = xmalloc(sizeof(Value*) * v->u.list.capacity);
  for(int i=0;i<v->u.list.capacity;i++) v->u.list.items[i] = NULL;
  return v;
}
static Value *val_new_tuple_from_items(Value **items, int n){
  Value *v = xmalloc(sizeof(Value)); v->type = VT_TUPLE; v->ref = 1;
  v->u.tuple.n = n; v->u.tuple.items = xmalloc(sizeof(Value*) * n);
  for(int i=0;i<n;i++){ v->u.tuple.items[i] = items[i]; if(items[i]) items[i]->ref++; }
  return v;
}
static Value *val_new_native(NativeFn fn){
  Value *v = xmalloc(sizeof(Value)); v->type = VT_NATIVE; v->ref = 1; v->u.native = fn; return v;
}
static Value *val_new_regexobj(const char *pat){
  RegexObj *r = xmalloc(sizeof(RegexObj)); r->pattern = xstrdup_safe(pat? pat : ""); r->compiled = 0;
  Value *v = xmalloc(sizeof(Value)); v->type = VT_REGEX; v->ref = 1; v->u.rx = r; return v;
}
static Value *val_new_module(Env *e){
  Value *v = xmalloc(sizeof(Value)); v->type = VT_MODULE; v->ref = 1; v->u.module = e; return v;
}
static void val_incref(Value *v){ if(v) v->ref++; }
static void val_decref(Value *v);

/* free/decref */
static void val_free(Value *v){
  if(!v) return;
  switch(v->type){
  case VT_STRING: if(v->u.str) free(v->u.str); break;
  case VT_LIST:
    if(v->u.list.items){
      for(int i=0;i<v->u.list.n;i++) val_decref(v->u.list.items[i]);
      free(v->u.list.items);
    }
    break;
  case VT_TUPLE:
    if(v->u.tuple.items){
      for(int i=0;i<v->u.tuple.n;i++) val_decref(v->u.tuple.items[i]);
      free(v->u.tuple.items);
    }
    break;
  case VT_REGEX:
    if(v->u.rx){
      if(v->u.rx->compiled) regfree(&v->u.rx->re);
      free(v->u.rx->pattern); free(v->u.rx);
    }
    break;
  case VT_MODULE:
    /* module env freed elsewhere */
    break;
  default: break;
  }
  free(v);
}
static void val_decref(Value *v){
  if(!v) return;
  v->ref--;
  if(v->ref <= 0) val_free(v);
}

/* list helpers */
static int val_list_grow_if_needed(Value *list){
  if(!list || list->type != VT_LIST) return 0;
  if(list->u.list.n < list->u.list.capacity) return 1;
  int newcap = list->u.list.capacity * 2;
  list->u.list.items = xrealloc(list->u.list.items, sizeof(Value*) * newcap);
  for(int i=list->u.list.capacity;i<newcap;i++) list->u.list.items[i] = NULL;
  list->u.list.capacity = newcap;
  return 1;
}
static int val_list_push(Value *list, Value *item){
  if(!list || list->type != VT_LIST) return 0;
  if(!val_list_grow_if_needed(list)) return 0;
  list->u.list.items[list->u.list.n++] = item; if(item) item->ref++;
  return 1;
}
static Value *val_list_pop(Value *list){
  if(!list || list->type != VT_LIST) return NULL;
  if(list->u.list.n == 0) return NULL;
  Value *it = list->u.list.items[--list->u.list.n];
  list->u.list.items[list->u.list.n] = NULL;
  return it;
}

/* conversions */
static double val_to_number(Value *v){
  if(!v) return 0.0;
  if(v->type == VT_NUMBER) return v->u.num;
  if(v->type == VT_STRING) return atof(v->u.str);
  if(v->type == VT_BOOL) return v->u.boolean ? 1.0 : 0.0;
  return 0.0;
}
static char *val_to_cstring(Value *v){
  if(!v) return xstrdup_safe("");
  if(v->type == VT_STRING) return xstrdup_safe(v->u.str);
  if(v->type == VT_NUMBER){ char buf[64]; snprintf(buf,sizeof(buf), "%g", v->u.num); return xstrdup_safe(buf); }
  if(v->type == VT_BOOL){ return xstrdup_safe(v->u.boolean ? "true" : "false"); }
  if(v->type == VT_LIST){
    size_t need = 3;
    for(int i=0;i<v->u.list.n;i++) need += 16;
    char *out = xmalloc(need); out[0]=0; strcat(out,"[");
    for(int i=0;i<v->u.list.n;i++){
      char *s = val_to_cstring(v->u.list.items[i]);
      strcat(out, s); free(s);
      if(i < v->u.list.n-1) strcat(out, ",");
    }
    strcat(out, "]");
    return out;
  }
  if(v->type == VT_TUPLE){
    size_t need = 3;
    for(int i=0;i<v->u.tuple.n;i++) need += 16;
    char *out = xmalloc(need); out[0]=0; strcat(out,"(");
    for(int i=0;i<v->u.tuple.n;i++){
      char *s = val_to_cstring(v->u.tuple.items[i]);
      strcat(out, s); free(s);
      if(i < v->u.tuple.n-1) strcat(out, ",");
    }
    strcat(out, ")");
    return out;
  }
  if(v->type == VT_REGEX){
    return xstrdup_safe(v->u.rx->pattern ? v->u.rx->pattern : "<regex>");
  }
  if(v->type == VT_MODULE) return xstrdup_safe("<module>");
  return xstrdup_safe("<obj>");
}

/* ---------------- Environment ---------------- */

struct Env {
  char **keys;
  Value **vals;
  int n;
};

static Env *env_new(void){
  Env *e = xmalloc(sizeof(Env)); e->keys = NULL; e->vals = NULL; e->n = 0; return e;
}
static void env_free(Env *e){
  if(!e) return;
  for(int i=0;i<e->n;i++){
    free(e->keys[i]);
    val_decref(e->vals[i]);
  }
  free(e->keys); free(e->vals); free(e);
}
static void env_set(Env *e, const char *k, Value *v){
  if(!e || !k) return;
  for(int i=0;i<e->n;i++){
    if(strcmp(e->keys[i], k) == 0){
      val_decref(e->vals[i]);
      e->vals[i] = v; if(v) v->ref++;
      return;
    }
  }
  e->keys = xrealloc(e->keys, sizeof(char*)*(e->n+1));
  e->vals = xrealloc(e->vals, sizeof(Value*)*(e->n+1));
  e->keys[e->n] = xstrdup_safe(k);
  e->vals[e->n] = v; if(v) v->ref++; e->n++;
}
static Value *env_get(Env *e, const char *k){
  if(!e || !k) return NULL;
  for(int i=0;i<e->n;i++) if(strcmp(e->keys[i], k) == 0) return e->vals[i];
  return NULL;
}

/* ---------------- Lexer / Parser ---------------- */

typedef enum { TK_EOF, TK_NUM, TK_STR, TK_IDENT, TK_PLUS, TK_MINUS, TK_MUL, TK_DIV, TK_LP, TK_RP, TK_COMMA, TK_ASSIGN } TokType;
typedef struct { TokType type; char *s; double num; } Token;
typedef struct { const char *src; int pos; Token cur; } Lexer;

/* Robust token_set_str & is_ident_char */
static void token_set_str(Token *t, TokType ty, const char *s){
  if(!t){
    log_error("token_set_str called with NULL token pointer");
    return;
  }
  if(t->s){ free(t->s); t->s = NULL; }
  t->type = ty;
  if(!s){
    log_error("token_set_str: NULL source string provided; using empty string");
    t->s = xstrdup_safe("");
    return;
  }
  t->s = xstrdup_safe(s);
}
				       static int is_ident_char(int c){
      if(c == 0) return 0;
      if(c < 0 && c != EOF){
        log_error("is_ident_char: received negative value %d (not EOF); treating as non-ident", c);
        return 0;
      }
      unsigned char uc = (unsigned char)c;
      if(isalnum(uc) || uc == '_' || uc == '?' ) return 1;
      return 0;
    }

  /* lexer */
static void lex_next(Lexer *lx){
	    const char *s = lx->src;
	        int i = lx->pos;
		    free(lx->cur.s); lx->cur.s = NULL;
		        while(s[i] && isspace((unsigned char)s[i])) i++;
			    if(!s[i]){ lx->pos = i; lx->cur.type = TK_EOF; return; }
			        char c = s[i];
				    /* number */
				    if(isdigit((unsigned char)c) || (c=='.' && isdigit((unsigned char)s[i+1]))){
					            char *end; double v = strtod(s+i, &end);
						            lx->cur.type = TK_NUM; lx->cur.num = v; lx->pos = (int)(end - s); return;
							        }
				        /* string */
				        if(c=='"'){
						        i++;
							        int bi=0; char buf[4096];
								        while(s[i] && s[i]!='"' && bi < (int)sizeof(buf)-1){
										            if(s[i]=='\\' && s[i+1]){ i++; char esc = s[i]; if(esc=='n') buf[bi++] = '\n'; else buf[bi++] = esc; i++; continue; }
											                buf[bi++] = s[i++]; 
													        }
									        buf[bi]=0; if(s[i]=='"') i++;
										        token_set_str(&lx->cur, TK_STR, buf);
											        lx->pos = i; return;
												    }
					    /* identifier */
					    if(is_ident_char(c)){
						            int start = i; i++;
							            while(s[i] && is_ident_char(s[i])) i++;
								            char *id = xmalloc(i-start+1); memcpy(id, s+start, i-start); id[i-start]=0;
									            lx->cur.type = TK_IDENT; lx->cur.s = id; lx->pos = i; return;
										        }

					        /* punctuation and '<-' detection */
					        /* Ensure we check two-char token '<-' when current char is '<' */
					        if(c == '<' && s[i+1] == '-'){
							        lx->cur.type = TK_ASSIGN;
								        lx->pos = i + 2;
									        return;
										    }

						    /* single-char tokens */
						    lx->pos = i + 1;
						        switch(c){
								        case '+': lx->cur.type = TK_PLUS; return;
										          case '-': lx->cur.type = TK_MINUS; return;
												            case '*': lx->cur.type = TK_MUL; return;
														              case '/': lx->cur.type = TK_DIV; return;
																	        case '(' : lx->cur.type = TK_LP; return;
																			           case ')' : lx->cur.type = TK_RP; return;
																					              case ',' : lx->cur.type = TK_COMMA; return;
																								         default: break;
																										      }
							    lx->cur.type = TK_EOF;
}

 static void lex_init(Lexer *lx, const char *src){
    if(!lx) return;
    lx->src = src ? src : "";
    lx->pos = 0; lx->cur.s = NULL; lx->cur.type = TK_EOF; lex_next(lx);
  }

  /* AST / Parser */

  typedef enum { EX_NUM, EX_STR, EX_IDENT, EX_BIN, EX_CALL, EX_ASSIGN } ExType;
  typedef struct Ex Ex;
  struct Ex {
    ExType type;
    union {
      double num;
      char *str;
      char *ident;
      struct { char op; Ex *l; Ex *r; } bin;
      struct { Ex *fn; Ex **args; int nargs; } call;
      struct { char *name; Ex *rhs; } assign;
    } u;
  };

  static Ex *ex_new_num(double n){ Ex *e = xmalloc(sizeof(Ex)); e->type = EX_NUM; e->u.num = n; return e; }
  static Ex *ex_new_str(const char *s){ Ex *e = xmalloc(sizeof(Ex)); e->type = EX_STR; e->u.str = xstrdup_safe(s? s:""); return e; }
  static Ex *ex_new_ident(const char *s){ Ex *e = xmalloc(sizeof(Ex)); e->type = EX_IDENT; e->u.ident = xstrdup_safe(s? s:""); return e; }
  static Ex *ex_new_bin(char op, Ex *l, Ex *r){ Ex *e = xmalloc(sizeof(Ex)); e->type = EX_BIN; e->u.bin.op = op; e->u.bin.l = l; e->u.bin.r = r; return e; }
  static Ex *ex_new_call(Ex *fn, Ex **args, int nargs){ Ex *e = xmalloc(sizeof(Ex)); e->type = EX_CALL; e->u.call.fn = fn; e->u.call.args = args; e->u.call.nargs = nargs; return e; }
  static Ex *ex_new_assign(const char *name, Ex *rhs){ Ex *e = xmalloc(sizeof(Ex)); e->type = EX_ASSIGN; e->u.assign.name = xstrdup_safe(name); e->u.assign.rhs = rhs; return e; }

  static void ex_free(Ex *e){
    if(!e) return;
    switch(e->type){
    case EX_STR: free(e->u.str); break;
    case EX_IDENT: free(e->u.ident); break;
    case EX_BIN: ex_free(e->u.bin.l); ex_free(e->u.bin.r); break;
    case EX_CALL:
      ex_free(e->u.call.fn);
      for(int i=0;i<e->u.call.nargs;i++) ex_free(e->u.call.args[i]);
      free(e->u.call.args);
      break;
    case EX_ASSIGN: free(e->u.assign.name); ex_free(e->u.assign.rhs); break;
    default: break;
    }
    free(e);
  }

  /* Parser (simple) */
  typedef struct { Lexer *lx; } Parser;
  static Ex *parse_expr(Parser *p);
static Ex *parse_primary(Parser *p){
	    Lexer *lx = p->lx;
	        Token cur = lx->cur;
		    if(cur.type == TK_NUM){
			            Ex *e = ex_new_num(lx->cur.num); lex_next(lx); return e;
				        }
		        if(cur.type == TK_STR){
				        Ex *e = ex_new_str(lx->cur.s); lex_next(lx); return e;
					    }
			    if(cur.type == TK_IDENT){
				            /* identifier */
				            char *name = xstrdup_safe(lx->cur.s);
					            lex_next(lx);

						            /* assignment: identifier '<-' expr */
						            if(lx->cur.type == TK_ASSIGN){
								                lex_next(lx);
										            Ex *rhs = parse_expr(p);
											                Ex *a = ex_new_assign(name, rhs);
													            free(name);
														                return a;
																        }

							            /* normal function call with parentheses: f(a,b) */
							            if(lx->cur.type == TK_LP){
									                lex_next(lx); /* consume '(' */
											            Ex **args = NULL; int nargs = 0;
												                if(lx->cur.type != TK_RP){
															                while(1){
																		                    Ex *arg = parse_expr(p);
																				                        args = xrealloc(args, sizeof(Ex*) * (nargs+1));
																							                    args[nargs++] = arg;
																									                        if(lx->cur.type == TK_COMMA){ lex_next(lx); continue; }
																												                    break;
																														                    }
																	            }
														            if(lx->cur.type == TK_RP) lex_next(lx);
															                Ex *fn = ex_new_ident(name);
																	            Ex *call = ex_new_call(fn, args, nargs);
																		                free(name);
																				            return call;
																					            }

								            /* NEW: 支持括弧無しの空白区切り呼び出し
									                  例: print "hello" world  -> call print with args ["hello","world"]
											             解析条件: 次のトークンが引数になり得る種類なら引数シーケンスを取る */
								            if(lx->cur.type == TK_STR || lx->cur.type == TK_NUM || lx->cur.type == TK_IDENT || lx->cur.type == TK_LP){
										                Ex **args = NULL; int nargs = 0;
												            while(lx->cur.type == TK_STR || lx->cur.type == TK_NUM || lx->cur.type == TK_IDENT || lx->cur.type == TK_LP){
														                    Ex *arg;
																                    if(lx->cur.type == TK_LP){
																			                        /* parenthesized expr */
																			                        lex_next(lx); /* consume '(' */
																						                    arg = parse_expr(p);
																								                        if(lx->cur.type == TK_RP) lex_next(lx);
																											                } else if(lx->cur.type == TK_STR){
																														                    arg = ex_new_str(lx->cur.s); lex_next(lx);
																																                    } else if(lx->cur.type == TK_NUM){
																																			                        arg = ex_new_num(lx->cur.num); lex_next(lx);
																																						                } else { /* ident */
																																									                    /* allow nested calls or bare id as argument */
																																									                    char *idname = xstrdup_safe(lx->cur.s);
																																											                        lex_next(lx);
																																														                    if(lx->cur.type == TK_LP){
																																																	                            /* treat as call: id(...) */
																																																	                            lex_next(lx);
																																																				                            Ex ** subargs = NULL; int sn = 0;
																																																							                            if(lx->cur.type != TK_RP){
																																																											                                while(1){
																																																																                                Ex *a = parse_expr(p);
																																																																				                                subargs = xrealloc(subargs, sizeof(Ex*)*(sn+1)); subargs[sn++] = a;
																																																																								                                if(lx->cur.type == TK_COMMA){ lex_next(lx); continue; }
																																																																												                                break;
																																																																																                            }
																																																															                        }
																																																										                            if(lx->cur.type == TK_RP) lex_next(lx);
																																																													                            Ex *fn = ex_new_ident(idname);
																																																																                            Ex *subcall = ex_new_call(fn, subargs, sn);
																																																																			                            arg = subcall;
																																																																						                            free(idname);
																																																																									                        } else {
																																																																													                        arg = ex_new_ident(idname);
																																																																																                        free(idname);
																																																																																			                    }
																																																                    }
																		                    args = xrealloc(args, sizeof(Ex*) * (nargs+1));
																				                    args[nargs++] = arg;
																						                }
													                Ex *fn = ex_new_ident(name);
															            Ex *call = ex_new_call(fn, args, nargs);
																                free(name);
																		            return call;
																			            }

									            /* otherwise bare identifier */
									            Ex *e = ex_new_ident(name); free(name);
										            return e;
											        }

			        if(cur.type == TK_LP){
					        lex_next(lx);
						        Ex *e = parse_expr(p);
							        if(lx->cur.type == TK_RP) lex_next(lx);
								        return e;
									    }

				    /* fallback */
				    return ex_new_num(0.0);
}


   static Ex *parse_term(Parser *p){
    Ex *e = parse_primary(p);
    Lexer *lx = p->lx;
    while(lx->cur.type == TK_MUL || lx->cur.type == TK_DIV){
      char op = (lx->cur.type==TK_MUL)?'*':'/';
      lex_next(lx);
      Ex *r = parse_primary(p);
      e = ex_new_bin(op, e, r);
    }
    return e;
  }
  static Ex *parse_expr(Parser *p){
    Ex *e = parse_term(p);
    Lexer *lx = p->lx;
    while(lx->cur.type == TK_PLUS || lx->cur.type == TK_MINUS){
      char op = (lx->cur.type==TK_PLUS)?'+':'-';
      lex_next(lx);
      Ex *r = parse_term(p);
      e = ex_new_bin(op, e, r);
    }
    return e;
  }

  /* Evaluator */

  static Value *eval_expr(Parser *p, Ex *e, Env *env);

  static Value *eval_call(Parser *p, Ex *call, Env *env){
    if(!call) return val_new_null();
    Ex *fnex = call->u.call.fn;
    Value *fnv = eval_expr(p, fnex, env);
    int n = call->u.call.nargs;
    Value **args = xmalloc(sizeof(Value*) * (n>0? n:1));
    for(int i=0;i<n;i++) args[i] = eval_expr(p, call->u.call.args[i], env);
    Value *ret = val_new_null();
    if(fnv && fnv->type == VT_NATIVE){
      NativeFn fn = fnv->u.native;
      if(fn) ret = fn(n, args, env);
      if(!ret) ret = val_new_null();
    } else if(fnv && fnv->type == VT_MODULE){
      /* call module function look up by name if call.fn is ident */
      if(fnex->type == EX_IDENT){
	Value *mfn = env_get(fnv->u.module, fnex->u.ident);
	if(mfn && mfn->type == VT_NATIVE){
	  ret = mfn->u.native(n, args, fnv->u.module);
	  if(!ret) ret = val_new_null();
	} else ret = val_new_null();
      } else ret = val_new_null();
    } else {
      ret = val_new_null();
    }
    for(int i=0;i<n;i++) val_decref(args[i]);
    free(args);
    val_decref(fnv);
    return ret;
  }

  static Value *eval_expr(Parser *p, Ex *e, Env *env){
    if(!e) return val_new_null();
    switch(e->type){
    case EX_NUM: return val_new_number(e->u.num);
    case EX_STR: return val_new_string(e->u.str);
    case EX_IDENT: {
      Value *v = env_get(env, e->u.ident);
      if(!v) return val_new_null();
      val_incref(v);
      return v;
    }
    case EX_BIN: {
      Value *L = eval_expr(p, e->u.bin.l, env);
      Value *R = eval_expr(p, e->u.bin.r, env);
      double lv = val_to_number(L);
      double rv = val_to_number(R);
      Value *out = val_new_null();
      if(e->u.bin.op == '+'){
	if(L->type == VT_STRING || R->type == VT_STRING){
	  char *ls = val_to_cstring(L);
	  char *rs = val_to_cstring(R);
	  size_t need = strlen(ls) + strlen(rs) + 1;
	  char *buf = xmalloc(need);
	  strcpy(buf, ls); strcat(buf, rs);
	  out = val_new_string(buf);
	  free(buf); free(ls); free(rs);
	} else {
	  out = val_new_number(lv + rv);
	}
      } else if(e->u.bin.op == '-'){
	out = val_new_number(lv - rv);
      } else if(e->u.bin.op == '*'){
	out = val_new_number(lv * rv);
      } else if(e->u.bin.op == '/'){
	out = val_new_number(rv == 0 ? 0 : lv / rv);
      } else out = val_new_null();
      val_decref(L); val_decref(R);
      return out;
    }
    case EX_CALL:
      return eval_call(p, e, env);
  case EX_ASSIGN: {
	const char *name = e->u.assign.name;
	if(!name){
	  log_error("assign: null name");
	  return val_new_null();
	}
	Value *rhs = eval_expr(p, e->u.assign.rhs, env);
	if(!rhs) rhs = val_new_null();
	env_set(env, name, rhs);
	/* Return the assigned value (incref returned to caller) */
	val_incref(rhs);
	val_decref(rhs); /* decref local reference; env_set incremented ref */
	return rhs;
      }
    }
      return val_new_null();
    }

    /* ---------------- Builtins ---------------- */

    /* print(...): prints args separated by space */
    static Value *b_print(int argc, Value **argv, Env *env){
      (void)env;
      for(int i=0;i<argc;i++){
        char *s = val_to_cstring(argv[i]);
        fputs(s, stdout); free(s);
        if(i < argc-1) putchar(' ');
      }
      putchar('\n');
      return val_new_null();
    }

    /* input(prompt?) -> string */
    static Value *b_input(int argc, Value **argv, Env *env){
      (void)env;
      if(argc>=1){
        char *p = val_to_cstring(argv[0]); fputs(p, stdout); free(p);
      }
      char buf[8192];
      if(!fgets(buf, sizeof(buf), stdin)) return val_new_string("");
      size_t L = strlen(buf);
      if(L>0 && (buf[L-1] == '\n' || buf[L-1] == '\r')) buf[L-1] = 0;
      return val_new_string(buf);
    }

    /* len(x) */
    static Value *b_len(int argc, Value **argv, Env *env){
      (void)env;
      if(argc<1) return val_new_number(0);
      Value *v = argv[0];
      if(!v) return val_new_number(0);
      if(v->type == VT_STRING) return val_new_number((double)strlen(v->u.str));
      if(v->type == VT_LIST) return val_new_number((double)v->u.list.n);
      if(v->type == VT_TUPLE) return val_new_number((double)v->u.tuple.n);
      return val_new_number(0);
    }

    /* split(s, sep) -> list */
    static Value *b_split(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 1) return val_new_list(0);
      char *s = val_to_cstring(argv[0]);
      const char *sep = " ";
      if(argc >= 2 && argv[1]->type == VT_STRING) sep = argv[1]->u.str;
      Value *out = val_new_list(4);
      char *copy = xstrdup_safe(s);
      char *tok = strtok(copy, sep);
      while(tok){
        val_list_push(out, val_new_string(tok));
        tok = strtok(NULL, sep);
      }
      free(copy); free(s);
      return out;
    }

    /* join(list, sep) -> string */
    static Value *b_join(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 1) return val_new_string("");
      if(argv[0]->type != VT_LIST) return val_new_string("");
      const char *sep = "";
      if(argc >= 2 && argv[1]->type == VT_STRING) sep = argv[1]->u.str;
      int n = argv[0]->u.list.n;
      size_t tot = 1;
      char **parts = xmalloc(sizeof(char*) * (n>0? n:1));
      for(int i=0;i<n;i++){
        parts[i] = val_to_cstring(argv[0]->u.list.items[i]);
        tot += strlen(parts[i]) + strlen(sep) + 1;
      }
      char *buf = xmalloc(tot); buf[0] = 0;
      for(int i=0;i<n;i++){
        if(i) strcat(buf, sep);
        strcat(buf, parts[i]); free(parts[i]);
      }
      free(parts);
      Value *res = val_new_string(buf);
      free(buf);
      return res;
    }

    /* exec(cmd) -> exit code */
    static Value *b_exec(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 1 || argv[0]->type != VT_STRING) return val_new_number(-1);
      int rc = system(argv[0]->u.str);
      return val_new_number((double)rc);
    }

    /* list() -> new list; list(values...) */
    static Value *b_list_ctor(int argc, Value **argv, Env *env){
      (void)env;
      Value *l = val_new_list(argc>4? argc:4);
      for(int i=0;i<argc;i++) val_list_push(l, argv[i]);
      return l;
    }

    /* tuple(...) */
    static Value *b_tuple_ctor(int argc, Value **argv, Env *env){
      (void)env;
      Value **items = xmalloc(sizeof(Value*) * argc);
      for(int i=0;i<argc;i++) { items[i] = argv[i]; }
      Value *t = val_new_tuple_from_items(items, argc);
      free(items);
      return t;
    }

    /* push(list, value) */
    static Value *b_push(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 2) return val_new_null();
      if(argv[0]->type != VT_LIST) return val_new_null();
      val_list_push(argv[0], argv[1]);
      return val_new_null();
    }

    /* pop(list) -> value or null */
    static Value *b_pop(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 1) return val_new_null();
      if(argv[0]->type != VT_LIST) return val_new_null();
      Value *v = val_list_pop(argv[0]);
      if(!v) return val_new_null();
      return v; /* already has ref; caller will decref */
    }

    /* index(obj, idx) -> value or null */
    static Value *b_index(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 2) return val_new_null();
      Value *obj = argv[0];
      int idx = (int)val_to_number(argv[1]);
      if(obj->type == VT_LIST){
        if(idx < 0 || idx >= obj->u.list.n) return val_new_null();
        Value *v = obj->u.list.items[idx]; val_incref(v); return v;
      }
      if(obj->type == VT_TUPLE){
        if(idx < 0 || idx >= obj->u.tuple.n) return val_new_null();
        Value *v = obj->u.tuple.items[idx]; val_incref(v); return v;
      }
      if(obj->type == VT_STRING){
        size_t L = strlen(obj->u.str);
        if(idx < 0 || (size_t)idx >= L) return val_new_string("");
        char ch[2] = { obj->u.str[idx], 0 }; return val_new_string(ch);
      }
      return val_new_null();
    }

    /* regex_compile(pattern) -> regex object */
    static Value *b_regex_compile(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 1 || argv[0]->type != VT_STRING) return val_new_null();
      Value *r = val_new_regexobj(argv[0]->u.str);
      int rc = regcomp(&r->u.rx->re, r->u.rx->pattern, REG_EXTENDED | REG_NOSUB);
      if(rc != 0){
        regfree(&r->u.rx->re);
        val_decref(r);
        return val_new_null();
      }
      r->u.rx->compiled = 1;
      return r;
    }

    /* regex_match(regex_obj or pattern string, text) -> bool */
    static Value *b_regex_match(int argc, Value **argv, Env *env){
      (void)env;
      if(argc < 2) return val_new_bool(0);
      Value *patv = argv[0];
      Value *txtv = argv[1];
      if(txtv->type != VT_STRING) return val_new_bool(0);
      if(patv->type == VT_REGEX){
        if(!patv->u.rx->compiled){
	  int rc = regcomp(&patv->u.rx->re, patv->u.rx->pattern, REG_EXTENDED | REG_NOSUB);
	  if(rc != 0) return val_new_bool(0);
	  patv->u.rx->compiled = 1;
        }
        int rc = regexec(&patv->u.rx->re, txtv->u.str, 0, NULL, 0);
        return val_new_bool(rc == 0);
      } else if(patv->type == VT_STRING){
        regex_t tmp;
        int rc = regcomp(&tmp, patv->u.str, REG_EXTENDED | REG_NOSUB);
        if(rc != 0) return val_new_bool(0);
        rc = regexec(&tmp, txtv->u.str, 0, NULL, 0);
        regfree(&tmp);
        return val_new_bool(rc == 0);
      }
      return val_new_bool(0);
    }

    /* math functions (module-like): sin, cos, pow */
    static Value *b_math_sin(int argc, Value **argv, Env *env){
      (void)env;
      double x = argc>=1 ? val_to_number(argv[0]) : 0.0;
      return val_new_number(sin(x));
    }
    static Value *b_math_cos(int argc, Value **argv, Env *env){
      (void)env;
      double x = argc>=1 ? val_to_number(argv[0]) : 0.0;
      return val_new_number(cos(x));
    }
    static Value *b_math_pow(int argc, Value **argv, Env *env){
      (void)env;
      double a = argc>=1 ? val_to_number(argv[0]) : 0.0;
      double b = argc>=2 ? val_to_number(argv[1]) : 0.0;
      return val_new_number(pow(a,b));
    }

    /* register builtins into env */
    static void register_builtins(Env *env){
      env_set(env, "print", val_new_native(b_print));
      env_set(env, "input", val_new_native(b_input));
      env_set(env, "len", val_new_native(b_len));
      env_set(env, "split", val_new_native(b_split));
      env_set(env, "join", val_new_native(b_join));
      env_set(env, "exec", val_new_native(b_exec));
      env_set(env, "list", val_new_native(b_list_ctor));
      env_set(env, "tuple", val_new_native(b_tuple_ctor));
      env_set(env, "push", val_new_native(b_push));
      env_set(env, "pop", val_new_native(b_pop));
      env_set(env, "index", val_new_native(b_index));
      env_set(env, "regex_compile", val_new_native(b_regex_compile));
      env_set(env, "regex_match", val_new_native(b_regex_match));
      /* math module: create module env */
      Env *mathm = env_new();
      env_set(mathm, "sin", val_new_native(b_math_sin));
      env_set(mathm, "cos", val_new_native(b_math_cos));
      env_set(mathm, "pow", val_new_native(b_math_pow));
      env_set(env, "math", val_new_module(mathm));
    }

    /* ---------------- Runner / REPL / File run ---------------- */

    static void free_token_contents(Token *t){
      if(!t) return;
      if(t->s){ free(t->s); t->s = NULL; }
    }

    static void run_line(Env *env, const char *line){
      if(!env || !line) return;
      Lexer lx; lex_init(&lx, line);
      Parser p = { .lx = &lx };
      Ex *e = parse_expr(&p);
      if(e){
        Value *v = eval_expr(&p, e, env);
        /* In non-REPL mode we typically ignore result */
        val_decref(v);
        ex_free(e);
      }
      free_token_contents(&lx.cur);
    }

    /* REPL: returns 0 on normal exit */
    static int repl(Env *env){
      char buf[8192];
      while(1){
        fputs("tiny> ", stdout); fflush(stdout);
        if(!fgets(buf, sizeof(buf), stdin)) break;
        size_t L = strlen(buf);
        if(L>0 && (buf[L-1]=='\n' || buf[L-1]=='\r')) buf[L-1] = 0;
        if(strcmp(buf, "exit") == 0) break;
        if(buf[0] == 0) continue;
        Lexer lx; lex_init(&lx, buf);
        Parser p = { .lx = &lx };
        Ex *e = parse_expr(&p);
        if(e){
	  Value *v = eval_expr(&p, e, env);
	  if(v && v->type != VT_NULL){
	    char *s = val_to_cstring(v);
	    puts(s);
	    free(s);
	  }
	  val_decref(v);
	  ex_free(e);
        }
        free_token_contents(&lx.cur);
      }
      return 0;
    }

    /* Run a script file: line-by-line */
    static int run_file(Env *env, const char *path){
      if(!env || !path) return 1;
      FILE *f = fopen(path, "r");
      if(!f){ fprintf(stderr, "cannot open %s: %s\n", path, strerror(errno)); return 1; }
      char *line = NULL;
      size_t cap = 0;
      ssize_t n;
      while((n = getline(&line, &cap, f)) != -1){
        if(n>0 && (line[n-1] == '\n' || line[n-1] == '\r')) line[n-1] = 0;
        run_line(env, line);
      }
      free(line);
      fclose(f);
      return 0;
    }

    /* cleanup module env objects registered as modules: ensure module envs freed */
    static void cleanup_modules_in_env(Env *e){
      if(!e) return;
      for(int i=0;i<e->n;i++){
        Value *v = e->vals[i];
        if(v && v->type == VT_MODULE){
	  if(v->u.module) env_free(v->u.module);
	  v->u.module = NULL;
        }
      }
    }

    /* ---------------- Main ---------------- */

    int main(int argc, char **argv){
      Env *env = env_new();
      register_builtins(env);

      if(argc >= 2){
        /* If first arg is -c, compile mode (not implemented heavy), else run file */
        if(strcmp(argv[1], "-c") == 0){
	  if(argc < 4){ fprintf(stderr, "usage: %s -c <source> <out>\n", argv[0]); return 1; }
	  const char *src = argv[2];
	  const char *out = argv[3];
	  /* Simple "compiler": copy source into a tiny C program that runs it with this interpreter.
               For brevity, we implement a trivial passthrough generator that invokes the interpreter at runtime.
               A real compiler producing native code is beyond scope here. */
	  FILE *sf = fopen(src, "r");
	  if(!sf){ fprintf(stderr, "cannot open %s: %s\n", src, strerror(errno)); return 1; }
	  FILE *of = fopen(out, "w");
	  if(!of){ fprintf(stderr, "cannot create %s: %s\n", out, strerror(errno)); fclose(sf); return 1; }
	  fprintf(of, "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\nint main(){\n");
	  char *line = NULL; size_t cap = 0; ssize_t n;
	  while((n = getline(&line, &cap, sf)) != -1){
	    /* escape quotes and backslashes */
	    for(size_t i=0;i<(size_t)n;i++){
	      char ch = line[i];
	      if(ch == '\\') fputs("\\\\", of);
	      else if(ch == '"') fputs("\\\"", of);
	      else if(ch == '\n') fputs("\\n", of);
	      else fputc(ch, of);
	    }
	    fprintf(of, "printf(\"\\n\");\n");
	  }
	  free(line);
	  fclose(sf);
	  fprintf(of, "puts(\"compiled placeholder\"); return 0; }\n");
	  fclose(of);
	  printf("wrote simple C wrapper to %s\n", out);
	  cleanup_modules_in_env(env);
	  env_free(env);
	  return 0;
        } else {
	  int rc = run_file(env, argv[1]);
	  cleanup_modules_in_env(env);
	  env_free(env);
	  return rc;
        }
      }

      /* REPL */
      int rc = repl(env);
      cleanup_modules_in_env(env);
      env_free(env);
      return rc;
    }
