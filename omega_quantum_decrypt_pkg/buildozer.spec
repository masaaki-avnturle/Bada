[app]
# Android build config for Buildozer / python-for-android.
# NOTE: buildozer requires this file to sit in the directory it is run from,
# so it lives at the package root (next to main.py), NOT under packaging/.
# Build:  cd omega_quantum_decrypt_pkg && buildozer -v android debug
# Produces:  bin/omegaqdecrypt-<version>-arm64-v8a-debug.apk

title = omega_quantum_decrypt
package.name = omegaqdecrypt
package.domain = io.github.masaaki_avnturle

# App sources = this directory (holds the Kivy entry point main.py).
source.dir = .
source.include_exts = py
# Keep host-only bits out of the APK.
source.exclude_dirs = tests, packaging, __pycache__, examples
source.exclude_patterns = run_demo.sh, .gitignore, gui_tk.py

version = 0.5.0
requirements = python3,kivy==2.3.1

orientation = portrait
fullscreen = 0

# Target Android 12 (API 31) as requested; min API 24 for broad coverage.
android.api = 31
android.minapi = 24
android.archs = arm64-v8a
android.allow_backup = 1
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
