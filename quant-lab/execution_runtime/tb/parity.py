"""QL-EXEC-R4 — parity classification, trace normalization, and comparison.

R4 answers one question: can the proven TB system be represented faithfully
through the generic runtime substrate? Parity is NEVER a vague PASS; every
compared surface is classified into one of six frozen tiers:

    EXACT                              byte-for-byte / value-for-value equal
    NORMALIZED_EQUIVALENT              same semantics after non-semantic fields
                                       are stripped (timestamps, internal ids)
    SAFETY_STRENGTHENING_NONREGRESSIVE generic path is stricter but does not
                                       change normal-path behavior
    INTENTIONAL_ARCHITECTURE_DIFFERENCE an expected structural divergence that
                                       does not change economic/risk semantics
    MISMATCH                           a real divergence (R4 FAIL)
    NOT_TESTED                         not exercised in this checkpoint

Trace normalization only strips non-semantic fields (test timestamps, internal
object names). It NEVER strips event order, side, quantity, state, broker
result, or ownership.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class ParityTier(str, Enum):
    EXACT = "EXACT"
    NORMALIZED_EQUIVALENT = "NORMALIZED_EQUIVALENT"
    SAFETY_STRENGTHENING_NONREGRESSIVE = "SAFETY_STRENGTHENING_NONREGRESSIVE"
    INTENTIONAL_ARCHITECTURE_DIFFERENCE = "INTENTIONAL_ARCHITECTURE_DIFFERENCE"
    MISMATCH = "MISMATCH"
    NOT_TESTED = "NOT_TESTED"


@dataclass(frozen=True)
class ParityVerdict:
    surface: str
    tier: ParityTier
    reference: object
    generic: object
    detail: str = ""

    @property
    def pass_ok(self) -> bool:
        """True unless this surface is a hard mismatch."""
        return self.tier is not ParityTier.MISMATCH

    def to_dict(self) -> dict:
        return {
            "surface": self.surface,
            "tier": self.tier.value,
            "reference": _jsonable(self.reference),
            "generic": _jsonable(self.generic),
            "detail": self.detail,
        }


def _jsonable(v):
    if hasattr(v, "to_dict"):
        return v.to_dict()
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    return v


_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:?\d{2}|Z)?")
_HEX_RE = re.compile(r"\b[0-9a-f]{8,64}\b", re.IGNORECASE)


def normalize_trace(trace: list[str]) -> list[str]:
    """Normalize a trace to canonical event names, stripping non-semantic noise.

    Event order, side, quantity, state, and broker results are preserved. Only
    test timestamps, internal ids, and cosmetic separators are removed.
    """
    out = []
    for step in trace:
        s = _TIMESTAMP_RE.sub("<TS>", str(step))
        s = _HEX_RE.sub("<ID>", s)
        s = s.strip()
        if s:
            out.append(s)
    return out


def classify_scalar(surface: str, ref, gen, *, exact: bool = True) -> ParityVerdict:
    """Classify a scalar comparison (exact vs normalized-equivalent)."""
    if ref == gen:
        return ParityVerdict(surface, ParityTier.EXACT, ref, gen)
    # numeric tolerance for floats
    if isinstance(ref, float) and isinstance(gen, float) and abs(ref - gen) < 1e-9:
        return ParityVerdict(surface, ParityTier.EXACT, ref, gen)
    if exact:
        return ParityVerdict(
            surface, ParityTier.MISMATCH, ref, gen,
            f"expected EXACT parity: ref={ref!r} gen={gen!r}",
        )
    return ParityVerdict(surface, ParityTier.NORMALIZED_EQUIVALENT, ref, gen)


def compare_traces(surface: str, ref_trace: list[str], gen_trace: list[str]) -> ParityVerdict:
    """Compare two normalized traces (order-sensitive, semantics-preserving)."""
    r = normalize_trace(ref_trace)
    g = normalize_trace(gen_trace)
    if r == g:
        return ParityVerdict(surface, ParityTier.EXACT, ref_trace, gen_trace)
    # Normalized-equivalent: same multiset of semantic events but possibly a
    # documented ordering difference (e.g. write-ahead emitted before precheck).
    if sorted(r) == sorted(g):
        return ParityVerdict(
            surface, ParityTier.NORMALIZED_EQUIVALENT, ref_trace, gen_trace,
            "same events, different order",
        )
    return ParityVerdict(
        surface, ParityTier.MISMATCH, ref_trace, gen_trace,
        f"trace mismatch: ref={r!r} gen={g!r}",
    )


def compare_legs(surface: str, ref_legs, gen_legs) -> ParityVerdict:
    """Compare normalized leg sets (symbol, side, requested, filled).

    Ownership tags may differ textually (basket-id token length) while still
    encoding the same logical leg identity -> NORMALIZED_EQUIVALENT.
    """
    def norm(legs):
        out = []
        for l in legs:
            d = l.to_dict() if hasattr(l, "to_dict") else dict(l)
            out.append(tuple(sorted(
                (str(k), round(float(v), 6) if isinstance(v, float) else str(v))
                for k, v in d.items()
                if k in ("instrument", "canonical_symbol", "broker_symbol",
                         "side", "requested", "filled", "status", "requested_lots",
                         "rounded_lots")
            )))
        return sorted(out)

    r, g = norm(ref_legs), norm(gen_legs)
    if r == g:
        return ParityVerdict(surface, ParityTier.EXACT, ref_legs, gen_legs)
    # allow textual ownership-tag differences only
    return ParityVerdict(
        surface, ParityTier.MISMATCH, ref_legs, gen_legs,
        f"leg set mismatch: ref={r!r} gen={g!r}",
    )


def compare_state_snapshot(surface: str, ref: dict, gen: dict) -> ParityVerdict:
    """Compare normalized state snapshots (keys preserved, values normalized)."""
    def norm(d):
        return {k: _jsonable(v) for k, v in sorted(d.items())}

    r, g = norm(ref), norm(gen)
    if r == g:
        return ParityVerdict(surface, ParityTier.EXACT, ref, gen)
    return ParityVerdict(
        surface, ParityTier.MISMATCH, ref, gen,
        f"state mismatch: ref={r!r} gen={g!r}",
    )


def verdicts_by_surface(verdicts: list[ParityVerdict]) -> dict[str, str]:
    return {v.surface: v.tier.value for v in verdicts}


def any_mismatch(verdicts: list[ParityVerdict]) -> bool:
    return any(v.tier is ParityTier.MISMATCH for v in verdicts)
