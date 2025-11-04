#include <stdio.h>
#include <stdlib.h>
extern int omega_eval_content(const char*); extern int omega_report_only(void);

static const char *script = 
"array A = [ \"one\", \"two\", \"three\" ];\n"
"list L = list(\"x\",\"y\");\n"
"func F1 = func(100);\n"
"hash H = { \"alpha\": 1, \"beta\": 2 };\n"
"puts(A);\n"
"puts(H);\n"
"puts(L);\n"
"puts(F1);\n"
"";

int main(int argc,char **argv){(void)argc;(void)argv; omega_report_only(); return omega_eval_content(script);}
