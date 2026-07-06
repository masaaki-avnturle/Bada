# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Windows build.
#
# Builds the Tkinter GUI (gui_tk.py) into a single windowed .exe.  Tkinter is
# part of CPython and needs no OpenGL, so this builds reliably on the headless
# windows-latest runner (Kivy does not -- it aborts without a GL>=2.0 context).
#
# Build (on Windows):  pyinstaller --noconfirm packaging/omega_qdecrypt.spec
# Produces:  dist/omega_quantum_decrypt.exe
#
# Paths resolve relative to this spec file (SPECPATH) so the working directory
# does not matter.

import os
from PyInstaller.utils.hooks import collect_submodules

PKG = os.path.abspath(os.path.join(SPECPATH, '..'))   # the package root

a = Analysis(
    [os.path.join(PKG, 'gui_tk.py')],
    pathex=[PKG],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('omega_qdecrypt') + ['app_controller'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['kivy'],          # the desktop build does not use Kivy
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='omega_quantum_decrypt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,              # windowed GUI (no console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
