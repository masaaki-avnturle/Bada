#!/usr/bin/env python3
"""Build a standalone executable for the mayu (窓使いの憂鬱) application.

Bundles the Bada VM (the `badalang` package) together with the mayu Bada
program and its libraries into a single self-contained executable using the
standard-library `zipapp` module - no third-party tools required.

    python3 tools/build_exe.py
    ./dist/mayu                 # runs directly (shebang + chmod +x)

The produced `dist/mayu` is a Python zip-application: a real executable file
that needs only a Python 3 interpreter.  To turn it into a dependency-free
native binary, run PyInstaller on the target OS (see tools/README_exe.md) -
on Windows that yields `mayu.exe`.
"""

import os
import sys
import shutil
import zipapp
import stat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # bada_lang/
BUILD = os.path.join(ROOT, "build_exe")
DIST = os.path.join(ROOT, "dist")

# Bada sources to embed (the app + the libraries it imports)
BADA_FILES = {
    "mayu_cli.bada": os.path.join(ROOT, "apps", "mayu_cli.bada"),
    "winreg.bada": os.path.join(ROOT, "lib", "winreg.bada"),
    "mayucfg.bada": os.path.join(ROOT, "lib", "mayucfg.bada"),
}

LAUNCHER = '''\
"""mayu - standalone executable launcher (Bada VM + bundled program)."""
import os
import sys
import tempfile

# Bada sources embedded at build time.
FILES = __BADA_FILES__


def main():
    from badalang.compiler import compile_source
    from badalang.vm import VM
    from badalang.errors import BadaError

    workdir = tempfile.mkdtemp(prefix="mayu_")
    for name, src in FILES.items():
        with open(os.path.join(workdir, name), "w", encoding="utf-8") as f:
            f.write(src)

    main_path = os.path.join(workdir, "mayu_cli.bada")
    with open(main_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        code = compile_source(source, main_path)
        VM().run_main(code, base_dir=workdir)
    except BadaError as e:
        print("mayu: " + str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    # fresh build dir
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)

    # 1. bundle the Bada VM package
    shutil.copytree(os.path.join(ROOT, "badalang"),
                    os.path.join(BUILD, "badalang"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 2. write the launcher with the embedded Bada sources
    files = {name: read(path) for name, path in BADA_FILES.items()}
    launcher = LAUNCHER.replace("__BADA_FILES__", repr(files))
    with open(os.path.join(BUILD, "__main__.py"), "w", encoding="utf-8") as f:
        f.write(launcher)

    # 3. zip it into a single executable
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "mayu")
    zipapp.create_archive(BUILD, target=out,
                          interpreter="/usr/bin/env python3", compressed=True)
    # make it executable
    st = os.stat(out)
    os.chmod(out, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    # also keep a .pyz copy (portable across OSes via `python mayu.pyz`)
    shutil.copy(out, os.path.join(DIST, "mayu.pyz"))

    shutil.rmtree(BUILD)
    size = os.path.getsize(out)
    print("built executable: dist/mayu  (%d bytes)" % size)
    print("                  dist/mayu.pyz")
    print("run:  ./dist/mayu          (Linux/macOS, needs python3)")
    print("      python dist\\\\mayu.pyz (Windows)")


if __name__ == "__main__":
    main()
