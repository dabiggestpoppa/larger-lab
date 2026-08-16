"""Causality / leakage harness for MVE infrastructure (R0.5.8).

This module provides the test infrastructure that proves every reusable MVE
component obeys:

    output at time t = f(information available at or before t)

It contains NO scientific logic. It provides:

- component timing classifications (CAUSAL_REALTIME / CAUSAL_DELAYED_CONFIRMATION /
  EX_POST_ONLY / CAUSAL_VIOLATION),
- the pivot knowledge-delay convention (event time vs known time),
- generic future-perturbation and truncation-invariance checkers,
- acceptance/rekey causal-schema validators,
- event-dedup identity helpers.

A component that requires future confirmation must expose that delay
explicitly. Anything that backdates (places a value at t using bars after t)
is a CAUSAL_VIOLATION and is recorded as a blocker, never silently repaired.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd


class CausalityError(Exception):
    """Raised when a causality contract is violated (fail-closed)."""


# ---------------------------------------------------------------------------
# Timing classifications
# ---------------------------------------------------------------------------

CAUSAL_REALTIME = "CAUSAL_REALTIME"
CAUSAL_DELAYED_CONFIRMATION = "CAUSAL_DELAYED_CONFIRMATION"
EX_POST_ONLY = "EX_POST_ONLY"
CAUSAL_VIOLATION = "CAUSAL_VIOLATION"
BLOCKED = "BLOCKED_SCIENTIFIC_IMPLEMENTATION"


# ---------------------------------------------------------------------------
# Pivot knowledge-delay convention
# ---------------------------------------------------------------------------

def pivot_delay(window: int) -> int:
    """A pivot at bar i is confirmed by the right side only at bar i+window,
    so its value is knowable only from bar i+window onward."""
    if window < 1:
        raise CausalityError(f"pivot window must be >= 1, got {window}")
    return window


def apply_anchor_delay(anchors: pd.Series, delay: int) -> pd.Series:
    """Return a causally-usable anchor series: the value at t is the most
    recent anchor whose event time + delay <= t (forward-filled, so no value
    is ever consumed before it is knowable). NaN in the first `delay` rows."""
    if delay < 0:
        raise CausalityError(f"delay must be >= 0, got {delay}")
    return anchors.shift(delay).ffill()


# ---------------------------------------------------------------------------
# Future-perturbation and truncation checkers
# ---------------------------------------------------------------------------

def future_perturbation_check(
    fn: Callable[[pd.DataFrame], pd.Series],
    data: pd.DataFrame,
    t_pos: int,
    seed: int,
    delay: int = 0,
    tol: float = 1e-9,
    signed: bool = True,
) -> float:
    """Compute fn on full data, radically alter all rows after position t_pos,
    recompute, and return the max absolute difference over rows whose KNOWLEDGE
    time <= t (positions 0..t_pos-delay). A causal component returns 0.0.

    Perturbation is deliberately brutal: per-row multiplicative factors in
    exp(U(-6, 6)) (0.0025x .. 403x). With signed=True (default) half the tail
    rows also flip sign (inverted directional paths). signed=False keeps all
    prices positive - used only for blocked scientific stubs whose int()
    conversions crash on NaN/negative inputs (the crash itself is recorded).
    """
    if t_pos >= len(data) - 1:
        raise CausalityError(f"t_pos={t_pos} leaves no future bars to perturb")
    base = fn(data)

    rng = np.random.default_rng(seed)
    n_tail = len(data) - t_pos - 1
    factors = np.exp(rng.uniform(-6.0, 6.0, size=n_tail))
    signs = np.where(rng.random(n_tail) < 0.5, -1.0, 1.0) if signed else np.ones(n_tail)

    pert = data.copy()
    for col in pert.columns:
        if not np.issubdtype(pert[col].dtype, np.number):
            continue
        values = pert[col].to_numpy(copy=True)
        values[t_pos + 1:] = values[t_pos + 1:] * factors * signs
        pert[col] = values

    alt = fn(pert)

    end = t_pos - delay + 1
    if end <= 0:
        return 0.0
    idx = data.index[:end]
    a = base.loc[idx]
    b = alt.loc[idx]
    mask = a.notna() & b.notna()
    if not mask.any():
        return 0.0
    return float((a[mask] - b[mask]).abs().max())


def truncation_check(
    fn: Callable[[pd.DataFrame], pd.Series],
    data: pd.DataFrame,
    t_pos: int,
    delay: int = 0,
    tol: float = 1e-9,
) -> float:
    """Run fn on (A) full history and (B) history truncated at position t_pos.
    Compare all values with knowledge time <= t (positions 0..t_pos-delay).
    Causal components return 0.0."""
    full = fn(data)
    truncated = fn(data.iloc[: t_pos + 1])

    end = t_pos - delay + 1
    if end <= 0:
        return 0.0
    idx = data.index[:end]
    a = full.loc[idx]
    b = truncated.loc[idx]
    mask = a.notna() & b.notna()
    if not mask.any():
        return 0.0
    return float((a[mask] - b[mask]).abs().max())


# ---------------------------------------------------------------------------
# Acceptance / rekey causal-schema validators
# ---------------------------------------------------------------------------

ACCEPTANCE_SCHEMA_FIELDS = (
    "state_event_time",
    "evidence_complete_time",
    "acceptance_known_time",
)

# R0.5.1 field set (supersedes the R0.5-gate field names
# original_state_time/acceptance_known_time/rekey_trigger_time):
# rekey_event_time <= rekey_evidence_complete_time <= rekey_known_time
# <= new_anchor_active_time.
REKEY_SCHEMA_FIELDS = (
    "rekey_event_time",
    "rekey_evidence_complete_time",
    "rekey_known_time",
    "new_anchor_active_time",
)


def validate_acceptance_events(
    events: Sequence[Dict], raise_on_error: bool = True
) -> List[str]:
    """Validate acceptance events against the frozen causal schema.

    Rule: state_event_time <= evidence_complete_time <= acceptance_known_time.
    An acceptance event is consumable only at acceptance_known_time.
    """
    problems: List[str] = []
    for ev in events:
        for field in ACCEPTANCE_SCHEMA_FIELDS:
            if field not in ev:
                problems.append(
                    f"acceptance event {ev.get('id', '?')}: missing {field}"
                )
        if all(f in ev for f in ACCEPTANCE_SCHEMA_FIELDS):
            if not (
                ev["state_event_time"]
                <= ev["evidence_complete_time"]
                <= ev["acceptance_known_time"]
            ):
                problems.append(
                    f"acceptance event {ev.get('id', '?')}: timestamp ordering "
                    "violated (state <= evidence <= known required)"
                )
    if problems and raise_on_error:
        raise CausalityError("; ".join(problems))
    return problems


def validate_rekey_events(
    rekeys: Sequence[Dict], raise_on_error: bool = True
) -> List[str]:
    """Validate rekey events against the frozen causal schema (R0.5.1 field set).

    Rule: rekey_event_time <= rekey_evidence_complete_time <= rekey_known_time
    <= new_anchor_active_time. Changing future data must never move a
    historical rekey earlier.
    """
    problems: List[str] = []
    for ev in rekeys:
        for field in REKEY_SCHEMA_FIELDS:
            if field not in ev:
                problems.append(f"rekey event {ev.get('id', '?')}: missing {field}")
        if all(f in ev for f in REKEY_SCHEMA_FIELDS):
            ordered = (
                ev["rekey_event_time"]
                <= ev["rekey_evidence_complete_time"]
                <= ev["rekey_known_time"]
                <= ev["new_anchor_active_time"]
            )
            if not ordered:
                problems.append(
                    f"rekey event {ev.get('id', '?')}: timestamp ordering "
                    "violated (event <= evidence <= known <= active required)"
                )
    if problems and raise_on_error:
        raise CausalityError("; ".join(problems))
    return problems


# ---------------------------------------------------------------------------
# Standard scientific-event schema (R0.5.1-I)
# ---------------------------------------------------------------------------

SCIENTIFIC_EVENT_SCHEMA_FIELDS = (
    "event_time",
    "evidence_complete_time",
    "known_time",
    "action_time",
)


def validate_scientific_event_times(
    events: Sequence[Dict], raise_on_error: bool = True
) -> List[str]:
    """Validate events against the standard scientific-event schema.

    Rule: event_time <= evidence_complete_time <= known_time <= action_time.
    Not every event needs all delays: for immediate causal events all four may
    be the same bar (as allowed by bar-close convention); for delayed
    confirmation, known_time must be later than event_time. action_time may
    equal known_time (e.g. close-known, next-open execution).
    """
    problems: List[str] = []
    for ev in events:
        for field in SCIENTIFIC_EVENT_SCHEMA_FIELDS:
            if field not in ev:
                problems.append(f"event {ev.get('id', '?')}: missing {field}")
        if all(f in ev for f in SCIENTIFIC_EVENT_SCHEMA_FIELDS):
            ordered = (
                ev["event_time"]
                <= ev["evidence_complete_time"]
                <= ev["known_time"]
                <= ev["action_time"]
            )
            if not ordered:
                problems.append(
                    f"event {ev.get('id', '?')}: ordering violated "
                    "(event <= evidence <= known <= action required)"
                )
    if problems and raise_on_error:
        raise CausalityError("; ".join(problems))
    return problems


# ---------------------------------------------------------------------------
# Event-dedup helpers
# ---------------------------------------------------------------------------

def event_identity(events: Sequence[Dict], identity_fields: Sequence[str]) -> set:
    """Project each event onto its frozen identity fields (asset, anchor id,
    direction, sigma level, first touch time, acceptance instance)."""
    return {
        tuple(str(ev.get(f, "<missing>")) for f in identity_fields)
        for ev in events
    }


def assert_unique_events(
    events: Sequence[Dict], identity_fields: Sequence[str], raise_on_error: bool = True
) -> List[str]:
    """One bar must not silently generate duplicate identical state events.
    Repeated occupancy may update state, but must not create a duplicate
    initial-state event unless the prior event is formally reset."""
    seen = {}
    problems: List[str] = []
    for ev in events:
        key = tuple(str(ev.get(f, "<missing>")) for f in identity_fields)
        if key in seen:
            problems.append(
                f"duplicate event identity {key} (first at {seen[key]}, "
                f"again at {ev.get('state_event_time', '?')})"
            )
        else:
            seen[key] = ev.get("state_event_time", "?")
    if problems and raise_on_error:
        raise CausalityError("; ".join(problems))
    return problems
