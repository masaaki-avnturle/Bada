#!/bin/bash
# SessionStart hook for Claude Code on the web.
#
# Installs the C build toolchain and dev libraries needed to build the
# biofeedback_audio app (and other C tools in this repo):
#   - build-essential / gcc, make
#   - libncurses-dev  (bfa_tui)
#   - libx11-dev      (bfa_gui)
#   - libxft-dev      (bfa_gui Japanese text via Xft/fontconfig)
#   - fonts-ipafont-gothic (Japanese glyphs for the X11 GUI)
#   - libgtk-3-dev    (bfa_gtk)
#   - libasound2-dev  (realtime ALSA playback, optional but auto-detected)
#
# Idempotent and non-interactive. Web-only (skips on local machines).
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive

# Some base images ship broken third-party PPAs that make `apt-get update`
# fail hard. Refresh only the main lists and don't abort the whole hook if a
# stale PPA can't be reached; the packages we need live in the main repos.
sudo apt-get update -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0" \
  || apt-get update -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0" \
  || true

PKGS="build-essential pkg-config libncurses-dev libx11-dev libxft-dev \
fonts-ipafont-gothic libgtk-3-dev libasound2-dev"

# apt-get install is idempotent: already-installed packages are skipped, and
# the container state is cached after the hook so this is fast on resume.
sudo apt-get install -y --no-install-recommends $PKGS \
  || apt-get install -y --no-install-recommends $PKGS

echo "[session-start] toolchain ready:"
gcc --version | head -1 || true
pkg-config --exists alsa     && echo "  ALSA      : $(pkg-config --modversion alsa)"     || echo "  ALSA      : missing"
pkg-config --exists gtk+-3.0 && echo "  GTK+3     : $(pkg-config --modversion gtk+-3.0)" || echo "  GTK+3     : missing"
pkg-config --exists ncursesw && echo "  ncursesw  : $(pkg-config --modversion ncursesw)" || true
pkg-config --exists x11      && echo "  X11       : $(pkg-config --modversion x11)"      || true
pkg-config --exists xft      && echo "  Xft       : $(pkg-config --modversion xft)"      || echo "  Xft       : missing"
