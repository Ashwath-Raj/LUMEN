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

Only the REGISTRY is exposed here — the sibling `/system/health` and
`/system/metrics` observability surfaces (§24/§25) are later sessions and are
not added. Read-only; the registry catalogues existing artifacts, never
mutates them from the request path.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.registry import models as model_registry
from lumen.registry import prompts as prompt_registry
from lumen.registry import services as service_registry

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
