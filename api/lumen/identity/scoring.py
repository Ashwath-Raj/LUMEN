"""
Candidate-pair scoring — LUMEN_MASTER_SPEC_V3 §6.3 (the `score` step of §6.2).

§6.3 fixes the v1 feature weights (to tune against the seed) exactly:

    | Feature                                       | Weight |
    | Normalised name similarity (Jaro-Winkler)     |  0.35  |
    | Phonetic key match                            |  0.15  |
    | Implied birth-year agreement (±2 y)           |  0.20  |
    | Gender agreement                              |  0.05  |
    | Shared arrest district                        |  0.10  |
    | Shared police station                         |  0.10  |
    | Shared already-resolved co-accused (2nd pass) |  0.15  |
    | Common-name penalty (inverse frequency)       | −0.20  |

"Cap at 1.0. The common-name penalty is mandatory."

Each feature contributes its full weight when its condition holds, scaled by
the feature's own magnitude where the feature is graded (name similarity is
Jaro-Winkler ∈ [0,1]; the rest are indicators ∈ {0,1}). The score is the sum,
capped at 1.0 (and floored at 0.0 — a heavily penalised pair cannot go below
zero and remain a probability-like confidence).

Jaro-Winkler is provided by `jellyfish`; §6.3 names it explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass

from jellyfish import jaro_winkler_similarity

from lumen.identity.features import AccusedSignals

# §6.3 weights — verbatim, the single source of these constants.
W_NAME = 0.35
W_PHONETIC = 0.15
W_BIRTH_YEAR = 0.20
W_GENDER = 0.05
W_ARREST_DISTRICT = 0.10
W_POLICE_STATION = 0.10
W_SHARED_COACCUSED = 0.15          # 2nd pass only
W_COMMON_NAME_PENALTY = -0.20      # mandatory (§6.3)

BIRTH_YEAR_TOLERANCE = 2           # §6.3 "±2 y"
METHOD_VERSION = "v1"              # §6.3 "(v1; tune against the seed)"

# The score bands are defined in `pipeline.py` (§6.2 threshold step); scoring
# only produces the raw pair confidence.


@dataclass
class PairScore:
    confidence: float                  # 0..1, capped
    features: dict                     # §6.4 "see why" — per-feature contribution


def _birth_year_agrees(a: AccusedSignals, b: AccusedSignals) -> bool:
    if a.implied_birth_year is None or b.implied_birth_year is None:
        return False
    return abs(a.implied_birth_year - b.implied_birth_year) <= BIRTH_YEAR_TOLERANCE


def score_pair(
    a: AccusedSignals,
    b: AccusedSignals,
    *,
    name_frequency: float,
    shared_resolved_coaccused: bool = False,
) -> PairScore:
    """Score one candidate pair per §6.3.

    `name_frequency` is the inverse-frequency driver of the common-name
    penalty: the fraction of Accused rows sharing this normalised name
    (∈ (0, 1]). A frequent name (large fraction) incurs the full −0.20; a
    unique name incurs ~0. `shared_resolved_coaccused` is the 2nd-pass
    signal (§6.3 last positive row), supplied by the pipeline once a first
    pass has produced clusters.
    """
    features: dict = {}

    # Normalised name similarity (Jaro-Winkler), graded ∈ [0,1].
    name_sim = jaro_winkler_similarity(a.normalised, b.normalised) if a.normalised and b.normalised else 0.0
    features["name_similarity"] = {"value": round(name_sim, 4), "weight": W_NAME, "contribution": round(W_NAME * name_sim, 4)}

    # Phonetic key match (indicator).
    phonetic_match = bool(a.phonetic) and a.phonetic == b.phonetic
    features["phonetic_match"] = {"value": phonetic_match, "weight": W_PHONETIC, "contribution": W_PHONETIC if phonetic_match else 0.0}

    # Implied birth-year agreement ±2y (indicator).
    birth_agree = _birth_year_agrees(a, b)
    features["birth_year_agreement"] = {"value": birth_agree, "weight": W_BIRTH_YEAR, "contribution": W_BIRTH_YEAR if birth_agree else 0.0}

    # Gender agreement (indicator; only when both known).
    gender_agree = a.gender_id is not None and a.gender_id == b.gender_id
    features["gender_agreement"] = {"value": gender_agree, "weight": W_GENDER, "contribution": W_GENDER if gender_agree else 0.0}

    # Shared arrest district (indicator).
    shared_district = bool(a.arrest_districts & b.arrest_districts)
    features["shared_arrest_district"] = {"value": shared_district, "weight": W_ARREST_DISTRICT, "contribution": W_ARREST_DISTRICT if shared_district else 0.0}

    # Shared police station (indicator).
    shared_station = bool(a.arrest_stations & b.arrest_stations)
    features["shared_police_station"] = {"value": shared_station, "weight": W_POLICE_STATION, "contribution": W_POLICE_STATION if shared_station else 0.0}

    # Shared already-resolved co-accused (2nd pass indicator).
    features["shared_resolved_coaccused"] = {"value": shared_resolved_coaccused, "weight": W_SHARED_COACCUSED, "contribution": W_SHARED_COACCUSED if shared_resolved_coaccused else 0.0}

    # Common-name penalty (inverse frequency) — mandatory. Scaled by how
    # common the name is: full −0.20 for the most frequent name, ~0 for a
    # unique one.
    penalty = W_COMMON_NAME_PENALTY * float(name_frequency)
    features["common_name_penalty"] = {"value": round(float(name_frequency), 4), "weight": W_COMMON_NAME_PENALTY, "contribution": round(penalty, 4)}

    raw = sum(f["contribution"] for f in features.values())
    confidence = max(0.0, min(1.0, raw))   # cap at 1.0 (§6.3); floor at 0.0
    return PairScore(confidence=confidence, features=features)
