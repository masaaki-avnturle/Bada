# bada_silent_vim — Operate the Bada language by silent talk

This package turns the ideas in the uploaded reports into one runnable system:

| Report | Idea realised here |
|:--|:--|
| **Bada1.pdf** — TupleSpace / `Omega::DATABASE`, operators `<- -< >- >> =>`, virtual machine | a working **Bada compiler + VM interpreter** (`bada/`) |
| **a23d7ab9** — brain interface: speech → 7-level resonance scale + lip-movement signal → text | **silent-talk recognition from lip images** (`silenttalk/`) |
| **omegascript_vim_*.txt** — Vim command/insert modes driven by an external keyboard | a **modal Bada editor** (`editor/`) |
| (integration) | drive the Bada editor entirely by silent talk (`app/`) |

Everything is **pure Python 3 (stdlib only)** — no third-party packages, no
camera, no audio. The silent-talk stream is recovered from real **PGM image
files**, so the full pipeline round-trips through disk.

```
lip-movement images ──▶ SilentTalkDecoder ──▶ tokens ──▶ BadaVim ──▶ Bada compiler+VM
   (silenttalk/)         7-band scale +                  (editor/)      (bada/)
                         viseme stream
```

## The four pieces

### 1. Bada language — compiler + interpreter (`bada/`)
`source → tokenize → parse → compile (bytecode) → BadaVM`. A real stack
machine. The five manifold operators from the report carry runtime meaning:

| op | report meaning | runtime |
|:--|:--|:--|
| `<-` | non-commutative left action | bind a name (assignment) |
| `-<` | manifold integral / spawn | form the pair `[a, b]` |
| `>-` | quantum right action / emit | combine (numbers add, sequences concat) |
| `>>` | stream forward | push `a` onto sequence `b`, log the flow |
| `=>` | map / transform | map `b` over the elements of `a` |

Plus `Omega::DATABASE[space] { push(x) pop() }` (the Akashic store),
`print`/`say`, `if/else`, `while`, `repeat`, arrays and arithmetic.

**Functions, arrays & libraries.** Bada is now expressive enough to write real
libraries in Bada itself:

```
def fib(n) {                 // functions + recursion
  if n < 2 { return n }
  return fib(n - 1) + fib(n - 2)
}
xs <- [10, 20, 30]           // arrays: index read/write, len, append
xs[1] <- 99
append(xs, fib(10))          // -> [10, 99, 30, 55]
```

Builtins: `len`, `append`, `idiv`, `imod`, `abs`, `pow2`, `str`. Source files
compose via `#include path` directives (`bada.load_program` / `run_program`).
A full worked example is the **Jones polynomial implemented in Bada** at
`../bada_webos/apps/lib/{laurent,jones}.bada` (Laurent-polynomial algebra +
the Kauffman-bracket state sum), verified against a reference implementation.

**Instruction-oriented ("directive object") dialect.** Control flow can be
written as directive objects instead of keywords:

| directive object | meaning | classic |
|:--|:--|:--|
| `<-` | assignment object | `=` |
| `<->` | comparison object | `==` |
| `-<` | branch object | `if` |
| `>-` | merge object | `else` |
| `->` | transition object | `while` |

```
-< x * y <-> 42 {          // if x*y == 42
  say "branch-merge works"
} >- {                     // else
  say "no"
}
-> n > 0 { n <- n - 1 }    // while n > 0
```
(`-<` / `>-` keep their expression meanings — manifold spawn / emit — within a
line; a pipe operator that *begins a line* is a directive.) Both dialects run.

**The reviser** rewrites classic Bada into this dialect, preserving comments,
strings and layout, and provably semantics-preserving (same bytecode):
```bash
python3 -m bada.reviser FILE.bada            # print revised
python3 -m bada.reviser --write FILE.bada    # rewrite in place
python3 -m bada.reviser --check FILE.bada    # verify equivalence
```
All of `../bada_webos/apps/**/*.bada` are written in this dialect via the
reviser.

**Editor tooling — grammar check, completion, parsers.** The `bada` package and
the `badatools` package provide IDE-style tooling:

* **grammar checker** — `bada.lint(src)` returns `Diagnostic(line, col, ...)`;
  `bada.is_valid(src)`. (Terminal: `check FILE.bada`.)
* **reserved words** — `bada.RESERVED`, `bada.BUILTIN_FUNCS`, `bada.DIRECTIVES`,
  `is_reserved/is_builtin`.
* **word + functional-word completion** — `bada.Completer`:
  `complete_functional(prefix)` (機能語: keywords+builtins) and
  `complete_words(src, prefix)` (buffer symbols: def/var names). The vim and
  emacs editors gain `.lint()` and `.complete()`.
* **Emacs and vim parsers** — `badatools.VimParser` / `EmacsParser` turn modal
  keystrokes / chords into one normalized command stream.
* **silent-talk + keyboard parser** — `badatools.UnifiedInputParser` parses
  *either* silent-talk visemes *or* keyboard keys into the same commands, and
  recognises **passphrases (合言葉)** via `badatools.PassphraseParser`
  (e.g. silently spelling `AI UO` → `UNLOCK`, `OA OA` → `RUN-SECRET`).

```python
from badatools import UnifiedInputParser
u = UnifiedInputParser()
u.from_silent_words(["AI", "EA", "UO", "OA"])  # -> insert, "say ", normal, run
u.from_keyboard(["i", "ESC", "!"], "vim")        # same command shape
```

### 2. Silent-talk recognition from images (`silenttalk/`)
Each frame is a grayscale PGM where the mouth is a dark ellipse.
`lipfeatures` recovers mouth **aperture** and **spread** and classifies a
**viseme** (`A I U O E`, `C`=rest). `scale` reconstructs the **7-level
resonance scale** (`do…si`) from the same frame. The two streams resonate:
consecutive equal visemes collapse (CTC-style), rests segment utterances, and
each collapsed viseme-word is looked up in `data/silenttalk_lexicon.json` to
yield an editor command or a dictated text token. `synth` can *draw* the lip
frames for any word, so the pipeline is verifiable end-to-end.

### 3. Modal Bada editor (`editor/`)
A vim-like editor: NORMAL / INSERT modes, `h j k l` motion, `i` insert,
`o` open line, `x` delete, `:w` `:q` `:wq`, and `!` to **run** the buffer
through the Bada VM with output shown inline. The core is headless and
scriptable; a `curses` front-end is included for interactive use.

### 4. Silent-Vim integration (`app/`)
`SilentVimSession` decodes silent-talk frames into tokens and feeds them to
the editor — in NORMAL mode a token is a command, in INSERT mode it is
dictated Bada source — then runs the result.

## Usage

```bash
cd bada_silent_vim

# Bada language
python3 cli.py run      examples/hello.bada     # interpret
python3 cli.py compile  examples/hello.bada     # show bytecode

# Silent talk
python3 cli.py synth  AI EI IA OU IE --out generated/frames   # draw lip frames
python3 cli.py decode generated/frames                        # frames -> tokens

# Operate Bada by silent talk (headless, reads images from disk)
python3 cli.py silent-edit examples/frames/hello_program --run

# Full end-to-end demo: a Bada program dictated entirely by silent talk
python3 cli.py demo

# Interactive editor (needs a terminal)
python3 cli.py edit examples/hello.bada
```

### `demo` output
Silent talk dictates, character by character, the program:

```
print [42]
say "hello"
```

then runs it on the BadaVM, printing `[42]` and `hello`.

## Silent-talk vocabulary
`data/silenttalk_lexicon.json` maps collapsed viseme-words to meanings.

| viseme-word | NORMAL mode | viseme-word | INSERT mode dictation |
|:--|:--|:--|:--|
| `AI` | INSERT | `EA` | `say ` |
| `UO` | ESCAPE | `EI` | `print ` |
| `AE` | SAVE   | `OE` | `hello` |
| `UI` | QUIT   | `IA` / `IE` | `[` / `]` |
| `OA` | RUN    | `OU` | `42` |
| `IO`/`UA`/`OI`/`EU` | UP/DOWN/LEFT/RIGHT | `EO` | ` <- ` |
| `AO` | NEWLINE | `UE` | `"` |
| `IU` | DELETE | `AU` | `x` |

## Tests
```bash
python3 -m unittest discover -s tests -v      # 27 tests
# or:
make test
```
