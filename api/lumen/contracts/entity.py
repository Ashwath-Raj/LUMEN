"""
EntityContract — LUMEN_MASTER_SPEC_V3 §7.

§7's contract table lists `EntityContract` (v1, produced by the semantic
layer, consumed by API/AI/graph/UI) alongside seven other contracts
(`InsightContract`, `GraphContract`, `PredictionContract`,
`RecommendationContract`, `EventContract`, `EvidenceContract`,
`QualityContract`). `EntityContract` is the only one of the eight whose
producer — the semantic layer — is in Session 2's scope; the other seven
are produced by subsystems (intelligence engine, graph module, prediction
engine, decision support, event bus, retriever, quality engine) that
Session 2 explicitly must not implement, and the spec gives no
field-level shape for any of the eight anywhere outside this one summary
row. Implementing the other seven now would mean inventing their fields
wholesale, which the specification does not authorise.

The specification also gives no field-level shape for `EntityContract`
itself beyond this table row. What §7's Rules section does fix for every
contract, generically:

    1. Contracts are additive within a major version.
    2. Every payload carries `contract_version`.
    3. A breaking change means a new major version, both served in
       parallel, with the old marked deprecated (§29.4).
    4. Contracts live in `contracts/` as Pydantic models and are the
       ONLY shapes crossing a module boundary.
    5. Frontend types are generated from these models — never hand-written.

`EntityContract` below is therefore built to exactly that generic shape —
a versioned envelope around one of the eleven closed-vocabulary semantic
entities (§2.1) — and nothing more is invented. `kind` is constrained to
the same eleven names as §2.1's entity vocabulary so the contract cannot
carry an entity the vocabulary doesn't recognise.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


EntityKind = Literal[
    "case",
    "person",
    "case_participant",
    "officer",
    "station",
    "jurisdiction",
    "court",
    "charge",
    "crime_type",
    "process_event",
    "insight",
]


class EntityContract(BaseModel):
    """Versioned envelope around one semantic entity (§2.1), crossing a
    module boundary per §7 rule 4. `data` holds whichever plain dict shape
    corresponds to `kind` (one of the eleven dataclasses in
    `semantics/entities.py`) — a discriminated union of eleven full
    submodels is not built here, since the spec does not specify field-
    level contracts for entities beyond what `semantics/entities.py`
    already carries, and duplicating that shape as Pydantic submodels
    without a spec-given justification would be inventing structure the
    document does not ask for.
    """

    contract_version: str = "v1"
    kind: EntityKind
    id: str
    data: dict
