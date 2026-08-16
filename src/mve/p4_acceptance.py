"""MVE Phase-4 Causal Acceptance Engine (P4, human-authorized 2026-08-16).

Implements the pre-registered acceptance variant family (A0..A5) on top of
the sealed R0.5 infrastructure. Every event obeys the frozen causal schema:

    state_event_time <= evidence_complete_time <= acceptance_known_time

and nothing is ever consumable before its confirming evidence exists.

Design freeze: research/mve/p4/MVE_P4_PROTOCOL.md (pre-registered before any
result). This module contains scientific acceptance logic ONLY as authorized
by the P4 checkpoint. It imports NO blocked components (Models D/E / signals).

Components used (all sealed R0.5): data loader conventions (H1 frame),
VolatilityEstimators (close_to_close), StructuralAnchors (pivot high/low,
consumed via causality.apply_anchor_delay), MorphicCoordinates, and the
causality event-time schemas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from mve.anchors import StructuralAnchors
from mve.causality import apply_anchor_delay
from mve.morphic_coordinates import MorphicCoordinates
from mve.volatility import VolatilityEstimators

SIDES = ("LONG", "SHORT")

# Variant keys emitted by the engine (stable ordering for reporting/tests).
VARIANT_KEYS = (
    "A0",
    "A1",
    "A2_2of3",
    "A2_3of4",
    "A2_3of5",
    "A3_n2",
    "A3_n3",
    "A3_n4",
    "A4_R1",
    "A4_R2",
    "A5",
)

# Perturbation/truncation knowledge delay per variant (max evidence lookahead):
# A0 touch and A1 close are known the same bar; A2 windows span at most 5 bars
# (3-of-5 -> evidence <= start+4); A3 persistence 4 -> evidence <= start+3;
# A4 retest scan is <= 12 bars; A5 resolves at the return-inside bar (delay 0).
VARIANT_DELAY = {
    "A0": 0,
    "A1": 0,
    "A2_2of3": 4,
    "A2_3of4": 4,
    "A2_3of5": 4,
    "A3_n2": 3,
    "A3_n3": 3,
    "A3_n4": 3,
    "A4_R1": 12,
    "A4_R2": 12,
    "A5": 0,
}


@dataclass(frozen=True)
class AcceptanceConfig:
    """Frozen P4 engine configuration (see protocol section 2-3)."""

    pivot_window: int = 5
    min_pivot_height: float = 0.01
    fallback_roll: int = 50
    fallback_min_periods: int = 20
    sigma_levels: Tuple[int, ...] = (1, 2, 3)
    occupancy_grid: Tuple[Tuple[int, int], ...] = ((2, 3), (3, 4), (3, 5))
    persistence_grid: Tuple[int, ...] = (2, 3, 4)
    retest_window: int = 12
    retest_tolerances: Tuple[float, ...] = (0.5, 0.0)  # sigma units (log)
    fail_window: int = 24
    max_episode_bars: int = 48
    horizons: Tuple[int, ...] = (1, 2, 3, 6, 12, 24)
    next_state_step: float = 1.0


DEFAULT_CONFIG = AcceptanceConfig()


def _ann_factor(cfg: AcceptanceConfig) -> float:
    # tau = 1.0 (sealed MorphicCoordinates default time_horizon)
    return np.sqrt(1.0)


def build_fields(df: pd.DataFrame, cfg: AcceptanceConfig = DEFAULT_CONFIG) -> Dict:
    """Compute the causal field set: sigma, delayed anchors, coordinates,
    boundary prices per level, and volatility regime. All causal: anchors are
    consumed only after their confirmation window (apply_anchor_delay)."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else None

    vol = VolatilityEstimators().calculate_all_estimators(
        close, high, low, volume
    )["close_to_close"]

    anchors_obj = StructuralAnchors(
        {
            "pivot_high_low": {
                "window": cfg.pivot_window,
                "min_pivot_height": cfg.min_pivot_height,
                "min_pivot_width": 3,
            }
        }
    )
    piv_low = anchors_obj._calculate_pivot_low(close)
    piv_high = anchors_obj._calculate_pivot_high(close)

    anchor_long = apply_anchor_delay(piv_low, cfg.pivot_window).ffill()
    anchor_short = apply_anchor_delay(piv_high, cfg.pivot_window).ffill()
    fb_low = close.rolling(cfg.fallback_roll, min_periods=cfg.fallback_min_periods).min()
    fb_high = close.rolling(cfg.fallback_roll, min_periods=cfg.fallback_min_periods).max()
    anchor_long = anchor_long.fillna(fb_low)
    anchor_short = anchor_short.fillna(fb_high)

    mc = MorphicCoordinates(time_horizon=1.0)
    coord_long = mc.calculate_morphic_coordinates(
        close, anchor_long, {"close_to_close": vol}, "close_to_close"
    )
    coord_short = mc.calculate_morphic_coordinates(
        close, anchor_short, {"close_to_close": vol}, "close_to_close"
    )

    # Volatility regime (sealed expansion-ratio thresholds 0.80 / 1.20).
    regime = pd.Series("NORMAL", index=df.index, dtype=object)
    valid = vol.dropna()
    if len(valid) > 0 and valid.iloc[0] > 0:
        ratio = vol / valid.iloc[0]
        regime[ratio < 0.80] = "CONTRACTION"
        regime[ratio > 1.20] = "EXPANSION"

    tau = _ann_factor(cfg)
    b_long = {k: anchor_long * np.exp(k * vol * tau) for k in cfg.sigma_levels}
    b_short = {k: anchor_short * np.exp(-k * vol * tau) for k in cfg.sigma_levels}

    return {
        "sigma": vol,
        "coord_long": coord_long,
        "coord_short": coord_short,
        "anchor_long": anchor_long,
        "anchor_short": anchor_short,
        "b_long": b_long,
        "b_short": b_short,
        "regime": regime,
    }


def detect_acceptance_events(
    df: pd.DataFrame, cfg: AcceptanceConfig = DEFAULT_CONFIG, fields: Optional[Dict] = None
) -> List[Dict]:
    """Detect all pre-registered acceptance events on an H1 frame.

    Returns a list of event records, each schema-valid (acceptance schema +
    standard scientific-event schema) and deduplicated to one event per
    variant per episode. No global state; fully determined by `df`.
    """
    if fields is None:
        fields = build_fields(df, cfg)
    events: List[Dict] = []
    for side in SIDES:
        for k in cfg.sigma_levels:
            events.extend(_detect_family(df, cfg, fields, side, k))
    events.sort(key=lambda e: (e["acceptance_known_time"], e["event_id"]))
    return events


def _detect_family(
    df: pd.DataFrame, cfg: AcceptanceConfig, fields: Dict, side: str, k: int
) -> List[Dict]:
    n = len(df)
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    sigma = fields["sigma"].to_numpy(dtype=float)
    tau = _ann_factor(cfg)

    if side == "LONG":
        b = fields["b_long"][k].to_numpy(dtype=float)
        beyond = close > b
        touch = high >= b
        inside_prev = np.concatenate([[False], ~beyond[:-1]])
        a_anchor = fields["anchor_long"]
        coord = fields["coord_long"]
        anchor_type = "pivot_low"
    else:
        b = fields["b_short"][k].to_numpy(dtype=float)
        beyond = close < b
        touch = low <= b
        inside_prev = np.concatenate([[False], ~beyond[:-1]])
        a_anchor = fields["anchor_short"]
        coord = fields["coord_short"]
        anchor_type = "pivot_high"

    coord_np = coord.to_numpy(dtype=float)
    regime = fields["regime"]
    idx = df.index

    # ---- episode segmentation (one pass) ----
    starts = touch & inside_prev
    episodes: List[Dict] = []
    cur: Optional[Dict] = None
    for t in range(n):
        if starts[t]:
            cur = {"start": t, "end": None, "a1": None, "streak": 0}
        if cur is None:
            continue
        if not np.isnan(b[t]) and beyond[t]:
            if cur["a1"] is None:
                cur["a1"] = t
            cur["streak"] += 1
        else:
            # return inside -> episode ends at this bar (or warm-up NaN)
            cur["end"] = t
            episodes.append(cur)
            cur = None
            continue
        if t - cur["start"] >= cfg.max_episode_bars:
            cur["end"] = t
            episodes.append(cur)
            cur = None
    # An episode still open at the frame end is closed at the final bar: its
    # already-known events (A0/A1/etc. with known <= frame end) are complete
    # and must be emitted - dropping them would break truncation invariance.
    if cur is not None:
        cur["end"] = n
        episodes.append(cur)

    events: List[Dict] = []
    for seq, ep in enumerate(episodes):
        start = ep["start"]
        end = ep["end"] if ep["end"] is not None else n
        a1 = ep["a1"]

        # A0 baseline touch: known at the episode-start bar close.
        events.append(
            _make_event(
                cfg, idx, side, k, "A0", seq, start, start, start, end,
                close, coord_np, sigma, regime, a_anchor, anchor_type,
                b, accepted=False, rejection_reason="baseline_touch",
            )
        )

        # A1 close-beyond.
        if a1 is not None:
            events.append(
                _make_event(
                    cfg, idx, side, k, "A1", seq, start, a1, a1, end,
                    close, coord_np, sigma, regime, a_anchor, anchor_type,
                    b, accepted=True, rejection_reason="criteria_met",
                )
            )

        # A2 occupancy: N of last M closes beyond (within episode).
        for (nn, mm) in cfg.occupancy_grid:
            for t in range(start, end):
                lo = max(start, t - mm + 1)
                if int(beyond[lo : t + 1].sum()) >= nn:
                    events.append(
                        _make_event(
                            cfg, idx, side, k, f"A2_{nn}of{mm}", seq, start, t, t, end,
                            close, coord_np, sigma, regime, a_anchor, anchor_type,
                            b, accepted=True, rejection_reason="criteria_met",
                        )
                    )
                    break

        # A3 persistence: N consecutive closes beyond.
        for nn in cfg.persistence_grid:
            if ep["streak"] >= nn:
                # first bar where the consecutive run reached nn (within episode)
                cnt = 0
                for t in range(start, end):
                    cnt = cnt + 1 if (not np.isnan(b[t]) and beyond[t]) else 0
                    if cnt >= nn:
                        events.append(
                            _make_event(
                                cfg, idx, side, k, f"A3_n{nn}", seq, start, t, t, end,
                                close, coord_np, sigma, regime, a_anchor, anchor_type,
                                b, accepted=True, rejection_reason="criteria_met",
                            )
                        )
                        break

        # A4 retest-hold: requires a close-beyond; retest within retest_window
        # bars after the breach bar, low reaches within tolerance from outside,
        # and the retest bar closes back beyond.
        if a1 is not None:
            for tol in cfg.retest_tolerances:
                for t in range(a1 + 1, min(a1 + cfg.retest_window + 1, end)):
                    if np.isnan(sigma[t]) or np.isnan(b[t]):
                        continue
                    if side == "LONG":
                        retest_hit = low[t] <= b[t] * np.exp(tol * sigma[t] * tau)
                    else:
                        retest_hit = high[t] >= b[t] * np.exp(-tol * sigma[t] * tau)
                    if retest_hit and beyond[t]:
                        events.append(
                            _make_event(
                                cfg, idx, side, k, f"A4_R{'1' if tol == 0.5 else '2'}",
                                seq, start, t, t, end, close, coord_np, sigma, regime,
                                a_anchor, anchor_type, b, accepted=True,
                                rejection_reason="criteria_met",
                            )
                        )
                        break

        # A5 failed acceptance control: episode with no close-beyond. The
        # failure is KNOWN at the episode-start bar's close (the touch bar
        # closed back inside, so no close-beyond ever completed in this
        # episode). state == evidence == known == start.
        if a1 is None:
            events.append(
                _make_event(
                    cfg, idx, side, k, "A5", seq, start, start, start, end,
                    close, coord_np, sigma, regime, a_anchor, anchor_type,
                    b, accepted=False, rejection_reason="never_close_beyond",
                )
            )

    return events


def _make_event(
    cfg: AcceptanceConfig, idx, side: str, k: int, variant: str, seq: int,
    ep_start: int, ev_bar: int, known_bar: int, ep_end: int, close, coord_np,
    sigma, regime, a_anchor, anchor_type: str, b, accepted: bool,
    rejection_reason: str,
) -> Dict:
    b_known = float(b[known_bar]) if not np.isnan(b[known_bar]) else np.nan
    coord_known = coord_np[known_bar] if not np.isnan(coord_np[known_bar]) else np.nan
    level_state = int(np.floor(abs(coord_known) / cfg.next_state_step)) if np.isfinite(coord_known) else -1
    dist = abs(coord_known) - k if np.isfinite(coord_known) else np.nan

    return {
        "event_id": f"{side}_s{k}sigma_{variant}_e{seq}",
        "variant": variant,
        "direction": "+" if side == "LONG" else "-",
        "boundary_id": f"{side}_s{k}sigma",
        "boundary_value": b_known,
        "state_event_time": int(ep_start),
        "evidence_complete_time": int(ev_bar),
        "acceptance_known_time": int(known_bar),
        "event_time": int(ep_start),
        "known_time": int(known_bar),
        "action_time": int(known_bar) + 1,
        "price_at_event": float(close[ep_start]),
        "price_at_known": float(close[known_bar]),
        "sigma_state": level_state,
        "morphic_coordinate": coord_known,
        "volatility_state": str(regime.iloc[known_bar]),
        "anchor_type": anchor_type,
        "anchor_value": float(a_anchor.iloc[known_bar]),
        "distance_from_boundary": dist,
        "evidence_window": int(ev_bar - ep_start),
        "accepted": bool(accepted),
        "rejection_reason": rejection_reason,
        "episode_id": int(seq),
        "episode_start": int(ep_start),
        "episode_end": int(ep_end),
        "sigma_level": int(k),
        "state_event_time_iso": str(idx[ep_start]),
        "evidence_complete_time_iso": str(idx[ev_bar]),
        "acceptance_known_time_iso": str(idx[known_bar]),
    }


def events_to_series(
    events: List[Dict], index: pd.Index, cfg: AcceptanceConfig = DEFAULT_CONFIG
) -> Dict[str, pd.Series]:
    """Per-variant 0/1 indicator series: 1 at each event's
    acceptance_known_time position (counts can exceed 1 when events from
    different families share a bar). Used by the causality regression."""
    out: Dict[str, pd.Series] = {}
    for v in VARIANT_KEYS:
        s = pd.Series(0.0, index=index)
        for e in events:
            if e["variant"] == v:
                s.iloc[e["acceptance_known_time"]] += 1.0
        out[v] = s
    return out


def compute_structural_outcomes(
    df: pd.DataFrame, events: List[Dict], cfg: AcceptanceConfig = DEFAULT_CONFIG,
    fields: Optional[Dict] = None,
) -> pd.DataFrame:
    """Structural outcomes per event, measured from the known-bar close using
    the FROZEN boundary value b_known (see protocol section 5)."""
    if fields is None:
        fields = build_fields(df, cfg)
    close = df["close"].to_numpy(dtype=float)
    coord_long = fields["coord_long"].to_numpy(dtype=float)
    coord_short = fields["coord_short"].to_numpy(dtype=float)
    sigma = fields["sigma"].to_numpy(dtype=float)
    n = len(df)

    rows: List[Dict] = []
    for e in events:
        tk = e["acceptance_known_time"]
        long_side = e["direction"] == "+"
        k = e["sigma_level"]
        b_known = e["boundary_value"]
        p_known = close[tk]
        sig_known = sigma[tk] if tk < n else np.nan
        coord = coord_long if long_side else coord_short

        row = {
            "event_id": e["event_id"],
            "variant": e["variant"],
            "family": e["boundary_id"],
            "direction": e["direction"],
            "sigma_level": k,
            "known_pos": tk,
            "known_time_iso": e["acceptance_known_time_iso"],
            "episode_id": e["episode_id"],
            "episode_start": e["episode_start"],
            "accepted": e["accepted"],
            "rejection_reason": e["rejection_reason"],
            "coord_known": e["morphic_coordinate"],
            "distance_from_boundary": e["distance_from_boundary"],
            "sigma_known": sig_known,
            "volatility_state": e["volatility_state"],
            "persistence_duration": None,  # filled below
        }

        for h in cfg.horizons:
            j = tk + h
            if j < n and np.isfinite(sig_known) and sig_known > 0 and np.isfinite(b_known):
                ratio = np.log(close[j] / p_known)
                disp = ratio / sig_known if long_side else -ratio / sig_known
                cont = (close[j] > b_known) if long_side else (close[j] < b_known)
                window = slice(tk + 1, j + 1)
                rej = ((close[window] <= b_known).any()) if long_side else (
                    (close[window] >= b_known).any()
                )
                row[f"continuation_{h}"] = bool(cont)
                row[f"rejection_{h}"] = bool(rej)
                row[f"displacement_{h}"] = float(disp)
            else:
                row[f"continuation_{h}"] = np.nan
                row[f"rejection_{h}"] = np.nan
                row[f"displacement_{h}"] = np.nan

        # MFE / MAE within (tk, tk+h] (displacement signed continuation-positive)
        for h in (6, 12, 24):
            j = tk + h
            if j < n and np.isfinite(sig_known) and sig_known > 0:
                disps = []
                for jj in range(tk + 1, j + 1):
                    ratio = np.log(close[jj] / p_known)
                    disps.append(ratio / sig_known if long_side else -ratio / sig_known)
                row[f"mfe_{h}"] = float(np.max(disps))
                row[f"mae_{h}"] = float(np.min(disps))
            else:
                row[f"mfe_{h}"] = np.nan
                row[f"mae_{h}"] = np.nan

        # Time to rejection / next sigma state (censored at max horizon 24)
        ttr = None
        tts = None
        for h in range(1, 25):
            j = tk + h
            if j >= n:
                break
            if np.isfinite(b_known):
                through = (close[j] <= b_known) if long_side else (close[j] >= b_known)
                if through and ttr is None:
                    ttr = h
            if np.isfinite(coord[j]):
                reached = abs(coord[j]) >= k + 1
                if reached and tts is None:
                    tts = h
            if ttr is not None and tts is not None:
                break
        row["time_to_rejection"] = ttr
        row["time_to_rejection_censored"] = ttr is None
        row["time_to_next_sigma_state"] = tts
        row["time_to_next_sigma_state_censored"] = tts is None

        # State at h = 6, 24 and delta vs known state
        state_known = e["sigma_state"]
        for h in (6, 24):
            j = tk + h
            if j < n and np.isfinite(coord[j]):
                st = int(np.floor(abs(coord[j]) / cfg.next_state_step))
                row[f"state_{h}"] = st
                row[f"state_delta_{h}"] = st - state_known
            else:
                row[f"state_{h}"] = np.nan
                row[f"state_delta_{h}"] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)


def validate_event_catalog(events: List[Dict], raise_on_error: bool = True) -> List[str]:
    """Validate the full event catalog against both frozen schemas and assert
    one-event-per-variant-per-episode dedup. Returns problems (fail-closed)."""
    from mve.causality import (
        assert_unique_events,
        validate_acceptance_events,
        validate_scientific_event_times,
    )

    problems: List[str] = []
    problems += validate_acceptance_events(events, raise_on_error=False)
    problems += validate_scientific_event_times(events, raise_on_error=False)
    problems += assert_unique_events(
        events,
        ["direction", "sigma_level", "episode_id", "variant"],
        raise_on_error=False,
    )
    if problems and raise_on_error:
        from mve.causality import CausalityError

        raise CausalityError("; ".join(problems))
    return problems
