"""
Explainability — LUMEN_MASTER_SPEC_V3 §8 (factors, evidence, lineage checks).

The explainability *structures* are the §8 contract models themselves
(`Factor`, `Evidence`, `Lineage` in `contracts/insight.py`). This module holds
the checks that make three of §8's CI invariants enforceable, and which the
§10 `verified` gate runs ("Passes schema, evidence resolution, P9 guard,
confidence floor"):

  Invariant 3 — every `Evidence.id` resolves to a real record.
  Invariant 4 — no `Factor.label` references a P9 attribute.
  Invariant 5 — `lineage.model_version` exists in `lumen_model_registry`.
  Invariant 6 — `classification` ≥ the highest classification of its evidence.

Evidence resolution follows the §2.1 entity vocabulary ("Backed by" column):

  case          CaseMaster (CaseMasterID)
  person        lumen_person (person_id UUID)
  participant   Accused | Victim | ComplainantDetails (composite —
                id format "accused:<id>" / "victim:<id>" / "complainant:<id>")
  officer       Employee (EmployeeID)
  station       Unit (UnitID)
  jurisdiction  District | State (composite — "district:<id>" / "state:<id>")
  court         Court (CourtID)
  charge        ActSectionAssociation (composite —
                "<CaseMasterID>:<ActID>:<SectionID>")
  process_event ArrestSurrender | ChargesheetDetails (composite —
                "arrest:<id>" / "chargesheet:<id>")
  kb_document   lumen_kb_document (§15 — resolves since Session 13 landed
                the knowledge base tables).

§2.1 declares the composite identities without fixing a string format; the
prefixed forms above are the recorded implementation choice (noted in the
Session 8 report), not a spec-derived fact.

Evidence classification (invariant 6) uses the §4.2 asset register via
`governance/classification.py`. Four canonical tables have NO declared
classification in §4.2 (`ActSectionAssociation`, `ArrestSurrender`,
`ChargesheetDetails`, `inv_arrestsurrenderaccused`) — for evidence backed by
those (charge, process_event) the classification cannot be determined from
the specification and `classification_of_evidence` raises rather than guesses.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.contracts.insight import Evidence, Factor, Insight
from lumen.db.models import canonical as m
from lumen.db.models.identity import LumenPerson
from lumen.db.models.intelligence import LumenModelRegistry
from lumen.governance.classification import (
    CLASSIFICATION_ORDER,
    Classification,
    classification_of,
)
from lumen.intelligence.guards import P9_DENIED_COLUMNS, P9ViolationError


# ── Invariant 3: evidence resolution ───────────────────────────────────────

def _int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_evidence(session: Session, evidence: Evidence) -> bool:
    """True iff `evidence.id` resolves to a real record (§8 invariant 3),
    per the §2.1 backing tables."""
    kind, eid = evidence.entity, evidence.id

    if kind == "case":
        cid = _int(eid)
        return cid is not None and session.get(m.CaseMaster, cid) is not None

    if kind == "person":
        return session.get(LumenPerson, eid) is not None

    if kind == "participant":
        prefix, _, raw = eid.partition(":")
        pid = _int(raw)
        if pid is None:
            return False
        table = {"accused": m.Accused, "victim": m.Victim,
                 "complainant": m.ComplainantDetails}.get(prefix)
        return table is not None and session.get(table, pid) is not None

    if kind == "officer":
        oid = _int(eid)
        return oid is not None and session.get(m.Employee, oid) is not None

    if kind == "station":
        sid = _int(eid)
        return sid is not None and session.get(m.Unit, sid) is not None

    if kind == "jurisdiction":
        prefix, _, raw = eid.partition(":")
        jid = _int(raw)
        if jid is None:
            return False
        table = {"district": m.District, "state": m.State}.get(prefix)
        return table is not None and session.get(table, jid) is not None

    if kind == "court":
        cid = _int(eid)
        return cid is not None and session.get(m.Court, cid) is not None

    if kind == "charge":
        parts = eid.split(":")
        if len(parts) != 3:
            return False
        cid = _int(parts[0])
        if cid is None:
            return False
        return session.get(m.ActSectionAssociation, (cid, parts[1], parts[2])) is not None

    if kind == "process_event":
        prefix, _, raw = eid.partition(":")
        pid = _int(raw)
        if pid is None:
            return False
        table = {"arrest": m.ArrestSurrender, "chargesheet": m.ChargesheetDetails}.get(prefix)
        return table is not None and session.get(table, pid) is not None

    if kind == "kb_document":
        # §15 knowledge base (Session 13): kb evidence resolves against
        # lumen_kb_document — the integration this resolver deferred until
        # that session landed.
        from lumen.db.models.kb import LumenKbDocument
        return session.get(LumenKbDocument, eid) is not None

    return False


def unresolved_evidence(session: Session, insight: Insight) -> list[Evidence]:
    """All evidence chips on `insight` that fail invariant 3."""
    return [e for e in insight.evidence if not resolve_evidence(session, e)]


# ── Invariant 4: no Factor.label references a P9 attribute ────────────────

# The P9 attributes by name: the four denied columns (§3.5's `-- P9` markers,
# held in guards.py) plus P9's own concept words — "Caste, religion, blood
# group, disability status" (§0).
_P9_TERMS: tuple[str, ...] = tuple(
    {column.lower() for _, column in P9_DENIED_COLUMNS}
    | {"caste", "religion", "blood group", "bloodgroup", "disability",
       "physically challenged"}
)


def factor_references_p9(factor: Factor) -> str | None:
    """The offending P9 term if `factor.label` references a protected
    attribute (§8 invariant 4), else None."""
    label = factor.label.lower()
    for term in _P9_TERMS:
        if term in label:
            return term
    return None


def assert_factors_clean(factors: list[Factor]) -> None:
    """Raise `P9ViolationError` (the §4.3 rule 6 guard's own error) if any
    factor label references a P9 attribute."""
    for factor in factors:
        term = factor_references_p9(factor)
        if term is not None:
            raise P9ViolationError(
                f"§8 invariant 4: Factor.label {factor.label!r} references the "
                f"P9-protected attribute {term!r}. Protected attributes are "
                "never analytical inputs (P9, §4.3 rule 6)."
            )


# ── Invariant 5: lineage.model_version exists in lumen_model_registry ─────

def model_version_registered(session: Session, model_version: str) -> bool:
    """True iff a `lumen_model_registry` row carries this version
    (§8 invariant 5: 'lineage.model_version exists in lumen_model_registry')."""
    return (
        session.query(LumenModelRegistry)
        .filter(LumenModelRegistry.version == model_version)
        .first()
        is not None
    )


# ── Invariant 6: classification ≥ highest classification of evidence ──────

# §2.1 backing tables per evidence entity, for §4.2 register lookup. For the
# composite kinds the classification is that of the specific backing table
# addressed by the id prefix.
_SINGLE_TABLE: dict[str, str] = {
    "case": "CaseMaster",
    "person": "lumen_person",
    "officer": "Employee",
    "station": "Unit",
    "court": "Court",
    "kb_document": "lumen_kb_*",
}
_PREFIXED_TABLE: dict[str, dict[str, str]] = {
    "participant": {"accused": "Accused", "victim": "Victim",
                    "complainant": "ComplainantDetails"},
    "jurisdiction": {"district": "District", "state": "State"},
    "process_event": {"arrest": "ArrestSurrender", "chargesheet": "ChargesheetDetails"},
}


def classification_of_evidence(evidence: Evidence) -> Classification:
    """The §4.2 declared classification of the record behind an evidence chip.
    Raises KeyError ("Cannot determine from the specification.") for evidence
    backed by a table with no §4.2 declaration (charge → ActSectionAssociation;
    process_event → ArrestSurrender/ChargesheetDetails)."""
    if evidence.entity in _SINGLE_TABLE:
        return classification_of(_SINGLE_TABLE[evidence.entity])
    if evidence.entity in _PREFIXED_TABLE:
        prefix, _, _rest = evidence.id.partition(":")
        table = _PREFIXED_TABLE[evidence.entity].get(prefix)
        if table is None:
            raise KeyError(
                f"Unknown {evidence.entity} id prefix {prefix!r}; cannot map to "
                "a §2.1 backing table."
            )
        return classification_of(table)
    if evidence.entity == "charge":
        return classification_of("ActSectionAssociation")   # raises — undeclared in §4.2
    raise KeyError(f"Unknown evidence entity {evidence.entity!r}")


def classification_satisfied(insight: Insight) -> bool:
    """§8 invariant 6: `classification` ≥ the highest classification of its
    evidence (ordering per §4.1; inheritance per §4.3 rule 2)."""
    if not insight.evidence:
        return True
    highest = max(
        (classification_of_evidence(e) for e in insight.evidence),
        key=lambda c: CLASSIFICATION_ORDER[c],
    )
    return CLASSIFICATION_ORDER[insight.classification] >= CLASSIFICATION_ORDER[highest]
