# LUMEN v3 — Master Platform Specification
### AI Crime Intelligence Platform · Karnataka State Police · Catalyst-native
**Status: FROZEN.** Architecture is closed. Changes require the process in §37.

**Contract with the implementer.** This document is the single source of truth. Do not invent features. Do not change a contract defined here. Do not modify files outside the paths named in the session brief. Where this document does not determine an answer, state *"Cannot determine from the specification"* and stop — do not guess.

**How to use it.** One build session per row of §33, opened with: *"Implement §X of LUMEN_MASTER_SPEC_V3.md."*

---

# PART I — FOUNDATIONS

## §0. Design philosophy

Twelve principles. Every decision below derives from one; any decision contradicting one is a defect.

| # | Principle | Operational meaning |
|---|---|---|
| P1 | **Intelligence over CRUD** | Every screen generates or consumes an `Insight`. A screen that only reads and writes rows does not ship. |
| P2 | **Evidence before AI** | The model never queries the database. It receives a retrieved bundle. Any entity ID in a response that was not in that bundle is discarded server-side. |
| P3 | **Human in the loop** | LUMEN recommends; officers decide. No automated enforcement, no assertion of guilt. Language is "associated with", never "is a criminal". |
| P4 | **Explainability by default** | No score without factors, confidence, method, lineage and stated limitations. |
| P5 | **Event-driven intelligence** | State changes emit domain events; intelligence updates itself rather than waiting to be asked. |
| P6 | **Catalyst native** | Where Catalyst provides a managed service for a capability, that service is used. Exceptions are registered in §26.3. |
| P7 | **Zero trust** | Every request authenticated, authorised, audited, attributable. No anonymous path to case data. |
| P8 | **Extensible platform** | Capabilities register through a common interface; a new one is added without touching the core. |
| P9 | **Protected attributes are never analytical inputs** | Caste, religion, blood group, disability status are stored because the canonical schema defines them, and excluded from every feature, filter, chart, prompt and map layer. Enforced by a deny-list, tested in CI. |
| P10 | **Identity claims carry uncertainty** | The schema has no person master, so every cross-case identity is *inferred*. The UI never says "this is the same person"; it says "high-confidence match (0.91), here is why." |
| P11 | **Data is classified and governed** | Every table declares classification, owner, retention, masking rule. Nothing is stored without a declared lifecycle. |
| P12 | **Fail visibly, degrade gracefully** | Every dependency has a defined failure mode and a fallback. The UI states when it is serving degraded data. Silent wrong answers are worse than stated unavailability. |

---

## §1. Build tiers

Tiering is about **truthfulness of claims**, not about effort. The organisers' guidance is explicit: do not list a service you do not use. The same discipline applies to subsystems.

| Tier | Meaning | Where it may be claimed |
|---|---|---|
| **T1** | Built, live, demonstrated | Code, demo, slides |
| **T2** | Built, demonstrated if stable | Code, demo, slides — dropped from slides if not working |
| **T3** | Designed and documented, deliberately not built | Architecture doc and roadmap slide only |

**A T3 subsystem is never described in the present tense.** Judges test claims. A stated roadmap reads as maturity; a discovered overclaim costs more than the feature was worth.

| Subsystem | § | Tier |
|---|---|---|
| Semantic layer & entity vocabulary | 2 | T1 |
| Canonical data model on Data Store | 3 | T1 |
| Data governance & classification | 4 | T1 (declaration) / T2 (enforcement automation) |
| Data quality engine | 5 | T1 |
| Entity resolution | 6 | T1 |
| Data contracts & versioning | 7 | T1 |
| Insight, explainability, lineage | 8 | T1 |
| Confidence model | 9 | T1 |
| Intelligence lifecycle | 10 | T1 (states) / T2 (approval workflow) |
| Trust framework | 11 | T1 |
| Feature store | 12 | T2 |
| Prediction engine | 13 | T1 |
| Knowledge graph & projection | 14 | T1 |
| Knowledge base & RAG | 15 | T1 |
| AI orchestrator | 16 | T1 |
| AI evaluation framework | 17 | T1 |
| Decision support | 18 | T2 |
| Intelligence bus & domain events | 19 | T1 |
| Policy engine | 20 | T1 (RBAC) / T2 (ABAC) |
| Event store & audit | 21 | T1 (auth+AI events) / T2 (full) |
| Service registry | 22 | T2 |
| Resource manager | 23 | T2 |
| Failure strategy | 24 | T1 |
| Observability | 25 | T2 |
| Multi-agent decomposition | 16.6 | T3 |
| District digital twin | 36.1 | T3 |
| Plugin SDK & marketplace | 36.2 | T3 |
| Research extensions & federation | 36.3 | T3 |

---

## §2. Semantic layer

**The problem it solves:** the UI, the AI and the graph must not know that SQL exists. Without a named vocabulary layer, three subsystems each invent their own idea of what a "case" is and they disagree on screen.

**The rule:** nothing above `db/repositories/` ever references a table or column name. Everything speaks the entity vocabulary below. Repositories translate; nothing else does.

### 2.1 Entity vocabulary

Eleven semantic entities. This list is closed.

| Entity | Backed by | Identity | Notes |
|---|---|---|---|
| `Case` | `CaseMaster` + children | `CaseMasterID` | The spine. Always returned as an aggregate, never a bare row |
| `Person` | `lumen_person` ← resolved `Accused` | `person_id` (UUID) | **Inferred.** Carries resolution confidence always |
| `CaseParticipant` | `Accused` \| `Victim` \| `ComplainantDetails` | composite | A role in one case, not a human |
| `Officer` | `Employee` | `EmployeeID` | Registering officer and IO are both this |
| `Station` | `Unit` where type = police station | `UnitID` | `Unit` hierarchy is flattened here |
| `Jurisdiction` | `District` / `State` | `DistrictID` / `StateID` | |
| `Court` | `Court` | `CourtID` | |
| `Charge` | `ActSectionAssociation` + `Act` + `Section` | composite | Rendered as "IPC 302" |
| `CrimeType` | `CrimeHead` + `CrimeSubHead` | `CrimeHeadID`/`CrimeSubHeadID` | Two-level |
| `ProcessEvent` | `ArrestSurrender` \| `ChargesheetDetails` \| dated `CaseMaster` columns | `event_id` | Everything on the timeline |
| `Insight` | `lumen_insight` | `insight_id` | The output currency of the platform |

### 2.2 Consequences

- **API responses use entity names**, not table names. `GET /cases/{id}` returns `participants`, not `accused_rows`.
- **Graph nodes are semantic entities**, never table rows. This is why `Person` (resolved) is a node and `Accused` is not.
- **AI prompts describe entities**, never schema. The retriever renders evidence as entity descriptions.
- **One translation point.** If `Accused` gains a column tomorrow, exactly one repository changes.

### 2.3 Canonical display forms

Fixed strings, used everywhere, defined once in `semantics/render.py`:

```
Case          "FIR 104430006202600001 · Murder · Heinous · Under Investigation"
Person        "Person P-4471 · 4 linked case records · confidence 0.91"
Officer       "PSI Ramesh (KGID 4429213), Whitefield PS"
Charge        "IPC 302 — Punishment for murder"
ProcessEvent  "Arrest · 12 Mar 2026 · Whitefield PS · IO PSI Ramesh"
```

---

## §3. Canonical data model

### 3.1 Source of truth

The supplied *Police FIR System — ER Diagram* is adopted verbatim. Column and key names are not "improved". Twenty-six tables are defined; two more are referenced in the relationship matrix without definitions (§3.4).

```
GEOGRAPHY      ORGANISATION   LEGAL                  CASE CORE
State          Unit           Act                    CaseMaster ◄── spine
District       UnitType       Section                Victim
Court          Employee       ActSectionAssociation  Accused
               Rank           CrimeHead              ComplainantDetails
               Designation    CrimeSubHead           ArrestSurrender
                              CrimeHeadActSection    ChargesheetDetails

LOOKUPS                              DEMOGRAPHIC (stored, never analysed — P9)
CaseCategory · GravityOffence        CasteMaster · ReligionMaster · OccupationMaster
CaseStatusMaster
```

### 3.2 The seven schema facts that drive the architecture

| # | Fact | Consequence |
|---|---|---|
| 1 | **No person master.** `Accused` is keyed by `AccusedMasterID` and carries `CaseMasterID` — a per-case row, not a human | Cross-case identity must be inferred (§6). This is also the strongest story in the pitch |
| 2 | `Accused.PersonID` is `VARCHAR` holding `A1, A2, A3…` — ordering within a case | Never join on it. Do use it: A1 vs A5 signals role |
| 3 | `CaseMaster.latitude`/`longitude` sit on the spine table | The entire geospatial pillar needs no joins. Index them |
| 4 | `CrimeNo` = **1 category + 4 district + 4 unit + 4 year + 5 serial**. Examples: FIR `1…`, UDR `3…`, PAR `4…`, Zero FIR `8…` | Free dimensions, a validation rule, and the signature UI device (§31.3) |
| 5 | `IncidentFromDate` and `InfoReceivedPSDate` are separate | **Reporting delay** is computable statewide. A genuine policing metric no other team will show |
| 6 | `ChargesheetDetails.cstype` = `A` chargesheet / `B` false / `C` undetected | Your **labelled outcome column**. Detection-rate modelling depends on it |
| 7 | `ArrestSurrender` links to `Accused` twice — directly and via `inv_arrestsurrenderaccused` | Support both; prefer the junction when populated. Document the choice |

### 3.3 Known inconsistencies — handle, don't silently "fix"

Logged in `docs/SCHEMA_NOTES.md`. Each becomes a `data_quality` insight where detectable at runtime.

| Issue | Handling |
|---|---|
| `ActSectionAssociation.ActID` is `INT` but references `Act.ActCode` (`VARCHAR`) | Store `VARCHAR`; note the coercion |
| `Section` has no declared PK | Composite `(ActCode, SectionCode)` |
| `CrimeHeadActSection` has no declared PK | Composite `(CrimeHeadID, ActCode, SectionCode)` |
| `ActSectionAssociation` has no declared PK | Composite `(CaseMasterID, ActID, SectionID)` |
| `Victim.VictimPolice` is `VARCHAR` holding `1`/`0` | Keep the type; expose boolean at the semantic layer |
| `ChargesheetDetails.PolicePersonID` references "employeeMaster.employee ID" | Resolve to `Employee.EmployeeID` |
| `Employee` has `FirstName` only | Display name = `FirstName` + rank + KGID suffix |
| `CrimeMajorHeadID` vs `CrimeSubHead.CrimeHeadID` can disagree | Validate; mismatch emits a `data_quality` insight |

### 3.4 Referenced but undefined

- `Inv_OccuranceTime` — 1:1 with `CaseMaster`. **Do not create it.** `CaseMaster` already carries the occurrence columns. Note the redundancy.
- `inv_arrestsurrenderaccused` — **create it**: `(ArrestSurrenderID, AccusedMasterID)`.

### 3.5 Canonical DDL → `data/schema.sql`

PostgreSQL types shown for local development; Data Store mapping in §26.2.

```sql
-- ═══ GEOGRAPHY ═══
CREATE TABLE State (StateID INT PRIMARY KEY, StateName VARCHAR(120) NOT NULL,
  NationalityID INT, Active BOOLEAN DEFAULT TRUE);

CREATE TABLE District (DistrictID INT PRIMARY KEY, DistrictName VARCHAR(120) NOT NULL,
  StateID INT REFERENCES State(StateID), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Court (CourtID INT PRIMARY KEY, CourtName VARCHAR(200) NOT NULL,
  DistrictID INT REFERENCES District(DistrictID),
  StateID INT REFERENCES State(StateID), Active BOOLEAN DEFAULT TRUE);

-- ═══ ORGANISATION ═══
CREATE TABLE UnitType (UnitTypeID INT PRIMARY KEY, UnitTypeName VARCHAR(120),
  CityDistState VARCHAR(20), Hierarchy INT, Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Unit (UnitID INT PRIMARY KEY, UnitName VARCHAR(200) NOT NULL,
  TypeID INT REFERENCES UnitType(UnitTypeID),
  ParentUnit INT REFERENCES Unit(UnitID), NationalityID INT,
  StateID INT REFERENCES State(StateID),
  DistrictID INT REFERENCES District(DistrictID), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Rank (RankID INT PRIMARY KEY, RankName VARCHAR(120),
  Hierarchy INT, Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Designation (DesignationID INT PRIMARY KEY, DesignationName VARCHAR(120),
  Active BOOLEAN DEFAULT TRUE, SortOrder INT);

CREATE TABLE Employee (EmployeeID INT PRIMARY KEY,
  DistrictID INT REFERENCES District(DistrictID),
  UnitID INT REFERENCES Unit(UnitID),
  RankID INT REFERENCES Rank(RankID),
  DesignationID INT REFERENCES Designation(DesignationID),
  KGID VARCHAR(40), FirstName VARCHAR(120), EmployeeDOB DATE,
  GenderID INT, BloodGroupID INT,            -- P9
  PhysicallyChallenged BOOLEAN,              -- P9
  AppointmentDate DATE);

-- ═══ LEGAL ═══
CREATE TABLE Act (ActCode VARCHAR(40) PRIMARY KEY, ActDescription VARCHAR(400),
  ShortName VARCHAR(80), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE Section (ActCode VARCHAR(40) REFERENCES Act(ActCode),
  SectionCode VARCHAR(40), SectionDescription VARCHAR(600),
  Active BOOLEAN DEFAULT TRUE, PRIMARY KEY (ActCode, SectionCode));

CREATE TABLE CrimeHead (CrimeHeadID INT PRIMARY KEY,
  CrimeGroupName VARCHAR(200), Active BOOLEAN DEFAULT TRUE);

CREATE TABLE CrimeSubHead (CrimeSubHeadID INT PRIMARY KEY,
  CrimeHeadID INT REFERENCES CrimeHead(CrimeHeadID),
  CrimeHeadName VARCHAR(200), SeqID INT);

CREATE TABLE CrimeHeadActSection (
  CrimeHeadID INT REFERENCES CrimeHead(CrimeHeadID),
  ActCode VARCHAR(40), SectionCode VARCHAR(40),
  PRIMARY KEY (CrimeHeadID, ActCode, SectionCode),
  FOREIGN KEY (ActCode, SectionCode) REFERENCES Section(ActCode, SectionCode));

-- ═══ LOOKUPS ═══
CREATE TABLE CaseCategory (CaseCategoryID INT PRIMARY KEY, LookupValue VARCHAR(80));
CREATE TABLE GravityOffence (GravityOffenceID INT PRIMARY KEY, LookupValue VARCHAR(80));
CREATE TABLE CaseStatusMaster (CaseStatusID INT PRIMARY KEY, CaseStatusName VARCHAR(120));
CREATE TABLE CasteMaster (caste_master_id INT PRIMARY KEY, caste_master_name VARCHAR(120));
CREATE TABLE ReligionMaster (ReligionID INT PRIMARY KEY, ReligionName VARCHAR(120));
CREATE TABLE OccupationMaster (OccupationID INT PRIMARY KEY, OccupationName VARCHAR(120));

-- ═══ CASE CORE ═══
CREATE TABLE CaseMaster (
  CaseMasterID INT PRIMARY KEY,
  CrimeNo VARCHAR(30) NOT NULL, CaseNo VARCHAR(20),
  CrimeRegisteredDate DATE,
  PolicePersonID INT REFERENCES Employee(EmployeeID),
  PoliceStationID INT REFERENCES Unit(UnitID),
  CaseCategoryID INT REFERENCES CaseCategory(CaseCategoryID),
  GravityOffenceID INT REFERENCES GravityOffence(GravityOffenceID),
  CrimeMajorHeadID INT REFERENCES CrimeHead(CrimeHeadID),
  CrimeMinorHeadID INT REFERENCES CrimeSubHead(CrimeSubHeadID),
  CaseStatusID INT REFERENCES CaseStatusMaster(CaseStatusID),
  CourtID INT REFERENCES Court(CourtID),
  IncidentFromDate TIMESTAMP, IncidentToDate TIMESTAMP, InfoReceivedPSDate TIMESTAMP,
  latitude DECIMAL(10,7), longitude DECIMAL(10,7),
  BriefFacts TEXT);

CREATE INDEX ix_case_geo  ON CaseMaster(latitude, longitude);
CREATE INDEX ix_case_date ON CaseMaster(CrimeRegisteredDate);
CREATE INDEX ix_case_unit ON CaseMaster(PoliceStationID);
CREATE INDEX ix_case_head ON CaseMaster(CrimeMajorHeadID, CrimeMinorHeadID);

CREATE TABLE Victim (VictimMasterID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  VictimName VARCHAR(200), AgeYear INT, GenderID INT, VictimPolice VARCHAR(2));

CREATE TABLE Accused (AccusedMasterID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  AccusedName VARCHAR(200), AgeYear INT, GenderID INT,
  PersonID VARCHAR(10));                     -- ordering, NOT identity

CREATE TABLE ComplainantDetails (ComplainantID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  ComplainantName VARCHAR(200), AgeYear INT,
  OccupationID INT REFERENCES OccupationMaster(OccupationID),
  ReligionID INT REFERENCES ReligionMaster(ReligionID),          -- P9
  CasteID INT REFERENCES CasteMaster(caste_master_id),           -- P9
  GenderID INT);

CREATE TABLE ActSectionAssociation (
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  ActID VARCHAR(40), SectionID VARCHAR(40),
  ActOrderID INT, SectionOrderID INT,
  PRIMARY KEY (CaseMasterID, ActID, SectionID));

CREATE TABLE ArrestSurrender (ArrestSurrenderID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  ArrestSurrenderTypeID INT, ArrestSurrenderDate DATE,
  ArrestSurrenderStateId INT REFERENCES State(StateID),
  ArrestSurrenderDistrictId INT REFERENCES District(DistrictID),
  PoliceStationID INT REFERENCES Unit(UnitID),
  IOID INT REFERENCES Employee(EmployeeID),
  CourtID INT REFERENCES Court(CourtID),
  AccusedMasterID INT REFERENCES Accused(AccusedMasterID),
  IsAccused BOOLEAN, IsComplainantAccused BOOLEAN);

CREATE TABLE inv_arrestsurrenderaccused (
  ArrestSurrenderID INT REFERENCES ArrestSurrender(ArrestSurrenderID),
  AccusedMasterID INT REFERENCES Accused(AccusedMasterID),
  PRIMARY KEY (ArrestSurrenderID, AccusedMasterID));

CREATE TABLE ChargesheetDetails (CSID INT PRIMARY KEY,
  CaseMasterID INT REFERENCES CaseMaster(CaseMasterID),
  csdate TIMESTAMP, cstype CHAR(1),
  PolicePersonID INT REFERENCES Employee(EmployeeID));
```

### 3.6 LUMEN-owned tables

Every LUMEN table is prefixed `lumen_`, keyed to canonical IDs, and **never duplicates a canonical column**. A judge must be able to drop every `lumen_` table and be left with exactly the official schema.

```sql
-- identity (§6)
lumen_person(person_id UUID PK, canonical_name, first_seen, last_seen,
             case_count, district_count, resolution_confidence, method_version)
lumen_person_link(person_id FK, accused_master_id FK, confidence,
                  match_features JSON, state, PRIMARY KEY(person_id, accused_master_id))
lumen_person_dispute(dispute_id PK, person_id FK, accused_master_id FK,
                     raised_by, reason, raised_at, resolution)

-- intelligence (§8–§11)
lumen_insight(insight_id UUID PK, kind, subject_type, subject_id, headline,
              score, confidence, confidence_components JSON, factors JSON,
              counterfactuals JSON, evidence JSON, limitations JSON,
              lineage JSON, contract_version, lifecycle_state,
              generated_at, expires_at, approved_by, approved_at)

-- graph (§14)
lumen_graph_edge(src_type, src_id, dst_type, dst_id, rel, weight, props JSON, computed_at)
lumen_person_metrics(person_id FK, degree, betweenness, eigenvector,
                     community_id, district_span, computed_at)
lumen_community(community_id PK, size, district_ids JSON, broker_person_id, computed_at)

-- geo / prediction
lumen_hotspot(cluster_id PK, centroid_lat, centroid_lng, radius_m, weight,
              district_id, crime_head_id, window_start, window_end, method)
lumen_district_risk(district_id FK, window_start, band, score, factors JSON, model_version)

-- knowledge base (§15)
lumen_kb_document(doc_id PK, kind, title, source, effective_from, classification, checksum)
lumen_kb_chunk(chunk_id PK, doc_id FK, ordinal, text, embedding_ref, token_count)

-- quality & governance (§4, §5)
lumen_quality_finding(finding_id PK, rule_id, severity, entity_type, entity_id,
                      detail JSON, detected_at, state)
lumen_quality_score(scope_type, scope_id, dimension, score, computed_at)
lumen_data_asset(table_name PK, classification, owner_role, retention_days,
                 masking_rule, encrypted, pii BOOLEAN)

-- platform (§12, §17, §21, §22)
lumen_feature(entity_type, entity_id, feature_name, value, version, computed_at)
lumen_model_registry(model_id PK, name, kind, version, params JSON,
                     metrics JSON, trained_at, active BOOLEAN)
lumen_prompt_registry(prompt_id PK, name, version, template_hash, created_at, active BOOLEAN)
lumen_service_registry(service_id PK, name, capability, version, endpoint,
                       depends_on JSON, health_state, last_check)
lumen_ai_eval(eval_id PK, run_id, question_id, groundedness, correctness,
              hallucinated_ids INT, latency_ms, prompt_version, evaluated_at)
lumen_event(event_id UUID PK, event_type, event_version, actor_id,
            subject_type, subject_id, payload JSON, trace_id, occurred_at)
lumen_audit(audit_id UUID PK, user_id, action, resource, decision,
            reason, ip, occurred_at)
lumen_user_role(user_id PK, role, district_scope JSON, unit_scope JSON)
lumen_case_note(note_id PK, CaseMasterID FK, author_id, body, created_at)
lumen_evidence_asset(asset_id PK, CaseMasterID FK, stratus_key, kind,
                     filename, classification, uploaded_by, uploaded_at)
```

---

## §4. Data governance — T1 declaration, T2 enforcement

**Why it belongs in a hackathon spec:** this is police data. A judge from a state police department will care more about who can see a victim's name than about your animation curve.

### 4.1 Classification scheme

| Class | Definition | Examples | Handling |
|---|---|---|---|
| **PUBLIC** | Safe for citizen-facing display | District names, act/section descriptions, aggregate counts | No masking |
| **INTERNAL** | Police-wide operational data | Crime heads, unit names, hotspot clusters, district risk | Any authenticated role |
| **CONFIDENTIAL** | Case-identifying data | `BriefFacts`, `CrimeNo`, case coordinates, officer identity | Role + jurisdiction scope |
| **RESTRICTED** | Person-identifying and protected attributes | Names of victims, accused, complainants; `CasteID`, `ReligionID`, ages, `KGID` | Role + scope + masking below threshold; every access audited individually |

### 4.2 Asset register (`lumen_data_asset`) — declared for every table

| Table | Class | Owner role | Retention | Masking |
|---|---|---|---|---|
| `CaseMaster` | CONFIDENTIAL | State Analyst | Per record-retention policy; not deleted by LUMEN | `BriefFacts` truncated below District SP |
| `Victim` | RESTRICTED | District SP | As above | Name masked to `V1`, age banded, below District SP |
| `Accused` | RESTRICTED | District SP | As above | Name masked to `A1` below Investigating Officer |
| `ComplainantDetails` | RESTRICTED | District SP | As above | Name masked; **caste/religion never rendered outside a single case-detail view for District SP and above, never in any aggregate** |
| `Employee` | CONFIDENTIAL | Admin | Employment + statutory | `EmployeeDOB`, `BloodGroupID`, `PhysicallyChallenged` never rendered in LUMEN at all |
| `lumen_insight` | CONFIDENTIAL | State Analyst | 180 days then archived | Inherits the classification of its subject |
| `lumen_person` | RESTRICTED | State Analyst | 180 days, recomputed | Always shown with confidence (P10) |
| `lumen_event` | INTERNAL | Auditor | 365 days | Immutable |
| `lumen_audit` | RESTRICTED | Auditor | 365 days | Immutable, readable only by Auditor |
| `lumen_kb_*` | INTERNAL | Admin | Until superseded | — |
| Lookup tables | PUBLIC | Admin | Indefinite | — |

### 4.3 Governance rules

1. **LUMEN never deletes canonical records.** It is an analytical overlay, not a system of record. Retention applies to `lumen_` tables only.
2. **Derived data inherits the highest classification of its inputs.** An insight built from `Victim` is RESTRICTED.
3. **Aggregates below k=5 are suppressed.** A district-week count of 2 with a caste breakdown is re-identification. The UI shows "fewer than 5 — suppressed."
4. **Encryption:** at rest via the platform store; in transit TLS. Evidence assets in Stratus are classified at upload.
5. **Export is a governed action** — role-gated, individually audited, watermarked with the requesting user and timestamp.
6. **P9 enforcement is structural**, not a convention: `intelligence/guards.py` holds the deny-list, every feature/prompt/chart builder passes through it, and a CI test fails the build if a denied column reaches a model input.

---

## §5. Data quality engine — T1

Government data is messy. Formalising quality turns a liability into an intelligence product, and gives you a screen no other team will have.

### 5.1 Rule catalogue

| Rule | Dimension | Severity | Detection |
|---|---|---|---|
| `Q01` missing coordinates | Completeness | High | `latitude` or `longitude` null |
| `Q02` impossible coordinates | Validity | Critical | Outside Karnataka bounding box, or (0,0) |
| `Q03` malformed CrimeNo | Validity | High | Not 18 digits, or category digit not in the documented set |
| `Q04` CrimeNo/Unit mismatch | Consistency | High | Embedded district or unit ≠ `Unit.DistrictID`/`UnitID` |
| `Q05` incident after registration | Consistency | High | `IncidentFromDate` > `CrimeRegisteredDate` |
| `Q06` info received before incident | Consistency | High | `InfoReceivedPSDate` < `IncidentFromDate` |
| `Q07` chargesheet before registration | Consistency | Critical | `csdate` < `CrimeRegisteredDate` |
| `Q08` arrest before incident | Consistency | Critical | `ArrestSurrenderDate` < `IncidentFromDate` |
| `Q09` orphan child row | Integrity | Critical | `CaseMasterID` with no parent |
| `Q10` broken lookup reference | Integrity | High | FK to a missing or inactive lookup |
| `Q11` crime head / sub-head disagreement | Consistency | Medium | `CrimeMajorHeadID` ≠ `CrimeSubHead.CrimeHeadID` |
| `Q12` duplicate case suspicion | Uniqueness | Medium | Same unit + date + head + ≥1 shared participant name |
| `Q13` implausible age | Validity | Medium | `AgeYear` < 1 or > 110 |
| `Q14` accused with no PersonID | Completeness | Low | `PersonID` null where siblings have it |
| `Q15` case with no charges | Completeness | Medium | No `ActSectionAssociation` rows |
| `Q16` stale open case | Timeliness | Medium | Status open, no process event in 180 days |
| `Q17` inactive act/section in use | Validity | Medium | `ActSectionAssociation` → `Active = false` |
| `Q18` empty BriefFacts | Completeness | Low | Null or under 20 characters |

### 5.2 Quality scoring

Six dimensions — **completeness, validity, consistency, integrity, uniqueness, timeliness** — scored 0–1 per scope (state, district, unit) as `1 − weighted_findings / records_in_scope`, weighted by severity (Critical 4, High 2, Medium 1, Low 0.5). Written to `lumen_quality_score` on every precompute run.

### 5.3 Quality as intelligence

Findings surface three ways, and this is the point:

1. **`Insight(kind="data_quality")`** on the affected entity — the case page says "this FIR's number encodes Unit 0012 but it is registered to Unit 0006."
2. **A `/quality` surface** with district-level scores, trend, and top rules firing. Frames it as *"which stations need data-entry support"* — a real administrative product, not a defect list.
3. **Confidence input** — quality scores feed the confidence model (§9), so insights computed over poor data honestly report lower confidence. This is the connection that makes the whole thing coherent rather than a bolt-on.

---

## §6. Entity resolution — T1

**Why Tier 1:** the ERD has no person master. Without resolution, `Accused` rows are islands, the network graph has no edge longer than one case, "repeat offender" is uncomputable, and the headline claim is false.

### 6.1 Available signals

Thin, and to be stated as such: `AccusedName`, `AgeYear` (with case date ⇒ approximate birth year), `GenderID`, arrest districts and stations from `ArrestSurrender`, the investigating officer, and the act-section signature of the cases.

### 6.2 Pipeline

```
Accused rows
  ↓ normalise   lowercase, honorifics stripped, patronymic particles (bin, s/o, d/o)
  ↓             separated, transliteration folded
  ↓ block       (gender, phonetic key)  ← Double Metaphone, Indic-aware
  ↓ score       weighted feature vector per candidate pair
  ↓ threshold   ≥0.85 auto-link · 0.65–0.85 candidate (surfaced, never auto-merged) · <0.65 reject
  ↓ cluster     connected components, transitivity capped at 3 hops
  ↓ persist     lumen_person + lumen_person_link with per-link confidence + match_features
```

### 6.3 Feature weights (v1; tune against the seed)

| Feature | Weight |
|---|---|
| Normalised name similarity (Jaro-Winkler) | 0.35 |
| Phonetic key match | 0.15 |
| Implied birth-year agreement (±2 y) | 0.20 |
| Gender agreement | 0.05 |
| Shared arrest district | 0.10 |
| Shared police station | 0.10 |
| Shared already-resolved co-accused (2nd pass) | 0.15 |
| **Common-name penalty** (inverse frequency) | **−0.20** |

Cap at 1.0. The common-name penalty is **mandatory** — without it, frequent names collapse hundreds of unrelated people into one node, which is both useless and defamatory.

### 6.4 Presentation rules (P3, P10)

- Confidence and a **"see why"** disclosure listing match features on every resolved identity.
- Links below 0.85 render as *candidate matches*, visually separated, excluded from centrality.
- Never "criminal", "offender", or "guilty" — always "person associated with N case records".
- A **"report incorrect match"** control on every identity, writing to `lumen_person_dispute` and emitting `PersonMatchDisputed`. Human-in-the-loop must be visible, not asserted.
- Resolution confidence propagates into every downstream insight's confidence (§9).

---

# PART II — INTELLIGENCE

## §7. Data contracts and versioning — T1

Every inter-module payload is a **versioned contract**. Modules depend on contracts, never on each other's internals.

| Contract | Version | Producer | Consumers |
|---|---|---|---|
| `EntityContract` | v1 | semantic layer | API, AI, graph, UI |
| `InsightContract` | v1 | intelligence engine | API, UI, AI, event bus |
| `GraphContract` | v1 | graph module | API, UI, AI |
| `PredictionContract` | v1 | prediction engine | intelligence engine |
| `RecommendationContract` | v1 | decision support | API, UI |
| `EventContract` | v1 | bus | all subscribers, event store |
| `EvidenceContract` | v1 | retriever | AI orchestrator, explainability |
| `QualityContract` | v1 | quality engine | intelligence engine, UI |

### Rules

1. Contracts are **additive within a major version**. Adding a field is allowed; removing or retyping one is not.
2. Every payload carries `contract_version`.
3. A breaking change means a new major version, both served in parallel, with the old marked deprecated (§29.4).
4. Contracts live in `contracts/` as Pydantic models and are the **only** shapes crossing a module boundary. A module returning a raw dict across a boundary is a defect.
5. Frontend types are generated from these models — never hand-written.

---

## §8. Insight, explainability, lineage — T1

One object. Everything in the platform that carries meaning is one of these.

```python
class Factor(BaseModel):
    label: str; weight: float; detail: str | None

class Evidence(BaseModel):
    entity: Literal["case","person","participant","officer","station",
                    "jurisdiction","court","charge","process_event","kb_document"]
    id: str; label: str; url: str            # every evidence chip is clickable

class Lineage(BaseModel):
    method: str                              # "isolation_forest"
    model_version: str                       # → lumen_model_registry
    prompt_version: str | None               # → lumen_prompt_registry
    features_used: list[str]                 # name@version
    query_ids: list[str]
    source_row_count: int
    quality_score: float                     # §5.2 for the scope
    computed_at: datetime

class ConfidenceBreakdown(BaseModel):
    evidence_quality: float
    model_confidence: float
    data_completeness: float
    identity_confidence: float
    graph_confidence: float
    composite: float

class Insight(BaseModel):
    id: str
    contract_version: str = "v1"
    kind: Literal["risk","anomaly","linkage","network","forecast","summary",
                  "recommendation","data_quality"]
    subject_type: Literal["case","person","district","unit","state"]
    subject_id: str
    headline: str                            # one plain sentence
    score: float | None
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    factors: list[Factor]
    counterfactuals: list[str]
    evidence: list[Evidence]
    limitations: list[str]                   # never empty
    lineage: Lineage
    lifecycle_state: LifecycleState          # §10
    classification: Literal["PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"]
    generated_at: datetime
    expires_at: datetime | None
```

**Invariants, enforced in CI:**
1. No endpoint returns a score outside an `Insight`.
2. `limitations` is never empty.
3. Every `Evidence.id` resolves to a real record.
4. No `Factor.label` references a P9 attribute.
5. `lineage.model_version` exists in `lumen_model_registry`.
6. `classification` ≥ the highest classification of its evidence.
7. `confidence` equals `confidence_breakdown.composite` to 3 decimal places.

---

## §9. Confidence model — T1

Confidence stops being a decorative number. It is computed, decomposed, and displayed as its parts.

```
composite = evidence_quality
          × model_confidence
          × data_completeness
          × identity_confidence
          × graph_confidence
```

| Component | Definition | Value when not applicable |
|---|---|---|
| `evidence_quality` | Retrieved evidence count ÷ expected, capped at 1, weighted by source classification | 1.0 |
| `model_confidence` | Model's own probability, or 1 − normalised anomaly distance | 1.0 |
| `data_completeness` | `lumen_quality_score` completeness dimension for the scope | 1.0 |
| `identity_confidence` | Minimum resolution confidence across persons in the evidence | 1.0 |
| `graph_confidence` | Edge support: 1 − 1/(1 + supporting_edges), damped by projection staleness | 1.0 |

Multiplicative is deliberate: a chain of inferences is only as strong as its weakest link, and an insight resting on a 0.66-confidence identity match should not read as certain.

**Display bands:** ≥0.80 High · 0.55–0.79 Moderate · <0.55 Low. Low-confidence insights render in a de-emphasised state with the weakest component named — *"limited by identity match confidence (0.61)."* That single sentence is worth more to a judge than a higher number would be.

---

## §10. Intelligence lifecycle — T1 states, T2 approval

```
Generated → Verified → Approved → Operational → Expired → Archived → Deleted
```

| State | Entered when | Visible to |
|---|---|---|
| `generated` | Producer emits it | Nobody (internal) |
| `verified` | Passes schema, evidence resolution, P9 guard, confidence floor | Analysts, marked unverified-by-human |
| `approved` | A District SP or State Analyst approves (T2) | All in scope, marked approved |
| `operational` | Referenced in a recommendation or alert | All in scope |
| `expired` | Past `expires_at` or inputs changed | Hidden, retained |
| `archived` | Retention window reached | Auditor only |
| `deleted` | Governance-driven purge | Nobody; deletion itself is audited |

**Rules.** An insight never skips `verified`. Anything below the confidence floor (0.35) is `generated` and never surfaces. Inputs changing emits `InsightExpired` and triggers regeneration. Approval is recorded with approver and timestamp — this is where P3 becomes auditable rather than rhetorical.

---

## §11. Trust framework — T1

The section that ties AI ethics to mechanism. Every claim LUMEN makes passes through seven gates; the UI exposes each one.

```
CLAIM
 ├─ 1 EVIDENCE     every claim links to canonical records          §8
 ├─ 2 CONFIDENCE   decomposed, not asserted                        §9
 ├─ 3 LINEAGE      method, model version, features, queries, quality §8
 ├─ 4 LIMITATIONS  what this cannot tell you — never empty          §8
 ├─ 5 GUARDS       P9 deny-list, evidence verification, k-anonymity §4, §16
 ├─ 6 APPROVAL     human review before operational use              §10
 └─ 7 AUDIT        who saw it, who acted on it, when                §21
        ↓
   HUMAN DECISION  ← LUMEN stops here, always
```

### Trust statements rendered in the product

- On every network result: *"Co-accusal reflects charging decisions, not adjudicated guilt."*
- On every identity: *"Inferred match. Confidence 0.91. Report if incorrect."*
- On every forecast: *"Trained on 14 months. Not valid for districts with fewer than 50 records."*
- On every recommendation: *"Suggestion for officer review. Not an instruction."*
- On the act-section suggestion: *"Reflects statistical co-occurrence in past filings. Not legal advice."*

**What LUMEN will never do**, stated in the deck and the docs: predict individual criminality, rank individuals by likelihood of offending, use protected attributes, take autonomous action, or present an inference as a fact. Naming your own red lines is the strongest governance signal available to you.

---

## §12. Feature store — T2

One table, one loader, versioned. It prevents the classic failure where the dashboard, the model and the prompt each compute "repeat offender" differently and disagree on screen.

| Feature | Entity | Definition |
|---|---|---|
| `repeat_offender_score` | person | linked cases at confidence ≥0.85, log-scaled |
| `mobility_index` | person | distinct districts ÷ cases |
| `network_influence` | person | normalised eigenvector centrality |
| `community_size` | person | Louvain community size |
| `arrest_delay_days` | case | arrest − registration |
| `report_delay_hours` | case | info received − incident |
| `charge_delay_days` | case | `csdate` − registration |
| `gravity_weight` | case | from `GravityOffenceID` |
| `signature_rarity` | case | inverse frequency of the act-section set |
| `crime_density_km2` | district | cases ÷ area, rolling 90 days |
| `detection_rate` | district/unit | `cstype='A'` ÷ chargesheeted |
| `officer_load` | unit | open cases ÷ employees |
| `repeat_victim_flag` | case | victim name+age matched in a prior case |
| `quality_completeness` | district/unit | from §5.2 |

Models and prompts **read** features; they never recompute them. Every feature carries `version` and `computed_at`; every insight records the versions it consumed.

---

## §13. Prediction engine — T1

| Model | Kind | Output | Path |
|---|---|---|---|
| District risk band | Classification | band + score + factor weights | **Zia AutoML**, scikit-learn fallback |
| Hotspot clusters | Unsupervised | clusters + weights | DBSCAN (haversine); **QuickML** pipeline at T2 |
| Volume anomaly | Detection | spike + baseline + σ | IsolationForest **and** z-score, both reported |
| Case linkage | Similarity | ranked linked cases | Local |
| Case outcome | Classification | P(`cstype` ∈ A/B/C) + factors | **Zia AutoML** |
| Reporting-delay outlier | Detection | units with anomalous delay | Local |

**Rules.** Every model reports feature importances — that is where `factors` comes from, and why tree ensembles beat deep learning here. No model consumes a P9 attribute (enforced, tested). Every prediction states its training window in `limitations`. All models batch-score into tables; the API reads.

---

## §14. Knowledge graph — T1

### 14.1 Runtime decision

Catalyst has **no graph database**. Under P6 an external graph DB is not a forbidden substitution, but it is an external dependency in a competition where Catalyst-native deployment is mandatory and judged.

**Decision:** primary runtime is **NetworkX in-process**, projections persisted to **Data Store** (`lumen_graph_edge`), adjacency snapshots in **Catalyst NoSQL**, hot ego-graphs in **Catalyst Cache**. Neo4j is optional and additive behind `graph/backend.py`. The API must not know which backend answered. See ADR-001.

### 14.2 Nodes

`Person` (resolved) · `Case` · `Officer` · `Station` · `Jurisdiction` · `Court` · `Charge` · `CrimeType` — semantic entities (§2.1), never table rows.

### 14.3 Edges

**Structural** (from foreign keys — necessary, not insightful alone): `ACCUSED_IN`, `REGISTERED_AT`, `IN`, `REGISTERED`, `INVESTIGATED`, `CHARGED_UNDER`, `TRIED_AT`, `ARRESTED_IN`.

**Derived** — the entire value of the graph:

| Edge | Derivation | Reveals |
|---|---|---|
| `(Person)-[:CO_ACCUSED_WITH {cases,first,last,districts}]->(Person)` | Shared `CaseMasterID` after resolution | The association network |
| `(Case)-[:SHARES_SIGNATURE {jaccard}]->(Case)` | Jaccard ≥0.6 on act-section sets, different units | MO families across jurisdictions |
| `(Person)-[:OPERATES_IN {cases,arrests}]->(Jurisdiction)` | Union of case and arrest districts | Cross-district mobility |
| `(Case)-[:PROXIMATE_TO {km,days}]->(Case)` | ≤5 km, ≤14 days, same major head | Spree detection |
| `(Person)-[:SAME_IO_AS]->(Person)` | Shared `IOID` | Investigative cluster — caveated as a workload artefact, not guilt |

### 14.4 The ten named queries

| # | Query | Algorithm | Question answered |
|---|---|---|---|
| Q1 | Shortest connection | BFS/Dijkstra | "How are these two connected?" |
| Q2 | Hidden intermediary | Betweenness on connecting subgraph | "Who is the only link between these groups?" |
| Q3 | Communities | Louvain | "Who operates as a unit?" |
| Q4 | Most influential in district | Eigenvector, district-filtered | "Who matters most here?" |
| Q5 | Repeat co-offender pairs | Edge-weight rank | "Who keeps offending together?" |
| Q6 | Cross-district networks | Communities spanning ≥2 districts | "Which groups cross jurisdictions?" |
| Q7 | 2-hop linked cases | Neighbourhood expansion via `Person` | "What else is this case connected to?" |
| Q8 | Signature families | Components over `SHARES_SIGNATURE` | "Which cases share a method?" |
| Q9 | Emerging cluster | Communities with ≥50% edge growth in 30 days | "What is forming now?" |
| Q10 | Spree chain | Path over `PROXIMATE_TO` ordered by date | "Is this a series?" |

Every result returns `Insight` **plus** graph payload, never a bare graph, and every result carries its limitations line.

### 14.5 Projection pipeline

```
Data Store → resolve persons (§6) → structural edges → derived edges
  → metrics (degree, betweenness, eigenvector, Louvain)
  → write lumen_graph_edge / lumen_person_metrics / lumen_community
  → snapshot to NoSQL → warm Cache for top-N ego graphs → emit GraphProjected
```

Nothing here runs per request. Any request path exceeding 400 ms reads a precomputed table instead.

---

## §15. Knowledge base and RAG — T1

RAG needs a modelled corpus, otherwise "we used RAG" means "we pasted rows into a prompt."

### 15.1 Corpus

| Kind | Source | Classification | Use |
|---|---|---|---|
| `act` | `Act.ActDescription` | PUBLIC | Legal grounding for charge questions |
| `section` | `Section.SectionDescription` | PUBLIC | The most-cited corpus; enables "what does 302 cover?" |
| `crime_taxonomy` | `CrimeHead` / `CrimeSubHead` / `CrimeHeadActSection` | PUBLIC | Maps heads to typical sections — powers the §18 charge suggestion |
| `case_brief` | `CaseMaster.BriefFacts` | CONFIDENTIAL | Similar-case retrieval; **chunked, never surfaced across jurisdiction scope** |
| `sop` | Uploaded SOPs / circulars / investigation guidelines | INTERNAL | Procedural answers. Optional — include only if real documents exist |

### 15.2 Rules

1. **Retrieval is scope-filtered before ranking.** A Station Officer's query never retrieves a chunk from a case outside their scope. Filter first, then rank — never the reverse.
2. Every chunk carries `doc_id`, `classification`, and `effective_from`. Retrieved chunks become `Evidence` entries with clickable URLs.
3. The legal corpus (PUBLIC) and the case corpus (CONFIDENTIAL) are **separate indexes**. Legal answers never leak case text.
4. Ingestion is a job: chunk → embed via QuickML → store refs in `lumen_kb_chunk`. Re-ingest on `Act`/`Section` change.
5. `Insight.limitations` records when an answer rests on legal text rather than case evidence.

---

## §16. AI orchestrator — T1

### 16.1 Provider decision (submission validity)

The organisers map *Text LLMs / RAG / knowledge bases* to **Catalyst QuickML (LLM Serving, RAG)**. Under P6, Gemini is a third-party alternative to an available Catalyst service. **Primary provider is QuickML.** One call site in `ai/provider.py`; any other provider sits behind the same interface as a development fallback and is declared in §26.3. Building the demo on Gemini is the most likely single point of disqualification in this project. See ADR-005.

### 16.2 Pipeline

```
question
 ↓ 1 intent            case | person | district | comparison | forecast | legal | network
 ↓ 2 entity resolution surface names → canonical IDs (§6)
 ↓ 3 scope filter      apply the caller's policy scope BEFORE retrieval (§20)
 ↓ 4 tool selection    which graph queries, which features, which KB index
 ↓ 5 retrieval         canonical rows + Insights + KB chunks, ranked, token-capped
 ↓ 6 prompt assembly   versioned template from lumen_prompt_registry
 ↓ 7 generation        QuickML LLM serving, JSON-only instruction
 ↓ 8 schema validation parse to Insight; one retry; then deterministic fallback
 ↓ 9 evidence verify   DROP any ID not in the retrieved bundle      ← P2, hard filter
 ↓ 10 confidence       compute breakdown (§9) from retrieval coverage and inputs
 ↓ 11 guard            P9 deny-list over output text
 ↓ 12 audit            question, prompt version, evidence IDs, answer, latency
 → Insight(kind="summary")
```

**Step 9 is the most important line in this document.** A fabricated FIR number shown to police officers is a project-ending failure. It is a hard server-side filter, not a prompt instruction, and §17 tests it adversarially.

### 16.3 Prompt registry

Prompts are versioned `.md` files under `ai/prompts/`, hashed into `lumen_prompt_registry` at startup. Every AI insight records `prompt_version`. Changing a prompt without bumping the version is a defect.

### 16.4 Deterministic fallback

If generation is unavailable, `/ai/ask` returns a **template-assembled** insight built from retrieved evidence and existing insights, marked `method: "deterministic_fallback"`, and the UI states it plainly. Build this on day one (P12). Demos fail on network, not on logic.

### 16.5 Cost and rate control

Token budget per request; per-user rate limit at the API Gateway; identical questions served from Cache within a 15-minute window; token counts recorded per request for §25.

### 16.6 Multi-agent decomposition — T3

One orchestrator with tool selection is what is built, and it is honest. A supervisor routing to seven specialist agents is the same capability with more failure modes and a slower demo. **Documented as the scaling path; not built.** If asked: "specialisation is expressed as tool selection today; the interface is designed so each tool group can become an agent under a supervisor when latency budgets allow."

---

## §17. AI evaluation framework — T1

Without this, AI quality is an opinion. With it, you can put a number on a slide and defend it.

### 17.1 Golden set

40–60 questions in `data/eval/golden.yaml`, each with question, expected entity IDs, expected intent, and an acceptable-answer rubric. Categories: case lookup, person history, district comparison, legal ("what does 302 cover"), network ("who connects A and B"), forecast, **and unanswerable** — questions whose correct response is "the data does not support this."

### 17.2 Metrics

| Metric | Definition | Target |
|---|---|---|
| **Groundedness** | Evidence IDs present in the retrieved bundle ÷ IDs cited | 1.00 (any deviation is a bug, not a score) |
| **Hallucinated ID count** | IDs dropped by step 9 per 100 questions | 0 after filtering; tracked before filtering as a model-quality signal |
| **Retrieval coverage** | Expected IDs retrieved ÷ expected | ≥0.85 |
| **Intent accuracy** | Correct intent classification | ≥0.90 |
| **Abstention rate** | Unanswerable questions correctly declined | ≥0.90 |
| **Answer correctness** | Rubric-scored, sampled | ≥0.85 |
| **P95 latency** | End to end | ≤6 s |
| **Fallback rate** | Deterministic fallback invocations | tracked |

### 17.3 Adversarial suite

Explicitly test the failure modes that matter: prompt injection through `BriefFacts` content, requests for protected attributes, requests to predict an individual's future criminality (must be declined per §11), cross-scope retrieval attempts, and questions about non-existent FIR numbers.

### 17.4 Operation

`make eval` runs the suite against the deployed API, writes `lumen_ai_eval`, prints a scorecard. Run it before the final build and put the scorecard on a slide. **A team that can show its own AI evaluation numbers is in a different category from one that cannot.**

### 17.5 Officer feedback

Thumbs up/down plus optional reason on every AI insight, written to `lumen_event` as `InsightFeedbackGiven`. Closes the loop and demonstrates P3 concretely.

---

## §18. Decision support — T2

Recommendations are `Insight(kind="recommendation")` derived from existing insights — no new model. Each carries reasoning and, per P3, is phrased as a suggestion.

| Recommendation | Derived from |
|---|---|
| Patrol priority | Hotspots × temporal profile × district risk |
| Cases worth linking | Q7 + Q8 + signature similarity |
| Persons worth interviewing | Q2 brokers within the case's community |
| Sections potentially applicable | `CrimeHeadActSection` vs sections invoked — **suggestion for legal review only** |
| Cases needing attention | Charge delay above district median with no recent process event |
| Stations needing data support | Quality scores below the state median (§5.3) |

---

# PART III — PLATFORM

## §19. Intelligence bus and domain event catalogue — T1

Modules publish and subscribe; they never call each other.

### 19.1 Event contract (`EventContract` v1)

```json
{ "event_id":"uuid", "event_type":"CaseRegistered", "event_version":"v1",
  "occurred_at":"iso8601", "actor_id":"user|system",
  "subject":{"type":"case","id":"12345"}, "payload":{},
  "trace_id":"uuid", "classification":"CONFIDENTIAL" }
```

### 19.2 Catalogue

| Event | Emitted when | Subscribers |
|---|---|---|
| `CaseRegistered` | New `CaseMaster` row | Resolution, graph, quality, cache, insight, notify |
| `CaseUpdated` | Case fields change | Insight regeneration, cache |
| `ArrestRecorded` | New `ArrestSurrender` | Graph, timeline, insight |
| `CaseChargesheeted` | New `ChargesheetDetails` | Outcome model, timeline, insight |
| `PersonResolved` | Resolution links or splits a cluster | Graph, feature store, insight |
| `PersonMatchDisputed` | Officer reports a bad match | Resolution review queue, audit |
| `GraphProjected` | Projection completes | Cache warm, insight, metrics |
| `RiskUpdated` | District risk recomputed | Insight, notify, cache |
| `AnomalyDetected` | Anomaly crosses threshold | Insight, Mail, Push, command centre |
| `HotspotsUpdated` | Clustering completes | Cache, geo surface |
| `InsightGenerated` | Any producer emits | Lifecycle, audit |
| `InsightVerified` / `InsightApproved` / `InsightExpired` | Lifecycle transitions | UI, audit, regeneration |
| `RecommendationGenerated` | Decision support runs | UI, audit |
| `QualityFindingRaised` | Quality rule fires | Quality surface, insight, confidence |
| `EvidenceUploaded` | Asset stored in Stratus | Case workspace, audit |
| `AIQueryExecuted` | `/ai/ask` completes | Audit, evaluation, metrics |
| `InsightFeedbackGiven` | Officer rates an insight | Evaluation, audit |
| `PolicyDenied` | Authorisation denies a request | Audit, security metrics |

Every event lands in `lumen_event` (append-only) **and** on the bus. The store is the replay log; the bus is delivery.

**T1 scope:** one end-to-end path proven live — `CaseRegistered` → resolution → graph edge update → cache invalidation → insight regeneration → command centre updates. Demonstrate it by inserting a case during the demo. One path that visibly works beats seven that are wired but untested.

---

## §20. Policy engine — T1 RBAC, T2 ABAC

### 20.1 Roles

| Role | Scope | May do |
|---|---|---|
| State Analyst | All districts | Read all, run AI, run graph queries, approve insights, export |
| District SP | Own district | Everything in scope, approve insights, see unmasked identities |
| Investigating Officer | Assigned cases + own unit | Case detail, notes, AI on own cases |
| Station Officer | Own unit | Unit cases, aggregate views, masked identities |
| Auditor | All, read-only | Audit log and quality only; no case detail |

### 20.2 Mechanism

Policies live in `lumen_policy`, evaluated by a single `authorize(user, action, resource) -> Decision`. Every decision — allow **and** deny — writes to `lumen_audit` with a reason and emits `PolicyDenied` on denial.

**T1:** Catalyst Authentication, roles in `lumen_user_role`, jurisdiction scoping on every case query and every retrieval (§16.2 step 3), all access audited.
**T2:** attribute rules — juvenile records, identity masking thresholds, export permissions, k-anonymity suppression.

**Build identity masking even though it is T2.** Showing a judge that a Station Officer sees `A2 (masked)` where a District SP sees a name is a thirty-second moment proving governance is real.

---

## §21. Event store and audit — T1 partial

`lumen_event` is append-only — no updates, no deletes, enforced in the repository layer. It is the bus replay log, the source of the case lifecycle timeline, and the substrate for "what changed since yesterday."

`lumen_audit` covers *access*, not domain events: who read which case, who ran which AI query, who exported what, who was denied. P7 requires both. **T1:** authentication, AI queries, policy denials, exports. **T2:** all reads.

---

## §22. Service registry — T2

`lumen_service_registry` records every internal capability: name, capability, version, endpoint, dependencies, health state, last check. Exposed at `/api/v1/system/registry` alongside model and prompt registries.

| Service | Capability | Depends on |
|---|---|---|
| `identity` | entity resolution | data store |
| `graph` | projection + queries | data store, identity |
| `prediction` | risk, anomaly, outcome | features, data store |
| `features` | feature computation | data store, graph |
| `quality` | rule evaluation | data store |
| `ai` | orchestration | QuickML, retrieval, graph, features, KB |
| `kb` | corpus + retrieval | QuickML, stratus |
| `policy` | authorisation | authentication |
| `bus` | event publication | signals |

Small subsystem, disproportionate maturity signal, and it makes §24's dependency table computable rather than hand-written.

---

## §23. Resource manager — T2

Police systems do not have infinite compute, and a demo does not have infinite latency budget. Grounded in Catalyst services rather than a bespoke scheduler.

| Concern | Mechanism |
|---|---|
| Request priority | Interactive reads > AI generation > batch. Batch jobs never run in the request path |
| Scheduling | Catalyst Cron; heavy jobs staggered, never concurrent with the demo window |
| Caching | Catalyst Cache with a documented TTL per payload: overview 60 s, hotspots 5 min, ego graphs 15 min, district risk 1 h, AI answers 15 min |
| Rate limiting | API Gateway throttling; `/ai/ask` limited per user per minute |
| Batch queue | Precompute stages are idempotent and checkpointed, so a partial run resumes rather than restarts |
| Budget | Token budget per AI request; recorded per call; a daily ceiling degrades to the deterministic fallback rather than failing |
| Degradation ladder | Full → cached → precomputed-only → deterministic → read-only (§24.2) |

---

## §24. Failure strategy — T1

Production systems are judged by failure behaviour. So are demos.

### 24.1 Dependency failure matrix

| Dependency | Failure mode | Detection | Response | User sees |
|---|---|---|---|---|
| Data Store | Unavailable / slow | Health probe, timeout 3 s | Serve cached payloads; read-only mode | Banner: "Serving cached data from HH:MM" |
| Catalyst Cache | Unavailable | Timeout 200 ms | Bypass to store | Nothing (slower) |
| QuickML LLM | Unavailable / timeout | Timeout 15 s, circuit breaker at 3 failures/60 s | Deterministic fallback (§16.4) | "AI narrative unavailable — showing evidence-based summary" |
| QuickML RAG | Unavailable | Timeout | Retrieval falls back to Data Store full-text | Limitation line added to the insight |
| Graph backend | Unavailable | Health probe | Serve last projection from `lumen_graph_edge` / NoSQL snapshot | "Network as of HH:MM" |
| Signals | Delayed | Lag metric | Precompute cron catches up; insights marked stale | Staleness timestamp on every card |
| Zia AutoML | Unavailable | Timeout | Local scikit-learn model | `lineage.method` records the fallback |
| Stratus | Unavailable | Timeout | Evidence list renders metadata without thumbnails | "Attachment temporarily unavailable" |
| Map tiles | Unavailable | Tile error | Choropleth renders on cached GeoJSON without basemap | Basemap absent, data intact |

### 24.2 Degradation ladder

```
L0 FULL          all services healthy
L1 CACHED        live queries fail → cached payloads, staleness shown
L2 PRECOMPUTED   cache cold → precomputed tables only; no ad-hoc filtering
L3 DETERMINISTIC LLM down → template insights from evidence
L4 READ-ONLY     store degraded → last snapshot, writes rejected with a clear message
```

The current level is exposed at `/system/health` and rendered as a small status pill in the app shell. **A visible degradation state is a feature.** Judges who see "L1 — serving cached data from 14:32" learn more about your engineering than any diagram.

### 24.3 Rules

1. Every outbound call has a timeout. No unbounded waits.
2. Circuit breakers on QuickML and the graph backend: 3 failures in 60 s opens for 120 s, then half-open.
3. Retries only on idempotent reads: 2 attempts, exponential backoff with jitter. Never retry generation blindly — it doubles cost and latency.
4. Precompute is idempotent and checkpointed.
5. **Never fabricate to fill a gap.** Missing data renders as "not available", never as zero, never as an interpolated value.
6. Every degradation emits an event and is audited.

---

## §25. Observability — T2

`/api/v1/system/health` (per-dependency state, degradation level) and `/api/v1/system/metrics`: latency percentiles per route, cache hit rate, precompute duration and last run, graph query timings, LLM latency and token counts, insight counts by kind and lifecycle state, fallback invocations, policy denials, quality score trend, AI evaluation scorecard. Catalyst monitoring and logs cover platform health. The metrics page doubles as a judge-facing screen.

---

## §26. Catalyst architecture

### 26.1 Complete service map — all 26 capabilities

Honesty rule: a listed service is used and demonstrable. Rows marked *Not applicable* say so with a reason. An unused service claimed as used is worse than an unused service.

| # | Capability | Service | LUMEN usage | Tier |
|---|---|---|---|---|
| 1 | Serverless functions | **Functions** | Event functions on Signals: resolution trigger, cache invalidation, notification dispatch, quality rule runs | T1 |
| 2 | Docker image deployment | **AppSail (custom OCI)** | Fallback runtime if ML/geo dependencies exceed the managed runtime. linux/amd64 | T2 |
| 3 | Managed runtime web app | **AppSail (managed)** | Primary FastAPI service | T1 |
| 4 | Frontend / SPA | **Web Client Hosting** | React SPA build output | T1 |
| 5 | Custom domain + SSL | **Domain Mappings** | `lumen.<domain>` if available | T2 |
| 6 | Relational database | **Data Store** | All 27 canonical + all `lumen_` tables | T1 |
| 7 | Unstructured data | **NoSQL** | Graph adjacency snapshots, insight payloads, prompt/response logs | T1 |
| 8 | Object storage | **Stratus** | Evidence assets, exported briefings, model artefacts, KB source documents | T1 |
| 9 | Cache | **Cache** | Overview, hotspots, ego graphs, district risk, AI answers — TTLs in §23 | T1 |
| 10 | Full-text search | **Data Store full-text** | Search over `BriefFacts`; also the RAG fallback path (§24.1) | T1 |
| 11 | Text LLMs / RAG | **QuickML (LLM serving, RAG)** | Generation step and the knowledge base (§15) | T1 |
| 12 | No-code ML pipelines | **QuickML** | Hotspot and anomaly pipelines as managed pipelines | T2 |
| 13 | Automated tabular training | **Zia AutoML** | District risk classifier; case outcome classifier | T1 |
| 14 | OCR / text analytics | **Zia Services** | OCR on scanned FIR/chargesheet uploads into the evidence pipeline; entity extraction from `BriefFacts` | T2 |
| 15 | Voice services | **Zia Services** | Speech-to-text into the Intelligence Console; Kannada→English translation of BriefFacts | T2 |
| 16 | PDF / headless browser | **SmartBrowz** | **Case Intelligence Briefing PDF** — dossier with insights, network figure, timeline, evidence, watermarked per §4.3 | T2 |
| 17 | User auth | **Authentication** | Replaces bespoke JWT entirely | T1 |
| 18 | API routing / throttling | **API Gateway** | Fronts AppSail, edge auth, rate limits `/ai/ask` | T1 |
| 19 | OAuth for Zoho / 3rd party | **Connections** | *Not applicable* — LUMEN integrates no external OAuth service. Stated rather than padded | — |
| 20 | Scheduled jobs | **Cron / Job Scheduling** | `jobs/precompute.py`: resolution, projection, metrics, hotspots, anomalies, quality | T1 |
| 21 | React to in-project events | **Signals + Event Functions** | The intelligence bus (§19) | T1 |
| 22 | Cross-app event bus | **Signals** | Routes `AnomalyDetected` to notification functions | T1 |
| 23 | Multi-step orchestration | **Circuits** | The AI orchestrator pipeline (§16.2) — genuinely branching and parallel | T2 |
| 24 | Transactional email | **Mail** | Anomaly alert to the district officer; briefing delivery | T2 |
| 25 | Push notifications | **Push Notifications** | High-risk alerts to officer devices | T2 |
| 26 | CI/CD | **Pipelines** | Build and deploy client + AppSail on push; runs the §17 eval suite | T2 |

### 26.2 Data Store migration notes

- Types map: `INT`→number, `VARCHAR`/`TEXT`→text, `DATE`/`TIMESTAMP`→datetime, `BOOLEAN`/`BIT`→boolean. **Verify decimal handling for `latitude`/`longitude` before seeding** — never store coordinates float-rounded; if a decimal type is unavailable, store as text and parse server-side.
- Data Store enforces relationships less strictly than PostgreSQL, so referential integrity also lives in `db/repositories/` — every write validates parents.
- Seed via bulk import, not row-by-row.
- A `DATABASE_URL` switch runs PostgreSQL locally and Data Store deployed, behind one repository interface. **Both paths pass the same repository test suite.**

### 26.3 P6 exception register

| Dependency | Catalyst equivalent | Reason |
|---|---|---|
| NetworkX (in-process) | None | No graph service exists in Catalyst |
| scikit-learn (local) | Zia AutoML / QuickML | Deterministic fallback path per P12; Zia AutoML is the primary trainer |
| Leaflet / OSM tiles | None | No map tile service in Catalyst |
| Non-Catalyst LLM | QuickML | Local development only. Never the deployed path |

Anything not in this table is a defect.

---

## §27. Deployment mechanics

- `catalyst.json` at the project root configures the whole project directory, including the `client` and `functions` sources; AppSail configuration is added there when the service is initialised.
- Initialising an AppSail service creates `app-config.json` in the app's source directory — the only AppSail-specific file there — holding the startup command, environment variables and memory. Edit it before deploying.
- Bind to the platform-provided port via `X_ZOHO_CATALYST_LISTEN_PORT`; port 9000 is the default, and if the port is not set in code it must match the startup command.
- **Write permissions are restricted in the working directory at runtime** — anything written during execution goes to the OS temp directory. This affects `MPLCONFIGDIR`, joblib, embedding caches, and any artefact written at import time. Load model artefacts read-only from Stratus or the bundle.
- Managed runtimes cover specific Java, Node.js and Python versions; a custom OCI image is the alternative and must be built for **linux/amd64**.
- Ensure deployable build files are present in the directory you deploy from.

```
# api/app-config.json startup command
uvicorn main:app --host 0.0.0.0 --port ${X_ZOHO_CATALYST_LISTEN_PORT}
```
```python
# main.py
port = int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", 9000))
```

---

# PART IV — PRODUCT

## §28. Repository structure

```
lumen/
├── catalyst.json · README.md · Makefile · .env.example
│
├── client/                                  # → Web Client Hosting
│   ├── client-package.json
│   ├── app/src/
│   │   ├── main.tsx · app/{router,providers}.tsx
│   │   ├── app/shell/                       # AppShell, CommandBar, LeftRail,
│   │   │                                    # RoleBadge, DegradationPill
│   │   ├── design/{tokens.css,motion.ts} · design/primitives/
│   │   ├── api/{client.ts,types.ts}  api/hooks/
│   │   ├── components/
│   │   │   ├── insight/    # InsightCard, FactorBars, ConfidenceBreakdown,
│   │   │   │               # EvidenceList, LineagePanel, LimitationsNote, TrustBadge
│   │   │   ├── graph/ map/ timeline/ charts/
│   │   │   ├── identity/   # ResolvedIdentity, MatchEvidence, ReportMatch
│   │   │   └── quality/    # QualityScore, FindingList
│   │   └── features/{command-center,geo,case,person,network,intelligence,
│   │                  predictions,quality}/
│   └── dist/
│
├── functions/                               # → Catalyst Functions
│   ├── on_case_registered/ on_anomaly_detected/
│   └── on_graph_projected/ on_quality_finding/
│
├── api/                                     # → AppSail
│   ├── app-config.json · requirements.txt · main.py
│   └── lumen/
│       ├── config.py
│       ├── contracts/                       # §7 — the only cross-boundary shapes
│       ├── semantics/{entities.py,render.py}# §2
│       ├── db/{session.py,datastore.py}
│       ├── db/models/ · db/repositories/    # the ONLY place table names appear
│       ├── services/
│       ├── identity/                        # §6
│       ├── quality/{rules.py,engine.py,scoring.py}   # §5
│       ├── governance/{classification.py,masking.py,retention.py}  # §4
│       ├── intelligence/
│       │   ├── engine.py risk.py hotspots.py anomaly.py linkage.py outcome.py
│       │   ├── explain.py counterfactual.py confidence.py lifecycle.py
│       │   ├── guards.py                    # P9 deny-list — enforced + tested
│       │   └── features.py                  # §12
│       ├── graph/{backend.py,projection.py,queries.py,metrics.py}
│       ├── kb/{ingest.py,retrieve.py}       # §15
│       ├── ai/
│       │   ├── orchestrator.py intent.py retriever.py toolsel.py
│       │   ├── envelope.py provider.py      # the ONLY LLM call site
│       │   ├── eval/{runner.py,rubric.py}   # §17
│       │   └── prompts/*.md
│       ├── bus/{signals.py,events.py,catalog.py}
│       ├── policy/{engine.py,roles.py}
│       ├── registry/{models.py,prompts.py,services.py}
│       ├── resilience/{breaker.py,timeouts.py,degradation.py}     # §24
│       ├── observability/{metrics.py,health.py}
│       ├── api/{deps.py,routers/}
│       └── jobs/{seed.py,precompute.py,resolve.py,quality.py,kb_ingest.py}
│
├── data/{schema.sql, seeds/, eval/golden.yaml}
└── docs/{ARCHITECTURE.md, ADR/, SCHEMA_NOTES.md, GOVERNANCE.md,
        DEMO_SCRIPT.md, JUDGE_QA.md, CATALYST_MAP.md, RUNBOOK.md}
```

### Structural rules (enforced in review)

1. Routers: parse → one service call → return contract. Over 30 lines means logic leaked in.
2. Services contain no SQL. Repositories contain no business rules.
3. **Table and column names appear only in `db/repositories/` and `db/models/`.** Everywhere else uses the semantic vocabulary (§2).
4. `intelligence/` is the only producer of `Insight`.
5. `ai/provider.py` is the only file that calls an LLM.
6. `bus/signals.py` is the only publisher.
7. `policy/engine.py` is the only authoriser.
8. `contracts/` holds the only shapes that cross module boundaries.
9. The frontend computes nothing — no scoring, ranking or clustering in the browser.
10. Nothing reads a P9 column outside the governed display path in `governance/masking.py`.

---

## §29. API contract

Base `/api/v1`. Envelope on every response:

```json
{ "data": {}, "meta": {"generated_at":"","method":"","model_version":"",
  "contract_version":"v1","cached":false,"degradation_level":"L0","trace_id":""},
  "error": null }
```

### 29.1 Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/overview` | Command centre: counts, trend, risk bands, anomalies, top network figures, quality score |
| GET | `/geo/districts` · `/geo/hotspots` · `/geo/units/{id}` · `/geo/delay` | Choropleth, clusters, drill-down, reporting-delay layer |
| GET | `/cases` | Filters: head, sub-head, gravity, status, category, district, unit, date range, `q` full-text |
| GET | `/cases/{id}` | Full aggregate in semantic form |
| GET | `/cases/{id}/timeline` | Derived lifecycle with gaps and district benchmarks |
| GET | `/cases/{id}/insights` · `/linked` · `/graph` | Insights, linked cases, investigation board payload |
| POST | `/cases/{id}/briefing` | SmartBrowz PDF → Stratus URL (T2) |
| GET | `/persons/{id}` · `/persons/{id}/network` | Dossier with resolution evidence; ego graph |
| POST | `/persons/{id}/dispute` | Report an incorrect identity match |
| GET | `/network/query/{q1..q10}` | Named queries — insight + graph |
| GET | `/insights` · `/insights/{id}/lineage` | Feed; lineage panel |
| POST | `/insights/{id}/approve` · `/feedback` | Lifecycle approval; officer feedback |
| GET | `/predictions/districts` · `/predictions/outcome/{case_id}` | Risk bands; outcome probability |
| GET | `/anomalies` · `/recommendations` | Ranked anomalies; decision support |
| GET | `/quality/scores` · `/quality/findings` | Quality surface |
| POST | `/ai/ask` | Evidence-grounded report (§16.2) |
| GET | `/system/health` · `/metrics` · `/registry` · `/eval` | Ops and judge-facing surfaces |
| GET | `/audit` | Auditor role only |

### 29.2 Rules

Contracts are **additive only** within a major version. Never change a field the frontend already reads. Every list endpoint returns `total` and accepts `limit`/`offset`.

### 29.3 Errors

```json
{"data":null,"meta":{...},
 "error":{"code":"SCOPE_DENIED","message":"Outside your jurisdiction scope",
          "trace_id":"…","retryable":false}}
```

Codes: `VALIDATION_FAILED` · `NOT_FOUND` · `SCOPE_DENIED` · `RATE_LIMITED` · `DEPENDENCY_UNAVAILABLE` · `DEGRADED_RESULT` · `INTERNAL`. Errors explain what happened and what to do — never a bare 500.

### 29.4 Versioning policy

`/api/v1` is the current major. A breaking change introduces `/api/v2`, both served in parallel; `v1` responses gain `meta.deprecated: true` with a sunset date. Minor additions never bump the major. Clients pin `contract_version` and log a warning on mismatch.

---

## §30. Frontend specification

### 30.1 Information architecture

```
Command Center → Geo Intelligence → Case Workspace → Person Dossier
                                          ↕                ↕
                                   Criminal Network ←───────┘
        Intelligence Console    Forecasts    Data Quality
```

Navigation is **drill-in, not sidebar-hop**. Every entity reference anywhere is a link to that entity's workspace. A judge should click continuously for two minutes without touching the nav rail.

### 30.2 Command Center (`/`)

Karnataka choropleth by risk band, districts fading in by ascending risk over ~600 ms — one orchestrated moment. Four counters (period cases, active anomalies, high-band districts, network-central persons), each navigating to a filtered view. Live insight feed. 12-month trend per top-5 crime head. Degradation pill and statewide quality score in the shell. Empty state: "No anomalies detected in the current window" — never a bare spinner.

### 30.3 Geo Intelligence (`/geo`)

Four real query levels: **State → District → Station → Cluster**. Layers: incident points, DBSCAN density, risk choropleth, station catchment, reporting-delay. Time scrubber re-queries on release, not on drag. Cluster click opens a peek panel; case click navigates on.

### 30.4 Case Workspace (`/case/:id`) — hero surface

```
┌─ header ───────────────────────────────────────────────────────────┐
│ CrimeNo decoder · crime type · gravity · status · trust badge       │
│ registered <date> at <station>, <district> · IO: <officer>          │
├──────────────┬───────────────────────────────┬─────────────────────┤
│ ENTITIES     │ INVESTIGATION BOARD           │ INTELLIGENCE        │
│ Victims      │ case ⇄ resolved persons ⇄     │ Risk insight        │
│ Accused A1…  │ arrests ⇄ officers ⇄          │  ↳ factors          │
│ Complainants │ linked cases                  │  ↳ confidence parts │
│ Charges      │                               │  ↳ counterfactuals  │
│ Court        │ ── timeline rail, to scale ── │  ↳ evidence chips   │
│ Evidence     │ incident→info→registered→     │  ↳ limitations      │
│ Notes        │ arrest→chargesheet→court      │  ↳ lineage panel    │
│ Quality      │ (district median reference)   │ Linked cases        │
│  findings    │                               │ Signature family    │
│              │                               │ AI case summary     │
└──────────────┴───────────────────────────────┴─────────────────────┘
```

Node expansion fetches 1-hop neighbours and animates them in — the discovery moment. The timeline draws gaps to scale so a nine-month charge delay is *visible*, against the district median. Every score expands to factors and its confidence breakdown. No exceptions.

### 30.5 Person Dossier (`/person/:id`)

Resolution banner first: *"Resolved identity · confidence 0.91 · 4 linked case records · see matching evidence · report incorrect match."* Then cases, arrest history, associates ranked by shared cases, districts of operation, network metrics in plain language. Candidate matches below threshold in a clearly separated block.

### 30.6 Criminal Network (`/network`)

Search seeds the graph. Ten named queries as a labelled rail, each with the question it answers. Results render as **insight plus graph**. Communities as coloured hulls, district labels on hulls that span districts. Every card carries its limitations line.

### 30.7 Intelligence Console (`/intelligence`)

Not a chat window. A question box with suggested queries; answers render as a **report card**: answer, confidence breakdown, factor bars, clickable evidence chips, tools and queries executed, limitations, lineage disclosure, feedback control. The twelve pipeline stages show progress while it works — this makes orchestration visible rather than asserted.

### 30.8 Forecasts (`/predictions`)

Risk table by band; rows expand to factors, counterfactuals, fitted series, and a caveat line stating the data window.

### 30.9 Data Quality (`/quality`)

District quality scores across the six dimensions, trend, top rules firing, and stations that would benefit from data-entry support. Framed as an administrative product, not a defect list.

### 30.10 Motion

Framer Motion for state (180–240 ms, easeOut). Orchestrated sequences at exactly three moments: command-centre map load, map zoom between levels, node expansion. `prefers-reduced-motion` respected globally. Graph layouts settle in ≤1.5 s or are precomputed. Nothing animates while a judge is reading data.

---

## §31. Design system

### 31.1 Tokens

```css
:root{
  --bg-void:#060D16; --bg-panel:#0D1826; --bg-raised:#14243A; --line:#1E3350;
  --ink-primary:#E6EEF8; --ink-muted:#8CA3BF; --ink-faint:#55708F;
  --signal:#35E0D4;
  --risk-critical:#FF5A5A; --risk-high:#FF9548; --risk-medium:#FFD166; --risk-low:#4ADE9B;
  --confidence-high:#4ADE9B; --confidence-med:#FFD166; --confidence-low:#8CA3BF;
  --state-degraded:#FF9548;
  --font-display:"Space Grotesk",system-ui,sans-serif;
  --font-body:"Inter",system-ui,sans-serif;
  --font-mono:"JetBrains Mono",ui-monospace,monospace;
  --radius:4px; --space:8px;
}
```

### 31.2 Rules

`--signal` means *interactive or live* and is never decorative. Risk colours are only for risk. One accent per screen region. Borders 1px `--line`; shadows only on floating panels. Radius 4px everywhere — government software is not rounded. Masked values render in `--ink-faint` with a lock affordance, never as blank space.

### 31.3 Signature device — the CrimeNo decoder

```
1 · 0443 · 0006 · 2026 · 00001
▔   ▔▔▔▔   ▔▔▔▔   ▔▔▔▔   ▔▔▔▔▔
FIR  Distr  Unit   Year   Serial
```

Segmented mono, each segment labelled on hover and clickable as a filter. Derived from the real schema, no other team will have it, doubles as navigation, and proves within five seconds that the schema was read. It also validates: a mismatch against `Unit.DistrictID` fires quality rule `Q04` and renders a warning glyph inline. Used in the case header and search results only.

---

## §32. Deterministic demo data

`jobs/seed.py`, fixed random seed, guaranteeing by construction:

1. A district with a visually obvious hotspot.
2. A resolved community of ≥8 persons spanning ≥2 districts with exactly one high-betweenness broker.
3. ≥3 persons appearing in ≥3 cases each under **name variants** — so resolution visibly does work rather than matching identical strings.
4. Two cases sharing an act-section signature, different districts, months apart.
5. A full-lifecycle case with a conspicuous charge delay.
6. A district-week ≥3σ above baseline.
7. Coordinates inside real Karnataka boundaries; `CrimeNo` values correctly encoding district and unit.
8. **One deliberate `CrimeNo`/Unit mismatch** so `Q04` has something to catch on stage.
9. **One case with missing coordinates and one with an impossible timestamp** so `Q01` and `Q05` are demonstrable.
10. A realistic `cstype` A/B/C distribution for the outcome model.
11. One low-confidence identity candidate (0.66–0.75) so the candidate-match UI is demonstrable.
12. At least five cases where scope masking differs between Station Officer and District SP.

Record demo-path entity IDs in `docs/DEMO_SCRIPT.md`. Re-run the seed and confirm the same IDs before the final build.

---

# PART V — EXECUTION

## §33. Build sequence

One session per row: *"Implement §X of LUMEN_MASTER_SPEC_V3.md. Do not invent features, do not change contracts, do not modify files outside the listed paths."*

| # | Session | § | Done when |
|---|---|---|---|
| 1 | Repo restructure; port working endpoints unchanged in behaviour | 28 | Old package deleted, prior endpoints still answer |
| 2 | Contracts + semantic layer + canonical schema + repositories + Data Store adapter | 2, 3, 7, 26.2 | Same test suite passes on PostgreSQL and Data Store; no table name outside `db/` |
| 3 | **Catalyst skeleton: AppSail + Web Client Hosting + API Gateway + Authentication** | 27, 20 | Two live URLs, login works. **Nothing else starts until green** |
| 4 | Governance register + masking + P9 guards | 4 | CI fails if a denied column reaches a model input |
| 5 | Seed job | 32 | All twelve guarantees verified by tests |
| 6 | Data quality engine + scoring + quality surface data | 5 | All 18 rules fire correctly against the seed |
| 7 | Entity resolution | 6 | Name-variant persons resolve with confidence and match evidence |
| 8 | Insight + explainability + confidence model + lifecycle + lineage | 8, 9, 10 | All seven invariants enforced in CI |
| 9 | Graph projection + ten queries + metrics | 14 | All ten answer in <400 ms from precomputed tables |
| 10 | Prediction engine | 13 | Insights carry factors, counterfactuals, limitations |
| 11 | Resilience: timeouts, breakers, degradation ladder, health | 24 | Killing QuickML degrades to L3 with a visible banner |
| 12 | Bus + domain events + precompute on Cron + one live end-to-end path | 19 | Inserting a case visibly updates the network |
| 13 | Knowledge base ingestion + scope-filtered retrieval | 15 | Legal and case indexes separate; scope filter tested |
| 14 | AI orchestrator on QuickML + deterministic fallback | 16 | Injected fake IDs are dropped — tested explicitly |
| 15 | AI evaluation framework + golden set + adversarial suite | 17 | `make eval` prints a scorecard |
| 16 | Design system + shell + InsightCard family + degradation pill | 31, 30 | Zero hard-coded colours; CrimeNo decoder working |
| 17 | Case Workspace: investigation board + scaled timeline | 30.4 | Whole case renders from one aggregate call |
| 18 | Command Center + Geo Intelligence | 30.2, 30.3 | Four-level drill-down |
| 19 | Criminal Network + Person Dossier | 30.5, 30.6 | Query rail returns insight + graph + limitations |
| 20 | Intelligence Console + Quality surface + Forecasts | 30.7–30.9 | Pipeline stages visible while running |
| 21 | Catalyst adoption: Cache, NoSQL, Stratus, full-text, Cron | 26.1 | Bespoke equivalents removed |
| 22 | Registries, observability, audit, ABAC scoping | 20–22, 25 | `/system/*` live; denials audited |
| 23 | T2 accelerators: SmartBrowz briefing, Mail/Push, Zia AutoML, Circuits, OCR/voice | 26.1 | Each demonstrable or dropped — no half-wired services |
| 24 | ADRs, runbook, governance doc, judge Q&A | 35, 36 | `docs/` complete |
| 25 | Demo hardening: reseed and verify, empty and error states, reduced motion, degraded-path rehearsal | 32, 34 | Full script runs twice with no reload, and once with QuickML disabled |

**Critical path if execution slips:** 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 14, 16, 17, 25. That is a deployed, Catalyst-native, governed, schema-aligned platform with entity resolution, a real graph, explainable predictions, a grounded AI orchestrator, resilience, and a strong hero surface.

**Never do:** more CRUD pages, more admin screens, framework migration, features outside §30, or wiring a Catalyst service you cannot demonstrate.

---

## §34. Demo script (six minutes)

1. **Command Center.** "Karnataka, live. Districts by current risk band. Three anomalies active. Statewide data quality 0.87." *(15s)*
2. **Highest-risk district.** Zoom; hotspots resolve. "DBSCAN over incident coordinates, not a bounding box." *(20s)*
3. **Hotspot → case.** Workspace loads whole. *(20s)*
4. **CrimeNo decoder.** "This code encodes category, district, unit, year, serial. Every segment filters. And this one" — the seeded mismatch — "doesn't match its registering unit, so the quality engine flagged it automatically." *(25s)*
5. **Expand an accused.** "The supplied schema has no person master. A2 appears in four case records under three spellings. We resolve that — 0.91 confidence, and here is the evidence for the match. An officer can dispute it." *(45s)* ← **the strongest 45 seconds you have**
6. **Risk insight → factors → confidence breakdown → lineage.** "Confidence isn't a number we chose. It's evidence quality × model confidence × data completeness × identity confidence × graph confidence. This one is limited by identity match at 0.79 — and it says so." *(40s)*
7. **Network → hidden intermediary (Q2).** "These groups look unconnected. This person is the only path between them." Then the caveat on the card: "co-accusal reflects charging decisions, not adjudicated guilt." *(40s)*
8. **Intelligence Console.** Watch the twelve stages progress. "The model never touches the database. It receives a scope-filtered evidence bundle, and any record ID it produces that wasn't in that bundle is discarded before you see it. Here is our evaluation scorecard for that." *(50s)*
9. **Switch role to Station Officer.** Same case, names masked. "Governance is enforced at query time, not in the UI." *(20s)*
10. **Insert a case live.** Anomaly count ticks; network updates. "Catalyst Signals — the system updates its own understanding." *(25s)*
11. **Disable the LLM.** Console degrades to the evidence-based summary; the pill reads L3. "Production systems are judged by how they fail." *(20s)*
12. **Catalyst map, ten seconds.** Services used, and why graph analytics runs in-process. *(15s)*

Rehearse until it runs twice without a reload, and once with QuickML disabled. Build features in this order.

---

## §35. Architecture decision records

Full records in `docs/ADR/`. Summary:

| ADR | Decision | Alternatives | Rationale |
|---|---|---|---|
| **001** | Graph analytics in-process (NetworkX) over Data Store + NoSQL, graph DB optional | Neo4j Aura, ArangoDB | Catalyst has no graph service; an external graph DB is an availability risk in a Catalyst-mandated deployment. In-process removes the dependency and keeps queries under the latency budget. Backend is swappable |
| **002** | Adopt the supplied KSP ERD verbatim as canonical | Keep the prototype's ~61 models; hybrid | Provenance and trust; and 27 well-defined tables are migratable to Data Store where 61 tangled ones are not |
| **003** | Build entity resolution rather than treating `Accused` as identity | Join on name; ignore cross-case identity | The schema has no person master. Without resolution the network graph has no edge longer than one case, and naive name joins are defamatory for common names |
| **004** | Explainability as a data structure (`Insight`), not a UI feature | Explanation strings from the model | Structure makes explanation testable, cacheable and impossible to omit. Tree ensembles chosen over deep learning for the same reason |
| **005** | QuickML as the primary LLM provider | Gemini, OpenAI | The organisers require Catalyst services where equivalents exist; a third-party LLM is the clearest substitution risk in the build |
| **006** | Modular monolith on AppSail, not microservices | Functions-per-domain, containers | One deployable, shared memory for graph and ML, simplest path to a working Catalyst deployment. Module boundaries are enforced by contracts (§7), so decomposition later is mechanical |
| **007** | Confidence as a decomposed product, not a scalar | Model probability alone | A chain of inferences is as strong as its weakest link. Decomposition lets the UI name the limiting factor honestly |
| **008** | Data quality as an intelligence product, not a maintenance chore | Silent cleaning; ignore | Cleaning silently destroys evidence about how the data was produced. Surfacing quality creates an administrative product and feeds confidence |
| **009** | Batch precompute over on-demand analytics | Compute per request | Centrality and clustering cannot meet an interactive latency budget. Precomputed tables also survive dependency failure (§24) |
| **010** | Protected attributes stored but never analysed | Drop them; use them as features | Dropping breaks canonical fidelity; using them encodes bias into policing. Store, never analyse, enforce in CI |

---

## §36. Documented, not built (T3)

**36.1 District digital twin** — live district state fusing crime, patrol, resources and forecast. Requires patrol and resource feeds that do not exist in the supplied schema. **Blocked on data availability, not engineering** — say exactly that.

**36.2 Plugin SDK and intelligence marketplace** — capability packs (cyber, women's safety, narcotics, missing persons) registering through the interface implied by P8 and §7. The contract layer is designed today; no packs are built.

**36.3 Research extensions** — graph neural networks over the knowledge graph, federated learning across state clusters with differential privacy, multimodal evidence (CCTV, video, satellite), digital evidence chain of custody.

**36.4 Multi-state federation** — state-owned clusters with a metadata-only national aggregation layer, cross-state linkage on anonymised hashes. Legal architecture, not only technical.

---

## §37. Freeze and change control

**The architecture is frozen at v3.** From here, improvement comes from execution, tests, documentation and demonstration — not from new subsystems. Every further concept adds surface area for inconsistency and costs implementation fidelity.

A change is admissible only if it: (1) fixes a contradiction in this document, (2) removes a subsystem, or (3) is required to make a T1 item work. Anything else goes to §36 as roadmap.

Record every change in `docs/ADR/` with date, reason, and the sections affected. If the implementer finds a contradiction, it is reported and resolved here — not resolved silently in code.

---

## §38. Judge Q&A

- **Why the official ERD?** Provenance and trust — and 27 defined tables are migratable to Data Store where a parallel 61-model schema is not.
- **What did you find in the schema that we didn't tell you?** There is no person master; `Accused` is per-case. Everything about repeat offenders depends on inferring identity, so we built resolution with explicit confidence rather than pretending name matches are facts. We also found eight structural inconsistencies, listed in `SCHEMA_NOTES.md`.
- **How do you stop hallucination?** Schema validation, then a server-side filter that drops any entity ID not in the retrieved bundle. We measure it: groundedness, hallucinated-ID count, and abstention rate on an adversarial golden set.
- **How is confidence computed?** Five components, multiplied. The UI names the limiting one.
- **You store caste and religion — do you use them?** No. Stored because the canonical schema defines them; excluded from every model, filter, chart and prompt by an enforced deny-list, with a CI test that fails the build.
- **What happens when a dependency fails?** A five-level degradation ladder, visible in the UI. We can demonstrate it — [disable the LLM].
- **How did you use Catalyst?** Walk §26.1. Name the one gap — no graph service — and explain the in-process decision.
- **What could go wrong in production?** Entity-resolution false positives, model drift, and coordinate quality in `CaseMaster`. Each has a stated mitigation and a monitoring signal.
- **What is not real yet?** The dataset is seeded, forecasts are fitted on a limited window, and everything in §36 is designed, not built. Said before being asked.