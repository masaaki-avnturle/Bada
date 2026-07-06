[app]
# Android build config for Buildozer / python-for-android.
# Build:  cd omega_quantum_decrypt_pkg && buildozer -v android debug
# Produces:  bin/omega_quantum_decrypt-<version>-arm64-v8a-debug.apk

title = omega_quantum_decrypt
package.name = omegaqdecrypt
package.domain = io.github.masaaki_avnturle

# App sources live one level up (the package root that holds main.py).
source.dir = ..
source.include_exts = py,txt,md
source.include_patterns = omega_qdecrypt/*.py, examples/*.txt
# Exclude host-only bits from the APK.
source.exclude_dirs = tests, packaging, __pycache__
source.exclude_patterns = run_demo.sh, .gitignore

version = 0.1.0
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
