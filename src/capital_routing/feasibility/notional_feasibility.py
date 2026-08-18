"""
Pure notional-cap feasibility engine — CR-RISK-BLOCK-IV-D1.1 Lane A.

Given a sealed economic target (an EconomicTargetRef carrying the equity-
normalized target-notional multiple) and a HYPOTHETICAL_DIAGNOSTIC maximum
notional/equity limit L, classify the target as exactly representable or
notional-limit blocked:

    survives  iff  target_notional_multiple <= max_notional_multiple

This engine is BROKER-INDEPENDENT and NOTIONAL-ONLY: no instrument spec, no
lots, no margin, no currency conversion, no account size, no broker truth.
Classification is account-size invariant because account equity cancels out of
the multiple.

Purity contract (same as the D0.1 core): no filesystem state, no DB, no
network, no broker, no execution-runtime import, no random UUID, no
wall-clock use.  Every result is a pure function of its inputs.

The cap is a HYPOTHETICAL_DIAGNOSTIC max_notional_multiple — never labeled
actual account leverage, broker leverage, a production limit, or a
recommended leverage.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Optional

STUDY_VERSION = "D1.1"
GRID_GENERATION = "G1"
TRUTH_CLASS_HYPOTHETICAL = "HYPOTHETICAL_DIAGNOSTIC"
SCHEMA_VERSION = "cr-block4.d1.1.notional-feasibility.v1"

STATE_EXACTLY_REPRESENTABLE = "EXACTLY_REPRESENTABLE_NOTIONAL_ONLY"
STATE_NOTIONAL_LIMIT_BLOCKED = "NOTIONAL_LIMIT_BLOCKED"

ID_PREFIX = "NS-"


class FeasibilityContractError(Exception):
    """Base error for feasibility-contract violations (fail closed)."""


class InvalidNotionalCapError(FeasibilityContractError):
    """max_notional_multiple is not a finite positive number."""


class InvalidTargetNotionalError(FeasibilityContractError):
    """target_notional_multiple is not a finite positive number."""


class InvalidEconomicTargetError(FeasibilityContractError):
    """EconomicTargetRef fields violate the pure contract."""


class InvalidEquityError(FeasibilityContractError):
    """Equity is not a finite positive number."""


@dataclass(frozen=True)
class EconomicTargetRef:
    """Equity-normalized sealed economic target (D0.1 output, translated).

    target_notional_multiple == target_notional / equity (m_t).  Equity is
    deliberately absent: Lane A classification must be account-size invariant.
    """

    event_id: str
    translation_id: str
    family: str
    pos_t: float
    target_notional_multiple: float
    known_time: str


@dataclass(frozen=True)
class NotionalFeasibilityResult:
    """Result of assessing one economic target against one notional cap."""

    scenario_id: str
    event_id: str
    translation_id: str
    family: str
    pos_t: float
    target_notional_multiple: float
    max_notional_multiple: float
    truth_class: str
    primary_state: str
    survives: bool
    known_time: str


def _canonical_json(obj) -> str:
    """Deterministic canonical serialization: sorted keys, compact separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def scenario_id(
    *,
    study_version: str,
    grid_generation: str,
    economic_target_ledger_hash: str,
    max_notional_multiple: float,
    truth_class: str,
    translation_id: str,
) -> str:
    """Deterministic scenario identity binding study / ledger / cap / class / target.

    Canonical (schema-versioned, sorted-key) serialization before SHA-256, so
    no delimiter-collision ambiguity is possible.  No random UUID.
    """
    payload = {
        "schema": SCHEMA_VERSION,
        "study_version": study_version,
        "grid_generation": grid_generation,
        "economic_target_ledger_hash": economic_target_ledger_hash,
        "max_notional_multiple": max_notional_multiple,
        "truth_class": truth_class,
        "translation_id": translation_id,
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{ID_PREFIX}{digest}"


def assess_notional_cap(
    economic_target: EconomicTargetRef,
    max_notional_multiple: float,
    *,
    study_version: str = STUDY_VERSION,
    grid_generation: str = GRID_GENERATION,
    economic_target_ledger_hash: str,
    truth_class: str = TRUTH_CLASS_HYPOTHETICAL,
) -> NotionalFeasibilityResult:
    """Classify one economic target under one notional cap (pure, deterministic).

    Fail-closed validation:
      - cap: must be finite and > 0 (zero / negative / NaN / +/-inf rejected)
      - target multiple: finite and > 0
      - pos_t: finite and > 0
      - event_id / translation_id / known_time: non-empty

    survive  <=>  target_notional_multiple <= max_notional_multiple.
    """
    if not math.isfinite(max_notional_multiple):
        raise InvalidNotionalCapError(
            f"max_notional_multiple must be finite, got {max_notional_multiple!r}")
    if max_notional_multiple <= 0:
        raise InvalidNotionalCapError(
            f"max_notional_multiple must be > 0, got {max_notional_multiple!r}")

    if not math.isfinite(economic_target.target_notional_multiple):
        raise InvalidTargetNotionalError(
            f"target_notional_multiple must be finite, got "
            f"{economic_target.target_notional_multiple!r}")
    if economic_target.target_notional_multiple <= 0:
        raise InvalidTargetNotionalError(
            f"target_notional_multiple must be > 0, got "
            f"{economic_target.target_notional_multiple!r}")

    if not math.isfinite(economic_target.pos_t) or economic_target.pos_t <= 0:
        raise InvalidEconomicTargetError(
            f"pos_t must be finite and > 0, got {economic_target.pos_t!r}")
    if not economic_target.event_id or not economic_target.translation_id:
        raise InvalidEconomicTargetError("event_id / translation_id must be non-empty")
    if not economic_target.known_time:
        raise InvalidEconomicTargetError("known_time must be non-empty")

    survives = economic_target.target_notional_multiple <= max_notional_multiple
    state = (
        STATE_EXACTLY_REPRESENTABLE if survives else STATE_NOTIONAL_LIMIT_BLOCKED
    )
    sid = scenario_id(
        study_version=study_version,
        grid_generation=grid_generation,
        economic_target_ledger_hash=economic_target_ledger_hash,
        max_notional_multiple=max_notional_multiple,
        truth_class=truth_class,
        translation_id=economic_target.translation_id,
    )
    return NotionalFeasibilityResult(
        scenario_id=sid,
        event_id=economic_target.event_id,
        translation_id=economic_target.translation_id,
        family=economic_target.family,
        pos_t=economic_target.pos_t,
        target_notional_multiple=economic_target.target_notional_multiple,
        max_notional_multiple=max_notional_multiple,
        truth_class=truth_class,
        primary_state=state,
        survives=survives,
        known_time=economic_target.known_time,
    )


def notional_from_multiple(target_notional_multiple: float, equity: float) -> float:
    """Dollar notional from an equity-normalized multiple (equity-invariance helper).

    The multiple is the sealed scientific quantity; equity is a pure input
    parameter for the equality fixture.  N = m_t x E scales linearly; m_t and
    therefore Lane A classification are invariant.
    """
    if not math.isfinite(target_notional_multiple) or target_notional_multiple <= 0:
        raise InvalidTargetNotionalError(
            f"target_notional_multiple must be finite and > 0, got "
            f"{target_notional_multiple!r}")
    if not math.isfinite(equity) or equity <= 0:
        raise InvalidEquityError(f"equity must be finite and > 0, got {equity!r}")
    return target_notional_multiple * equity


def classify_multiple(target_notional_multiple: float, max_notional_multiple: float):
    """Small pure helper: (primary_state, survives) for a multiple/cap pair.

    Used by the equity-invariance fixture to prove classification is identical
    across account sizes.
    """
    if not math.isfinite(max_notional_multiple) or max_notional_multiple <= 0:
        raise InvalidNotionalCapError(
            f"max_notional_multiple must be finite and > 0, got "
            f"{max_notional_multiple!r}")
    if not math.isfinite(target_notional_multiple) or target_notional_multiple <= 0:
        raise InvalidTargetNotionalError(
            f"target_notional_multiple must be finite and > 0, got "
            f"{target_notional_multiple!r}")
    survives = target_notional_multiple <= max_notional_multiple
    state = STATE_EXACTLY_REPRESENTABLE if survives else STATE_NOTIONAL_LIMIT_BLOCKED
    return state, survives
