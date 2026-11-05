# Contributing to LUMEN

Thank you for considering a contribution. LUMEN is an open development effort around responsible, evidence-grounded crime-intelligence decision support. This local showcase is a demonstration layer, not an authorized operational police system.

## Good first contributions

- Improve the local showcase UI, accessibility and responsive behavior.
- Add API contract tests and end-to-end tests.
- Improve synthetic-data generation while keeping all generated people and cases fictional.
- Add explainability, lineage and uncertainty to analytical outputs.
- Improve developer documentation, architecture decisions and setup reproducibility.
- Add benchmarks and evaluation harnesses using documented synthetic or otherwise authorized datasets.

## Before opening a pull request

1. Open an issue describing the problem and expected behavior.
2. Keep changes aligned with the upstream `docs/LUMEN_MASTER_SPEC_V3.md` where they touch the primary application.
3. Run `./test.sh` from the showcase package for local-runtime changes.
4. Add tests for new API behavior and error paths.
5. Document data provenance, model assumptions, confidence semantics and limitations.
6. Never add credentials, personal data, real case records, police operational details or unapproved datasets.

## Responsible-use constraints

- Do not build individual criminality prediction, guilt scoring or automated enforcement.
- Do not use caste, religion, disability, blood group or other protected attributes as analytical features.
- Treat entity matches as uncertain investigative leads, not identity facts.
- Use only synthetic, public, de-identified or explicitly authorized data in development.
- Do not publish screenshots containing credentials or non-public operational information.

## Pull request format

Include: problem statement, implementation summary, test results, screenshots for UI changes, data/model assumptions, security/privacy considerations and known limitations.
