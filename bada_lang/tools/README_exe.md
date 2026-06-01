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
