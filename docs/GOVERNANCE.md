# LUMEN v3 — Data Governance

Sourced from LUMEN_MASTER_SPEC_V3 §4 (governance), §9 (confidence), §11 (trust
framework). This document records the governance model as specified and
implemented; it does not add rules the specification does not define.

Governance is Tier 1 for declaration, Tier 2 for enforcement automation (§1).
"This is police data. A judge from a state police department will care more
about who can see a victim's name than about your animation curve." (§4)

---

## 1. Classification scheme (§4.1)

| Class | Definition | Examples | Handling |
|---|---|---|---|
| **PUBLIC** | Safe for citizen-facing display | District names, act/section descriptions, aggregate counts | No masking |
| **INTERNAL** | Police-wide operational data | Crime heads, unit names, hotspot clusters, district risk | Any authenticated role |
| **CONFIDENTIAL** | Case-identifying data | `BriefFacts`, `CrimeNo`, case coordinates, officer identity | Role + jurisdiction scope |
| **RESTRICTED** | Person-identifying and protected attributes | Names of victims, accused, complainants; `CasteID`, `ReligionID`, ages, `KGID` | Role + scope + masking below threshold; every access audited individually |

Ascending sensitivity order — PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED —
is implemented in `governance/classification.py` and used for §4.3 rule 2
(derived data inherits the highest classification of its inputs).

---

## 2. Asset register (§4.2) — `lumen_data_asset`

Declared for every table named in §4.2:

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

The register is `governance/classification.py`. Canonical tables not covered by
an explicit §4.2 row or the lookup catch-all (`ActSectionAssociation`,
`ArrestSurrender`, `inv_arrestsurrenderaccused`, `ChargesheetDetails`) have no
declared classification; the code raises rather than inventing one.

---

## 3. Governance rules (§4.3)

1. **LUMEN never deletes canonical records.** It is an analytical overlay, not
   a system of record. Retention applies to `lumen_` tables only.
2. **Derived data inherits the highest classification of its inputs.** An
   insight built from `Victim` is RESTRICTED (§8 invariant 6).
3. **Aggregates below k=5 are suppressed.** A district-week count of 2 with a
   caste breakdown is re-identification. The UI shows "fewer than 5 —
   suppressed." (`governance/masking.suppress_small_aggregate`, threshold 5.)
4. **Encryption:** at rest via the platform store; in transit TLS. Evidence
   assets in Stratus are classified at upload.
5. **Export is a governed action** — role-gated, individually audited,
   watermarked with the requesting user and timestamp (the Case Intelligence
   Briefing carries this watermark, §26.1 #16).
6. **P9 enforcement is structural**, not a convention (see §5 below).

---

## 4. Roles and access (§20)

| Role | Scope | May do |
|---|---|---|
| State Analyst | All districts | Read all, run AI, run graph queries, approve insights, export |
| District SP | Own district | Everything in scope, approve insights, see unmasked identities |
| Investigating Officer | Assigned cases + own unit | Case detail, notes, AI on own cases |
| Station Officer | Own unit | Unit cases, aggregate views, masked identities |
| Auditor | All, read-only | Audit log and quality only; no case detail |

Authorisation is a single `authorize(user, action, resource) -> Decision`
(`policy/engine.py`, the only authoriser, §28 rule 7). Every decision — allow
and deny — writes to `lumen_audit`; a denial also emits `PolicyDenied` (§20.2).
Jurisdiction scoping is applied on every case query and every retrieval (§16.2
step 3). Identity masking is built even though ABAC is T2 (§20.2), so a Station
Officer sees `A2 (masked)` where a District SP sees a name.

---

## 5. P9 — protected attributes are never analytical inputs

Caste, religion, blood group, disability status are stored because the
canonical schema defines them (ADR-010) and excluded from every feature,
filter, chart, prompt, and map layer. The denied columns are exactly those the
schema marks `-- P9`:

```
Employee.BloodGroupID
Employee.PhysicallyChallenged
ComplainantDetails.ReligionID
ComplainantDetails.CasteID
```

Enforcement is **structural** (§4.3 rule 6): `intelligence/guards.py` holds the
deny-list and the single `assert_no_denied_columns` gate every
feature/prompt/chart builder passes through. `test_p9_guards.py` fails the build
if a denied column reaches a model input. `Insight` invariant 4 (§8) applies the
same rule to explanation text — no `Factor.label` references a P9 attribute.
Nothing reads a P9 column outside the governed display path in
`governance/masking.py` (§28 rule 10).

---

## 6. Confidence and trust (§9, §11)

**Confidence (§9)** is decomposed, not asserted: `composite = evidence_quality
× model_confidence × data_completeness × identity_confidence ×
graph_confidence`. Multiplicative composition means a chain of inferences is
only as strong as its weakest link; the UI names the limiting component
("limited by identity match confidence (0.61)"). Display bands: ≥0.80 High ·
0.55–0.79 Moderate · <0.55 Low.

**Trust framework (§11)** — every claim passes seven gates: 1 Evidence · 2
Confidence · 3 Lineage · 4 Limitations (never empty) · 5 Guards (P9, evidence
verification, k-anonymity) · 6 Approval (human review before operational use) ·
7 Audit. **LUMEN stops at the human decision, always.**

Trust statements rendered in the product (§11):

- On every network result: *"Co-accusal reflects charging decisions, not
  adjudicated guilt."*
- On every identity: *"Inferred match. Confidence 0.91. Report if incorrect."*
- On every forecast: *"Trained on 14 months. Not valid for districts with fewer
  than 50 records."*
- On every recommendation: *"Suggestion for officer review. Not an
  instruction."*
- On the act-section suggestion: *"Reflects statistical co-occurrence in past
  filings. Not legal advice."*

**What LUMEN will never do** (§11): predict individual criminality, rank
individuals by likelihood of offending, use protected attributes, take
autonomous action, or present an inference as a fact.

---

## 7. Audit (§21)

`lumen_audit` covers *access*: who read which case, who ran which AI query, who
exported what, who was denied. **T1:** authentication, AI queries, policy
denials, exports. **T2:** all reads. `lumen_audit` is immutable and readable
only by the Auditor role (`GET /audit`, §29.1). `lumen_event` is the
append-only domain-event replay log (§19). Both are enforced append-only in the
repository layer.
