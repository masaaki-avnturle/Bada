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
- **Reviser (リバイザ)** — a grammar/syntax rewriting facility: rules in a
  `reviser { ... }` block rewrite the source before the lexer, so you can add
  custom keywords and brand-new operators. Applied rules live in an immutable
  `Reviser` tuplespace.
- **Garbage collection (ガベージコレクション)** — a tracing mark-and-sweep
  collector over the Bada object graph, with finalizers (`__finalize__`),
  manual `gc()` and automatic collection.
- **Exception handling** — `try` / `catch (e)` / `finally` and `throw`.
- **File I/O** — `read_file`, `write_file`, `read_lines`, plus a streaming
  `open(path, mode)` handle.
- **Libraries & imports** — `import name` loads `name.bada` from a search path
  and binds a namespace; supports `import a::b`, `import "file.bada"` and
  `import x as y`.

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

### Reviser — rewriting the grammar

```bada
reviser {
    word "関数" => "fun"      // custom keyword
    word "表示" => "print"
    op   "←"   => "<-"        // brand-new operator symbol
}

関数 greet(n) { 表示 "hi", n }
greet("world")
```

Rules run **before** the lexer, so they reshape the surface syntax itself.
String literals and comments are never rewritten. The applied rules are
exposed as an immutable `Reviser` tuplespace.

### Garbage collection

```bada
class Node {
    field id
    method init(id) { self.id <- id }
    method __finalize__() { print "collected", self.id }   // optional finalizer
}

Node.new(1)                 // unreachable
let keep <- Node.new(2)     // reachable
print gc_collect()          // -> reclaims Node 1, runs its finalizer
print gc_stats()            // {heap, enabled, threshold, collections, ...}
```

Other GC builtins: `gc()`, `gc_heap()`, `gc_enable()`, `gc_disable()`,
`gc_threshold(n)`. Collection is also triggered automatically once
allocations pass the threshold (checked at safe points between instructions).

### Exceptions

```bada
try {
    throw {"code": 400, "reason": "bad input"}
} catch (e) {
    print "caught", e["code"], e["reason"]
} finally {
    print "always runs"
}
```

`throw` raises any value. `catch` binds it; a built-in runtime error is caught
as a map `{"type": ..., "message": ...}`. (Note: a `return` inside a `try`
body bypasses its `finally` — a documented limitation.)

### File I/O

```bada
write_file("/tmp/x.txt", "hello\n")
append_file("/tmp/x.txt", "world\n")
print read_file("/tmp/x.txt")
for line in read_lines("/tmp/x.txt") { print "-", line }

let f <- open("/tmp/x.txt", "a")   // modes: "r" "w" "a"
f.write("more\n")
f.close()
```

Also: `file_exists(path)`, `delete_file(path)`, `list_dir(path)`.

### Libraries & imports

```bada
import mathx                 // loads mathx.bada, binds namespace `mathx`
import collections
import mathx as M            // rename
import Omega::DATABASE as DB // also works for built-in namespaces

print mathx.gcd(48, 36)
let s <- collections.Stack.new()
```

Modules are searched in: the importing file's directory, `./lib`, every path
in the `BADA_PATH` environment variable, and the bundled standard library
(`bada_lang/lib/`). A module's top-level `let`/`fun`/`class` become the members
of the imported namespace. Modules are executed once and cached.

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
| `badalang/objects.py`  | runtime object model (class, instance, TupleSpace, FileHandle, …) |
| `badalang/builtins.py` | builtin functions, math, operator-algebra, file I/O, `Omega` |
| `badalang/reviser.py`  | the Reviser — source/grammar rewriting |
| `badalang/gc.py`       | the mark-and-sweep garbage collector |
| `badalang/vm.py`       | the bytecode interpreter (VM): exceptions, imports, GC roots |
| `bada.py` / `bada`     | command-line driver (`run`/`dis`/`compile`/`exec`/`repl`) |
| `lib/`                 | bundled standard library (`mathx`, `collections`) |
| `examples/`            | sample programs (01–11) |
| `tests/run_tests.py`   | test suite (63 checks) |

See [`GRAMMAR.md`](GRAMMAR.md) for the full grammar and the bytecode
instruction set.
