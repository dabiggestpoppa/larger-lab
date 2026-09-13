"""
CRYPTO-MECH-1: Core mechanism analysis functions.

Pure, deterministic, testable. No strategy PnL, no optimization.

Lanes:
- perp-spot basis (1h, frozen overlap 2026-01-25..2026-06-15)
- funding + premium (mark-index displacement) anatomy (3.3y deep)
- OI / book snapshot anatomy (honest limits)
- resolution survival from dislocation episodes
- time-epoch anatomy (24/7 crypto, no FX session rules)
- BTC/ETH cross-asset state
- AMM pilot anatomy (days, not years)
- null models (unconditional, vol-matched, block-shuffled, AR1)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

SEED = 20260821

# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Causal alignment
# ---------------------------------------------------------------------------

@dataclass
class AlignmentResult:
    """Causal same-bucket / nearest-prior alignment output."""
    matched: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_a: int = 0
    unmatched_b: int = 0
    stale_count: int = 0
    max_staleness_hours: float = 0.0
    alignment_method: str = "same_bucket_causal_nearest_prior"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def align_causal(
    series_a: List[Dict],       # primary series (e.g. perp), with event_time_utc
    series_b: List[Dict],       # reference series (e.g. spot)
    price_field_a: str = "close",
    price_field_b: str = "close",
    bucket_fn=bucket_hour,
    max_staleness_hours: float = 1.0,
) -> AlignmentResult:
    """
    Align A to B causally: for each A record, use the B record in the same
    bucket; if absent, the nearest B record strictly BEFORE A's bucket
    (nearest prior, no future). A's bucket time is the reference.
    """
    res = AlignmentResult()

    b_by_bucket: Dict[str, float] = {}
    b_times: List[Tuple[datetime, float]] = []
    for r in series_b:
        if "error" in r:
            continue
        ts = parse_ts(r.get("event_time_utc"))
        price = r.get(price_field_b)
        if ts is None or price is None or not isinstance(price, (int, float)) or price <= 0:
            continue
        bk = bucket_fn(ts)
        if bk is not None:
            b_by_bucket[bk] = price
            b_times.append((ts, float(price)))
    b_times.sort(key=lambda x: x[0])
    b_bucket_keys = sorted(b_by_bucket.keys())

    for r in series_a:
        if "error" in r:
            continue
        ts = parse_ts(r.get("event_time_utc"))
        price_a = r.get(price_field_a)
        if ts is None or price_a is None or not isinstance(price_a, (int, float)) or price_a <= 0:
            continue
        bk = bucket_fn(ts)
        if bk is None:
            res.unmatched_a += 1
            continue
        price_b = b_by_bucket.get(bk)
        staleness = 0.0
        if price_b is None:
            # nearest prior bucket
            prior = [k for k in b_bucket_keys if k < bk]
            if not prior:
                res.unmatched_a += 1
                continue
            price_b = b_by_bucket[prior[-1]]
            # staleness in hours
            try:
                t_bk = datetime.fromisoformat(bk)
                t_pr = datetime.fromisoformat(prior[-1])
                staleness = (t_bk - t_pr).total_seconds() / 3600.0
            except ValueError:
                staleness = 1.0
            if staleness > max_staleness_hours:
                res.stale_count += 1
                res.unmatched_a += 1
                continue
            res.max_staleness_hours = max(res.max_staleness_hours, staleness)
        res.matched.append({
            "event_time_utc": r.get("event_time_utc"),
            "bucket": bk,
            "price_a": float(price_a),
            "price_b": float(price_b),
            "staleness_hours": staleness,
            "basis_bps": 10000.0 * float(np.log(price_a / price_b)) if price_b > 0 else np.nan,
        })

    res.unmatched_b = len(series_b) - len(b_by_bucket) + len(b_by_bucket) - len(
        {bk for bk in b_by_bucket if bk in {m["bucket"] for m in res.matched}} or set()
    )
    return res


# ---------------------------------------------------------------------------
# Basis series construction
# ---------------------------------------------------------------------------

def build_basis_series(
    perp_records: List[Dict],
    spot_records: List[Dict],
    max_staleness_hours: float = 1.0,
) -> List[Dict]:
    """Causal perp-spot basis at hourly buckets."""
    aligned = align_causal(perp_records, spot_records, "close", "close",
                           bucket_hour, max_staleness_hours)
    out = []
    for m in aligned.matched:
        out.append({
            "event_time_utc": m["event_time_utc"],
            "bucket": m["bucket"],
            "perp_close": m["price_a"],
            "spot_close": m["price_b"],
            "basis_bps": m["basis_bps"],
            "staleness_hours": m["staleness_hours"],
        })
    out.sort(key=lambda x: x["bucket"])
    return out


# ---------------------------------------------------------------------------
# Descriptive stats
# ---------------------------------------------------------------------------

def desc_stats(x: List[float], label: str = "") -> Dict[str, float]:
    a = np.asarray([v for v in x if v is not None and np.isfinite(v)], dtype=float)
    if len(a) == 0:
        return {"label": label, "n": 0}
    q = np.percentile(a, [1, 5, 10, 25, 50, 75, 90, 95, 97.5, 99])
    return {
        "label": label,
        "n": int(len(a)),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
        "mad": float(np.median(np.abs(a - np.median(a)))),
        "p1": float(q[0]), "p5": float(q[1]), "p10": float(q[2]),
        "p25": float(q[3]), "p50": float(q[4]), "p75": float(q[5]),
        "p90": float(q[6]), "p95": float(q[7]), "p97_5": float(q[8]),
        "p99": float(q[9]),
        "min": float(a.min()), "max": float(a.max()),
    }


def autocorr(x: List[float], lag: int = 1) -> float:
    a = np.asarray([v for v in x if v is not None and np.isfinite(v)], dtype=float)
    if len(a) <= lag + 1:
        return np.nan
    a = a - a.mean()
    var = (a ** 2).sum()
    if var == 0:
        return np.nan
    return float((a[:-lag] * a[lag:]).sum() / var)


# ---------------------------------------------------------------------------
# Dislocation episodes
# ---------------------------------------------------------------------------

def segment_dislocations(
    series: List[Dict],
    elevated_q: float = 90.0,
    normal_q: float = 75.0,
) -> Tuple[List[Dict], Dict[str, float]]:
    """
    One active episode per basis object at a time.
    Episode starts when |basis| > p_elevated; ends when |basis| < p_normal
    (hysteresis) or series end (CENSORED).
    """
    bases = [r["basis_bps"] for r in series if np.isfinite(r.get("basis_bps"))]
    p_elev = float(np.percentile(np.abs(bases), elevated_q))
    p_norm = float(np.percentile(np.abs(bases), normal_q))
    bands = {"p_elevated": p_elev, "p_normal": p_norm}

    episodes: List[Dict] = []
    active: Optional[Dict] = None
    idx = 0
    while idx < len(series):
        r = series[idx]
        b = r.get("basis_bps")
        if b is None or not np.isfinite(b):
            idx += 1
            continue
        if active is None:
            if abs(b) > p_elev:
                active = {
                    "start_index": idx,
                    "start_time": r["event_time_utc"],
                    "start_basis_bps": b,
                    "peak_basis_bps": abs(b),
                    "peak_time": r["event_time_utc"],
                    "max_abs": abs(b),
                    "end_index": None,
                    "end_time": None,
                    "resolved": False,
                    "expanded": False,
                    "path": [],
                }
        else:
            active["path"].append((r["event_time_utc"], b))
            active["max_abs"] = max(active["max_abs"], abs(b))
            if abs(b) > active["peak_basis_bps"]:
                active["peak_basis_bps"] = abs(b)
                active["peak_time"] = r["event_time_utc"]
            if abs(b) < p_norm:
                active["end_index"] = idx
                active["end_time"] = r["event_time_utc"]
                active["resolved"] = True
                episodes.append(active)
                active = None
        idx += 1
    if active is not None:
        active["end_index"] = len(series) - 1
        active["end_time"] = series[-1]["event_time_utc"]
        active["resolved"] = False
        active["censored"] = True
        episodes.append(active)

    # classify expanded / persisted / regime-shifted
    for ep in episodes:
        if not ep.get("resolved"):
            ep["classification"] = "CENSORED"
        else:
            start = ep["start_basis_bps"]
            peak = ep["peak_basis_bps"]
            end = ep.get("path", [])[-1][1] if ep.get("path") else start
            if peak > abs(start) * 1.5:
                ep["classification"] = "EXPANDED"
            elif abs(end) < p_norm:
                ep["classification"] = "RESOLVED"
            else:
                ep["classification"] = "PERSISTED"
        # duration / times
        try:
            t0 = datetime.fromisoformat(str(ep["start_time"]).replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(str(ep["end_time"]).replace("Z", "+00:00"))
            ep["duration_hours"] = (t1 - t0).total_seconds() / 3600.0
        except (ValueError, TypeError):
            ep["duration_hours"] = np.nan
        ep.pop("path", None)
    for n, ep in enumerate(episodes):
        ep["episode_id"] = f"ep_{n}"
    return episodes, bands


# ---------------------------------------------------------------------------
# Survival
# ---------------------------------------------------------------------------

def resolution_survival(episodes: List[Dict], max_hours: float = 120.0) -> List[Dict]:
    """Empirical time-to-resolution survival curve from episodes."""
    resolved_times = []
    for ep in episodes:
        if ep.get("resolved") and np.isfinite(ep.get("duration_hours", np.nan)):
            resolved_times.append(float(ep["duration_hours"]))
    if not resolved_times:
        return []
    rt = np.sort(np.asarray(resolved_times))
    n = len(rt)
    curve = []
    for t in np.arange(0.0, max_hours + 1.0, 1.0):
        surv = float((rt > t).mean())
        curve.append({"t_hours": float(t), "p_not_resolved": surv,
                      "p_resolved_by_t": 1.0 - surv})
    stats = {
        "n_resolved": n,
        "n_censored": sum(1 for ep in episodes if not ep.get("resolved")),
        "median_resolution_hours": float(np.median(rt)),
        "p75_resolution_hours": float(np.percentile(rt, 75)),
        "p90_resolution_hours": float(np.percentile(rt, 90)),
        "max_resolution_hours": float(rt[-1]),
    }
    return [{"t_hours": c["t_hours"], "p_not_resolved": c["p_not_resolved"],
             "p_resolved_by_t": c["p_resolved_by_t"]} for c in curve] + [
        {"stats": json.dumps(stats)}
    ]


# ---------------------------------------------------------------------------
# Funding / premium anatomy
# ---------------------------------------------------------------------------

def funding_anatomy(records: List[Dict], label: str = "") -> Dict[str, Any]:
    fr = [r["funding_rate"] for r in records
          if r.get("funding_rate") is not None and np.isfinite(r.get("funding_rate"))]
    pr = [r["premium"] for r in records
          if r.get("premium") is not None and np.isfinite(r.get("premium"))]
    fr_bps = [v * 1e4 for v in fr]
    pr_bps = [v * 1e4 for v in pr]
    out: Dict[str, Any] = {"label": label, "n": len(records)}
    out["funding_rate_bps"] = desc_stats(fr_bps, f"{label}_funding_bps")
    out["premium_bps"] = desc_stats(pr_bps, f"{label}_premium_bps")
    f = np.asarray(fr_bps, dtype=float)
    p = np.asarray(pr_bps, dtype=float)
    out["funding_positive_pct"] = float((f > 0).mean()) if len(f) else np.nan
    out["funding_negative_pct"] = float((f < 0).mean()) if len(f) else np.nan
    out["premium_positive_pct"] = float((p > 0).mean()) if len(p) else np.nan
    out["funding_autocorr_1"] = autocorr(fr_bps, 1)
    out["premium_autocorr_1"] = autocorr(pr_bps, 1)
    if len(f) and len(p):
        out["corr_funding_premium"] = float(np.corrcoef(f, p)[0, 1])
    else:
        out["corr_funding_premium"] = np.nan
    # extreme crowding: |funding| > p95
    if len(f):
        thr = float(np.percentile(np.abs(f), 95))
        out["p95_abs_funding_bps"] = thr
        out["extreme_funding_pct"] = float((np.abs(f) > thr).mean())
    return out


def oi_snapshot_anatomy(mark_oi_records: List[Dict], label: str = "") -> Dict[str, Any]:
    """OI and mark/index are snapshots only in the frozen data — honest limits."""
    marks = [r for r in mark_oi_records if r.get("mark_price") is not None]
    ois = [r for r in mark_oi_records if r.get("open_interest") is not None]
    out: Dict[str, Any] = {"label": label, "snapshot_only": True}
    if marks:
        r = marks[0]
        out["mark_price"] = r["mark_price"]
        out["index_price"] = r.get("index_price")
        out["oracle_price"] = r.get("oracle_price")
        if r.get("mark_price") and r.get("index_price"):
            out["mark_index_basis_bps"] = 10000.0 * np.log(
                r["mark_price"] / r["index_price"])
    if ois:
        out["open_interest"] = ois[0].get("open_interest")
    out["limitation"] = ("OI/mark/index time series NOT available in frozen "
                         "DATA-1 freeze (snapshot rows only); OI_UP/OI_DOWN "
                         "classification over time impossible on frozen data")
    return out


# ---------------------------------------------------------------------------
# Time-epoch anatomy
# ---------------------------------------------------------------------------

def time_epoch_anatomy(series: List[Dict], field: str = "basis_bps",
                       label: str = "") -> List[Dict]:
    """Event concentration by hour-of-day UTC, weekday/weekend (24/7 crypto)."""
    rows: Dict[str, List[float]] = {}
    weekend_rows: List[float] = []
    weekday_rows: List[float] = []
    for r in series:
        ts = parse_ts(r.get("event_time_utc"))
        v = r.get(field)
        if ts is None or v is None or not np.isfinite(v):
            continue
        h = ts.hour
        rows.setdefault(h, []).append(float(v))
        if ts.weekday() >= 5:
            weekend_rows.append(float(v))
        else:
            weekday_rows.append(float(v))
    out = []
    for h in sorted(rows.keys()):
        s = desc_stats(rows[h], f"{label}_h{h}")
        out.append({"label": f"{label}_hour{h:02d}_utc", **s})
    out.append({**desc_stats(weekend_rows, f"{label}_weekend"), "partition": "weekend"})
    out.append({**desc_stats(weekday_rows, f"{label}_weekday"), "partition": "weekday"})
    return out


# ---------------------------------------------------------------------------
# BTC/ETH cross-asset
# ---------------------------------------------------------------------------

def cross_asset_state(
    btc_series: List[Dict], eth_series: List[Dict],
    field: str = "basis_bps", label: str = "basis",
) -> Dict[str, Any]:
    """Align BTC and ETH series by bucket; joint dislocation counts; lead-lag."""
    b_by_bucket = {r["bucket"]: r for r in btc_series}
    e_by_bucket = {r["bucket"]: r for r in eth_series}
    common = sorted(set(b_by_bucket) & set(e_by_bucket))
    bv = [b_by_bucket[b].get(field) for b in common if np.isfinite(b_by_bucket[b].get(field))]
    ev = [e_by_bucket[b].get(field) for b in common if np.isfinite(e_by_bucket[b].get(field))]
    bf = np.asarray(bv, dtype=float)
    ef = np.asarray(ev, dtype=float)
    out: Dict[str, Any] = {
        "label": label, "n_common": len(common),
        "corr": float(np.corrcoef(bf, ef)[0, 1]) if len(bf) > 1 else np.nan,
    }
    if len(bf) > 1:
        thr_b = float(np.percentile(np.abs(bf), 90))
        thr_e = float(np.percentile(np.abs(ef), 90))
        both = float(((np.abs(bf) > thr_b) & (np.abs(ef) > thr_e)).mean())
        only_b = float(((np.abs(bf) > thr_b) & (np.abs(ef) <= thr_e)).mean())
        only_e = float(((np.abs(bf) <= thr_b) & (np.abs(ef) > thr_e)).mean())
        out["both_elevated_pct"] = both
        out["btc_only_elevated_pct"] = only_b
        out["eth_only_elevated_pct"] = only_e
        # lead-lag via cross-correlation on first differences
        db = np.diff(bf)
        de = np.diff(ef)
        lags = range(-6, 7)
        ccs = {}
        for lag in lags:
            if lag == 0:
                ccs["0"] = float(np.corrcoef(db, de)[0, 1]) if len(db) > 1 else np.nan
            elif lag > 0:  # ETH lags BTC by lag
                ccs[str(lag)] = float(np.corrcoef(db[:-lag], de[lag:])[0, 1]) if len(db) > lag + 1 else np.nan
            else:  # BTC lags ETH by -lag
                ccs[str(lag)] = float(np.corrcoef(db[-lag:], de[:lag])[0, 1]) if len(db) > -lag + 1 else np.nan
        out["cross_corr_by_lag"] = ccs
    return out


# ---------------------------------------------------------------------------
# AMM pilot anatomy
# ---------------------------------------------------------------------------

def amm_pilot_anatomy(
    swap_records: List[Dict],
    perp_records: List[Dict],
    label: str = "",
    pool_token0_is_asset: bool = True,
) -> Dict[str, Any]:
    """
    AMM pilot: derive AMM price from recorded price fields with explicit
    orientation, align causally to perp, measure basis, signed flow,
    intensity, price impact.
    """
    rows = []
    for r in swap_records:
        ts = parse_ts(r.get("event_time_utc"))
        if ts is None:
            continue
        # price_token0_per_token1 = price of token0 in token1 units
        # price_token1_per_token0 = price of token1 in token0 units
        # both are already asset-price-direct for the chosen orientation
        if pool_token0_is_asset:
            price = r.get("price_token0_per_token1")
        else:
            price = r.get("price_token1_per_token0")
        amt0 = r.get("amount0")
        amt1 = r.get("amount1")
        if price is None or not np.isfinite(float(price)) or float(price) <= 0:
            continue
        # signed flow: positive = asset bought (in USD notional)
        a0 = float(amt0) if amt0 is not None else 0.0
        a1 = float(amt1) if amt1 is not None else 0.0
        if pool_token0_is_asset:
            signed_asset_flow = a0
            notional = abs(a0) * float(price)
        else:
            signed_asset_flow = a1
            notional = abs(a1)
        rows.append({
            "event_time_utc": r["event_time_utc"],
            "bucket": bucket_5m(ts),
            "amm_price": float(price),
            "signed_asset_flow": signed_asset_flow,
            "notional_usd": notional,
            "sqrt_price_x96": r.get("sqrt_price_x96"),
            "tick": r.get("tick"),
            "liquidity": r.get("liquidity"),
        })
    if not rows:
        return {"label": label, "n": 0, "limitation": "no usable swap rows"}
    rows.sort(key=lambda x: x["bucket"])

    # bucket into 5m: price = last, signed flow = sum, intensity = count
    by_bucket: Dict[str, Dict] = {}
    for row in rows:
        bk = row["bucket"]
        b = by_bucket.setdefault(bk, {
            "bucket": bk, "amm_price": None, "signed_flow": 0.0,
            "notional": 0.0, "count": 0,
        })
        b["amm_price"] = row["amm_price"]
        b["signed_flow"] += row["signed_asset_flow"]
        b["notional"] += row["notional_usd"]
        b["count"] += 1
    buckets = list(by_bucket.values())

    # causal alignment to perp (nearest prior within same bucket)
    perp_by_bucket: Dict[str, float] = {}
    for r in perp_records:
        ts = parse_ts(r.get("event_time_utc"))
        if ts is None:
            continue
        bk = bucket_5m(ts)
        if bk is not None:
            perp_by_bucket[bk] = r.get("close")
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
            basis = 10000.0 * np.log(float(b["amm_price"]) / float(pp))
            aligned.append({**b, "perp_close": float(pp), "amm_perp_basis_bps": float(basis)})

    out: Dict[str, Any] = {
        "label": label, "n_swaps": len(rows), "n_5m_buckets": len(buckets),
        "n_aligned": len(aligned),
    }
    if aligned:
        bases = [a["amm_perp_basis_bps"] for a in aligned]
        flows = [a["signed_flow"] for a in aligned]
        notional = [a["notional"] for a in aligned]
        counts = [a["count"] for a in aligned]
        out["amm_price_stats"] = desc_stats([a["amm_price"] for a in aligned], f"{label}_amm_price")
        out["basis_stats"] = desc_stats(bases, f"{label}_amm_perp_basis")
        out["signed_flow_stats"] = desc_stats(flows, f"{label}_signed_flow")
        out["notional_stats"] = desc_stats(notional, f"{label}_notional")
        out["intensity_stats"] = desc_stats(counts, f"{label}_intensity")
        fb = np.asarray(bases, dtype=float)
        ff = np.asarray(flows, dtype=float)
        if len(fb) > 1:
            out["corr_basis_signed_flow"] = float(np.corrcoef(fb, ff)[0, 1])
        out["positive_flow_pct"] = float((ff > 0).mean())
    out["evidence_class"] = "PILOT_MECHANISM_EVIDENCE"
    out["limitation"] = ("AMM window is days (2026-08-14..20), not years; "
                         "cannot support long-history claims")
    return out


# ---------------------------------------------------------------------------
# Null models
# ---------------------------------------------------------------------------

def null_unconditional_future_basis(
    basis_series: List[Dict], horizons_hours: List[int] = (1, 4, 24),
) -> List[Dict]:
    """Unconditional expected change in |basis| over horizons."""
    by_bucket = {r["bucket"]: r for r in basis_series}
    keys = sorted(by_bucket.keys())
    out = []
    for h in horizons_hours:
        changes = []
        for i, k in enumerate(keys):
            v = abs(by_bucket[k]["basis_bps"])
            j = i + h
            if j < len(keys):
                v2 = abs(by_bucket[keys[j]]["basis_bps"])
                changes.append(v2 - v)
        s = desc_stats(changes, f"unconditional_h{h}")
        out.append({**s, "horizon_hours": h})
    return out


def null_vol_matched_random(
    basis_series: List[Dict], vol_bucket_fn=None, n_perm: int = 200, seed: int = SEED,
) -> Dict[str, Any]:
    """
    Compare dislocation resolution to random timestamps matched by
    volatility regime (|basis| magnitude buckets).

    Null = permutation of the |basis| sequence (destroys temporal structure
    while preserving the marginal distribution). Decay probability is
    computed within the top-33% volatility bucket for both observed and
    permuted sequences.
    """
    rng = np.random.default_rng(seed)
    vals = np.asarray([abs(r["basis_bps"]) for r in basis_series], dtype=float)
    if len(vals) < 20:
        return {"n": len(vals), "note": "insufficient"}
    obs_decay = _decay_prob_array(vals, top_quantile=67.0, hours=4)
    null_decays = []
    for _ in range(n_perm):
        perm = rng.permutation(len(vals))
        null_decays.append(_decay_prob_array(vals[perm], top_quantile=67.0, hours=4))
    out = {
        "observed_decay_pct": obs_decay,
        "null_mean_decay_pct": float(np.mean(null_decays)) if null_decays else np.nan,
        "null_p95_decay_pct": float(np.percentile(null_decays, 95)) if null_decays else np.nan,
        "null_p05_decay_pct": float(np.percentile(null_decays, 5)) if null_decays else np.nan,
        "n_perm": n_perm, "seed": seed,
        "effect": float(obs_decay - np.mean(null_decays)) if null_decays else np.nan,
    }
    return out


def _decay_prob_array(vals: np.ndarray, top_quantile: float, hours: int) -> float:
    """P(|basis| decays >50% within `hours` steps) for top volatility bucket."""
    vals = np.asarray(vals, dtype=float)
    if len(vals) < hours + 1:
        return np.nan
    thr = float(np.percentile(vals, top_quantile))
    cnt = 0
    hit = 0
    for i in range(len(vals) - hours):
        v = vals[i]
        if v < thr:
            continue
        cnt += 1
        if vals[i + hours] <= v * 0.5:
            hit += 1
    return float(hit / cnt) if cnt else np.nan


def _decay_prob(series: List[Dict], top_only: bool, hours: int,
                mask: Optional[np.ndarray] = None) -> float:
    by_bucket = {r["bucket"]: r for r in series}
    keys = sorted(by_bucket.keys())
    vals = np.asarray([abs(by_bucket[k]["basis_bps"]) for k in keys], dtype=float)
    if mask is not None:
        vals = vals[mask]
    if len(vals) < hours + 1:
        return np.nan
    thr = float(np.percentile(vals, 67)) if top_only else -np.inf
    cnt = 0
    hit = 0
    for i in range(len(vals) - hours):
        v = vals[i]
        if top_only and v < thr:
            continue
        cnt += 1
        if vals[i + hours] <= v * 0.5:
            hit += 1
    return float(hit / cnt) if cnt else np.nan


def null_block_shuffle_resolution(
    episodes: List[Dict], n_perm: int = 200, seed: int = SEED,
) -> Dict[str, Any]:
    """Shuffle episode labels preserving time blocks; compare resolution rate."""
    rng = np.random.default_rng(seed)
    resolved = [ep for ep in episodes if ep.get("resolved")]
    censored = [ep for ep in episodes if not ep.get("resolved")]
    obs_rate = len(resolved) / len(episodes) if episodes else np.nan
    rates = []
    all_ep = list(episodes)
    for _ in range(n_perm):
        idx = rng.permutation(len(all_ep))
        # block shuffle: contiguous blocks of 4 episodes
        blocks = [idx[i:i + 4] for i in range(0, len(idx), 4)]
        rng.shuffle(blocks)
        flat = [i for b in blocks for i in b]
        perm_resolved = sum(1 for k in flat if all_ep[k].get("resolved"))
        rates.append(perm_resolved / len(all_ep))
    return {
        "observed_resolution_rate": obs_rate,
        "null_mean": float(np.mean(rates)) if rates else np.nan,
        "null_p05": float(np.percentile(rates, 5)) if rates else np.nan,
        "null_p95": float(np.percentile(rates, 95)) if rates else np.nan,
        "n_perm": n_perm, "seed": seed,
        "n_episodes": len(episodes),
        "n_resolved": len(resolved), "n_censored": len(censored),
    }


def null_ar1_mean_reversion(basis_series: List[Dict], horizon: int = 4) -> Dict[str, Any]:
    """AR(1)-implied expected |basis| decay vs observed."""
    bases = [r["basis_bps"] for r in basis_series if np.isfinite(r.get("basis_bps"))]
    if len(bases) < 30:
        return {"n": len(bases), "note": "insufficient"}
    a = np.asarray(bases, dtype=float)
    # fit AR(1) on levels: x_t = c + phi x_{t-1}
    y = a[1:]
    x = a[:-1]
    phi = float(np.cov(x, y)[0, 1] / np.var(x)) if np.var(x) > 0 else 0.0
    c = float(np.mean(y) - phi * np.mean(x))
    # expected |basis| decay over `horizon` steps for a unit dislocation
    obs = []
    exp = []
    for i, v in enumerate(a[:-horizon]):
        if abs(v) >= np.percentile(np.abs(a), 90):
            obs.append(abs(a[i + horizon]))
            # iterate AR(1)
            xh = v
            for _ in range(horizon):
                xh = c + phi * xh
            exp.append(abs(xh))
    out = {"phi": phi, "c": c, "n_dislocations": len(obs)}
    if obs:
        out["observed_mean_abs_after"] = float(np.mean(obs))
        out["ar1_expected_mean_abs_after"] = float(np.mean(exp))
        out["observed_minus_ar1"] = float(np.mean(obs) - np.mean(exp))
    return out


# ---------------------------------------------------------------------------
# Funding during dislocations
# ---------------------------------------------------------------------------

def funding_during_dislocations(
    basis_series: List[Dict],
    funding_records: List[Dict],
    episodes: List[Dict],
    label: str = "",
) -> Dict[str, Any]:
    """
    Compare funding behavior inside vs outside dislocation episodes
    (causal: funding at/just before episode bars only, never future).
    """
    # funding rate by hour bucket (last known before bucket end)
    fund_by_bucket: Dict[str, float] = {}
    for r in funding_records:
        bk = bucket_hour(r.get("event_time_utc"))
        if bk is not None and r.get("funding_rate") is not None:
            fund_by_bucket[bk] = float(r["funding_rate"]) * 1e4  # bps

    in_episode: set = set()
    for ep in episodes:
        start_idx = ep.get("start_index")
        end_idx = ep.get("end_index")
        if start_idx is None:
            continue
        end_idx = end_idx if end_idx is not None else len(basis_series) - 1
        for i in range(start_idx, end_idx + 1):
            if i < len(basis_series):
                in_episode.add(basis_series[i]["bucket"])

    inside = []
    outside = []
    for r in basis_series:
        bk = r["bucket"]
        f = fund_by_bucket.get(bk)
        if f is None:
            continue
        (inside if bk in in_episode else outside).append(f)

    out: Dict[str, Any] = {"label": label}
    out["inside_episode"] = desc_stats(inside, f"{label}_inside") if inside else {"n": 0}
    out["outside_episode"] = desc_stats(outside, f"{label}_outside") if outside else {"n": 0}
    if inside and outside:
        a = np.asarray(inside, dtype=float)
        b = np.asarray(outside, dtype=float)
        out["inside_mean_bps"] = float(a.mean())
        out["outside_mean_bps"] = float(b.mean())
        out["inside_minus_outside_bps"] = float(a.mean() - b.mean())
        # bootstrap CI on the difference (block-ish, fixed seed)
        rng = np.random.default_rng(SEED)
        diffs = []
        for _ in range(500):
            sa = rng.choice(a, size=len(a), replace=True)
            sb = rng.choice(b, size=min(len(b), len(a)), replace=True)
            diffs.append(sa.mean() - sb.mean())
        out["diff_p05_bps"] = float(np.percentile(diffs, 5))
        out["diff_p95_bps"] = float(np.percentile(diffs, 95))
        out["n_inside"] = len(inside)
        out["n_outside"] = len(outside)
    return out


# ---------------------------------------------------------------------------
# Determinism / causality utilities
# ---------------------------------------------------------------------------

def future_perturbation_invariance(build_fn, records: List[Dict], truncate_at: str) -> Dict[str, Any]:
    """States before cutoff must be identical after truncating future data."""
    full = build_fn(records)
    truncated = build_fn([r for r in records if str(r.get("event_time_utc", "")) <= truncate_at])
    full_prefix = [r for r in full if str(r.get("event_time_utc", "")) <= truncate_at]
    eq = full_prefix == truncated
    return {
        "equal": eq,
        "full_prefix_rows": len(full_prefix),
        "truncated_rows": len(truncated),
        "truncate_at": truncate_at,
    }


def stable_hash(obj: Any) -> str:
    s = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
