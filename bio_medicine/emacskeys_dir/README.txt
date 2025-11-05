Windows remapper package (窓使いの憂鬱風)

Contents:
 - src/remapper.c                 : main
 - src/emacs_bindings.c/.h        : Emacs-like handlers
 - src/vim_bindings.c/.h          : Vim-like handlers
 - src/keymap.h                   : mode enum
 - targets.txt                     : target process list
 - build-win.sh                    : cross-build (mingw-w64)
 - emacskeys.runner                : linux helper (wine/build)
 - emacskeys.runner.bat            : windows helper
 - Makefile                        : cross-build Makefile
 - directories: bin/, lib/, include/, usr/ (created empty)

Build (Linux cross-compile):
 1) sudo apt install mingw-w64
 2) ./build-win.sh x86_64

Build (Windows):
 1) With MinGW (gcc) in PATH: emacskeys.runner.bat build

Run (Linux):
 ./emacskeys.runner run    # requires wine and remapper.exe

Notes:
 - This is an educational demo. Use responsibly. Some behavior is approximate.
