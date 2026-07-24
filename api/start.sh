#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port "${X_ZOHO_CATALYST_LISTEN_PORT:-9000}"
