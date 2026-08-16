"""P6 — Rekey Mechanics (MVE Phase 6 science).

This module implements the pre-registered rekey-event machinery required by
checkpoint MVE-P6-REKEY-MECHANICS.

Scientific contract (frozen, see research/mve/p6/MVE_P6_PROTOCOL.md):

- Every rekey event obeys the frozen R0.5.1 rekey schema:
      rekey_event_time <= rekey_evidence_complete_time <= rekey_known_time
      <= new_anchor_active_time
  (MVE_REKEY_CAUSAL_SCHEMA.json, enforced by mve.causality.validate_rekey_events).
- Detection consumes ONLY the sealed MorphicRekey detector plus a backward-
  looking dedup merge: no future bars decide any event or episode that is
  emitted at time t.
- RKEY-B is DELAYED: the new anchor becomes active at the retest bar j, never
  at the scan-origin bar i. No backdating, no historical rewrite.
- Outcome measurement is deliberately EX-POST relative to the activation bar
  (continuation after rekey is the object of study) and never feeds back into
  detection.
- The old-anchor counterfactual compares two state representations of the
  SAME realized path; it is ex-post evaluation only and never decides an
  anchor.
- NaN coordinates never fabricate events (fail-closed). No synthetic fill of
  missing scientific state.
- No trading logic. No PnL.

Frozen registry (P6-D):

    RKEY_A  realtime re-anchor on |x| crossing above B
    RKEY_B  delayed confirmation (retest in (i, i+4]); anchor active at j
    RKEY_C  realtime state-survival re-anchor (3-of-3 window above B)

Boundary grid B in {1.0, 2.0}; direction grid d in {+1, -1}.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mve.p4_acceptance import executable_leakage_scan  # noqa: F401  (re-exported)
from mve.rekey import MorphicRekey

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

P6_VARIANTS: tuple = ("RKEY_A", "RKEY_B", "RKEY_C")
P6_BOUNDARIES: tuple = (1.0, 2.0)
P6_DIRECTIONS: tuple = (1.0, -1.0)
P6_HORIZONS: tuple = (1, 2, 3, 6, 12, 24)
P6_MAX_HORIZON = 24
P6_STEP = 1.0
# RKEY-B retest lookahead window (sealed detector): bars (i, i+4].
P6_B_RETEST_WINDOW = 4

# Control sampling seed (frequency-matched controls).
P6_CONTROL_SEED = 4242

_MORPHIC_REKEY = MorphicRekey()


# ---------------------------------------------------------------------------
# Episode detection (sealed detector + backward dedup merge)
# ---------------------------------------------------------------------------

def _side_filtered_events(
    x: pd.Series, boundary: float, variant: str
) -> list:
    """Run the sealed detector on one signed family and keep only events whose
    ACTIVATION bar has the family's sign (positive = beyond in that family).

    The detector is direction-agnostic (abs-based). RKEY-B's sealed scan-origin
    flag can persist across a re-entry and fire a retest on the OPPOSITE side
    of its scan-origin coordinate, so the scan-origin anchor is NOT a reliable
    side indicator: the activation (retest) bar is the scientifically
    meaningful rekey bar and determines the side. Filtering by the activation
    bar's sign partitions events cleanly with no double count.
    """
    n = boundary / P6_STEP
    # the sealed detector's variant param is the single letter A/B/C
    events = _MORPHIC_REKEY.detect_rekey_events(x, step=P6_STEP, n=n, variant=variant[-1])
    xa = x.to_numpy(dtype=float)
    kept = []
    for ev in events:
        kt = int(ev["rekey_known_time"])
        if kt < 0 or kt >= len(xa):
            continue
        val = xa[kt]
        if np.isnan(val):
            continue
        if val >= 0:
            kept.append(ev)
    return kept


def _true_crossing(x: np.ndarray, lo: int, kt: int, boundary: float) -> int:
    """First bar in [lo, kt] beyond the boundary ON THE ACTIVATION SIDE after
    the last inside bar.

    `kt` is the activation bar and defines the side (sign(x[kt])); the scan
    skips opposite-side excursions so a down-move inside an up-episode is not
    mistaken for the up-crossing. Causal: uses only bars <= kt. Returns a
    position <= kt (kt itself always qualifies).
    """
    last_inside = lo - 1
    for t in range(lo, kt + 1):
        if t < len(x) and not np.isnan(x[t]) and abs(x[t]) <= boundary:
            last_inside = t
    side_sign = 1.0 if x[kt] >= 0 else -1.0
    c = last_inside + 1
    while c < kt and (
        np.isnan(x[c]) or abs(x[c]) <= boundary or np.sign(x[c]) != side_sign
    ):
        c += 1
    return int(c)


def _merge_episodes(events: list, x: np.ndarray, boundary: float) -> list:
    """Collapse the raw detection stream into distinct anchor transitions.

    Merge rule (frozen protocol sec. 5): process events in emission order; a
    candidate event begins a NEW episode iff at least one bar strictly between
    the previous kept episode's known_time and the candidate's event_time has
    abs(x) <= boundary (re-entry invalidates) or is NaN (fail-closed: unknown
    breaks continuity). Otherwise the candidate belongs to the same structural
    transition and is dropped.

    For RKEY-A/C the raw stream is already one-per-crossing, so the merge is a
    no-op. For RKEY-B it collapses the per-bar dense stream in sustained
    beyond-states into one episode per anchor transition.
    """
    ordered = sorted(events, key=lambda e: (int(e["rekey_event_time"]), int(e["rekey_known_time"])))
    kept: list = []
    for ev in ordered:
        et = int(ev["rekey_event_time"])
        if not kept:
            kept.append(ev)
            continue
        prev_kt = int(kept[-1]["rekey_known_time"])
        inside = False
        for pos in range(prev_kt + 1, et):
            if pos >= len(x):
                inside = True
                break
            v = x[pos]
            if np.isnan(v) or abs(v) <= boundary:
                inside = True
                break
        if not inside:
            continue  # same structural transition -> keep the earlier event
        kept.append(ev)
    return kept


def detect_rekey_episodes(
    signals: pd.DataFrame,
    variant: str,
    boundary: float,
    direction: float,
) -> pd.DataFrame:
    """Detect rekey EPISODES for one (variant, boundary, direction) cell.

    `signals` must carry 'x' (the signed sigma coordinate for the requested
    direction: x_up for d=+1, x_lo for d=-1; positive = beyond), 'close' and
    'vol'.

    Returns one row per episode with the frozen catalog fields (timestamps as
    timestamps, positions as ints) plus context fields used downstream.

    All fields are causal: every value placed at a bar depends only on bars
    <= that bar (the RKEY-B lookahead only schedules activation at the retest
    bar j, which is when the value is emitted).
    """
    if variant not in P6_VARIANTS:
        raise ValueError(f"Unknown P6 variant: {variant}")
    if boundary not in P6_BOUNDARIES:
        raise ValueError(f"Boundary {boundary} not in frozen grid {P6_BOUNDARIES}")
    if direction not in P6_DIRECTIONS:
        raise ValueError(f"Direction {direction} not in frozen grid {P6_DIRECTIONS}")

    x_series = signals["x"].astype(float)
    x = x_series.to_numpy(dtype=float)
    close = signals["close"].to_numpy(dtype=float)
    vol = signals["vol"].to_numpy(dtype=float)
    idx = signals.index
    n = len(idx)

    raw = _side_filtered_events(x_series, boundary, variant)
    kept = _merge_episodes(raw, x, boundary)

    rows = []
    prev_activation = None
    for ev in kept:
        et = int(ev["rekey_event_time"])
        kt = int(ev["rekey_known_time"])
        if et < 0 or et >= n or kt < 0 or kt >= n:
            continue
        if np.isnan(float(ev["new_anchor"])):
            continue
        xk = x[kt]
        vk = vol[kt]
        if np.isnan(xk) or np.isnan(vk) or vk <= 0 or np.isnan(close[kt]) or close[kt] <= 0:
            continue

        # anchor price at the activation bar (invert the coordinate definition)
        if direction > 0:
            anchor_price = close[kt] / np.exp(xk * vk)
        else:
            anchor_price = close[kt] * np.exp(xk * vk)

        # Structural re-anchor bar (P6-D amendment). Variant-specific:
        #   RKEY_A: the event bar IS the boundary crossing bar.
        #   RKEY_B: the breakout bar = first beyond bar after the last inside
        #           bar in (prev_known, kt] (the sealed scan-origin event_time
        #           can lag this when its breakout flag persists).
        #   RKEY_C: the event bar IS the sigma-state crossing bar (the sealed
        #           _rekey_variant_c anchors at the coordinate of that bar).
        # The re-anchor point is the coordinate at this bar (equals the sealed
        # scan-origin value in well-formed cases; honest in stale-flag cases).
        if variant == "RKEY_B":
            lo = 0 if prev_activation is None else prev_activation + 1
            crossing = _true_crossing(x, lo, kt, boundary)
        else:
            crossing = et
        anchor_coord = x[crossing] if not np.isnan(x[crossing]) else float(ev["new_anchor"])

        # rekey level and boundary level (price axis)
        if direction > 0:
            level = anchor_price * np.exp(anchor_coord * vk)
            level_b = anchor_price * np.exp(boundary * vk)
        else:
            level = anchor_price * np.exp(-anchor_coord * vk)
            level_b = anchor_price * np.exp(-boundary * vk)

        # prior-state duration (variant-specific):
        #   A/B: consecutive inside bars before the breakout (pre-breakout
        #        consolidation).
        #   C:   consecutive bars in the previous sigma state before the
        #        state up-crossing.
        prior_dur = 0
        if variant == "RKEY_C":
            prev_state = int(abs(x[et]) // P6_STEP) - 1
            p = et - 1
            while p >= 0 and not np.isnan(x[p]) and int(abs(x[p]) // P6_STEP) == prev_state:
                prior_dur += 1
                p -= 1
        else:
            p = crossing - 1
            while p >= 0 and not np.isnan(x[p]) and abs(x[p]) <= boundary:
                prior_dur += 1
                p -= 1

        # anchor age: bars since the previous kept episode activation (the
        # origin anchor predates the series; its age is lower-bounded by et).
        anchor_age = et if prev_activation is None else et - prev_activation

        coord_after = xk - anchor_coord  # new-frame displacement at activation
        mom = 0
        if kt > 0 and not np.isnan(x[kt - 1]):
            mom = 1 if xk >= x[kt - 1] else -1

        rows.append(
            {
                "episode_id": f"RK-{variant[-1]}-d{int(direction):+d}-b{boundary:g}-e{et}-k{kt}",
                "variant": variant,
                "direction": int(direction),
                "boundary": boundary,
                "old_anchor_type": "TRAILING50",
                "new_anchor_type": "TRAILING50",
                "old_anchor_value": float(anchor_price),
                "new_anchor_value": float(anchor_coord),
                "anchor_value_sealed": float(ev["new_anchor"]),
                "rekey_event_time": idx[et],
                "rekey_evidence_complete_time": idx[kt],
                "rekey_known_time": idx[kt],
                "new_anchor_active_time": idx[kt],
                "event_pos": int(et),
                "known_pos": int(kt),
                "crossing_pos": int(crossing),
                "latency_bars": int(kt - et),
                "crossing_latency_bars": int(kt - crossing),
                "coordinate_before": float(xk),
                "coordinate_after": float(coord_after),
                "sigma_state_before": float(np.floor(abs(xk))),
                "sigma_state_after": float(np.floor(abs(coord_after))),
                "dist_from_old_anchor": float(abs(xk)),
                "dist_from_new_anchor": float(abs(coord_after)),
                "dist_from_boundary": float(xk - boundary),
                "vol_known": float(vk),
                "prior_state_duration": int(prior_dur),
                "anchor_age": int(anchor_age),
                "momentum": int(mom),
                "level_known": float(level),
                "level_b_known": float(level_b),
                "anchor_price_known": float(anchor_price),
                "duplicate_episode_id": f"X-d{int(direction):+d}-b{boundary:g}-e{crossing}",
            }
        )
        prev_activation = int(kt)
    return pd.DataFrame(rows)


def rekey_known_series(
    signals: pd.DataFrame,
    variant: str,
    boundary: float,
    direction: float,
) -> pd.Series:
    """Per-bar rekey-known indicator (float 0/1) for the causality gates.

    position t == 1 iff a rekey episode of this variant is KNOWN at t
    (new_anchor_active_time == t). A causal detector must return max diff 0.0
    under future perturbation and truncation.
    """
    ep = detect_rekey_episodes(signals, variant, boundary, direction)
    known = np.zeros(len(signals), dtype=float)
    if len(ep):
        pos = ep["known_pos"].to_numpy(dtype=int)
        pos = pos[(pos >= 0) & (pos < len(signals))]
        if len(pos):
            known[pos] = 1.0
    return pd.Series(known, index=signals.index)


# ---------------------------------------------------------------------------
# Outcome measurement (EX-POST relative to activation; deliberate)
# ---------------------------------------------------------------------------

def measure_rekey_outcomes(
    episodes: pd.DataFrame,
    signals: pd.DataFrame,
    horizons: tuple = P6_HORIZONS,
    max_horizon: int = P6_MAX_HORIZON,
) -> pd.DataFrame:
    """Measure forward state outcomes for rekey episodes.

    k = known_pos (new anchor active bar). All outcomes are measured over
    bars strictly after k against the FIXED rekey level L (frozen protocol
    sec. 6). Ex-post by design; never feeds back into detection.

    Requires signals to carry 'x', 'close' and 'vol'.
    """
    if episodes.empty:
        return episodes.copy()

    x = signals["x"].to_numpy(dtype=float)
    close = signals["close"].to_numpy(dtype=float)
    vol = signals["vol"].to_numpy(dtype=float)

    rows = []
    for _, ev in episodes.iterrows():
        k = int(ev["known_pos"])
        if k < 0 or k >= len(x):
            continue
        d = float(ev["direction"])
        L = float(ev["level_known"])
        A_k = float(ev["anchor_price_known"])
        vk = float(ev["vol_known"])
        if L <= 0 or A_k <= 0 or np.isnan(vk) or vk <= 0:
            continue

        def s(t: int) -> float:
            c = close[t]
            if np.isnan(c) or c <= 0:
                return np.nan
            return d * np.log(c / L) / vk

        def z(t: int) -> float:
            c = close[t]
            if np.isnan(c) or c <= 0:
                return np.nan
            return d * np.log(c / A_k) / vk

        row = {
            "x_known": float(ev["coordinate_before"]),
            "abs_x_known": float(abs(ev["coordinate_before"])),
            "sigma_state_known": float(ev["sigma_state_before"]),
            "dist_boundary_known": float(ev["dist_from_boundary"]),
            "vol_known": float(vk),
            "level_known": float(L),
            "level_b_known": float(ev["level_b_known"]),
        }
        time_to_rej = None
        time_to_next = None
        persist = 0
        j = k + 1
        while j < len(close):
            sv = s(j)
            if np.isnan(sv) or sv <= 0:
                break
            persist += 1
            j += 1
        row["persist_dur"] = persist

        for h in horizons:
            kh = k + h
            if kh >= len(close):
                cont, disp, ndisp, mfd, mad, nxt, oldst = (np.nan,) * 7
            else:
                sv = s(kh)
                zv = z(kh)
                if np.isnan(sv) or np.isnan(zv) or np.isnan(close[kh]):
                    cont, disp, ndisp, mfd, mad, nxt, oldst = (np.nan,) * 7
                else:
                    cont = 1.0 if sv > 0 else 0.0
                    disp = d * (close[kh] - L)
                    ndisp = d * (close[kh] - L) / L
                    seg = []
                    for tt in range(k + 1, kh + 1):
                        if tt < len(close) and not np.isnan(close[tt]):
                            seg.append(d * (close[tt] - L) / L)
                    mfd = float(max(seg)) if seg else np.nan
                    mad = float(max(-v for v in seg)) if seg else np.nan
                    nxt = float(np.floor(abs(sv)))
                    oldst = float(np.floor(abs(zv)))
            row[f"cont_{h}"] = cont
            row[f"disp_{h}"] = disp
            row[f"norm_disp_{h}"] = ndisp
            row[f"mfd_{h}"] = mfd
            row[f"mad_{h}"] = mad
            row[f"next_state_{h}"] = nxt
            row[f"old_state_{h}"] = oldst
            if time_to_rej is None:
                for jj in range(k + 1, kh + 1):
                    if jj < len(close):
                        sv = s(jj)
                        if not np.isnan(sv) and sv <= 0:
                            time_to_rej = jj - k
                            break
            row[f"rej_within_{h}"] = 1.0 if (time_to_rej is not None and time_to_rej <= h) else 0.0
            if time_to_next is None:
                for jj in range(k + 1, kh + 1):
                    if jj < len(close):
                        sv = s(jj)
                        if not np.isnan(sv) and floor_abs(sv) >= 1:
                            time_to_next = jj - k
                            break
        row["time_to_rejection"] = time_to_rej
        row["time_to_next_state"] = time_to_next
        row["survival_censor"] = 1 if time_to_rej is None else 0
        rows.append(row)

    out = pd.concat([episodes.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    # the events frame already carries level_known/level_b_known/vol_known;
    # the outcome row repeats them identically -> drop the duplicate copies.
    out = out.loc[:, ~out.columns.duplicated()]
    return out


def floor_abs(v: float) -> int:
    return int(np.floor(abs(v)))


# ---------------------------------------------------------------------------
# Old-anchor counterfactual (PATH A rekey vs PATH B keep-old-anchor)
# ---------------------------------------------------------------------------

def old_anchor_counterfactual(
    outcomes: pd.DataFrame,
    signals: pd.DataFrame,
    horizon: int = 6,
) -> pd.DataFrame:
    """Per-episode state-representation comparison (frozen protocol sec. 7).

    For each episode, both frames are evaluated on the SAME realized path
    from the activation bar k with vol frozen at k:

        frame A (rekey):   s_t = d * ln(close_t / L) / vol_k
        frame B (old):     z_t = d * ln(close_t / A_k) / vol_k

    Returns one row per episode with per-frame h-horizon state, displacement
    dispersion over (k, k+h], and the new-frame persistence.

    Ex-post evaluation only; neither frame is chosen using future data.
    """
    if outcomes.empty:
        return outcomes.copy()
    close = signals["close"].to_numpy(dtype=float)
    rows = []
    for _, ev in outcomes.iterrows():
        k = int(ev["known_pos"])
        if k < 0 or k >= len(close):
            continue
        d = float(ev["direction"])
        L = float(ev["level_known"])
        A_k = float(ev["anchor_price_known"])
        vk = float(ev["vol_known"])
        if L <= 0 or A_k <= 0 or np.isnan(vk) or vk <= 0:
            continue
        kk = k + horizon
        if kk >= len(close):
            continue
        if np.isnan(close[kk]) or close[kk] <= 0:
            continue
        sv = d * np.log(close[kk] / L) / vk
        zv = d * np.log(close[kk] / A_k) / vk
        seg_s, seg_z = [], []
        for tt in range(k + 1, kk + 1):
            if tt < len(close) and not np.isnan(close[tt]) and close[tt] > 0:
                seg_s.append(d * np.log(close[tt] / L) / vk)
                seg_z.append(d * np.log(close[tt] / A_k) / vk)
        rows.append(
            {
                "episode_id": ev["episode_id"],
                "variant": ev["variant"],
                "boundary": ev["boundary"],
                "direction": ev["direction"],
                "known_pos": int(k),
                "state_A_at_h": float(np.floor(abs(sv))),
                "state_B_at_h": float(np.floor(abs(zv))),
                "abs_disp_A_at_h": float(abs(sv)),
                "abs_disp_B_at_h": float(abs(zv)),
                "mean_abs_disp_A_win": float(np.mean(np.abs(seg_s))) if seg_s else np.nan,
                "mean_abs_disp_B_win": float(np.mean(np.abs(seg_z))) if seg_z else np.nan,
                "persist_dur": float(ev["persist_dur"]) if "persist_dur" in ev else np.nan,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Control events for incremental-information tests (frozen protocol sec. 8)
# ---------------------------------------------------------------------------

def control_events(
    signals: pd.DataFrame,
    variant: str,
    boundary: float,
    direction: float,
    n_target: int,
    seed: int = P6_CONTROL_SEED,
) -> pd.DataFrame:
    """Build the no-rekey control event set for one variant cell.

    RKEY_A control: frequency-matched sample of beyond-state bars that are NOT
    fresh crossings (the already-rekeyed state; known at the bar itself).

    RKEY_B control: fresh crossings with NO confirming retest within 4 bars
    (breakout without confirmation; classification known at i+4).

    RKEY_C control: fresh crossings where C did NOT fire (state up-crossing
    without the 3-of-3 window; known at the crossing bar).

    Returns a DataFrame with the same catalog columns the outcome/LR pipeline
    expects (episode_id, variant, direction, boundary, event_pos, known_pos,
    coordinate_before, dist_from_boundary, sigma_state_before, vol_known,
    level_b_known, anchor_price_known, level_known, anchor_age, ...).
    """
    x = signals["x"].to_numpy(dtype=float)
    close = signals["close"].to_numpy(dtype=float)
    vol = signals["vol"].to_numpy(dtype=float)
    idx = signals.index
    n = len(idx)

    crossing = set()
    for i in range(1, n):
        if not np.isnan(x[i]) and not np.isnan(x[i - 1]) and abs(x[i]) > boundary and abs(x[i - 1]) <= boundary:
            crossing.add(i)

    rows = []
    if variant == "RKEY_A":
        # beyond-state bars that are NOT fresh crossings
        pool = [i for i in range(n) if not np.isnan(x[i]) and abs(x[i]) > boundary and i not in crossing]
        rng = np.random.default_rng(seed + int(direction) * 1000)
        if len(pool) > 0:
            take = min(n_target, len(pool))
            for i in rng.choice(pool, size=take, replace=False):
                r = _control_row(idx, x, close, vol, boundary, direction, i, i, "CONTROL_A")
                if r is not None:
                    rows.append(r)
    elif variant == "RKEY_B":
        # crossings with no B episode: no |x|>B bar in (i, i+4]
        for i in sorted(crossing):
            confirmed = False
            for j in range(i + 1, min(i + P6_B_RETEST_WINDOW + 1, n)):
                if not np.isnan(x[j]) and abs(x[j]) > boundary:
                    confirmed = True
                    break
            if confirmed:
                continue
            kt = min(i + P6_B_RETEST_WINDOW, n - 1)
            if kt < n:
                r = _control_row(idx, x, close, vol, boundary, direction, i, kt, "CONTROL_B")
                if r is not None:
                    rows.append(r)
    elif variant == "RKEY_C":
        # crossings where C did not fire (state up-crossing without 3-of-3)
        for i in sorted(crossing):
            cur_state = int(abs(x[i]) // P6_STEP)
            prev = x[i - 1] if i > 0 else np.nan
            prev_state = int(abs(prev) // P6_STEP) if not np.isnan(prev) else -1
            window_ok = False
            if i >= 5:
                win = x[max(0, i - 2): i + 1]
                if not np.isnan(win).any():
                    window_ok = int(np.sum(np.abs(win) > boundary)) >= 3
            fired = cur_state > prev_state and window_ok
            if not fired:
                r = _control_row(idx, x, close, vol, boundary, direction, i, i, "CONTROL_C")
                if r is not None:
                    rows.append(r)
    else:  # pragma: no cover
        raise ValueError(f"Unknown variant: {variant}")

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # order by control event time, dedupe by (event_pos)
    out = out.drop_duplicates(subset=["event_pos"]).sort_values("event_pos").reset_index(drop=True)
    return out


def _control_row(idx, x, close, vol, boundary, direction, et, kt, ctrl_id: str) -> dict:
    xk = x[kt]
    vk = vol[kt]
    if np.isnan(xk) or np.isnan(vk) or vk <= 0 or np.isnan(close[kt]) or close[kt] <= 0:
        return None
    if direction > 0:
        anchor_price = close[kt] / np.exp(xk * vk)
    else:
        anchor_price = close[kt] * np.exp(xk * vk)
    if anchor_price <= 0:
        return None
    if direction > 0:
        level_b = anchor_price * np.exp(boundary * vk)
    else:
        level_b = anchor_price * np.exp(-boundary * vk)
    # prior duration of the beyond-state (control context)
    prior_dur = 0
    p = et - 1
    while p >= 0 and not np.isnan(x[p]) and abs(x[p]) > boundary:
        prior_dur += 1
        p -= 1
    return {
        "episode_id": f"{ctrl_id}-d{int(direction):+d}-b{boundary:g}-e{et}",
        "variant": "RKEY_" + ctrl_id[-1],
        "direction": int(direction),
        "boundary": boundary,
        "old_anchor_type": "TRAILING50",
        "new_anchor_type": "NONE",
        "old_anchor_value": float(anchor_price),
        "new_anchor_value": 0.0,
        "rekey_event_time": idx[et],
        "rekey_evidence_complete_time": idx[kt],
        "rekey_known_time": idx[kt],
        "new_anchor_active_time": idx[kt],
        "event_pos": int(et),
        "known_pos": int(kt),
        "latency_bars": int(kt - et),
        "coordinate_before": float(xk),
        "coordinate_after": float(xk),
        "sigma_state_before": float(np.floor(abs(xk))),
        "sigma_state_after": float(np.floor(abs(xk))),
        "dist_from_old_anchor": float(abs(xk)),
        "dist_from_new_anchor": float(abs(xk)),
        "dist_from_boundary": float(xk - boundary),
        "vol_known": float(vk),
        "prior_state_duration": int(prior_dur),
        "anchor_age": int(et),
        "momentum": 0,
        "level_known": float(level_b),
        "level_b_known": float(level_b),
        "anchor_price_known": float(anchor_price),
        "duplicate_episode_id": f"X-d{int(direction):+d}-b{boundary:g}-e{et}",
        "is_control": True,
    }
