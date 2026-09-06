はい、Osloのコンパイラーの構文解析器と字句生成器を合わせて、C言語で、oslo.cとして、flexとbisonとは違う、元からソースコードを作りました。

```c
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

typedef struct {
  int type;
  union {
    int number;
    char *identifier;
    struct {
      char *identifier;
      struct Node *expression;
    } let;
    struct {
      char *identifier;
      struct Node **statements;
      int num_statements;
    } def;
    struct {
      struct Node *expression;
    } ret;
  } data;
} Node;

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
  default:
    fprintf(stderr, "Unexpected character: %c\n", input_str[current_pos]);
    exit(1);
  }
}

Node *parse_expression() {
  Token *token = next_token();
  if (token == NULL) {
    fprintf(stderr, "Unexpected end of input\n");
    exit(1);
  }

  if (token->type == TOKEN_NUMBER) {
    Node *node = malloc(sizeof(Node));
    node->type = TOKEN_NUMBER;
    node->data.number = atoi(token->value);
    free(token->value);
    free(token);
    return node;
  } else if (token->type == TOKEN_IDENTIFIER) {
    Node *node = malloc(sizeof(Node));
    node->type = TOKEN_IDENTIFIER;
    node->data.identifier = token->value;
    free(token);
    return node;
  } else {
    fprintf(stderr, "Unexpected token: %s\n", token->value);
    exit(1);
  }
}

Node *parse_let_statement() {
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

  Node *expression = parse_expression();

  token = next_token();
  if (token == NULL || token->type != TOKEN_SEMICOLON) {
    fprintf(stderr, "Expected ';' after expression\n");
    exit(1);
  }
  free(token);

  Node *node = malloc(sizeof(Node));
  node->type = TOKEN_LET;
  node->data.let.identifier = identifier;
  node->data.let.expression = expression;
  return node;
}

Node *parse_def_statement() {
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

  Node **statements = NULL;
  int num_statements = 0;
  while (1) {
    Node *statement = parse_statement();
    if (statement == NULL) {
      break;
    }
    statements = realloc(statements, (num_statements + 1) * sizeof(Node *));
    statements[num_statements++] = statement;
  }

  token = next_token();
  if (token == NULL || token->type != TOKEN_RBRACE) {
    fprintf(stderr, "Expected '}' after statements\n");
    exit(1);
  }
  free(token);

  Node *node = malloc(sizeof(Node));
  node->type = TOKEN_DEF;
  node->data.def.identifier = identifier;
  node->data.def.statements = statements;
  node->data.def.num_statements = num_statements;
  return node;
}

Node *parse_return_statement() {
  Node *expression = parse_expression();

  Token *token = next_token();
  if (token == NULL || token->type != TOKEN_SEMICOLON) {
    fprintf(stderr, "Expected ';' after expression\n");
    exit(1);
  }
  free(token);

  Node *node = malloc(sizeof(Node));
  node->type = TOKEN_RETURN;
  node->data.ret.expression = expression;
  return node;
}

Node *parse_statement() {
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

Node *parse_program() {
  Node *program = NULL;
  while (1) {
    Node *statement = parse_statement();
    if (statement == NULL) {
      break;
    }
    program = realloc(program, (program == NULL ? 1 : 2) * sizeof(Node *));
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

  Node *program = parse_program();
  // Do something with the parsed program

  free(input_str);
  return 0;
}
```

このソースコードには以下の機能が含まれています:

1. **トークンの定義**:
   - `TokenType` 列挙型で、トークンの種類を定義しています。

   2. **抽象構文木のノードの定義**:
   - `Node` 構造体で、抽象構文木のノードを表現しています。

   3. **字句解析の処理**:
- `next_token()` 関数で、入力文字列からトークンを生成します。

4. **構文解析の処理**:
- `parse_expression()`、`parse_let_statement()`、`parse_def_statement()`、`parse_return_statement()`、`parse_statement()`、`parse_program()` 関数で、それぞれの構文要素を解析します。

5. **メインの処理**:
- `main()` 関数で、入力ファイルを読み込み、抽象構文木を生成します。

この実装では、Osloプログラミング言語の基本的な構文解析を行っています。具体的には、`let`、`def`、`return`ステートメントの解析と、数値や識別子を表すノードの生成を行っています。

必要に応じて、この実装を拡張して、式の評価や型チェック、コード生成などの機能を追加することができます。
