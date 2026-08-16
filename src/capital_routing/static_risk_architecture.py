"""
CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL — minimal static risk-policy.

Freezes the simplest portfolio-risk architecture justified by R1-R6 evidence:

    VALID ALPHA EVENTS
        -> FAMILY CLASSIFICATION
        -> STATIC FAMILY ALLOCATION
        -> SIMPLE GROSS SIMULTANEOUS-HEAT LIMIT
        -> PORTFOLIO

No dynamic drawdown rule, no episode memory budget, no Kelly, no hybrid
policy, no state machine for sizing.

The canonical heat primitive is H1_SIMPLE_GROSS_HEAT_CAP. Admission is strictly
CAUSAL: only information known at entry time (active positions that entered
earlier) decides ACCEPT_FULL / ACCEPT_SCALED / REJECT_HEAT_CAP.

This module MUST NOT:
  - calculate alpha
  - change entries or exits
  - perform broker execution
  - calculate Kelly
  - inspect future episode membership
  - adapt to drawdown
  - adapt to previous PnL

Family allocation and gross heat cap are CONFIGURATION, never optimized here.
The Block-II static architecture seal selects the ARCHITECTURE, not a
production capital level.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# Canonical heat mechanism (frozen by the Block-II intermediate seal).
CANONICAL_HEAT_MECHANISM = "H1_SIMPLE_GROSS_HEAT_CAP"

# Frozen research reference allocations (no universally optimal winner).
ALLOCATION_REFERENCES: Tuple[str, ...] = ("50/50", "70/30", "100/0 A")

# Allowed policy roles (frozen by the Block-II intermediate seal).
POLICY_ROLES: Dict[str, str] = {
    "H0": "KEEP_AS_UNCONSTRAINED_CONTROL",
    "H1": "ADOPT_AS_CANONICAL_SIMPLE_HEAT_MECHANISM",
    "H2": "PRUNE_FROM_DEFAULT_DIAGNOSTIC_ONLY",
    "H3": "SECONDARY_OPTIONAL",
    "H4": "PRUNED_REDUNDANT",
    "H5": "DEFERRED_COMPLEXITY",
}

# Valid admission decisions emitted by the static architecture.
DECISIONS = ("ACCEPT_FULL", "ACCEPT_SCALED", "REJECT_HEAT_CAP")

# Valid treatments for the gross heat cap.
TREATMENTS = ("REJECT", "SCALE")


@dataclass(frozen=True)
class FamilyAllocation:
    """Static family allocation expressed as configuration (not optimized)."""

    weights: Dict[str, float]

    def __post_init__(self) -> None:
        if set(self.weights.keys()) != {"A", "B"}:
            raise ValueError("family allocation must define weights for A and B")
        for k, v in self.weights.items():
            if v < 0.0:
                raise ValueError(f"family weight for {k} must be >= 0")
        s = self.weights["A"] + self.weights["B"]
        if not np.isclose(s, 1.0, atol=1e-9):
            raise ValueError("family weights must sum to 1.0")

    def weight(self, family: str) -> float:
        return self.weights[family]


@dataclass(frozen=True)
class StaticRiskConfig:
    """The full static architecture configuration.

    base_f               : total account heat for one unit of "f" (percent
                           units where 1.0 == 1% of account). Requested heat
                           per event = base_f * family_weight(family).
    gross_heat_cap_mult  : H1 gross-cap multiplier relative to base_f.
                           max active gross heat = base_f * gross_heat_cap_mult.
    treatment            : "REJECT" (reject when cap would breach) or
                           "SCALE" (scale new event down to remaining cap).
    """

    allocation: FamilyAllocation
    base_f: float = 1.0
    gross_heat_cap_mult: Optional[float] = None
    treatment: str = "REJECT"

    def __post_init__(self) -> None:
        if self.base_f <= 0.0:
            raise ValueError("base_f must be > 0")
        if self.gross_heat_cap_mult is not None and self.gross_heat_cap_mult <= 0.0:
            raise ValueError("gross_heat_cap_mult must be > 0")
        if self.treatment not in TREATMENTS:
            raise ValueError(f"treatment must be one of {TREATMENTS}")
        # H0 (unconstrained) has no cap; H1 has a cap.
        if self.gross_heat_cap_mult is None and self.treatment != "REJECT":
            raise ValueError("unconstrained config must use REJECT treatment")

    @property
    def policy_id(self) -> str:
        # Match the frozen R6 policy-id convention exactly (e.g. "H1-1.00-REJ").
        if self.gross_heat_cap_mult is None:
            return "H0"
        return f"H1-{self.gross_heat_cap_mult:.2f}-{self.treatment[:3].upper()}"

    def requested_heat(self, family: str) -> float:
        return self.base_f * self.allocation.weight(family)

    def gross_cap(self) -> Optional[float]:
        if self.gross_heat_cap_mult is None:
            return None
        return self.base_f * self.gross_heat_cap_mult


@dataclass
class AdmissionResult:
    """Deterministic causal admission output for one book sweep."""

    requested_f: np.ndarray
    admitted_f: np.ndarray
    decision: np.ndarray
    reason: np.ndarray
    pre_gross_heat: np.ndarray
    remaining_heat: np.ndarray
    n_accept_full: int = 0
    n_accept_scaled: int = 0
    n_rejected: int = 0
    max_gross_heat: float = 0.0
    config: StaticRiskConfig = field(default=None)  # type: ignore[assignment]


def _numeric_times(entry: Sequence, exit_: Sequence) -> Tuple[np.ndarray, np.ndarray]:
    """Convert entry/exit timestamps to numeric (ns) arrays for comparison."""
    ent = np.asarray(entry)
    ext = np.asarray(exit_)
    if ent.dtype.kind in ("O", "U", "M", "S") or ent.dtype.kind == "i":
        # strings / datetimes -> ns int64
        import pandas as pd
        ent = pd.to_datetime(ent, utc=True).to_numpy(dtype="int64")
        ext = pd.to_datetime(ext, utc=True).to_numpy(dtype="int64")
    return ent.astype("int64"), ext.astype("int64")


def admit_book(
    entry: Sequence,
    exit_: Sequence,
    family: Sequence,
    config: StaticRiskConfig,
    direction: Optional[Sequence] = None,
    *,
    entry_order: bool = True,
) -> AdmissionResult:
    """Causal admission over a chronological book of events.

    entry / exit_ : event entry / exit timestamps (str, datetime, or numeric).
    family        : "A" or "B" per event.
    direction     : optional +/-1.0 per event (reserved for diagnostics; the
                    canonical H1 gross cap does not depend on direction).
    entry_order   : if True, the book is assumed already sorted by entry time.

    Only information available at each event's entry time is used: active
    positions that entered strictly earlier. Future returns, future episode
    membership, and future drawdown are never inspected.

    Returns an AdmissionResult with per-event requested/admitted heat and
    ACCEPT_FULL / ACCEPT_SCALED / REJECT_HEAT_CAP decisions.
    """
    if entry_order:
        ent, ext = _numeric_times(entry, exit_)
        fam = np.asarray(family)
        idx = np.argsort(ent, kind="stable")
        ent, ext = ent[idx], ext[idx]
        fam = fam[idx]
        if direction is not None:
            direc = np.asarray(direction, dtype=float)[idx]
        else:
            direc = np.ones(len(ent), dtype=float)
    else:
        ent, ext = _numeric_times(entry, exit_)
        fam = np.asarray(family)
        direc = np.asarray(direction, dtype=float) if direction is not None else np.ones(len(ent))

    n = len(ent)
    if n != len(ext) or n != len(fam):
        raise ValueError("entry/exit/family must have equal length")

    base_f = config.base_f
    cap = config.gross_cap()  # None for H0
    treat = config.treatment

    requested = np.array([config.requested_heat(f) for f in fam], dtype=float)
    admitted = np.zeros(n, dtype=float)
    decisions = np.full(n, "ACCEPT_FULL", dtype=object)
    reasons = np.full(n, "", dtype=object)
    pre_gross = np.zeros(n, dtype=float)
    remaining = np.zeros(n, dtype=float)

    # Active positions as a FIFO queue keyed by exit time. All holds are a
    # fixed duration so exits ascend with entry order; pop expired at each
    # entry time.
    from collections import deque
    active: deque = deque()  # entries: (exit_t, admitted_f)
    gross = 0.0
    max_gross = 0.0
    n_full = n_scaled = n_rej = 0

    for i in range(n):
        t0 = float(ent[i])
        while active and active[0][0] <= t0:
            expired = active.popleft()[1]
            gross -= expired
        rem = (cap - gross) if cap is not None else requested[i]
        pre_gross[i] = gross
        remaining[i] = rem
        if cap is None:
            f_ = requested[i]
            decision = "ACCEPT_FULL"
            reason = ""
        elif rem >= requested[i] - 1e-15:
            f_ = requested[i]
            decision = "ACCEPT_FULL"
            reason = ""
        elif rem > 1e-15 and treat == "SCALE":
            f_ = rem
            decision = "ACCEPT_SCALED"
            reason = "gross_cap"
        else:
            f_ = 0.0
            decision = "REJECT_HEAT_CAP"
            reason = "gross_cap"
        admitted[i] = f_
        decisions[i] = decision
        reasons[i] = reason
        if decision == "ACCEPT_FULL":
            n_full += 1
        elif decision == "ACCEPT_SCALED":
            n_scaled += 1
        else:
            n_rej += 1
        if f_ > 0.0:
            active.append((float(ext[i]), f_))
            gross += f_
            max_gross = max(max_gross, gross)

    return AdmissionResult(
        requested_f=requested,
        admitted_f=admitted,
        decision=decisions,
        reason=reasons,
        pre_gross_heat=pre_gross,
        remaining_heat=remaining,
        n_accept_full=n_full,
        n_accept_scaled=n_scaled,
        n_rejected=n_rej,
        max_gross_heat=max_gross,
        config=config,
    )


def active_gross_heat(entry: Sequence, exit_: Sequence, admitted_f: Sequence) -> float:
    """Maximum concurrent admitted gross heat across the book (diagnostic)."""
    ent, ext = _numeric_times(entry, exit_)
    f = np.asarray(admitted_f, dtype=float)
    idx = np.argsort(ent, kind="stable")
    ent, ext, f = ent[idx], ext[idx], f[idx]
    from collections import deque
    active: deque = deque()
    gross = 0.0
    peak = 0.0
    for i in range(len(ent)):
        while active and active[0][0] <= float(ent[i]):
            gross -= active.popleft()[1]
        if f[i] > 0.0:
            active.append((float(ext[i]), f[i]))
            gross += f[i]
            peak = max(peak, gross)
    return peak


# Frozen reference configurations (parity targets; NOT production selections).
def reference_configs() -> Dict[str, StaticRiskConfig]:
    """The three frozen research allocations plus the canonical H1 reference."""
    half = FamilyAllocation({"A": 0.5, "B": 0.5})
    seventythirty = FamilyAllocation({"A": 0.7, "B": 0.3})
    a_only = FamilyAllocation({"A": 1.0, "B": 0.0})
    return {
        "H0_50_50": StaticRiskConfig(allocation=half, base_f=1.0),
        "H0_70_30": StaticRiskConfig(allocation=seventythirty, base_f=1.0),
        "H0_100_0_A": StaticRiskConfig(allocation=a_only, base_f=1.0),
        "H1_70_30_1x": StaticRiskConfig(
            allocation=seventythirty, base_f=1.0, gross_heat_cap_mult=1.0,
            treatment="REJECT"),
    }
