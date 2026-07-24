"""
Prompt registry access — LUMEN_MASTER_SPEC_V3 §3.6, §16.3, §22.

Read-only catalogue over `lumen_prompt_registry` (the §3.6 table created in
Session 14, `db/models/prompt.py`, and WRITTEN at prompt-assembly time by
`ai/envelope.register_prompts` — "prompts hashed into lumen_prompt_registry",
§16.3). §22 exposes it "alongside" the service registry.

This module CATALOGUES the table; the hashing/registration stays in
`ai/envelope.py` (§16.3's home). List/get only — no re-hashing here.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.db.models.prompt import LumenPromptRegistry


def list_prompts(session: Session) -> list[LumenPromptRegistry]:
    return (session.query(LumenPromptRegistry)
            .order_by(LumenPromptRegistry.prompt_id).all())


def get_prompt(session: Session, prompt_id: str) -> LumenPromptRegistry | None:
    return session.get(LumenPromptRegistry, prompt_id)


def as_dict(row: LumenPromptRegistry) -> dict:
    return {
        "prompt_id": row.prompt_id,
        "name": row.name,
        "version": row.version,
        "template_hash": row.template_hash,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "active": row.active,
    }
