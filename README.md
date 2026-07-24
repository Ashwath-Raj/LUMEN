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
uvicorn main:app --reload
```

Or use `start-backend.ps1` from the repo root (Windows/PowerShell).
