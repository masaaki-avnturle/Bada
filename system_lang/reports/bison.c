%{
#include <stdio.h>
#include <stdlib.h>
#include "bison.h"

int yylex();
void yyerror(const char *s) { fprintf(stderr, "%s\n", s); }

typedef struct {
    int type;
    union {
        int num;
        char *str;
    } value;
} Node;

Node *makeNode(int type, ...) {
    Node *node = malloc(sizeof(Node));
    node->type = type;
    va_list args;
    va_start(args, type);
    switch (type) {
        case NUMBER:
            node->value.num = va_arg(args, int);
            break;
        case IDENTIFIER:
            node->value.str = va_arg(args, char *);
            break;
    }
    va_end(args);
    return node;
}

void freeNode(Node *node) {
    if (node->type == IDENTIFIER) {
        free(node->value.str);
    }
    free(node);
}

%}

%union {
    Node *node;
}

%token LET DEF RETURN
%token <num> NUMBER
%token <str> IDENTIFIER

%%

program:
    | program statement
    ;

statement:
    let_statement
    | def_statement
    | return_statement
    ;

let_statement:
    LET IDENTIFIER '=' expression ';' { printf("Let %s = %d\n", $2, $4->value.num); freeNode($4); }
    ;

def_statement:
    DEF IDENTIFIER '(' ')' '{' statements '}' { printf("Def %s()\n", $2); }
    ;

return_statement:
    RETURN expression ';' { printf("Return %d\n", $2->value.num); freeNode($2); }
    ;

expression:
    NUMBER { $$ = makeNode(NUMBER, $1); }
    | IDENTIFIER { $$ = makeNode(IDENTIFIER, $1); }
    ;

statements:
    | statements statement
    ;

%%

int main() {
    yyparse();
    return 0;
}
