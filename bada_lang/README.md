# Bada Language — Compiler & Interpreter

An object-oriented, operator-algebra scripting language with a full
**compiler** (source → bytecode) and **interpreter** (a stack-based virtual
machine that executes that bytecode).

Bada is the executable realization of the *Yamaguchi operator-algebra /
TupleSpace* design found elsewhere in this repository (`Bada#.pdf`,
`README.md`, `omega_language/`). It captures the core ideas in a small,
clean, runnable language:

- **Object orientation** — classes, fields, methods, single inheritance
  (written `class Dog <- Animal`), `self` / `super`, and operator
  overloading.
- **TupleSpace / `Omega::DATABASE`** — a *write-once* immutable associative
  store, modelling the "Akashic record" where no memory is ever overwritten.
- **Operator-algebra builtins** — `zeta`, `gamma`, `beta`, the
  non-commutative `pi_op`, and three overloadable *manifold operators*
  `<~`, `~>`, `-<`.

## Pipeline

```
source.bada
   │  Lexer (badalang/lexer.py)        字句解析器
   ▼
 tokens
   │  Parser (badalang/parser.py)      構文解析器  →  AST (badalang/nodes.py)
   ▼
  AST
   │  Compiler (badalang/compiler.py)  → bytecode CodeObject
   ▼
 bytecode  ──(pickle)──►  .badac file
   │  VM (badalang/vm.py)              interpreter / 仮想機械
   ▼
 result
```

## Quick start

```bash
cd bada_lang

# run a program
./bada run examples/02_classes.bada

# show the compiled bytecode (the compiler's output)
./bada dis examples/02_classes.bada

# compile to a standalone bytecode file, then execute it
./bada compile examples/02_classes.bada -o classes.badac
./bada exec classes.badac

# interactive REPL
./bada repl

# run the test suite (40 checks)
python3 tests/run_tests.py
```

(If `./bada` isn't executable in your shell, use `python3 bada.py <cmd>`.)

## Language tour

### Values and variables

```bada
let x <- 3.14          // declare with  <-
x <- x + 1             // reassign
let parts <- split("a,b,c", ",")
let scores <- {"alice": 90, "bob": 75}
print "x =", x, "parts =", parts
```

Types: `int`, `float`, `string`, `bool` (`true`/`false`), `nil`, `list`
(`[1,2,3]`), `map` (`{"k": v}`), plus `class`, instance, function and
`tuplespace`.

### Classes, inheritance, operators

```bada
class Vector {
    field x <- 0
    field y <- 0

    method init(x, y) { self.x <- x  self.y <- y }
    method length() { return sqrt(self.x*self.x + self.y*self.y) }

    operator + (other) {            // overload  v + w
        return Vector.new(self.x + other.x, self.y + other.y)
    }
}

class Vector3 <- Vector {           // inheritance with  <-
    field z <- 0
    method length() {
        let base <- super.length()  // call parent method
        return sqrt(base*base + self.z*self.z)
    }
}
```

Instances are created with `ClassName.new(args)`, which runs the `init`
method. Overloadable operators: `+ - * / % == != < > <= >=` and the manifold
operators `<~ ~> -<`.

### TupleSpace — write-once memory

```bada
let db <- Omega::DATABASE.new("akashic")
db.push("alpha", 1.0)     // bind a key
db["beta"] <- 2.5         // index-assign also writes once
print db.get("alpha"), db["beta"], db.keys()
// db.push("alpha", 9)    // -> ImmutableError: key is write-once
```

### Operator-algebra / manifold features

| Construct        | Meaning (illustrative numeric semantics)                |
|------------------|----------------------------------------------------------|
| `zeta(s)`        | Riemann ζ(s) via truncated Dirichlet series (real s > 1) |
| `gamma(x)`       | Γ(x)                                                     |
| `beta(p, q)`     | B(p,q) = Γ(p)Γ(q)/Γ(p+q)                                 |
| `pi_op(chi, x)`  | π(χ,x) = π·χ·log x  (non-commutative left action)        |
| `a <~ b`         | left action, default `pi_op(a, b)`                       |
| `a ~> b`         | right action, default `a · e^(−b·log b)` (γ-deprivation) |
| `a -< b`         | branch / manifold integral, default `beta(a, b)`         |

A class may override `<~`, `~>`, `-<` (as `operator <~ (x) { ... }`) to give
its instances custom operator-algebra behaviour.

> **Note on operator naming.** The design documents write the three manifold
> operators as `<-`, `-<`, `>-`. Because executable Bada uses `<-` for
> assignment (as in `sample.omega`), the left/right-action operators are
> written `<~` and `~>` in code, while `-<` is kept as-is.

## Files

| File | Role |
|------|------|
| `badalang/lexer.py`    | tokenizer (字句解析器) |
| `badalang/parser.py`   | recursive-descent parser (構文解析器) → AST |
| `badalang/nodes.py`    | AST node definitions |
| `badalang/compiler.py` | AST → bytecode |
| `badalang/opcodes.py`  | bytecode instruction set |
| `badalang/objects.py`  | runtime object model (class, instance, TupleSpace, …) |
| `badalang/builtins.py` | builtin functions, math, operator-algebra, `Omega` |
| `badalang/vm.py`       | the bytecode interpreter (virtual machine) |
| `bada.py` / `bada`     | command-line driver (`run`/`dis`/`compile`/`exec`/`repl`) |
| `examples/`            | sample programs |
| `tests/run_tests.py`   | test suite |

See [`GRAMMAR.md`](GRAMMAR.md) for the full grammar and the bytecode
instruction set.
