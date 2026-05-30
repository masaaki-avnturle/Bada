#!/usr/bin/env python3
"""Bada language command-line driver.

Usage:
    bada run   <file.bada>             compile and execute a program
    bada dis   <file.bada>             show the compiled bytecode
    bada compile <file.bada> [-o out]  compile to a .badac bytecode file
    bada exec  <file.badac>            execute pre-compiled bytecode
    bada repl                          interactive read-eval-print loop
    bada version
"""

import sys
import os
import pickle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from badalang.compiler import compile_source           # noqa: E402
from badalang.vm import VM                              # noqa: E402
from badalang.parser import parse                       # noqa: E402
from badalang.objects import bada_repr                  # noqa: E402
from badalang.errors import BadaError                   # noqa: E402

MAGIC = b"BADAC1\n"


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def cmd_run(args):
    if not args:
        die("run: missing source file")
    path = args[0]
    src = read_file(path)
    try:
        code = compile_source(src, path)
        VM().run_main(code)
    except BadaError as e:
        die(str(e))
    return 0


def cmd_dis(args):
    if not args:
        die("dis: missing source file")
    path = args[0]
    src = read_file(path)
    try:
        code = compile_source(src, path)
    except BadaError as e:
        die(str(e))
    print(code.disassemble())
    return 0


def cmd_compile(args):
    if not args:
        die("compile: missing source file")
    path = args[0]
    out = None
    if "-o" in args:
        i = args.index("-o")
        out = args[i + 1]
    if out is None:
        base = os.path.splitext(path)[0]
        out = base + ".badac"
    src = read_file(path)
    try:
        code = compile_source(src, path)
    except BadaError as e:
        die(str(e))
    with open(out, "wb") as f:
        f.write(MAGIC)
        pickle.dump(code, f)
    print(f"compiled -> {out}")
    return 0


def cmd_exec(args):
    if not args:
        die("exec: missing bytecode file")
    path = args[0]
    with open(path, "rb") as f:
        magic = f.read(len(MAGIC))
        if magic != MAGIC:
            die(f"{path} is not a Bada bytecode file")
        code = pickle.load(f)
    try:
        VM().run_main(code)
    except BadaError as e:
        die(str(e))
    return 0


def cmd_repl(args):
    vm = VM()
    print("Bada REPL — type 'exit' or Ctrl-D to quit.")
    from badalang.compiler import Compiler
    from badalang import nodes as N
    while True:
        try:
            line = input("bada> ")
        except EOFError:
            print()
            break
        if line.strip() in ("exit", "quit"):
            break
        if not line.strip():
            continue
        try:
            ast = parse(line, "<repl>")
            # If it's a single expression statement, echo its value.
            comp = Compiler("<repl>")
            stmts = ast.statements
            if len(stmts) == 1 and isinstance(stmts[0], N.ExprStmt):
                comp.expression(stmts[0].expr)
                from badalang import opcodes as O
                comp.emit(O.RETURN)
                result = vm.run(comp.code, vm.global_env)
                if result is not None:
                    print(bada_repr(result))
            else:
                code = comp.compile_program(ast)
                vm.run(code, vm.global_env)
        except BadaError as e:
            print(str(e), file=sys.stderr)
        except Exception as e:  # noqa
            print(f"InternalError: {e}", file=sys.stderr)
    return 0


def cmd_version(args):
    from badalang import __version__
    print(f"Bada {__version__}")
    return 0


def die(msg):
    print(f"bada: {msg}", file=sys.stderr)
    sys.exit(1)


COMMANDS = {
    "run": cmd_run,
    "dis": cmd_dis,
    "compile": cmd_compile,
    "exec": cmd_exec,
    "repl": cmd_repl,
    "version": cmd_version,
}


def main(argv):
    if len(argv) < 2:
        # Convenience: `bada foo.bada` behaves like `bada run foo.bada`.
        print(__doc__)
        return 0
    cmd = argv[1]
    rest = argv[2:]
    if cmd in COMMANDS:
        return COMMANDS[cmd](rest)
    if os.path.exists(cmd):
        return cmd_run([cmd])
    die(f"unknown command {cmd!r} (try: run, dis, compile, exec, repl, version)")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except BrokenPipeError:
        # downstream pipe (e.g. `| head`) closed early — exit quietly
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
