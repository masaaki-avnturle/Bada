#!/usr/bin/env python3
"""Build ONE standalone executable for the whole Bada toolchain.

Bundles the Bada VM (the `badalang` package) together with EVERY library
(`lib/*.bada`) and EVERY application (`apps/*.bada`) into a single
self-contained executable using the standard-library `zipapp` module.

    python3 tools/build_all.py
    ./dist/bada list                 # list all bundled apps
    ./dist/bada run quantum_os       # run an app (writes its .html into cwd)
    ./dist/bada mayu                 # the mayu CLI (registry remapper)
    ./dist/bada repl                 # interactive Bada REPL

The produced `dist/bada` is the entire Bada language + all apps in one file;
it needs only a Python 3 interpreter (the VM and every program are inside it).
"""

import os
import shutil
import zipapp
import stat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # bada_lang/
BUILD = os.path.join(ROOT, "build_all")
DIST = os.path.join(ROOT, "dist")


LAUNCHER = '''\
"""bada - the whole Bada toolchain as one executable (VM + libs + apps)."""
import os
import sys
import tempfile

FILES = __BADA_FILES__   # {relpath: source}


def materialise():
    work = tempfile.mkdtemp(prefix="bada_")
    for rel, src in FILES.items():
        path = os.path.join(work, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return work


def list_apps():
    return sorted(os.path.splitext(os.path.basename(k))[0]
                  for k in FILES if k.startswith("apps/"))


def usage():
    print("bada - Bada language toolchain (one executable)")
    print("usage:")
    print("  bada list                list every bundled application")
    print("  bada run <app|file>      run an app (writes its .html into cwd)")
    print("  bada mayu                run the mayu CLI (registry key remapper)")
    print("  bada repl                interactive Bada REPL")
    print("  bada version")


def main(argv):
    if len(argv) < 2 or argv[1] in ("help", "-h", "--help"):
        usage(); return 0
    cmd = argv[1]

    if cmd == "version":
        from badalang import __version__
        print("Bada " + __version__ + " (bundled executable)")
        return 0
    if cmd == "list":
        for a in list_apps():
            print("  " + a)
        return 0

    work = materialise()
    libdir = os.path.join(work, "lib")
    os.environ["BADA_PATH"] = libdir
    from badalang.compiler import compile_source
    from badalang.vm import VM
    from badalang.errors import BadaError

    def run_file(path):
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        try:
            code = compile_source(src, path)
            VM().run_main(code, base_dir=work)   # base_dir/lib holds the libs
        except BadaError as e:
            print("bada: " + str(e), file=sys.stderr); sys.exit(1)

    if cmd == "mayu":
        run_file(os.path.join(work, "apps", "mayu_cli.bada")); return 0
    if cmd == "repl":
        vm = VM(); vm.base_dir = work; os.environ["BADA_PATH"] = libdir
        print("Bada REPL - Ctrl-D to quit.")
        from badalang.parser import parse
        from badalang.compiler import Compiler
        from badalang import nodes as N, opcodes as O
        from badalang.objects import bada_repr
        while True:
            try:
                line = input("bada> ")
            except EOFError:
                print(); break
            if not line.strip():
                continue
            try:
                ast = parse(line, "<repl>")
                comp = Compiler("<repl>")
                if len(ast.statements) == 1 and isinstance(ast.statements[0], N.ExprStmt):
                    comp.expression(ast.statements[0].expr); comp.emit(O.RETURN)
                    r = vm.run(comp.code, vm.global_env)
                    if r is not None:
                        print(bada_repr(r))
                else:
                    vm.run(comp.compile_program(ast), vm.global_env)
            except BadaError as e:
                print(str(e), file=sys.stderr)
        return 0
    if cmd == "run":
        if len(argv) < 3:
            print("bada run: missing app/file", file=sys.stderr); return 1
        target = argv[2]
        cand = target
        if not cand.endswith(".bada"):
            cand = os.path.join(work, "apps", target + ".bada")
        if not os.path.isfile(cand):
            print("bada: no such app: " + target, file=sys.stderr)
            print("try: bada list", file=sys.stderr); return 1
        run_file(cand); return 0

    usage(); return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)

    # 1. the Bada VM package
    shutil.copytree(os.path.join(ROOT, "badalang"),
                    os.path.join(BUILD, "badalang"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 2. gather every lib and app
    files = {}
    for sub in ("lib", "apps"):
        d = os.path.join(ROOT, sub)
        for nm in sorted(os.listdir(d)):
            if nm.endswith(".bada"):
                files[sub + "/" + nm] = read(os.path.join(d, nm))

    launcher = LAUNCHER.replace("__BADA_FILES__", repr(files))
    with open(os.path.join(BUILD, "__main__.py"), "w", encoding="utf-8") as f:
        f.write(launcher)

    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "bada")
    zipapp.create_archive(BUILD, target=out,
                          interpreter="/usr/bin/env python3", compressed=True)
    st = os.stat(out)
    os.chmod(out, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    shutil.copy(out, os.path.join(DIST, "bada.pyz"))
    shutil.rmtree(BUILD)

    print("built: dist/bada  (%d bytes, %d libs + apps bundled)"
          % (os.path.getsize(out), len(files)))
    print("       dist/bada.pyz")
    print("run:   ./dist/bada list")


if __name__ == "__main__":
    main()
