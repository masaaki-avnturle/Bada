#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>
#include <math.h>

typedef enum {
	      TOKEN_LET,
	      TOKEN_DEF,
	      TOKEN_RETURN,
	      TOKEN_NUMBER,
	      TOKEN_IDENTIFIER,
	      TOKEN_LBRACE,
	      TOKEN_RBRACE,
	      TOKEN_LPAREN,
	      TOKEN_RPAREN,
	      TOKEN_ASSIGN,
	      TOKEN_SEMICOLON,
	      TOKEN_COMMA,
	      TOKEN_LBRACKET,
    TOKEN_RBRACKET
} TokenType;

typedef struct {
  TokenType type;
  char *value;
} Token;

typedef enum {
	      NODE_NUMBER,
	      NODE_IDENTIFIER,
	      NODE_LET,
	      NODE_DEF,
	      NODE_RETURN,
	      NODE_ARRAY,
	      NODE_HASH,
	      NODE_TUPLE,
    NODE_LIST
} NodeType;

typedef struct ASTNode {
  NodeType type;
  union {
    int number;
    char *identifier;
    struct {
      char *identifier;
      struct ASTNode *expression;
    } let;
    struct {
      char *identifier;
      struct ASTNode **statements;
      int num_statements;
    } def;
    struct {
      struct ASTNode *expression;
    } ret;
    struct {
      struct ASTNode **elements;
      int num_elements;
    } array;
    struct {
      char **keys;
      struct ASTNode **values;
      int num_entries;
    } hash;
    struct {
      struct ASTNode **elements;
      int num_elements;
    } tuple;
    struct {
      struct ASTNode **elements;
      int num_elements;
    } list;
  } data;
} ASTNode;

int current_pos = 0;
char *input_str;

Token *next_token() {
  while (input_str[current_pos] == ' ' || input_str[current_pos] == '\t' || input_str[current_pos] == '\n') {
    current_pos++;
  }

  if (input_str[current_pos] == '\0') {
    return NULL;
  }

  if (strncmp(&input_str[current_pos], "let", 3) == 0) {
    Token *token = malloc(sizeof(Token));
    token->type = TOKEN_LET;
    token->value = "let";
    current_pos += 3;
    return token;
  }

  if (strncmp(&input_str[current_pos], "def", 3) == 0) {
    Token *token = malloc(sizeof(Token));
    token->type = TOKEN_DEF;
    token->value = "def";
    current_pos += 3;
    return token;
  }

  if (strncmp(&input_str[current_pos], "return", 6) == 0) {
    Token *token = malloc(sizeof(Token));
    token->type = TOKEN_RETURN;
    token->value = "return";
    current_pos += 6;
    return token;
  }

  if (isdigit(input_str[current_pos])) {
    int start = current_pos;
    while (isdigit(input_str[current_pos])) {
      current_pos++;
    }
    Token *token = malloc(sizeof(Token));
    token->type = TOKEN_NUMBER;
    token->value = malloc(current_pos - start + 1);
    strncpy(token->value, &input_str[start], current_pos - start);
    token->value[current_pos - start] = '\0';
    return token;
  }

  if (isalpha(input_str[current_pos]) || input_str[current_pos] == '_') {
    int start = current_pos;
    while (isalnum(input_str[current_pos]) || input_str[current_pos] == '_') {
      current_pos++;
    }
    Token *token = malloc(sizeof(Token));
    token->type = TOKEN_IDENTIFIER;
    token->value = malloc(current_pos - start + 1);
    strncpy(token->value, &input_str[start], current_pos - start);
    token->value[current_pos - start] = '\0';
    return token;
  }

  switch (input_str[current_pos]) {
  case '{':
    current_pos++;
    Token *lbrace_token = malloc(sizeof(Token));
    lbrace_token->type = TOKEN_LBRACE;
    lbrace_token->value = "{";
    return lbrace_token;
  case '}':
    current_pos++;
    Token *rbrace_token = malloc(sizeof(Token));
    rbrace_token->type = TOKEN_RBRACE;
    rbrace_token->value = "}";
    return rbrace_token;
  case '(':
    current_pos++;
    Token *lparen_token = malloc(sizeof(Token));
    lparen_token->type = TOKEN_LPAREN;
    lparen_token->value = "(";
    return lparen_token;
  case ')':
    current_pos++;
    Token *rparen_token = malloc(sizeof(Token));
    rparen_token->type = TOKEN_RPAREN;
    rparen_token->value = ")";
    return rparen_token;
  case '=':
    current_pos++;
    Token *assign_token = malloc(sizeof(Token));
    assign_token->type = TOKEN_ASSIGN;
    assign_token->value = "=";
    return assign_token;
  case ';':
    current_pos++;
    Token *semicolon_token = malloc(sizeof(Token));
    semicolon_token->type = TOKEN_SEMICOLON;
    semicolon_token->value = ";";
    return semicolon_token;
  case ',':
    current_pos++;
    Token *comma_token = malloc(sizeof(Token));
    comma_token->type = TOKEN_COMMA;
    comma_token->value = ",";
    return comma_token;
  case '[':
    current_pos++;
    Token *lbracket_token = malloc(sizeof(Token));
    lbracket_token->type = TOKEN_LBRACKET;
    lbracket_token->value = "[";
    return lbracket_token;
  case ']':
    current_pos++;
    Token *rbracket_token = malloc(sizeof(Token));
    rbracket_token->type = TOKEN_RBRACKET;
    rbracket_token->value = "]";
    return rbracket_token;
  default:
    fprintf(stderr, "Unexpected character: %c\n", input_str[current_pos]);
    exit(1);
  }
}

ASTNode *parse_expression() {
  Token *token = next_token();
  if (token == NULL) {
    fprintf(stderr, "Unexpected end of input\n");
    exit(1);
  }

  if (token->type == TOKEN_NUMBER) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_NUMBER;
    node->data.number = atoi(token->value);
    free(token->value);
    free(token);
    return node;
  } else if (token->type == TOKEN_IDENTIFIER) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = NODE_IDENTIFIER;
    node->data.identifier = token->value;
    free(token);
    return node;
  } else if (token->type == TOKEN_LBRACKET) {
    free(token);
    return parse_array();
  } else if (token->type == TOKEN_LBRACE) {
    free(token);
    return parse_hash();
  } else if (token->type == TOKEN_LPAREN) {
    free(token);
    return parse_tuple();
  } else if (token->type == TOKEN_LBRACKET) {
    free(token);
    return parse_list();
  } else {
    fprintf(stderr, "Unexpected token: %s\n", token->value);
    exit(1);
  }
}

ASTNode *parse_let_statement() {
  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_IDENTIFIER) {
    fprintf(stderr, "Expected identifier after 'let'\n");
    exit(1);
  }
  char *identifier = token->value;
  free(token);

  token = next_token();
  if (token == NULL || token->type != TOKEN_ASSIGN) {
    fprintf(stderr, "Expected '=' after identifier\n");
    exit(1);
  }
  free(token);

  ASTNode *expression = parse_expression();

  token = next_token();
  if (token == NULL || token->type != TOKEN_SEMICOLON) {
    fprintf(stderr, "Expected ';' after expression\n");
    exit(1);
  }
  free(token);

  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = NODE_LET;
  node->data.let.identifier = identifier;
  node->data.let.expression = expression;
  return node;
}

ASTNode *parse_def_statement() {
  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_IDENTIFIER) {
    fprintf(stderr, "Expected identifier after 'def'\n");
    exit(1);
  }
  char *identifier = token->value;
  free(token);

  token = next_token();
  if (token == NULL || token->type != TOKEN_LPAREN) {
    fprintf(stderr, "Expected '(' after identifier\n");
    exit(1);
  }
  free(token);

  token = next_token();
  if (token == NULL || token->type != TOKEN_RPAREN) {
    fprintf(stderr, "Expected ')' after '('\n");
    exit(1);
  }
  free(token);

  token = next_token();
  if (token == NULL || token->type != TOKEN_LBRACE) {
    fprintf(stderr, "Expected '{' after ')'\n");
    exit(1);
  }
  free(token);

  ASTNode **statements = NULL;
  int num_statements = 0;
  while (1) {
    ASTNode *statement = parse_statement();
    if (statement == NULL) {
      break;
    }
    statements = realloc(statements, (num_statements + 1) * sizeof(ASTNode *));
    statements[num_statements++] = statement;
  }

  token = next_token();
  if (token == NULL || token->type != TOKEN_RBRACE) {
    fprintf(stderr, "Expected '}' after statements\n");
    exit(1);
  }
  free(token);

  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = NODE_DEF;
  node->data.def.identifier = identifier;
  node->data.def.statements = statements;
  node->data.def.num_statements = num_statements;
  return node;
}

ASTNode *parse_return_statement() {
  ASTNode *expression = parse_expression();

  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_SEMICOLON) {
    fprintf(stderr, "Expected ';' after expression\n");
    exit(1);
  }
  free(token);

  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = NODE_RETURN;
  node->data.ret.expression = expression;
  return node;
}

ASTNode *parse_array() {
  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_LBRACKET) {
    fprintf(stderr, "Expected '[' for array\n");
    exit(1);
  }
  free(token);

  ASTNode **elements = NULL;
  int num_elements = 0;

  while (1) {
    ASTNode *element = parse_expression();
    if (element == NULL) {
      break;
    }
    elements = realloc(elements, (num_elements + 1) * sizeof(ASTNode *));
    elements[num_elements++] = element;

    token = next_token();
    if (token == NULL || token->type == TOKEN_RBRACKET) {
      free(token);
      break;
    } else if (token->type != TOKEN_COMMA) {
      fprintf(stderr, "Expected ',' or ']' for array\n");
      exit(1);
    }
    free(token);
  }

  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = NODE_ARRAY;
  node->data.array.elements = elements;
  node->data.array.num_elements = num_elements;
  return node;
}

ASTNode *parse_hash() {
  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_LBRACE) {
    fprintf(stderr, "Expected '{' for hash\n");
    exit(1);
  }
  free(token);

  char **keys = NULL;
  ASTNode **values = NULL;
  int num_entries = 0;

  while (1) {
    token = next_token();
    if (token == NULL || token->type != TOKEN_IDENTIFIER) {
      fprintf(stderr, "Expected identifier for hash key\n");
      exit(1);
    }
    char *key = token->value;
    free(token);

    token = next_token();
    if (token == NULL || token->type != TOKEN_ASSIGN) {
      fprintf(stderr, "Expected '=' for hash entry\n");
      exit(1);
    }
    free(token);

    ASTNode *value = parse_expression();

    keys = realloc(keys, (num_entries + 1) * sizeof(char *));
    values = realloc(values, (num_entries + 1) * sizeof(ASTNode *));
    keys[num_entries] = key;
    values[num_entries++] = value;

    token = next_token();
    if (token == NULL || token->type == TOKEN_RBRACE) {
      free(token);
      break;
    } else if (token->type != TOKEN_COMMA) {
      fprintf(stderr, "Expected ',' or '}' for hash\n");
      exit(1);
    }
    free(token);
  }

  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = NODE_HASH;
  node->data.hash.keys = keys;
  node->data.hash.values = values;
  node->data.hash.num_entries = num_entries;
  return node;
}

ASTNode *parse_tuple() {
  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_LPAREN) {
    fprintf(stderr, "Expected '(' for tuple\n");
    exit(1);
  }
  free(token);

  ASTNode **elements = NULL;
  int num_elements = 0;

  while (1) {
    ASTNode *element = parse_expression();
    if (element == NULL) {
      break;
    }
    elements = realloc(elements, (num_elements + 1) * sizeof(ASTNode *));
    elements[num_elements++] = element;

    token = next_token();
    if (token == NULL || token->type == TOKEN_RPAREN) {
      free(token);
      break;
    } else if (token->type != TOKEN_COMMA) {
      fprintf(stderr, "Expected ',' or ')' for tuple\n");
      exit(
	   はい、省略していた部分も含めて、完全なソースコードを記述します。

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <regex.h>
#include <math.h>

	   typedef enum {
			 TOKEN_LET,
			 TOKEN_DEF,
			 TOKEN_RETURN,
			 TOKEN_NUMBER,
			 TOKEN_IDENTIFIER,
			 TOKEN_LBRACE,
			 TOKEN_RBRACE,
			 TOKEN_LPAREN,
			 TOKEN_RPAREN,
			 TOKEN_ASSIGN,
			 TOKEN_SEMICOLON,
			 TOKEN_COMMA,
			 TOKEN_LBRACKET,
    TOKEN_RBRACKET
	   } TokenType;

	   typedef struct {
	     TokenType type;
	     char *value;
	   } Token;

	   typedef enum {
			 NODE_NUMBER,
			 NODE_IDENTIFIER,
			 NODE_LET,
			 NODE_DEF,
			 NODE_RETURN,
			 NODE_ARRAY,
			 NODE_HASH,
			 NODE_TUPLE,
    NODE_LIST
	   } NodeType;

	   typedef struct ASTNode {
	     NodeType type;
	     union {
	       int number;
	       char *identifier;
	       struct {
		 char *identifier;
		 struct ASTNode *expression;
	       } let;
	       struct {
		 char *identifier;
		 struct ASTNode **statements;
		 int num_statements;
	       } def;
	       struct {
		 struct ASTNode *expression;
	       } ret;
	       struct {
		 struct ASTNode **elements;
		 int num_elements;
	       } array;
	       struct {
		 char **keys;
		 struct ASTNode **values;
		 int num_entries;
	       } hash;
	       struct {
		 struct ASTNode **elements;
		 int num_elements;
	       } tuple;
	       struct {
		 struct ASTNode **elements;
		 int num_elements;
	       } list;
	     } data;
	   } ASTNode;

	   int current_pos = 0;
	   char *input_str;

	   Token *next_token() {
	     while (input_str[current_pos] == ' ' || input_str[current_pos] == '\t' || input_str[current_pos] == '\n') {
	       current_pos++;
	     }

	     if (input_str[current_pos] == '\0') {
	       return NULL;
	     }

	     if (strncmp(&input_str[current_pos], "let", 3) == 0) {
	       Token *token = malloc(sizeof(Token));
	       token->type = TOKEN_LET;
	       token->value = "let";
	       current_pos += 3;
	       return token;
	     }

	     if (strncmp(&input_str[current_pos], "def", 3) == 0) {
	       Token *token = malloc(sizeof(Token));
	       token->type = TOKEN_DEF;
	       token->value = "def";
	       current_pos += 3;
	       return token;
	     }

	     if (strncmp(&input_str[current_pos], "return", 6) == 0) {
	       Token *token = malloc(sizeof(Token));
	       token->type = TOKEN_RETURN;
	       token->value = "return";
	       current_pos += 6;
	       return token;
	     }

	     if (isdigit(input_str[current_pos])) {
	       int start = current_pos;
	       while (isdigit(input_str[current_pos])) {
		 current_pos++;
	       }
	       Token *token = malloc(sizeof(Token));
	       token->type = TOKEN_NUMBER;
	       token->value = malloc(current_pos - start + 1);
	       strncpy(token->value, &input_str[start], current_pos - start);
	       token->value[current_pos - start] = '\0';
	       return token;
	     }

	     if (isalpha(input_str[current_pos]) || input_str[current_pos] == '_') {
	       int start = current_pos;
	       while (isalnum(input_str[current_pos]) || input_str[current_pos] == '_') {
		 current_pos++;
	       }
	       Token *token = malloc(sizeof(Token));
	       token->type = TOKEN_IDENTIFIER;
	       token->value = malloc(current_pos - start + 1);
	       strncpy(token->value, &input_str[start], current_pos - start);
	       token->value[current_pos - start] = '\0';
	       return token;
	     }

	     switch (input_str[current_pos]) {
	     case '{':
	       current_pos++;
	       Token *lbrace_token = malloc(sizeof(Token));
	       lbrace_token->type = TOKEN_LBRACE;
	       lbrace_token->value = "{";
	       return lbrace_token;
	     case '}':
	       current_pos++;
	       Token *rbrace_token = malloc(sizeof(Token));
	       rbrace_token->type = TOKEN_RBRACE;
	       rbrace_token->value = "}";
	       return rbrace_token;
	     case '(':
	       current_pos++;
	       Token *lparen_token = malloc(sizeof(Token));
	       lparen_token->type = TOKEN_LPAREN;
	       lparen_token->value = "(";
	       return lparen_token;
	     case ')':
	       current_pos++;
	       Token *rparen_token = malloc(sizeof(Token));
	       rparen_token->type = TOKEN_RPAREN;
	       rparen_token->value = ")";
	       return rparen_token;
	     case '=':
	       current_pos++;
	       Token *assign_token = malloc(sizeof(Token));
	       assign_token->type = TOKEN_ASSIGN;
	       assign_token->value = "=";
	       return assign_token;
	     case ';':
	       current_pos++;
	       Token *semicolon_token = malloc(sizeof(Token));
	       semicolon_token->type = TOKEN_SEMICOLON;
	       semicolon_token->value = ";";
	       return semicolon_token;
	     case ',':
	       current_pos++;
	       Token *comma_token = malloc(sizeof(Token));
	       comma_token->type = TOKEN_COMMA;
	       comma_token->value = ",";
	       return comma_token;
	     case '[':
	       current_pos++;
	       Token *lbracket_token = malloc(sizeof(Token));
	       lbracket_token->type = TOKEN_LBRACKET;
	       lbracket_token->value = "[";
	       return lbracket_token;
	     case ']':
	       current_pos++;
	       Token *rbracket_token = malloc(sizeof(Token));
	       rbracket_token->type = TOKEN_RBRACKET;
	       rbracket_token->value = "]";
	       return rbracket_token;
	     default:
	       fprintf(stderr, "Unexpected character: %c\n", input_str[current_pos]);
	       exit(1);
	     }
	   }

	   ASTNode *parse_expression() {
	     Token *token = next_token();
	     if (token == NULL) {
	       fprintf(stderr, "Unexpected end of input\n");
	       exit(1);
	     }

	     if (token->type == TOKEN_NUMBER) {
	       ASTNode *node = malloc(sizeof(ASTNode));
	       node->type = NODE_NUMBER;
	       node->data.number = atoi(token->value);
	       free(token->value);
	       free(token);
	       return node;
	     } else if (token->type == TOKEN_IDENTIFIER) {
	       ASTNode *node = malloc(sizeof(ASTNode));
	       node->type = NODE_IDENTIFIER;
	       node->data.identifier = token->value;
	       free(token);
	       return node;
	     } else if (token->type == TOKEN_LBRACKET) {
	       free(token);
	       return parse_array();
	     } else if (token->type == TOKEN_LBRACE) {
	       free(token);
	       return parse_hash();
	     } else if (token->type == TOKEN_LPAREN) {
	       free(token);
	       return parse_tuple();
	     } else if (token->type == TOKEN_LBRACKET) {
	       free(token);
	       return parse_list();
	     } else {
	       fprintf(stderr, "Unexpected token: %s\n", token->value);
	       exit(1);
	     }
	   }

	   ASTNode *parse_let_statement() {
	     Token *token = next_token();
	     if (token == NULL || token->type != TOKEN_IDENTIFIER) {
	       fprintf(stderr, "Expected identifier after 'let'\n");
	       exit(1);
	     }
	     char *identifier = token->value;
	     free(token);

	     token = next_token();
	     if (token == NULL || token->type != TOKEN_ASSIGN) {
	       fprintf(stderr, "Expected '=' after identifier\n");
	       exit(1);
	     }
	     free(token);

	     ASTNode *expression = parse_expression();

	     token = next_token();
	     if (token == NULL || token->type != TOKEN_SEMICOLON) {
	       fprintf(stderr, "Expected ';' after expression\n");
	       exit(1);
	     }
	     free(token);

	     ASTNode *node = malloc(sizeof(ASTNode));
	     node->type = NODE_LET;
	     node->data.let.identifier = identifier;
	     node->data.let.expression = expression;
	     return node;
	   }

	   ASTNode *parse_def_statement() {
	     Token *token = next_token();
	     if (token == NULL || token->type != TOKEN_IDENTIFIER) {
	       fprintf(stderr, "Expected identifier after 'def'\n");
	       exit(1);
	     }
	     char *identifier = token->value;
	     free(token);

	     token = next_token();
	     if (token == NULL || token->type != TOKEN_LPAREN) {
	       fprintf(stderr, "Expected '(' after identifier\n");
	       exit(1);
	     }
	     free(token);

	     token = next_token();
	     if (token == NULL || token->type != TOKEN_RPAREN) {
	       fprintf(stderr, "Expected ')' after '('\n");
	       exit(1);
	     }
	     free(token);

	     token = next_token();
	     if (token == NULL || token->type != TOKEN_LBRACE) {
	       fprintf(stderr, "Expected '{' after ')'\n");
	       exit(1);
	     }
	     free(token);

	     ASTNode **statements = NULL;
	     int num_statements = 0;
	     while (1) {
	       ASTNode *statement = parse_statement();
	       if (statement == NULL) {
		 break;
	       }
	       statements = realloc(statements, (num_statements + 1) * sizeof(ASTNode *));
	       statements[num_statements++] = statement;
	     }

	     token = next_token();
	     if (token == NULL || token->type != TOKEN_RBRACE) {
	       fprintf(stderr, "Expected '}' after statements\n");
	       exit(1);
	     }
	     free(token);

	     ASTNode *node = malloc(sizeof(ASTNode));
	     node->type = NODE_DEF;
	     node->data.def.identifier = identifier;
	     node->data.def.statements = statements;
	     node->data.def.num_statements = num_statements;
	     return node;
	   }

	   ASTNode *parse_return_statement() {
	     ASTNode *expression = parse_expression();

	     Token *token = next_token();
	     if (token == NULL || token->type != TOKEN_SEMICOLON) {
	       fprintf(stderr, "Expected ';' after expression\n");
	       exit(1);
	     }
	     free(token);

	     ASTNode *node = malloc(sizeof(ASTNode));
	     node->type = NODE_RETURN;
	     node->data.ret.expression = expression;
	     return node;
	   }

	   ASTNode *parse_array() {
	     Token *token = next_token();
	     if (token == NULL || token->type != TOKEN_LBRACKET) {
	       fprintf(stderr, "Expected '[' for array\n");
	       exit(1);
	     }
	     free(token);

	     ASTNode **elements = NULL;
	     int num_elements = 0;

	     while (1) {
	       ASTNode *element = parse_expression();
	       if (element == NULL) {
		 break;
	       }
	       elements = realloc(elements, (num_elements + 1) * sizeof(ASTNode *));
	       elements[num_elements++] = element;

	       token = next_token();
	       if (token == NULL || token->type == TOKEN_RBRACKET) {
		 free(token);
		 break;
	       } else if (token->type != TOKEN_COMMA) {
		 fprintf(stderr, "Expected ',' or ']' for array\n");
		 exit(1);
	       }
	       free(token);
	     }

	     ASTNode *node = malloc(sizeof(ASTNode));
	     node->type = NODE_ARRAY;
	     node->data.array.elements = elements;
	     node->data.array.num_elements = num_elements;
	     return node;
	   }

	   ASTNode *parse_hash() {
	     Token *token = next_token();
	     if (token == NULL || token->type != TOKEN_LBRACE) {
	       fprintf(stderr, "Expected '{' for hash\n");
	       exit(1);
	     }
	     free(token);

	     char **keys = NULL;
	     ASTNode **values = NULL;
	     int num_entries = 0;

	     while (1) {
	       token = next_token();
	       if (token == NULL || token->type != TOKEN_IDENTIFIER) {
		 fprintf(stderr, "Expected identifier for hash key\n");
		 exit(1);
	       }
	       char *key = token->value;
	       free(token);

	       token = next_token();
	       if (token == NULL || token->type != TOKEN_ASSIGN) {
		 fprintf(stderr, "Expected '=' for hash entry\n");
		 exit(1);
	       }
	       free(token);

	       ASTNode *value = parse_expression();

	       keys = realloc(keys, (num_entries + 1) * sizeof(char *));
	       values = realloc(values, (num_entries + 1) * sizeof(ASTNode *));
	       keys[num_entries] = key;
	       values[num_entries++] = value;

	       token = next_token();
	       if (token == NULL || token->type == TOKEN_RBRACE) {
		 free(token);
		 break;
	       } else if (token->type != TOKEN_COMMA) {
		 fprintf(stderr, "Expected ',' or '}' for hash\n");
		 exit(1);
	       }
	       free(token);
	     }

	     ASTNode *node = malloc(sizeof(ASTNode));
	     node->type = NODE_HASH;
	     node->data.hash.keys = keys;
	     node->data.hash.values = values;
	     node->data.hash.num_entries = num_entries;
	     return node;
	   }

	  		      ASTNode *parse_tuple() {
			Token *token = next_token();
			if (token == NULL || token->type != TOKEN_LPAREN) {
			  fprintf(stderr, "Expected '(' for tuple\n");
			  exit(1);
			}
			free(token);

			ASTNode **elements = NULL;
			int num_elements = 0;

			while (1) {
			  ASTNode *element = parse_expression();
			  if (element == NULL) {
			    break;
			  }
			  elements = realloc(elements, (num_elements + 1) * sizeof(ASTNode *));
			  elements[num_elements++] = element;

			  token = next_token();
			  if (token == NULL || token->type == TOKEN_RPAREN) {
			    free(token);
			    break;
			  } else if (token->type != TOKEN_COMMA) {
			    fprintf(stderr, "Expected ',' or ')' for tuple\n");
			    exit(1);
			  }
			  free(token);
			}

			ASTNode *node = malloc(sizeof(ASTNode));
			node->type = NODE_TUPLE;
			node->data.tuple.elements = elements;
			node->data.tuple.num_elements = num_elements;
			return node;
		      }

		      ASTNode *parse_list() {
			Token *token = next_token();
			if (token == NULL || token->type != TOKEN_LBRACKET) {
			  fprintf(stderr, "Expected '[' for list\n");
			  exit(1);
			}
			free(token);

			ASTNode **elements = NULL;
			int num_elements = 0;

			while (1) {
			  ASTNode *element = parse_expression();
			  if (element == NULL) {
			    break;
			  }
			  elements = realloc(elements, (num_elements + 1) * sizeof(ASTNode *));
			  elements[num_elements++] = element;

			  token = next_token();
			  if (token == NULL || token->type == TOKEN_RBRACKET) {
			    free(token);
			    break;
			  } else if (token->type != TOKEN_COMMA) {
			    fprintf(stderr, "Expected ',' or ']' for list\n");
			    exit(1);
			  }
			  free(token);
			}

			ASTNode *node = malloc(sizeof(ASTNode));
			node->type = NODE_LIST;
			node->data.list.elements = elements;
			node->data.list.num_elements = num_elements;
			return node;
		      }

		      ASTNode *parse_statement() {
			Token *token = next_token();
			if (token == NULL) {
			  return NULL;
			}

			if (token->type == TOKEN_LET) {
			  free(token);
			  return parse_let_statement();
			} else if (token->type == TOKEN_DEF) {
			  free(token);
			  return parse_def_statement();
			} else if (token->type == TOKEN_RETURN) {
			  free(token);
			  return parse_return_statement();
			} else if (token->type == TOKEN_LBRACKET) {
			  free(token);
			  return parse_array();
			} else if (token->type == TOKEN_LBRACE) {
			  free(token);
			  return parse_hash();
			} else if (token->type == TOKEN_LPAREN) {
			  free(token);
			  return parse_tuple();
			} else if (token->type == TOKEN_LBRACKET) {
			  free(token);
			  return parse_list();
			} else {
			  fprintf(stderr, "Unexpected token: %s\n", token->value);
			  exit(1);
			}
		      }

		      ASTNode *parse_program() {
			ASTNode *program = NULL;
			while (1) {
			  ASTNode *statement = parse_statement();
			  if (statement == NULL) {
			    break;
			  }
			  program = realloc(program, (program == NULL ? 1 : 2) * sizeof(ASTNode *));
			  program[program == NULL ? 0 : 1] = statement;
			}
			return program;
		      }

		      int main(int argc, char *argv[]) {
			if (argc != 2) {
			  fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
			  return 1;
			}

			FILE *fp = fopen(argv[1], "r");
			if (!fp) {
			  fprintf(stderr, "Error: could not open file %s\n", argv[1]);
			  return 1;
			}

			fseek(fp, 0, SEEK_END);
			long size = ftell(fp);
			fseek(fp, 0, SEEK_SET);

			input_str = malloc(size + 1);
			fread(input_str, 1, size, fp);
			input_str[size] = '\0';

			fclose(fp);

			ASTNode *program = parse_program();
			// Do something with the parsed program

			free(input_str);
			return 0;
		      }
    }
  }
}
