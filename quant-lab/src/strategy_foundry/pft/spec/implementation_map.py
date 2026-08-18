"""B1 formula -> implementation mapping.

Maps every frozen A1 formula id to its planned implementation target,
its reference test location, and its fail-closed failure behavior.
The B1 builder merges this into FORMULA_REGISTER.json.
"""

from __future__ import annotations

ENGINE = "strategy_foundry.pft.engine"
TESTS = "quant-lab/tests/strategy_foundry/pft"

IMPLEMENTATION_TARGETS = {
    "A1.F01.LOG_RETURN": f"{ENGINE}.returns.log_return",
    "A1.F02.PARKINSON_14H": f"{ENGINE}.parkinson.parkinson_14h",
    "A1.F03.GAMMA_RAW": f"{ENGINE}.k2.gamma_raw",
    "A1.F04.GAMMA_SMA3": f"{ENGINE}.k2.gamma_sma3",
    "A1.F05.ACCELERATION": f"{ENGINE}.k2.acceleration",
    "A1.F06.DMD_OPERATOR": f"{ENGINE}.k1.dmd_operator",
    "A1.F07.MODE_PARTICIPATION": f"{ENGINE}.k1.mode_participation",
    "A1.F08.PHASE_DISTANCE": f"{ENGINE}.k1.phase_distance",
    "A1.F09.VR_DISTANCE": f"{ENGINE}.k3.vr_distance",
    "A1.F10.VR_CLASSIFICATION": f"{ENGINE}.k3.vr_classification",
    "A1.F11.K3_OLS": f"{ENGINE}.k3.k3_ols",
    "A1.F12.K3_ALPHA": f"{ENGINE}.k3.k3_alpha",
    "A1.F13.RV6": f"{ENGINE}.k4.rv6",
    "A1.F14.COMMUTATOR": f"{ENGINE}.k4.commutator",
    "A1.F15.CLUSTER_FSM": f"{ENGINE}.portfolio.cluster_fsm",
    "A1.F16.GROSS_CAP": f"{ENGINE}.portfolio.gross_cap",
    "A1.F17.FADE": f"{ENGINE}.portfolio.fade",
    "A1.F18.DRAWDOWN": f"{ENGINE}.portfolio.drawdown_overlay",
    "A1.F19.LEG_STOP": f"{ENGINE}.portfolio.leg_stop",
}

TEST_TARGETS = {
    "A1.F01.LOG_RETURN": f"{TESTS}/test_reference_fixtures.py::TestLogReturn",
    "A1.F02.PARKINSON_14H": f"{TESTS}/test_reference_fixtures.py::TestParkinson",
    "A1.F03.GAMMA_RAW": f"{TESTS}/test_reference_fixtures.py::TestGamma",
    "A1.F04.GAMMA_SMA3": f"{TESTS}/test_reference_fixtures.py::TestGammaSmooth",
    "A1.F05.ACCELERATION": f"{TESTS}/test_reference_fixtures.py::TestAcceleration",
    "A1.F06.DMD_OPERATOR": f"{TESTS}/test_reference_fixtures.py::TestDMD",
    "A1.F07.MODE_PARTICIPATION": f"{TESTS}/test_reference_fixtures.py::TestDMDParticipation",
    "A1.F08.PHASE_DISTANCE": f"{TESTS}/test_reference_fixtures.py::TestCircularPhase",
    "A1.F09.VR_DISTANCE": f"{TESTS}/test_reference_fixtures.py::TestVRDistance",
    "A1.F10.VR_CLASSIFICATION": f"{TESTS}/test_reference_fixtures.py::TestVRTopology",
    "A1.F11.K3_OLS": f"{TESTS}/test_reference_fixtures.py::TestK3OLS",
    "A1.F12.K3_ALPHA": f"{TESTS}/test_reference_fixtures.py::TestK3Alpha",
    "A1.F13.RV6": f"{TESTS}/test_reference_fixtures.py::TestRV6",
    "A1.F14.COMMUTATOR": f"{TESTS}/test_reference_fixtures.py::TestCommutator",
    "A1.F15.CLUSTER_FSM": f"{TESTS}/test_reference_fixtures.py::TestFSM",
    "A1.F16.GROSS_CAP": f"{TESTS}/test_reference_fixtures.py::TestGrossCap",
    "A1.F17.FADE": f"{TESTS}/test_reference_fixtures.py::TestFade",
    "A1.F18.DRAWDOWN": f"{TESTS}/test_reference_fixtures.py::TestDrawdown",
    "A1.F19.LEG_STOP": f"{TESTS}/test_reference_fixtures.py::TestLegStop",
}

FAILURE_BEHAVIOR = {
    "A1.F01.LOG_RETURN": "stale/closed slot: r=0 with stale flag; missing/NaN input -> INVALID with reason",
    "A1.F02.PARKINSON_14H": "insufficient closed bars (<14) -> INVALID with reason; zero ranges contribute 0",
    "A1.F03.GAMMA_RAW": "H==L -> gamma=0; invalid OHLC -> INVALID with reason",
    "A1.F04.GAMMA_SMA3": "insufficient history (<3) -> INVALID with reason",
    "A1.F05.ACCELERATION": "previous sigma==0 -> acceleration=0; non-finite -> 0 with reason",
    "A1.F06.DMD_OPERATOR": "no eligible mode -> w3=0, K1_VALID=false, reason; singular X -> INVALID",
    "A1.F07.MODE_PARTICIPATION": "same mode wins both -> DeltaPhi=0; no eligible mode -> w3=0",
    "A1.F08.PHASE_DISTANCE": "non-finite phase -> INVALID; result bounded [0, pi]",
    "A1.F09.VR_DISTANCE": "insufficient z-history (<6) -> INVALID with reason",
    "A1.F10.VR_CLASSIFICATION": "degenerate point cloud (all distances 0) -> NO_HOLE (mult 0)",
    "A1.F11.K3_OLS": "singular/unstable (X^T X)^-1 -> K3_OLS_VALID=false, w2=0, reason; NO pseudoinverse",
    "A1.F12.K3_ALPHA": "K3_OLS_VALID=false -> w2=0; non-finite alpha2 -> w2=0 with reason",
    "A1.F13.RV6": "fewer than six valid returns -> INVALID with reason; ddof=1 enforced",
    "A1.F14.COMMUTATOR": "insufficient history (N<20) -> alpha_D invalid, w_total=0, reason",
    "A1.F15.CLUSTER_FSM": "non-finite w_total -> neutral, W_base=[0,0,0], reason",
    "A1.F16.GROSS_CAP": "non-finite weights -> target rejected with reason; g>1 -> scale by 1/g",
    "A1.F17.FADE": "signal flip during fade -> restart from current exposure; neutral -> fade to zero",
    "A1.F18.DRAWDOWN": "DD>=0.195 -> flatten, terminal lock (manual/new-generation reset only)",
    "A1.F19.LEG_STOP": "trigger -> leg target 0 + 12-bar execution ban; signal continues",
}

FORMULA_STATUS_AFTER_B1 = "MAPPED"


def enrich_formula_register(formulas: list) -> list:
    """Return the formula register entries with B1 mapping fields attached."""
    enriched = []
    for entry in formulas:
        fid = entry["id"]
        if fid not in IMPLEMENTATION_TARGETS:
            raise KeyError(f"no implementation target registered for {fid}")
        enriched.append({
            **entry,
            "implementation_target": IMPLEMENTATION_TARGETS[fid],
            "test_target": TEST_TARGETS[fid],
            "failure_behavior": FAILURE_BEHAVIOR[fid],
            "implementation_status": FORMULA_STATUS_AFTER_B1,
        })
    return enriched
