"""P7 — Signal-Model Falsification engine.

Falsifies the sealed Models A/B/C (src/mve/signals.py) against their closest
simple baselines on the frozen MVE coordinate field. This module provides:

- signal builders: sealed generators (A/B/C) and frozen simple baselines
  (B3_PLAIN_BREAKOUT, A_BASE, B_BASE, C_BASE, C_DIRECT_2SIGMA),
- episode detection (dedup of consecutive same-direction signals),
- event matching (MODEL_AND_BASELINE / MODEL_ONLY / BASELINE_ONLY),
- structural outcomes from known_time at fixed horizons,
- per-bar control fields (sigma state, vol tercile, hour, session,
  anchor age, prior state duration).

All logic is causal: every emitted event is known at its known_time bar, and
outcomes are measured strictly after known_time. No acceptance/rekey alpha,
no Model D/E, no 2026 access.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mve.signals import SignalGenerator

BOUNDARY = 1.0
STEP = 1.0
N_SIGMA = 1
OCCUPANCY_THRESHOLD = 0.8
OCC_WINDOW = 3

HORIZONS = (1, 2, 3, 6, 12, 24)
MAX_HORIZON = 24

MATCH_WINDOW = 2  # bars

# Frozen contrast baselines (protocol sec. 3): the plain event each model's
# extra construction layer must beat.
CONTRAST_BASELINE = {
    "MODEL_A": "B3_PLAIN_BREAKOUT",
    "MODEL_B": "B3_PLAIN_BREAKOUT",
    "MODEL_C": "C_DIRECT_2SIGMA",
}

MODELS = ("MODEL_A", "MODEL_B", "MODEL_C")
BASELINES = (
    "B3_PLAIN_BREAKOUT",
    "A_BASE",
    "B_BASE",
    "C_BASE",
    "C_DIRECT_2SIGMA",
)

STRUCTURAL_BASELINE = {
    "MODEL_A": "A_BASE",
    "MODEL_B": "B_BASE",
    "MODEL_C": "C_BASE",
}

# Delay (bars) between a signal's bar and its knowledge time.
SIGNAL_DELAY = {"MODEL_A": 0, "MODEL_B": 0, "MODEL_C": 0}


def _crossing_events(x: np.ndarray, level: float) -> np.ndarray:
    """First bar beyond |level| (close basis), realtime at bar i.

    Signal = sign(x[i]) at bars where |x[i]| > level and |x[i-1]| <= level.
    NaN-safe (NaN treated as inside).
    """
    n = len(x)
    out = np.zeros(n, dtype=float)
    for i in range(n):
        xi = x[i]
        if np.isnan(xi):
            continue
        if abs(xi) <= level:
            continue
        if i == 0:
            out[i] = np.sign(xi)
            continue
        prev = x[i - 1]
        if np.isnan(prev) or abs(prev) <= level:
            out[i] = np.sign(xi)
    return out


def _persistence_confirm_events(x: np.ndarray, level: float) -> np.ndarray:
    """Cross level at i, still beyond at i+1; signal known at i+1 (A_BASE)."""
    n = len(x)
    out = np.zeros(n, dtype=float)
    for i in range(n - 1):
        xi = x[i]
        if np.isnan(xi):
            continue
        crossed = abs(xi) > level and (
            i == 0 or np.isnan(x[i - 1]) or abs(x[i - 1]) <= level
        )
        if crossed and not np.isnan(x[i + 1]) and abs(x[i + 1]) > level:
            out[i + 1] = np.sign(xi)
    return out


def _occupancy_events(x: np.ndarray, level: float, window: int = OCC_WINDOW) -> np.ndarray:
    """State: |x| > level AND window-bar occupancy >= threshold (B_BASE).

    Occupancy = fraction of the trailing `window` bars (inclusive) with
    |x| > level. Emits at bar i (realtime), 1 when the state holds.
    """
    n = len(x)
    out = np.zeros(n, dtype=float)
    for i in range(n):
        if np.isnan(x[i]):
            continue
        lo = max(0, i - window + 1)
        seg = x[lo : i + 1]
        valid = seg[~np.isnan(seg)]
        if len(valid) == 0:
            continue
        occ = float(np.mean(np.abs(valid) > level))
        if abs(x[i]) > level and occ >= OCCUPANCY_THRESHOLD:
            out[i] = 1.0
    return out


def _escalation_events(x: np.ndarray, level: float) -> np.ndarray:
    """Cross 1*level at i-1, reach |x| > 2*level at i (C_BASE).

    Signal known at the +2-level confirmation bar i.
    """
    n = len(x)
    out = np.zeros(n, dtype=float)
    for i in range(1, n):
        prev = x[i - 1]
        xi = x[i]
        if np.isnan(prev) or np.isnan(xi):
            continue
        crossed_prev = abs(prev) > level and (
            i == 1 or np.isnan(x[i - 2]) or abs(x[i - 2]) <= level
        )
        if crossed_prev and abs(xi) > 2 * level:
            out[i] = np.sign(xi)
    return out


def build_signal(model_or_baseline: str, x: pd.Series) -> pd.Series:
    """Return the causal signal series (indexed like x) for a model/baseline.

    Models call the SEALED SignalGenerator; baselines are the frozen simple
    rules from the P7 protocol. Model B and B_BASE emit a state (1); all
    others emit discrete directional entries (+1/-1).
    """
    xv = x.to_numpy(dtype=float)
    gen = SignalGenerator()
    if model_or_baseline == "MODEL_A":
        out = gen.generate_sigma_escape_signals(x, step=STEP, n=N_SIGMA)
    elif model_or_baseline == "MODEL_B":
        out = gen.generate_accepted_sigma_breakout_signals(
            x, step=STEP, n=N_SIGMA, acceptance_threshold=OCCUPANCY_THRESHOLD
        )
    elif model_or_baseline == "MODEL_C":
        out = gen.generate_recursive_morphic_trend_signals(x, step=STEP, n=N_SIGMA)
    elif model_or_baseline == "B3_PLAIN_BREAKOUT":
        out = pd.Series(_crossing_events(xv, BOUNDARY), index=x.index)
    elif model_or_baseline == "A_BASE":
        out = pd.Series(_persistence_confirm_events(xv, BOUNDARY), index=x.index)
    elif model_or_baseline == "B_BASE":
        out = pd.Series(_occupancy_events(xv, BOUNDARY), index=x.index)
    elif model_or_baseline == "C_BASE":
        out = pd.Series(_escalation_events(xv, BOUNDARY), index=x.index)
    elif model_or_baseline == "C_DIRECT_2SIGMA":
        out = pd.Series(_crossing_events(xv, 2.0 * BOUNDARY), index=x.index)
    else:
        raise ValueError(f"unknown model/baseline: {model_or_baseline}")
    return out.astype(float)


# ---------------------------------------------------------------------------
# Episodes (dedup consecutive same-direction signals)
# ---------------------------------------------------------------------------

def to_episodes(
    signal: pd.Series, name: str, x: pd.Series = None, merge_gap: int = 2
) -> pd.DataFrame:
    """Convert a signal series to episodes.

    Discrete entries (+1/-1): each signal starts an episode; consecutive
    same-direction signals within `merge_gap` bars are merged (dedup).
    State series (Model B/B_BASE, values in {0,1}): contiguous runs of the
    active state form one episode; event time = first bar of the run.

    Returns columns: event_id, model, event_time, evidence_complete_time,
    known_time, action_time, direction.
    """
    vals = signal.to_numpy(dtype=float)
    idx = signal.index
    n = len(vals)

    # State-run detection for values that are only {0,1} AND never emit -1.
    is_state = name in ("MODEL_B", "B_BASE")
    # Signed models carry their direction in the signal; everything else
    # (Model B, B_BASE, Model C entry) takes direction from the coordinate.
    signed = name in ("MODEL_A", "B3_PLAIN_BREAKOUT", "A_BASE", "C_BASE", "C_DIRECT_2SIGMA")
    episodes = []
    if is_state:
        run_start = None
        for i in range(n):
            v = vals[i]
            if v == 1.0 and run_start is None:
                run_start = i
            elif v != 1.0 and run_start is not None:
                episodes.append((run_start, i - 1))
                run_start = None
        if run_start is not None:
            episodes.append((run_start, n - 1))
    else:
        pending = None  # (start_idx, direction)
        for i in range(n):
            v = vals[i]
            if v == 0.0 or np.isnan(v):
                continue
            # MODEL_C's -1 is an EXIT signal (active field failed), not a
            # short entry; only +1 bars are entry events.
            if name == "MODEL_C" and v < 0:
                continue
            d = 1.0 if v > 0 else -1.0
            if pending is None:
                pending = (i, d)
            else:
                start, pd_ = pending
                if pd_ == d and i - start <= merge_gap:
                    pending = (start, d)  # extend
                else:
                    episodes.append((start, start))
                    pending = (i, d)
        if pending is not None:
            episodes.append((pending[0], pending[0]))

    xv = x.to_numpy(dtype=float) if x is not None else None
    rows = []
    for j, (start, _end) in enumerate(episodes):
        ev_time = idx[start]
        sig_dir = 1.0 if vals[start] > 0 else -1.0
        if signed:
            direction = sig_dir
        elif xv is not None and not np.isnan(xv[start]):
            direction = 1.0 if xv[start] >= 0 else -1.0
        else:
            direction = 1.0
        rows.append(
            {
                "event_id": f"{name}_{j:06d}",
                "model": name,
                "event_time": ev_time,
                "evidence_complete_time": ev_time,
                "known_time": ev_time,
                "action_time": ev_time,
                "direction": direction,
                "known_pos": start,
            }
        )
    return pd.DataFrame(rows)


def attach_coordinate_context(episodes: pd.DataFrame, x: pd.Series) -> pd.DataFrame:
    """Attach coordinate/state context at the known bar."""
    if episodes.empty:
        return episodes
    pos = episodes["known_pos"].to_numpy(dtype=int)
    xv = x.to_numpy(dtype=float)
    out = episodes.copy()
    out["x_known"] = [float(xv[p]) if not np.isnan(xv[p]) else np.nan for p in pos]
    out["dir_from_coord"] = np.sign(out["x_known"])
    # For discrete signed signals, direction is the signal sign; for state
    # signals (Model B/B_BASE) direction = sign of the coordinate at start.
    return out


def match_events(
    model_eps: pd.DataFrame, base_eps: pd.DataFrame, model: str, base: str
) -> pd.DataFrame:
    """Pair model episodes with contrast-baseline episodes.

    Classes:
      MODEL_AND_BASELINE  matched within MATCH_WINDOW bars, same direction
      MODEL_ONLY          model fires, no baseline match
      BASELINE_ONLY       baseline fires, no model match

    Returns one row per episode with: model, baseline, class,
    baseline_index (matched baseline episode or -1), timing_delta (bars,
    baseline_time - model_time; positive = baseline earlier).
    """
    rows = []
    if model_eps.empty and base_eps.empty:
        return pd.DataFrame(rows)

    base_pos = base_eps["known_pos"].to_numpy(dtype=int) if not base_eps.empty else np.array([], dtype=int)
    base_dir = base_eps["direction"].to_numpy(dtype=float) if not base_eps.empty else np.array([], dtype=float)

    if model_eps.empty:
        for j in range(len(base_eps)):
            rows.append(
                {
                    "event_id": base_eps.iloc[j]["event_id"],
                    "model": model,
                    "baseline": base,
                    "class": "BASELINE_ONLY",
                    "known_pos": int(base_pos[j]),
                    "direction": float(base_dir[j]),
                    "baseline_event_id": base_eps.iloc[j]["event_id"],
                    "baseline_index": int(j),
                    "timing_delta": np.nan,
                }
            )
        return pd.DataFrame(rows)

    model_pos = model_eps["known_pos"].to_numpy(dtype=int)
    model_dir = model_eps["direction"].to_numpy(dtype=float)
    base_used = set()

    for i in range(len(model_eps)):
        mp = model_pos[i]
        md = model_dir[i]
        best = -1
        best_dist = 10**9
        for j in range(len(base_eps)):
            if base_dir[j] != md:
                continue
            d = abs(base_pos[j] - mp)
            if d <= MATCH_WINDOW and d < best_dist:
                best = j
                best_dist = d
        if best >= 0:
            base_used.add(best)
            rows.append(
                {
                    "event_id": model_eps.iloc[i]["event_id"],
                    "model": model,
                    "baseline": base,
                    "class": "MODEL_AND_BASELINE",
                    "known_pos": int(mp),
                    "direction": float(md),
                    "baseline_event_id": base_eps.iloc[best]["event_id"],
                    "baseline_index": int(best),
                    "timing_delta": int(base_pos[best] - mp),
                }
            )
        else:
            rows.append(
                {
                    "event_id": model_eps.iloc[i]["event_id"],
                    "model": model,
                    "baseline": base,
                    "class": "MODEL_ONLY",
                    "known_pos": int(mp),
                    "direction": float(md),
                    "baseline_event_id": "",
                    "baseline_index": -1,
                    "timing_delta": np.nan,
                }
            )

    # baseline-only episodes
    for j in range(len(base_eps)):
        if j in base_used:
            continue
        rows.append(
            {
                "event_id": base_eps.iloc[j]["event_id"],
                "model": model,
                "baseline": base,
                "class": "BASELINE_ONLY",
                "known_pos": int(base_pos[j]),
                "direction": float(base_dir[j]),
                "baseline_event_id": base_eps.iloc[j]["event_id"],
                "baseline_index": int(j),
                "timing_delta": np.nan,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Structural outcomes
# ---------------------------------------------------------------------------

def measure_outcomes(episodes: pd.DataFrame, x: pd.Series, horizons=HORIZONS) -> pd.DataFrame:
    """Measure structural outcomes from known_time at fixed horizons.

    Columns: for each h — signed_disp_h, abs_disp_h, cont_h (|x| > B),
    rej_h (|x| <= B), mfe_h, mae_h; plus time_to_rej, time_to_next_state,
    next_sigma_h (h=6), persistence.
    All in σ-normalized coordinate units (x already vol-normalized).
    """
    if episodes.empty:
        return episodes.copy()
    xv = x.to_numpy(dtype=float)
    n = len(xv)
    pos = episodes["known_pos"].to_numpy(dtype=int)
    dirs = episodes["direction"].to_numpy(dtype=float)
    out = episodes.copy().reset_index(drop=True)
    H = max(horizons)
    cont = {}
    rej = {}
    sdisp = {}
    adisp = {}
    mfe = {}
    mae = {}
    for h in horizons:
        sdisp[h] = np.full(len(pos), np.nan)
        adisp[h] = np.full(len(pos), np.nan)
        cont[h] = np.full(len(pos), np.nan)
        rej[h] = np.full(len(pos), np.nan)
        mfe[h] = np.full(len(pos), np.nan)
        mae[h] = np.full(len(pos), np.nan)
    t_rej = np.full(len(pos), np.nan)
    t_next = np.full(len(pos), np.nan)
    pers = np.full(len(pos), np.nan)
    next_sigma6 = np.full(len(pos), np.nan)

    for i in range(len(pos)):
        k = pos[i]
        d = dirs[i]
        if k >= n:
            continue
        xk = xv[k]
        if np.isnan(xk):
            continue
        entry_mag = abs(xk)
        # persistence: contiguous beyond-state length from k
        plen = 0
        j = k
        while j < n and not np.isnan(xv[j]) and abs(xv[j]) > BOUNDARY:
            plen += 1
            j += 1
        pers[i] = plen
        # time to rejection / next sigma state
        for j in range(k + 1, min(k + MAX_HORIZON + 1, n)):
            if np.isnan(xv[j]):
                continue
            if np.isnan(t_rej[i]) and abs(xv[j]) <= BOUNDARY:
                t_rej[i] = j - k
            s0 = 1 if xk >= 0 else -1
            s1 = 1 if xv[j] >= 0 else -1
            if np.isnan(t_next[i]) and s1 != s0:
                t_next[i] = j - k
        for h in horizons:
            kh = k + h
            if kh >= n:
                continue
            xh = xv[kh]
            if np.isnan(xh):
                continue
            disp = xh - xk
            sdisp[h][i] = d * disp
            adisp[h][i] = abs(disp)
            cont[h][i] = 1.0 if abs(xh) > BOUNDARY else 0.0
            rej[h][i] = 1.0 if abs(xh) <= BOUNDARY else 0.0
            seg = xv[k + 1 : kh + 1]
            valid = seg[~np.isnan(seg)]
            if len(valid):
                fav = d * (valid - xk)
                mfe[h][i] = float(np.max(fav))
                mae[h][i] = float(np.min(fav))
            if h == 6:
                next_sigma6[i] = np.sign(xh) * float(np.floor(abs(xh) / STEP))
                if np.sign(xh) == 0:
                    next_sigma6[i] = 0.0

    for h in horizons:
        out[f"signed_disp_{h}"] = sdisp[h]
        out[f"abs_disp_{h}"] = adisp[h]
        out[f"cont_{h}"] = cont[h]
        out[f"rej_{h}"] = rej[h]
        out[f"mfe_{h}"] = mfe[h]
        out[f"mae_{h}"] = mae[h]
    out["time_to_rej"] = t_rej
    out["time_to_next_state"] = t_next
    out["persistence"] = pers
    out["next_sigma_6"] = next_sigma6
    return out


# ---------------------------------------------------------------------------
# Per-bar control fields
# ---------------------------------------------------------------------------

def control_fields(x: pd.Series, vol: pd.Series, dev_end: str) -> pd.DataFrame:
    """Per-bar controls: sigma state, vol tercile (frozen on dev), hour,
    session, anchor age, prior state duration. All causal (bar t uses <= t).

    Vol terciles are computed on the development window only, then applied to
    all bars (frozen, matching P4/P6 discipline).
    """
    out = pd.DataFrame(index=x.index)
    xv = x.to_numpy(dtype=float)
    n = len(xv)
    sigma = np.zeros(n, dtype=float)
    for i in range(n):
        xi = xv[i]
        if np.isnan(xi):
            sigma[i] = np.nan
        else:
            s = np.sign(xi) * np.floor(abs(xi) / STEP)
            sigma[i] = s if s != 0 else 0.0
    out["sigma_state"] = sigma

    dev_vol = vol.loc[vol.index <= pd.Timestamp(dev_end, tz="UTC")].dropna()
    lo_cut, hi_cut = dev_vol.quantile([1 / 3, 2 / 3])
    out["vol_tercile"] = pd.cut(
        vol, bins=[-np.inf, lo_cut, hi_cut, np.inf], labels=["low", "med", "high"]
    ).astype(str)

    out["hour"] = x.index.hour
    out["session"] = (x.index.hour // 4).astype(int)

    # anchor age: bars since the current trailing-50 extreme value last
    # appeared in the window (bounded backward scan, causal).
    anchor_age = np.full(n, np.nan)
    for i in range(n):
        xi = xv[i]
        if np.isnan(xi):
            continue
        lo = max(0, i - 50)
        seg = xv[lo:i]
        valid = seg[~np.isnan(seg)]
        if len(valid) == 0:
            anchor_age[i] = 0.0
            continue
        ref = abs(xi)  # reference magnitude; anchor level ~ |x| reference
        # approximate anchor age as bars since the last |x| beyond the
        # current |x| (fresh extreme), capped at 50.
        last = -1
        for j in range(i - 1, lo - 1, -1):
            if not np.isnan(xv[j]):
                if abs(xv[j]) >= ref - 1e-12:
                    last = j
                    break
        anchor_age[i] = float(i - last) if last >= 0 else float(min(i, 50))
    out["anchor_age"] = anchor_age

    # prior state duration: bars since sigma state last changed (capped 50)
    prior_dur = np.zeros(n, dtype=float)
    for i in range(n):
        if np.isnan(sigma[i]):
            prior_dur[i] = np.nan
            continue
        d = 0
        for j in range(i - 1, max(-1, i - 51), -1):
            if j < 0 or np.isnan(sigma[j]) or sigma[j] != sigma[i]:
                break
            d += 1
        prior_dur[i] = float(d)
    out["prior_state_duration"] = prior_dur
    return out
