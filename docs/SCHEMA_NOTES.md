# LUMEN v3 — Schema Notes

Sourced from LUMEN_MASTER_SPEC_V3 §3 (canonical data model). The supplied
*Police FIR System — ER Diagram* (KSP ERD) is adopted verbatim as canonical
(ADR-002); column and key names are not "improved" (§3.1). This document
records the schema facts that drive the architecture, the known inconsistencies
that are **handled, not silently fixed**, and the two tables referenced but not
defined.

This is the file the §38 judge answer points to: "We also found eight
structural inconsistencies, listed in `SCHEMA_NOTES.md`."

---

## 1. The seven schema facts that drive the architecture (§3.2)

| # | Fact | Consequence |
|---|---|---|
| 1 | **No person master.** `Accused` is keyed by `AccusedMasterID` and carries `CaseMasterID` — a per-case row, not a human | Cross-case identity must be inferred (§6, ADR-003). Also the strongest story in the pitch |
| 2 | `Accused.PersonID` is `VARCHAR` holding `A1, A2, A3…` — ordering within a case | Never join on it. Do use it: A1 vs A5 signals role |
| 3 | `CaseMaster.latitude`/`longitude` sit on the spine table | The geospatial pillar needs no joins. Indexed (`ix_case_geo`) |
| 4 | `CrimeNo` = **1 category + 4 district + 4 unit + 4 year + 5 serial**. Examples: FIR `1…`, UDR `3…`, PAR `4…`, Zero FIR `8…` | Free dimensions, a validation rule (`Q04`), and the signature UI device (§31.3) |
| 5 | `IncidentFromDate` and `InfoReceivedPSDate` are separate | **Reporting delay** is computable statewide — a genuine policing metric |
| 6 | `ChargesheetDetails.cstype` = `A` chargesheet / `B` false / `C` undetected | The **labelled outcome column**; detection-rate and outcome modelling depend on it |
| 7 | `ArrestSurrender` links to `Accused` twice — directly and via `inv_arrestsurrenderaccused` | Support both; prefer the junction when populated |

---

## 2. Known inconsistencies — handled, don't silently "fix" (§3.3)

Each is handled as specified below; where detectable at runtime it becomes a
`data_quality` insight (§5.3, §3.3).

| # | Issue | Handling |
|---|---|---|
| 1 | `ActSectionAssociation.ActID` is `INT` but references `Act.ActCode` (`VARCHAR`) | Store `VARCHAR`; note the coercion |
| 2 | `Section` has no declared PK | Composite `(ActCode, SectionCode)` |
| 3 | `CrimeHeadActSection` has no declared PK | Composite `(CrimeHeadID, ActCode, SectionCode)` |
| 4 | `ActSectionAssociation` has no declared PK | Composite `(CaseMasterID, ActID, SectionID)` |
| 5 | `Victim.VictimPolice` is `VARCHAR` holding `1`/`0` | Keep the type; expose boolean at the semantic layer |
| 6 | `ChargesheetDetails.PolicePersonID` references "employeeMaster.employee ID" | Resolve to `Employee.EmployeeID` |
| 7 | `Employee` has `FirstName` only | Display name = `FirstName` + rank + KGID suffix |
| 8 | `CrimeMajorHeadID` vs `CrimeSubHead.CrimeHeadID` can disagree | Validate; mismatch emits a `data_quality` insight (quality rule `Q11`) |

Eight inconsistencies — the number the §38 judge answer states.

---

## 3. Referenced but undefined (§3.4)

- **`Inv_OccuranceTime`** — 1:1 with `CaseMaster`. **Not created.** `CaseMaster`
  already carries the occurrence columns (`IncidentFromDate`, `IncidentToDate`,
  `InfoReceivedPSDate`). The redundancy is noted, not reproduced.
- **`inv_arrestsurrenderaccused`** — **created** per the spec's explicit
  instruction: `(ArrestSurrenderID, AccusedMasterID)` (§3.4, `db/models/
  canonical.py`).

---

## 4. Canonical inventory

Twenty-six tables are defined in the supplied ERD and one more
(`inv_arrestsurrenderaccused`) is created per §3.4 — **27 canonical tables**,
grouped as (§3.1):

- **Geography:** State, District, Court
- **Organisation:** UnitType, Unit, Rank, Designation, Employee
- **Legal:** Act, Section, ActSectionAssociation, CrimeHead, CrimeSubHead,
  CrimeHeadActSection
- **Case core:** CaseMaster (the spine), Victim, Accused, ComplainantDetails,
  ArrestSurrender, ChargesheetDetails, inv_arrestsurrenderaccused
- **Lookups:** CaseCategory, GravityOffence, CaseStatusMaster
- **Demographic (stored, never analysed — P9):** CasteMaster, ReligionMaster,
  OccupationMaster

The `lumen_` overlay (§3.6) is keyed to these canonical IDs and never
duplicates a canonical column: "A judge must be able to drop every `lumen_`
table and be left with exactly the official schema."

The full canonical DDL is in the specification §3.5 and `data/schema.sql`.
