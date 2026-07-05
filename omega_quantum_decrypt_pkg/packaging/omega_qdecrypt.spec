# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Windows build.
# Build (on Windows):  pyinstaller packaging/omega_qdecrypt.spec
# Produces:  dist/omega_quantum_decrypt.exe  (one-file, windowed)
#
# Paths are resolved relative to this spec file (via SPECPATH) so the build
# works no matter which directory pyinstaller is invoked from.

import os
from kivy_deps import sdl2, glew   # provided by kivy on Windows

block_cipher = None
PKG = os.path.abspath(os.path.join(SPECPATH, '..'))   # the package root (holds main.py)

a = Analysis(
    [os.path.join(PKG, 'main.py')],
    pathex=[PKG],
    binaries=[],
    datas=[(os.path.join(PKG, 'omega_qdecrypt'), 'omega_qdecrypt')],
    hiddenimports=['app_controller'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name='omega_quantum_decrypt',
    debug=False,
    strip=False,
    upx=True,
    console=False,          # windowed GUI app
    onefile=True,
)
