#include <stdio.h>
#include <stdlib.h>
extern int omega_eval_content(const char*); extern int omega_report_only(void);

static const char *script = 
"array A = [\"one\",\"two\",\"three\"];\n"
"puts(A);\n"
"";

int main(int argc,char **argv){(void)argc;(void)argv; omega_report_only(); return omega_eval_content(script);}
