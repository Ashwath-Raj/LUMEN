"""
System registry surface — LUMEN_MASTER_SPEC_V3 §22, §29.1.

§22: `lumen_service_registry` is "Exposed at /api/v1/system/registry alongside
model and prompt registries." §29.1 lists `/registry` among the ops/judge
surfaces. This router serves the read-only registry view — all three
registries (service, model, prompt) in one response.

Endpoint path note (disclosed): the spec writes `/api/v1/system/registry`, but
this app mounts every router under `settings.API_PREFIX` which is `/api` (not
`/api/v1`); `v1` is the spec's notation, tracked as `settings.API_VERSION`.
Mounted here as `/system/registry` under the `/api` prefix, matching every
existing router — the concrete path is `/api/system/registry`.

This router hosts the read-only `/system/*` surfaces as their sessions land:
`/system/registry` (§22, Session 17), `/system/health` (§24.2, Session 18),
and `/system/metrics` (§25, Session 20). All are read-only; they catalogue or
aggregate existing artifacts, never mutating anything from the request path.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.registry import models as model_registry
from lumen.registry import prompts as prompt_registry
from lumen.registry import services as service_registry
from lumen.resilience import degradation
from lumen.observability import metrics as obs_metrics

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/registry")
def get_registry(db: Session = Depends(get_db)) -> dict:
    """The service registry alongside the model and prompt registries (§22)."""
    services = [service_registry.as_dict(r) for r in service_registry.list_services(db)]
    models = [model_registry.as_dict(r) for r in model_registry.list_models(db)]
    prompts = [prompt_registry.as_dict(r) for r in prompt_registry.list_prompts(db)]
    return {
        "services": {"total": len(services), "items": services},
        "models": {"total": len(models), "items": models},
        "prompts": {"total": len(prompts), "items": prompts},
    }


@router.get("/health")
def get_health() -> dict:
    """§24.2: the current degradation level + per-dependency state. In this
    environment the external Catalyst dependencies have no live probe, so
    every dependency reports "unknown" and the level resolves to L0 (absence
    of a probe is not evidence of failure — §24.3 rule 5's no-fabrication
    principle applied to health itself). A deployment injects real probes.
    §25's rich metrics are served separately at /system/metrics."""
    return degradation.health_report(probes={})


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> dict:
    """§25: the observability metrics surface (the judge-facing screen).
    Six metrics are aggregated deterministically from persisted tables; the
    four requiring runtime instrumentation (route latency, cache hit rate,
    precompute/graph timings, LLM token counts) are reported "not available"
    — never fabricated (§24.3 rule 5)."""
    return obs_metrics.system_metrics(db)


@router.get("/eval")
def get_eval(run_id: str | None = None, db: Session = Depends(get_db)) -> dict:
    """§29.1: the AI evaluation scorecard (judge-facing). Reads the
    lumen_ai_eval rows the §17 eval runner wrote — for the given run_id, or
    the latest run present. Aggregation is the Session-20 observability
    `eval_scorecard` (consumed, not duplicated)."""
    return obs_metrics.eval_scorecard(db, run_id=run_id)
