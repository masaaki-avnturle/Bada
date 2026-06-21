# vimbada — a vim written in Bada, its C binaries, `bada.vim`, and the Xcode embed

This is the editor side of Bada self-hosting: the **modal vim editor (insert
mode + command mode) implemented in the Bada language**, the supporting
**libraries in Bada**, the same editing primitives compiled to **C executable
binaries** (reserved-word, *class-method* and *receiver* binaries), the
**`bada.vim`** plugin (from `.vimrc`), and a scaffold that **embeds the Bada vim
into Apple's Xcode** IDE.

```
vimbada/
  lib/vimlib.bada     string/buffer helpers, in Bada
  lib/vim.bada        the modal vim (NORMAL/INSERT + : commands), in Bada
  bridge.py           drive the Bada vim from Python (keystroke script -> buffer)
  cbackend_vim.py     emit the C receiver + class-method binaries
  bada.vim            Vim plugin: filetype/syntax/completion + :BadaRun/:BadaVim
  xcode/              embed the Bada vim into Xcode (External Build System)
```

## 1. The vim written in Bada (`lib/vim.bada`)

A real modal editor whose logic lives in Bada. State is an array
`[lines, cy, cx, mode, lastcmd]`; `vim_key(state, key)` processes one keystroke
and `vim_feed(state, keys)` a whole script. It supports

* **NORMAL mode**: `i a h j k l 0 $ x o dd` and `:w :q :wq`,
* **INSERT mode**: literal text, `RET` (split line), `BS` (delete / join), `ESC`.

It relies only on Bada's string operations — `len(s)`, `s[i]` (1-char string),
`+` concatenation — with the helpers in `lib/vimlib.bada` (`substr`,
`str_insert`, `str_delete`, `clamp`). Lines are strings rebuilt on edit.

Bada has no interactive terminal IO, so the editor is driven by a keystroke
script. `bridge.py` runs a script through the Bada vim and returns the buffer:

```python
from vimbada import bridge
bridge.run(["i", "h", "i", "RET", "there", "ESC", ":wq"])
# {'text': 'hi\nthere', 'mode': 'N', 'lastcmd': 'wq'}
bridge.type_text("abc\ndef")          # {'text': 'abc\ndef', ...}
```

(The interactive, curses front-end remains the Python `BadaVim` in `editor/`;
this is the same modal model with its core re-expressed in Bada.)

## 2. The C binaries (`cbackend_vim.py`)

The Bada vim edits a buffer by sending **class-method messages** (insert,
delete, newline, open-line, delete-line, show) to a line buffer. This backend
emits those as **real C executables**, alongside the **reserved-word binaries**
from `../cbackend/gen.py`:

* `bufrt.c` — shared runtime (load / save / edit a line-buffer file),
* **class-method** binaries: `vim_insert vim_delete vim_newline vim_appendline
  vim_deleteline vim_show`,
* a **receiver** binary `bada_vim` that takes a method name and dispatches the
  message to the matching class-method binary (`execv`).

```sh
python3 -m vimbada.cbackend_vim --out generated --build
generated/bin/bada_vim buf.txt vim_insert 0 0 hello
generated/bin/bada_vim buf.txt vim_appendline 0
generated/bin/bada_vim buf.txt vim_insert 1 0 world
generated/bin/bada_vim buf.txt vim_show          # -> hello / world
```

The test suite checks the receiver reproduces exactly what the Bada vim
produces for the equivalent edit script.

## 3. `bada.vim` (from `.vimrc`)

A self-contained Vim plugin packaging the Bada support from `../.vimrc`:
`*.bada` filetype detection, syntax highlighting, reserved-word/buffer
completion, and the commands `:BadaCheck`, `:BadaRun`, `:BadaVim` (run the
Bada-written vim over a keystroke script) and `:BadaCC` (build the C binaries).

```vim
:source /path/to/vimbada/bada.vim     " or drop into ~/.vim/plugin/
:BadaVim i h i ESC :wq                 " runs the vim written in Bada
```

Set `BADA_HOME` to the `bada_silent_vim` directory, or let it be inferred from
the plugin's location.

## 4. Xcode embed (`xcode/`)

`xcode/BadaVim.xcodeproj` is a minimal **External Build System** project; its
build tool is `xcode/bada-vim`, the launcher that

* `bada-vim edit FILE` — opens a `.bada` file in Vim with `bada.vim` loaded,
* `bada-vim build` — builds the C receiver + class-method binaries,
* `bada-vim run KEY...` — runs the Bada-written vim over a keystroke script,
* `bada-vim check FILE` — grammar-checks a `.bada` file.

```sh
open xcode/BadaVim.xcodeproj      # on macOS; Build runs `bada-vim build`
xcode/bada-vim run i H i ESC      # works from any shell too
```

**Honest scope note:** Xcode itself only runs on macOS, so the `.xcodeproj`
here is a checked-in, hand-written *External Build System* project (no Xcode is
invoked to produce it, and it is not exercised in CI). On macOS, opening it and
pressing **Build** runs `bada-vim build`; editing a `.bada` file inside Xcode
uses Xcode's "Open with External Editor" → Vim, which loads `bada.vim`. The
launcher and the build it drives are fully verified on Linux in the test suite;
the IDE wrapper is the thin, platform-specific shell around them.

## Tests
`../tests/test_vimbada.py` — the Bada vim (insert/command mode) via the bridge,
the C receiver/class-method binaries compiling and matching the Bada vim, and
the `bada.vim` plugin loading in headless Vim.
