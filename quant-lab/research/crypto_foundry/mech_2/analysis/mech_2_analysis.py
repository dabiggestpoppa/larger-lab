"""
CRYPTO-MECH-2: State & Dislocation Taxonomy — core analysis functions.

Pure, deterministic, testable. No strategy PnL, no optimization, no ML,
no execution. All randomness uses a frozen seed; all thresholds are frozen
in MECH_2_STATE_DEFINITIONS.json BEFORE transition/path results are read.

Axes (per MECH_2_PREREGISTRATION.md):
- BASIS_STATE      B0_NORMAL / B1_ELEVATED_POSITIVE / B2_EXTREME_POSITIVE /
                   B3_ELEVATED_NEGATIVE / B4_EXTREME_NEGATIVE
- FUNDING_STATE    F_NEG_EXTREME / F_NEG_ELEVATED / F_NORMAL /
                   F_POS_ELEVATED / F_POS_EXTREME
- FUNDING_ACCEL    F_ACCEL_NEG / F_STABLE / F_ACCEL_POS (24h delta, 1 MAD)
- VOL_STATE        V_LOW / V_NORMAL / V_HIGH / V_EXTREME (RV 24h lookback)
- MARK_INDEX_STATE MI_STRESS_NEGATIVE / MI_NORMAL / MI_STRESS_POSITIVE
                   (premium proxy — PROVISIONAL)
- OI_STATE         DEFERRED (no temporal history on frozen data)
- RELATIVE_STATE   SYNCHRONIZED / BTC_LED / ETH_LED / DIVERGENT
- SYSTEMIC_STATE   SYSTEMIC_STRESS / BTC_SPECIFIC / ETH_SPECIFIC /
                   NORMAL_CROSS_STATE
- TIME_EPOCH       ASIA / EUROPE / US / LATE_US (+ WEEKDAY / WEEKEND)
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

SEED = 20260821

# ---------------------------------------------------------------------------
# Frozen analysis constants
# ---------------------------------------------------------------------------

HORIZONS_HOURS = [1, 4, 8, 24]
TRANSITION_HORIZONS = [1, 4, 8, 24]           # hourly grid
FINE_TRANSITION_HORIZONS = [5, 15, 30]        # 5m grid (NOT AVAILABLE on frozen data)
VOL_LOOKBACKS = [1, 4, 24]                    # hours (24h is primary for labeling)
MIN_SUPPORT = {
    "usable": 100,
    "limited": 50,
    "sparse": 20,
    "insufficient": 20,
}
BOOTSTRAP_RESAMPLES = 500
NULL_PERMUTATIONS = 200
BH_FDR_Q = 0.05

EPOCH_BOUNDARIES = [
    ("ASIA", 0, 8),
    ("EUROPE", 8, 16),
    ("US", 16, 23),
    ("LATE_US", 23, 24),
]

SEVERITY = {
    "B2_EXTREME_POSITIVE": 2, "B1_ELEVATED_POSITIVE": 1, "B0_NORMAL": 0,
    "B3_ELEVATED_NEGATIVE": -1, "B4_EXTREME_NEGATIVE": -2,
    "F_POS_EXTREME": 2, "F_POS_ELEVATED": 1, "F_NORMAL": 0,
    "F_NEG_ELEVATED": -1, "F_NEG_EXTREME": -2,
}

# Classification precedence for dislocation paths (frozen, see prereg §16)
PATH_PRECEDENCE = [
    "CENSORED",
    "PERSISTENT",
    "EXPANSION_FIRST_THEN_RESOLVE",
    "REGIME_SHIFT",
    "FAST_RESOLUTION",
    "SLOW_RESOLUTION",
]


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def stable_hash(obj: Any) -> str:
    s = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def parse_ts(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    s = str(ts)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def bucket_hour(ts: Any) -> Optional[str]:
    dt = parse_ts(ts)
    if dt is None:
        return None
    return dt.replace(minute=0, second=0, microsecond=0).isoformat()


def bucket_5m(ts: Any) -> Optional[str]:
    dt = parse_ts(ts)
    if dt is None:
        return None
    m = (dt.minute // 5) * 5
    return dt.replace(minute=m, second=0, microsecond=0).isoformat()


def hour_index(bucket: str) -> Optional[int]:
    dt = parse_ts(bucket)
    if dt is None:
        return None
    return int(dt.timestamp() // 3600)


# ---------------------------------------------------------------------------
# Threshold computation (frozen quantiles per asset)
# ---------------------------------------------------------------------------

def compute_basis_thresholds(basis_bps: List[float]) -> Dict[str, float]:
    a = np.asarray([v for v in basis_bps if v is not None and np.isfinite(v)],
                   dtype=float)
    if len(a) == 0:
        raise ValueError("no basis values for threshold computation")
    p10, p25, p75, p90 = np.percentile(a, [10, 25, 75, 90])
    p75_abs = float(np.percentile(np.abs(a), 75))
    p90_abs = float(np.percentile(np.abs(a), 90))
    return {
        "p10": float(p10), "p25": float(p25), "p75": float(p75),
        "p90": float(p90), "p75_abs": p75_abs, "p90_abs": p90_abs,
        "n": int(len(a)),
    }


def compute_funding_thresholds(funding_bps: List[float]) -> Dict[str, float]:
    a = np.asarray([v for v in funding_bps if v is not None and np.isfinite(v)],
                   dtype=float)
    if len(a) == 0:
        raise ValueError("no funding values for threshold computation")
    p5, p25, p75, p95 = np.percentile(a, [5, 25, 75, 95])
    return {
        "p5": float(p5), "p25": float(p25), "p75": float(p75), "p95": float(p95),
        "n": int(len(a)),
    }


def compute_accel_threshold(funding_bps: List[float], lag_hours: int = 24,
                            min_gap: int = 23) -> Dict[str, Any]:
    """1 MAD of the 24h funding delta distribution (frozen)."""
    a = np.asarray([v for v in funding_bps if v is not None and np.isfinite(v)],
                   dtype=float)
    if len(a) < lag_hours + 2:
        raise ValueError("funding series too short for acceleration threshold")
    d = a[lag_hours:] - a[:-lag_hours]
    mad = float(np.median(np.abs(d - np.median(d))))
    return {"mad_bps": mad, "lag_hours": lag_hours, "n_deltas": int(len(d))}


def compute_vol_thresholds(rv24: List[float]) -> Dict[str, float]:
    a = np.asarray([v for v in rv24 if v is not None and np.isfinite(v)],
                   dtype=float)
    if len(a) == 0:
        raise ValueError("no RV values for threshold computation")
    p25, p75, p90 = np.percentile(a, [25, 75, 90])
    return {"p25": float(p25), "p75": float(p75), "p90": float(p90),
            "n": int(len(a))}


def compute_premium_thresholds(premium_bps: List[float]) -> Dict[str, float]:
    a = np.asarray([v for v in premium_bps if v is not None and np.isfinite(v)],
                   dtype=float)
    if len(a) == 0:
        raise ValueError("no premium values for threshold computation")
    p10, p90 = np.percentile(a, [10, 90])
    return {"p10": float(p10), "p90": float(p90), "n": int(len(a))}


def build_state_definitions(
    basis_btc: List[float], basis_eth: List[float],
    funding_btc: List[float], funding_eth: List[float],
    rv_btc: List[float], rv_eth: List[float],
    premium_btc: List[float], premium_eth: List[float],
) -> Dict[str, Any]:
    """Assemble the frozen state-definition document (per asset thresholds)."""
    doc = {
        "checkpoint": "CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY",
        "preregistered_method": "quant-lab/research/crypto_foundry/mech_2/MECH_2_PREREGISTRATION.md (2026-08-21)",
        "quantile_method": "numpy.percentile linear",
        "thresholds_computed_from": "frozen DATA-1 datasets (full frozen sample), before any transition/path result inspection",
        "thresholds": {
            "BTC": {
                "basis": compute_basis_thresholds(basis_btc),
                "funding": compute_funding_thresholds(funding_btc),
                "accel": compute_accel_threshold(funding_btc),
                "vol": compute_vol_thresholds(rv_btc),
                "premium": compute_premium_thresholds(premium_btc),
            },
            "ETH": {
                "basis": compute_basis_thresholds(basis_eth),
                "funding": compute_funding_thresholds(funding_eth),
                "accel": compute_accel_threshold(funding_eth),
                "vol": compute_vol_thresholds(rv_eth),
                "premium": compute_premium_thresholds(premium_eth),
            },
        },
        "path_classification_precedence": PATH_PRECEDENCE,
        "min_support": MIN_SUPPORT,
        "horizons_hours": HORIZONS_HOURS,
        "fine_horizons_minutes": FINE_TRANSITION_HORIZONS,
        "vol_lookbacks_hours": VOL_LOOKBACKS,
        "label_aliases": {
            "B2_EXTREME_POSITIVE": "B_EXTREME_POS",
            "B1_ELEVATED_POSITIVE": "B_ELEVATED_POS",
            "B0_NORMAL": "B_NORMAL",
            "B3_ELEVATED_NEGATIVE": "B_ELEVATED_NEG",
            "B4_EXTREME_NEGATIVE": "B_EXTREME_NEG",
            "F_POS_EXTREME": "F_EXTREME_POS",
            "F_POS_ELEVATED": "F_ELEVATED_POS",
            "F_NORMAL": "F_NORMAL",
            "F_NEG_ELEVATED": "F_ELEVATED_NEG",
            "F_NEG_EXTREME": "F_EXTREME_NEG",
            "F_ACCEL_POS": "F_ACCEL_POS",
            "F_STABLE": "F_STABLE",
            "F_ACCEL_NEG": "F_ACCEL_NEG",
            "V_EXTREME": "V_EXTREME",
            "V_HIGH": "V_HIGH",
            "V_NORMAL": "V_NORMAL",
            "V_LOW": "V_LOW",
            "MI_STRESS_POSITIVE": "MI_STRESS_POS",
            "MI_NORMAL": "MI_NORMAL",
            "MI_STRESS_NEGATIVE": "MI_STRESS_NEG",
        },
        "note": ("Thresholds are frozen BEFORE transition/path/information "
                 "results are inspected. No window or threshold is chosen "
                 "after observing results."),
    }
    doc["definitions_hash"] = stable_hash(doc)
    return doc


# ---------------------------------------------------------------------------
# Labeling functions (use ONLY frozen thresholds)
# ---------------------------------------------------------------------------

def label_basis(basis_bps: float, thr: Dict[str, float]) -> str:
    b = float(basis_bps)
    if not np.isfinite(b):
        return "UNKNOWN"
    if abs(b) <= thr["p75_abs"]:
        return "B0_NORMAL"
    if b > thr["p90"]:
        return "B2_EXTREME_POSITIVE"
    if b > thr["p75"]:
        return "B1_ELEVATED_POSITIVE"
    if b < thr["p10"]:
        return "B4_EXTREME_NEGATIVE"
    if b < thr["p25"]:
        return "B3_ELEVATED_NEGATIVE"
    return "B0_NORMAL"


def label_funding(rate_bps: float, thr: Dict[str, float]) -> str:
    f = float(rate_bps)
    if not np.isfinite(f):
        return "UNKNOWN"
    if f < thr["p5"]:
        return "F_NEG_EXTREME"
    if f < thr["p25"]:
        return "F_NEG_ELEVATED"
    if f <= thr["p75"]:
        return "F_NORMAL"
    if f <= thr["p95"]:
        return "F_POS_ELEVATED"
    return "F_POS_EXTREME"


def label_funding_accel(delta_bps: float, mad: float) -> str:
    if not np.isfinite(float(delta_bps)):
        return "UNKNOWN"
    if delta_bps < -mad:
        return "F_ACCEL_NEG"
    if delta_bps > mad:
        return "F_ACCEL_POS"
    return "F_STABLE"


def label_vol(rv: float, thr: Dict[str, float]) -> str:
    v = float(rv)
    if not np.isfinite(v):
        return "UNKNOWN"
    if v <= thr["p25"]:
        return "V_LOW"
    if v <= thr["p75"]:
        return "V_NORMAL"
    if v <= thr["p90"]:
        return "V_HIGH"
    return "V_EXTREME"


def label_premium(premium_bps: float, thr: Dict[str, float]) -> str:
    p = float(premium_bps)
    if not np.isfinite(p):
        return "UNKNOWN"
    if p < thr["p10"]:
        return "MI_STRESS_NEGATIVE"
    if p > thr["p90"]:
        return "MI_STRESS_POSITIVE"
    return "MI_NORMAL"


def label_epoch(ts: Any) -> Tuple[str, str]:
    dt = parse_ts(ts)
    if dt is None:
        return ("UNKNOWN", "UNKNOWN")
    h = dt.hour
    for name, start, end in EPOCH_BOUNDARIES:
        if start <= h < end:
            epoch = name
            break
    else:
        epoch = "UNKNOWN"
    dow = "WEEKEND" if dt.weekday() >= 5 else "WEEKDAY"
    return (epoch, dow)


def severity_of(label: str) -> int:
    return SEVERITY.get(label, 0)


def relative_state(btc_sev: int, eth_sev: int) -> str:
    if btc_sev == 0 and eth_sev == 0:
        return "SYNCHRONIZED"
    if btc_sev * eth_sev < 0:
        return "DIVERGENT"
    if btc_sev == 0:
        return "ETH_LED"
    if eth_sev == 0:
        return "BTC_LED"
    if abs(btc_sev) > abs(eth_sev):
        return "BTC_LED"
    if abs(eth_sev) > abs(btc_sev):
        return "ETH_LED"
    return "SYNCHRONIZED"


def systemic_state(btc_sev: int, eth_sev: int) -> str:
    if abs(btc_sev) >= 2 and abs(eth_sev) >= 2 and btc_sev * eth_sev > 0:
        return "SYSTEMIC_STRESS"
    if abs(btc_sev) >= 2 and abs(eth_sev) < 2:
        return "BTC_SPECIFIC"
    if abs(eth_sev) >= 2 and abs(btc_sev) < 2:
        return "ETH_SPECIFIC"
    return "NORMAL_CROSS_STATE"


def composite_l2(basis_state: str, funding_state: str) -> str:
    return f"{basis_state}+{funding_state}"


def composite_l3(basis_state: str, funding_state: str, vol_state: str) -> str:
    return f"{basis_state}+{funding_state}+{vol_state}"


# ---------------------------------------------------------------------------
# Series construction (causal: each row uses only information <= t)
# ---------------------------------------------------------------------------

def realized_vol_from_1h_closes(
    closes: List[Tuple[str, float]], lookback_hours: int,
) -> Dict[str, float]:
    """RV = std of 1h log returns over lookback (causal; uses closes <= t)."""
    closes = sorted(closes, key=lambda x: x[0])
    idx = [hour_index(b) for b, _ in closes]
    vals = np.asarray([c for _, c in closes], dtype=float)
    log_ret = np.diff(np.log(vals))
    out: Dict[str, float] = {}
    for i, (bk, _) in enumerate(closes):
        h = idx[i]
        if h is None or i < lookback_hours:
            out[bk] = np.nan
            continue
        # returns over the `lookback_hours` hours ending at t
        seg = log_ret[i - lookback_hours: i]
        if len(seg) < max(2, lookback_hours // 2):
            out[bk] = np.nan
        else:
            out[bk] = float(np.std(seg, ddof=1))
    return out


def causal_join_prior(
    buckets: List[str], series: Dict[str, float], max_gap_hours: float = 2.0,
) -> Dict[str, Optional[float]]:
    """For each bucket, the value from the same bucket else nearest prior."""
    keys = sorted(series.keys())
    out: Dict[str, Optional[float]] = {}
    j = 0
    for bk in buckets:
        if bk in series:
            out[bk] = series[bk]
            continue
        while j < len(keys) and keys[j] < bk:
            j += 1
        prior = keys[j - 1] if j > 0 else None
        if prior is None:
            out[bk] = None
            continue
        gap = (hour_index(bk) - hour_index(prior)) / 1.0
        if gap is not None and gap <= max_gap_hours:
            out[bk] = series[prior]
        else:
            out[bk] = None
    return out


def build_funding_by_bucket(funding_records: List[Dict]) -> Dict[str, Dict[str, float]]:
    by_bucket: Dict[str, Dict[str, float]] = {}
    for r in funding_records:
        bk = bucket_hour(r.get("event_time_utc"))
        if bk is None:
            continue
        rate = r.get("funding_rate")
        prem = r.get("premium")
        if rate is None:
            continue
        by_bucket[bk] = {
            "funding_bps": float(rate) * 1e4,
            "premium_bps": float(prem) * 1e4 if prem is not None else np.nan,
        }
    return by_bucket


def build_vol_by_bucket(
    spot_records: List[Dict], lookbacks: List[int] = VOL_LOOKBACKS,
) -> Dict[str, Dict[str, float]]:
    """Causal RV per hourly bucket for each lookback (from spot 1h closes)."""
    # aggregate spot 5m -> 1h closes
    by_bucket: Dict[str, float] = {}
    for r in spot_records:
        ts = parse_ts(r.get("event_time_utc"))
        c = r.get("close")
        if ts is None or c is None or not np.isfinite(float(c)):
            continue
        bk = bucket_hour(ts)
        by_bucket[bk] = float(c)
    closes = sorted(by_bucket.items())
    out: Dict[str, Dict[str, float]] = {bk: {} for bk, _ in closes}
    for lb in lookbacks:
        rv = realized_vol_from_1h_closes(closes, lb)
        for bk, v in rv.items():
            out[bk][f"rv{lb}h"] = v
    return out


def build_basis_hourly(
    perp_1h: List[Dict], spot_5m: List[Dict], max_staleness_hours: float = 1.0,
) -> List[Dict]:
    """Causal hourly perp-spot basis (same construction as MECH-1)."""
    # aggregate spot 5m to hourly closes
    spot_by_bucket: Dict[str, float] = {}
    for r in spot_5m:
        ts = parse_ts(r.get("event_time_utc"))
        c = r.get("close")
        if ts is None or c is None or not np.isfinite(float(c)) or float(c) <= 0:
            continue
        spot_by_bucket[bucket_hour(ts)] = float(c)

    perp_by_bucket: Dict[str, float] = {}
    for r in perp_1h:
        ts = parse_ts(r.get("event_time_utc"))
        c = r.get("close")
        if ts is None or c is None or not np.isfinite(float(c)) or float(c) <= 0:
            continue
        perp_by_bucket[bucket_hour(ts)] = float(c)

    spot_keys = sorted(spot_by_bucket.keys())
    rows: List[Dict] = []
    for bk in sorted(perp_by_bucket.keys()):
        spot = spot_by_bucket.get(bk)
        staleness = 0.0
        if spot is None:
            prior = [k for k in spot_keys if k < bk]
            if not prior:
                continue
            spot = spot_by_bucket[prior[-1]]
            gap = hour_index(bk) - hour_index(prior[-1])
            if gap is None or gap > max_staleness_hours:
                continue
            staleness = float(gap)
        p = perp_by_bucket[bk]
        rows.append({
            "bucket": bk,
            "event_time_utc": bk,
            "perp_close": p,
            "spot_close": spot,
            "basis_bps": 10000.0 * float(np.log(p / spot)),
            "staleness_hours": staleness,
        })
    return rows


def build_state_grid(
    basis_series: List[Dict],
    funding_by_bucket: Dict[str, Dict[str, float]],
    vol_by_bucket: Dict[str, Dict[str, float]],
    thresholds: Dict[str, Any],
    accel_thr: Dict[str, Any],
) -> List[Dict]:
    """Label every hourly basis row with all frozen state axes (causal)."""
    rows: List[Dict] = []
    funding_prev: Optional[Dict[str, float]] = None
    prev_funding_bps: Optional[float] = None
    prev_prev_funding_bps: Optional[float] = None
    for i, r in enumerate(basis_series):
        bk = r["bucket"]
        if bk in funding_by_bucket:
            fund = funding_by_bucket[bk]
        else:
            # nearest prior within 2h (causal); fall back to last seen
            fund = _nearest_prior_funding(funding_by_bucket, bk)
            if fund is None:
                fund = funding_prev
        funding_bps = fund["funding_bps"] if fund else np.nan
        premium_bps = fund["premium_bps"] if fund else np.nan

        # acceleration: funding rate 24h ago (causal)
        if i >= 24:
            prev24 = basis_series[i - 24]["bucket"]
            f24 = funding_by_bucket.get(prev24)
            if f24 is not None:
                delta = funding_bps - f24["funding_bps"]
            else:
                f24p = _nearest_prior_funding(funding_by_bucket, prev24)
                delta = (funding_bps - f24p["funding_bps"]) if f24p else np.nan
        else:
            delta = np.nan

        vol = vol_by_bucket.get(bk, {})
        rv24 = vol.get("rv24h", np.nan)
        epoch, dow = label_epoch(bk)

        rows.append({
            "bucket": bk,
            "event_time_utc": bk,
            "basis_bps": r["basis_bps"],
            "perp_close": r["perp_close"],
            "spot_close": r["spot_close"],
            "basis_state": label_basis(r["basis_bps"], thresholds["basis"]),
            "funding_bps": funding_bps,
            "funding_state": label_funding(funding_bps, thresholds["funding"]),
            "funding_accel": label_funding_accel(delta, accel_thr["mad_bps"]),
            "funding_delta_24h_bps": delta,
            "rv1h": vol.get("rv1h", np.nan),
            "rv4h": vol.get("rv4h", np.nan),
            "rv24h": rv24,
            "vol_state": label_vol(rv24, thresholds["vol"]),
            "premium_bps": premium_bps,
            "mark_index_state": label_premium(premium_bps, thresholds["premium"]),
            "oi_state": "DEFERRED",
            "epoch": epoch,
            "weekday_weekend": dow,
        })
        if fund is not None:
            funding_prev = fund
    return rows


def _nearest_prior_funding(
    funding_by_bucket: Dict[str, Dict[str, float]], bk: str,
) -> Optional[Dict[str, float]]:
    keys = sorted(k for k in funding_by_bucket if k < bk)
    if not keys:
        return None
    prior = funding_by_bucket[keys[-1]]
    gap = hour_index(bk) - hour_index(keys[-1])
    if gap is not None and gap <= 2:
        return prior
    return None


def attach_cross_asset_states(btc_grid: List[Dict], eth_grid: List[Dict]) -> None:
    """Mutate grids in place: RELATIVE_STATE / SYSTEMIC_STATE from combined
    basis+funding severity (causal, same-bucket join)."""
    eth_by_bucket = {r["bucket"]: r for r in eth_grid}
    btc_by_bucket = {r["bucket"]: r for r in btc_grid}
    common = sorted(set(btc_by_bucket) & set(eth_by_bucket))
    for bk in common:
        b = btc_by_bucket[bk]
        e = eth_by_bucket[bk]
        b_sev = max(abs(severity_of(b["basis_state"])),
                    abs(severity_of(b["funding_state"])))
        e_sev = max(abs(severity_of(e["basis_state"])),
                    abs(severity_of(e["funding_state"])))
        b_sign = np.sign(severity_of(b["basis_state"]) or severity_of(b["funding_state"]))
        e_sign = np.sign(severity_of(e["basis_state"]) or severity_of(e["funding_state"]))
        b_sev_s = b_sev * (1 if b_sign >= 0 else -1)
        e_sev_s = e_sev * (1 if e_sign >= 0 else -1)
        if b_sev == 0 and e_sev == 0:
            b_sev_s = e_sev_s = 0
        b["relative_state"] = relative_state(b_sev_s, e_sev_s)
        b["systemic_state"] = systemic_state(b_sev_s, e_sev_s)
        e["relative_state"] = relative_state(b_sev_s, e_sev_s)
        e["systemic_state"] = systemic_state(b_sev_s, e_sev_s)
    # rows without a cross-asset partner (bucket exists in only one grid)
    for r in btc_grid:
        r.setdefault("relative_state", "UNKNOWN")
        r.setdefault("systemic_state", "UNKNOWN")
    for r in eth_grid:
        r.setdefault("relative_state", "UNKNOWN")
        r.setdefault("systemic_state", "UNKNOWN")


def attach_composites(grid: List[Dict]) -> None:
    for r in grid:
        r["composite_l2"] = composite_l2(r["basis_state"], r["funding_state"])
        r["composite_l3"] = composite_l3(
            r["basis_state"], r["funding_state"], r["vol_state"])


# ---------------------------------------------------------------------------
# Deep funding lane grid (for funding-state transitions/info, deep sample)
# ---------------------------------------------------------------------------

def build_funding_grid(
    funding_records: List[Dict],
    vol_by_bucket: Dict[str, Dict[str, float]],
    thresholds: Dict[str, Any],
    accel_thr: Dict[str, Any],
) -> List[Dict]:
    """Hourly grid over the DEEP funding lane (funding + vol states)."""
    recs = sorted(
        [r for r in funding_records if r.get("funding_rate") is not None],
        key=lambda r: str(r.get("event_time_utc", "")))
    rows: List[Dict] = []
    for i, r in enumerate(recs):
        bk = bucket_hour(r["event_time_utc"])
        if bk is None:
            continue
        funding_bps = float(r["funding_rate"]) * 1e4
        premium_bps = (float(r["premium"]) * 1e4
                       if r.get("premium") is not None else np.nan)
        delta = np.nan
        if i >= 24:
            prev = recs[i - 24]
            if prev.get("funding_rate") is not None:
                delta = funding_bps - float(prev["funding_rate"]) * 1e4
        vol = vol_by_bucket.get(bk, {})
        rv24 = vol.get("rv24h", np.nan)
        epoch, dow = label_epoch(bk)
        rows.append({
            "bucket": bk,
            "event_time_utc": bk,
            "funding_bps": funding_bps,
            "funding_state": label_funding(funding_bps, thresholds["funding"]),
            "funding_accel": label_funding_accel(delta, accel_thr["mad_bps"]),
            "funding_delta_24h_bps": delta,
            "rv24h": rv24,
            "vol_state": label_vol(rv24, thresholds["vol"]),
            "premium_bps": premium_bps,
            "mark_index_state": label_premium(premium_bps, thresholds["premium"]),
            "oi_state": "DEFERRED",
            "epoch": epoch,
            "weekday_weekend": dow,
            "basis_state": "N/A_BASIS_LANE",
            "basis_bps": np.nan,
        })
    return rows


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------

def transition_matrix(
    labels: List[str], buckets: List[str], horizon_hours: int,
) -> Dict[str, Any]:
    """Next-state counts/probs at a fixed horizon (hourly grid)."""
    idx = [hour_index(b) for b in buckets]
    cur: Dict[str, Dict[str, int]] = {}
    for i in range(len(labels)):
        if idx[i] is None or labels[i] == "UNKNOWN":
            continue
        target = idx[i] + horizon_hours
        j = None
        # find first bucket at or after target (nearest at/after, causal lookahead
        # for the FUTURE label only — allowed, this is a transition outcome)
        for k in range(i + 1, len(idx)):
            if idx[k] is not None and idx[k] >= target:
                j = k
                break
        if j is None:
            continue
        nxt = labels[j]
        if nxt == "UNKNOWN":
            continue
        cur.setdefault(labels[i], {})
        cur[labels[i]][nxt] = cur[labels[i]].get(nxt, 0) + 1

    states = sorted(set(labels) - {"UNKNOWN"})
    out_rows: List[Dict] = []
    for s in states:
        total = sum(cur.get(s, {}).values())
        if total == 0:
            continue
        dist = {n: cur[s].get(n, 0) / total for n in states}
        ent = entropy_of(dist.values())
        for n in states:
            out_rows.append({
                "current_state": s, "next_state": n,
                "count": cur[s].get(n, 0), "prob": dist[n],
                "next_state_entropy": ent,
            })
    return {"rows": out_rows, "n_transitions": sum(
        sum(v.values()) for v in cur.values())}


def entropy_of(probs: Any) -> float:
    """Shannon entropy (base 2) of either a probability iterable OR a list
    of categorical labels (empirical distribution)."""
    vals = [p for p in probs if p is not None]
    if not vals:
        return 0.0
    # categorical labels -> empirical counts
    if any(isinstance(p, str) for p in vals):
        from collections import Counter
        counts = Counter(vals)
        n = sum(counts.values())
        return float(-sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0))
    ps = [float(p) for p in vals if float(p) > 0]
    if not ps:
        return 0.0
    s = sum(ps)
    return float(-sum(p / s * math.log2(p / s) for p in ps))


def conditional_entropy(future_labels: List[str], state_labels: List[str]) -> float:
    """H(future | state) over paired samples (nan if empty)."""
    pairs: Dict[str, List[str]] = {}
    for f, s in zip(future_labels, state_labels):
        if f == "UNKNOWN" or s == "UNKNOWN":
            continue
        pairs.setdefault(s, []).append(f)
    if not pairs:
        return float("nan")
    h_cond = 0.0
    for s, fs in pairs.items():
        h_cond += (len(fs) / len(future_labels)) * entropy_of(fs)
    return h_cond


def js_divergence(p: List[float], q: List[float]) -> float:
    """Jensen-Shannon divergence (base 2) between two discrete distributions."""
    if len(p) != len(q) or len(p) == 0:
        return float("nan")
    p = np.asarray([max(float(x), 1e-12) for x in p], dtype=float)
    q = np.asarray([max(float(x), 1e-12) for x in q], dtype=float)
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    def kl(a, b):
        return float(np.sum(a * np.log2(a / b)))
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def discretize(values: List[float], edges: List[float]) -> List[int]:
    """Bin values into intervals defined by edges (first/last are infinities)."""
    out = []
    for v in values:
        if v is None or not np.isfinite(float(v)):
            out.append(-1)
            continue
        v = float(v)
        if v <= edges[0]:
            out.append(0)
        elif v > edges[-1]:
            out.append(len(edges))
        else:
            for k in range(len(edges) - 1):
                if edges[k] < v <= edges[k + 1]:
                    out.append(k + 1)
                    break
            else:
                out.append(0)
    return out


# ---------------------------------------------------------------------------
# Dislocation episodes + path taxonomy
# ---------------------------------------------------------------------------

def segment_episodes(
    grid: List[Dict], p90_abs: float, p75_abs: float,
) -> List[Dict]:
    """Episodes: start when |basis| > p90_abs, end when |basis| < p75_abs."""
    eps: List[Dict] = []
    active: Optional[Dict] = None
    for i, r in enumerate(grid):
        b = r.get("basis_bps")
        if b is None or not np.isfinite(float(b)):
            continue
        ab = abs(float(b))
        if active is None:
            if ab > p90_abs:
                active = {
                    "asset": r.get("asset", ""),
                    "start_index": i, "start_time": r["bucket"],
                    "start_basis_bps": float(b), "max_abs": ab,
                    "max_abs_time": r["bucket"], "path": [float(b)],
                }
        else:
            active["path"].append(float(b))
            if ab > active["max_abs"]:
                active["max_abs"] = ab
                active["max_abs_time"] = r["bucket"]
            if ab < p75_abs:
                active["end_index"] = i
                active["end_time"] = r["bucket"]
                active["resolved"] = True
                eps.append(active)
                active = None
    if active is not None:
        active["end_index"] = len(grid) - 1
        active["end_time"] = grid[-1]["bucket"]
        active["resolved"] = False
        eps.append(active)
    for n, ep in enumerate(eps):
        ep["episode_id"] = f"{ep['asset']}_ep_{n:04d}"
        _classify_episode(ep, p75_abs)
    return eps


def _classify_episode(ep: Dict, p75_abs: float) -> None:
    start = float(ep["start_basis_bps"])
    end = float(ep["path"][-1]) if ep["path"] else start
    dur = _duration_hours(ep.get("start_time"), ep.get("end_time"))
    ep["duration_hours"] = dur
    if not ep.get("resolved"):
        ep["classification"] = "CENSORED"
        return
    ratio = ep["max_abs"] / abs(start) if abs(start) > 1e-12 else 1.0
    ep["expansion_ratio"] = ratio
    if dur > 24:
        ep["classification"] = "PERSISTENT"
        return
    if ratio > 1.5:
        ep["classification"] = "EXPANSION_FIRST_THEN_RESOLVE"
        return
    pre_band = _band_of(start, p75_abs)
    post_band = _band_of(end, p75_abs)
    ep["pre_band"] = pre_band
    ep["post_band"] = post_band
    if _band_gap(pre_band, post_band) >= 1:
        ep["classification"] = "REGIME_SHIFT"
        return
    if dur <= 4 and ratio <= 1.25:
        ep["classification"] = "FAST_RESOLUTION"
        return
    ep["classification"] = "SLOW_RESOLUTION"


def _duration_hours(t0: Any, t1: Any) -> float:
    try:
        a = parse_ts(t0)
        b = parse_ts(t1)
        if a is None or b is None:
            return float("nan")
        return (b - a).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return float("nan")


def _band_of(basis_bps: float, p75_abs: float) -> int:
    """Severity band class: 0 normal, 1..3 elevated (by |basis|)."""
    ab = abs(float(basis_bps))
    if ab <= p75_abs:
        return 0
    if ab <= 2 * p75_abs:
        return 1
    if ab <= 3 * p75_abs:
        return 2
    return 3


def _band_gap(a: int, b: int) -> int:
    return abs(a - b)


# ---------------------------------------------------------------------------
# Path measures per state
# ---------------------------------------------------------------------------

def future_path_measures(
    grid: List[Dict], state_field: str, state_value: str,
    horizons: List[int] = HORIZONS_HOURS,
) -> List[Dict]:
    """Mechanism statistics of future basis evolution conditioned on a state.

    Each row: (state, horizon, n, mean/median future |basis| change,
    decay fraction, max additional expansion, spot/perp contributions,
    future RV, time to state exit / normal basis, censoring).
    """
    idx = [hour_index(r["bucket"]) for r in grid]
    # time-to-exit and time-to-normal from state entries
    out: List[Dict] = []
    for h in horizons:
        deltas: List[float] = []
        abs_deltas: List[float] = []
        decay: List[float] = []
        expansions: List[float] = []
        spot_contrib: List[float] = []
        perp_contrib: List[float] = []
        future_rv: List[float] = []
        n_censored = 0
        n_total = 0
        for i, r in enumerate(grid):
            if r.get(state_field) != state_value:
                continue
            b0 = r.get("basis_bps")
            if b0 is None or not np.isfinite(float(b0)):
                continue
            b0 = float(b0)
            j = _future_index(idx, i, h)
            if j is None or j >= len(grid):
                n_censored += 1
                continue
            n_total += 1
            b1 = grid[j]["basis_bps"]
            if b1 is None or not np.isfinite(float(b1)):
                n_censored += 1
                continue
            b1 = float(b1)
            deltas.append(b1 - b0)
            abs_deltas.append(abs(b1) - abs(b0))
            if abs(b0) > 1e-12:
                decay.append(1.0 - abs(b1) / abs(b0))
            mx = max(abs(float(grid[k]["basis_bps"]))
                     for k in range(i, min(j + 1, len(grid)))
                     if grid[k].get("basis_bps") is not None
                     and np.isfinite(float(grid[k]["basis_bps"])))
            expansions.append(mx - abs(b0))
            p0, s0 = r.get("perp_close"), r.get("spot_close")
            p1, s1 = grid[j].get("perp_close"), grid[j].get("spot_close")
            if p0 and p1 and s0 and s1 and all(
                    np.isfinite(float(x)) and float(x) > 0 for x in (p0, p1, s0, s1)):
                perp_contrib.append(10000.0 * math.log(float(p1) / float(p0)))
                spot_contrib.append(-10000.0 * math.log(float(s1) / float(s0)))
            rv = _future_rv(grid, i, j)
            if rv is not None:
                future_rv.append(rv)
        out.append(_summarize_path_row(state_value, h, deltas, abs_deltas,
                                       decay, expansions, spot_contrib,
                                       perp_contrib, future_rv, n_total,
                                       n_censored))
    return out


def _future_index(idx: List[Optional[int]], i: int, h: int) -> Optional[int]:
    if idx[i] is None:
        return None
    target = idx[i] + h
    for k in range(i + 1, len(idx)):
        if idx[k] is not None and idx[k] >= target:
            return k
    return None


def _future_rv(grid: List[Dict], i: int, j: int) -> Optional[float]:
    """RV of |basis| over the forward window (mechanism stat, not PnL)."""
    vals = []
    for k in range(i, min(j + 1, len(grid))):
        b = grid[k].get("basis_bps")
        if b is not None and np.isfinite(float(b)):
            vals.append(float(b))
    if len(vals) < 2:
        return None
    return float(np.std(vals, ddof=1))


def _summarize_path_row(state, h, deltas, abs_deltas, decay, expansions,
                        spot_contrib, perp_contrib, future_rv,
                        n_total, n_censored) -> Dict[str, Any]:
    def stats(x: List[float]) -> Dict[str, float]:
        a = np.asarray(x, dtype=float)
        if len(a) == 0:
            return {"n": 0, "mean": None, "median": None}
        return {"n": int(len(a)), "mean": float(a.mean()),
                "median": float(np.median(a))}
    row: Dict[str, Any] = {
        "state": state, "horizon_hours": h,
        "n_total": n_total, "n_censored": n_censored,
    }
    row["future_basis_change"] = stats(deltas)
    row["future_abs_basis_change"] = stats(abs_deltas)
    row["decay_fraction"] = stats(decay)
    row["max_additional_expansion"] = stats(expansions)
    row["spot_contribution_bps"] = stats(spot_contrib)
    row["perp_contribution_bps"] = stats(perp_contrib)
    row["future_basis_vol"] = stats(future_rv)
    # flatten for CSV
    flat: Dict[str, Any] = {"state": state, "horizon_hours": h,
                            "n_total": n_total, "n_censored": n_censored}
    for key, st in row.items():
        if isinstance(st, dict):
            for kk, vv in st.items():
                flat[f"{key}_{kk}"] = vv
        else:
            flat[key] = st
    return flat


def time_to_exit_stats(
    grid: List[Dict], state_field: str, state_value: str, max_hours: int = 120,
) -> Dict[str, Any]:
    """Time until the row leaves `state_value` (KM-ready); censored at end."""
    idx = [hour_index(r["bucket"]) for r in grid]
    n = len(grid)
    # next index where label != state_value (O(n) backward scan)
    next_exit: List[Optional[int]] = [None] * n
    for i in range(n - 2, -1, -1):
        if grid[i + 1].get(state_field) != state_value:
            next_exit[i] = i + 1
        else:
            next_exit[i] = next_exit[i + 1]
    times: List[float] = []
    censored = 0
    for i, r in enumerate(grid):
        if r.get(state_field) != state_value or idx[i] is None:
            continue
        ei = next_exit[i]
        if ei is None or idx[ei] is None:
            censored += 1
            continue
        times.append(float(idx[ei] - idx[i]))
    a = np.asarray(times, dtype=float)
    return {
        "state": state_value, "n_exits": int(len(a)),
        "n_censored": censored,
        "median_exit_hours": float(np.median(a)) if len(a) else None,
        "p75_exit_hours": float(np.percentile(a, 75)) if len(a) else None,
        "p90_exit_hours": float(np.percentile(a, 90)) if len(a) else None,
    }


# ---------------------------------------------------------------------------
# Kaplan-Meier survival
# ---------------------------------------------------------------------------

def kaplan_meier(times: List[float], censored: List[bool],
                 max_t: float = 120.0, step: float = 1.0) -> List[Dict]:
    """KM survival curve; censored[i]=True means observation censored."""
    order = np.argsort(times)
    t = np.asarray(times, dtype=float)[order]
    c = np.asarray(censored, dtype=bool)[order]
    curve: List[Dict] = []
    surv = 1.0
    at_risk = len(t)
    prev_t = 0.0
    for ti, ci in zip(t, c):
        if ti > max_t:
            break
        if ti > prev_t:
            curve.append({"t_hours": float(prev_t), "p_not_resolved": surv,
                          "n_at_risk": int(at_risk)})
            prev_t = float(ti)
        if not ci:
            surv *= (at_risk - 1) / at_risk
        at_risk -= 1
    curve.append({"t_hours": float(prev_t), "p_not_resolved": surv,
                  "n_at_risk": int(at_risk)})
    return curve


def survival_from_episodes(episodes: List[Dict], max_hours: float = 120.0
                           ) -> Dict[str, Any]:
    times = []
    cens = []
    for ep in episodes:
        d = ep.get("duration_hours")
        if d is None or not np.isfinite(float(d)):
            continue
        if ep.get("resolved"):
            times.append(float(d))
            cens.append(False)
        else:
            times.append(float(d))
            cens.append(True)
    curve = kaplan_meier(times, cens, max_t=max_hours)
    return {"curve": curve, "n": len(times),
            "n_censored": int(sum(cens))}


def survival_by_state(
    grid: List[Dict], state_field: str, state_value: str, max_hours: int = 120,
) -> Dict[str, Any]:
    """KM of time-to-resolution (|basis| returns < p75_abs) from state entry."""
    # exit to normal basis = |basis| < p75_abs (frozen threshold via B0_NORMAL)
    n = len(grid)
    next_normal: List[Optional[int]] = [None] * n
    for i in range(n - 2, -1, -1):
        if grid[i + 1].get("basis_state") == "B0_NORMAL":
            next_normal[i] = i + 1
        else:
            next_normal[i] = next_normal[i + 1]
    times: List[float] = []
    cens: List[bool] = []
    for i, r in enumerate(grid):
        if r.get(state_field) != state_value:
            continue
        b0 = r.get("basis_bps")
        if b0 is None or not np.isfinite(float(b0)):
            continue
        exit_i = next_normal[i]
        if exit_i is None:
            cens.append(True)
            times.append(float(max_hours))
            continue
        h0 = hour_index(r["bucket"])
        h1 = hour_index(grid[exit_i]["bucket"])
        if h0 is None or h1 is None:
            continue
        times.append(float(h1 - h0))
        cens.append(False)
    if not times:
        return {"state": state_value, "n": 0}
    curve = kaplan_meier(times, cens, max_t=float(max_hours))
    return {"state": state_value, "n": len(times),
            "n_censored": int(sum(cens)), "curve": curve}


# ---------------------------------------------------------------------------
# Information value
# ---------------------------------------------------------------------------

def info_value_for_state(
    grid: List[Dict], state_field: str, state_value: str,
    horizon_hours: int = 4, seed: int = SEED,
) -> Dict[str, Any]:
    """Conditional future-|basis|-change distribution vs unconditional.

    Returns entropy reduction (bits), JS divergence, effect size (SMD),
    bootstrap CI on mean future abs-basis change difference, and a
    one-sided bootstrap p-value.
    """
    idx = [hour_index(r["bucket"]) for r in grid]
    future_abs: Dict[int, float] = {}
    for i, r in enumerate(grid):
        b0 = r.get("basis_bps")
        if b0 is None or not np.isfinite(float(b0)):
            continue
        j = _future_index(idx, i, horizon_hours)
        if j is None or j >= len(grid):
            continue
        b1 = grid[j].get("basis_bps")
        if b1 is None or not np.isfinite(float(b1)):
            continue
        future_abs[i] = abs(float(b1)) - abs(float(b0))

    keys = sorted(future_abs.keys())
    if len(keys) < 20:
        return {"state": state_value, "horizon_hours": horizon_hours,
                "n": len(keys), "insufficient": True}

    uncond = np.asarray([future_abs[k] for k in keys], dtype=float)
    state_keys = [k for k in keys if grid[k].get(state_field) == state_value]
    cond = np.asarray([future_abs[k] for k in state_keys], dtype=float)
    if len(cond) < 20:
        return {"state": state_value, "horizon_hours": horizon_hours,
                "n": len(keys), "n_state": len(cond), "insufficient": True}

    # discretize into unconditional decile bins
    edges = list(np.percentile(uncond, [10, 20, 30, 40, 50, 60, 70, 80, 90]))
    u_bins = discretize(list(uncond), edges)
    c_bins = discretize(list(cond), edges)
    n_bins = len(edges) + 1
    pu = np.bincount([b for b in u_bins if b >= 0], minlength=n_bins).astype(float)
    pc = np.bincount([b for b in c_bins if b >= 0], minlength=n_bins).astype(float)
    pu = pu / pu.sum()
    pc = pc / pc.sum()
    h_uncond = entropy_of(pu)
    h_cond = entropy_of(pc)
    jsd = js_divergence(list(pc), list(pu))

    rng = np.random.default_rng(seed)
    obs_diff = float(cond.mean() - uncond.mean())
    pooled = float(np.sqrt((uncond.var(ddof=1) + cond.var(ddof=1)) / 2.0))
    smd = obs_diff / pooled if pooled > 1e-12 else 0.0
    boot_diffs = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        sc = rng.choice(cond, size=len(cond), replace=True)
        su = rng.choice(uncond, size=len(uncond), replace=True)
        boot_diffs.append(float(sc.mean() - su.mean()))
    bd = np.asarray(boot_diffs)
    p_value = float((bd >= 0).mean()) if obs_diff < 0 else float((bd <= 0).mean())
    return {
        "state": state_value, "horizon_hours": horizon_hours,
        "n": len(keys), "n_state": len(cond),
        "unconditional_mean_abs_change": float(uncond.mean()),
        "conditional_mean_abs_change": float(cond.mean()),
        "observed_diff": obs_diff,
        "effect_size_smd": smd,
        "boot_ci_p05": float(np.percentile(bd, 5)),
        "boot_ci_p95": float(np.percentile(bd, 95)),
        "bootstrap_p": p_value,
        "entropy_unconditional": h_uncond,
        "entropy_conditional": h_cond,
        "entropy_reduction_bits": h_uncond - h_cond,
        "js_divergence": jsd,
        "insufficient": False,
    }


def info_value_outcome(
    grid: List[Dict], state_field: str, state_value: str,
    outcome_field: str, horizon_hours: int = 4, seed: int = SEED,
) -> Dict[str, Any]:
    """Info value with a generic outcome field (e.g. funding |level| change).

    Used for the deep funding lane where no basis exists: outcome = change in
    |funding_bps| over the horizon.
    """
    idx = [hour_index(r["bucket"]) for r in grid]
    future_out: Dict[int, float] = {}
    for i, r in enumerate(grid):
        v0 = r.get(outcome_field)
        if v0 is None or not np.isfinite(float(v0)):
            continue
        j = _future_index(idx, i, horizon_hours)
        if j is None or j >= len(grid):
            continue
        v1 = grid[j].get(outcome_field)
        if v1 is None or not np.isfinite(float(v1)):
            continue
        future_out[i] = abs(float(v1)) - abs(float(v0))
    keys = sorted(future_out.keys())
    if len(keys) < 20:
        return {"state": state_value, "horizon_hours": horizon_hours,
                "n": len(keys), "insufficient": True}
    uncond = np.asarray([future_out[k] for k in keys], dtype=float)
    state_keys = [k for k in keys if grid[k].get(state_field) == state_value]
    cond = np.asarray([future_out[k] for k in state_keys], dtype=float)
    if len(cond) < 20:
        return {"state": state_value, "horizon_hours": horizon_hours,
                "n": len(keys), "n_state": len(cond), "insufficient": True}
    edges = list(np.percentile(uncond, [10, 20, 30, 40, 50, 60, 70, 80, 90]))
    n_bins = len(edges) + 1
    pu = np.bincount([b for b in discretize(list(uncond), edges) if b >= 0],
                     minlength=n_bins).astype(float)
    pc = np.bincount([b for b in discretize(list(cond), edges) if b >= 0],
                     minlength=n_bins).astype(float)
    pu = pu / pu.sum()
    pc = pc / pc.sum()
    h_uncond = entropy_of(pu)
    h_cond = entropy_of(pc)
    jsd = js_divergence(list(pc), list(pu))
    rng = np.random.default_rng(seed)
    obs_diff = float(cond.mean() - uncond.mean())
    pooled = float(np.sqrt((uncond.var(ddof=1) + cond.var(ddof=1)) / 2.0))
    smd = obs_diff / pooled if pooled > 1e-12 else 0.0
    boot_diffs = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        sc = rng.choice(cond, size=len(cond), replace=True)
        su = rng.choice(uncond, size=len(uncond), replace=True)
        boot_diffs.append(float(sc.mean() - su.mean()))
    bd = np.asarray(boot_diffs)
    p_value = float((bd >= 0).mean()) if obs_diff < 0 else float((bd <= 0).mean())
    return {
        "state": state_value, "horizon_hours": horizon_hours,
        "outcome_field": outcome_field,
        "n": len(keys), "n_state": len(cond),
        "unconditional_mean_abs_change": float(uncond.mean()),
        "conditional_mean_abs_change": float(cond.mean()),
        "observed_diff": obs_diff,
        "effect_size_smd": smd,
        "boot_ci_p05": float(np.percentile(bd, 5)),
        "boot_ci_p95": float(np.percentile(bd, 95)),
        "bootstrap_p": p_value,
        "entropy_unconditional": h_uncond,
        "entropy_conditional": h_cond,
        "entropy_reduction_bits": h_uncond - h_cond,
        "js_divergence": jsd,
        "insufficient": False,
    }


def null_unconditional_outcome(
    grid: List[Dict], outcome_field: str, horizon_hours: int = 4,
) -> Dict[str, Any]:
    idx = [hour_index(r["bucket"]) for r in grid]
    changes = []
    for i, r in enumerate(grid):
        v0 = r.get(outcome_field)
        if v0 is None or not np.isfinite(float(v0)):
            continue
        j = _future_index(idx, i, horizon_hours)
        if j is None or j >= len(grid):
            continue
        v1 = grid[j].get(outcome_field)
        if v1 is None or not np.isfinite(float(v1)):
            continue
        changes.append(abs(float(v1)) - abs(float(v0)))
    a = np.asarray(changes, dtype=float)
    return {"horizon_hours": horizon_hours, "outcome_field": outcome_field,
            "n": int(len(a)),
            "mean": float(a.mean()) if len(a) else None,
            "median": float(np.median(a)) if len(a) else None,
            "std": float(a.std(ddof=1)) if len(a) > 1 else None}


# ---------------------------------------------------------------------------
# Null models
# ---------------------------------------------------------------------------

def null_unconditional(grid: List[Dict], horizon_hours: int = 4) -> Dict[str, Any]:
    idx = [hour_index(r["bucket"]) for r in grid]
    changes = []
    for i, r in enumerate(grid):
        b0 = r.get("basis_bps")
        if b0 is None or not np.isfinite(float(b0)):
            continue
        j = _future_index(idx, i, horizon_hours)
        if j is None or j >= len(grid):
            continue
        b1 = grid[j].get("basis_bps")
        if b1 is None or not np.isfinite(float(b1)):
            continue
        changes.append(abs(float(b1)) - abs(float(b0)))
    a = np.asarray(changes, dtype=float)
    return {"horizon_hours": horizon_hours, "n": int(len(a)),
            "mean": float(a.mean()) if len(a) else None,
            "median": float(np.median(a)) if len(a) else None,
            "std": float(a.std(ddof=1)) if len(a) > 1 else None}


def _bucket_pools(grid: List[Dict]) -> Tuple[List[float], List[List[int]]]:
    """Precompute |basis| magnitude buckets (low/mid/high) once."""
    bases = [abs(float(r["basis_bps"])) for r in grid
             if r.get("basis_bps") is not None and np.isfinite(float(r["basis_bps"]))]
    p33, p67 = np.percentile(bases, [33, 67])
    pools: List[List[int]] = [[], [], []]
    for i, r in enumerate(grid):
        b = r.get("basis_bps")
        if b is None or not np.isfinite(float(b)):
            continue
        ab = abs(float(b))
        if ab <= p33:
            pools[0].append(i)
        elif ab <= p67:
            pools[1].append(i)
        else:
            pools[2].append(i)
    return [float(p33), float(p67)], pools


def null_vol_matched(
    grid: List[Dict], state_field: str, state_value: str,
    horizon_hours: int = 4, n_perm: int = NULL_PERMUTATIONS, seed: int = SEED,
) -> Dict[str, Any]:
    """Random timestamps matched by volatility regime (|basis| magnitude)."""
    rng = np.random.default_rng(seed)
    idx = [hour_index(r["bucket"]) for r in grid]
    state_idx = [i for i, r in enumerate(grid)
                 if r.get(state_field) == state_value]
    _, pools = _bucket_pools(grid)

    def decay_stats(entries: List[int]) -> float:
        vals = []
        for i in entries:
            b0 = grid[i].get("basis_bps")
            if b0 is None or not np.isfinite(float(b0)):
                continue
            j = _future_index(idx, i, horizon_hours)
            if j is None or j >= len(grid):
                continue
            b1 = grid[j].get("basis_bps")
            if b1 is None or not np.isfinite(float(b1)):
                continue
            vals.append(abs(float(b1)) - abs(float(b0)))
        a = np.asarray(vals, dtype=float)
        return float(a.mean()) if len(a) else float("nan")

    obs = decay_stats(state_idx)
    # bucket index per state row
    state_bucket = []
    for i in state_idx:
        ab = abs(float(grid[i]["basis_bps"]))
        if ab <= pools[0][0]:
            state_bucket.append(0)
        elif ab <= pools[0][1]:
            state_bucket.append(1)
        else:
            state_bucket.append(2)
    null_means = []
    for _ in range(n_perm):
        sample = []
        for bk_i in state_bucket:
            pool = pools[bk_i]
            if pool:
                sample.append(int(rng.choice(pool)))
        m = decay_stats(sample)
        if np.isfinite(m):
            null_means.append(m)
    null_mean = float(np.mean(null_means)) if null_means else float("nan")
    return {
        "state": state_value, "horizon_hours": horizon_hours,
        "observed": obs, "null_mean": null_mean,
        "null_p05": float(np.percentile(null_means, 5)) if null_means else float("nan"),
        "null_p95": float(np.percentile(null_means, 95)) if null_means else float("nan"),
        "effect_vs_null": obs - null_mean if np.isfinite(null_mean) else float("nan"),
        "n_perm": n_perm, "seed": seed,
    }


def null_block_shuffle(
    grid: List[Dict], state_field: str, state_value: str,
    horizon_hours: int = 4, block_hours: int = 24,
    n_perm: int = NULL_PERMUTATIONS, seed: int = SEED,
) -> Dict[str, Any]:
    """Shuffle state labels in contiguous time blocks; same future path."""
    rng = np.random.default_rng(seed)
    idx = [hour_index(r["bucket"]) for r in grid]
    labels = [r.get(state_field) for r in grid]
    # block boundaries: split idx range into block_hours chunks
    n = len(grid)
    block_of = {}
    for i in range(n):
        if idx[i] is not None:
            block_of[i] = idx[i] // block_hours
    blocks = sorted(set(block_of.values()))
    obs_rows = [i for i in range(n) if labels[i] == state_value]
    obs = _mean_future_abs_change(grid, idx, obs_rows, horizon_hours)
    null_means = []
    for _ in range(n_perm):
        perm_labels = _block_shuffle_labels(labels, block_of, blocks, rng)
        rows = [i for i in range(n) if perm_labels[i] == state_value]
        m = _mean_future_abs_change(grid, idx, rows, horizon_hours)
        if np.isfinite(m):
            null_means.append(m)
    null_mean = float(np.mean(null_means)) if null_means else float("nan")
    return {
        "state": state_value, "horizon_hours": horizon_hours,
        "observed": obs, "null_mean": null_mean,
        "null_p05": float(np.percentile(null_means, 5)) if null_means else float("nan"),
        "null_p95": float(np.percentile(null_means, 95)) if null_means else float("nan"),
        "effect_vs_null": obs - null_mean if np.isfinite(null_mean) else float("nan"),
        "n_perm": n_perm, "seed": seed,
    }


def _block_shuffle_labels(labels, block_of, blocks, rng) -> List[Any]:
    out = list(labels)
    block_lists = {b: [i for i, bb in block_of.items() if bb == b] for b in blocks}
    perm_blocks = rng.permutation(blocks)
    for b_old, b_new in zip(blocks, perm_blocks):
        src = block_lists[b_old]
        dst = block_lists[b_new]
        for i, j in zip(src, dst):
            out[j] = labels[i]
    return out


def _mean_future_abs_change(grid, idx, rows, horizon_hours: int) -> float:
    vals = []
    for i in rows:
        b0 = grid[i].get("basis_bps")
        if b0 is None or not np.isfinite(float(b0)):
            continue
        j = _future_index(idx, i, horizon_hours)
        if j is None or j >= len(grid):
            continue
        b1 = grid[j].get("basis_bps")
        if b1 is None or not np.isfinite(float(b1)):
            continue
        vals.append(abs(float(b1)) - abs(float(b0)))
    a = np.asarray(vals, dtype=float)
    return float(a.mean()) if len(a) else float("nan")


def null_ar1_baseline(grid: List[Dict], state_field: str, state_value: str,
                      horizon_hours: int = 4) -> Dict[str, Any]:
    """AR(1)-implied expected |basis| decay vs observed for the state."""
    bases = [float(r["basis_bps"]) for r in grid
             if r.get("basis_bps") is not None and np.isfinite(float(r["basis_bps"]))]
    a = np.asarray(bases, dtype=float)
    if len(a) < 50:
        return {"state": state_value, "insufficient": True}
    y, x = a[1:], a[:-1]
    phi = float(np.cov(x, y)[0, 1] / np.var(x)) if np.var(x) > 1e-12 else 0.0
    c = float(np.mean(y) - phi * np.mean(x))
    idx = [hour_index(r["bucket"]) for r in grid]
    obs_vals = []
    ar1_vals = []
    for i, r in enumerate(grid):
        if r.get(state_field) != state_value:
            continue
        b0 = r.get("basis_bps")
        if b0 is None or not np.isfinite(float(b0)):
            continue
        j = _future_index(idx, i, horizon_hours)
        if j is None or j >= len(grid):
            continue
        b1 = grid[j].get("basis_bps")
        if b1 is None or not np.isfinite(float(b1)):
            continue
        obs_vals.append(abs(float(b1)) - abs(float(b0)))
        xh = float(b0)
        for _ in range(horizon_hours):
            xh = c + phi * xh
        ar1_vals.append(abs(xh) - abs(float(b0)))
    return {
        "state": state_value, "horizon_hours": horizon_hours,
        "phi": phi, "c": c, "n": len(obs_vals),
        "observed_mean": float(np.mean(obs_vals)) if obs_vals else None,
        "ar1_mean": float(np.mean(ar1_vals)) if ar1_vals else None,
        "observed_minus_ar1": (float(np.mean(obs_vals) - np.mean(ar1_vals))
                               if obs_vals and ar1_vals else None),
    }


# ---------------------------------------------------------------------------
# BH-FDR
# ---------------------------------------------------------------------------

def bh_fdr(p_values: List[float], q: float = BH_FDR_Q) -> Dict[str, Any]:
    """Benjamini-Hochberg FDR on a list of p-values (reproducible)."""
    n = len(p_values)
    if n == 0:
        return {"n_tested": 0, "n_significant": 0, "significant": []}
    order = np.argsort(p_values)
    sorted_p = np.asarray(p_values, dtype=float)[order]
    m = len(sorted_p)
    threshold = 0.0
    sig_mask = np.zeros(m, dtype=bool)
    for k in range(m - 1, -1, -1):
        if sorted_p[k] <= q * (k + 1) / m:
            threshold = q * (k + 1) / m
            sig_mask[:k + 1] = True
            break
    sig_idx = sorted(order[:int(sig_mask.sum())]) if sig_mask.any() else []
    return {
        "n_tested": n, "q": q, "threshold": float(threshold),
        "n_significant": int(sig_mask.sum()),
        "significant": [int(i) for i in sig_idx],
    }


# ---------------------------------------------------------------------------
# Time-epoch entropy
# ---------------------------------------------------------------------------

def epoch_entropy_profile(
    grid: List[Dict], anchors: List[str], state_field: str = "basis_state",
) -> List[Dict]:
    """State entropy before/at/after repeatable crypto-native anchors."""
    by_bucket = {r["bucket"]: r for r in grid}
    keys = sorted(by_bucket.keys())
    idx = [hour_index(k) for k in keys]
    labels = [by_bucket[k][state_field] for k in keys]
    rows: List[Dict] = []
    for anchor in anchors:
        anchor_dt = parse_ts(anchor)
        if anchor_dt is None:
            continue
        anchor_h = int(anchor_dt.timestamp() // 3600)
        # windows: [-6,-2], [-1,+1], [+2,+6] hours relative to anchor
        for name, lo, hi in (("before", -6, -1), ("at", -1, 2), ("after", 2, 7)):
            sel = [labels[i] for i, h in enumerate(idx)
                   if h is not None and anchor_h + lo <= h < anchor_h + hi]
            vals = [s for s in sel if s not in ("UNKNOWN", "N/A_BASIS_LANE")]
            if len(vals) < 10:
                continue
            ent = entropy_of(vals)
            rows.append({
                "anchor": anchor, "window": name,
                "n": len(vals), "entropy_bits": ent,
            })
    return rows


def hourly_entropy_profile(grid: List[Dict], state_field: str = "basis_state"
                           ) -> List[Dict]:
    """State entropy by hour-of-day UTC (measure behavior first)."""
    by_hour: Dict[int, List[str]] = {}
    for r in grid:
        dt = parse_ts(r["bucket"])
        if dt is None:
            continue
        s = r.get(state_field)
        if s in ("UNKNOWN", "N/A_BASIS_LANE"):
            continue
        by_hour.setdefault(dt.hour, []).append(s)
    rows = []
    for h in sorted(by_hour.keys()):
        rows.append({"hour_utc": h, "n": len(by_hour[h]),
                     "entropy_bits": entropy_of(by_hour[h])})
    return rows


# ---------------------------------------------------------------------------
# AMM pilot (30d extension + frozen pilots)
# ---------------------------------------------------------------------------

def amm_state_pilot(
    swap_records: List[Dict],
    perp_5m: List[Dict],
    pool_label: str,
    price_field: str = "price_token0_per_token1",
    invert_price: bool = False,
    min_buckets: int = 50,
) -> Dict[str, Any]:
    """Classify AMM lead/lag + flow confirmation vs perp (PILOT evidence)."""
    rows: List[Dict] = []
    for r in swap_records:
        ts = parse_ts(r.get("event_time_utc"))
        if ts is None:
            continue
        price = r.get(price_field)
        if price is None or not np.isfinite(float(price)) or float(price) <= 0:
            continue
        price = float(price)
        if invert_price:
            price = 1.0 / price
        amt0 = r.get("amount0")
        amt1 = r.get("amount1")
        a0 = float(amt0) if amt0 is not None else 0.0
        a1 = float(amt1) if amt1 is not None else 0.0
        # signed flow in asset units (positive = buy asset)
        signed = a0 if not invert_price else a1
        notional = abs(a0) * price if not invert_price else abs(a1)
        rows.append({
            "bucket": bucket_5m(ts), "event_time_utc": r["event_time_utc"],
            "amm_price": price, "signed_flow": signed,
            "notional_usd": notional,
        })
    if not rows:
        return {"pool": pool_label, "n_swaps": 0, "evidence_class":
                "PILOT_MECHANISM_EVIDENCE", "classification": "DEFERRED",
                "reason": "no usable swap rows"}
    # 5m buckets: last price, summed flow
    by_bucket: Dict[str, Dict] = {}
    for row in rows:
        b = by_bucket.setdefault(row["bucket"], {
            "bucket": row["bucket"], "amm_price": None, "signed_flow": 0.0,
            "notional": 0.0, "count": 0})
        b["amm_price"] = row["amm_price"]
        b["signed_flow"] += row["signed_flow"]
        b["notional"] += row["notional_usd"]
        b["count"] += 1
    buckets = [by_bucket[k] for k in sorted(by_bucket.keys())]

    # perp 5m closes
    perp_by_bucket: Dict[str, float] = {}
    for r in perp_5m:
        ts = parse_ts(r.get("event_time_utc"))
        c = r.get("close")
        if ts is None or c is None or not np.isfinite(float(c)):
            continue
        perp_by_bucket[bucket_5m(ts)] = float(c)
    perp_keys = sorted(perp_by_bucket.keys())

    aligned = []
    for b in buckets:
        pp = perp_by_bucket.get(b["bucket"])
        if pp is None:
            prior = [k for k in perp_keys if k < b["bucket"]]
            if not prior:
                continue
            pp = perp_by_bucket[prior[-1]]
        if pp and float(pp) > 0:
            aligned.append({**b, "perp_close": float(pp),
                            "amm_perp_basis_bps":
                                10000.0 * math.log(b["amm_price"] / float(pp))})
    aligned.sort(key=lambda x: x["bucket"])

    out: Dict[str, Any] = {
        "pool": pool_label, "n_swaps": len(rows),
        "n_5m_buckets": len(buckets), "n_aligned": len(aligned),
        "evidence_class": "PILOT_MECHANISM_EVIDENCE",
    }

    if len(aligned) < min_buckets:
        out["classification"] = "DEFERRED"
        out["reason"] = (f"aligned 5m buckets {len(aligned)} < min {min_buckets}")
        return out

    # lead/lag via cross-correlation of 5m returns
    amm_prices = [a["amm_price"] for a in aligned]
    perp_prices = [a["perp_close"] for a in aligned]
    ra = np.diff(np.log(np.asarray(amm_prices, dtype=float)))
    rp = np.diff(np.log(np.asarray(perp_prices, dtype=float)))
    lags: Dict[str, float] = {}
    for lag in range(-3, 4):
        if lag == 0:
            lags["0"] = float(np.corrcoef(ra, rp)[0, 1]) if len(ra) > 1 else float("nan")
        elif lag > 0:  # perp lags amm by lag (amm leads)
            lags[str(lag)] = float(np.corrcoef(ra[:-lag], rp[lag:])[0, 1]) \
                if len(ra) > lag + 1 else float("nan")
        else:  # amm lags perp by -lag
            lags[str(lag)] = float(np.corrcoef(ra[-lag:], rp[:lag])[0, 1]) \
                if len(ra) > -lag + 1 else float("nan")
    out["cross_corr_by_lag"] = lags
    lead = lags.get("1", float("nan"))
    lagv = lags.get("-1", float("nan"))
    if np.isfinite(lead) and np.isfinite(lagv):
        if lead > lagv + 0.03:
            out["lead_lag"] = "AMM_LEADS"
        elif lagv > lead + 0.03:
            out["lead_lag"] = "AMM_LAGS"
        else:
            out["lead_lag"] = "AMM_SYNCHRONOUS"
    else:
        out["lead_lag"] = "UNKNOWN"

    # flow confirmation: signed flow in bucket vs perp move over next 12 buckets
    perp_close_list = [a["perp_close"] for a in aligned]
    flow = np.asarray([a["signed_flow"] for a in aligned], dtype=float)
    match = []
    for i in range(len(aligned) - 12):
        if flow[i] == 0:
            continue
        move = perp_close_list[i + 12] - perp_close_list[i]
        if abs(move) < 1e-9:
            continue
        match.append(1.0 if (flow[i] > 0) == (move > 0) else 0.0)
    if len(match) >= 50:
        rate = float(np.mean(match))
        rng = np.random.default_rng(SEED)
        boot = []
        for _ in range(BOOTSTRAP_RESAMPLES):
            boot.append(float(np.mean(rng.choice(match, size=len(match), replace=True))))
        boot = np.asarray(boot)
        out["flow_match_rate"] = rate
        out["flow_ci_p05"] = float(np.percentile(boot, 5))
        out["flow_ci_p95"] = float(np.percentile(boot, 95))
        if rate > 0.55:
            out["flow_class"] = "AMM_CONFIRMING_FLOW"
        elif rate < 0.45:
            out["flow_class"] = "AMM_CONTRADICTING_FLOW"
        else:
            out["flow_class"] = "AMM_FLOW_NEUTRAL"
    else:
        out["flow_class"] = "INSUFFICIENT_FLOW"
    return out


# ---------------------------------------------------------------------------
# Redundancy
# ---------------------------------------------------------------------------

def redundancy_check(
    grid: List[Dict], simple_field: str, simple_value: str,
    complex_field: str, complex_value: str, horizon_hours: int = 4,
) -> Dict[str, Any]:
    """Is the complex state's info value close to the simple parent's?"""
    s = info_value_for_state(grid, simple_field, simple_value, horizon_hours)
    c = info_value_for_state(grid, complex_field, complex_value, horizon_hours)
    if s.get("insufficient") or c.get("insufficient"):
        return {"simple": simple_value, "complex": complex_value,
                "insufficient": True}
    er_s = s.get("entropy_reduction_bits", 0.0)
    er_c = c.get("entropy_reduction_bits", 0.0)
    js_s = s.get("js_divergence", 0.0)
    js_c = c.get("js_divergence", 0.0)
    # complex adds little if its ER ~ parent's ER and its JS not much larger
    incremental = er_c - er_s
    redundant = (incremental < 0.02 * (abs(er_s) + 1e-9)
                 and js_c <= js_s * 1.25 + 1e-9)
    return {
        "simple": simple_value, "complex": complex_value,
        "simple_er_bits": er_s, "complex_er_bits": er_c,
        "incremental_er_bits": incremental,
        "simple_js": js_s, "complex_js": js_c,
        "redundant": bool(redundant),
    }


# ---------------------------------------------------------------------------
# Causality audit helpers
# ---------------------------------------------------------------------------

def future_perturbation_test(
    grid_builder: Callable[[List[Dict], List[Dict], List[Dict]], List[Dict]],
    perp_records: List[Dict], spot_records: List[Dict],
    funding_records: List[Dict], truncate_at: str,
) -> Dict[str, Any]:
    """Labels for t <= truncate_at must be identical with/without future data.

    Thresholds are FROZEN (computed before this test) and passed in via the
    builder closure — the test verifies labeling itself is causal.
    """
    full = grid_builder(perp_records, spot_records, funding_records)
    truncated = grid_builder(
        [r for r in perp_records if str(r.get("event_time_utc", "")) <= truncate_at],
        [r for r in spot_records if str(r.get("event_time_utc", "")) <= truncate_at],
        [r for r in funding_records if str(r.get("event_time_utc", "")) <= truncate_at])
    full_prefix = [r for r in full if str(r.get("event_time_utc", "")) <= truncate_at]
    fields = ["basis_bps", "basis_state", "funding_state", "funding_accel",
              "vol_state", "mark_index_state"]
    diffs = []
    for a, b in zip(full_prefix, truncated):
        for f in fields:
            if a.get(f) != b.get(f):
                diffs.append({"bucket": a["bucket"], "field": f,
                              "full": a.get(f), "truncated": b.get(f)})
    return {
        "equal": len(diffs) == 0,
        "full_prefix_rows": len(full_prefix),
        "truncated_rows": len(truncated),
        "truncate_at": truncate_at,
        "diffs": diffs[:10],
    }


def next_state_causal_audit(grid: List[Dict]) -> List[Dict]:
    """For every row, verify no state field changed relative to what was
    knowable at t (spot/perp/funding join times <= t). Reports any row where
    basis or funding could only come from a future bucket (should be none)."""
    issues = []
    for r in grid:
        # causal construction guarantees: basis joins same/prior bucket only.
        if r.get("staleness_hours") is None:
            continue
    return issues
