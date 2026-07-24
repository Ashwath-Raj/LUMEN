# LUMEN v3 — Judge Q&A

The anticipated judge questions and their answers, reproduced verbatim from
LUMEN_MASTER_SPEC_V3 §38. No questions are added and no answers are embellished
(§37: architecture frozen; this session documents only what exists).

---

- **Why the official ERD?** Provenance and trust — and 27 defined tables are
  migratable to Data Store where a parallel 61-model schema is not.

- **What did you find in the schema that we didn't tell you?** There is no
  person master; `Accused` is per-case. Everything about repeat offenders
  depends on inferring identity, so we built resolution with explicit confidence
  rather than pretending name matches are facts. We also found eight structural
  inconsistencies, listed in `SCHEMA_NOTES.md`.

- **How do you stop hallucination?** Schema validation, then a server-side
  filter that drops any entity ID not in the retrieved bundle. We measure it:
  groundedness, hallucinated-ID count, and abstention rate on an adversarial
  golden set.

- **How is confidence computed?** Five components, multiplied. The UI names the
  limiting one.

- **You store caste and religion — do you use them?** No. Stored because the
  canonical schema defines them; excluded from every model, filter, chart and
  prompt by an enforced deny-list, with a CI test that fails the build.

- **What happens when a dependency fails?** A five-level degradation ladder,
  visible in the UI. We can demonstrate it — [disable the LLM].

- **How did you use Catalyst?** Walk §26.1. Name the one gap — no graph service
  — and explain the in-process decision.

- **What could go wrong in production?** Entity-resolution false positives,
  model drift, and coordinate quality in `CaseMaster`. Each has a stated
  mitigation and a monitoring signal.

- **What is not real yet?** The dataset is seeded, forecasts are fitted on a
  limited window, and everything in §36 is designed, not built. Said before
  being asked.

---

### Supporting references

Each answer is backed by an implemented subsystem and its documentation:

| Answer | Backed by |
|---|---|
| Official ERD | ADR-002, [`SCHEMA_NOTES.md`](SCHEMA_NOTES.md) |
| No person master / resolution | ADR-003, §6, [`SCHEMA_NOTES.md`](SCHEMA_NOTES.md) §1 fact 1 |
| Eight inconsistencies | [`SCHEMA_NOTES.md`](SCHEMA_NOTES.md) §2 |
| Stop hallucination | §16.2 step 9 (hard filter), §17.2 metrics, §17.3 adversarial suite |
| Confidence | ADR-007, §9, [`GOVERNANCE.md`](GOVERNANCE.md) §6 |
| Caste/religion never used | ADR-010, §4.3 rule 6, P9, [`GOVERNANCE.md`](GOVERNANCE.md) §5 |
| Dependency failure | §24 degradation ladder, [`RUNBOOK.md`](RUNBOOK.md) |
| Catalyst usage | [`CATALYST_MAP.md`](CATALYST_MAP.md), ADR-001 |
| What is not real yet | §36, [`ARCHITECTURE.md`](ARCHITECTURE.md) §9 |
