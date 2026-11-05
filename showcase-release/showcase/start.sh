#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
LUMEN local showcase

Usage:
  ./start.sh [--no-browser] [--reset-demo-data] [--help]

Options:
  --no-browser       Do not open a browser automatically.
  --reset-demo-data  Rebuild the synthetic SQLite dataset from the seed generator.
  --help             Show this help.

Environment:
  PORT=8765                  HTTP port
  LUMEN_HOST=127.0.0.1       Bind address (keep localhost for a safe demo)
  LUMEN_DB=/path/to/file     SQLite database path
  LUMEN_OPEN_BROWSER=0       Disable automatic browser launch
EOF
}

for arg in "$@"; do
  case "$arg" in
    --no-browser) export LUMEN_OPEN_BROWSER=0 ;;
    --reset-demo-data) export LUMEN_RESET_DEMO=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required. Install Python 3.10+ and retry." >&2
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("ERROR: Python 3.10 or newer is required.")
print(f"Using Python {sys.version.split()[0]}")
PY

export LUMEN_DB="${LUMEN_DB:-$HERE/data/lumen_showcase.sqlite3}"
export LUMEN_HOST="${LUMEN_HOST:-127.0.0.1}"
export PORT="${PORT:-8765}"
export LUMEN_OPEN_BROWSER="${LUMEN_OPEN_BROWSER:-1}"
mkdir -p "$(dirname -- "$LUMEN_DB")"

if [[ "${LUMEN_RESET_DEMO:-0}" == "1" ]]; then
  echo "Resetting only the synthetic showcase database at: $LUMEN_DB"
fi

cd "$HERE"
exec python3 server.py
