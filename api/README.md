# LUMEN - Karnataka State Police Intelligence Platform

> **Note:** this document describes the backend as it existed before the
> repository was restructured to match `docs/LUMEN_MASTER_SPEC_V3.md` §28.
> Paths below (`app/...`) now live under `lumen/...` (e.g. `app/core/config.py`
> is now `lumen/config.py`, `app/services/repositories/module_service.py` is
> now `lumen/services/module_service.py`); the entrypoint is run as
> `uvicorn main:app` from inside `api/`, not `fastapi dev app/main.py`. See
> `docs/MIGRATION.md` for the authoritative record of what moved where and
> `docs/LUMEN_MASTER_SPEC_V3.md` §16.1/ADR-005 regarding the Gemini-primary
> AI provider described below, which the frozen spec designates a dev-only
> fallback (QuickML is the primary provider going forward). This file is
> kept as a historical description of the pre-migration backend, not a
> current guide.

LUMEN is an advanced, AI-driven backend localized for the Karnataka State Police (KSP). It unifies operations, geospatial tracking, field intelligence, and predictive analytics using a strict, modular architecture designed for high scalability and secure Indian law enforcement workflows, leveraging BNS/IPC standards.

## Backend Architecture

The backend is constructed using **FastAPI** on Python 3.14.
- **Database**: SQLite (Development) / PostgreSQL (Production ready). SQLAlchemy powers the ORM layer, ensuring SQL injection resistance.
- **AI Integration**: The platform features a modular AI abstraction layer (`app/ai`) running Google's `google-genai` SDK.
- **Authentication**: JWT-based stateless authentication with `Access` and `Refresh` token support. Secure Role-Based Access Control (RBAC) restricts endpoints by operator tier.

### Core Directories
- `app/api/routers`: FastAPI endpoints mapped directly to frontend modules.
- `app/ai/`: Central AI layer. Contains provider factory, isolated prompt configurations, strict JSON validation/extraction utilities, and `AIService`.
- `app/core/`: Configuration, logging, exception handling, and security logic.
- `app/db/`: SQLAlchemy ORM definitions and the automated seeder.
- `app/repositories/`: Abstracted domain repositories to isolate database operations from routers.
- `app/services/`: Business logic. Features `ModuleService`, which unites all repositories and the `AIService` into a single, cohesive facade for the routers.

## AI Architecture

LUMEN seamlessly integrates Google Gemini (`gemini-flash-latest`) for real-time intelligence.
- **Fault-Tolerant Provider Factory**: `ACTIVE_AI_PROVIDER` safely delegates requests between `GeminiProvider` and `MockProvider`.
- **Tenacity Resilience**: Network/API failures are intercepted, utilizing exponential backoff logic up to 3 times before failing over.
- **Self-Healing Output Parsing**: If the LLM returns broken JSON, the AI layer catches the `JSONDecodeError`, retries the specific prompt with strict schema enforcement, and successfully degrades to local stubs if validation still fails.
- **Prompt Sanitization**: Common prompt-injection patterns (e.g. `<system>`) are stripped out in the `AIService` prior to querying the provider.

## Authentication Flow

LUMEN utilizes a Dual-Token Bearer structure.
- **Access Tokens**: Short-lived (15 minutes). Used to access all protected routers via standard HTTP Bearer headers.
- **Refresh Tokens**: Long-lived (7 days). Stored securely. Enables headless background rotation.
- **Password Hashing**: `bcrypt` is used via the `passlib` cryptography standard.

## Environment Variables

All critical credentials and configurations are strictly governed by `.env`. **Never hardcode secrets into the source.**

```bash
# Example .env configuration
ENVIRONMENT=development    # 'development' or 'production'
DEBUG=true                 # Enable/disable debug traces
API_PREFIX=/api            # Global router prefix

SECRET_KEY=your_secure_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=sqlite:///./lumen.db  # Or postgresql://user:pass@host/db

# --- Google Gemini AI ---
ACTIVE_AI_PROVIDER=gemini   # 'gemini' or 'mock'
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-flash-latest

CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

## Local Development Setup

1. **Install Dependencies**: `pip install -r requirements.txt` (or manage via your python environment).
2. **Environment File**: Create a `.env` file referencing the structure above.
3. **Run Server**: `fastapi dev app/main.py`
4. **Database Seeding**: The server automatically seeds standard data into `lumen.db` upon its first boot.
5. **View API Specs**: Navigate to `http://localhost:8000/docs` to view Swagger UI.

## Production Deployment Guide

1. **Dependencies**: Ensure the server runs a production-grade ASGI server like `uvicorn` managed by `gunicorn`.
2. **Environment Swap**: Set `DEBUG=false` and `ENVIRONMENT=production`. Provide a strong `SECRET_KEY`.
3. **Database Migration**: Switch `DATABASE_URL` to the production PostgreSQL cluster. The idempotent seeder will safely bypass if data exists, but ideally, you'll manage schema migrations using `Alembic`.
4. **CORS Hardening**: Ensure `CORS_ORIGINS` points strictly to the frontend domains.
5. **Reverse Proxy**: Serve the backend behind an NGINX or Traefik reverse proxy to handle SSL termination.

## API Overview

- `/auth/*`: Login, token refresh, user info, and logout.
- `/dashboard/*`: Fetch global command center metrics and threat alerts.
- `/intelligence/*`: Threat feeds, workbench states, and AI QA against case databases.
- `/investigation/*`: FIR processing, textual NLP extractions, and criminal network graphs.
- `/geospatial/*`: Retrieves tactical overlays and heatmap density grids.
- `/analytics/*`: Deep numerical statistical arrays for charts.
- `/operations/*`: Live field coordination and agent deployment rosters.
- `/administration/*`: Personnel management and global system audits.
