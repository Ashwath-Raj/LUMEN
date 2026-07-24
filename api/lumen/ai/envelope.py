"""
Prompt envelope — LUMEN_MASTER_SPEC_V3 §16.2 steps 6, 8, 9; §16.3.

Three responsibilities, all fixed by §16:

  * Step 6 — prompt assembly: versioned templates are .md files under
    ai/prompts/, hashed into `lumen_prompt_registry` at startup (§16.3).
    `register_prompts` does the hashing; `assemble` renders the template.
    Template FILENAME convention: "<name>.<version>.md" (e.g.
    "ask_summary.v1.md"). The template text itself is authored — §16.3
    mandates versioned files, not wording.

  * Step 8 — schema validation: `parse_generation` parses the model's
    JSON-only reply into the fixed generation shape; a malformed reply
    raises (the orchestrator gives one retry, then deterministic fallback).

  * Step 9 — evidence verification, "the most important line in this
    document": `verify_cited_ids` DROPS any ID not in the retrieved bundle.
    A hard server-side filter, not a prompt instruction (§16.2). The
    orchestrator applies it to everything the model cited before anything
    reaches an Insight.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy.orm import Session

from lumen.db.models.prompt import LumenPromptRegistry

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


class Generation(BaseModel):
    """The JSON-only generation shape the prompt instructs (§16.2 step 7)."""
    headline: str
    answer: str
    cited_ids: list[str] = []
    abstained: bool = False


# ── §16.3 prompt registry ──────────────────────────────────────────────────

def _templates() -> dict[tuple[str, str], Path]:
    """{(name, version): path} for every ai/prompts/<name>.<version>.md."""
    out: dict[tuple[str, str], Path] = {}
    for path in sorted(PROMPT_DIR.glob("*.md")):
        stem_parts = path.stem.rsplit(".", 1)
        if len(stem_parts) == 2:
            out[(stem_parts[0], stem_parts[1])] = path
    return out


def register_prompts(session: Session, *, now: datetime | None = None) -> int:
    """Hash every versioned prompt file into lumen_prompt_registry (§16.3
    'hashed into lumen_prompt_registry at startup'). Idempotent merge;
    returns the number of registered prompts."""
    now = now or datetime.now(timezone.utc)
    count = 0
    for (name, version), path in _templates().items():
        text = path.read_text(encoding="utf-8")
        session.merge(LumenPromptRegistry(
            prompt_id=f"{name}@{version}", name=name, version=version,
            template_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            created_at=now, active=True))
        count += 1
    session.flush()
    return count


def assemble(name: str, version: str, *, question: str, evidence: str) -> str:
    """Step 6: render the versioned template with the question and the
    evidence bundle."""
    path = _templates().get((name, version))
    if path is None:
        raise KeyError(f"No prompt template {name!r} version {version!r} "
                       f"under {PROMPT_DIR}")
    template = path.read_text(encoding="utf-8")
    return template.replace("{question}", question).replace("{evidence}", evidence)


# ── §16.2 step 8: schema validation ────────────────────────────────────────

def parse_generation(raw: str) -> Generation:
    """Parse the model's JSON-only reply. Raises ValueError on malformed
    output (the orchestrator retries once, then falls back)."""
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        payload = json.loads(raw[start:end])
        return Generation.model_validate(payload)
    except Exception as exc:                    # malformed JSON/shape
        raise ValueError(f"generation is not the required JSON shape: {exc}") from exc


# ── §16.2 step 9: the hard filter ──────────────────────────────────────────

def verify_cited_ids(cited: list[str], bundle_ids: set[str]) -> tuple[list[str], list[str]]:
    """DROP any ID not in the retrieved bundle. Returns (kept, dropped).
    Hard server-side filter — P2. §17.2 tracks the dropped count as a
    model-quality signal."""
    kept = [i for i in cited if i in bundle_ids]
    dropped = [i for i in cited if i not in bundle_ids]
    return kept, dropped
