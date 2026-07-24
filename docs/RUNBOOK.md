# LUMEN v3 — Runbook

Operational runbook for LUMEN. Content is drawn from LUMEN_MASTER_SPEC_V3 §27
(deployment mechanics), §23 (resource manager), §24 (failure strategy), and the
implemented tooling (Makefile, Alembic migrations, precompute pipeline). It
records how the platform is initialised, run, scheduled, and how it behaves when
a dependency fails. It introduces no new behaviour.

---

## 1. Local development

### 1.1 Database initialisation

The schema is created **entirely through Alembic migrations**; the app never
calls `Base.metadata.create_all()`. Configuration comes from the single
canonical root `.env` (copy from `.env.example`); `DATABASE_URL` is required and
the app fails fast if it is missing.

```bash
make init        # verify PostgreSQL, create the DB if absent, alembic upgrade head, verify tables
make migrate     # alembic upgrade head only
make revision m="message"   # autogenerate a migration from the ORM models
make downgrade   # alembic downgrade -1
```

Migrations `0001`–`0011` build the canonical baseline and the `lumen_` overlay
tables (identity, insight, graph, prediction, event, KB, prompt registry, AI
eval, policy/audit, service registry, feature store).

### 1.2 Run the backend and tests

```bash
make backend     # uvicorn main:app --host 0.0.0.0 --port 8000 --reload
make test        # the pytest suite
make eval        # the §17 AI evaluation suite — prints a scorecard
```

### 1.3 Precompute pipeline

The precompute pipeline (`jobs/precompute.py`, ADR-009) runs the batch stages
off the request path, in data-dependency order:

```
resolution (§6) → projection + metrics (§14) → quality (§5)
  → predictions: hotspots, anomalies, risk, outcome (§13) → features (§12)
```

Stages are **idempotent and checkpointed** (§23, §24.3 rule 4): a partial run
resumes rather than restarts. In deployment it is scheduled on **Catalyst Cron**
(§26.1 #20); locally it is a plain callable.

---

## 2. Deployment mechanics (§27)

- `catalyst.json` at the project root configures the whole project directory,
  including the `client` and `functions` sources; AppSail configuration is added
  there when the service is initialised.
- Initialising an AppSail service creates `app-config.json` in the app's source
  directory — the only AppSail-specific file there — holding the startup
  command, environment variables and memory. Edit it before deploying.
- Bind to the platform-provided port via `X_ZOHO_CATALYST_LISTEN_PORT`; port
  9000 is the default, and if the port is not set in code it must match the
  startup command.

```
# api/app-config.json startup command
uvicorn main:app --host 0.0.0.0 --port ${X_ZOHO_CATALYST_LISTEN_PORT}
```
```python
# main.py
port = int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", 9000))
```

- **Write permissions are restricted in the working directory at runtime** —
  anything written during execution goes to the OS temp directory. This affects
  `MPLCONFIGDIR`, joblib, embedding caches, and any artefact written at import
  time. Load model artefacts read-only from Stratus or the bundle.
- Managed runtimes cover specific Java, Node.js and Python versions; a custom
  OCI image is the alternative and must be built for **linux/amd64**.
- Ensure deployable build files are present in the directory you deploy from.

### 2.1 DATABASE_URL switch (§26.2)

A `DATABASE_URL` switch runs **PostgreSQL locally and Data Store deployed**,
behind one repository interface. Both paths pass the same repository test suite.
Verify decimal handling for `latitude`/`longitude` before seeding; seed via bulk
import, not row-by-row.

---

## 3. Resource management (§23)

| Concern | Mechanism |
|---|---|
| Request priority | Interactive reads > AI generation > batch. Batch jobs never run in the request path |
| Scheduling | Catalyst Cron; heavy jobs staggered, never concurrent with the demo window |
| Caching | Catalyst Cache, documented TTL per payload: overview 60 s, hotspots 5 min, ego graphs 15 min, district risk 1 h, AI answers 15 min |
| Rate limiting | API Gateway throttling; `/ai/ask` limited per user per minute |
| Batch queue | Precompute stages idempotent and checkpointed; a partial run resumes |
| Budget | Token budget per AI request; recorded per call; a daily ceiling degrades to the deterministic fallback |
| Degradation ladder | Full → cached → precomputed-only → deterministic → read-only (§24.2) |

The cache TTLs are implemented in `services/cache.py`; the swappable local
backend runs when Catalyst Cache is unavailable.

---

## 4. Failure strategy (§24)

### 4.1 Dependency failure matrix (§24.1)

| Dependency | Failure mode | Detection | Response | User sees |
|---|---|---|---|---|
| Data Store | Unavailable / slow | Health probe, timeout 3 s | Serve cached payloads; read-only mode | "Serving cached data from HH:MM" |
| Catalyst Cache | Unavailable | Timeout 200 ms | Bypass to store | Nothing (slower) |
| QuickML LLM | Unavailable / timeout | Timeout 15 s, circuit breaker at 3 failures/60 s | Deterministic fallback (§16.4) | "AI narrative unavailable — showing evidence-based summary" |
| QuickML RAG | Unavailable | Timeout | Retrieval falls back to Data Store full-text | Limitation line added to the insight |
| Graph backend | Unavailable | Health probe | Serve last projection from `lumen_graph_edge` / NoSQL snapshot | "Network as of HH:MM" |
| Signals | Delayed | Lag metric | Precompute cron catches up; insights marked stale | Staleness timestamp on every card |
| Zia AutoML | Unavailable | Timeout | Local scikit-learn model | `lineage.method` records the fallback |
| Stratus | Unavailable | Timeout | Evidence list renders metadata without thumbnails | "Attachment temporarily unavailable" |
| Map tiles | Unavailable | Tile error | Choropleth renders on cached GeoJSON without basemap | Basemap absent, data intact |

### 4.2 Degradation ladder (§24.2)

```
L0 FULL          all services healthy
L1 CACHED        live queries fail → cached payloads, staleness shown
L2 PRECOMPUTED   cache cold → precomputed tables only; no ad-hoc filtering
L3 DETERMINISTIC LLM down → template insights from evidence
L4 READ-ONLY     store degraded → last snapshot, writes rejected with a clear message
```

The current level is exposed at `/system/health` and rendered as a status pill
in the app shell. Implemented in `resilience/degradation.py`.

### 4.3 Rules (§24.3)

1. Every outbound call has a timeout. No unbounded waits.
2. Circuit breakers on QuickML and the graph backend: 3 failures in 60 s opens
   for 120 s, then half-open (`resilience/breaker.py`).
3. Retries only on idempotent reads: 2 attempts, exponential backoff with
   jitter. Never retry generation blindly.
4. Precompute is idempotent and checkpointed.
5. **Never fabricate to fill a gap.** Missing data renders as "not available",
   never as zero, never as an interpolated value.
6. Every degradation emits an event and is audited.

### 4.4 Degraded-path check

To demonstrate L3: disable the QuickML provider. `/ai/ask` returns a
template-assembled insight marked `method: "deterministic_fallback"`, and
`/system/health` reports the degraded level (§16.4, §24.2, §34 step 11).

---

## 5. Observability surfaces (§25)

The `/system/*` ops surfaces (all read-only):

- `GET /system/health` — per-dependency state + degradation level (§24.2).
- `GET /system/metrics` — insight counts by kind/lifecycle, policy denials, AI
  fallback rate and latency, quality score trend, AI eval scorecard. Metrics
  requiring runtime instrumentation not persisted locally report "not
  available" (never fabricated).
- `GET /system/registry` — the service, model, and prompt registries (§22).
- `GET /system/eval` — the AI evaluation scorecard (§17).
- `GET /audit` — Auditor role only (§21, §29.1).

---

## 6. Related documents

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture as built.
- [`CATALYST_MAP.md`](CATALYST_MAP.md) — Catalyst service map and P6 register.
- [`GOVERNANCE.md`](GOVERNANCE.md) — classification, P9, trust.
- [`ADR/`](ADR/README.md) — architecture decision records.
