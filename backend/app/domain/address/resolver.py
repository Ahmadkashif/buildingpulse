"""Pure address resolution against a frozen LL84 index.

Given a free-form NYC street address and a pre-loaded
:class:`Ll84Index`, return either an :class:`Ll84Match` (with a
confidence flag) or an :class:`Ll84Miss`.

Strategy:

1. Reject malformed input (non-string, empty, whitespace-only) with a
   ``"malformed"`` miss — the resolver never raises.
2. Normalize the input to the same canonical form used by the index
   (uppercase, punctuation stripped, USPS suffixes canonicalized).
3. If exactly one indexed record matches the normalized form, return a
   high-confidence match. If several do, return the first with low
   confidence — the caller cannot disambiguate without more input.
4. Otherwise, fuzzy-match against the indexed addresses with
   :mod:`difflib`. If the top candidate is meaningfully better than the
   runner-up, return a high-confidence match; otherwise low. If nothing
   clears the cutoff, return a ``"not_found"`` miss.

The address normalization rules here mirror
``training.build_ll84_index.normalize_address`` — duplicated rather than
imported because the layering rules forbid ``app.domain`` from
depending on ``training``. The two implementations must stay in sync;
the cross-module contract is exercised by integration tests.
"""

from __future__ import annotations

import difflib
import re

from app.domain.address.types import (
    Confidence,
    Ll84Index,
    Ll84Match,
    Ll84Miss,
    Ll84Record,
)

__all__ = [
    "AMBIGUITY_MARGIN",
    "FUZZY_CUTOFF",
    "lookup",
    "normalize_address",
]

# Minimum SequenceMatcher ratio for a fuzzy candidate to be considered.
# 0.80 catches typos and minor abbreviation variance ("ST" vs "STREET"
# after canonicalization is exact, not fuzzy) without surfacing
# unrelated addresses that share a house number.
FUZZY_CUTOFF: float = 0.80

# If the top fuzzy candidate's ratio is within this margin of the
# runner-up's, the resolver flags the match as low confidence. The
# threshold is small on purpose: callers should treat anything close to
# a tie as "user must disambiguate".
AMBIGUITY_MARGIN: float = 0.05

_PUNCT_RE: re.Pattern[str] = re.compile(r"[^\w\s]+")
_WS_RE: re.Pattern[str] = re.compile(r"\s+")

_SUFFIX_MAP: dict[str, str] = {
    "STREET": "ST",
    "STR": "ST",
    "AVENUE": "AVE",
    "AV": "AVE",
    "BOULEVARD": "BLVD",
    "ROAD": "RD",
    "DRIVE": "DR",
    "PLACE": "PL",
    "COURT": "CT",
    "PARKWAY": "PKWY",
    "TERRACE": "TER",
    "LANE": "LN",
    "HIGHWAY": "HWY",
    "SQUARE": "SQ",
    "EXPRESSWAY": "EXPY",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
}


def normalize_address(value: str) -> str:
    """Canonicalize an address string for index lookup.

    Pure: same input → same output. Returns an empty string when the
    input collapses to no tokens (whitespace, punctuation only).
    """
    text = value.strip().upper()
    text = _PUNCT_RE.sub(" ", text)
    tokens = [_SUFFIX_MAP.get(tok, tok) for tok in text.split()]
    return _WS_RE.sub(" ", " ".join(tokens)).strip()


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(a=a, b=b).ratio()


def _first_record_with(records: tuple[Ll84Record, ...], normalized: str) -> Ll84Record:
    for r in records:
        if r.address_normalized == normalized:
            return r
    # Unreachable: ``normalized`` always comes from the records themselves.
    raise LookupError(normalized)  # pragma: no cover


def lookup(address: object, index: Ll84Index) -> Ll84Match | Ll84Miss:
    """Resolve ``address`` against ``index``.

    See module docstring for the resolution strategy. Never raises;
    malformed input becomes ``Ll84Miss(reason="malformed")``.
    """
    if not isinstance(address, str):
        return Ll84Miss(reason="malformed")
    normalized = normalize_address(address)
    if not normalized:
        return Ll84Miss(reason="malformed")

    records = index.records
    if not records:
        return Ll84Miss(reason="not_found")

    exact = [r for r in records if r.address_normalized == normalized]
    if len(exact) == 1:
        return Ll84Match(record=exact[0], confidence="high")
    if len(exact) > 1:
        return Ll84Match(record=exact[0], confidence="low")

    candidates = [r.address_normalized for r in records]
    matches = difflib.get_close_matches(normalized, candidates, n=2, cutoff=FUZZY_CUTOFF)
    if not matches:
        return Ll84Miss(reason="not_found")

    top = matches[0]
    confidence: Confidence = "high"
    if len(matches) >= 2:
        top_score = _ratio(normalized, top)
        runner_up_score = _ratio(normalized, matches[1])
        if top_score - runner_up_score < AMBIGUITY_MARGIN:
            confidence = "low"

    return Ll84Match(record=_first_record_with(records, top), confidence=confidence)
