#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Ashwath-Raj/LUMEN.git"
BRANCH="lumen-development"
TARGET="${1:-$SCRIPT_DIR/LUMEN-upstream}"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required for clone-and-start." >&2
  exit 1
fi

if [[ -d "$TARGET/.git" ]]; then
  echo "Using existing LUMEN checkout: $TARGET"
else
  if [[ -e "$TARGET" ]]; then
    echo "ERROR: target exists but is not a Git repository: $TARGET" >&2
    exit 1
  fi
  echo "Cloning LUMEN branch '$BRANCH'..."
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TARGET"
fi

mkdir -p "$TARGET/showcase"
cp -a "$SCRIPT_DIR/showcase/." "$TARGET/showcase/"
echo
echo "Showcase files installed at: $TARGET/showcase"
echo "Starting local showcase. This does not modify the upstream Git history."
exec "$TARGET/showcase/start.sh"
