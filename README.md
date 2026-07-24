# LUMEN — AI Crime Intelligence Platform

Karnataka State Police · Catalyst-native. Architecture frozen at v3 — see
`docs/LUMEN_MASTER_SPEC_V3.md` for the single source of truth.

## Repository structure

```
client/      React (Vite) frontend               → Catalyst Web Client Hosting
api/         FastAPI backend (package: lumen)     → Catalyst AppSail
functions/   Catalyst Functions (event handlers)  → Catalyst Functions
data/        Canonical schema, seeds, eval set
docs/        Specification, ADRs, migration record
legacy/      Archived pre-migration code, kept for reference, not imported
             by the live application (see docs/MIGRATION.md)
```

This structure was migrated from a prior `backend/` + `src/` layout to
match the frozen specification. See `docs/MIGRATION.md` for the full
record of what moved, what was archived, and what remains before
implementation proceeds per the build sequence in spec §33.

## Getting started

**Frontend** (`client/`):

```bash
cd client
npm install
npm run dev
```

**Backend** (`api/`):

```bash
cd api
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Or use `start-backend.ps1` from the repo root (Windows/PowerShell).
