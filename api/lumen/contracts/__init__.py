"""Contracts — the only shapes that cross a module boundary.

See LUMEN_MASTER_SPEC_V3 §7 (Data contracts and versioning).

Implemented (Session 2): `EntityContract` (see `entity.py`) — the only one
of §7's eight contracts whose producer, the semantic layer, is in
Session 2's scope.

Not yet implemented: `InsightContract`, `GraphContract`,
`PredictionContract`, `RecommendationContract`, `EventContract`,
`EvidenceContract`, `QualityContract` — each is produced by a subsystem
(intelligence engine, graph module, prediction engine, decision support,
event bus, retriever, quality engine) that later sessions build, and the
specification gives no field-level shape for any of them beyond the §7
summary table. Building them now would mean inventing structure the
document does not specify.
"""
