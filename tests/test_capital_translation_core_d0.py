"""
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 tests.

The PURE deterministic capital translation core:
sealed CapitalDecision + AccountBinding + event pos_t -> EconomicExposureTarget
with the corrected R1 formula N = E x (f/100) x pos_t x 1e4 / RISK.

Locked behavior:
- 1R exact definition / corrected notional includes pos
- long & short translation; A 0.70 / B 0.30 requested f
- H1 decisions consumed as IMMUTABLE upstream inputs (A+B exact cap, second A
  rejected, three B = 0.90); REJECTED -> NO_EXPOSURE zero exposure
- gross + research-modeled net parity over all accepted events through the core
- same-timestamp determinism / exit-release causality / equity snapshot frozen
  at admission (no dynamic resizing)
- fail-closed validation (stale state, unknown instrument, binding mismatch,
  missing equity, unresolved currency, invalid pos/status)
- idempotency (same inputs -> same output; no duplicate exposure)
- no broker fields in the pure output; no H1/family recompute; no broker call;
  science unchanged (890 / 826 / 64; canonical notional stats)
"""
from __future__ import annotations

import json
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

import run_capital_translation_core_d0 as d0  # noqa: E402
import run_exec_translation_planning_r1 as r1  # noqa: E402

from capital_routing.translation.capital_translation_core import (  # noqa: E402
    FAMILY_W, RISK_UNIT_BPS, TRANSLATION_VERSION,
    AccountBindingMismatchError, BoundAccountSnapshot, CapitalDecisionReference,
    InvalidDecisionStatusError, InvalidPositionError, MissingAccountEquityError,
    StaleAccountStateError, TranslationError, UnresolvedAccountCurrencyError,
    UnknownInstrumentSpecError, one_R_budget, one_R_price_move_bps,
    target_notional, translate,
)
from capital_routing.translation.capital_translation_core import (  # noqa: E402
    AccountBindingReference, StrategyEventReference,
)
from capital_routing.static_risk_architecture import (  # noqa: E402
    FamilyAllocation, StaticRiskConfig, admit_book,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0"
EVENT_CSV = (ROOT / "research" / "capital_routing" / "risk"
             / "block3_execution_translation_planning_r1"
             / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv")

ONE_R_NOTIONAL_FACTOR = 1e4 / RISK_UNIT_BPS
E = 10000.0  # concrete equity for the pure-formula tests


def _decision(status="ACCEPT_FULL", admitted_f_pct=0.70, family="A",
              event_id="EV-1", decision_id="DEC-1") -> CapitalDecisionReference:
    return CapitalDecisionReference(
        decision_id=decision_id, policy_id="H1-1.00-REJ",
        requested_f_pct=FAMILY_W[family], admitted_f_pct=admitted_f_pct,
        status=status, model_heat_before=0.0,
        model_heat_after=admitted_f_pct if status == "ACCEPT_FULL" else 0.0,
        decision_timestamp="2024-01-01 00:00", configuration_hash="cfg-test")


def _event(family="A", direction="LONG", pos=1.5, event_id="EV-1") -> StrategyEventReference:
    return StrategyEventReference(
        event_id=event_id, strategy_id="capital-routing", family=family,
        direction=direction, instrument_research_identity="USDJPY",
        entry_known_timestamp="2024-01-01 00:00", pos_t=pos,
        risk_unit_bps=RISK_UNIT_BPS, translation_science_version="R1.1")


def _binding(account_id="acct-1") -> AccountBindingReference:
    return AccountBindingReference(account_id=account_id,
                                   portfolio_group_id="portfolio-1",
                                   account_role="PORTFOLIO_MASTER")


def _snapshot(account_id="acct-1", equity=E, currency="USD",
              staleness="FRESH") -> BoundAccountSnapshot:
    return BoundAccountSnapshot(account_id=account_id, account_currency=currency,
                                equity_at_admission=equity,
                                observed_at="2024-01-01 00:00",
                                staleness_status=staleness,
                                profile_config_hash="cfg-test")


# --- artifacts ---------------------------------------------------------------
def test_artifacts_present():
    for name in ["CR_D0_PROTOCOL.md", "CR_D0_CORE_DOC.md", "CR_D0_EVENT_TRANSLATIONS.csv",
                 "CR_D0_PARITY_890.json", "CR_D0_H1_PARITY.json",
                 "CR_D0_REJECTED_ZERO_EXPOSURE.json", "CR_D0_IDEMPOTENCY.json",
                 "CR_D0_TEST_AUDIT.json", "CR_D0_SOURCE_SHA_MANIFEST.json",
                 "CR_D0_REPORT.md", "CR_D0_DECISION.json"]:
        assert (OUT / name).exists(), f"missing artifact {name}"


# --- 1R definition / formulas -------------------------------------------------
def test_risk_unit_definition_unchanged():
    assert RISK_UNIT_BPS == 24.49489742783178
    # 1R = TARGET_VOL x sqrt(6h)
    assert abs(RISK_UNIT_BPS - 10.0 * np.sqrt(6.0)) < 1e-12


def test_raw_notional_formula_includes_pos():
    f = 0.70
    pos = 2.0
    expected = E * (f / 100.0) * pos * ONE_R_NOTIONAL_FACTOR
    assert abs(target_notional(E, f, pos) - expected) < 1e-9 * expected
    # removing pos (pos=1) does NOT reproduce the pos-scaled target
    assert abs(target_notional(E, f, 1.0) - expected) > 1e-3 * expected


def test_one_R_budget_formula():
    assert abs(one_R_budget(E, 0.70) - 70.0) < 1e-12
    assert abs(one_R_budget(E, 0.30) - 30.0) < 1e-12


def test_one_R_price_move_event_specific():
    m1 = one_R_price_move_bps(1.5)
    m2 = one_R_price_move_bps(11.0)
    assert abs(m1 - RISK_UNIT_BPS / 1.5) < 1e-12
    assert abs(m2 - RISK_UNIT_BPS / 11.0) < 1e-12
    assert m1 != m2  # event-specific, not a fixed 24.4949 bps
    assert abs(m1 - RISK_UNIT_BPS) > 1e-9  # pos != 1 -> different from RISK


# --- long / short translation -------------------------------------------------
def test_long_translation():
    t = translate(_event("A", "LONG", 1.5), _decision("ACCEPT_FULL", 0.70),
                  _binding(), _snapshot())
    assert t.status == "ECONOMIC_TARGET"
    assert t.direction == "LONG" and t.family == "A"
    assert abs(t.one_R_budget_account_ccy - 70.0) < 1e-9
    assert abs(t.target_notional_account_ccy - target_notional(E, 0.70, 1.5)) < 1e-9
    assert abs(t.one_R_price_move_bps - RISK_UNIT_BPS / 1.5) < 1e-9


def test_short_translation():
    t = translate(_event("B", "SHORT", 2.0), _decision("ACCEPT_FULL", 0.30),
                  _binding(), _snapshot())
    assert t.status == "ECONOMIC_TARGET"
    assert t.direction == "SHORT" and t.family == "B"
    assert abs(t.one_R_budget_account_ccy - 30.0) < 1e-9
    assert abs(t.target_notional_account_ccy - target_notional(E, 0.30, 2.0)) < 1e-9


def test_requested_f_A_070_B_030():
    assert FAMILY_W["A"] == 0.70 and FAMILY_W["B"] == 0.30
    ta = translate(_event("A", "LONG", 1.0), _decision("ACCEPT_FULL", 0.70),
                   _binding(), _snapshot())
    tb = translate(_event("B", "SHORT", 1.0), _decision("ACCEPT_FULL", 0.30),
                   _binding(), _snapshot())
    assert abs(ta.one_R_budget_account_ccy / tb.one_R_budget_account_ccy
               - 0.70 / 0.30) < 1e-9


# --- H1 decisions consumed upstream; D0 maps them -----------------------------
def _admit(entry, fam):
    exit_ = (pd.to_datetime(pd.Series(entry)) + pd.Timedelta(hours=6))
    exit_ = exit_.dt.strftime("%Y-%m-%d %H:%M").tolist()
    cfg = StaticRiskConfig(allocation=FamilyAllocation({"A": 0.7, "B": 0.3}),
                           base_f=1.0, gross_heat_cap_mult=1.0, treatment="REJECT")
    return admit_book(entry, exit_, fam, cfg)


def test_h1_A_plus_B_exact_cap_consumed():
    res = _admit(["2024-01-01 00:00", "2024-01-01 01:00"], ["A", "B"])
    assert list(res.decision) == ["ACCEPT_FULL", "ACCEPT_FULL"]
    assert abs(float(res.max_gross_heat) - 1.00) < 1e-12
    # D0: both accepted -> ECONOMIC_TARGET
    tA = translate(_event("A", "LONG", 1.0, "e1"),
                   _decision("ACCEPT_FULL", 0.70, "A", "e1"), _binding(), _snapshot())
    tB = translate(_event("B", "SHORT", 1.0, "e2"),
                   _decision("ACCEPT_FULL", 0.30, "B", "e2"), _binding(), _snapshot())
    assert tA.status == "ECONOMIC_TARGET" and tB.status == "ECONOMIC_TARGET"


def test_h1_second_A_rejected_maps_to_no_exposure():
    res = _admit(["2024-01-01 00:00", "2024-01-01 01:00"], ["A", "A"])
    assert list(res.decision) == ["ACCEPT_FULL", "REJECT_HEAT_CAP"]
    # D0: the rejected decision -> NO_EXPOSURE, zero exposure
    t = translate(_event("A", "LONG", 1.5, "e2"),
                  _decision("REJECT_HEAT_CAP", 0.0, "A", "e2"), _binding(), _snapshot())
    assert t.status == "NO_EXPOSURE"
    assert t.target_notional_account_ccy == 0.0
    assert t.one_R_budget_account_ccy == 0.0
    assert t.one_R_price_move_bps == 0.0


def test_h1_three_B_events_090_consumed():
    res = _admit(["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 02:00"],
                 ["B", "B", "B"])
    assert list(res.decision) == ["ACCEPT_FULL"] * 3
    assert abs(float(res.max_gross_heat) - 0.90) < 1e-12
    for i in range(3):
        t = translate(_event("B", "SHORT", 1.0, f"e{i}"),
                      _decision("ACCEPT_FULL", 0.30, "B", f"e{i}"),
                      _binding(), _snapshot())
        assert t.status == "ECONOMIC_TARGET"


def test_exit_release_ordering_causality():
    # an event exiting at exactly the new entry time releases heat (exit <= entry)
    res = _admit(["2024-01-01 00:00", "2024-01-01 06:00"], ["A", "B"])
    assert list(res.decision) == ["ACCEPT_FULL", "ACCEPT_FULL"]
    # overlapping A+A at 5h would exceed cap -> second rejected
    res2 = _admit(["2024-01-01 00:00", "2024-01-01 05:00"], ["A", "A"])
    assert list(res2.decision) == ["ACCEPT_FULL", "REJECT_HEAT_CAP"]


def test_same_timestamp_events_deterministic():
    # stable ordering by entry time; same-timestamp A then B both fit the cap
    res = _admit(["2024-01-01 00:00", "2024-01-01 00:00"], ["A", "B"])
    assert list(res.decision) == ["ACCEPT_FULL", "ACCEPT_FULL"]
    # D0 translation itself is deterministic: repeated calls byte-identical
    t1 = translate(_event("A", "LONG", 1.5), _decision("ACCEPT_FULL", 0.70),
                   _binding(), _snapshot())
    t2 = translate(_event("A", "LONG", 1.5), _decision("ACCEPT_FULL", 0.70),
                   _binding(), _snapshot())
    assert t1 == t2


# --- equity snapshot / no dynamic resizing ------------------------------------
def test_equity_snapshot_frozen_at_admission():
    t = translate(_event("A", "LONG", 1.5), _decision("ACCEPT_FULL", 0.70),
                  _binding(), _snapshot(equity=25000.0))
    assert t.equity_reference == 25000.0
    assert abs(t.target_notional_account_ccy - target_notional(25000.0, 0.70, 1.5)) < 1e-9


def test_no_active_position_dynamic_resizing():
    # D0 is stateless: the snapshot is the ONLY equity source. Translating the
    # same event with a different snapshot uses the supplied equity; the
    # admission decision and admitted_f never change (no revaluation).
    t1 = translate(_event("A", "LONG", 1.5), _decision("ACCEPT_FULL", 0.70),
                   _binding(), _snapshot(equity=10000.0))
    t2 = translate(_event("A", "LONG", 1.5), _decision("ACCEPT_FULL", 0.70),
                   _binding(), _snapshot(equity=50000.0))
    assert t1.admitted_f_pct == t2.admitted_f_pct == 0.70
    assert t1.status == t2.status == "ECONOMIC_TARGET"
    assert abs(t2.target_notional_account_ccy / t1.target_notional_account_ccy - 5.0) < 1e-9
    assert t1.translation_id == t2.translation_id  # same event/decision idempotency


# --- fail-closed validation ----------------------------------------------------
def test_stale_account_state_fail_closed():
    with pytest.raises(StaleAccountStateError):
        translate(_event(), _decision(), _binding(), _snapshot(staleness="STALE"))
    with pytest.raises(StaleAccountStateError):
        translate(_event(), _decision(), _binding(), _snapshot(staleness="UNKNOWN"))


def test_unknown_instrument_spec_fail_closed():
    ev = _event()
    ev = StrategyEventReference(event_id=ev.event_id, strategy_id=ev.strategy_id,
                                family=ev.family, direction=ev.direction,
                                instrument_research_identity="EURJPY",
                                entry_known_timestamp=ev.entry_known_timestamp,
                                pos_t=ev.pos_t, risk_unit_bps=ev.risk_unit_bps,
                                translation_science_version=ev.translation_science_version)
    with pytest.raises(UnknownInstrumentSpecError):
        translate(ev, _decision(), _binding(), _snapshot())


def test_account_binding_mismatch_fail_closed():
    with pytest.raises(AccountBindingMismatchError):
        translate(_event(), _decision(), _binding("acct-1"),
                  _snapshot(account_id="acct-2"))


def test_missing_equity_fail_closed():
    with pytest.raises(MissingAccountEquityError):
        translate(_event(), _decision(), _binding(), _snapshot(equity=0.0))
    with pytest.raises(MissingAccountEquityError):
        translate(_event(), _decision(), _binding(), _snapshot(equity=-5.0))


def test_unresolved_account_currency_fail_closed():
    with pytest.raises(UnresolvedAccountCurrencyError):
        translate(_event(), _decision(), _binding(), _snapshot(currency=""))


def test_invalid_pos_and_status_fail_closed():
    ev = _event(pos=0.0)
    with pytest.raises(InvalidPositionError):
        translate(ev, _decision(), _binding(), _snapshot())
    with pytest.raises(InvalidDecisionStatusError):
        translate(_event(), _decision(status="BOGUS"), _binding(), _snapshot())
    with pytest.raises(TranslationError):
        target_notional(E, 0.70, 0.0)


# --- idempotency / no duplicate exposure ---------------------------------------
def test_duplicate_event_idempotency():
    t1 = translate(_event("A", "LONG", 1.5, "EV-99"), _decision("ACCEPT_FULL", 0.70, "A", "EV-99"),
                   _binding(), _snapshot())
    t2 = translate(_event("A", "LONG", 1.5, "EV-99"), _decision("ACCEPT_FULL", 0.70, "A", "EV-99"),
                   _binding(), _snapshot())
    assert t1 == t2
    assert t1.translation_id == t2.translation_id
    assert t1.translation_id.startswith("TR-")


# --- no broker fields / purity -------------------------------------------------
def test_no_broker_fields_in_output():
    t = translate(_event(), _decision(), _binding(), _snapshot())
    fields = set(t.__dataclass_fields__.keys())
    for bad in ["broker_lot", "margin", "buying_power", "order_type", "fill_mode",
                "slippage", "broker_symbol"]:
        assert bad not in fields, f"broker field {bad} leaked into pure output"


def test_core_never_recomputes_h1_family_heat():
    d = json.loads((OUT / "CR_D0_DECISION.json").read_text(encoding="utf-8"))
    pure = d["core_is_pure"]
    assert pure["translator_recomputes_h1"] is False
    assert pure["translator_recomputes_family"] is False
    assert pure["translator_recomputes_model_heat"] is False
    # the module contains no admission logic beyond consuming status
    src = (ROOT / "src" / "capital_routing" / "translation"
           / "capital_translation_core.py").read_text(encoding="utf-8")
    assert "admit_book" not in src and "run_policy" not in src


def test_no_broker_call():
    d = json.loads((OUT / "CR_D0_DECISION.json").read_text(encoding="utf-8"))
    assert d["broker_execution_performed"] is False
    assert d["broker_authorized"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False


# --- 890-event parity through the core -----------------------------------------
def test_admission_parity_890():
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]
    assert len(df) == 890
    assert len(acc) == 826
    assert len(acc[acc["family"] == "A"]) == 371
    assert len(acc[acc["family"] == "B"]) == 455
    assert len(df[df["status"] != "ACCEPT_FULL"]) == 64
    d = json.loads((OUT / "CR_D0_DECISION.json").read_text(encoding="utf-8"))
    assert d["n_events"] == 890 and d["n_accepted"] == 826 and d["n_rejected"] == 64
    assert d["accepted_A"] == 371 and d["accepted_B"] == 455


def test_gross_parity_every_accepted_event_through_core():
    par = json.loads((OUT / "CR_D0_PARITY_890.json").read_text(encoding="utf-8"))
    assert par["gross_parity_pass"] is True
    assert par["gross_max_err"] < 1e-10
    assert par["notional_parity_pass"] is True
    rows = par["events"]
    acc = [r for r in rows if r["accepted"]]
    assert len(acc) == 826
    assert all(r["gross_abs_error"] < 1e-10 for r in acc)
    assert all(r["notional_abs_error"] < 1e-10 for r in acc)


def test_long_and_short_parity():
    par = json.loads((OUT / "CR_D0_PARITY_890.json").read_text(encoding="utf-8"))
    trans = pd.read_csv(OUT / "CR_D0_EVENT_TRANSLATIONS.csv")
    longs = trans[trans["direction"] == "LONG"]
    shorts = trans[trans["direction"] == "SHORT"]
    assert len(longs) == 432 and len(shorts) == 458
    assert longs["decision"].eq("ACCEPT_FULL").sum() == 371
    assert shorts["decision"].eq("ACCEPT_FULL").sum() == 455
    assert (par["events"][0]["gross_abs_error"] < 1e-10
            and par["events"][-1]["gross_abs_error"] < 1e-10)


def test_rejected_zero_exposure_all_64():
    rej = json.loads((OUT / "CR_D0_REJECTED_ZERO_EXPOSURE.json").read_text(encoding="utf-8"))
    assert rej["n_rejected"] == 64
    assert rej["all_no_exposure"] is True
    assert all(r["target_notional_account_ccy"] == 0.0 for r in rej["events"])
    trans = pd.read_csv(OUT / "CR_D0_EVENT_TRANSLATIONS.csv")
    rej_t = trans[trans["decision"] != "ACCEPT_FULL"]
    assert (rej_t["translation_status"] == "NO_EXPOSURE").all()
    assert (rej_t["target_notional_account_ccy"] == 0.0).all()


def test_research_net_parity_through_core():
    par = json.loads((OUT / "CR_D0_PARITY_890.json").read_text(encoding="utf-8"))
    assert par["research_net_parity_pass"] is True
    assert par["research_net_max_err"] < 1e-10
    assert par["execution_net_parity_status"] == "BROKER_DEPENDENT_UNRESOLVED"


def test_canonical_notional_stats_unchanged():
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]["notional_multiple_equity"]
    assert abs(np.percentile(acc, 50) - 1.9842) < 5e-4
    assert abs(np.percentile(acc, 95) - 7.6105) < 5e-3
    assert abs(np.percentile(acc, 99) - 16.0364) < 5e-3
    assert abs(acc.max() - 32.7663) < 5e-3
    # the core's equity-normalized targets reproduce the sealed multipliers
    trans = pd.read_csv(OUT / "CR_D0_EVENT_TRANSLATIONS.csv")
    core_acc = trans[trans["decision"] == "ACCEPT_FULL"]["target_notional_account_ccy"]
    assert abs(np.percentile(core_acc, 50) - np.percentile(acc, 50)) < 5e-4
    assert abs(np.percentile(core_acc, 95) - np.percentile(acc, 95)) < 5e-3
    assert abs(core_acc.max() - acc.max()) < 5e-3


def test_no_science_changes():
    d = json.loads((OUT / "CR_D0_DECISION.json").read_text(encoding="utf-8"))
    assert d["science_unchanged"] is True
    assert d["risk_unit_bps"] == RISK_UNIT_BPS
    assert d["risk_unit_is_hard_stop"] is False
    assert d["status"] == "PASS"
    assert d["implementation_ready"] is True
    assert d["implementation_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True
    assert d["translation_version"] == TRANSLATION_VERSION
    assert d["next_checkpoint_recommended"] == (
        "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D1")
