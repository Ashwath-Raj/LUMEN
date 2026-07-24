"""
Name normalisation + blocking key — LUMEN_MASTER_SPEC_V3 §6.2 (steps
`normalise` and `block`).

§6.2's pipeline opens:

    ↓ normalise   lowercase, honorifics stripped, patronymic particles
                  (bin, s/o, d/o) separated, transliteration folded
    ↓ block       (gender, phonetic key)  ← Double Metaphone, Indic-aware

This module implements exactly those two steps and nothing more. It does
not score, threshold, or cluster (later §6.2 steps, in `scoring.py` /
`pipeline.py`).

Double Metaphone comes from the `Metaphone` package (`doublemetaphone`),
which §6.2 names explicitly; Jaro-Winkler (the scoring step) comes from
`jellyfish`. Both are recorded in requirements.txt.
"""
from __future__ import annotations

import re
import unicodedata

from metaphone import doublemetaphone

# §6.2 "honorifics stripped". Common Indian honorifics / salutations that
# precede a personal name and carry no identity signal.
HONORIFICS = {
    "mr", "mrs", "ms", "miss", "dr", "shri", "sri", "smt", "kum", "km",
    "sir", "madam", "prof", "late", "m/s",
}

# §6.2 "patronymic particles (bin, s/o, d/o) separated". These introduce a
# parent's name, not part of the individual's own name — everything from the
# particle onward is dropped so "Ravi s/o Kumar" and "Ravi" block together.
PATRONYMIC_PARTICLES = {
    "bin", "binte", "bint", "s/o", "d/o", "w/o", "c/o", "son of", "daughter of",
}

_WS = re.compile(r"\s+")
# §6.2 "transliteration folded" — after accents are folded to ASCII (NFKD),
# strip anything that is not a Latin letter or space so residual punctuation
# from romanised Indic names goes away.
_NON_ALPHA = re.compile(r"[^a-z\s]")


def _fold_transliteration(text: str) -> str:
    """Fold accented/diacritic characters to their base ASCII letter (é→e,
    ä→a) via NFKD decomposition + combining-mark removal — §6.2 'transliteration
    folded'. Base letters are preserved, not dropped."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _strip_patronymic(text: str) -> str:
    """Cut the string at the first patronymic particle (§6.2 'separated')."""
    tokens = text.split()
    out: list[str] = []
    i = 0
    while i < len(tokens):
        # multi-word particles ("son of", "daughter of")
        two = f"{tokens[i]} {tokens[i + 1]}" if i + 1 < len(tokens) else None
        if two in PATRONYMIC_PARTICLES:
            break
        if tokens[i] in PATRONYMIC_PARTICLES:
            break
        out.append(tokens[i])
        i += 1
    return " ".join(out)


def normalise_name(raw: str | None) -> str:
    """Apply the §6.2 normalise step: lowercase, strip honorifics, separate
    patronymic particles, fold transliteration. Returns a canonical token
    string (may be empty if the input had no usable name content)."""
    if not raw:
        return ""
    # Fold accents to ASCII first, then lowercase — done before punctuation is
    # stripped so patronymic particles like "s/o" and "d/o" are still intact
    # for the split below.
    text = _fold_transliteration(raw).strip().lower()
    text = _WS.sub(" ", text)
    if not text:
        return ""
    # Separate patronymic particles (drop the parent-name tail) — matched on
    # their raw "s/o"/"d/o"/"bin" forms while the slashes are still present.
    text = _strip_patronymic(text)
    # Now remove residual punctuation, collapse whitespace.
    text = _NON_ALPHA.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    # Strip leading honorifics.
    tokens = [t for t in text.split() if t]
    while tokens and tokens[0] in HONORIFICS:
        tokens.pop(0)
    return " ".join(tokens)


def phonetic_key(normalised: str) -> str:
    """§6.2 blocking phonetic key via Double Metaphone. Concatenates the
    primary code of each name token so that spelling variants of the same
    spoken name ('Ravi Kumar' / 'Ravikumar' / 'Ravi Kumr') share a key.
    An empty normalised name yields an empty key."""
    if not normalised:
        return ""
    parts: list[str] = []
    for token in normalised.split():
        primary, _secondary = doublemetaphone(token)
        parts.append(primary or token.upper())
    return "".join(parts)


def block_key(gender_id: int | None, normalised: str) -> tuple:
    """§6.2 blocking key: (gender, phonetic key). Two Accused rows are only
    compared as a candidate pair when they share this key — the blocking
    step that keeps the pairwise scan tractable."""
    return (gender_id, phonetic_key(normalised))
