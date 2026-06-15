#include "noema_value.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>

/* VM 側の Value 生成関数プロトタイプ（実装に合わせて置換） */
Value *val_string(const char *s);
Value *val_null(void);

/* 書き込みコールバックで受け取るバッファ */
struct membuf {
	    char *buf;
	        size_t len;
};

static size_t write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
	    size_t realsz = size * nmemb;
	        struct membuf *m = (struct membuf*)userdata;
		    char *newbuf = realloc(m->buf, m->len + realsz + 1);
		        if (!newbuf) return 0;
			    m->buf = newbuf;
			        memcpy(m->buf + m->len, ptr, realsz);
				    m->len += realsz;
				        m->buf[m->len] = '\0';
					    return realsz;
}

/* native llm_query(prompt, opts_json_string_or_null) */
static Value *native_llm_query(int argc, Value **argv) {
	    const char *prompt = NULL;
	        const char *opts_json = NULL;

		    if (argc >= 1 && argv[0]->type == T_STRING) prompt = argv[0]->v.str;
		        if (argc >= 2 && argv[1]->type == T_STRING) opts_json = argv[1]->v.str;

			    if (!prompt) return val_null();

			        const char *endpoint = getenv("LLM_ENDPOINT");
				    const char *api_key  = getenv("LLM_API_KEY");
				        if (!endpoint) return val_null();

					    CURL *curl = curl_easy_init();
					        if (!curl) return val_null();

						    struct membuf resp;
						        resp.buf = malloc(1);
							    resp.len = 0;

							        /* build JSON body: {"prompt":"...","opts":{...}} or opts omitted */
							        /* naive JSON escaping for prompt (handles quotes and backslashes) */
							        size_t plen = strlen(prompt);
								    size_t esc_cap = plen * 2 + 1;
								        char *prompt_esc = malloc(esc_cap);
									    size_t pi = 0;
									        for (size_t i = 0; i < plen; ++i) {
											        char c = prompt[i];
												        if (c == '\\' || c == '"') { prompt_esc[pi++] = '\\'; prompt_esc[pi++] = c; }
													        else if (c == '\n') { prompt_esc[pi++] = '\\'; prompt_esc[pi++] = 'n'; }
														        else prompt_esc[pi++] = c;
															    }
										    prompt_esc[pi] = '\0';

										        const char *template_noopts = "{\"prompt\":\"%s\"}";
											    const char *template_withopts = "{\"prompt\":\"%s\",\"opts\":%s}";
											        size_t body_cap = strlen(template_withopts) + pi + (opts_json? strlen(opts_json):0) + 32;
												    char *body = malloc(body_cap);
												        if (opts_json && opts_json[0] != '\0') {
														        snprintf(body, body_cap, template_withopts, prompt_esc, opts_json);
															    } else {
																            snprintf(body, body_cap, template_noopts, prompt_esc);
																	        }

													    struct curl_slist *hdrs = NULL;
													        hdrs = curl_slist_append(hdrs, "Content-Type: application/json");
														    if (api_key) {
															            size_t authlen = strlen("Authorization: Bearer ") + strlen(api_key) + 1;
																            char *auth = malloc(authlen);
																	            snprintf(auth, authlen, "Authorization: Bearer %s", api_key);
																		            hdrs = curl_slist_append(hdrs, auth);
																			            free(auth);
																				        }

														        curl_easy_setopt(curl, CURLOPT_URL, endpoint);
															    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, hdrs);
															        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body);
																    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
																        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &resp);
																	    /* optional: timeout */
																	    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

																	        CURLcode res = curl_easy_perform(curl);

																		    Value *ret = NULL;
																		        if (res != CURLE_OK) {
																				        ret = val_null();
																					    } else {
																						            /* resp.buf contains response body (assumed text). Return as VM string. */
																						            ret = val_string(resp.buf ? resp.buf : "");
																							        }

																			    /* cleanup */
																			    curl_slist_free_all(hdrs);
																			        curl_easy_cleanup(curl);
																				    free(resp.buf);
																				        free(prompt_esc);
																					    free(body);

																					        return ret;
}

/* 登録例（bootstrap 内など）:
       env_set("llm_query", val_func(native_llm_query, 2));
       */
