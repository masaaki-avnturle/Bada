#include <stdio.h>
#include <stdlib.h>
extern int omega_eval_content(const char*); extern int omega_report_only(void);

static const char *script = 
"/* example demonstrating features */\n"
"array A = [ \"one\", \"two\", \"three\" ];\n"
"list L = list(\"x\",\"y\");\n"
"func F1 = func(100);\n"
"hash H = { \"alpha\": 1, \"beta\": 2 };\n"
"/* builtins usage */\n"
"puts(A);\n"
"puts(H);\n"
"puts(L);\n"
"puts(F1);\n"
"/* file I/O */\n"
"write_file(\"omega_pkg/examples/tmp.txt\", \"hello world\");\n"
"read_file(\"omega_pkg/examples/tmp.txt\");\n"
"/* regex_match */\n"
"b = regex_match(\"^hello\",\"hello world\");\n"
"puts(b);\n"
"/* exec */\n"
"a = exec_cmd(\"echo hi\");\n"
"puts(a);\n"
"/* now */\n"
"now();\n"
"/* network (connect to example.com:80 may fail if no network) */\n"
"/* net_connect(\"example.com\",\"80\"); net_send(3,\"GET / HTTP/1.0\\r\\n\\r\\n\"); net_recv(3,512); */\n"
"";

int main(int argc,char **argv){(void)argc;(void)argv; omega_report_only(); return omega_eval_content(script);}
