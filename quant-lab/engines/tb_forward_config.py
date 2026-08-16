"""
TB-FORWARD CONFIG LOCK — primary / control strategy separation
================================================================

Frozen forward-contract configuration for the TB deployment translation.

This module is the SINGLE source of truth for the forward strategy config
derived from the sealed P5/P6/P7 research (R0 truth lock). It does NOT
contain any strategy math — the math lives in the canonical research engine
(verify_tb_04a / tb_p5_validate / tb_p6_anatomy / tb_p7_convergence).

It exists so the live wrapper NEVER mutates one global config back and forth
between the primary candidate and the legacy control. The two models are
explicit, separately-stateful, and the control is shadow-only.

SCIENTIFIC INVARIANTS (must not change):
    basis formula, rolling-z (lookback 200, ddof=0, previous-bars-only),
    direction convention, TB-B weighting definition, z=6.0 stop semantics,
    session semantics (London 3-12 EST, fixed UTC-5, no DST), hard-exit
    semantics, re-entry semantics, cost assumptions.

The ONLY config transition authorized here is the sealed P6/P7 deployment
translation:
    CONTROL 2.5 / exit 0.0  ->  PRIMARY 3.0 / signed +-0.25 overshoot exit.
"""

from __future__ import annotations

from dataclasses import dataclass


# ─── SHARED FROZEN RESEARCH CONSTANTS ────────────────────────────────────
# These mirror the sealed tb_p5_validate frozen config and MUST NOT drift.

LOOKBACK = 200
STOP_Z = 6.0
LONDON_START_H_EST = 3
LONDON_END_H_EST = 12
HARD_EXIT_H_EST = 12
MIN_MINUTES_TO_EXIT = 120
ATR_PERIOD = 20
MAX_TOTAL_LEVERAGE = 3.0
EXPECTED_COST_PIPS = 10.2

# Fixed canonical research time semantics (no DST correction, ever).
CANONICAL_RESEARCH_TIME_SEMANTICS = "FIXED_UTC_MINUS_5"


@dataclass(frozen=True)
class StrategyModelConfig:
    """Frozen forward configuration for ONE strategy model.

    Exit thresholds are SIGNED per direction (never a single symmetric
    constant): a SHORT trade exits when the rolling z reaches short_exit_z
    or below; a LONG trade exits when z reaches long_exit_z or above.
    The stop is symmetric magnitude (stop_z).
    """
    strategy_id: str
    model_id: str
    entry_z: float          # strict: |z| > entry_z
    short_exit_z: float     # SHORT exits when z <= short_exit_z
    long_exit_z: float      # LONG exits when z >= long_exit_z
    stop_z: float           # SHORT stops at z >= +stop_z; LONG at z <= -stop_z
    shadow_only: bool
    execution_allowed: bool


# ─── PRIMARY: TB-FWD-V1 (sealed P6 entry 3.0 + P7 exit overshoot -0.25) ──
PRIMARY_CONFIG = StrategyModelConfig(
    strategy_id="TB-FWD-V1",
    model_id="TB-B",
    entry_z=3.0,
    short_exit_z=-0.25,
    long_exit_z=+0.25,
    stop_z=STOP_Z,
    shadow_only=False,          # intended for future execution, NOT this checkpoint
    execution_allowed=False,    # execution_authorization = NOT_AUTHORIZED
)

# ─── CONTROL: TB-FROZEN-CONTROL (legacy 2.5 / exit 0) — SHADOW ONLY ──────
CONTROL_CONFIG = StrategyModelConfig(
    strategy_id="TB-FROZEN-CONTROL",
    model_id="TB-B",
    entry_z=2.5,
    short_exit_z=0.0,
    long_exit_z=0.0,
    stop_z=STOP_Z,
    shadow_only=True,
    execution_allowed=False,    # control must NEVER execute
)


def build_config(strategy_id: str = None, model_config: StrategyModelConfig = None):
    """Resolve a StrategyModelConfig for a given strategy_id.

    Recognized strategy ids are the PRIMARY and CONTROL ids. Anything else
    (including legacy "trade"/"live" style ids) fails closed to the CONTROL
    (shadow-only, non-executing) so an unknown id can never enable execution.
    """
    if model_config is not None:
        return model_config
    if strategy_id in (None, CONTROL_CONFIG.strategy_id):
        return CONTROL_CONFIG
    if strategy_id == PRIMARY_CONFIG.strategy_id:
        return PRIMARY_CONFIG
    return CONTROL_CONFIG
