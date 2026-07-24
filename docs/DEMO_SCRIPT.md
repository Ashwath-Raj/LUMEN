# DEMO_SCRIPT — deterministic demo-path entity IDs

Recorded per LUMEN_MASTER_SPEC_V3 §32 ("Record demo-path entity IDs in
`docs/DEMO_SCRIPT.md`. Re-run the seed and confirm the same IDs before the
final build.").

**Source of truth:** `api/lumen/jobs/seed.py`, run with the fixed seed
`SEED_RANDOM = 42` (the default in `config.py`). Every ID below is fixed by
construction — re-running `seed_database()` produces identical IDs on every
run, on any backend. This is asserted by
`api/tests/test_seed_guarantees.py::test_seed_is_deterministic_across_runs`.

To regenerate this file's values:

```python
from lumen.jobs.seed import seed_database   # against a fresh DB
manifest = seed_database(session)            # manifest.as_dict() == the values below
```

---

## The twelve §32 guarantees and their demo-path IDs

### 1. District with a visually obvious hotspot
- **District:** `1` (Bengaluru Urban)
- **Clustered case IDs:** `1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009` (10 cases, all within <1 km, unit `11` / Whitefield PS)

### 2. Resolved community ≥8 persons, ≥2 districts, exactly one broker
- **Districts spanned:** `1, 2`
- **Broker person label:** `P-BROKER` (the only person co-accused across both districts)
- **Community accused row IDs:** `2001–2004` (cluster A, district 1), `2101–2104` (cluster B, district 2), `2201, 2202, 2211, 2212` (broker + bridge cases `2200`/`2210`)
- **Person labels:** `P-A1..P-A4`, `P-B1..P-B4`, `P-BROKER` (9 distinct persons)

### 3. ≥3 persons in ≥3 cases each under name variants
- **Ravi Kumar** → accused IDs `3000, 3001, 3002` (variants: "Ravi Kumar", "Ravikumar", "Ravi Kumr")
- **Sunil Rao** → accused IDs `3003, 3004, 3005` (variants: "Sunil Rao", "Suneel Rao", "Sunil Raoo")
- **Anil Shetty** → accused IDs `3006, 3007, 3008` (variants: "Anil Shetty", "Aneel Shetty", "Anil Shety")

### 4. Two cases sharing an act-section signature, different districts, months apart
- **Case IDs:** `4000` (district 1, registered 2026-01-15), `4001` (district 3, registered 2026-05-20)
- **Shared signature:** `IPC 392` + `IPC 420`

### 5. Full-lifecycle case with a conspicuous charge delay
- **Case ID:** `5000`
- **Charge delay:** `278` days (~9 months) between registration (2026-01-10) and chargesheet (2026-10-15)
- Full lifecycle: incident (2026-01-05) → info received (2026-01-06) → registered (2026-01-10) → arrest (2026-01-20, ArrestSurrenderID `5000`) → chargesheet (CSID `5000`, cstype `A`)

### 6. District-week ≥3σ above baseline
- **District:** `2` (Mysuru)
- **Spike week start:** `2026-06-01`
- **Spike-week case IDs:** `6012–6026` (15 cases in one week; baseline weeks have 1 each)

### 7. Valid Karnataka coordinates + correct CrimeNo encoding
- Every seeded case (except the deliberate exceptions in guarantees 8 and 9) has coordinates inside the Karnataka bounding box (lat 11.5–18.5°N, lng 74–78.6°E) and an 18-digit `CrimeNo` whose embedded district/unit match its registering `Unit` (encoding: `1 category + 4 district + 4 unit + 4 year + 5 serial`, §3.2 fact 4).

### 8. One deliberate CrimeNo/Unit mismatch (for Q04)
- **Case ID:** `8000`
- **CrimeNo:** `100010012202600800` — decodes to category `1` (FIR), district `0001`, unit `0012`, year `2026`, serial `00800`, but the case is **registered to unit `11`** (Whitefield PS). Embedded unit 12 ≠ registering unit 11.

### 9. One missing-coordinates case (Q01) + one impossible-timestamp case (Q05)
- **Missing coordinates:** case ID `9000` (`latitude`/`longitude` both NULL)
- **Impossible timestamp:** case ID `9001` (incident 2026-04-01 dated *after* registration 2026-03-01)

### 10. Realistic cstype A/B/C distribution
- **A (chargesheet):** 12 · **B (false):** 3 · **C (undetected):** 5 (chargesheets seeded across case IDs `10000+`, plus cstype `A` on the lifecycle case `5000`)

### 11. One low-confidence identity candidate (0.66–0.75)
- **Accused IDs:** `11001` ("Mohammed Ali", age 41, district 1) and `11002` ("Mohammad Ali", age 43, district 3)
- **Intended confidence:** `0.70` (band `[0.66, 0.75]`) — near-identical name, close age, different district and no shared co-accused; the raw shape §6 resolution scores into the candidate band. No `lumen_person_link` row is seeded (that is §6/Session 7 output, not seed input).

### 12. ≥5 cases whose masking differs between Station Officer and District SP
- **Case IDs:** `12000, 12001, 12002, 12003, 12004` — each has a named `Victim` and named `Accused`; a Station Officer sees `V1`/`A1`, a District SP sees the real names (§4.2 masking thresholds).

---

## Notes

- The seed touches the **canonical §3.5 schema only**. `lumen_` platform tables
  (§3.6) are populated by later-session subsystems (entity resolution §6,
  intelligence §8, graph §14, quality §5), not by the seed — guarantees 2 and
  11 are seeded as the *raw shapes* those subsystems will detect, not as
  pre-computed results.
- Guarantee counts are lower-bound safe for their `≥` requirements; exact
  values above are what the current seed emits.
