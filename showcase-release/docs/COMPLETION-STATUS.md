# Showcase completion status and remaining production work

## Delivered in this package

- [x] Local launch script for Ubuntu / Linux
- [x] Optional clone-and-install helper for the public `lumen-development` branch
- [x] Persistent SQLite showcase schema and deterministic synthetic seed data
- [x] Responsive command-centre dashboard
- [x] Case search, district filter and case dossier API
- [x] Synthetic person directory and entity dossier API
- [x] Entity relationship graph and candidate listing
- [x] Karnataka coordinate plotting view
- [x] District indicator and volume-deviation views
- [x] Evidence-returning deterministic assistant
- [x] Protected-attribute and individual-criminality refusal examples
- [x] Data quality / trust boundary page
- [x] Local audit feed
- [x] Automated tests for primary API surfaces

## Still required before a real deployment

1. Reconcile and run the upstream frontend/backend build on a clean checkout; verify the current default branch and eliminate migration-era stale references.
2. Complete Catalyst project setup and deploy to isolated staging: Web Client Hosting, AppSail, Data Store, Authentication, API Gateway, Signals/Functions and Cron only where actually used.
3. Configure and test the QuickML transport from the deployment environment; verify the exact provider request/response contract and timeouts.
4. Verify all routers against migrated canonical tables, not only against seeded local records. Add integration tests for every end-to-end screen workflow.
5. Replace generated seed data with authorized, minimized, de-identified operational data only after legal, privacy, security and data-owner approval.
6. Run threat modelling, security testing, role/permission tests, secret scanning, dependency scanning and audit-retention review.
7. Validate model training data, temporal splits, baseline comparisons, calibration, false-positive rates, subgroup harm and drift. Do not operationalize district predictions until validated.
8. Validate entity resolution using representative labelled pairs, review thresholds, false-match controls and an appeal/correction process.
9. Verify coordinate provenance, geocoding precision, missingness and uncertainty. Do not infer incident coordinates from district centres.
10. Complete load, latency, resilience, backup/restore, observability and disaster-recovery tests.
11. Conduct user acceptance and workflow testing with authorized KSP stakeholders.

## Claims discipline

The local package is a runnable prototype demonstrator. It is not a production-complete KSP deployment, and it does not claim that the upstream Catalyst integrations are operational. The product's T1/T2/T3 classification in `LUMEN_MASTER_SPEC_V3.md` remains the authoritative build-status reference for the upstream codebase.
