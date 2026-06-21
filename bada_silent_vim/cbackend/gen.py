"""C backend: emit one C executable per Bada method-command.

For every reserved word, builtin and operator-command (the manifest is produced
BY Bada, see ``bootstrap/commands.bada``) this generates a standalone C program
``cmd_<name>.c`` plus a tiny runtime and a Makefile, so the whole set compiles
to real executables — Bada's reserved words as executable files.
"""

from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                  # bada_silent_vim
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from bootstrap import command_manifest          # noqa: E402

RUNTIME_H = """\
#ifndef BADA_RT_H
#define BADA_RT_H
#include <stdio.h>
#include <stdlib.h>
int ba_atoi(const char *s);
#endif
"""

RUNTIME_C = """\
#include "runtime.h"
int ba_atoi(const char *s) { return s ? atoi(s) : 0; }
"""

# echo helper used by print/say/append
_ECHO = ('  for (int i = 1; i < argc; i++) {\n'
         '    if (i > 1) printf("%s", sep);\n'
         '    printf("%s", argv[i]);\n'
         '  }\n  printf("\\n");\n')

# informational bodies for control-flow / structural reserved words
_INFO = {
    "if": "branch object: -<",
    "else": "merge object: >-",
    "while": "transition object: ->",
    "repeat": "count loop: repeat",
    "def": "function definition: def",
    "return": "return value: return",
    "push": "tuplespace push",
    "pop": "tuplespace pop",
    "Omega": "namespace: Omega::DATABASE",
    "true": "true",
    "false": "false",
    "nil": "nil",
}

# two-integer operator commands
_BINOP = {"add": "+", "sub": "-", "mul": "*", "mod": "%"}
_CMPOP = {"eq": "==", "lt": "<", "gt": ">"}


def _body(name: str) -> str:
    if name in ("print", "say"):
        return '  const char *sep = " ";\n' + _ECHO
    if name == "append":
        return '  const char *sep = "";\n' + _ECHO
    if name in _INFO:
        return f'  printf("{_INFO[name]}\\n");\n'
    if name == "len":
        return '  printf("%d\\n", argc - 1);\n'
    if name == "str":
        return '  printf("%s\\n", argc > 1 ? argv[1] : "");\n'
    if name == "abs":
        return '  printf("%d\\n", abs(ba_atoi(argv[1])));\n'
    if name == "pow2":
        return '  printf("%ld\\n", 1L << ba_atoi(argv[1]));\n'
    if name == "idiv" or name == "div":
        return ('  int b = ba_atoi(argv[2]);\n'
                '  if (b == 0) { fprintf(stderr, "division by zero\\n");'
                ' return 1; }\n'
                '  printf("%d\\n", ba_atoi(argv[1]) / b);\n')
    if name == "imod":
        return ('  int b = ba_atoi(argv[2]);\n'
                '  if (b == 0) { fprintf(stderr, "division by zero\\n");'
                ' return 1; }\n'
                '  printf("%d\\n", ba_atoi(argv[1]) % b);\n')
    if name in _BINOP:
        return (f'  printf("%d\\n", ba_atoi(argv[1]) {_BINOP[name]} '
                f'ba_atoi(argv[2]));\n')
    if name in _CMPOP:
        return (f'  printf("%s\\n", ba_atoi(argv[1]) {_CMPOP[name]} '
                f'ba_atoi(argv[2]) ? "true" : "false");\n')
    # fallback: identify the command
    return f'  printf("bada command: {name}\\n");\n'


def _cmd_source(name: str) -> str:
    return (f"/* cmd_{name}.c -- Bada method command: {name} */\n"
            '#include "runtime.h"\n'
            "int main(int argc, char **argv) {\n"
            "  (void)argc; (void)argv;\n"
            f"{_body(name)}"
            "  return 0;\n}\n")


def _makefile(names: list[str]) -> str:
    bins = " ".join(f"bin/{n}" for n in names)
    return (
        "CC ?= cc\n"
        "CFLAGS ?= -O2 -Wall\n"
        f"BINS = {bins}\n\n"
        "all: $(BINS)\n\n"
        "bin/%: cmd_%.c runtime.c runtime.h\n"
        "\t@mkdir -p bin\n"
        "\t$(CC) $(CFLAGS) -o $@ $< runtime.c\n\n"
        "clean:\n"
        "\trm -rf bin\n")


def generate(out_dir: str, manifest: list[str] | None = None) -> list[str]:
    manifest = manifest if manifest is not None else command_manifest()
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "runtime.h"), "w") as f:
        f.write(RUNTIME_H)
    with open(os.path.join(out_dir, "runtime.c"), "w") as f:
        f.write(RUNTIME_C)
    for name in manifest:
        with open(os.path.join(out_dir, f"cmd_{name}.c"), "w") as f:
            f.write(_cmd_source(name))
    with open(os.path.join(out_dir, "Makefile"), "w") as f:
        f.write(_makefile(manifest))
    return manifest


def build(out_dir: str) -> list[str]:
    subprocess.run(["make", "-s"], cwd=out_dir, check=True,
                   capture_output=True, text=True)
    bindir = os.path.join(out_dir, "bin")
    return sorted(os.listdir(bindir)) if os.path.isdir(bindir) else []


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        prog="bada-cbackend",
        description="Generate C executables for Bada method commands.")
    p.add_argument("--out", default="generated/cbackend")
    p.add_argument("--build", action="store_true", help="compile with make")
    args = p.parse_args(argv)
    manifest = generate(args.out)
    print(f"generated {len(manifest)} command sources in {args.out}")
    if args.build:
        bins = build(args.out)
        print(f"built {len(bins)} executables in {args.out}/bin")


if __name__ == "__main__":
    main()
