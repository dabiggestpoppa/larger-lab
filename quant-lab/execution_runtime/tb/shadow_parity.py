"""QL-EXEC-R4.2 — live shadow parity comparator (frozen tolerances).

Compares the legacy export record (produced by the proven TB path) against the
generic shadow's recomputed values for each synchronized closed bar, using the
tolerances frozen in QL_EXEC_R4_1_NUMERIC_TOLERANCE:

- bar key / source timestamp: exact string equality
- basis: relative 1e-12
- z-score: absolute 1e-9
- weights / direction / decision / session / basket state: exact
- target lots: exact string equality (2dp), float 1e-9

Tolerances are NEVER widened after a live mismatch. A value outside tolerance
produces a MISMATCH verdict with an exact mismatch class; the shadow remains
orderless and the science is never altered.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .parity import ParityTier

# Frozen numeric tolerances (from R4.1 NUMERIC_TOLERANCE; do NOT change).
TOL_BASIS_REL = 1e-12
TOL_Z_ABS = 1e-9
TOL_LOT_ABS = 1e-9

# Export schema version frozen for G1.
SHADOW_EXPORT_SCHEMA_VERSION = 1


class ShadowMismatchClass(str, Enum):
    MARKET_DATA_KEY_MISMATCH = "MARKET_DATA_KEY_MISMATCH"
    SOURCE_TIMESTAMP_MISMATCH = "SOURCE_TIMESTAMP_MISMATCH"
    BASIS_MISMATCH = "BASIS_MISMATCH"
    ZSCORE_MISMATCH = "ZSCORE_MISMATCH"
    ENTRY_DECISION_MISMATCH = "ENTRY_DECISION_MISMATCH"
    EXIT_DECISION_MISMATCH = "EXIT_DECISION_MISMATCH"
    DIRECTION_MISMATCH = "DIRECTION_MISMATCH"
    WEIGHT_MISMATCH = "WEIGHT_MISMATCH"
    LOT_MISMATCH = "LOT_MISMATCH"
    SESSION_MISMATCH = "SESSION_MISMATCH"
    BASKET_STATE_MISMATCH = "BASKET_STATE_MISMATCH"
    RESTART_STATE_MISMATCH = "RESTART_STATE_MISMATCH"


@dataclass(frozen=True)
class LiveParityVerdict:
    bar_key: str
    surface: str
    tier: ParityTier
    legacy_value: object
    generic_value: object
    mismatch_class: Optional[ShadowMismatchClass] = None
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "bar_key": self.bar_key,
            "surface": self.surface,
            "tier": self.tier.value,
            "legacy_value": _jsonable(self.legacy_value),
            "generic_value": _jsonable(self.generic_value),
            "mismatch_class": (
                self.mismatch_class.value if self.mismatch_class else None
            ),
            "detail": self.detail,
        }


def _jsonable(v):
    if hasattr(v, "to_dict"):
        return v.to_dict()
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in sorted(v.items())}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, float):
        return round(v, 8)
    return v


def _close_floats(a, b, *, rel: Optional[float] = None, abs_: Optional[float] = None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if abs(fa - fb) <= (abs_ if abs_ is not None else 0.0):
        return True
    if rel is not None:
        scale = max(abs(fa), abs(fb), 1e-300)
        return abs(fa - fb) <= rel * scale
    return False


def _exact(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        return _close_floats(a, b, abs_=TOL_LOT_ABS)
    return a == b


def _verdict(bar_key: str, surface: str, ref, gen, cls: ShadowMismatchClass,
             ok: bool, detail: str = "") -> LiveParityVerdict:
    if ok:
        return LiveParityVerdict(bar_key, surface, ParityTier.EXACT, ref, gen)
    return LiveParityVerdict(
        bar_key, surface, ParityTier.MISMATCH, ref, gen,
        mismatch_class=cls, detail=detail or f"ref={ref!r} gen={gen!r}",
    )


def _weights_dict(raw) -> dict:
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            out[str(k)] = round(float(v), 6)
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, dict):
                out[str(item.get("canonical_symbol", item.get("symbol", "")))] = round(
                    float(item.get("model_weight", item.get("weight", 0.0))), 6)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                out[str(item[0])] = round(float(item[1]), 6)
    return out


def _lots_dict(raw) -> dict:
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            out[str(k)] = round(float(v), 6)
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, dict):
                key = str(item.get("broker_symbol", item.get("symbol", "")))
                val = item.get("target_lots", item.get("target_quantity", item.get("lots")))
                out[key] = round(float(val), 6)
    return out


def _decision_normalized(raw) -> str:
    if raw is None:
        return "NO_SIGNAL"
    s = str(raw).upper()
    for token in ("ENTRY", "OPEN"):
        if token in s:
            return "ENTRY"
    if "EXIT" in s or "CLOSE" in s:
        return "EXIT"
    if "NO_ACTION" in s or "NO_SIGNAL" in s or s in ("NONE", "NOOP"):
        return "NO_SIGNAL"
    return s


def compare_live_record(bar_key: str, legacy: dict, generic: dict) -> list[LiveParityVerdict]:
    """Compare one legacy export record vs the generic shadow's recomputation.

    ``legacy`` is the exporter record's ``primary``/``control`` sub-dict plus
    top-level market fields; ``generic`` is the shadow's recomputed dict
    (same shape). Returns a list of per-surface verdicts.
    """
    out: list[LiveParityVerdict] = []

    # market-data key (common bar) — exact
    out.append(_verdict(
        bar_key, "market_data_key", legacy.get("bar_key"), generic.get("bar_key"),
        ShadowMismatchClass.MARKET_DATA_KEY_MISMATCH,
        str(legacy.get("bar_key")) == str(generic.get("bar_key")),
    ))
    # source timestamp — exact
    out.append(_verdict(
        bar_key, "source_timestamp", legacy.get("source_timestamp"),
        generic.get("source_timestamp"),
        ShadowMismatchClass.SOURCE_TIMESTAMP_MISMATCH,
        str(legacy.get("source_timestamp")) == str(generic.get("source_timestamp")),
    ))
    # session / market-open — exact
    out.append(_verdict(
        bar_key, "session", legacy.get("session"), generic.get("session"),
        ShadowMismatchClass.SESSION_MISMATCH,
        bool(legacy.get("session")) == bool(generic.get("session")),
    ))

    for tag in ("primary", "control"):
        l = legacy.get(tag) or {}
        g = generic.get(tag) or {}
        out.append(_verdict(
            bar_key, f"{tag}_basis", l.get("basis"), g.get("basis"),
            ShadowMismatchClass.BASIS_MISMATCH,
            _close_floats(l.get("basis"), g.get("basis"), rel=TOL_BASIS_REL),
        ))
        out.append(_verdict(
            bar_key, f"{tag}_z", l.get("z"), g.get("z"),
            ShadowMismatchClass.ZSCORE_MISMATCH,
            _close_floats(l.get("z"), g.get("z"), abs_=TOL_Z_ABS),
        ))
        out.append(_verdict(
            bar_key, f"{tag}_decision", l.get("decision"), g.get("decision"),
            ShadowMismatchClass.ENTRY_DECISION_MISMATCH
            if "exit" not in str(l.get("decision", "")).lower()
            else ShadowMismatchClass.EXIT_DECISION_MISMATCH,
            _decision_normalized(l.get("decision"))
            == _decision_normalized(g.get("decision")),
        ))
        out.append(_verdict(
            bar_key, f"{tag}_direction", l.get("direction"), g.get("direction"),
            ShadowMismatchClass.DIRECTION_MISMATCH,
            _exact(l.get("direction"), g.get("direction")),
        ))
        out.append(_verdict(
            bar_key, f"{tag}_weights", l.get("weights"), g.get("weights"),
            ShadowMismatchClass.WEIGHT_MISMATCH,
            _weights_dict(l.get("weights")) == _weights_dict(g.get("weights")),
        ))
        out.append(_verdict(
            bar_key, f"{tag}_lots", l.get("lots"), g.get("lots"),
            ShadowMismatchClass.LOT_MISMATCH,
            _lots_dict(l.get("lots")) == _lots_dict(g.get("lots")),
        ))

    out.append(_verdict(
        bar_key, "basket_state", legacy.get("basket_state"),
        generic.get("basket_state"),
        ShadowMismatchClass.BASKET_STATE_MISMATCH,
        str(legacy.get("basket_state")) == str(generic.get("basket_state")),
    ))
    return out


def any_mismatch(verdicts: list[LiveParityVerdict]) -> bool:
    return any(v.tier is ParityTier.MISMATCH for v in verdicts)


def mismatches(verdicts: list[LiveParityVerdict]) -> list[LiveParityVerdict]:
    return [v for v in verdicts if v.tier is ParityTier.MISMATCH]
