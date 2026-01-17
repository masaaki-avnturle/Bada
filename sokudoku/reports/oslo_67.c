#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    TOKEN_SEMICOLON
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
    NODE_RETURN
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

  // 他のトークンの処理も追加する

  switch (input_str[current_pos]) {
  case '{':
    current_pos++;
    Token *lbrace_token = malloc(sizeof(Token));
    lbrace_token->type = TOKEN_LBRACE;
    lbrace_token->value = "{";
    return lbrace_token;
    // 他の特殊文字のトークンの処理も追加する
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
