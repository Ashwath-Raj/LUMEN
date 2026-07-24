"""Contracts — the only shapes that cross a module boundary.

See LUMEN_MASTER_SPEC_V3 §7 (Data contracts and versioning) and §8
(Insight, explainability, lineage). Not yet implemented: EntityContract,
InsightContract, GraphContract, PredictionContract, RecommendationContract,
EventContract, EvidenceContract, QualityContract (§7 table).

`operator.py` and `auth.py` in this package are pre-existing Pydantic
models carried over from the prior implementation; they are the seed of
this module but do not yet conform to the versioned-contract pattern
required by §7.
"""
