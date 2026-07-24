"""
Service registry table — LUMEN_MASTER_SPEC_V3 §3.6, §22.

    lumen_service_registry(service_id PK, name, capability, version, endpoint,
                           depends_on JSON, health_state, last_check)

§22: "records every internal capability: name, capability, version, endpoint,
dependencies, health state, last check." Eight columns, verbatim.

The OTHER two registry tables §22 exposes "alongside" — `lumen_model_registry`
(§3.6, created Session 8 in db/models/intelligence.py) and
`lumen_prompt_registry` (§3.6, created Session 14 in db/models/prompt.py) —
already exist and are NOT re-created here; the registry modules read them.

`health_state` / `last_check`: §22 lists them as columns but defines no
health-PROBING mechanism (that is §24 resilience — a later session). Seed rows
carry `health_state="unknown"` and `last_check=NULL`; live probing is deferred.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, JSON, String

from lumen.db.session import Base


class LumenServiceRegistry(Base):
    __tablename__ = "lumen_service_registry"

    service_id = Column(String(60), primary_key=True)
    name = Column(String(60))
    capability = Column(String(120))
    version = Column(String(20))
    endpoint = Column(String(200))
    depends_on = Column(JSON)            # [service name, ...] (§22 "Depends on")
    health_state = Column(String(20))    # "unknown" until §24 probing (later)
    last_check = Column(DateTime)
