"""
Mail + Push notifications — LUMEN_MASTER_SPEC_V3 §26.1 rows 24, 25.

§26.1 #24 (Mail): "Anomaly alert to the district officer; briefing delivery."
§26.1 #25 (Push): "High-risk alerts to officer devices."

Both are external Catalyst services (Mail, Push Notifications). Each is a
swappable BACKEND with a local deterministic default that RECORDS the dispatch
in an in-memory outbox — demonstrable now (§33 row-23), never half-wired. The
Catalyst Mail / Push clients slot in at deployment via `set_mail_backend` /
`set_push_backend`, no caller changing.

§26.1 #22 (Signals) routes `AnomalyDetected` to notification functions; this
module is the dispatch target such a function would call. Wiring the bus
subscription is the §19/Session-12 event layer's job — this module provides
the send primitive, consumed by that wiring (not duplicated here).

Cannot determine from the specification (recorded in the deliverables):
  * recipient ADDRESSING — §26.1 says "the district officer" / "officer
    devices" but no address/token scheme; the recipient is a caller-supplied
    opaque identifier.
  * message TEMPLATES — no wording is given; subject/body are caller-supplied.
  * a persistence table — §3.6 defines none for sent mail/push, so the outbox
    is in-memory (not a fabricated table).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class Message:
    channel: str            # "mail" | "push"
    recipient: str          # opaque id (address / device token) — caller-supplied
    subject: str
    body: str
    sent_at: str            # iso8601


# ── Mail (#24) ──────────────────────────────────────────────────────────────

class MailBackend(Protocol):
    name: str

    def send(self, *, recipient: str, subject: str, body: str,
             sent_at: str) -> Message: ...


@dataclass
class LocalMailBackend:
    """Local deterministic Mail backend: records to an in-memory outbox."""
    name: str = "local"
    outbox: list[Message] = field(default_factory=list)

    def send(self, *, recipient: str, subject: str, body: str,
             sent_at: str) -> Message:
        msg = Message("mail", recipient, subject, body, sent_at)
        self.outbox.append(msg)
        return msg


# ── Push (#25) ──────────────────────────────────────────────────────────────

class PushBackend(Protocol):
    name: str

    def send(self, *, recipient: str, subject: str, body: str,
             sent_at: str) -> Message: ...


@dataclass
class LocalPushBackend:
    """Local deterministic Push backend: records to an in-memory outbox."""
    name: str = "local"
    outbox: list[Message] = field(default_factory=list)

    def send(self, *, recipient: str, subject: str, body: str,
             sent_at: str) -> Message:
        msg = Message("push", recipient, subject, body, sent_at)
        self.outbox.append(msg)
        return msg


_mail: MailBackend = LocalMailBackend()
_push: PushBackend = LocalPushBackend()


def set_mail_backend(backend: MailBackend) -> None:
    global _mail
    _mail = backend


def set_push_backend(backend: PushBackend) -> None:
    global _push
    _push = backend


def active_mail_backend() -> MailBackend:
    return _mail


def active_push_backend() -> PushBackend:
    return _push


def send_mail(*, recipient: str, subject: str, body: str,
              now: datetime | None = None) -> Message:
    """§26.1 #24: send transactional email via the active backend."""
    now = now or datetime.now(timezone.utc)
    return _mail.send(recipient=recipient, subject=subject, body=body,
                      sent_at=now.isoformat())


def send_push(*, recipient: str, subject: str, body: str,
              now: datetime | None = None) -> Message:
    """§26.1 #25: send a push notification via the active backend."""
    now = now or datetime.now(timezone.utc)
    return _push.send(recipient=recipient, subject=subject, body=body,
                      sent_at=now.isoformat())
