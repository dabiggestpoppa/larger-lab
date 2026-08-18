"""
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1 tests — contract / idempotency
truth repair over the D0 pure core.

Locks the D0.1 repairs:
- risk_unit_bps argument is USED by target-notional arithmetic; translate()
  enforces the frozen strategy-science risk unit (RiskUnitMismatchError)
- all numeric contract fields fail closed on NaN / +inf / -inf
- translation_id is account / profile / portfolio / snapshot bound with
  canonical (schema-versioned, sorted-key JSON) serialization — no delimiter
  ambiguity; same complete inputs -> same id
- PORTFOLIO_MASTER topology required for the canonical A+B book;
  EXCLUSIVE_STRATEGY_MASTER / FOLLOWER / MIRROR blocked; portfolio_group_id
  required
- CapitalDecision consistency: REJECT + admitted_f > 0 blocked; ACCEPT +
  admitted_f == 0 blocked; frozen family-f contract (A 0.70/0.70,
  B 0.30/0.30) enforced; model-heat bounds enforced
- causal known_time = max(event / decision / snapshot) on aware timestamps
- output audit chain (decision_id, requested_f, model heat, config/profile/
  portfolio hashes) passed through; NO broker fields
- 890-event economics unchanged (parity + canonical notional distribution)
- no H1 / family / model-heat recomputation; no broker call
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_SRC = str(Path(__file__).resolve().parents[1] / "src")
_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
for _p in (_SRC, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

import capital_routing.translation.capital_translation_core as core  # noqa: E402

from capital_routing.translation.capital_translation_core import (  # noqa: E402
    ACCOUNT_ROLES, FAMILY_F_CONTRACT, FAMILY_W, MODEL_HEAT_CAP_F_UNITS,
    RISK_UNIT_BPS, SCIENCE_VERSION, TRANSLATION_VERSION,
    AccountBindingReference, AccountBindingMismatchError,
    BoundAccountSnapshot, CapitalDecisionConsistencyError,
    CapitalDecisionReference, EconomicExposureTarget,
    InvalidAccountRoleError, InvalidDecisionStatusError, InvalidDirectionError,
    InvalidFamilyError, InvalidNumericInputError, InvalidPositionError,
    InvalidTimestampError, MissingAccountEquityError,
    PortfolioAuthorityMismatchError,    RiskUnitMismatchError, StaleAccountStateError, StrategyEventReference,
    TranslationError, UnresolvedAccountCurrencyError,
    UnknownInstrumentSpecError, account_snapshot_id, one_R_budget,
    one_R_price_move_bps, target_notional, translate, translation_id,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = (ROOT / "research" / "capital_routing" / "risk"
       / "block4_capital_translation_core_d0_1")
EVENT_CSV = (ROOT / "research" / "capital_routing" / "risk"
             / "block3_execution_translation_planning_r1"
             / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv")

E = 10000.0  # concrete equity for pure-formula tests
R_ALT = RISK_UNIT_BPS * 2.0  # non-frozen risk unit for negative tests


def _decision(status="ACCEPT_FULL", admitted_f_pct=0.70, family="A",
              event_id="EV-1", decision_id="DEC-1", model_heat_after=None,
              requested_f_pct=None, model_heat_before=0.0,
              decision_timestamp="2024-01-01 00:00") -> CapitalDecisionReference:
    if requested_f_pct is None:
        requested_f_pct = FAMILY_W[family]
    if model_heat_after is None:
        model_heat_after = admitted_f_pct if status == "ACCEPT_FULL" else 0.0
    return CapitalDecisionReference(
        decision_id=decision_id, policy_id="H1-1.00-REJ",
        requested_f_pct=requested_f_pct, admitted_f_pct=admitted_f_pct,
        status=status, model_heat_before=model_heat_before,
        model_heat_after=model_heat_after,
        decision_timestamp=decision_timestamp, configuration_hash="cfg-test")


def _event(family="A", direction="LONG", pos=1.5, event_id="EV-1",
           risk_unit_bps=RISK_UNIT_BPS, ts="2024-01-01 00:00") -> StrategyEventReference:
    return StrategyEventReference(
        event_id=event_id, strategy_id="capital-routing", family=family,
        direction=direction, instrument_research_identity="USDJPY",
        entry_known_timestamp=ts, pos_t=pos, risk_unit_bps=risk_unit_bps,
        translation_science_version=SCIENCE_VERSION)


def _binding(account_id="acct-1", role="PORTFOLIO_MASTER",
             portfolio_group_id="portfolio-1") -> AccountBindingReference:
    return AccountBindingReference(account_id=account_id,
                                   portfolio_group_id=portfolio_group_id,
                                   account_role=role)


def _snapshot(account_id="acct-1", equity=E, currency="USD", staleness="FRESH",
              profile_config_hash="cfg-test", observed_at="2024-01-01 00:00",
              ) -> BoundAccountSnapshot:
    return BoundAccountSnapshot(account_id=account_id, account_currency=currency,
                                equity_at_admission=equity,
                                observed_at=observed_at,
                                staleness_status=staleness,
                                profile_config_hash=profile_config_hash)


# ===========================================================================
# Defect 1 — risk_unit_bps argument used in math + frozen R enforced
# ===========================================================================
def test_1_helper_uses_provided_risk_unit_bps():
    n1 = target_notional(E, 0.70, 2.0, RISK_UNIT_BPS)
    n2 = target_notional(E, 0.70, 2.0, R_ALT)
    assert abs(n1 - E * 0.007 * 2.0 * 1e4 / RISK_UNIT_BPS) < 1e-9
    assert abs(n2 - E * 0.007 * 2.0 * 1e4 / R_ALT) < 1e-9
    assert n1 != n2  # the argument changes the result


def test_2_different_helper_R_changes_notional_inversely():
    n1 = target_notional(E, 0.70, 2.0, RISK_UNIT_BPS)
    n2 = target_notional(E, 0.70, 2.0, R_ALT)
    assert abs(n2 / n1 - RISK_UNIT_BPS / R_ALT) < 1e-9  # inversely proportional


def test_3_translate_rejects_non_frozen_risk_unit():
    with pytest.raises(RiskUnitMismatchError):
        translate(_event(risk_unit_bps=R_ALT), _decision(), _binding(), _snapshot())


def test_4_nan_risk_unit_rejected():
    ev = _event(risk_unit_bps=float("nan"))
    with pytest.raises(InvalidNumericInputError):
        translate(ev, _decision(), _binding(), _snapshot())


def test_5_inf_risk_unit_rejected():
    for bad in (float("inf"), float("-inf")):
        with pytest.raises(InvalidNumericInputError):
            translate(_event(risk_unit_bps=bad), _decision(), _binding(), _snapshot())


def test_6_nan_pos_rejected():
    ev = _event(pos=float("nan"))
    with pytest.raises(InvalidNumericInputError):
        translate(ev, _decision(), _binding(), _snapshot())


def test_7_inf_pos_rejected():
    for bad in (float("inf"), float("-inf")):
        with pytest.raises(InvalidNumericInputError):
            translate(_event(pos=bad), _decision(), _binding(), _snapshot())


def test_8_nan_equity_rejected():
    with pytest.raises(InvalidNumericInputError):
        translate(_event(), _decision(), _binding(), _snapshot(equity=float("nan")))


def test_9_inf_equity_rejected():
    for bad in (float("inf"), float("-inf")):
        with pytest.raises(InvalidNumericInputError):
            translate(_event(), _decision(), _binding(), _snapshot(equity=bad))


def test_10_nan_admitted_f_rejected():
    with pytest.raises(InvalidNumericInputError):
        translate(_event(), _decision(admitted_f_pct=float("nan")), _binding(),
                  _snapshot())


def test_11_inf_admitted_f_rejected():
    for bad in (float("inf"), float("-inf")):
        with pytest.raises(InvalidNumericInputError):
            translate(_event(), _decision(admitted_f_pct=bad), _binding(),
                      _snapshot())


# ===========================================================================
# Defect 4 — CapitalDecision consistency
# ===========================================================================
def test_12_rejected_with_nonzero_admitted_f_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event(), _decision(status="REJECT_HEAT_CAP", admitted_f_pct=0.30),
                  _binding(), _snapshot())


def test_13_accepted_with_zero_admitted_f_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event(), _decision(status="ACCEPT_FULL", admitted_f_pct=0.0),
                  _binding(), _snapshot())


def test_14_A_requested_f_mismatch_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event("A"), _decision(requested_f_pct=0.30), _binding(),
                  _snapshot())


def test_15_A_admitted_f_mismatch_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event("A"), _decision(admitted_f_pct=0.30), _binding(),
                  _snapshot())


def test_16_B_requested_f_mismatch_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event("B", "SHORT"), _decision(status="ACCEPT_FULL",
                                                  admitted_f_pct=0.30, family="B",
                                                  requested_f_pct=0.70),
                  _binding(), _snapshot())


def test_17_B_admitted_f_mismatch_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event("B", "SHORT"), _decision(status="ACCEPT_FULL",
                                                  admitted_f_pct=0.70, family="B"),
                  _binding(), _snapshot())


def test_100x_f_unit_error_blocked():
    # "A = 70 instead of 0.70" must fail the frozen family contract
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event("A"), _decision(admitted_f_pct=70.0, requested_f_pct=70.0),
                  _binding(), _snapshot())
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event("A"), _decision(requested_f_pct=70.0), _binding(),
                  _snapshot())


def test_model_heat_after_above_cap_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event(), _decision(model_heat_after=1.01), _binding(),
                  _snapshot())


def test_negative_f_and_negative_heat_blocked():
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event(), _decision(admitted_f_pct=-0.70), _binding(), _snapshot())
    with pytest.raises(CapitalDecisionConsistencyError):
        translate(_event(), _decision(model_heat_before=-0.5), _binding(),
                  _snapshot())


# ===========================================================================
# Defect 3 — PORTFOLIO_MASTER topology
# ===========================================================================
def test_18_exclusive_master_blocked():
    with pytest.raises(PortfolioAuthorityMismatchError):
        translate(_event(), _decision(), _binding(role="EXCLUSIVE_STRATEGY_MASTER"),
                  _snapshot())


def test_19_follower_blocked():
    with pytest.raises(PortfolioAuthorityMismatchError):
        translate(_event(), _decision(), _binding(role="FOLLOWER"), _snapshot())
    with pytest.raises(PortfolioAuthorityMismatchError):
        translate(_event(), _decision(), _binding(role="MIRROR"), _snapshot())


def test_20_portfolio_master_accepted():
    t = translate(_event(), _decision(), _binding(role="PORTFOLIO_MASTER"),
                  _snapshot())
    assert t.status == "ECONOMIC_TARGET"


def test_21_empty_portfolio_group_rejected():
    with pytest.raises(PortfolioAuthorityMismatchError):
        translate(_event(), _decision(), _binding(portfolio_group_id=""),
                  _snapshot())
    with pytest.raises(PortfolioAuthorityMismatchError):
        translate(_event(), _decision(), _binding(portfolio_group_id="   "),
                  _snapshot())


def test_unknown_role_rejected():
    with pytest.raises(InvalidAccountRoleError):
        translate(_event(), _decision(), _binding(role="BOGUS_ROLE"), _snapshot())
    assert "MIRROR" in ACCOUNT_ROLES  # represented in the enum, blocked by gate


# ===========================================================================
# Defect 2 — account / snapshot-bound canonical translation_id
# ===========================================================================
def _base_translate():
    return translate(_event("A", "LONG", 1.5, "EV-1"),
                     _decision("ACCEPT_FULL", 0.70, "A", "EV-1"),
                     _binding(), _snapshot())


def test_22_different_account_id_different_translation_id():
    t1 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding("acct-A"), _snapshot(account_id="acct-A"))
    t2 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding("acct-B"), _snapshot(account_id="acct-B"))
    assert t1.translation_id != t2.translation_id


def test_23_different_account_profile_hash_different_translation_id():
    t1 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding(), _snapshot(profile_config_hash="profile-A"))
    t2 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding(), _snapshot(profile_config_hash="profile-B"))
    assert t1.translation_id != t2.translation_id


def test_24_different_equity_snapshot_different_translation_id():
    t1 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding(), _snapshot(equity=10000.0))
    t2 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding(), _snapshot(equity=50000.0))
    assert t1.translation_id != t2.translation_id
    assert t1.account_snapshot_id != t2.account_snapshot_id


def test_different_portfolio_group_different_translation_id():
    t1 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding(portfolio_group_id="pg-A"), _snapshot())
    t2 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding(portfolio_group_id="pg-B"), _snapshot())
    assert t1.translation_id != t2.translation_id


def test_different_configuration_hash_different_translation_id():
    d1 = CapitalDecisionReference(decision_id="DEC-1", policy_id="H1-1.00-REJ",
                                  requested_f_pct=0.70, admitted_f_pct=0.70,
                                  status="ACCEPT_FULL", model_heat_before=0.0,
                                  model_heat_after=0.70,
                                  decision_timestamp="2024-01-01 00:00",
                                  configuration_hash="cfg-A")
    d2 = CapitalDecisionReference(decision_id="DEC-1", policy_id="H1-1.00-REJ",
                                  requested_f_pct=0.70, admitted_f_pct=0.70,
                                  status="ACCEPT_FULL", model_heat_before=0.0,
                                  model_heat_after=0.70,
                                  decision_timestamp="2024-01-01 00:00",
                                  configuration_hash="cfg-B")
    t1 = translate(_event("A", "LONG", 1.5, "EV-1"), d1, _binding(), _snapshot())
    t2 = translate(_event("A", "LONG", 1.5, "EV-1"), d2, _binding(), _snapshot())
    assert t1.translation_id != t2.translation_id


def test_different_translation_version_different_translation_id(monkeypatch):
    t1 = _base_translate()
    monkeypatch.setattr(core, "TRANSLATION_VERSION", "D0.1-2")
    t2 = _base_translate()
    assert t1.translation_id != t2.translation_id


def test_25_delimiter_collision_cannot_collide():
    # ["a|b","c"] vs ["a","b|c"] must NOT collide under canonical JSON
    t1 = translate(_event("A", "LONG", 1.5, "a|b"),
                   _decision("ACCEPT_FULL", 0.70, "A", "c"),
                   _binding(), _snapshot())
    t2 = translate(_event("A", "LONG", 1.5, "a"),
                   _decision("ACCEPT_FULL", 0.70, "A", "b|c"),
                   _binding(), _snapshot())
    assert t1.translation_id != t2.translation_id
    # same for pipe-bearing account ids
    t3 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding("acct|X"), _snapshot(account_id="acct|X"))
    t4 = translate(_event("A", "LONG", 1.5, "EV-1"), _decision("ACCEPT_FULL", 0.70,
                                                               "A", "EV-1"),
                   _binding("acct"), _snapshot(account_id="acct"))
    assert t3.translation_id != t4.translation_id


def test_26_same_complete_input_same_translation_id():
    t1 = _base_translate()
    t2 = _base_translate()
    assert t1 == t2
    assert t1.translation_id == t2.translation_id
    assert t1.translation_id.startswith("TR-")
    assert t1.account_snapshot_id.startswith("SNP-")


def test_snapshot_id_stable_and_deterministic():
    s1 = _snapshot()
    s2 = _snapshot()
    assert account_snapshot_id(s1) == account_snapshot_id(s2)
    assert account_snapshot_id(_snapshot(equity=1.0)) != account_snapshot_id(s1)


# ===========================================================================
# Defect 5 — causal known_time
# ===========================================================================
def test_27_later_snapshot_changes_known_time():
    t = translate(_event("A", "LONG", 1.5, "EV-1", ts="2024-01-01 00:00"),
                  _decision("ACCEPT_FULL", 0.70, "A", "EV-1",
                            decision_timestamp="2024-01-01 00:00"),
                  _binding(), _snapshot(observed_at="2024-01-01 00:05:00+00:00"))
    assert t.known_time == "2024-01-01T00:05:00+00:00"  # snapshot is latest
    t2 = translate(_event("A", "LONG", 1.5, "EV-1", ts="2024-01-01 01:00:00+00:00"),
                   _decision("ACCEPT_FULL", 0.70, "A", "EV-1",
                             decision_timestamp="2024-01-01 00:30:00+00:00"),
                   _binding(), _snapshot(observed_at="2024-01-01 00:20:00+00:00"))
    assert t2.known_time == "2024-01-01T01:00:00+00:00"  # event is latest


def test_28_malformed_timestamp_fails_closed():
    with pytest.raises(InvalidTimestampError):
        translate(_event(ts="not-a-timestamp"), _decision(), _binding(), _snapshot())
    with pytest.raises(InvalidTimestampError):
        translate(_event(), _decision(decision_timestamp="2024-13-99"), _binding(),
                  _snapshot())
    with pytest.raises(InvalidTimestampError):
        translate(_event(), _decision(), _binding(), _snapshot(observed_at=""))
    with pytest.raises(InvalidTimestampError):
        translate(_event(), _decision(), _binding(), _snapshot(observed_at="banana"))


def test_naive_timestamp_normalized_to_utc():
    t = _base_translate()
    assert t.known_time.endswith("+00:00")
    aware = translate(_event(ts="2024-01-01 00:00:00+00:00"), _decision(),
                      _binding(), _snapshot())
    naive = translate(_event(ts="2024-01-01 00:00:00"), _decision(),
                      _binding(), _snapshot())
    assert aware.known_time == naive.known_time  # same instant, deterministic


# ===========================================================================
# Rejected events — zero exposure, never silently repaired
# ===========================================================================
def test_rejected_maps_to_no_exposure_zero_everything():
    t = translate(_event("A", "LONG", 1.5, "EV-1"),
                  _decision("REJECT_HEAT_CAP", 0.0, "A", "EV-1"),
                  _binding(), _snapshot())
    assert t.status == "NO_EXPOSURE"
    assert t.one_R_budget_account_ccy == 0.0
    assert t.target_notional_account_ccy == 0.0
    assert t.one_R_price_move_bps == 0.0
    assert t.admitted_f_pct == 0.0
    # audit chain still bound to the rejected decision (no exposure, no H1 rerun)
    assert t.decision_id == "DEC-1"
    assert t.requested_f_pct == 0.70
    assert t.model_heat_before == 0.0
    assert t.portfolio_group_id == "portfolio-1"
    assert t.account_snapshot_id == account_snapshot_id(_snapshot())


# ===========================================================================
# Output audit chain + purity
# ===========================================================================
def test_output_audit_chain_complete():
    t = _base_translate()
    for field in ["decision_id", "requested_f_pct", "model_heat_before",
                  "model_heat_after", "configuration_hash", "portfolio_group_id",
                  "account_profile_hash", "account_snapshot_id", "science_version"]:
        assert field in t.__dataclass_fields__, f"missing audit field {field}"
    assert t.decision_id == "DEC-1"
    assert t.requested_f_pct == 0.70
    assert t.model_heat_before == 0.0
    assert t.model_heat_after == 0.70
    assert t.configuration_hash == "cfg-test"
    assert t.portfolio_group_id == "portfolio-1"
    assert t.account_profile_hash == "cfg-test"
    assert t.science_version == SCIENCE_VERSION


def test_30_no_broker_fields_introduced():
    t = _base_translate()
    fields = set(t.__dataclass_fields__.keys())
    for bad in ["broker_lot", "margin", "buying_power", "order_type", "fill_mode",
                "slippage", "broker_symbol", "lot", "contracts", "leverage",
                "broker_ticket"]:
        assert bad not in fields, f"broker field {bad} leaked into pure output"


def test_31_32_no_h1_family_model_heat_recompute():
    src = (ROOT / "src" / "capital_routing" / "translation"
           / "capital_translation_core.py").read_text(encoding="utf-8")
    for banned in ["admit_book", "run_policy", "static_risk_architecture",
                   "gross_heat", "FAMILY_W[event.family]"]:
        assert banned not in src, f"core must not contain {banned}"
    # purity: no wall-clock / random / network / fs / broker imports
    for banned in ["datetime.now", "uuid", "random", "socket", "requests",
                   "urllib", "MetaTrader", "mt5", "open(", "Path("]:
        assert banned not in src, f"core must not contain {banned}"
    d = json.loads((OUT / "CR_BLOCK4_D0_1_DECISION.json").read_text(encoding="utf-8"))
    assert d["h1_recomputed"] is False
    assert d["family_recomputed"] is False
    assert d["model_heat_recomputed"] is False


def test_translate_uses_no_wall_clock():
    # known_time is derived ONLY from the three input timestamps
    t1 = _base_translate()
    t2 = _base_translate()
    assert t1.known_time == t2.known_time
    assert t1.known_time == "2024-01-01T00:00:00+00:00"


# ===========================================================================
# Structural fail-closed (existing D0 semantics preserved)
# ===========================================================================
def test_structural_errors_preserved():
    with pytest.raises(InvalidFamilyError):
        translate(_event(family="X"), _decision(), _binding(), _snapshot())
    with pytest.raises(InvalidDirectionError):
        translate(_event(direction="SIDEWAYS"), _decision(), _binding(), _snapshot())
    with pytest.raises(InvalidDecisionStatusError):
        translate(_event(), _decision(status="BOGUS"), _binding(), _snapshot())
    with pytest.raises(UnknownInstrumentSpecError):
        translate(StrategyEventReference(
            event_id="EV-1", strategy_id="capital-routing", family="A",
            direction="LONG", instrument_research_identity="EURJPY",
            entry_known_timestamp="2024-01-01 00:00", pos_t=1.5,
            risk_unit_bps=RISK_UNIT_BPS,
            translation_science_version=SCIENCE_VERSION),
            _decision(), _binding(), _snapshot())
    with pytest.raises(AccountBindingMismatchError):
        translate(_event(), _decision(), _binding("acct-1"),
                  _snapshot(account_id="acct-2"))
    with pytest.raises(StaleAccountStateError):
        translate(_event(), _decision(), _binding(), _snapshot(staleness="STALE"))
    with pytest.raises(UnresolvedAccountCurrencyError):
        translate(_event(), _decision(), _binding(), _snapshot(currency=""))
    with pytest.raises(MissingAccountEquityError):
        translate(_event(), _decision(), _binding(), _snapshot(equity=0.0))
    with pytest.raises(InvalidPositionError):
        translate(_event(pos=0.0), _decision(), _binding(), _snapshot())
    with pytest.raises(RiskUnitMismatchError):
        translate(_event(risk_unit_bps=1.0), _decision(), _binding(), _snapshot())
    with pytest.raises(RiskUnitMismatchError):
        # unsupported science version fails closed
        ev = _event()
        translate(StrategyEventReference(
            event_id=ev.event_id, strategy_id=ev.strategy_id, family=ev.family,
            direction=ev.direction,
            instrument_research_identity=ev.instrument_research_identity,
            entry_known_timestamp=ev.entry_known_timestamp, pos_t=ev.pos_t,
            risk_unit_bps=ev.risk_unit_bps,
            translation_science_version="R2.0"),
            _decision(), _binding(), _snapshot())


def test_helpers_fail_closed_on_nan_inf():
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(InvalidNumericInputError):
            target_notional(bad, 0.70, 1.0)
        with pytest.raises(InvalidNumericInputError):
            target_notional(E, 0.70, bad)
        with pytest.raises(InvalidNumericInputError):
            one_R_price_move_bps(bad)
        with pytest.raises(InvalidNumericInputError):
            one_R_budget(bad, 0.70)


# ===========================================================================
# 890-event nonregression
# ===========================================================================
def test_29_890_event_parity_unchanged():
    d = json.loads((OUT / "CR_BLOCK4_D0_1_DECISION.json").read_text(encoding="utf-8"))
    assert d["n_events"] == 890
    assert d["n_accepted"] == 826
    assert d["n_rejected"] == 64
    assert d["gross_parity_pass"] is True
    assert d["research_net_parity_pass"] is True
    assert d["notional_distribution_unchanged"] is True
    nr = json.loads((OUT / "CR_BLOCK4_D0_1_890_NONREGRESSION.json").read_text(encoding="utf-8"))
    assert nr["n_events"] == 890 and nr["n_accepted"] == 826 and nr["n_rejected"] == 64
    assert nr["accepted_A"] == 371 and nr["accepted_B"] == 455
    assert nr["gross_parity_pass"] is True and nr["research_net_parity_pass"] is True


def test_canonical_notional_stats_unchanged():
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]["notional_multiple_equity"]
    assert abs(np.percentile(acc, 50) - 1.9842) < 5e-4
    assert abs(np.percentile(acc, 95) - 7.6105) < 5e-3
    assert abs(np.percentile(acc, 99) - 16.0364) < 5e-3
    assert abs(acc.max() - 32.7663) < 5e-3
    # D0.1 core outputs reproduce the same distribution
    trans = pd.read_csv(OUT / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv")
    core_acc = trans[trans["decision"] == "ACCEPT_FULL"]["target_notional_account_ccy"]
    assert abs(np.percentile(core_acc, 50) - np.percentile(acc, 50)) < 5e-4
    assert abs(np.percentile(core_acc, 95) - np.percentile(acc, 95)) < 5e-3
    assert abs(core_acc.max() - acc.max()) < 5e-3


def test_all_890_pass_through_core():
    # every sealed event (accepted + rejected) translates through the repaired
    # core without a contract error
    trans = pd.read_csv(OUT / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv")
    assert len(trans) == 890
    assert trans["translation_status"].eq("ECONOMIC_TARGET").sum() == 826
    assert trans["translation_status"].eq("NO_EXPOSURE").sum() == 64
    assert trans["translation_id"].nunique() == 890  # one id per event/decision
    assert (trans["translation_id"].str.startswith("TR-")).all()
    assert (trans["account_snapshot_id"].str.startswith("SNP-")).all()


def test_decision_file_expected_truth():
    d = json.loads((OUT / "CR_BLOCK4_D0_1_DECISION.json").read_text(encoding="utf-8"))
    assert d["status"] == "PASS"
    assert d["d0_1_pass"] is True
    assert d["science_unchanged"] is True
    assert d["risk_unit_argument_used_in_math"] is True
    assert d["frozen_risk_unit_enforced"] is True
    assert d["nan_inf_fail_closed"] is True
    assert d["translation_id_account_bound"] is True
    assert d["translation_id_snapshot_bound"] is True
    assert d["translation_id_canonical_serialization"] is True
    assert d["portfolio_master_required"] is True
    assert d["exclusive_master_blocked_for_canonical_ab"] is True
    assert d["follower_blocked"] is True
    assert d["portfolio_group_required"] is True
    assert d["rejected_nonzero_admitted_f_blocked"] is True
    assert d["accepted_zero_admitted_f_blocked"] is True
    assert d["family_f_contract_enforced"] is True
    assert d["h1_recomputed"] is False
    assert d["family_recomputed"] is False
    assert d["model_heat_recomputed"] is False
    assert d["known_time_causal"] is True
    assert d["output_audit_chain_complete"] is True
    assert d["broker_execution_performed"] is False
    assert d["broker_fields_added"] is False
    assert d["d1_plan_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True
    assert d["next_checkpoint_recommended"] == (
        "CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN")
    assert d["risk_unit_bps"] == RISK_UNIT_BPS
    assert d["translation_version"] == TRANSLATION_VERSION
    assert d["science_version"] == SCIENCE_VERSION


def test_artifacts_present():
    names = [
        "CR_BLOCK4_D0_1_PROTOCOL.md", "CR_BLOCK4_D0_1_SOURCE_SHA_MANIFEST.json",
        "CR_BLOCK4_D0_1_DEFECT_AUDIT.md", "CR_BLOCK4_D0_1_RISK_UNIT_CONTRACT.md",
        "CR_BLOCK4_D0_1_TRANSLATION_ID_CONTRACT.md",
        "CR_BLOCK4_D0_1_CAPITAL_DECISION_INVARIANTS.md",
        "CR_BLOCK4_D0_1_ACCOUNT_ROLE_INVARIANTS.md",
        "CR_BLOCK4_D0_1_NUMERIC_FINITE_AUDIT.md",
        "CR_BLOCK4_D0_1_CAUSAL_TIME_AUDIT.md",
        "CR_BLOCK4_D0_1_OUTPUT_AUDIT_CHAIN.md",
        "CR_BLOCK4_D0_1_890_NONREGRESSION.json",
        "CR_BLOCK4_D0_1_ADVERSARIAL_TEST_AUDIT.json",
        "CR_BLOCK4_D0_1_COMPONENT_STATUS.csv",
        "CR_BLOCK4_D0_1_TEST_AUDIT.json",
        "CR_BLOCK4_D0_1_REPORT.md",
        "CR_BLOCK4_D0_1_DECISION.json",
        "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv",
    ]
    for name in names:
        assert (OUT / name).exists(), f"missing artifact {name}"
