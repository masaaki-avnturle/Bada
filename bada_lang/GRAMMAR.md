# Bada — Grammar & Bytecode Reference

## Lexical structure

- **Comments:** `// line` and `/* block */`.
- **Numbers:** `42`, `3.14`, `.5`. Integers and floats are distinct.
- **Strings:** `"..."` or `'...'`, with escapes `\n \t \r \\ \" \' \0`.
- **Identifiers:** letter or `_` followed by letters/digits/`_`.
- **Keywords:** `let class method static field operator fun if else while for
  in return break continue print import and or not true false nil self super`.
- **Operators / punctuation:**
  `<- <~ ~> -< :: => == != <= >= < > + - * / % ( ) { } [ ] , . : ;`

## Grammar (EBNF)

```ebnf
program     = { statement } ;

statement   = letStmt | classDecl | funcDecl | ifStmt | whileStmt
            | forStmt | returnStmt | "break" | "continue"
            | printStmt | importStmt | block | exprStmt ;

letStmt     = "let" IDENT "<-" expression ;
funcDecl    = "fun" IDENT params block ;
classDecl   = "class" IDENT [ "<-" IDENT ] "{" { member } "}" ;
member      = fieldDecl | methodDecl | operatorDecl ;
fieldDecl   = "field" IDENT [ "<-" expression ] ;
methodDecl  = [ "static" ] "method" IDENT params block ;
operatorDecl= "operator" OPSYM params block ;
params      = "(" [ IDENT { "," IDENT } ] ")" ;

ifStmt      = "if" expression block
              { "else" "if" expression block } [ "else" block ] ;
whileStmt   = "while" expression block ;
forStmt     = "for" IDENT "in" expression block ;
returnStmt  = "return" [ expression ] ;
printStmt   = "print" [ expression { "," expression } ] ;
importStmt  = "import" IDENT { "::" IDENT } ;
block       = "{" { statement } "}" ;
exprStmt    = expression ;

expression  = assignment ;
assignment  = ( IDENT | attribute | index ) "<-" assignment | logicOr ;
logicOr     = logicAnd { "or" logicAnd } ;
logicAnd    = equality { "and" equality } ;
equality    = comparison { ( "==" | "!=" ) comparison } ;
comparison  = term { ( "<" | ">" | "<=" | ">=" ) term } ;
term        = factor { ( "+" | "-" ) factor } ;
factor      = unary { ( "*" | "/" | "%" ) unary } ;
unary       = ( "not" | "-" ) unary | manifold ;
manifold    = postfix { ( "<~" | "~>" | "-<" ) postfix } ;
postfix     = primary { "." IDENT | "::" IDENT | "(" args ")" | "[" expr "]" } ;
primary     = NUMBER | STRING | "true" | "false" | "nil" | "self"
            | superCall | IDENT | "(" expression ")" | listLit | mapLit ;
superCall   = "super" "." IDENT "(" args ")" ;
listLit     = "[" [ expression { "," expression } ] "]" ;
mapLit      = "{" [ entry { "," entry } ] "}" ;
entry       = expression ":" expression ;
args        = [ expression { "," expression } ] ;

OPSYM       = "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | ">"
            | "<=" | ">=" | "<~" | "~>" | "-<" ;
```

Semicolons (`;`) are optional separators and may appear between statements.

## Precedence (lowest → highest)

1. `<-` assignment
2. `or`
3. `and`
4. `==` `!=`
5. `<` `>` `<=` `>=`
6. `+` `-`
7. `*` `/` `%`
8. unary `not` `-`
9. manifold `<~` `~>` `-<`
10. postfix `.` `::` `()` `[]`

## Operator → method mapping (overloading)

| Symbol | Method        | Symbol | Method        |
|--------|---------------|--------|---------------|
| `+`    | `__add__`     | `==`   | `__eq__`      |
| `-`    | `__sub__`     | `!=`   | `__ne__`      |
| `*`    | `__mul__`     | `<`    | `__lt__`      |
| `/`    | `__div__`     | `>`    | `__gt__`      |
| `%`    | `__mod__`     | `<=`   | `__le__`      |
| `<~`   | `__lact__`    | `>=`   | `__ge__`      |
| `~>`   | `__ract__`    | `-<`   | `__branch__`  |

When the left operand of a binary operator is a class instance and the class
(or an ancestor) defines the corresponding method, that method is invoked
with the right operand as its single argument.

## Bytecode instruction set

The compiler emits `(opcode, arg)` pairs into a `CodeObject` that also holds a
constant pool. Most `arg`s index into that pool.

| Opcode | Effect |
|--------|--------|
| `LOAD_CONST i`        | push `consts[i]` |
| `LOAD_NAME i`         | push value of variable `consts[i]` |
| `DECLARE_NAME i`      | pop; declare `consts[i]` in current scope |
| `STORE_NAME i`        | assign top-of-stack to existing `consts[i]` (value kept) |
| `LOAD_ATTR i`         | pop obj; push `obj.consts[i]` (field or bound method) |
| `STORE_ATTR i`        | pop value, obj; set attr; push value |
| `LOAD_INDEX`          | pop idx, obj; push `obj[idx]` |
| `STORE_INDEX`         | pop value, idx, obj; set; push value |
| `LOAD_SELF`           | push current `self` |
| `LOAD_SUPER_METHOD i` | push bound super-method `consts[i]` |
| `POP` / `DUP`         | discard / duplicate top |
| `BUILD_LIST n`        | pop `n` items → push list |
| `BUILD_MAP n`         | pop `2n` items → push map |
| `BINARY_OP i`         | pop r, l; push `l <op> r` (`op = consts[i]`) |
| `UNARY_OP i`          | pop v; push `<op> v` |
| `JUMP t`              | jump to `t` |
| `JUMP_IF_FALSE t`     | pop; jump if falsey |
| `JUMP_IF_TRUE t`      | pop; jump if truthy |
| `CALL n`              | pop `n` args + callee; push result |
| `MAKE_FUNCTION i`     | build closure from `CodeObject consts[i]` |
| `BUILD_CLASS i`       | build class from `ClassDescriptor consts[i]` |
| `RETURN`              | return top of stack from frame |
| `PRINT n`             | pop `n` values; print them space-separated |
| `GET_ITER`            | replace top with an iterator |
| `FOR_ITER t`          | push next value, or jump to `t` when exhausted |
| `NOP`                 | no operation |

Inspect any program's bytecode with `./bada dis file.bada`.

## Truthiness

Only `nil` and `false` are falsey. Everything else — including `0`, `""` and
empty collections — is truthy.
