"""P4 — Causal Acceptance Engine (MVE Phase 4 science).

This module implements the pre-registered acceptance-variant family and the
forward-only episode machinery required by checkpoint MVE-P4-CAUSAL-ACCEPTANCE-ENGINE.

Scientific contract (frozen, see research/mve/p4/MVE_P4_PROTOCOL.md):

- Every acceptance event obeys the frozen acceptance schema:
      state_event_time <= evidence_complete_time <= acceptance_known_time
  (MVE_ACCEPTANCE_CAUSAL_SCHEMA.json, enforced by mve.causality).
- Event detection is STRICTLY forward: the state at bar t depends only on
  bars <= t. No future bars, no centered windows, no backfill, no synthetic
  fill of missing scientific state.
- Outcome measurement is deliberately EX-POST relative to the acceptance-known
  bar (that is the object of study: continuation after acceptance). It never
  feeds back into detection.
- NaN coordinates are never fabricated into events; warmup bars simply produce
  no events (fail-closed).
- No trading logic. No stops, no targets, no sizing. This is structure-first
  science.

Frozen variant registry (P4-D):

    A0 TOUCH          — intrabar touch/breach of the boundary; acceptance known
                        at the touch bar close (baseline).
    A1 CLOSE          — close beyond the boundary; accepted iff the touch bar
                        closes beyond, else REJECTED at the touch bar close.
    A2 OCCUPANCY MofN — accepted at the first beyond-close bar whose trailing
                        N-bar close-beyond count >= M (grid 2of3 / 3of4 / 3of5).
                        Dips are tolerated (occupancy semantics). Rejection =
                        episode horizon expiry without completion.
    A3 PERSISTENCE K  — K consecutive beyond closes (grid 2/3/4). Any inside
                        close after the beyond run has begun breaks it
                        (REJECTED).
    A4 RETEST-HOLD    — break (beyond close) -> retest (close in the retest
                        zone [0.5B, B) after a beyond close) -> hold
                        (beyond close after the retest). Rejection = close
                        < 0.5B before confirmation. Episodes that break and
                        hold without a retest EXPIRE at the horizon (variant
                        never claims them).
    A5 (classification) — REJECTED/EXPIRED episodes = failed acceptance /
                        rejection control for the variant under study.

Episodes are per (direction, boundary, variant). An episode opens at the
first touch bar with no active episode for that variant and closes at its
resolution (acceptance / rejection / expiry at the max horizon H=24).
"""
from __future__ import annotations

import ast
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

# Acceptance variants: id -> human label. Order is the pre-registered order.
P4_VARIANTS: tuple = (
    "A0_TOUCH",
    "A1_CLOSE",
    "A2_2OF3",
    "A2_3OF4",
    "A2_3OF5",
    "A3_PERS_2",
    "A3_PERS_3",
    "A3_PERS_4",
    "A4_RETEST_HOLD",
)

A2_GRID = {"A2_2OF3": (2, 3), "A2_3OF4": (3, 4), "A2_3OF5": (3, 5)}
A3_GRID = {"A3_PERS_2": 2, "A3_PERS_3": 3, "A3_PERS_4": 4}

# Boundaries (signed, in sigma units) tested in P4.
P4_BOUNDARIES: tuple = (1.0, 2.0)

# Directions: +1 = upper boundary (price above anchor), -1 = lower boundary.
P4_DIRECTIONS: tuple = (1.0, -1.0)

# Max episode horizon (H1 bars) before an unresolved episode EXPIRES.
P4_MAX_HORIZON = 24

# Fixed outcome horizons (H1 bars) measured after acceptance-known time.
P4_HORIZONS: tuple = (1, 2, 3, 6, 12, 24)

# Retest zone for A4: close coordinate within [RETEST_LOW, B) after a break.
P4_RETEST_LOW = 0.5

# Pivot confirmation window (bars) for the delayed pivot anchors.
P4_PIVOT_WINDOW = 5
# Volatility estimator used for P4 coordinates.
P4_VOL_ESTIMATOR = "close_to_close"
# Pivot config mirrors mve.anchors defaults.
P4_ANCHOR_CONFIG = {"pivot_high_low": {"window": 5, "min_pivot_height": 0.01, "min_pivot_width": 3}}
# Trailing-anchor robustness family parameters.
P4_TRAILING_WINDOW = 50
P4_TRAILING_MIN_PERIODS = 20


# ---------------------------------------------------------------------------
# Coordinate fields (causal building blocks)
# ---------------------------------------------------------------------------

def coordinate_fields(
    df: pd.DataFrame,
    anchor_up: pd.Series,
    anchor_lo: pd.Series,
    vol: pd.Series,
) -> pd.DataFrame:
    """Signed directional coordinate fields from OHLCV + causal anchors + vol.

    For direction d = +1 (upper family): x = ln(price / anchor_up) / vol.
    For direction d = -1 (lower family): x = -ln(price / anchor_lo) / vol
    (signed so that positive x means "beyond" for BOTH directions).

    Returns a DataFrame indexed like df with columns:
        x_close, x_extreme  (x_extreme uses high for d=+1, low for d=-1)
        beyond              (x_close >= B placeholder, per-boundary)
        touch               (x_extreme >= B placeholder, per-boundary)
    The caller supplies per-boundary B; see per_boundary_signals().

    NaN in anchor/vol propagates to NaN coordinates (no synthetic fill).
    """
    out = pd.DataFrame(index=df.index, dtype=float)
    vol_safe = vol.replace(0.0, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["x_close_up"] = np.log(df["close"] / anchor_up) / vol_safe
        out["x_extreme_up"] = np.log(df["high"] / anchor_up) / vol_safe
        out["x_close_lo"] = -np.log(df["close"] / anchor_lo) / vol_safe
        out["x_extreme_lo"] = -np.log(df["low"] / anchor_lo) / vol_safe
    return out


def per_boundary_signals(
    fields: pd.DataFrame, boundary: float, direction: float
) -> pd.DataFrame:
    """Signed coordinate signals for one (boundary, direction) cell.

    Returns a DataFrame with columns:
        x        signed close coordinate (NaN where anchor/vol missing)
        x_ext    signed extreme coordinate (high/low)
        beyond   bool: x >= boundary (close basis)
        touch    bool: x_ext >= boundary (intrabar basis)

    All columns are causal (bar t uses only bars <= t).
    """
    if direction > 0:
        x = fields["x_close_up"].astype(float)
        x_ext = fields["x_extreme_up"].astype(float)
    else:
        x = fields["x_close_lo"].astype(float)
        x_ext = fields["x_extreme_lo"].astype(float)
    sig = pd.DataFrame({"x": x, "x_ext": x_ext}, index=fields.index)
    sig["beyond"] = sig["x"] >= boundary
    sig["touch"] = sig["x_ext"] >= boundary
    return sig


# ---------------------------------------------------------------------------
# Forward episode detection (one variant state machine per (d, B, variant))
# ---------------------------------------------------------------------------

def _run_variant(
    x: np.ndarray,
    beyond: np.ndarray,
    touch: np.ndarray,
    variant: str,
    boundary: float,
    max_horizon: int = P4_MAX_HORIZON,
) -> tuple:
    """Run the forward state machine for one variant on one (d, B) cell.

    Returns parallel lists over resolved episodes:
        start_pos, accept_pos (or -1), reject_pos (or -1), expiry_pos (or -1),
        first_beyond_pos (or -1), resolution.

    Pure forward: position i is processed only with data <= i.
    NaN coordinates are treated as not-beyond / not-touch (never fabricated
    into events); the state machine itself is NaN-agnostic because beyond and
    touch are precomputed booleans.
    """
    n = len(x)
    starts: list = []
    accepts: list = []
    rejects: list = []
    expires: list = []
    first_beyonds: list = []
    resolutions: list = []

    i = 0
    while i < n:
        # Find the next touch bar that opens an episode.
        while i < n and not bool(touch[i]):
            i += 1
        if i >= n:
            break
        t0 = i
        first_beyond = -1
        accepted = -1
        rejected = -1
        expired = -1
        resolution = "ACTIVE"

        if variant == "A0_TOUCH":
            accepted = t0
            first_beyond = t0 if beyond[t0] else -1
        elif variant == "A1_CLOSE":
            if beyond[t0]:
                accepted = t0
                first_beyond = t0
            else:
                rejected = t0
        elif variant.startswith("A2_"):
            m, nwin = A2_GRID[variant]
            # Trailing beyond-count window (causal). Pre-episode bars can never
            # be beyond (a beyond close implies a touch, which would have
            # opened the episode earlier), so no clip is required.
            counts = np.convolve(beyond.astype(np.int8), np.ones(nwin, dtype=np.int8), mode="full")[:n]
            t = t0
            while t < n and (t - t0) <= max_horizon:
                if beyond[t] and counts[t] >= m:
                    accepted = t
                    break
                t += 1
            if accepted == -1:
                expired = min(t0 + max_horizon, n - 1)
            # first_beyond for A2 (descriptive): first beyond close in episode.
            for j in range(t0, n):
                if beyond[j]:
                    first_beyond = j
                    break
        elif variant.startswith("A3_"):
            k = A3_GRID[variant]
            run = 0
            t = t0
            while t < n and (t - t0) <= max_horizon:
                if beyond[t]:
                    if t > t0 and beyond[t - 1]:
                        run += 1
                    else:
                        run = 1
                    if first_beyond == -1:
                        first_beyond = t
                    if run >= k:
                        accepted = t
                        break
                else:
                    if first_beyond != -1:
                        rejected = t
                        break
                t += 1
            if accepted == -1 and rejected == -1:
                expired = min(t0 + max_horizon, n - 1)
        elif variant == "A4_RETEST_HOLD":
            state = 0  # 0=WAIT_BREAK, 1=WAIT_RETEST, 2=WAIT_CONFIRM
            t = t0
            while t < n and (t - t0) <= max_horizon:
                val = x[t]
                if np.isnan(val):
                    t += 1
                    continue
                if val >= boundary:
                    if state == 0:
                        first_beyond = t
                        state = 1
                    elif state == 2:
                        accepted = t
                        break
                    # state 1: holding beyond, no retest yet — keep waiting.
                elif val >= P4_RETEST_LOW * boundary:
                    if state == 1:
                        state = 2
                else:
                    rejected = t
                    break
                t += 1
            if accepted == -1 and rejected == -1:
                expired = min(t0 + max_horizon, n - 1)
        else:  # pragma: no cover — guarded by registry checks upstream
            raise ValueError(f"Unknown variant: {variant}")

        starts.append(t0)
        accepts.append(accepted)
        rejects.append(rejected)
        expires.append(expired)
        first_beyonds.append(first_beyond)
        if accepted != -1:
            resolutions.append("ACCEPTED")
        elif rejected != -1:
            resolutions.append("REJECTED")
        elif expired != -1:
            resolutions.append("EXPIRED")
        else:  # pragma: no cover
            resolutions.append("ACTIVE")

        # The episode closes at its terminal bar; the next episode opens at the
        # next touch AFTER the terminal bar.
        terminal = max(accepted, rejected, expired)
        i = terminal + 1 if terminal != -1 else n

    return starts, accepts, rejects, expires, first_beyonds, resolutions


def detect_acceptance_episodes(
    signals: pd.DataFrame,
    variant: str,
    boundary: float,
    direction: float,
    max_horizon: int = P4_MAX_HORIZON,
) -> pd.DataFrame:
    """Detect episodes for one (variant, boundary, direction) cell.

    Returns a DataFrame (one row per episode) with:
        episode_id, variant, direction, boundary,
        event_time, evidence_complete_time, acceptance_known_time,
        event_pos, terminal_pos, first_beyond_pos,
        resolution, accepted (bool).

    Timestamps are derived from the signals index (UTC). All fields are
    causal: no bar's episode state depends on later bars.
    """
    if variant not in P4_VARIANTS:
        raise ValueError(f"Unknown P4 variant: {variant}")
    if variant.startswith("A2_") and variant not in A2_GRID:
        raise ValueError(f"Unknown occupancy grid: {variant}")
    if variant.startswith("A3_") and variant not in A3_GRID:
        raise ValueError(f"Unknown persistence grid: {variant}")

    idx = signals.index
    x = signals["x"].to_numpy(dtype=float)
    beyond = signals["beyond"].to_numpy(dtype=bool)
    touch = signals["touch"].to_numpy(dtype=bool)

    starts, accepts, rejects, expires, first_beyonds, resolutions = _run_variant(
        x, beyond, touch, variant, boundary, max_horizon
    )

    rows = []
    for k, t0 in enumerate(starts):
        accept = accepts[k]
        reject = rejects[k]
        expire = expires[k]
        terminal = max(accept, reject, expire)
        resolution = resolutions[k]
        if resolution == "ACCEPTED":
            ev_known = accept
        else:
            ev_known = terminal
        rows.append(
            {
                "episode_id": f"EP-d{int(direction):+d}-b{boundary:g}-t{t0}",
                "variant": variant,
                "direction": int(direction),
                "boundary": boundary,
                "event_time": idx[t0],
                "evidence_complete_time": idx[ev_known],
                "acceptance_known_time": idx[ev_known],
                "event_pos": int(t0),
                "terminal_pos": int(terminal),
                "first_beyond_pos": int(first_beyonds[k]),
                "acceptance_pos": int(accept),
                "rejection_pos": int(reject),
                "expiry_pos": int(expire),
                "resolution": resolution,
                "accepted": resolution == "ACCEPTED",
            }
        )
    return pd.DataFrame(rows)


def acceptance_known_series(
    signals: pd.DataFrame,
    variant: str,
    boundary: float,
    direction: float,
    max_horizon: int = P4_MAX_HORIZON,
) -> pd.Series:
    """Per-bar acceptance-known indicator (float 0/1) for causality checks.

    position t == 1 iff an acceptance event for this variant is KNOWN at t
    (acceptance_known_time == t). Used by the future-perturbation and
    truncation harness: a causal detector must return max diff 0.0.
    """
    ep = detect_acceptance_episodes(signals, variant, boundary, direction, max_horizon)
    known = np.zeros(len(signals), dtype=float)
    if len(ep):
        pos = ep.loc[ep["accepted"], "acceptance_pos"].to_numpy(dtype=int)
        pos = pos[(pos >= 0) & (pos < len(signals))]
        if len(pos):
            known[pos] = 1.0
    return pd.Series(known, index=signals.index)


# ---------------------------------------------------------------------------
# Outcome measurement (EX-POST relative to acceptance-known time; deliberate)
# ---------------------------------------------------------------------------

def measure_outcomes(
    episodes: pd.DataFrame,
    signals: pd.DataFrame,
    horizons: tuple = P4_HORIZONS,
    max_horizon: int = P4_MAX_HORIZON,
) -> pd.DataFrame:
    """Measure forward state outcomes for accepted episodes.

    k = acceptance_pos (acceptance-known bar). All outcomes are measured over
    bars strictly after k. These are ex-post measurements BY DESIGN and never
    feed back into detection.

    Outcome semantics (frozen in MVE_P4_PROTOCOL.md sec. 4): the acceptance
    bar k defines a FIXED price level L = anchor_k * exp(B * sigma_k), i.e.
    the price level of the accepted boundary. Continuation/rejection are
    measured against L (not against the ratcheting live anchor, which absorbs
    the acceptance bar and would make "still beyond" degenerate):

        cont_h           close[k+h] >= L
        rej_within_h     first bar in (k, k+h] with close < L
        disp_h           close[k+h] - L           (signed, level units)
        norm_disp_h      (close[k+h] - L) / L     (price-relative)
        mfd_h            max_{j in (k,k+h]} (close[j] - L) / L
        mad_h            max_{j in (k,k+h]} (L - close[j]) / L
        sigma_state_h    floor(|x_frozen[k+h]|), x_frozen = ln(close/anchor_k)/sigma_k
        time_to_next_state / next_state_first    first frozen-state increase
        persist_dur      consecutive bars from k+1 with close >= L

    Requires signals to carry 'x', 'close' and 'vol' columns.
    """
    accepted = episodes[episodes["accepted"]].copy()
    if accepted.empty:
        return accepted
    return _measure_from_anchor(accepted, signals, "acceptance_pos", horizons)


def measure_failed_outcomes(
    episodes: pd.DataFrame,
    signals: pd.DataFrame,
    horizons: tuple = P4_HORIZONS,
    max_horizon: int = P4_MAX_HORIZON,
) -> pd.DataFrame:
    """Measure forward state outcomes for FAILED (rejected/expired) episodes.

    k = terminal_pos (the bar at which the acceptance attempt failed). This is
    the A5 failed-acceptance / rejection control: what happens after a breach
    that fails the variant's acceptance criterion. Same ex-post contract as
    measure_outcomes.
    """
    failed = episodes[~episodes["accepted"]].copy()
    if failed.empty:
        return failed
    return _measure_from_anchor(failed, signals, "terminal_pos", horizons)


def _measure_from_anchor(
    episodes: pd.DataFrame,
    signals: pd.DataFrame,
    anchor_col: str,
    horizons: tuple,
) -> pd.DataFrame:
    """Shared outcome measurement anchored at an explicit episode column."""
    if episodes.empty:
        return episodes

    x = signals["x"].to_numpy(dtype=float)
    close = signals["close"].to_numpy(dtype=float)
    vol = signals["vol"].to_numpy(dtype=float)
    boundary = float(episodes["boundary"].to_numpy()[0])

    rows = []
    for _, ev in episodes.iterrows():
        k = int(ev[anchor_col])
        if k < 0 or k >= len(x):
            continue
        xk = x[k]
        vk = vol[k]
        if np.isnan(xk) or np.isnan(vk) or vk <= 0 or np.isnan(close[k]) or close[k] <= 0:
            continue
        # anchor price at k and the fixed boundary price level at k
        ak = close[k] / np.exp(xk * vk)
        level = ak * np.exp(boundary * vk)

        row = {
            "x_known": float(xk),
            "abs_x_known": float(abs(xk)),
            "dist_boundary_known": float(xk - boundary),
            "sigma_state_known": float(np.floor(abs(xk))),
            "level_known": float(level),
        }
        time_to_rej = None
        next_state = None
        time_to_next = None
        persist = 0
        j = k + 1
        while j < len(close) and not np.isnan(close[j]) and close[j] >= level:
            persist += 1
            j += 1
        row["persist_dur"] = persist
        cur_state = int(np.floor(abs(xk)))

        for h in horizons:
            kh = k + h
            if kh >= len(close) or np.isnan(close[kh]) or close[kh] <= 0:
                cont = np.nan
                disp = np.nan
                ndisp = np.nan
                mfd = np.nan
                mad = np.nan
                nxt = np.nan
            else:
                cont = float(close[kh] >= level)
                disp = float(close[kh] - level)
                ndisp = float((close[kh] - level) / level)
                seg = close[k + 1 : kh + 1]
                mfd = float(np.nanmax((seg - level) / level))
                mad = float(np.nanmax((level - seg) / level))
                # frozen-coordinate state (anchor/vol frozen at k)
                xf = np.log(close[kh] / ak) / vk
                nxt = float(np.floor(abs(xf)))
            row[f"cont_{h}"] = cont
            row[f"disp_{h}"] = disp
            row[f"norm_disp_{h}"] = ndisp
            row[f"mfd_{h}"] = mfd
            row[f"mad_{h}"] = mad
            row[f"next_state_{h}"] = nxt
            if time_to_rej is None:
                for jj in range(k + 1, kh + 1):
                    if jj < len(close) and not np.isnan(close[jj]) and close[jj] < level:
                        time_to_rej = jj - k
                        break
            row[f"rej_within_{h}"] = 1.0 if (time_to_rej is not None and time_to_rej <= h) else 0.0
            if next_state is None:
                for jj in range(k + 1, kh + 1):
                    if jj < len(close) and not np.isnan(close[jj]) and close[jj] > 0:
                        xf = np.log(close[jj] / ak) / vk
                        st = int(np.floor(abs(xf)))
                        if st > cur_state:
                            next_state = st
                            time_to_next = jj - k
                            break
        row["time_to_rejection"] = time_to_rej
        row["time_to_next_state"] = time_to_next
        row["next_state_first"] = next_state
        rows.append(row)

    out = pd.concat([episodes.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    return out


# ---------------------------------------------------------------------------
# Static-leakage self-audit (AST-level; mirrors MVE_R05_2_STATIC_LEAKAGE_SUMMARY)
# ---------------------------------------------------------------------------

def executable_leakage_scan(source: str, module_name: str) -> list:
    """AST-level static-leakage scan: flags only executable operations.

    Detects the forbidden-operation family required by the causality
    regression contract:

        .shift(-N)            future shift
        center=True           centered window
        .bfill()/.backfill()  backfill of missing scientific state
        iloc[i+1]             positional future slice
        .rolling()/.mean()/.std()  informational: require classification
                                   (CAUSAL if trailing/expanding only,
                                    EX_POST_ONLY if in outcome measurement,
                                    BLOCKED otherwise)

    Findings are never auto-classified: every one is classified manually in
    the P4 causality audit (no unknowns allowed).
    """
    findings = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        # .shift(-N) — future shift
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "shift"
        ):
            for a in node.args:
                if isinstance(a, ast.UnaryOp) and isinstance(a.op, ast.USub):
                    findings.append(_finding(module_name, line, "shift(-", node))
        # center=True — centered window
        if (
            isinstance(node, ast.keyword)
            and node.arg == "center"
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        ):
            findings.append(_finding(module_name, line, "center=True", node))
        # .bfill() / .backfill() calls
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("bfill", "backfill")
        ):
            findings.append(_finding(module_name, line, node.func.attr + "()", node))
        # iloc[i+1]-style positional future slice: iloc subscript whose index
        # is an EXPRESSION (e.g. i+1), not a fixed constant row access.
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "iloc"
            and not isinstance(node.slice, ast.Constant)
            and not isinstance(node.slice, ast.Slice)
        ):
            findings.append(_finding(module_name, line, "iloc[]", node))
        # informational: rolling/mean/std calls need classification
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("rolling", "mean", "std")
        ):
            findings.append(_finding(module_name, line, node.func.attr + "()", node))
    return findings


def _finding(module_name: str, line, pattern: str, node) -> dict:
    return {
        "module": module_name,
        "line": line,
        "pattern": pattern,
        "code": ast.unparse(node)[:120],
        "classification": "NEEDS_CLASSIFICATION",
    }
