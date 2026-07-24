"""
Entity-resolution pipeline — LUMEN_MASTER_SPEC_V3 §6.2 (threshold + cluster
steps, orchestrating normalise/block/score).

§6.2's full pipeline:

    Accused rows
      ↓ normalise   (normalize.py)
      ↓ block       (gender, phonetic key)              (normalize.py)
      ↓ score       weighted feature vector per pair     (scoring.py)
      ↓ threshold   ≥0.85 auto-link · 0.65–0.85 candidate (surfaced, never
                    auto-merged) · <0.65 reject
      ↓ cluster     connected components, transitivity capped at 3 hops
      ↓ persist     lumen_person + lumen_person_link      (jobs/resolve.py)

This module implements block → score → threshold → cluster and returns an
in-memory `ResolutionResult`. Persistence is `jobs/resolve.py`'s job (§6.2
"persist"), matching how §5 keeps detection (engine) separate from writing
(job).

A second scoring pass adds the §6.3 "shared already-resolved co-accused"
signal: after a first clustering pass, a pair whose two Accused rows sit in
cases that already share a resolved person is re-scored with that bonus, and
clusters are recomputed once. §6.3 labels this feature "2nd pass" explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from lumen.identity.features import AccusedSignals, build_signals
from lumen.identity.scoring import PairScore, score_pair
from lumen.identity.normalize import block_key

# §6.2 threshold bands.
AUTO_LINK_THRESHOLD = 0.85          # ≥0.85 auto-link
CANDIDATE_THRESHOLD = 0.65          # 0.65–0.85 candidate; <0.65 reject
MAX_TRANSITIVITY_HOPS = 3           # §6.2 "transitivity capped at 3 hops"

LINK_STATE_LINKED = "linked"        # auto-linked member of a cluster
LINK_STATE_CANDIDATE = "candidate"  # surfaced 0.65–0.85 pair, never auto-merged


@dataclass
class ScoredPair:
    a_id: int
    b_id: int
    confidence: float
    features: dict


@dataclass
class ResolvedCluster:
    """A connected component of auto-linked Accused rows = one inferred
    person. Confidence is the minimum pairwise confidence along the links
    (a chain is as strong as its weakest link — ADR-007)."""
    accused_ids: list[int]
    confidence: float
    # per accused_master_id -> the match evidence that linked it in
    member_features: dict = field(default_factory=dict)


@dataclass
class ResolutionResult:
    clusters: list[ResolvedCluster]                 # auto-linked persons (≥0.85)
    candidate_pairs: list[ScoredPair]               # 0.65–0.85, surfaced not merged
    signals: dict[int, AccusedSignals]


def _name_frequencies(signals: dict[int, AccusedSignals]) -> dict[str, float]:
    """Inverse-frequency driver for the §6.3 common-name penalty: the
    fraction of Accused rows sharing each normalised name."""
    counts: dict[str, int] = {}
    total = 0
    for s in signals.values():
        if not s.normalised:
            continue
        counts[s.normalised] = counts.get(s.normalised, 0) + 1
        total += 1
    if total == 0:
        return {}
    return {name: c / total for name, c in counts.items()}


def _blocks(signals: dict[int, AccusedSignals]) -> dict[tuple, list[int]]:
    """§6.2 block step: group Accused ids by (gender, phonetic key). Only
    rows sharing a block are compared."""
    blocks: dict[tuple, list[int]] = {}
    for s in signals.values():
        if not s.phonetic:            # no usable name → cannot block/resolve
            continue
        key = block_key(s.gender_id, s.normalised)
        blocks.setdefault(key, []).append(s.accused_master_id)
    return blocks


def _score_all_pairs(
    signals: dict[int, AccusedSignals],
    freqs: dict[str, float],
    resolved_coaccused: set[frozenset] | None = None,
) -> list[ScoredPair]:
    """Score every within-block candidate pair (§6.2 block→score)."""
    pairs: list[ScoredPair] = []
    for ids in _blocks(signals).values():
        ids_sorted = sorted(ids)
        for i in range(len(ids_sorted)):
            for j in range(i + 1, len(ids_sorted)):
                a = signals[ids_sorted[i]]
                b = signals[ids_sorted[j]]
                freq = max(freqs.get(a.normalised, 0.0), freqs.get(b.normalised, 0.0))
                shared_co = False
                if resolved_coaccused is not None:
                    shared_co = frozenset((a.accused_master_id, b.accused_master_id)) in resolved_coaccused
                ps: PairScore = score_pair(a, b, name_frequency=freq, shared_resolved_coaccused=shared_co)
                pairs.append(ScoredPair(a.accused_master_id, b.accused_master_id, ps.confidence, ps.features))
    return pairs


def _cluster(
    auto_pairs: list[ScoredPair],
    signals: dict[int, AccusedSignals],
) -> list[ResolvedCluster]:
    """§6.2 cluster step: connected components over auto-link (≥0.85) edges,
    with transitivity capped at 3 hops. The hop cap bounds how far a chain of
    pairwise links may bind members together, so an over-long transitive chain
    doesn't collapse loosely-related people into one node."""
    # adjacency of auto-link edges
    adj: dict[int, dict[int, ScoredPair]] = {}
    for p in auto_pairs:
        adj.setdefault(p.a_id, {})[p.b_id] = p
        adj.setdefault(p.b_id, {})[p.a_id] = p

    seen: set[int] = set()
    clusters: list[ResolvedCluster] = []

    for start in sorted(adj):
        if start in adj and start in seen:
            continue
        if start not in adj:
            continue
        # BFS from `start`, but only follow edges within MAX_TRANSITIVITY_HOPS
        # of the seed — the §6.2 transitivity cap.
        component: dict[int, int] = {start: 0}   # node -> hop distance from seed
        queue = [start]
        while queue:
            node = queue.pop(0)
            hop = component[node]
            if hop >= MAX_TRANSITIVITY_HOPS:
                continue
            for nb in adj.get(node, {}):
                if nb not in component:
                    component[nb] = hop + 1
                    queue.append(nb)
        members = sorted(component)
        if len(members) < 2:
            continue
        seen.update(members)

        # Confidence = weakest auto-link within the component (ADR-007);
        # member evidence = the strongest edge that attached each member.
        edge_confidences = []
        member_features: dict[int, dict] = {}
        for m in members:
            best_edge = None
            for other, p in adj.get(m, {}).items():
                if other in component:
                    edge_confidences.append(p.confidence)
                    if best_edge is None or p.confidence > best_edge.confidence:
                        best_edge = p
            if best_edge is not None:
                member_features[m] = best_edge.features
        confidence = min(edge_confidences) if edge_confidences else 0.0
        clusters.append(ResolvedCluster(accused_ids=members, confidence=confidence, member_features=member_features))

    return clusters


def resolve(session: Session) -> ResolutionResult:
    """Run the full §6.2 pipeline against the canonical Accused rows and
    return the in-memory resolution result (no persistence)."""
    signals = build_signals(session)
    freqs = _name_frequencies(signals)

    # First pass: block → score → threshold → cluster.
    pairs = _score_all_pairs(signals, freqs)
    auto = [p for p in pairs if p.confidence >= AUTO_LINK_THRESHOLD]
    clusters = _cluster(auto, signals)

    # Second pass (§6.3 "shared already-resolved co-accused"): a pair gains the
    # bonus when its two Accused rows sit in cases that share an already-
    # resolved person from pass 1. Re-score, re-threshold, re-cluster once.
    resolved_coaccused = _resolved_coaccused_pairs(clusters, signals)
    if resolved_coaccused:
        pairs = _score_all_pairs(signals, freqs, resolved_coaccused=resolved_coaccused)
        auto = [p for p in pairs if p.confidence >= AUTO_LINK_THRESHOLD]
        clusters = _cluster(auto, signals)

    # Candidate band: 0.65–0.85 pairs whose members were NOT auto-linked into
    # the same cluster — surfaced, never auto-merged (§6.2 / §6.4).
    linked_members = {mid for c in clusters for mid in c.accused_ids}
    candidates = [
        p for p in pairs
        if CANDIDATE_THRESHOLD <= p.confidence < AUTO_LINK_THRESHOLD
        and not _same_cluster(p.a_id, p.b_id, clusters)
    ]

    return ResolutionResult(clusters=clusters, candidate_pairs=candidates, signals=signals)


def _same_cluster(a_id: int, b_id: int, clusters: list[ResolvedCluster]) -> bool:
    for c in clusters:
        if a_id in c.accused_ids and b_id in c.accused_ids:
            return True
    return False


def _resolved_coaccused_pairs(
    clusters: list[ResolvedCluster],
    signals: dict[int, AccusedSignals],
) -> set[frozenset]:
    """Build the set of Accused pairs {a,b} for which a and b sit in cases
    that already share a resolved person from the first pass — the trigger
    for §6.3's 2nd-pass 'shared already-resolved co-accused' bonus."""
    # person (cluster index) -> set of case ids it appears in
    person_cases: list[set[int]] = []
    for c in clusters:
        cases = {signals[a].case_master_id for a in c.accused_ids if signals[a].case_master_id is not None}
        person_cases.append(cases)

    # case -> resolved persons appearing in it
    case_persons: dict[int, set[int]] = {}
    for pidx, cases in enumerate(person_cases):
        for cid in cases:
            case_persons.setdefault(cid, set()).add(pidx)

    # Accused rows co-appearing in a case that already contains ≥1 resolved
    # person are candidate co-accused. Two Accused a,b get the bonus if they
    # share a case whose resolved-person set is non-empty.
    accused_by_case: dict[int, list[int]] = {}
    for s in signals.values():
        if s.case_master_id is not None:
            accused_by_case.setdefault(s.case_master_id, []).append(s.accused_master_id)

    out: set[frozenset] = set()
    for cid, resolved_here in case_persons.items():
        if not resolved_here:
            continue
        members = sorted(accused_by_case.get(cid, []))
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                out.add(frozenset((members[i], members[j])))
    return out
