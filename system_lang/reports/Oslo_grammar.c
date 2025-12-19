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

// 構文解析器
typedef struct {
  Token *tokens;
  int index;
} Parser;

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

// 構文解析ルール
ASTNode *parse_program(Parser *parser) {
  ASTNode *program = malloc(sizeof(ASTNode));
  program->type = AST_PROGRAM;
  program->children = malloc(sizeof(ASTNode *) * 1024);
  program->childCount = 0;

  while (parser_current_token(parser)->type != TOKEN_EOF) {
    ASTNode *statement = parse_statement(parser);
    program->children[program->childCount++] = statement;
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

// その他の構文解析ルールの実装 (省略)

int main(int argc, char *argv[]) {
  char *input = "let x = 42\nlet y = \"hello\"\ndef add(a, b) {\n    return a + b\n}";
  Token *tokens = lex(input);
  Parser *parser = parser_new(tokens);
  ASTNode *program = parse_program(parser);

  // AST の出力
  print_ast(program, 0);

  // メモリの解放
  free_ast(program);
  parser_free(parser);
  for (int i = 0; tokens[i].type != TOKEN_EOF; i++) {
    free(tokens[i].value);
  }
  free(tokens);

  return 0;
}
