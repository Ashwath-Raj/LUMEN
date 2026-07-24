"""
Canonical display forms — LUMEN_MASTER_SPEC_V3 §2.3.

Fixed strings, used everywhere, defined once here. The spec gives five
worked examples:

    Case          "FIR 104430006202600001 · Murder · Heinous · Under Investigation"
    Person        "Person P-4471 · 4 linked case records · confidence 0.91"
    Officer       "PSI Ramesh (KGID 4429213), Whitefield PS"
    Charge        "IPC 302 — Punishment for murder"
    ProcessEvent  "Arrest · 12 Mar 2026 · Whitefield PS · IO PSI Ramesh"

Each render function below reproduces exactly one of those five forms.
§2.1 names eleven semantic entities in total; the spec gives worked
display forms for only these five (Case, Person, Officer, Charge,
ProcessEvent) — the remaining six (CaseParticipant, Station, Jurisdiction,
CrimeType, CourtWork, Insight) have no canonical string prescribed
anywhere in §2.3 or elsewhere, so no render function is defined for them
here: inventing a format for them would be inventing architecture, which
this session must not do. Cannot determine display forms for entities
outside the five worked examples from the specification.

Some fields the display forms require are not present on the bare
semantic-entity dataclasses in `semantics/entities.py` (e.g. a case's
crime-type/gravity/status *names*, an officer's rank name, a station
name) because those live on separate canonical lookup tables (`CrimeHead`,
`GravityOffence`, `CaseStatusMaster`, `Rank`, `Unit` — §3.5) that a
repository joins in, not fields the entity itself carries. Render
functions therefore take the resolved lookup strings as explicit
parameters rather than performing any lookup themselves — `render.py` only
formats what it is given; it does not query.
"""
from __future__ import annotations

from lumen.semantics.entities import Case, Charge, Officer, Person, ProcessEvent


def render_case(
    case: Case,
    *,
    crime_type_name: str,
    gravity_name: str,
    status_name: str,
) -> str:
    """"FIR 104430006202600001 · Murder · Heinous · Under Investigation" """
    return f"FIR {case.crime_no} · {crime_type_name} · {gravity_name} · {status_name}"


def render_person(person: Person) -> str:
    """"Person P-4471 · 4 linked case records · confidence 0.91" """
    short_id = person.person_id[:6] if len(person.person_id) > 6 else person.person_id
    return (
        f"Person P-{short_id} · {person.case_count} linked case records "
        f"· confidence {person.resolution_confidence:.2f}"
    )


def render_officer(officer: Officer, *, rank_short_name: str, station_name: str) -> str:
    """"PSI Ramesh (KGID 4429213), Whitefield PS" """
    return f"{rank_short_name} {officer.first_name} (KGID {officer.kgid}), {station_name}"


def render_charge(charge: Charge, *, act_short_name: str, section_description_short: str) -> str:
    """"IPC 302 — Punishment for murder" """
    return f"{act_short_name} {charge.section_id} — {section_description_short}"


def render_process_event(
    event: ProcessEvent,
    *,
    station_name: str,
    io_rank_short_name: str,
    io_first_name: str,
) -> str:
    """"Arrest · 12 Mar 2026 · Whitefield PS · IO PSI Ramesh" """
    kind_label = {
        "incident": "Incident",
        "info_received": "Information received",
        "registered": "Registered",
        "arrest": "Arrest",
        "chargesheet": "Chargesheet",
    }[event.kind]
    date_str = event.occurred_at.strftime("%d %b %Y") if event.occurred_at else "date unknown"
    return f"{kind_label} · {date_str} · {station_name} · IO {io_rank_short_name} {io_first_name}"
