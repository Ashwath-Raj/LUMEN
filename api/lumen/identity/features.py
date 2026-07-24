"""
Per-Accused resolution signals — LUMEN_MASTER_SPEC_V3 §6.1.

§6.1 states the available signals, "thin, and to be stated as such":
`AccusedName`, `AgeYear` (with case date ⇒ approximate birth year), `GenderID`,
arrest districts and stations from `ArrestSurrender`, the investigating
officer, and the act-section signature of the cases.

This module reads the canonical (§3.5) tables once and builds an
`AccusedSignals` record per `Accused` row — the raw material the §6.3 feature
vector scores. It computes nothing beyond assembling §6.1's stated signals; it
does not normalise names (that is `normalize.py`) or score pairs (`scoring.py`).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.identity.normalize import normalise_name, phonetic_key


@dataclass
class AccusedSignals:
    accused_master_id: int
    case_master_id: int | None
    raw_name: str
    normalised: str
    phonetic: str
    gender_id: int | None
    implied_birth_year: int | None       # §6.1 "AgeYear + case date ⇒ approx birth year"
    arrest_districts: set[int] = field(default_factory=set)   # §6.1 ArrestSurrender
    arrest_stations: set[int] = field(default_factory=set)    # §6.1 ArrestSurrender
    act_section_signature: frozenset = frozenset()            # §6.1 act-section signature


def _implied_birth_year(age_year: int | None, case_registered) -> int | None:
    """§6.1: AgeYear with the case date implies an approximate birth year."""
    if age_year is None or case_registered is None:
        return None
    return case_registered.year - int(age_year)


def build_signals(session: Session) -> dict[int, AccusedSignals]:
    """Assemble the §6.1 signal bundle for every Accused row, keyed by
    AccusedMasterID."""
    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}

    # Act-section signature per case (§6.1 "act-section signature of the cases").
    signature: dict[int, set] = {}
    for a in session.query(m.ActSectionAssociation).all():
        signature.setdefault(a.CaseMasterID, set()).add((a.ActID, a.SectionID))

    signals: dict[int, AccusedSignals] = {}
    for acc in session.query(m.Accused).all():
        case = cases.get(acc.CaseMasterID)
        registered = case.CrimeRegisteredDate if case is not None else None
        norm = normalise_name(acc.AccusedName)
        signals[acc.AccusedMasterID] = AccusedSignals(
            accused_master_id=acc.AccusedMasterID,
            case_master_id=acc.CaseMasterID,
            raw_name=acc.AccusedName or "",
            normalised=norm,
            phonetic=phonetic_key(norm),
            gender_id=acc.GenderID,
            implied_birth_year=_implied_birth_year(acc.AgeYear, registered),
            act_section_signature=frozenset(signature.get(acc.CaseMasterID, set())),
        )

    # Arrest districts / stations per Accused (§6.1 ArrestSurrender).
    for ar in session.query(m.ArrestSurrender).all():
        sig = signals.get(ar.AccusedMasterID)
        if sig is None:
            continue
        if ar.ArrestSurrenderDistrictId is not None:
            sig.arrest_districts.add(ar.ArrestSurrenderDistrictId)
        if ar.PoliceStationID is not None:
            sig.arrest_stations.add(ar.PoliceStationID)

    return signals
