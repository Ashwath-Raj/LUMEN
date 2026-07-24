"""
Model registry access — LUMEN_MASTER_SPEC_V3 §3.6, §22.

Read-only catalogue over `lumen_model_registry` (the §3.6 table created in
Session 8, `db/models/intelligence.py`, and WRITTEN by the model producers —
graph projection, the prediction engine, the AI orchestrator). §22 exposes it
"alongside" the service registry.

This module CATALOGUES the table; it does not duplicate the writers. Nothing
here trains, registers, or mutates models — registration stays with each
producer (§8 invariant 5 depends on those writes). List/get only.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.db.models.intelligence import LumenModelRegistry


def list_models(session: Session) -> list[LumenModelRegistry]:
    return (session.query(LumenModelRegistry)
            .order_by(LumenModelRegistry.model_id).all())


def get_model(session: Session, model_id: str) -> LumenModelRegistry | None:
    return session.get(LumenModelRegistry, model_id)


def as_dict(row: LumenModelRegistry) -> dict:
    return {
        "model_id": row.model_id,
        "name": row.name,
        "kind": row.kind,
        "version": row.version,
        "params": row.params,
        "metrics": row.metrics,
        "trained_at": row.trained_at.isoformat() if row.trained_at else None,
        "active": row.active,
    }
