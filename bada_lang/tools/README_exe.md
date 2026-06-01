# Bada executables

Two standalone executables are built from the standard library only (no
third-party tools), each bundling the Bada VM so they need only a Python 3
interpreter:

| build | output | what it is |
|-------|--------|------------|
| `python3 tools/build_all.py` | `dist/bada` | the **whole toolchain** — VM + every library + every app, in one file |
| `python3 tools/build_exe.py` | `dist/mayu` | just the **mayu** (窓使いの憂鬱) registry remapper |

## dist/bada — the whole Bada toolchain in one file

```bash
./dist/bada list              # list every bundled application
./dist/bada run quantum_os    # run an app (writes its .html into the cwd)
./dist/bada run xray_scanner  # writes chest_xray.pgm / .ppm / .gif
./dist/bada mayu              # the mayu CLI
./dist/bada repl              # interactive Bada REPL
./dist/bada version
```

Apps that build a GUI write their `.html`; imaging apps write `.pgm/.ppm/.gif`;
all 20 applications are available from this one executable.

---

# mayu — executable build (窓使いの憂鬱)

`mayu` (Madotsukai no Yuuutsu) is shipped as a **standalone executable file**
that bundles the Bada VM together with the mayu Bada program and its libraries.
It compiles a key-binding DSL into the Windows registry (Windows 10 / 11),
prints the registry tree, exports a `.reg` file, and offers an interactive
prompt.

## Build it

```bash
cd bada_lang
python3 tools/build_exe.py
```

This produces (using only the Python standard library — no third-party tools):

```
dist/mayu       a self-contained executable (zipapp + shebang, chmod +x)
dist/mayu.pyz   the same archive, portable to any OS with Python
```

## Run it

```bash
./dist/mayu                 # Linux / macOS - runs directly
python dist/mayu.pyz        # Windows / anywhere with Python 3
```

It needs only a Python 3 interpreter; **no Bada source files or separate
`bada` launcher** — the VM and the program are inside the file.

Inside the prompt:

```
mayu> reg                show the Windows registry tree
mayu> export out.reg     write a .reg file (import it with regedit /s out.reg)
mayu> find C-k           search every scope for a key chord
mayu> os win10           recompile for Windows 10 (or win11)
mayu> scopes             list the registered scopes
mayu> quit
```

## A dependency-free native binary

`dist/mayu` is a Python zip-application, so it requires Python on the target
machine.  To produce a single native binary that needs **no** Python:

- **Linux / macOS** (run on that OS):
  ```bash
  pip install pyinstaller
  pyinstaller --onefile --name mayu --collect-submodules badalang \
      tools/build_exe.py    # or a small launcher that runs apps/mayu_cli.bada
  # -> dist/mayu  (native ELF / Mach-O)
  ```
- **Windows** (run on Windows, yields `mayu.exe`):
  ```bat
  pip install pyinstaller
  pyinstaller --onefile --name mayu --collect-submodules badalang launcher.py
  rem -> dist\mayu.exe
  ```

PyInstaller is not preinstalled in the Bada cloud sandbox and its download is
blocked there, so the native-binary step is done on a machine with PyInstaller;
the portable `dist/mayu` / `dist/mayu.pyz` is built here with the stdlib.
