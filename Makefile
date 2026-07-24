# ============================================================================
# LUMEN — developer entry points.
#
# The database schema is created ENTIRELY through Alembic migrations, driven by
# the bootstrap script (api/scripts/init_db.py). You never start the backend to
# create or inspect the schema.
#
#   make init        one-shot: verify PG, create DB if absent, migrate, verify
#   make migrate     alembic upgrade head only (DB must already exist)
#   make revision m="msg"   autogenerate a new migration from the ORM models
#   make downgrade   alembic downgrade -1
#   make backend     run the FastAPI backend (after init)
#   make test        run the backend test suite
#
# Uses the project virtualenv at api/.venv if present, else the PATH python.
# ============================================================================

API_DIR := api
VENV_PY := $(API_DIR)/.venv/Scripts/python.exe
SYS_PY  := python
PY      := $(shell [ -x "$(VENV_PY)" ] && echo "$(VENV_PY)" || echo "$(SYS_PY)")

.DEFAULT_GOAL := help
.PHONY: help init migrate revision downgrade backend eval test

help:
	@echo "LUMEN targets:"
	@echo "  make init       - bootstrap the database (verify, create-if-absent, migrate, verify)"
	@echo "  make migrate    - alembic upgrade head"
	@echo "  make revision m=\"message\" - autogenerate a migration from the ORM models"
	@echo "  make downgrade  - alembic downgrade -1"
	@echo "  make backend    - run the FastAPI backend"
	@echo "  make eval       - run the §17 AI evaluation suite and print a scorecard"
	@echo "  make test       - run the test suite"

# One command: a fresh developer runs `make init` and can inspect all tables in
# DBeaver immediately, without ever starting the backend.
init:
	cd $(API_DIR) && "$(PY)" -m scripts.init_db

migrate:
	cd $(API_DIR) && "$(PY)" -m alembic upgrade head

revision:
	cd $(API_DIR) && "$(PY)" -m alembic revision --autogenerate -m "$(m)"

downgrade:
	cd $(API_DIR) && "$(PY)" -m alembic downgrade -1

backend:
	cd $(API_DIR) && "$(PY)" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# §17.4: runs the golden + adversarial suite in-process and prints a scorecard.
eval:
	cd $(API_DIR) && "$(PY)" -m scripts.eval

test:
	cd $(API_DIR) && "$(PY)" -m pytest -q
