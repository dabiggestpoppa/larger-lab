"""Portfolio layer — cluster FSM, gross cap, reversal fade, drawdown
overlay, per-leg stop.

A1.F15.CLUSTER_FSM / F16.GROSS_CAP / F17.FADE / F18.DRAWDOWN / F19.LEG_STOP

The drawdown and leg-stop overlays require NAV/equity and are therefore
implemented as pure state machines exercised ONLY on synthetic fixtures
in pre-economic mode. They are never run against real market data here.
"""

from __future__ import annotations

import numpy as np

NEUTRAL_THRESHOLD = 0.05
W3_CLUSTER_SCALE = 0.5
GROSS_CAP = 1.0
FADE_HOUR1_RETAIN = 0.67
DD_ZONE1 = 0.12
DD_ZONE2 = 0.18
DD_ZONE3 = 0.195
DD_SCALE_WINDOW = 0.06
DD_REFLECTOR = -0.50
LEG_STOP_WINDOW = 6
LEG_STOP_TRIGGER = -0.02
LEG_STOP_BAN = 12


def cluster_fsm(w_total: np.ndarray, w1: np.ndarray, w2: np.ndarray, w3: np.ndarray) -> dict:
    """FSM state per slot and W_base cluster target.

    neutral: |w_total| < 0.05 -> W_base = [0,0,0]
    long:    w_total >= +0.05
    short:   w_total <= -0.05
    active:  W_base = [w_total*w1, w_total*w2, w_total*0.5*w3]
    """
    n = len(w_total)
    states = np.array(["NEUTRAL"] * n, dtype=object)
    w_base = np.zeros((n, 3))
    for t in range(n):
        wt = w_total[t]
        if not np.isfinite(wt):
            states[t] = "NEUTRAL"  # fail closed
            continue
        if abs(wt) < NEUTRAL_THRESHOLD:
            states[t] = "NEUTRAL"
            continue
        states[t] = "LONG" if wt >= NEUTRAL_THRESHOLD else "SHORT"
        w_base[t] = [wt * w1[t], wt * w2[t], wt * W3_CLUSTER_SCALE * w3[t]]
    return {"state": states, "w_base": w_base}


def gross_cap(w_base: np.ndarray) -> np.ndarray:
    """g = sum(abs(W_base)); if g > 1: W_cap = W_base/g else W_cap = W_base."""
    g = np.abs(w_base).sum(axis=1)
    out = w_base.copy()
    scale = np.where(g > GROSS_CAP, 1.0 / np.where(g > 0, g, 1.0), 1.0)
    return out * scale[:, None]


def fade_sequence(w_cap: np.ndarray, leg_count: int = 3) -> dict:
    """Reversal fade over the full sequence.

    - Sign reversal (old and new cluster targets both nonzero, opposite
      signs): hour1 keeps 67% of old exposure, hour2 exactly flat,
      hour3 ramps to the new target (100%).
    - Neutralization (old nonzero -> new zero): fade to zero (67% then
      flat), then stop.
    - Entry (old zero -> new nonzero): no fade, target applies directly.
    - Re-flip during a fade: restart from the current exposure toward
      the newest target.
    """
    n = len(w_cap)
    w_fade = np.zeros((n, leg_count))
    phase = np.array([0] * n)
    reasons = np.array([""] * n, dtype=object)
    current = np.zeros(leg_count)
    fade_phase = 0          # 0 = none, 1, 2, 3
    fade_target = np.zeros(leg_count)
    for t in range(n):
        target = w_cap[t]
        old_current = current.copy()
        target_zero = np.all(np.abs(target) < 1e-15)
        current_zero = np.all(np.abs(current) < 1e-15)
        sign_flip = np.any(np.sign(target) != np.sign(current))
        if fade_phase == 0:
            if (sign_flip and not target_zero and not current_zero) or (target_zero and not current_zero):
                # reversal (both nonzero) or neutralization (nonzero -> zero)
                fade_target = target.copy()
                fade_phase = 1
        else:
            if target_zero:
                fade_target = np.zeros(leg_count)  # continue fading to zero
            elif np.any(np.sign(target) != np.sign(fade_target)) and not target_zero:
                # re-flip: restart from current exposure toward newest target
                fade_target = target.copy()
                fade_phase = 1
            else:
                fade_target = target.copy()
        if fade_phase == 1:
            current = FADE_HOUR1_RETAIN * old_current
            phase[t] = 1
            fade_phase = 2
            reasons[t] = "FADE_HOUR1"
        elif fade_phase == 2:
            current = np.zeros(leg_count)
            phase[t] = 2
            if np.all(np.abs(fade_target) < 1e-15):
                fade_phase = 0  # faded to zero and stopped
                reasons[t] = "FADE_TO_ZERO_STOP"
            else:
                fade_phase = 3
                reasons[t] = "FADE_HOUR2_FLAT"
        elif fade_phase == 3:
            current = fade_target.copy()  # linear ramp complete (100%)
            phase[t] = 3
            fade_phase = 0
            reasons[t] = "FADE_HOUR3_RAMP"
        else:
            current = target.copy()
            reasons[t] = "NO_FADE"
        w_fade[t] = current
    return {"w_fade": w_fade, "phase": phase, "reason": reasons}


def drawdown_overlay(w_fade: np.ndarray, nav: np.ndarray) -> dict:
    """Drawdown weight overlay. Pure fixture function (requires NAV).

    DD = 1 - NAV/max(NAV). Zones per A1.F18. Terminal at DD >= 0.195.
    """
    n = len(nav)
    dd = np.zeros(n)
    scaled = w_fade.copy()
    terminal = np.zeros(n, dtype=bool)
    running_max = -np.inf
    latched = False
    for t in range(n):
        if np.isfinite(nav[t]):
            running_max = max(running_max, nav[t])
            dd[t] = 1.0 - nav[t] / running_max if running_max > 0 else 0.0
        # The 19.5% circuit breaker is TERMINAL: it latches and never
        # auto-restarts, even if a (synthetic) NAV later recovers.
        if dd[t] >= DD_ZONE3:
            latched = True
        if latched:
            scaled[t] = 0.0
            terminal[t] = True
        elif dd[t] >= DD_ZONE2:
            scaled[t] = DD_REFLECTOR * w_fade[t]
        elif dd[t] >= DD_ZONE1:
            scale = 1.0 - (dd[t] - DD_ZONE1) / DD_SCALE_WINDOW
            scaled[t] = w_fade[t] * scale
        # else: full scale
    return {"w_dd": scaled, "dd": dd, "terminal": terminal, "terminal_latched": latched}


def leg_stop(marked_leg_equity: np.ndarray, nav: np.ndarray,
             w_final_in: np.ndarray | None = None) -> dict:
    """Per-leg stop state machine. Pure fixture function (requires equity).

    Trigger: (LE_t - LE_{t-6}) / NAV_t < -0.02 -> leg target 0 and a
    12-completed-H1-bar execution ban. The leg stays in signal
    calculations during the ban.
    """
    n = len(nav)
    legs = marked_leg_equity.shape[1] if marked_leg_equity.ndim > 1 else 1
    banned_until = np.zeros(legs, dtype=int)
    target = np.ones((n, legs))
    trigger_hits = np.zeros((n, legs), dtype=bool)
    for t in range(n):
        for leg in range(legs):
            le = marked_leg_equity[t, leg]
            nav_t = nav[t]
            if t >= LEG_STOP_WINDOW and np.isfinite(le) and np.isfinite(nav_t) and nav_t != 0:
                le_prev = marked_leg_equity[t - LEG_STOP_WINDOW, leg]
                if np.isfinite(le_prev) and (le - le_prev) / nav_t < LEG_STOP_TRIGGER:
                    banned_until[leg] = t + LEG_STOP_BAN
                    trigger_hits[t, leg] = True
            target[t, leg] = 0.0 if t < banned_until[leg] else 1.0
    return {"target": target, "trigger_hits": trigger_hits, "banned_until": banned_until}
