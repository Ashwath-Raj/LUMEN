"""
AI evaluation table — LUMEN_MASTER_SPEC_V3 §3.6 (Session 15, §17.4).

    lumen_ai_eval(eval_id PK, run_id, question_id, groundedness, correctness,
                  hallucinated_ids INT, latency_ms, prompt_version, evaluated_at)

§17.4: "`make eval` runs the suite ... writes `lumen_ai_eval`, prints a
scorecard." One row per evaluated question per run. §3.6 gives no types for
`eval_id`/`run_id`/`question_id` — strings (uuid run id, golden-set question
id); `groundedness`/`correctness` are the §17.2 ratios (floats),
`hallucinated_ids` the §17.2 pre-filter dropped-ID count (INT, verbatim).
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String

from lumen.db.session import Base


class LumenAiEval(Base):
    __tablename__ = "lumen_ai_eval"

    eval_id = Column(String(80), primary_key=True)
    run_id = Column(String(80))
    question_id = Column(String(80))
    groundedness = Column(Float)         # §17.2 — IDs in bundle ÷ IDs cited
    correctness = Column(Float)          # §17.2 — rubric score
    hallucinated_ids = Column(Integer)   # §17.2 — dropped by step 9 (pre-filter signal)
    latency_ms = Column(Float)
    prompt_version = Column(String(20))
    evaluated_at = Column(DateTime)
