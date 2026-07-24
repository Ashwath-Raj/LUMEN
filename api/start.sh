#!/bin/bash
set -e

# NOTE: schema creation/migration is NOT done here. It is owned by the
# `db-init` bootstrap (scripts/init_db.py, run as its own compose service), so
# the database schema exists and is inspectable without ever starting this
# backend. The backend never creates or migrates schema — it only serves.

echo "Starting Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port "${X_ZOHO_CATALYST_LISTEN_PORT:-9000}"
