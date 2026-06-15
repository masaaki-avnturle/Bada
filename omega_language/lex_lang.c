#include "omega_lang.h"
/* --- 改良済み lex_next: '<-' を確実に検出 --- */
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
/* --- 改良済み parse_primary:
        - 識別子の直後に '(' がなければ、続くトークンが引数であれば
	       空白区切りの呼び出し (call) として扱う。
	            - 例: print "hi"   => call print with one arg "hi"
		                exec "ls -la" => call exec with one arg "ls -la"
				*/
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
