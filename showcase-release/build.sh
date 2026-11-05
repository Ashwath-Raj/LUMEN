#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "[1/3] Checking shell scripts..."
for f in start.sh clone-and-start.sh test.sh build.sh showcase/start.sh; do bash -n "$f"; done
echo "[2/3] Checking Python and JavaScript syntax..."
python3 -m py_compile showcase/server.py showcase/tests/test_server.py
if command -v node >/dev/null 2>&1; then node --check showcase/web/app.js; else echo "Node.js not installed; skipped optional JS parser check."; fi
echo "[3/3] Running API tests..."
./test.sh
echo "Build checks passed. Run ./start.sh to launch the local showcase."
