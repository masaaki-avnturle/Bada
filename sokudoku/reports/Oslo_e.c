#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// トークンの種類
typedef enum {
	      TOKEN_IDENTIFIER,
	      TOKEN_NUMBER,
	      TOKEN_STRING,
	      TOKEN_OPERATOR,
	      TOKEN_KEYWORD,
    TOKEN_EOF
} TokenType;

// トークン構造体
typedef struct {
  TokenType type;
  char *value;
  int line;
  int column;
} Token;

// 字句解析器
Token *lex(char *input) {
  // 字句解析器の実装 (省略)
}

// 抽象構文木のノード
typedef struct ASTNode {
  int type;
  char *value;
  struct ASTNode *left;
  struct ASTNode *right;
} ASTNode;

// 構文解析器
ASTNode *parse(Token *tokens) {
  // 構文解析器の実装 (省略)
}

// 評価器
int evaluate(ASTNode *node) {
  switch (node->type) {
  case AST_NUMBER:
    return atoi(node->value);
  case AST_IDENTIFIER:
    // 変数の値を返す
    return 0;
  case AST_BINARY_OPERATION:
    int left = evaluate(node->left);
    int right = evaluate(node->right);
    if (strcmp(node->value, "+") == 0) {
      return left + right;
    } else if (strcmp(node->value, "-") == 0) {
      return left - right;
    } else if (strcmp(node->value, "*") == 0) {
      return left * right;
    } else if (strcmp(node->value, "/") == 0) {
      return left / right;
    }
    break;
  }
  return 0;
}

// コンパイラー
void compile(ASTNode *node) {
  switch (node->type) {
  case AST_NUMBER:
    // 数値のコード生成
    break;
  case AST_IDENTIFIER:
    // 変数のコード生成
    break;
  case AST_BINARY_OPERATION:
    // 二項演算のコード生成
    compile(node->left);
    compile(node->right);
    break;
  }
}

			  // トークンの種類
  typedef enum {
		TOKEN_IDENTIFIER,
		TOKEN_NUMBER,
		TOKEN_STRING,
		TOKEN_OPERATOR,
		TOKEN_KEYWORD,
    TOKEN_EOF
} TokenType;

// トークン構造体
typedef struct {
  TokenType type;
  char *value;
  int line;
  int column;
} Token;

// 字句解析器
Token *lex(char *input) {
  int i = 0, line = 1, column = 1;
  Token *tokens = malloc(sizeof(Token) * 1024);
  int tokenCount = 0;

  while (input[i] != '\0') {
    // 空白文字をスキップ
    while (isspace(input[i])) {
      if (input[i] == '\n') {
	line++;
	column = 1;
      } else {
	column++;
      }
      i++;
    }

    // 識別子
    if (isalpha(input[i])) {
      int start = i;
      while (isalnum(input[i])) {
	i++;
      }
      tokens[tokenCount].type = TOKEN_IDENTIFIER;
      tokens[tokenCount].value = malloc(i - start + 1);
      strncpy(tokens[tokenCount].value, input + start, i - start);
      tokens[tokenCount].value[i - start] = '\0';
      tokens[tokenCount].line = line;
      tokens[tokenCount].column = column;
      column += i - start;
      tokenCount++;
    }
    // 数値
    else if (isdigit(input[i])) {
      int start = i;
      while (isdigit(input[i])) {
	i++;
      }
      tokens[tokenCount].type = TOKEN_NUMBER;
      tokens[tokenCount].value = malloc(i - start + 1);
      strncpy(tokens[tokenCount].value, input + start, i - start);
      tokens[tokenCount].value[i - start] = '\0';
      tokens[tokenCount].line = line;
      tokens[tokenCount].column = column;
      column += i - start;
      tokenCount++;
    }
    // 文字列
    else if (input[i] == '"') {
      int start = i + 1;
      i++;
      while (input[i] != '"' && input[i] != '\0') {
	if (input[i] == '\n') {
	  line++;
	  column = 1;
	} else {
	  column++;
	}
	i++;
      }
      if (input[i] == '\0') {
	fprintf(stderr, "Error: Unterminated string at line %d, column %d\n", line, column);
	exit(1);
      }
      tokens[tokenCount].type = TOKEN_STRING;
      tokens[tokenCount].value = malloc(i - start + 1);
      strncpy(tokens[tokenCount].value, input + start, i - start);
      tokens[tokenCount].value[i - start] = '\0';
      tokens[tokenCount].line = line;
      tokens[tokenCount].column = column - (i - start);
      i++;
      column++;
      tokenCount++;
    }
    // 演算子
    else if (strchr("+-*/=!<>", input[i])) {
      int start = i;
      i++;
      tokens[tokenCount].type = TOKEN_OPERATOR;
      tokens[tokenCount].value = malloc(2);
      tokens[tokenCount].value[0] = input[start];
      tokens[tokenCount].value[1] = '\0';
      tokens[tokenCount].line = line;
      tokens[tokenCount].column = column;
      column++;
      tokenCount++;
    }
    // キーワード
    else {
      fprintf(stderr, "Error: Unexpected character '%c' at line %d, column %d\n", input[i], line, column);
      exit(1);
    }
  }

  tokens[tokenCount].type = TOKEN_EOF;
  tokens[tokenCount].value = NULL;
  tokens[tokenCount].line = line;
  tokens[tokenCount].column = column;
  tokenCount++;

  return tokens;
}

// 抽象構文木のノード
typedef struct ASTNode {
  int type;
  char *value;
  struct ASTNode *left;
  struct ASTNode *right;
} ASTNode;

#define AST_NUMBER 1
#define AST_IDENTIFIER 2
#define AST_BINARY_OPERATION 3
#define AST_PROGRAM 4

// 構文解析器
ASTNode *parse(Token *tokens) {
  Parser *parser = parser_new(tokens);
  ASTNode *program = parse_program(parser);
  parser_free(parser);
  return program;
}

Parser *parser_new(Token *tokens) {
  Parser *parser = malloc(sizeof(Parser));
  parser->tokens = tokens;
  parser->index = 0;
  return parser;
}

void parser_free(Parser *parser) {
  free(parser);
}

Token *parser_current_token(Parser *parser) {
  return &parser->tokens[parser->index];
}

Token *parser_peek_token(Parser *parser) {
  return &parser->tokens[parser->index + 1];
}

void parser_advance(Parser *parser) {
  parser->index++;
}

ASTNode *parse_program(Parser *parser) {
  ASTNode *program = malloc(sizeof(ASTNode));
  program->type = AST_PROGRAM;
  program->value = NULL;
  program->left = NULL;
  program->right = NULL;

  while (parser_current_token(parser)->type != TOKEN_EOF) {
    ASTNode *statement = parse_statement(parser);
    // 文の処理を行う
  }

  return program;
}

ASTNode *parse_statement(Parser *parser) {
  Token *token = parser_current_token(parser);
  if (token->type == TOKEN_IDENTIFIER && parser_peek_token(parser)->value[0] == '=') {
    return parse_assignment(parser);
  } else if (token->type == TOKEN_IDENTIFIER && parser_peek_token(parser)->value[0] == '(') {
    return parse_function_call(parser);
  } else if (strcmp(token->value, "def") == 0) {
    return parse_function_definition(parser);
  } else if (strcmp(token->value, "let") == 0) {
    return parse_variable_declaration(parser);
  } else {
    fprintf(stderr, "Error: Unexpected token '%s' at line %d, column %d\n", token->value, token->line, token->column);
    exit(1);
  }
}

ASTNode *parse_assignment(Parser *parser) {
  // 代入文の解析処理
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_BINARY_OPERATION;
  node->value = "=";
  node->left = parse_expression(parser);
  node->right = parse_expression(parser);
  return node;
}

ASTNode *parse_function_call(Parser *parser) {
  // 関数呼び出しの解析処理
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_IDENTIFIER;
  node->value = parser_current_token(parser)->value;
  parser_advance(parser); // '(' を読み飛ばす
  // 引数の解析処理
  return node;
}

ASTNode *parse_function_definition(Parser *parser) {
  // 関数定義の解析処理
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_IDENTIFIER;
  node->value = parser_current_token(parser)->value;
  parser_advance(parser); // 'def' を読み飛ばす
  // 引数の解析処理
  // 関数本体の解析処理
  return node;
}

ASTNode *parse_variable_declaration(Parser *parser) {
  // 変数宣言の解析処理
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_IDENTIFIER;
  node->value = parser_current_token(parser)->value;
  parser_advance(parser); // 'let' を読み飛ばす
  // 変数名の解析処理
  // 初期値の解析処理
  return node;
}

ASTNode *parse_expression(Parser *parser) {
  // 式の解析処理
  ASTNode *left = parse_term(parser);
  while (parser_current_token(parser)->type == TOKEN_OPERATOR) {
    char *op = parser_current_token(parser)->value;
    parser_advance(parser);
    ASTNode *right = parse_term(parser);
    left = create_binary_operation(op, left, right);
  }
  return left;
}

ASTNode *parse_term(Parser *parser) {
  // 項の解析処理
  ASTNode *node = NULL;
  Token *token = parser_current_token(parser);
  if (token->type == TOKEN_NUMBER) {
    node = create_number_node(token->value);
  } else if (token->type == TOKEN_IDENTIFIER) {
    node = create_identifier_node(token->value);
  } else if (token->value[0] == '(') {
    parser_advance(parser);
    node = parse_expression(parser);
    if (parser_current_token(parser)->value[0] != ')') {
      fprintf(stderr, "Error: Expected ')' at line %d, column %d\n", token->line, token->column);
      exit(1);
    }
    parser_advance(parser);
  } else {
    fprintf(stderr, "Error: Unexpected token '%s' at line %d, column %d\n", token->value, token->line, token->column);
    exit(1);
  }
  return node;
}

ASTNode *create_number_node(char *value) {
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_NUMBER;
  node->value = value;
  node->left = NULL;
  node->right = NULL;
  return node;
}

ASTNode *create_identifier_node(char *value) {
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_IDENTIFIER;
  node->value = value;
  node->left = NULL;
  node->right = NULL;
  return node;
}

ASTNode *create_binary_operation(char *op, ASTNode *left, ASTNode *right) {
  ASTNode *node = malloc(sizeof(ASTNode));
  node->type = AST_BINARY_OPERATION;
  node->value = op;
  node->left = left;
  node->right = right;
  return node;
}

void free_ast(ASTNode *node) {
  if (node == NULL) {
    return;
  }
  free_ast(node->left);
  free_ast(node->right);
  free(node->value);
  free(node);
}

void free_tokens(Token *tokens) {
  for (int i = 0; tokens[i].type != TOKEN_EOF; i++) {
    free(tokens[i].value);
  }
  free(tokens);
}

int evaluate(ASTNode *node) {
  switch (node->type) {
  case AST_NUMBER:
    return atoi(node->value);
  case AST_IDENTIFIER:
    // 変数の値を返す
    return 0;
  case AST_BINARY_OPERATION:
    int left = evaluate(node->left);
    int right = evaluate(node->right);
    if (strcmp(node->value, "+") == 0) {
      return left + right;
    } else if (strcmp(node->value, "-") == 0) {
      return left - right;
    } else if (strcmp(node->value, "*") == 0) {
      return left * right;
    } else if (strcmp(node->value, "/") == 0) {
      return left / right;
    }
    break;
  }
  return 0;
}

void compile(ASTNode *node) {
  switch (node->type) {
  case AST_NUMBER:
    // 数値のコード生成
    break;
  case AST_IDENTIFIER:
    // 変数のコード生成
    break;
  case AST_BINARY_OPERATION:
    // 二項演算のコード生成
    compile(node->left);
    compile(node->right);
    break;
  }
}

int main(int argc, char *argv[]) {
  char *input = "let x = 42\nlet y = 10\nx + y";

  // 字句解析
  Token *tokens = lex(input);

  // 構文解析
  ASTNode *ast = parse(tokens);

  // 評価
  int result = evaluate(ast);
  printf("Result: %d\n", result);

  // コンパイル
  compile(ast);

  // メモリの解放
  free_tokens(tokens);
  free_ast(ast);

  return 0;
}
