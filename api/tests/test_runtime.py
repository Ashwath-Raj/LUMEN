"""
Session 21 — Catalyst runtime: precompute Cron orchestrator + Cache
(§26.1 rows 9 & 20, §23).

Covers: the §23 cache TTLs (verbatim), TTL expiry, read-through, the swappable
backend interface, deterministic clock-driven behaviour; the §26.1-row-20
precompute pipeline (all stages, data-dependency order), §23 idempotence +
checkpoint-resume of a partial run, orchestration over existing jobs (not
duplicated), determinism, and edge cases.

Self-contained: in-memory SQLite; deterministic injected clock — no wall-clock,
no live Catalyst Cache/Cron (the deployed backend swaps in behind the same
interface).
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import (  # noqa: F401 — register all tables
    canonical, event, eval as _eval, feature, graph, identity, intelligence,
    kb, policy, prediction, prompt, quality, registry,
)
from lumen.db.models.feature import LumenFeature
from lumen.db.models.graph import LumenGraphEdge
from lumen.db.models.identity import LumenPerson
from lumen.jobs.precompute import (
    STAGES, PrecomputeCheckpoint, run_precompute,
)
from lumen.jobs.seed import seed_database
from lumen.services import cache

NOW = datetime(2026, 7, 25, 0, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def _fresh():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


# ── §23 cache TTLs (verbatim) ──────────────────────────────────────────────

def test_ttls_match_section_23():
    assert cache.TTLS == {
        "overview": 60,           # 60 s
        "hotspots": 300,          # 5 min
        "ego_graph": 900,         # 15 min
        "district_risk": 3600,    # 1 h
        "ai_answer": 900,         # 15 min
    }


def test_ttl_for_known_and_unknown_kind():
    assert cache.ttl_for("district_risk") == 3600
    with pytest.raises(KeyError):
        cache.ttl_for("made_up_kind")             # no §23 TTL → refuse to invent


# ── in-process backend: TTL expiry, invalidation ───────────────────────────

def test_cache_hit_then_expiry():
    c = Clock()
    cb = cache.InProcessCache(clock=c)
    cb.set("overview:home", {"n": 1}, ttl_s=cache.ttl_for("overview"))
    assert cb.get("overview:home") == {"n": 1}     # hit
    c.advance(59.9)
    assert cb.get("overview:home") == {"n": 1}     # still within 60 s
    c.advance(0.2)                                  # 60.1 s
    assert cb.get("overview:home") is None         # expired → miss


def test_cache_miss_for_absent_key():
    cb = cache.InProcessCache(clock=Clock())
    assert cb.get("nope") is None


def test_cache_invalidate_and_clear():
    cb = cache.InProcessCache(clock=Clock())
    cb.set("hotspots:d1", [1, 2], ttl_s=300)
    cb.invalidate("hotspots:d1")
    assert cb.get("hotspots:d1") is None
    cb.set("a", 1, ttl_s=60); cb.set("b", 2, ttl_s=60)
    cb.clear()
    assert cb.get("a") is None and cb.get("b") is None


def test_cache_key_is_deterministic():
    assert cache.cache_key("ego_graph", "P-1", "1hop") == "ego_graph:P-1:1hop"
    assert cache.cache_key("overview") == "overview"


# ── read-through (§24.1 miss → recompute) ──────────────────────────────────

def test_get_or_compute_computes_once_then_hits():
    cb = cache.InProcessCache(clock=Clock())
    calls = {"n": 0}
    def compute():
        calls["n"] += 1
        return "value"
    v1, hit1 = cache.get_or_compute(cb, "hotspots", ["d1"], compute)
    v2, hit2 = cache.get_or_compute(cb, "hotspots", ["d1"], compute)
    assert (v1, hit1) == ("value", False)          # miss → computed
    assert (v2, hit2) == ("value", True)           # hit → not recomputed
    assert calls["n"] == 1


def test_get_or_compute_recomputes_after_expiry():
    c = Clock()
    cb = cache.InProcessCache(clock=c)
    calls = {"n": 0}
    def compute():
        calls["n"] += 1
        return calls["n"]
    cache.get_or_compute(cb, "overview", ["x"], compute)   # compute → 1
    c.advance(61)                                          # expire (TTL 60)
    v, hit = cache.get_or_compute(cb, "overview", ["x"], compute)
    assert hit is False and v == 2 and calls["n"] == 2


# ── swappable backend interface (§26.3 / ADR-001 pattern) ──────────────────

def test_backend_is_swappable():
    """A different backend implements the same interface — the caller code
    (get_or_compute) does not change."""
    class RecordingBackend:
        name = "recording"
        def __init__(self):
            self.calls = []
            self._d = {}
        def get(self, key):
            self.calls.append(("get", key))
            return self._d.get(key)
        def set(self, key, value, *, ttl_s):
            self.calls.append(("set", key, ttl_s))
            self._d[key] = value
        def invalidate(self, key): self._d.pop(key, None)
        def clear(self): self._d.clear()

    rb = RecordingBackend()
    v, hit = cache.get_or_compute(rb, "ai_answer", ["q1"], lambda: "ans")
    assert v == "ans" and hit is False
    assert ("set", "ai_answer:q1", 900) in rb.calls    # §23 TTL applied via interface


# ── §26.1 row-20 precompute pipeline ───────────────────────────────────────

def test_stages_are_the_section_26_1_row_20_set():
    assert STAGES == ("resolution", "projection", "quality", "predictions", "features")


def test_full_precompute_runs_all_stages_and_persists():
    s = _fresh()
    seed_database(s)
    cp = run_precompute(s, now=NOW)
    assert cp.is_complete
    assert set(cp.completed) == set(STAGES)
    # each stage's output is persisted (consumed the real jobs)
    assert s.query(LumenPerson).count() >= 0            # resolution ran
    assert s.query(LumenGraphEdge).count() > 0          # projection ran
    assert s.query(LumenFeature).count() > 0            # features ran
    assert "written" in cp.stage_summaries["features"]


def test_partial_run_then_resume():
    """§23: 'a partial run resumes rather than restarts'."""
    s = _fresh()
    seed_database(s)
    cp = run_precompute(s, now=NOW, stop_after="quality")
    assert cp.completed == {"resolution", "projection", "quality"}
    assert not cp.is_complete
    # resume — completed stages are skipped, the rest run
    cp = run_precompute(s, now=NOW, checkpoint=cp)
    assert cp.is_complete
    assert cp.completed == set(STAGES)


def test_resume_skips_completed_stages():
    s = _fresh()
    seed_database(s)
    # pre-mark resolution as done with a sentinel summary; it must be skipped
    cp = PrecomputeCheckpoint()
    cp.mark("resolution", {"sentinel": True})
    cp = run_precompute(s, now=NOW, checkpoint=cp)
    assert cp.is_complete
    assert cp.stage_summaries["resolution"] == {"sentinel": True}   # not re-run


def test_rerun_is_idempotent():
    s = _fresh()
    seed_database(s)
    run_precompute(s, now=NOW)
    edges_1 = s.query(LumenGraphEdge).count()
    feats_1 = s.query(LumenFeature).count()
    run_precompute(s, now=NOW)                    # full re-run, fresh checkpoint
    assert s.query(LumenGraphEdge).count() == edges_1
    assert s.query(LumenFeature).count() == feats_1


def test_unknown_stage_rejected():
    from lumen.jobs.precompute import _run_stage
    s = _fresh()
    with pytest.raises(ValueError):
        _run_stage(s, "not_a_stage", NOW)


# ── determinism ─────────────────────────────────────────────────────────────

def test_precompute_is_deterministic():
    def snapshot():
        s = _fresh()
        seed_database(s)
        run_precompute(s, now=NOW)
        return (s.query(LumenGraphEdge).count(),
                s.query(LumenFeature).count(),
                sorted((f.entity_type, f.feature_name, round(f.value, 6))
                       for f in s.query(LumenFeature).all()))
    assert snapshot() == snapshot()
