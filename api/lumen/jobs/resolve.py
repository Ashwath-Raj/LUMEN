"""
Entity resolution batch job — LUMEN_MASTER_SPEC_V3 §6.2 (the `persist` step).

Runs the §6.2 pipeline (`lumen.identity.pipeline.resolve`) and writes its
result to the three §3.6 identity tables:

  - `lumen_person`      — one row per resolved (inferred) person, carrying
                          resolution confidence always (P10 / §3.4).
  - `lumen_person_link` — one row per (person, Accused) membership, with the
                          per-link confidence and `match_features` evidence
                          (§6.2 "with per-link confidence + match_features";
                          §6.4 "see why"). Auto-linked members are `state =
                          "linked"`; surfaced 0.65–0.85 candidate pairs are
                          persisted as `state = "candidate"` so the UI can
                          render them separately and never in centrality
                          (§6.4).

The job is re-runnable: it clears the person/link tables first (never any
canonical or other `lumen_` table), so a second run reflects current data
rather than appending duplicates — the same idempotent shape `jobs/quality.py`
uses. `lumen_person_dispute` is written by the surface (a human action, §6.4),
so it is NOT cleared here.

`person_id` (§3.6 UUID) is generated deterministically (UUID5 over the sorted
member Accused ids) so re-running the job on unchanged data yields identical
person ids — consistent with the platform's determinism discipline (§32) and
testable, without adding a random seed dependency.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.db.models.identity import LumenPerson, LumenPersonLink
from lumen.identity.pipeline import (
    LINK_STATE_CANDIDATE,
    LINK_STATE_LINKED,
    ResolutionResult,
    resolve,
)
from lumen.identity.scoring import METHOD_VERSION

logger = logging.getLogger("lumen")

# Fixed namespace so person_id is a deterministic function of the member set.
_PERSON_NS = uuid.UUID("6c1e7b2a-0000-4000-8000-000000000006")


def _person_id_for(accused_ids: list[int]) -> str:
    key = ",".join(str(a) for a in sorted(accused_ids))
    return str(uuid.uuid5(_PERSON_NS, key))


def run_resolution(session: Session, *, now: datetime | None = None) -> dict:
    """Resolve identities and persist them. Returns a small summary (counts)
    for logging / the batch caller."""
    now = now or datetime.now(timezone.utc)

    # Clear prior run (identity person/link tables only — never canonical,
    # never disputes which are human-authored).
    session.query(LumenPersonLink).delete()
    session.query(LumenPerson).delete()
    session.flush()

    result: ResolutionResult = resolve(session)

    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}
    units = {u.UnitID: u.DistrictID for u in session.query(m.Unit).all()}

    persons = 0
    links = 0
    for cluster in result.clusters:
        pid = _person_id_for(cluster.accused_ids)
        first_seen, last_seen, districts = _span(cluster.accused_ids, result, cases, units)
        session.add(
            LumenPerson(
                person_id=pid,
                canonical_name=_canonical_name(cluster.accused_ids, result),
                first_seen=first_seen,
                last_seen=last_seen,
                case_count=_case_count(cluster.accused_ids, result),
                district_count=len(districts),
                resolution_confidence=cluster.confidence,
                method_version=METHOD_VERSION,
            )
        )
        persons += 1
        for aid in cluster.accused_ids:
            session.add(
                LumenPersonLink(
                    person_id=pid,
                    accused_master_id=aid,
                    confidence=cluster.confidence,
                    match_features=cluster.member_features.get(aid, {}),
                    state=LINK_STATE_LINKED,
                )
            )
            links += 1

    # Candidate band (0.65–0.85): surfaced, never auto-merged (§6.2/§6.4).
    # Persisted as two candidate links against a candidate-person id so the
    # surface can render the pair with its evidence and keep it out of
    # centrality. The candidate person carries the pair confidence.
    candidate_persons = 0
    for pair in result.candidate_pairs:
        pid = _person_id_for([pair.a_id, pair.b_id])
        if session.get(LumenPerson, pid) is not None:
            continue   # never collide a candidate id with a resolved person
        first_seen, last_seen, districts = _span([pair.a_id, pair.b_id], result, cases, units)
        session.add(
            LumenPerson(
                person_id=pid,
                canonical_name=_canonical_name([pair.a_id, pair.b_id], result),
                first_seen=first_seen,
                last_seen=last_seen,
                case_count=_case_count([pair.a_id, pair.b_id], result),
                district_count=len(districts),
                resolution_confidence=pair.confidence,
                method_version=METHOD_VERSION,
            )
        )
        candidate_persons += 1
        for aid in (pair.a_id, pair.b_id):
            session.add(
                LumenPersonLink(
                    person_id=pid,
                    accused_master_id=aid,
                    confidence=pair.confidence,
                    match_features=pair.features,
                    state=LINK_STATE_CANDIDATE,
                )
            )
            links += 1

    session.commit()
    summary = {
        "persons": persons,
        "candidate_persons": candidate_persons,
        "links": links,
        "method_version": METHOD_VERSION,
    }
    logger.info("§6 entity resolution complete: %s", summary)
    return summary


def _case_count(accused_ids, result) -> int:
    return len({result.signals[a].case_master_id for a in accused_ids
                if result.signals[a].case_master_id is not None})


def _canonical_name(accused_ids: list[int], result: ResolutionResult) -> str:
    """Representative display name: the most frequent raw name among members
    (ties broken lexicographically for determinism)."""
    counts: dict[str, int] = {}
    for aid in accused_ids:
        name = result.signals[aid].raw_name
        if name:
            counts[name] = counts.get(name, 0) + 1
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _span(accused_ids, result, cases, units):
    """first_seen / last_seen (from case registration dates) and the set of
    districts the person's cases span."""
    dates = []
    districts: set[int] = set()
    for aid in accused_ids:
        cid = result.signals[aid].case_master_id
        case = cases.get(cid) if cid is not None else None
        if case is None:
            continue
        if case.CrimeRegisteredDate is not None:
            d = case.CrimeRegisteredDate
            dates.append(datetime(d.year, d.month, d.day))
        did = units.get(case.PoliceStationID)
        if did is not None:
            districts.add(did)
    first_seen = min(dates) if dates else None
    last_seen = max(dates) if dates else None
    return first_seen, last_seen, districts
