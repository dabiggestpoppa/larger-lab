"""
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1 — pure capital translation core
(contract / idempotency truth repair over D0).

PURPOSE
-------
Convert a SEALED CapitalDecision + AccountBinding + event pos_t into an
economic exposure target (the corrected R1 translation):

    one_R_budget_account_ccy    = equity_at_admission x admitted_f_pct / 100
    target_notional_account_ccy = equity x (admitted_f_pct/100) x pos_t
                                  x 10,000 / risk_unit_bps
    one_R_price_move_bps        = risk_unit_bps / pos_t   (event-specific)

The corrected formula is derived from the sealed PnL construction
(phase_r1_ledger.py): gross_pnl_bps = dir x pos_t x price_return_bps with
pos_t = TARGET_VOL / rv_t, and account_return = admitted_f_decimal x r_R.
Gross exposure parity was proven at machine precision over all 826 accepted
events in CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 (00bef1b5) and
re-proven through the D0 core (18bd63aa).

D0.1 REPAIRS (this checkpoint, base 18bd63aa)
---------------------------------------------
1. RISK UNIT ARGUMENT IS USED: target_notional() arithmetic uses the explicit
   risk_unit_bps argument (1e4 / risk_unit_bps), never a silent module
   constant. ONE_R_NOTIONAL_FACTOR remains ONLY a frozen reference constant
   (diagnostic; not used in arithmetic). translate() additionally ENFORCES
   the frozen strategy-science risk unit (24.49489742783178) at the boundary
   -> RiskUnitMismatchError for any other value / unsupported science version.
2. ACCOUNT / SNAPSHOT-BOUND translation_id: canonical serialization
   (schema-versioned, sorted-key JSON, UTF-8, SHA-256) over event, decision,
   policy/config, account binding (account_id, portfolio_group_id, role),
   the deterministic account_snapshot_id, translation version and science
   version. Same event+decision on a different account / profile / frozen
   equity snapshot -> different economic target -> different translation_id.
3. PORTFOLIO_MASTER INVARIANT: the canonical A+B book (A1_70_30 + H1) was
   validated as ONE shared portfolio capital authority. For science R1.1 the
   core REQUIRES account_role == PORTFOLIO_MASTER and a non-empty
   portfolio_group_id. EXCLUSIVE_STRATEGY_MASTER / FOLLOWER / MIRROR are
   rejected (PortfolioAuthorityMismatchError) — never silently reinterpreted.
4. CAPITAL DECISION CONSISTENCY: contradictory immutable inputs are rejected
   (CapitalDecisionConsistencyError), never silently repaired:
   REJECT_HEAT_CAP must carry admitted_f_pct == 0; ACCEPT_FULL must carry
   admitted_f_pct > 0 and the frozen family-f contract (A 0.70/0.70,
   B 0.30/0.30); model heat must be finite and non-negative (tolerance for
   fp noise), and ACCEPT_FULL model_heat_after <= H1 cap 1.00 + tolerance.
   ALL numeric contract fields fail closed on NaN / +inf / -inf
   (InvalidNumericInputError) — `not pos_t` style guards alone do not catch
   NaN, so explicit math.isfinite checks are used.
5. CAUSAL KNOWN_TIME: known_time = max(event.entry_known_timestamp,
   decision.decision_timestamp, snapshot.observed_at) on timezone-aware
   parsed timestamps. Naive timestamps are normalized to UTC per the sealed
   ledger semantics (documented, deterministic). No wall-clock use.
6. TYPED ERRORS: InvalidFamilyError, InvalidDirectionError,
   InvalidAccountRoleError, PortfolioAuthorityMismatchError,
   CapitalDecisionConsistencyError, RiskUnitMismatchError,
   InvalidNumericInputError, InvalidTimestampError.
7. OUTPUT AUDIT CHAIN: EconomicExposureTarget passes through the upstream
   audit truth (decision_id, requested_f_pct, model_heat_before,
   model_heat_after, configuration_hash, portfolio_group_id,
   account_profile_hash, account_snapshot_id, science_version) so a
   downstream runtime can answer which event/decision/policy/binding/heat
   state produced the target without reopening source files. Nothing is
   recomputed. No broker fields are introduced.

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
H1. Per the frozen R1.1 handoff contract, rejection still requires a valid
binding + account snapshot (the output is a fully bound translation record
carrying account identity / snapshot truth); a contradictory CapitalDecision
(e.g. REJECT_HEAT_CAP with admitted_f > 0) is rejected, never silently
overwritten. Invalid or unavailable inputs raise fail-closed TranslationError
subclasses.

IDEMPOTENCY
-----------
translate() is a pure deterministic function of its inputs. The translation_id
is a canonical hash binding every execution-semantics input — event, decision,
capital policy/config, account binding, and the frozen account snapshot (via
account_snapshot_id). The same complete inputs always yield the same
translation_id (idempotency key); different account / profile / snapshot /
config inputs yield different ids because they are different economic targets.

SCIENCE (FROZEN, UNTOUCHED)
----------------------------
890 events (A 432 / B 458); A1_70_30 + H1-1.00-REJ: 826 ACCEPT_FULL
(A 371 / B 455), 64 REJECT_HEAT_CAP. 1R = 24.49489742783178 bps — a
NORMALIZED EXPECTED-MOVE UNIT, NOT a hard stop / max loss / broker stop.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Frozen science constants (sealed; DO NOT CHANGE)
# ---------------------------------------------------------------------------
RISK_UNIT_BPS = 24.49489742783178          # TARGET_VOL x sqrt(6h hold)
TARGET_VOL = 10.0                          # bps per hour normalized target vol
FAMILY_W: dict = {"A": 0.70, "B": 0.30}    # frozen family weights (percent)
F_TOTAL_PCT = 1.00                         # f_total = 1.00% (research default)
MODEL_HEAT_CAP_F_UNITS = 1.00              # H1-1.00-REJ gross-heat cap (f-units)
TRANSLATION_VERSION = "D0.1-1"
SCIENCE_VERSION = "R1.1"

# Frozen strategy-science contract checks (applied when the event's
# translation_science_version == SCIENCE_VERSION; any other version fails
# closed because this core implements exactly the sealed R1.1 contract).
RISK_UNIT_TOL = 1e-9                       # strict tolerance vs frozen 1R
F_FAMILY_TOL = 1e-9                        # strict tolerance vs frozen f
HEAT_EPS = 1e-9                            # fp-noise tolerance for heat bounds
FAMILY_F_CONTRACT = {                      # (requested_f_pct, admitted_f_pct)
    "A": (0.70, 0.70),
    "B": (0.30, 0.30),
}

# Frozen reference value = 1e4 / RISK_UNIT_BPS = 408.2483... (x pos per event).
# DIAGNOSTIC ONLY: D0.1 arithmetic uses the explicit risk_unit_bps argument
# (1e4 / risk_unit_bps), never this constant.
ONE_R_NOTIONAL_FACTOR = 1e4 / RISK_UNIT_BPS

# The sealed research universe. Anything else is UNKNOWN_INSTRUMENT_SPEC until
# a future research checkpoint extends it (would be new science).
KNOWN_RESEARCH_INSTRUMENTS = frozenset({"USDJPY"})

FAMILIES = ("A", "B")
DIRECTIONS = ("LONG", "SHORT")
DECISION_STATUSES = ("ACCEPT_FULL", "REJECT_HEAT_CAP")
STALENESS_STATUSES = ("FRESH", "STALE", "UNKNOWN")
ACCOUNT_ROLES = ("EXCLUSIVE_STRATEGY_MASTER", "PORTFOLIO_MASTER",
                 "FOLLOWER", "MIRROR")

# Canonical A+B book topology (sealed): ONE shared portfolio capital authority.
REQUIRED_ACCOUNT_ROLE = "PORTFOLIO_MASTER"

# Canonical serialization versions for identity hashes.
ID_SCHEMA_VERSION = 2
SNAPSHOT_ID_SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Fail-closed translation errors
# ---------------------------------------------------------------------------
class TranslationError(Exception):
    """Base class for fail-closed capital-translation failures."""


class InvalidDecisionStatusError(TranslationError):
    """CapitalDecision.status is not a sealed value."""


class InvalidFamilyError(TranslationError):
    """Event family is not in the sealed universe (A, B)."""


class InvalidDirectionError(TranslationError):
    """Event direction is not a sealed value (LONG, SHORT)."""


class InvalidAccountRoleError(TranslationError):
    """Account role is not a known role value (or is empty)."""


class PortfolioAuthorityMismatchError(TranslationError):
    """The bound account is not the PORTFOLIO_MASTER required by the sealed
    canonical A+B portfolio (one shared capital / H1 authority)."""


class CapitalDecisionConsistencyError(TranslationError):
    """Immutable CapitalDecision inputs are internally contradictory
    (e.g. REJECT with admitted_f > 0, ACCEPT with admitted_f == 0, family-f
    contract breach, heat bounds breached). Never silently repaired."""


class RiskUnitMismatchError(TranslationError):
    """risk_unit_bps does not match the frozen strategy-science contract
    (24.49489742783178 for science R1.1) or the science version is
    unsupported by this core."""


class InvalidNumericInputError(TranslationError):
    """A numeric contract field is NaN / +inf / -inf (never valid)."""


class InvalidTimestampError(TranslationError):
    """A required timestamp is empty, unparseable, or not zone-safe."""


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
    and never recomputes H1, family, or model heat; it only validates that
    they are internally consistent."""

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
# Output contract (mirror CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA + audit chain)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EconomicExposureTarget:
    """Pure economic exposure target. NO broker fields (no lots, margin,
    buying power, order type, fill mode, slippage, broker symbol).
    Carries the upstream audit chain (decision_id, requested_f_pct, model
    heat, configuration/profile/portfolio identity) as immutable passthrough
    so a downstream runtime can attribute the target without reopening source
    files. Nothing in this output is recomputed by the core."""

    event_id: str
    decision_id: str
    account_id: str
    strategy_id: str
    family: str
    direction: str
    research_instrument: str
    requested_f_pct: float
    admitted_f_pct: float
    pos_t: float
    risk_unit_bps: float
    model_heat_before: float
    model_heat_after: float
    equity_reference: float
    account_currency: str
    one_R_budget_account_ccy: float
    target_notional_account_ccy: float
    one_R_price_move_bps: float
    capital_policy_id: str
    configuration_hash: str
    portfolio_group_id: str
    account_profile_hash: str
    account_snapshot_id: str
    translation_version: str
    science_version: str
    known_time: str
    status: str                      # ECONOMIC_TARGET | NO_EXPOSURE
    translation_id: str              # idempotency key (canonical hash)


# ---------------------------------------------------------------------------
# Canonical serialization + identity (no delimiter ambiguity)
# ---------------------------------------------------------------------------
def _canonical_json(obj) -> str:
    """Deterministic canonical serialization: sorted keys, compact separators,
    UTF-8-safe ASCII escaping. Versioned schemas keep future evolutions
    unambiguous; nested structure (not "|".join) removes delimiter-collision
    ambiguity such as ["a|b","c"] vs ["a","b|c"]."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_ts(value: str, field: str) -> datetime:
    """Parse a required ISO 8601 timestamp, fail closed on empty/unparseable,
    and normalize naive timestamps to UTC (sealed ledger semantics: naive
    wall-clock timestamps are UTC). Returns an AWARE datetime so comparisons
    are zone-safe."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidTimestampError(f"{field} is empty; expected ISO 8601")
    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError:
        raise InvalidTimestampError(
            f"{field} {value!r} is not a parseable ISO 8601 timestamp")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # documented normalization
    return dt


def account_snapshot_id(snapshot: BoundAccountSnapshot) -> str:
    """Deterministic identity of the frozen account snapshot (Option B from
    the D0.1 contract): account_id + equity_at_admission + account_currency +
    observed_at + profile_config_hash. A different frozen equity snapshot is a
    DIFFERENT economic basis -> different snapshot id -> different
    translation_id."""
    payload = _canonical_json({
        "schema_version": SNAPSHOT_ID_SCHEMA_VERSION,
        "account_id": snapshot.account_id,
        "equity_at_admission": snapshot.equity_at_admission,
        "account_currency": snapshot.account_currency,
        "observed_at": _normalize_ts(snapshot.observed_at,
                                     "snapshot.observed_at").isoformat(),
        "profile_config_hash": snapshot.profile_config_hash,
    })
    return "SNP-" + _sha256_hex(payload)[:32]


def translation_id(
    event: StrategyEventReference,
    decision: CapitalDecisionReference,
    binding: AccountBindingReference,
    snapshot_id: str,
) -> str:
    """Canonical, account/snapshot-bound translation identity. Binds every
    execution-semantics input: event, decision, capital policy/config,
    account binding (account_id, portfolio_group_id, role), the frozen
    account snapshot (via account_snapshot_id), translation version and
    science version. Same complete inputs -> same id; any change to an
    execution-semantics input -> different id."""
    payload = _canonical_json({
        "schema_version": ID_SCHEMA_VERSION,
        "event_id": event.event_id,
        "decision_id": decision.decision_id,
        "policy_id": decision.policy_id,
        "configuration_hash": decision.configuration_hash,
        "account_id": binding.account_id,
        "portfolio_group_id": binding.portfolio_group_id,
        "account_role": binding.account_role,
        "account_snapshot_id": snapshot_id,
        "translation_version": TRANSLATION_VERSION,
        "science_version": SCIENCE_VERSION,
    })
    return "TR-" + _sha256_hex(payload)[:32]


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def _require_finite(value: float, field: str) -> None:
    """Fail closed on NaN / +/-inf. (`not value` style guards do NOT catch
    NaN because bool(float('nan')) is True; explicit isfinite is required.)"""
    if isinstance(value, bool) or not isinstance(value, (int, float)) \
            or not math.isfinite(value):
        raise InvalidNumericInputError(
            f"{field} must be a finite number (got {value!r})")


def one_R_price_move_bps(pos_t: float, risk_unit_bps: float = RISK_UNIT_BPS) -> float:
    """Underlying gross price move associated with +1R (event-specific):
    1R PnL = pos_t x price_move_bps  =>  price_move_bps = risk_unit / pos_t."""
    _require_finite(pos_t, "pos_t")
    _require_finite(risk_unit_bps, "risk_unit_bps")
    if pos_t <= 0:
        raise InvalidPositionError(f"pos_t must be > 0 (got {pos_t!r})")
    if risk_unit_bps <= 0:
        raise TranslationError(f"risk_unit_bps must be > 0 (got {risk_unit_bps!r})")
    return risk_unit_bps / pos_t


def target_notional(
    equity: float,
    admitted_f_pct: float,
    pos_t: float,
    risk_unit_bps: float = RISK_UNIT_BPS,
) -> float:
    """Corrected R1 formula: N = E x (f/100) x pos_t x 1e4 / risk_unit_bps.

    D0.1: the arithmetic uses the EXPLICIT risk_unit_bps argument — never a
    silent module constant. ONE_R_NOTIONAL_FACTOR is a frozen reference value
    only (diagnostic)."""
    _require_finite(equity, "equity")
    _require_finite(admitted_f_pct, "admitted_f_pct")
    _require_finite(pos_t, "pos_t")
    _require_finite(risk_unit_bps, "risk_unit_bps")
    if equity <= 0:
        raise MissingAccountEquityError(f"equity must be > 0 (got {equity!r})")
    if admitted_f_pct < 0:
        raise TranslationError(f"admitted_f_pct must be >= 0 (got {admitted_f_pct!r})")
    if pos_t <= 0:
        raise InvalidPositionError(f"pos_t must be > 0 (got {pos_t!r})")
    if risk_unit_bps <= 0:
        raise TranslationError(f"risk_unit_bps must be > 0 (got {risk_unit_bps!r})")
    return equity * (admitted_f_pct / 100.0) * pos_t * (1e4 / risk_unit_bps)


def one_R_budget(equity: float, admitted_f_pct: float) -> float:
    """one_R_budget_account_ccy = equity x admitted_f_pct / 100."""
    _require_finite(equity, "equity")
    _require_finite(admitted_f_pct, "admitted_f_pct")
    if equity <= 0:
        raise MissingAccountEquityError(f"equity must be > 0 (got {equity!r})")
    if admitted_f_pct < 0:
        raise TranslationError(f"admitted_f_pct must be >= 0 (got {admitted_f_pct!r})")
    return equity * (admitted_f_pct / 100.0)


# ---------------------------------------------------------------------------
# The pure translate() — the entire D0.1 core
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

    D0.1 contract gates (all fail closed):
      - science version must be R1.1 (this core implements exactly one
        sealed science contract); risk_unit_bps must equal the frozen 1R
      - all numeric contract fields must be finite (NaN/inf rejected)
      - canonical A+B book requires PORTFOLIO_MASTER + portfolio_group_id
      - CapitalDecision must be internally consistent (never silently
        repaired): REJECT -> admitted_f == 0; ACCEPT -> admitted_f > 0 and
        frozen family-f contract (A 0.70/0.70, B 0.30/0.30); model heat
        finite, >= 0, and ACCEPT model_heat_after <= H1 cap
      - known_time = max(event.entry, decision.timestamp, snapshot.observed)
        on timezone-aware timestamps (naive normalized to UTC)
    """
    # -- science-version + structural validation (fail closed) ---------------
    if event.translation_science_version != SCIENCE_VERSION:
        raise RiskUnitMismatchError(
            f"unsupported translation_science_version "
            f"{event.translation_science_version!r}; this core implements "
            f"science version {SCIENCE_VERSION!r} only")
    if event.family not in FAMILIES:
        raise InvalidFamilyError(f"unknown family {event.family!r}")
    if event.direction not in DIRECTIONS:
        raise InvalidDirectionError(f"unknown direction {event.direction!r}")
    if event.instrument_research_identity not in KNOWN_RESEARCH_INSTRUMENTS:
        raise UnknownInstrumentSpecError(
            f"instrument {event.instrument_research_identity!r} is not in the "
            f"sealed research universe {sorted(KNOWN_RESEARCH_INSTRUMENTS)}")
    if decision.status not in DECISION_STATUSES:
        raise InvalidDecisionStatusError(
            f"unknown decision status {decision.status!r}")
    if binding.account_role not in ACCOUNT_ROLES:
        raise InvalidAccountRoleError(
            f"unknown account role {binding.account_role!r}")
    if binding.account_role != REQUIRED_ACCOUNT_ROLE:
        raise PortfolioAuthorityMismatchError(
            f"canonical A+B book (science {SCIENCE_VERSION}) requires account "
            f"role {REQUIRED_ACCOUNT_ROLE!r}; got {binding.account_role!r}. "
            f"Splitting A/B across independent accounts would change the "
            f"sealed portfolio science.")
    if not binding.portfolio_group_id or not str(binding.portfolio_group_id).strip():
        raise PortfolioAuthorityMismatchError(
            "portfolio_group_id must be non-empty: the canonical A+B book "
            "requires ONE shared portfolio binding")
    if not decision.policy_id or not str(decision.policy_id).strip():
        raise CapitalDecisionConsistencyError("policy_id must be non-empty")
    if not decision.configuration_hash or not str(decision.configuration_hash).strip():
        raise CapitalDecisionConsistencyError(
            "configuration_hash must be non-empty")
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

    # -- numeric finiteness (NaN/inf fail closed) ----------------------------
    for value, field in [
        (event.pos_t, "pos_t"),
        (event.risk_unit_bps, "risk_unit_bps"),
        (decision.requested_f_pct, "requested_f_pct"),
        (decision.admitted_f_pct, "admitted_f_pct"),
        (decision.model_heat_before, "model_heat_before"),
        (decision.model_heat_after, "model_heat_after"),
        (snapshot.equity_at_admission, "equity_at_admission"),
    ]:
        _require_finite(value, field)

    if snapshot.equity_at_admission <= 0:
        raise MissingAccountEquityError(
            f"equity_at_admission must be > 0 (got {snapshot.equity_at_admission!r})")
    if event.pos_t <= 0:
        raise InvalidPositionError(f"pos_t must be > 0 (got {event.pos_t!r})")
    if event.risk_unit_bps <= 0:
        raise InvalidNumericInputError(
            f"risk_unit_bps must be > 0 (got {event.risk_unit_bps!r})")
    if not math.isclose(event.risk_unit_bps, RISK_UNIT_BPS,
                        rel_tol=0.0, abs_tol=RISK_UNIT_TOL):
        raise RiskUnitMismatchError(
            f"risk_unit_bps {event.risk_unit_bps!r} does not match the frozen "
            f"strategy-science risk unit {RISK_UNIT_BPS!r} (science "
            f"{SCIENCE_VERSION}); refusing to translate under a different R")
    if decision.requested_f_pct < 0 or decision.admitted_f_pct < 0:
        raise CapitalDecisionConsistencyError(
            f"requested_f_pct / admitted_f_pct must be >= 0 "
            f"(got {decision.requested_f_pct!r} / {decision.admitted_f_pct!r})")

    # -- model heat bounds (contract checks only; never recomputed) ----------
    if decision.model_heat_before < -HEAT_EPS or decision.model_heat_after < -HEAT_EPS:
        raise CapitalDecisionConsistencyError(
            f"model heat must be >= 0 (got before {decision.model_heat_before!r} / "
            f"after {decision.model_heat_after!r}); negative heat is not a "
            f"valid sealed state")

    # -- capital decision consistency (immutable; reject, never repair) ------
    req_f, adm_f = FAMILY_F_CONTRACT[event.family]
    if not math.isclose(decision.requested_f_pct, req_f,
                        rel_tol=0.0, abs_tol=F_FAMILY_TOL):
        raise CapitalDecisionConsistencyError(
            f"family {event.family} requested_f_pct must be {req_f} under the "
            f"frozen R1.1 policy (got {decision.requested_f_pct!r})")
    if decision.status == "ACCEPT_FULL":
        if not math.isclose(decision.admitted_f_pct, adm_f,
                            rel_tol=0.0, abs_tol=F_FAMILY_TOL):
            raise CapitalDecisionConsistencyError(
                f"ACCEPT_FULL family {event.family} admitted_f_pct must be "
                f"{adm_f} under the frozen R1.1 policy "
                f"(got {decision.admitted_f_pct!r})")
        if decision.model_heat_after > MODEL_HEAT_CAP_F_UNITS + HEAT_EPS:
            raise CapitalDecisionConsistencyError(
                f"ACCEPT_FULL model_heat_after {decision.model_heat_after!r} "
                f"exceeds the H1 gross-heat cap "
                f"{MODEL_HEAT_CAP_F_UNITS} (policy H1-1.00-REJ)")
    else:  # REJECT_HEAT_CAP
        if not math.isclose(decision.admitted_f_pct, 0.0,
                            rel_tol=0.0, abs_tol=F_FAMILY_TOL):
            raise CapitalDecisionConsistencyError(
                f"rejected decision {decision.status!r} must carry "
                f"admitted_f_pct == 0 (got {decision.admitted_f_pct!r}); "
                f"a rejected event has ZERO admitted exposure — not silently "
                f"overwritten")

    # -- causal timestamps (timezone-aware; naive normalized to UTC) ---------
    _normalize_ts(event.entry_known_timestamp, "event.entry_known_timestamp")
    _normalize_ts(decision.decision_timestamp, "decision.decision_timestamp")
    _normalize_ts(snapshot.observed_at, "snapshot.observed_at")

    # -- identity: account/snapshot-bound canonical hash ---------------------
    snap_id = account_snapshot_id(snapshot)
    tid = translation_id(event, decision, binding, snap_id)

    # final economic exposure is known only once the account snapshot is
    # observed: causal known_time = max of event / decision / snapshot times
    known_time = max(
        _normalize_ts(event.entry_known_timestamp, "event.entry_known_timestamp"),
        _normalize_ts(decision.decision_timestamp, "decision.decision_timestamp"),
        _normalize_ts(snapshot.observed_at, "snapshot.observed_at"),
    ).isoformat()

    # -- rejected events: NO_EXPOSURE (zero everything, no H1 reconsideration)
    if decision.status != "ACCEPT_FULL":
        return EconomicExposureTarget(
            event_id=event.event_id, decision_id=decision.decision_id,
            account_id=binding.account_id, strategy_id=event.strategy_id,
            family=event.family, direction=event.direction,
            research_instrument=event.instrument_research_identity,
            requested_f_pct=decision.requested_f_pct, admitted_f_pct=0.0,
            pos_t=event.pos_t, risk_unit_bps=event.risk_unit_bps,
            model_heat_before=decision.model_heat_before,
            model_heat_after=decision.model_heat_after,
            equity_reference=snapshot.equity_at_admission,
            account_currency=snapshot.account_currency,
            one_R_budget_account_ccy=0.0, target_notional_account_ccy=0.0,
            one_R_price_move_bps=0.0, capital_policy_id=decision.policy_id,
            configuration_hash=decision.configuration_hash,
            portfolio_group_id=binding.portfolio_group_id,
            account_profile_hash=snapshot.profile_config_hash,
            account_snapshot_id=snap_id,
            translation_version=TRANSLATION_VERSION,
            science_version=SCIENCE_VERSION, known_time=known_time,
            status="NO_EXPOSURE", translation_id=tid)

    # -- accepted events: corrected economic exposure ------------------------
    budget = one_R_budget(snapshot.equity_at_admission, decision.admitted_f_pct)
    notional = target_notional(snapshot.equity_at_admission,
                               decision.admitted_f_pct, event.pos_t,
                               event.risk_unit_bps)
    move_bps = one_R_price_move_bps(event.pos_t, event.risk_unit_bps)

    return EconomicExposureTarget(
        event_id=event.event_id, decision_id=decision.decision_id,
        account_id=binding.account_id, strategy_id=event.strategy_id,
        family=event.family, direction=event.direction,
        research_instrument=event.instrument_research_identity,
        requested_f_pct=decision.requested_f_pct,
        admitted_f_pct=decision.admitted_f_pct, pos_t=event.pos_t,
        risk_unit_bps=event.risk_unit_bps,
        model_heat_before=decision.model_heat_before,
        model_heat_after=decision.model_heat_after,
        equity_reference=snapshot.equity_at_admission,
        account_currency=snapshot.account_currency,
        one_R_budget_account_ccy=budget,
        target_notional_account_ccy=notional,
        one_R_price_move_bps=move_bps,
        capital_policy_id=decision.policy_id,
        configuration_hash=decision.configuration_hash,
        portfolio_group_id=binding.portfolio_group_id,
        account_profile_hash=snapshot.profile_config_hash,
        account_snapshot_id=snap_id,
        translation_version=TRANSLATION_VERSION,
        science_version=SCIENCE_VERSION, known_time=known_time,
        status="ECONOMIC_TARGET", translation_id=tid)
