"""
Entity vocabulary — LUMEN_MASTER_SPEC_V3 §2.1.

Eleven semantic entities. This list is closed (§2.1: "This list is closed.").
Nothing above `db/repositories/` may reference a table or column name;
everything speaks this vocabulary instead. Repositories translate; nothing
else does (§2, the rule stated at the top of the section).

Each class below is a plain dataclass carrying the fields implied by the
entity's row in the §2.1 table plus the columns of its backing canonical
table(s) (§3.5), reshaped under semantic names rather than table names.

Two entities — `Person` and `Insight` — are backed by `lumen_person` and
`lumen_insight` (§3.6), which are LUMEN-owned platform tables that belong
to entity resolution (§6, Session 7) and the intelligence engine (§8-§11,
Session 8), not to Session 2's canonical schema (§3). Per the Session 2
build contract ("Do NOT implement Entity Resolution / Insight Engine..."),
those two tables are not created here. `Person` and `Insight` are still
declared below, since the entity vocabulary itself is closed and named in
full by §2.1 — but their dataclasses carry only the fields the spec gives
textually (§2.1's Identity column, §3.6's column list for `lumen_person`
and `lumen_insight`), and no repository queries a real table for them yet
(see `db/repositories/`). Instantiating them today requires a caller to
already hold resolved data; nothing in Session 2 produces that data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


@dataclass(frozen=True)
class Case:
    """The spine. Always returned as an aggregate, never a bare row.
    Backed by `CaseMaster` + children (§3.5). Identity: `CaseMasterID`."""

    case_master_id: int
    crime_no: str
    case_no: str | None
    crime_registered_date: date | None
    police_person_id: int | None
    police_station_id: int | None
    case_category_id: int | None
    gravity_offence_id: int | None
    crime_major_head_id: int | None
    crime_minor_head_id: int | None
    case_status_id: int | None
    court_id: int | None
    incident_from_date: datetime | None
    incident_to_date: datetime | None
    info_received_ps_date: datetime | None
    latitude: float | None
    longitude: float | None
    brief_facts: str | None


@dataclass(frozen=True)
class Person:
    """**Inferred.** Carries resolution confidence always (§2.1, P10).
    Backed by `lumen_person` <- resolved `Accused` (§3.6). Identity:
    `person_id` (UUID).

    Not populated in Session 2 — entity resolution (§6) is Session 7's
    scope, and `lumen_person` is not created by this session's schema
    work. This dataclass exists only because the entity vocabulary (§2.1)
    is closed and names `Person` as one of the eleven; nothing in
    Session 2 constructs or persists one.
    """

    person_id: str          # UUID
    canonical_name: str
    first_seen: datetime | None
    last_seen: datetime | None
    case_count: int
    district_count: int
    resolution_confidence: float
    method_version: str


@dataclass(frozen=True)
class CaseParticipant:
    """A role in one case, not a human. Backed by `Accused` | `Victim` |
    `ComplainantDetails` (§3.5). Identity: composite."""

    role: Literal["accused", "victim", "complainant"]
    case_master_id: int
    # Accused
    accused_master_id: int | None = None
    accused_name: str | None = None
    person_id_label: str | None = None   # Accused.PersonID — ordering (A1, A2…), NOT identity (§3.2 fact 2)
    # Victim
    victim_master_id: int | None = None
    victim_name: str | None = None
    victim_police: str | None = None      # §3.3 — stored VARCHAR "1"/"0"; exposed as bool by render/semantic helpers
    # ComplainantDetails
    complainant_id: int | None = None
    complainant_name: str | None = None
    occupation_id: int | None = None
    religion_id: int | None = None        # P9 — stored, never analysed
    caste_id: int | None = None           # P9 — stored, never analysed
    # Shared
    age_year: int | None = None
    gender_id: int | None = None


@dataclass(frozen=True)
class Officer:
    """Registering officer and IO are both this. Backed by `Employee`
    (§3.5). Identity: `EmployeeID`."""

    employee_id: int
    district_id: int | None
    unit_id: int | None
    rank_id: int | None
    designation_id: int | None
    kgid: str | None
    first_name: str | None
    appointment_date: date | None
    # EmployeeDOB, BloodGroupID, PhysicallyChallenged are P9/§4.2-restricted
    # ("never rendered in LUMEN at all" per the asset register) — deliberately
    # not exposed on this semantic entity.


@dataclass(frozen=True)
class Station:
    """`Unit` hierarchy is flattened here. Backed by `Unit` where type =
    police station (§3.5). Identity: `UnitID`."""

    unit_id: int
    unit_name: str
    type_id: int | None
    parent_unit: int | None
    state_id: int | None
    district_id: int | None


@dataclass(frozen=True)
class Jurisdiction:
    """Backed by `District` / `State` (§3.5). Identity: `DistrictID` /
    `StateID`."""

    level: Literal["district", "state"]
    district_id: int | None = None
    district_name: str | None = None
    state_id: int | None = None
    state_name: str | None = None


@dataclass(frozen=True)
class Court:
    """Backed by `Court` (§3.5). Identity: `CourtID`."""

    court_id: int
    court_name: str
    district_id: int | None
    state_id: int | None


@dataclass(frozen=True)
class Charge:
    """Rendered as "IPC 302". Backed by `ActSectionAssociation` + `Act` +
    `Section` (§3.5). Identity: composite."""

    case_master_id: int
    act_id: str
    section_id: str
    act_short_name: str | None = None
    section_description: str | None = None


@dataclass(frozen=True)
class CrimeType:
    """Two-level. Backed by `CrimeHead` + `CrimeSubHead` (§3.5). Identity:
    `CrimeHeadID`/`CrimeSubHeadID`."""

    crime_head_id: int
    crime_group_name: str | None
    crime_sub_head_id: int | None = None
    crime_head_name: str | None = None


@dataclass(frozen=True)
class ProcessEvent:
    """Everything on the timeline. Backed by `ArrestSurrender` |
    `ChargesheetDetails` | dated `CaseMaster` columns (§3.5). Identity:
    `event_id`."""

    event_id: str
    case_master_id: int
    kind: Literal["incident", "info_received", "registered", "arrest", "chargesheet"]
    occurred_at: datetime | None
    # Arrest-specific
    arrest_surrender_id: int | None = None
    ioid: int | None = None
    # Chargesheet-specific
    csid: int | None = None
    cstype: str | None = None   # 'A' chargesheet / 'B' false / 'C' undetected (§3.2 fact 6)


@dataclass(frozen=True)
class Insight:
    """The output currency of the platform. Backed by `lumen_insight`
    (§3.6). Identity: `insight_id`.

    Not populated in Session 2 — the full `Insight` object with factors,
    evidence, lineage, and confidence breakdown is defined in §8 (Session
    8), and `lumen_insight` is not created by this session's schema work.
    This dataclass exists only because the entity vocabulary (§2.1) is
    closed and names `Insight` as one of the eleven; nothing in Session 2
    constructs or persists one. Its shape here is deliberately the
    minimal identity/subject fields §2.1 and §3.6 give textually, not the
    full `Insight` Pydantic model from §8, which this session must not
    implement.
    """

    insight_id: str          # UUID
    kind: str
    subject_type: str
    subject_id: str
    headline: str
