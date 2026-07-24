"""
Catalyst T2 accelerators — LUMEN_MASTER_SPEC_V3 §26.1 (rows 14, 15, 16, 24, 25).

The T2 accelerators from §26.1's service map that carry a defined LUMEN usage:

    16  SmartBrowz     Case Intelligence Briefing PDF → Stratus URL   (briefing.py)
    24  Mail           Anomaly alert / briefing delivery              (notify.py)
    25  Push           High-risk alerts to officer devices            (notify.py)
    14  Zia OCR        OCR on scanned FIR/chargesheet uploads         (zia.py)
    15  Zia voice      Speech-to-text + Kannada→English translation   (zia.py)

Each is an EXTERNAL Catalyst/Zoho service, absent in this environment. §33
row-23's done-when — "Each demonstrable or dropped — no half-wired services" —
and §26.3's honesty rule ("an unused service claimed as used is worse than an
unused service") govern the implementation: every accelerator is a swappable
BACKEND (the ADR-001 / Sessions-18/21 pattern) with a LOCAL, deterministic
default that produces a demonstrable artifact now, and a Catalyst client that
slots in at deployment without any caller changing. Deployment-time
substitutions are documented per module.

§28 lists no accelerator module; this package is a disclosed placement choice.
Circuits (#23 = the §16.2 AI orchestrator pipeline, Session 14) and Zia AutoML
(#13 = the scikit-learn fallback, Session 10) already exist and are NOT
rebuilt here.
"""
