# LUMEN — AI Crime Intelligence Platform (LUMEN-Linked-Urban-Mapping-Entities-Network)

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

> **Two auth modes, selected automatically by build mode**
> (`client/app/src/api/authService.js`):
>
> - **`npm run dev`** — a DEV build never touches Catalyst auth.
>   `/__catalyst/*` doesn't exist under Vite (only `/api/*` is proxied,
>   see `vite.config.js`), so "Continue to Sign-In" establishes a local
>   **mock session** instead (`VITE_USE_MOCKS` unset or not `'false'`,
>   the default) and lands on `/dashboard`. The `init.js` 404 in the dev
>   console is expected noise: the CDN Web SDK loads but is deliberately
>   ignored in DEV builds, because without `/__catalyst/sdk/init.js` it
>   is an uninitialized husk that cannot authenticate.
>
> - **Real Catalyst login** — production builds (what `catalyst serve`
>   and deployed hosting serve from `client/dist`) redirect to the real
>   hosted login page:
>
>   ```bash
>   cd client && npm run build      # produces client/dist, which catalyst.json points at
>   cd .. && catalyst serve
>   ```
>
>   Verified locally: `/__catalyst/auth/login` (200, real Zoho Sign-In
>   page) and `/__catalyst/sdk/init.js` (200) both served by the emulator.

**Backend** (`api/`):

```bash
cd api
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
```

### Database initialization

The database schema is created **entirely through Alembic migrations** — the
FastAPI app never calls `Base.metadata.create_all()`. A single bootstrap
command brings a fresh PostgreSQL instance to the full, migrated schema
**without starting the backend**, so every table is immediately inspectable in
DBeaver / psql.

1. Set `DATABASE_URL` in the root `.env` (copy from `.env.example`). The
   backend fails fast if it is missing — no credentials are invented.
2. Run the bootstrap:

   ```bash
   make init            # from the repo root
   # equivalently, from api/:
   python -m scripts.init_db
   ```

`init_db.py` performs, in order (fail-fast on any error):

1. **Verify PostgreSQL connectivity** (connects to the server's `postgres`
   maintenance database).
2. **Create the target database if it does not exist.**
3. **Run `alembic upgrade head`** — the single canonical baseline migration
   (`0001_canonical_baseline`) creates all 32 LUMEN tables (27 canonical +
   `inv_arrestsurrenderaccused` + the five `lumen_` platform tables) in
   foreign-key order, plus indexes.
4. **Verify every expected table exists**, printing the full table list.

After it finishes, open DBeaver, point it at the same `DATABASE_URL`, and you
will see all 32 tables (plus Alembic's `alembic_version`) — the backend has not
been started. Related migration commands:

```bash
make migrate     # alembic upgrade head only (DB already exists)
make revision m="describe change"   # autogenerate a new migration from the ORM models
make downgrade   # alembic downgrade -1
```

### Run the backend

```bash
cd api
uvicorn main:app --reload      # or: make backend
```

Or use `start-backend.ps1` from the repo root (Windows/PowerShell).

### Docker Compose

The same initialization runs in Docker via a dedicated one-shot `db-init`
service that migrates the schema and exits; the `backend` service waits for it
to complete successfully and never creates schema itself.

```bash
docker compose up db-init        # provision + migrate the schema only, then exit
docker compose up --build        # full stack: postgres -> db-init -> backend -> frontend
```

After `docker compose up db-init` you can inspect all tables in DBeaver
(connect to the `postgres` service / published port) before the backend starts.
