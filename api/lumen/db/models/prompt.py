"""
Prompt registry table — LUMEN_MASTER_SPEC_V3 §3.6 (Session 14, §16.3).

    lumen_prompt_registry(prompt_id PK, name, version, template_hash,
                          created_at, active BOOLEAN)

§16.3: "Prompts are versioned .md files under ai/prompts/, hashed into
lumen_prompt_registry at startup. Every AI insight records prompt_version.
Changing a prompt without bumping the version is a defect."

Only the TABLE lands here (the pattern Sessions 8/10 set for
lumen_model_registry); the §21 registry *module* (`registry/prompts.py`)
remains a Session 22 placeholder. Hashing/registration lives in
`ai/envelope.py` (prompt assembly's home).
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, String

from lumen.db.session import Base


class LumenPromptRegistry(Base):
    __tablename__ = "lumen_prompt_registry"

    prompt_id = Column(String(80), primary_key=True)     # "<name>@<version>"
    name = Column(String(80))
    version = Column(String(20))
    template_hash = Column(String(64))                   # sha256 of the .md file
    created_at = Column(DateTime)
    active = Column(Boolean)
