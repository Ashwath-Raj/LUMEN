"""
Zia Services — OCR + voice — LUMEN_MASTER_SPEC_V3 §26.1 rows 14, 15.

§26.1 #14 (Zia OCR): "OCR on scanned FIR/chargesheet uploads into the evidence
pipeline; entity extraction from BriefFacts."
§26.1 #15 (Zia voice): "Speech-to-text into the Intelligence Console;
Kannada→English translation of BriefFacts."

Both are external Zoho Zia services. Each capability is a swappable BACKEND
with a local deterministic default so the interface is demonstrable now (§33
row-23), never half-wired; the Zia client slots in at deployment via the
`set_*_backend` seams.

The local backends are HONEST no-ops, NOT fake AI (§26.3 honesty rule): they
do not fabricate an OCR transcription or a translation — no local model is
specified and inventing one would be a defect. `OcrResult`/`VoiceResult` carry
`engine="local_stub"` and an explicit `available=False`, so a caller can see
the capability exists but is not fulfilled without the Zia backend. A real Zia
adapter returns `available=True` with the actual output.

Cannot determine from the specification (recorded in the deliverables):
  * the OCR / STT / translation request+response contracts (Zia API shapes).
  * any local OCR/translation model — none is named; the local backend does
    not invent one (§26.3: never fabricate).
  * a persistence table for OCR/voice outputs — §3.6 defines none.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OcrResult:
    text: str | None
    engine: str
    available: bool          # False when no Zia backend fulfils the request


@dataclass(frozen=True)
class VoiceResult:
    text: str | None
    engine: str
    available: bool
    source_language: str | None = None
    target_language: str | None = None


# ── OCR (#14) ───────────────────────────────────────────────────────────────

class OcrBackend(Protocol):
    name: str

    def extract_text(self, document_ref: str) -> OcrResult: ...


class LocalOcrBackend:
    """Honest local stub: OCR requires the Zia service. No local OCR model is
    specified, so this backend does not fabricate a transcription — it reports
    the capability as unavailable (available=False) rather than inventing text
    (§26.3 honesty rule)."""

    name = "local_stub"

    def extract_text(self, document_ref: str) -> OcrResult:
        return OcrResult(text=None, engine=self.name, available=False)


# ── Voice (#15): STT + Kannada→English translation ─────────────────────────

class VoiceBackend(Protocol):
    name: str

    def speech_to_text(self, audio_ref: str) -> VoiceResult: ...

    def translate(self, text: str, *, source: str, target: str) -> VoiceResult: ...


class LocalVoiceBackend:
    """Honest local stub for STT and Kannada→English translation. No local
    speech/translation model is specified; the stub reports unavailable rather
    than fabricating output."""

    name = "local_stub"

    def speech_to_text(self, audio_ref: str) -> VoiceResult:
        return VoiceResult(text=None, engine=self.name, available=False)

    def translate(self, text: str, *, source: str, target: str) -> VoiceResult:
        return VoiceResult(text=None, engine=self.name, available=False,
                           source_language=source, target_language=target)


_ocr: OcrBackend = LocalOcrBackend()
_voice: VoiceBackend = LocalVoiceBackend()


def set_ocr_backend(backend: OcrBackend) -> None:
    global _ocr
    _ocr = backend


def set_voice_backend(backend: VoiceBackend) -> None:
    global _voice
    _voice = backend


def active_ocr_backend() -> OcrBackend:
    return _ocr


def active_voice_backend() -> VoiceBackend:
    return _voice


def ocr_extract(document_ref: str) -> OcrResult:
    """§26.1 #14: OCR a scanned FIR/chargesheet upload via the active backend."""
    return _ocr.extract_text(document_ref)


def speech_to_text(audio_ref: str) -> VoiceResult:
    """§26.1 #15: speech-to-text via the active backend."""
    return _voice.speech_to_text(audio_ref)


def translate_kn_en(text: str) -> VoiceResult:
    """§26.1 #15: Kannada→English translation via the active backend."""
    return _voice.translate(text, source="kn", target="en")
