"""
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 — pure capital translation core.

PURPOSE
-------
Convert a SEALED CapitalDecision + AccountBinding + event pos_t into an
economic exposure target (the corrected R1 translation):

    one_R_budget_account_ccy    = equity_at_admission x admitted_f_pct / 100
    target_notional_account_ccy = equity x (admitted_f_pct/100) x pos_t
                                  x 10,000 / RISK_UNIT_BPS
    one_R_price_move_bps        = RISK_UNIT_BPS / pos_t        (event-specific)

The corrected formula is derived from the sealed PnL construction
(phase_r1_ledger.py): gross_pnl_bps = dir x pos_t x price_return_bps with
pos_t = TARGET_VOL / rv_t, and account_return = admitted_f_decimal x r_R.
Gross exposure parity was proven at machine precision over all 826 accepted
events in CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 (commit 00bef1b5).

BOUNDARY (this module MUST NOT, and provably does not):
  - recompute H1 / model admission / gross model heat   (upstream CapitalPolicy)
  - classify family                                     (upstream, sealed)
  - recompute requested_f / admitted_f                  (immutable inputs)
  - produce broker quantities / margin / buying power / order fields
  - track account state, revalue open events, or adapt to later equity
    (equity_at_admission is a FROZEN snapshot input; no dynamic resizing)
  - make broker calls or touch execution-runtime-foundation

FAIL-CLOSED
-----------
Rejected events (status != ACCEPT_FULL) translate to NO_EXPOSURE with zero
budget / zero notional / zero price move, WITHOUT independently reconsidering
H1. Invalid or unavailable inputs raise fail-closed TranslationError
subclasses (stale account state, unknown instrument spec, binding mismatch,
missing equity, unresolved account currency, invalid pos, invalid status).

IDEMPOTENCY
-----------
translate() is a pure deterministic function of its inputs. The same
(event_id, decision_id, policy_id, configuration_hash) always yields the same
EconomicExposureTarget; the translation_id (canonical hash) can be used as an
idempotency key so a duplicate event can never consume exposure twice.

SCIENCE (FROZEN, UNTOUCHED)
----------------------------
890 events (A 432 / B 458); A1_70_30 + H1-1.00-REJ: 826 ACCEPT_FULL
(A 371 / B 455), 64 REJECT_HEAT_CAP. 1R = 24.49489742783178 bps — a
NORMALIZED EXPECTED-MOVE UNIT, NOT a hard stop / max loss / broker stop.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Frozen science constants (sealed; DO NOT CHANGE)
# ---------------------------------------------------------------------------
RISK_UNIT_BPS = 24.49489742783178          # TARGET_VOL x sqrt(6h hold)
TARGET_VOL = 10.0                          # bps per hour normalized target vol
FAMILY_W: dict = {"A": 0.70, "B": 0.30}    # frozen family weights (percent)
F_TOTAL_PCT = 1.00                         # f_total = 1.00% (research default)
ONE_R_NOTIONAL_FACTOR = 1e4 / RISK_UNIT_BPS  # 408.2483... (x pos per event)
TRANSLATION_VERSION = "D0-1"
SCIENCE_VERSION = "R1.1"

# The sealed research universe. Anything else is UNKNOWN_INSTRUMENT_SPEC until
# a future research checkpoint extends it (would be new science).
KNOWN_RESEARCH_INSTRUMENTS = frozenset({"USDJPY"})

FAMILIES = ("A", "B")
DIRECTIONS = ("LONG", "SHORT")
DECISION_STATUSES = ("ACCEPT_FULL", "REJECT_HEAT_CAP")
STALENESS_STATUSES = ("FRESH", "STALE", "UNKNOWN")
ACCOUNT_ROLES = ("EXCLUSIVE_STRATEGY_MASTER", "PORTFOLIO_MASTER", "FOLLOWER")


# ---------------------------------------------------------------------------
# Fail-closed translation errors
# ---------------------------------------------------------------------------
class TranslationError(Exception):
    """Base class for fail-closed capital-translation failures."""


class InvalidDecisionStatusError(TranslationError):
    """CapitalDecision.status is not a sealed value."""


class UnknownInstrumentSpecError(TranslationError):
    """research_instrument is not in the sealed research universe."""


class StaleAccountStateError(TranslationError):
    """BoundAccountSnapshot is not FRESH; block rather than translate."""


class AccountBindingMismatchError(TranslationError):
    """snapshot.account_id differs from binding.account_id."""


class MissingAccountEquityError(TranslationError):
    """equity_at_admission is missing / non-positive; cannot size."""


class UnresolvedAccountCurrencyError(TranslationError):
    """executable account currency is unresolved; cannot size."""


class InvalidPositionError(TranslationError):
    """pos_t is missing / non-positive; cannot translate."""


# ---------------------------------------------------------------------------
# Frozen input contracts (mirror CR_EXEC_R1_1_CAPITAL_TRANSLATION_REQUEST_SCHEMA)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StrategyEventReference:
    """A_StrategyEventReference — event facts from the sealed strategy.

    family and direction are INPUT passthrough (classified UPSTREAM; this core
    never classifies). pos_t = TARGET_VOL / rv_t from the sealed ledger.
    """

    event_id: str
    strategy_id: str
    family: str
    direction: str
    instrument_research_identity: str
    entry_known_timestamp: str
    pos_t: float
    risk_unit_bps: float = RISK_UNIT_BPS
    translation_science_version: str = SCIENCE_VERSION


@dataclass(frozen=True)
class CapitalDecisionReference:
    """B_CapitalDecisionReference — IMMUTABLE upstream audit truth from the
    Capital Router / CapitalPolicy authority. This core consumes these values
    and never recomputes H1, family, or model heat."""

    decision_id: str
    policy_id: str
    requested_f_pct: float
    admitted_f_pct: float
    status: str
    model_heat_before: float
    model_heat_after: float
    decision_timestamp: str
    configuration_hash: str


@dataclass(frozen=True)
class AccountBindingReference:
    """C_AccountBindingReference — from the Account Control Plane. No equity
    here; equity comes only from the BoundAccountSnapshot."""

    account_id: str
    portfolio_group_id: str
    account_role: str


@dataclass(frozen=True)
class BoundAccountSnapshot:
    """D_BoundAccountSnapshot — current equity at CAUSAL admission. FROZEN per
    event: an opened event is never revalued because equity changes later."""

    account_id: str
    account_currency: str
    equity_at_admission: float
    observed_at: str
    staleness_status: str
    profile_config_hash: str


# ---------------------------------------------------------------------------
# Output contract (mirror CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EconomicExposureTarget:
    """Pure economic exposure target. NO broker fields (no lots, margin,
    buying power, order type, fill mode, slippage, broker symbol)."""

    event_id: str
    account_id: str
    strategy_id: str
    family: str
    direction: str
    research_instrument: str
    admitted_f_pct: float
    pos_t: float
    risk_unit_bps: float
    equity_reference: float
    account_currency: str
    one_R_budget_account_ccy: float
    target_notional_account_ccy: float
    one_R_price_move_bps: float
    capital_policy_id: str
    translation_version: str
    known_time: str
    status: str                      # ECONOMIC_TARGET | NO_EXPOSURE
    translation_id: str              # idempotency key (canonical hash)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def one_R_price_move_bps(pos_t: float, risk_unit_bps: float = RISK_UNIT_BPS) -> float:
    """Underlying gross price move associated with +1R (event-specific):
    1R PnL = pos_t x price_move_bps  =>  price_move_bps = RISK / pos_t."""
    if not pos_t or pos_t <= 0:
        raise InvalidPositionError(f"pos_t must be > 0 (got {pos_t!r})")
    return risk_unit_bps / pos_t


def target_notional(
    equity: float,
    admitted_f_pct: float,
    pos_t: float,
    risk_unit_bps: float = RISK_UNIT_BPS,
) -> float:
    """Corrected R1 formula: N = E x (f/100) x pos_t x 1e4 / RISK."""
    if not equity or equity <= 0:
        raise MissingAccountEquityError(f"equity must be > 0 (got {equity!r})")
    if admitted_f_pct < 0:
        raise TranslationError(f"admitted_f_pct must be >= 0 (got {admitted_f_pct!r})")
    if not pos_t or pos_t <= 0:
        raise InvalidPositionError(f"pos_t must be > 0 (got {pos_t!r})")
    if risk_unit_bps <= 0:
        raise TranslationError(f"risk_unit_bps must be > 0 (got {risk_unit_bps!r})")
    return equity * (admitted_f_pct / 100.0) * pos_t * ONE_R_NOTIONAL_FACTOR


def one_R_budget(equity: float, admitted_f_pct: float) -> float:
    """one_R_budget_account_ccy = equity x admitted_f_pct / 100."""
    if not equity or equity <= 0:
        raise MissingAccountEquityError(f"equity must be > 0 (got {equity!r})")
    if admitted_f_pct < 0:
        raise TranslationError(f"admitted_f_pct must be >= 0 (got {admitted_f_pct!r})")
    return equity * (admitted_f_pct / 100.0)


def _translation_id(event: StrategyEventReference, decision: CapitalDecisionReference) -> str:
    payload = "|".join([
        event.event_id, decision.decision_id, decision.policy_id,
        decision.configuration_hash, TRANSLATION_VERSION,
    ])
    return "TR-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# The pure translate() — the entire D0 core
# ---------------------------------------------------------------------------
def translate(
    event: StrategyEventReference,
    decision: CapitalDecisionReference,
    binding: AccountBindingReference,
    snapshot: BoundAccountSnapshot,
) -> EconomicExposureTarget:
    """Translate one sealed capital decision into an economic exposure target.

    Pure and deterministic: identical inputs -> identical output. Rejected
    events -> NO_EXPOSURE with zero budget / zero notional / zero price move,
    WITHOUT reconsidering H1. All failures are fail-closed TranslationErrors.
    """
    # -- validation (fail closed) ------------------------------------------
    if event.family not in FAMILIES:
        raise InvalidDecisionStatusError(f"unknown family {event.family!r}")
    if event.direction not in DIRECTIONS:
        raise InvalidDecisionStatusError(f"unknown direction {event.direction!r}")
    if event.instrument_research_identity not in KNOWN_RESEARCH_INSTRUMENTS:
        raise UnknownInstrumentSpecError(
            f"instrument {event.instrument_research_identity!r} is not in the "
            f"sealed research universe {sorted(KNOWN_RESEARCH_INSTRUMENTS)}")
    if decision.status not in DECISION_STATUSES:
        raise InvalidDecisionStatusError(f"unknown decision status {decision.status!r}")
    if binding.account_role not in ACCOUNT_ROLES:
        raise InvalidDecisionStatusError(f"unknown account role {binding.account_role!r}")
    if snapshot.account_id != binding.account_id:
        raise AccountBindingMismatchError(
            f"snapshot account {snapshot.account_id!r} != binding account "
            f"{binding.account_id!r}")
    if snapshot.staleness_status != "FRESH":
        raise StaleAccountStateError(
            f"account snapshot staleness = {snapshot.staleness_status!r}; "
            f"require FRESH before sizing")
    if not snapshot.account_currency or not str(snapshot.account_currency).strip():
        raise UnresolvedAccountCurrencyError(
            "executable account currency is unresolved; cannot size")
    if not snapshot.equity_at_admission or snapshot.equity_at_admission <= 0:
        raise MissingAccountEquityError(
            f"equity_at_admission must be > 0 (got {snapshot.equity_at_admission!r})")
    if not event.pos_t or event.pos_t <= 0:
        raise InvalidPositionError(f"pos_t must be > 0 (got {event.pos_t!r})")
    if event.risk_unit_bps <= 0:
        raise TranslationError(f"risk_unit_bps must be > 0 (got {event.risk_unit_bps!r})")

    tid = _translation_id(event, decision)

    # -- rejected events: NO_EXPOSURE (zero everything, no H1 reconsideration)
    if decision.status != "ACCEPT_FULL":
        return EconomicExposureTarget(
            event_id=event.event_id, account_id=binding.account_id,
            strategy_id=event.strategy_id, family=event.family,
            direction=event.direction, research_instrument=event.instrument_research_identity,
            admitted_f_pct=0.0, pos_t=event.pos_t, risk_unit_bps=event.risk_unit_bps,
            equity_reference=snapshot.equity_at_admission,
            account_currency=snapshot.account_currency,
            one_R_budget_account_ccy=0.0, target_notional_account_ccy=0.0,
            one_R_price_move_bps=0.0, capital_policy_id=decision.policy_id,
            translation_version=TRANSLATION_VERSION,
            known_time=decision.decision_timestamp,
            status="NO_EXPOSURE", translation_id=tid)

    # -- accepted events: corrected economic exposure -----------------------
    budget = one_R_budget(snapshot.equity_at_admission, decision.admitted_f_pct)
    notional = target_notional(snapshot.equity_at_admission,
                               decision.admitted_f_pct, event.pos_t,
                               event.risk_unit_bps)
    move_bps = one_R_price_move_bps(event.pos_t, event.risk_unit_bps)

    return EconomicExposureTarget(
        event_id=event.event_id, account_id=binding.account_id,
        strategy_id=event.strategy_id, family=event.family,
        direction=event.direction, research_instrument=event.instrument_research_identity,
        admitted_f_pct=decision.admitted_f_pct, pos_t=event.pos_t,
        risk_unit_bps=event.risk_unit_bps,
        equity_reference=snapshot.equity_at_admission,
        account_currency=snapshot.account_currency,
        one_R_budget_account_ccy=budget,
        target_notional_account_ccy=notional,
        one_R_price_move_bps=move_bps,
        capital_policy_id=decision.policy_id,
        translation_version=TRANSLATION_VERSION,
        known_time=decision.decision_timestamp,
        status="ECONOMIC_TARGET", translation_id=tid)
