#!/usr/bin/env bash
# Install the client-side access-signature hooks into a working copy.
# Usage:  access_signature/hooks/install-hooks.sh [path-to-repo]
set -euo pipefail

HOOK_SRC="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${1:-$(pwd)}"
GIT_DIR="$(git -C "$REPO_DIR" rev-parse --git-dir)"
DEST="$REPO_DIR/$GIT_DIR/hooks"

for h in pre-push post-checkout post-merge; do
  cp "$HOOK_SRC/$h" "$DEST/$h"
  chmod +x "$DEST/$h"
  echo "installed $h -> $DEST/$h"
done
echo "client-side access-signature hooks installed."
echo "For server-side enforcement use hooks/pre-receive.sample on a self-hosted"
echo "server, or the GitHub Action for github.com push checks."
