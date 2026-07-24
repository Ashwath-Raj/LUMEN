# data/seeds/

Deterministic demo seed data, fixed random seed, per `LUMEN_MASTER_SPEC_V3.md`
§32 (Deterministic demo data) — the twelve guarantees a seed run must satisfy.

Not yet implemented as data files. The prior implementation's Karnataka
seed generators (`api/lumen/jobs/seed.py`, `api/lumen/jobs/seeds/karnataka/*`)
are real, working code carried over from the previous backend; they
produce data programmatically rather than from static seed files here.
Whether §32's twelve guarantees are satisfied by that generator, and
whether this directory should hold static fixtures instead of/alongside
it, is open — see `docs/MIGRATION.md` §5.
