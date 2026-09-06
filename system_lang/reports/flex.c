%{
#include <stdio.h>
#include "bison.h"

int yylex();
%}

%%

"let"     { return LET; }
"def"     { return DEF; }
"return"  { return RETURN; }
[a-zA-Z][a-zA-Z0-9]* { yylval.str = strdup(yytext); return IDENTIFIER; }
[0-9]+    { yylval.num = atoi(yytext); return NUMBER; }
[ \t\n]+  { /* ignore whitespace */ }
.         { return yytext[0]; }

%%

int yywrap() {
    return 1;
}
