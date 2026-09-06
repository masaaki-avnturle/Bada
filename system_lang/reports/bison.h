#ifndef BISON_H
#define BISON_H

#include <stdarg.h>

typedef enum {
	      LET,
	      DEF,
	      RETURN,
	      NUMBER,
    IDENTIFIER
} TokenType;

typedef struct {
  int type;
  union {
    int num;
    char *str;
  } value;
} Node;

Node *makeNode(int type, ...);
void freeNode(Node *node);

#endif // BISON_H
