"""PFT program registry — single source of truth for governance artifacts.

Species statuses, frozen A1 v2.2 author constants and the 19-formula
register are defined here and emitted into program/*.json artifacts.
Values are transcribed from SPECIFICATION_V2_2.md (frozen RAW spec).
"""

from __future__ import annotations

from .governance.identity import PROGRAM_ID, PROGRAM_VERSION, SPECIES_IDS
from .governance.parameters import Parameter, ParameterRegister

PROGRAM_BRANCH = "agent/deepers-strategy-foundry"
PROGRAM_BASE_SHA = "9f61288679eea56a298e08f718c314f2ca509bc5"
PLANNING_COMMIT_SHA = "225393631406200909cda8106f09edb2e456fee1"

# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

SPECIES_REGISTER = {
    "A0-GENESIS": {
        "name": "PFT-A0-GENESIS",
        "status": "SPECIMEN_REGISTERED",
        "description": "Original agent formulation. Preserved as historical "
                       "raw specimen; Deepers v2.2 is not retrofitted into it.",
        "raw_source": "quant-lab/research/strategy_foundry/pft/a0_genesis/spec/LINEAGE.md",
        "spec_files": [
            "quant-lab/research/strategy_foundry/pft/a0_genesis/spec/LINEAGE.md",
        ],
        "spec_status": "LINEAGE_SEALED_AT_B1",
    },
    "A1-DEEPERS": {
        "name": "PFT-A1-DEEPERS",
        "status": "FROZEN_PRIMARY_RAW_SPEC",
        "description": "Deepers Specification Closure v2.2. Primary RAW model. "
                       "Frozen: no reinterpretation, repair, or optimization.",
        "raw_source": "quant-lab/research/strategy_foundry/pft/a1_deepers_v2/SPECIFICATION_V2_2.md",
        "spec_files": [
            "quant-lab/research/strategy_foundry/pft/a1_deepers_v2/SPECIFICATION_V2_2.md",
            "quant-lab/research/strategy_foundry/pft/a1_deepers_v2/spec/SPEC_A1_V2_2.json",
        ],
        "spec_status": "FROZEN_MACHINE_SPEC_SEALED_AT_B1",
    },
    "Q0-TRANSMISSION": {
        "name": "PFT-Q0-TRANSMISSION",
        "status": "SPECIMEN_REGISTERED",
        "description": "Independent Quant Box transmission-deficit / "
                       "self-resolution model. Does not borrow information "
                       "from A1 results.",
        "raw_source": "quant-lab/research/strategy_foundry/pft/q0_transmission/spec/LINEAGE.md",
        "spec_files": [
            "quant-lab/research/strategy_foundry/pft/q0_transmission/spec/LINEAGE.md",
        ],
        "spec_status": "LINEAGE_SEALED_AT_B1",
    },
    "X1-SYNTHESIS": {
        "name": "PFT-X1-SYNTHESIS",
        "status": "NOT_AUTHORIZED",
        "description": "Hybrid synthesis. Not authorized before A0/A1/Q0 "
                       "attribution, falsification and validation.",
        "raw_source": "N/A",
        "spec_files": [],
        "spec_status": "NOT_AUTHORIZED",
    },
}

# ---------------------------------------------------------------------------
# Frozen A1 v2.2 author constants (AUTHOR_CONSTANT class)
# Transcribed from SPECIFICATION_V2_2.md sections 9-15 of the build prompt.
# ---------------------------------------------------------------------------

SPEC_REF = "SPECIFICATION_V2_2.md"


def _author(id_: str, name: str, value, source: str, unit: str = "", notes: str = "") -> Parameter:
    return Parameter(
        id=id_,
        name=name,
        value=value,
        parameter_class="AUTHOR_CONSTANT",
        source_ref=f"{SPEC_REF} ({source})",
        unit=unit,
        notes=notes,
    )


def build_parameter_register() -> ParameterRegister:
    reg = ParameterRegister()

    # Program / time (frozen RAW semantics)
    reg.add(_author("A1.PGM.BASE_INTERVAL", "base interval", "H1",
                    "Universe", notes="frozen"))
    reg.add(_author("A1.PGM.TIMEZONE", "canonical timezone", "America/New_York",
                    "Universe", notes="DST-aware"))
    reg.add(_author("A1.PGM.STATE_WINDOW", "canonical state window", 720,
                    "Universe", unit="H1 slots"))
    reg.add(_author("A1.PGM.STALE_MAX_HOURS", "max stale age before kernel disable", 2,
                    "Universe", unit="hours",
                    notes="stale>2h disables affected K1/K3 calculation"))

    # Parkinson volatility
    reg.add(_author("A1.F02.PARKINSON_WINDOW", "Parkinson rolling window", 14,
                    "Parkinson Oil Volatility", unit="H1 bars"))
    reg.add(_author("A1.F02.PARKINSON_ANNUALIZATION", "Parkinson annualization factor", 365 * 24,
                    "Parkinson Oil Volatility", unit="sqrt(hours/year)"))

    # K1 — DMD / Koopman phase
    reg.add(_author("A1.F06.DMD_LAMBDA_LOW", "eligible |lambda| lower bound", 0.95,
                    "K1", notes="0.95 < |lambda| < 1.0"))
    reg.add(_author("A1.F06.DMD_LAMBDA_HIGH", "eligible |lambda| upper bound", 1.0,
                    "K1", notes="exclusive"))
    reg.add(_author("A1.F06.DMD_PHASE_THRESHOLD", "phase activation threshold", 1.57,
                    "K1", unit="radians", notes="DeltaPhi > 1.57 activates w3"))
    reg.add(_author("A1.F06.W3_PHASE_DIVISOR", "w3 phase divisor", 2.0,
                    "K1", notes="w3 = -sign(r_I) * min(DeltaPhi/2.0, 0.35)"))
    reg.add(_author("A1.F06.W3_MAGNITUDE_CAP", "w3 magnitude cap", 0.35,
                    "K1"))

    # K2 — Brent range-asymmetry / volatility acceleration
    reg.add(_author("A1.F03.GAMMA_HL_ZERO", "gamma when H==L", 0,
                    "K2", notes="H==L -> gamma=0"))
    reg.add(_author("A1.F04.GAMMA_SMA_WINDOW", "gamma smoothing window", 3,
                    "K2", unit="H1 bars"))
    reg.add(_author("A1.F05.ACCEL_THRESHOLD", "acceleration activation threshold", 0.025,
                    "K2", notes="A_t > 0.025 required"))
    reg.add(_author("A1.F05.GAMMA_BAR_THRESHOLD", "|gamma_bar| activation threshold", 0.10,
                    "K2"))
    reg.add(_author("A1.F05.W1_LEADING_SCALE", "w1 leading scale", -0.45,
                    "K2", notes="leading negative sign intentional in v2.2"))
    reg.add(_author("A1.F05.ACCEL_CAP_DIVISOR", "acceleration cap divisor", 0.04,
                    "K2", notes="min(A_t/0.04, 1)"))

    # K3 — Vietoris-Rips topology + causal OLS
    reg.add(_author("A1.F09.VR_PATH_WINDOW", "path distance window", 6,
                    "K3", unit="H1 bars", notes="tau=0..5"))
    reg.add(_author("A1.F09.VR_MEDIAN_COEFF", "epsilon median coefficient", 0.45,
                    "K3", notes="epsilon = 0.45*median(D_ij) + 0.015*sigma_W"))
    reg.add(_author("A1.F09.VR_SIGMA_COEFF", "epsilon sigma coefficient", 0.015,
                    "K3", notes="do NOT divide sigma by oil price"))
    reg.add(_author("A1.F10.VR_PERSISTENCE_SCALE", "persistence filtration scale", 1.15,
                    "K3", notes="beta1 at 1.15*epsilon"))
    reg.add(_author("A1.F11.K3_OLS_LAG", "OLS lag window", 20,
                    "K3", unit="H1 bars", notes="current t excluded from fitting"))
    reg.add(_author("A1.F12.K3_BASE2_SCALE", "base2 scale", 0.30,
                    "K3"))
    reg.add(_author("A1.F12.K3_ALPHA2_DIVISOR", "alpha2 magnitude divisor", 0.002,
                    "K3"))
    reg.add(_author("A1.F12.K3_W2_CLIP", "w2 clip bound", 0.30,
                    "K3", notes="clip(base2*m, -0.30, +0.30)"))
    reg.add(_author("A1.F12.K3_TOPOLOGY_PERSISTENT_MULT", "persistent topology multiplier", 1.8,
                    "K3"))
    reg.add(_author("A1.F12.K3_TOPOLOGY_FRAGILE_MULT", "fragile topology multiplier", 0.6,
                    "K3"))
    reg.add(_author("A1.F12.K3_TOPOLOGY_NOHOLE_MULT", "no-hole topology multiplier", 0.0,
                    "K3"))
    reg.add(_author("A1.K3.NOON_SNAPSHOT_HOUR", "K3 classification snapshot hour", 12,
                    "K3", unit="NY hour", notes="H1 candle ending 12:00 NY"))
    reg.add(_author("A1.K3.IMPLEMENTATION_HOUR", "K3 implementation hour", 13,
                    "K3", unit="NY hour", notes="13:00 bar open"))

    # K4 — antisymmetric commutator
    reg.add(_author("A1.F14.COMMUTATOR_N", "commutator window N", 20,
                    "K4", unit="H1 bars"))
    reg.add(_author("A1.F13.RV6_WINDOW", "RV6 window", 6,
                    "K4", unit="H1 returns", notes="exactly six, ddof=1, hourly nonannualized"))
    reg.add(_author("A1.F13.RV6_DDOF", "RV6 ddof", 1,
                    "K4", notes="sample std"))
    reg.add(_author("A1.F14.COMMUTATOR_DIVISOR", "commutator divisor", 0.0005,
                    "K4", notes="w_total = clip(sign*min(|alpha_D|/0.0005,1), -1, 1)"))

    # FSM / cluster
    reg.add(_author("A1.F15.FSM_NEUTRAL_THRESHOLD", "FSM neutral threshold", 0.05,
                    "FSM", notes="|w_total| < 0.05 neutral"))
    reg.add(_author("A1.F15.CLUSTER_W3_SCALE", "cluster w3 scale", 0.5,
                    "Base Portfolio Target", notes="W_base = [w_tot*w1, w_tot*w2, w_tot*0.5*w3]"))

    # Gross cap
    reg.add(_author("A1.F16.GROSS_CAP", "gross leverage cap", 1.0,
                    "Gross Cap", unit="x NAV", notes="sum(abs(W_base)) <= 1"))

    # Fade
    reg.add(_author("A1.F17.FADE_HOUR1_RETAIN", "fade hour 1 retained fraction", 0.67,
                    "Reversal Fade"))
    reg.add(_author("A1.F17.FADE_HOUR2_FLAT", "fade hour 2 target exposure", 0.0,
                    "Reversal Fade", notes="exactly flat for the full hour"))
    reg.add(_author("A1.F17.FADE_HOUR3_RAMP", "fade hour 3 ramp to full", 1.0,
                    "Reversal Fade", notes="linear ramp"))

    # Drawdown overlay
    reg.add(_author("A1.F18.DD_ZONE1", "DD zone 1 threshold", 0.12,
                    "Drawdown Overlay", notes="below: full scale"))
    reg.add(_author("A1.F18.DD_ZONE2", "DD zone 2 threshold", 0.18,
                    "Drawdown Overlay", notes="0.12<=DD<0.18 linear scale-down over 0.06"))
    reg.add(_author("A1.F18.DD_SCALE_WINDOW", "DD scale-down width", 0.06,
                    "Drawdown Overlay", notes="(DD-0.12)/0.06"))
    reg.add(_author("A1.F18.DD_ZONE3", "DD zone 3 threshold", 0.195,
                    "Drawdown Overlay", notes="0.18<=DD<0.195: reflector -0.50"))
    reg.add(_author("A1.F18.DD_REFLECTOR", "DD reflector scale", -0.50,
                    "Drawdown Overlay"))
    reg.add(_author("A1.F18.DD_TERMINAL", "terminal DD threshold", 0.195,
                    "Drawdown Overlay", notes="DD>=0.195: flatten, strategy_terminal=true"))

    # Per-leg stop
    reg.add(_author("A1.F19.LEG_STOP_WINDOW", "leg stop lookback", 6,
                    "Per-Leg Stop", unit="H1 bars", notes="(LE_t - LE_{t-6})/NAV_t < -0.02"))
    reg.add(_author("A1.F19.LEG_STOP_TRIGGER", "leg stop trigger", -0.02,
                    "Per-Leg Stop", unit="fraction of NAV"))
    reg.add(_author("A1.F19.LEG_STOP_BAN", "leg execution ban", 12,
                    "Per-Leg Stop", unit="completed H1 bars"))

    # Research constants (lab preregistered, not author-supplied)
    reg.add(Parameter(
        id="PFT.SPLIT.DEVELOPMENT",
        name="development partition range",
        value={"start": "2020-01-01", "end": "2024-12-31"},
        parameter_class="RESEARCH_CONSTANT",
        source_ref="PROGRAM_PLAN.md (Tentative Data Split)",
        notes="Tentative; finalize at B2 on objective data-availability grounds only",
    ))
    reg.add(Parameter(
        id="PFT.SPLIT.CONFIRMATION",
        name="confirmation partition range",
        value={"start": "2025-01-01", "end": "2025-12-31"},
        parameter_class="RESEARCH_CONSTANT",
        source_ref="PROGRAM_PLAN.md (Tentative Data Split)",
        notes="Locked until explicit authorization",
    ))
    reg.add(Parameter(
        id="PFT.SPLIT.HOLDOUT",
        name="holdout partition range",
        value={"start": "2026-01-01", "end": None},
        parameter_class="RESEARCH_CONSTANT",
        source_ref="PROGRAM_PLAN.md (Tentative Data Split)",
        notes="One-use; locked until explicit authorization",
    ))
    return reg


# ---------------------------------------------------------------------------
# Formula register (19 formulas, per build prompt section 16)
# ---------------------------------------------------------------------------

FORMULA_IDS = [
    "A1.F01.LOG_RETURN",
    "A1.F02.PARKINSON_14H",
    "A1.F03.GAMMA_RAW",
    "A1.F04.GAMMA_SMA3",
    "A1.F05.ACCELERATION",
    "A1.F06.DMD_OPERATOR",
    "A1.F07.MODE_PARTICIPATION",
    "A1.F08.PHASE_DISTANCE",
    "A1.F09.VR_DISTANCE",
    "A1.F10.VR_CLASSIFICATION",
    "A1.F11.K3_OLS",
    "A1.F12.K3_ALPHA",
    "A1.F13.RV6",
    "A1.F14.COMMUTATOR",
    "A1.F15.CLUSTER_FSM",
    "A1.F16.GROSS_CAP",
    "A1.F17.FADE",
    "A1.F18.DRAWDOWN",
    "A1.F19.LEG_STOP",
]

FORMULA_REGISTER = [
    {"id": "A1.F01.LOG_RETURN", "name": "log return",
     "equation": "r_t = ln(P_t / P_{t-1}) on H1 closes; stale closed-market slot r_t = 0 (flagged)",
     "source_ref": f"{SPEC_REF} (Returns)", "implementation_status": "REGISTERED"},
    {"id": "A1.F02.PARKINSON_14H", "name": "Parkinson 14H oil volatility",
     "equation": "sigma_W = sqrt((1/(4 ln 2)) * (1/14) * sum(ln(H/L)^2, i=0..13)) * sqrt(365*24)",
     "source_ref": f"{SPEC_REF} (Parkinson Oil Volatility)", "implementation_status": "REGISTERED"},
    {"id": "A1.F03.GAMMA_RAW", "name": "raw range skew",
     "equation": "gamma = ((H-C)-(C-L))/(H-L); H==L -> 0",
     "source_ref": f"{SPEC_REF} (K2)", "implementation_status": "REGISTERED"},
    {"id": "A1.F04.GAMMA_SMA3", "name": "three-hour gamma smooth",
     "equation": "gamma_bar_t = (gamma_t + gamma_{t-1} + gamma_{t-2})/3",
     "source_ref": f"{SPEC_REF} (K2)", "implementation_status": "REGISTERED"},
    {"id": "A1.F05.ACCELERATION", "name": "volatility acceleration",
     "equation": "A_t = sigma_t/sigma_{t-1} - 1; previous sigma==0 -> A_t=0",
     "source_ref": f"{SPEC_REF} (K2)", "implementation_status": "REGISTERED"},
    {"id": "A1.F06.DMD_OPERATOR", "name": "DMD / Koopman phase operator",
     "equation": "A = Y X^+; A Phi = Phi Lambda; eligible: 0.95<|lambda|<1.0, Im(lambda)>0; "
                 "unit-L2 eigenvectors",
     "source_ref": f"{SPEC_REF} (K1)", "implementation_status": "REGISTERED"},
    {"id": "A1.F07.MODE_PARTICIPATION", "name": "mode participation assignment",
     "equation": "P_W = sum|Phi rows 1-2|; P_EC = sum|Phi rows 3-6|; lambda_W/EC = argmax "
                 "eligible; same mode -> DeltaPhi=0",
     "source_ref": f"{SPEC_REF} (K1)", "implementation_status": "REGISTERED"},
    {"id": "A1.F08.PHASE_DISTANCE", "name": "circular phase distance",
     "equation": "DeltaPhi = min(|phi_W-phi_EC|, 2pi - |phi_W-phi_EC|), bounded [0, pi]",
     "source_ref": f"{SPEC_REF} (K1)", "implementation_status": "REGISTERED"},
    {"id": "A1.F09.VR_DISTANCE", "name": "Vietoris-Rips path distance",
     "equation": "z-score H1 returns on 720-slot state; D_ij = sqrt(sum_{tau=0..5}(z_i-z_j)^2)",
     "source_ref": f"{SPEC_REF} (K3)", "implementation_status": "REGISTERED"},
    {"id": "A1.F10.VR_CLASSIFICATION", "name": "runtime topology classification",
     "equation": "epsilon = 0.45*median(D_ij) + 0.015*sigma_W; VR 2-simplices for 3-cliques, "
                 "3-simplices for 4-cliques; PERSISTENT/FRAGILE/NO_HOLE via beta1 at epsilon "
                 "and 1.15*epsilon",
     "source_ref": f"{SPEC_REF} (K3)", "implementation_status": "REGISTERED"},
    {"id": "A1.F11.K3_OLS", "name": "causal OLS expected EC distance",
     "equation": "beta = (X^T X)^-1 X^T y, y = lagged D_EC (t-1..t-20), X = [1, D_WE, D_WC] "
                 "lagged; current t excluded; singular -> K3_OLS_VALID=false, w2=0, no "
                 "pseudoinverse",
     "source_ref": f"{SPEC_REF} (K3 - Causal theoretical EC distance)",
     "implementation_status": "REGISTERED"},
    {"id": "A1.F12.K3_ALPHA", "name": "EURCAD directional alpha and sizing",
     "equation": "alpha2 = sign(r_E+r_C)*|D_EC-Dhat_EC|; base2 = 0.30*sign(alpha2)*|alpha2|/0.002; "
                 "w2 = clip(base2*mult, -0.30, +0.30), mult in {1.8, 0.6, 0.0}",
     "source_ref": f"{SPEC_REF} (K3 - EURCAD alpha / K3 sizing)",
     "implementation_status": "REGISTERED"},
    {"id": "A1.F13.RV6", "name": "six-hour EURCAD realized volatility",
     "equation": "B_t = sample_std(r_EC,t-5..r_EC,t), ddof=1, hourly, nonannualized",
     "source_ref": f"{SPEC_REF} (K4)", "implementation_status": "REGISTERED"},
    {"id": "A1.F14.COMMUTATOR", "name": "antisymmetric commutator",
     "equation": "alpha_D = (1/20) sum_{k=1..20}(A_{t-k}B_{t-k+1} - B_{t-k}A_{t-k+1}); k=1 uses "
                 "current A_t,B_t; w_total = clip(sign(alpha_D)*min(|alpha_D|/0.0005,1), -1, 1)",
     "source_ref": f"{SPEC_REF} (K4)", "implementation_status": "REGISTERED"},
    {"id": "A1.F15.CLUSTER_FSM", "name": "cluster state machine and base weights",
     "equation": "neutral |w_total|<0.05; long >= +0.05; short <= -0.05; "
                 "W_base = [w_tot*w1, w_tot*w2, w_tot*0.5*w3] else zeros",
     "source_ref": f"{SPEC_REF} (FSM / Base Portfolio Target)",
     "implementation_status": "REGISTERED"},
    {"id": "A1.F16.GROSS_CAP", "name": "gross leverage cap",
     "equation": "g = sum(abs(W_base)); if g>1: W_cap = W_base/g else W_cap = W_base; cap 1.0x NAV",
     "source_ref": f"{SPEC_REF} (Gross Cap)", "implementation_status": "REGISTERED"},
    {"id": "A1.F17.FADE", "name": "reversal fade",
     "equation": "sign reversal: hour1 67% retained, hour2 exactly flat, hour3 linear ramp to "
                 "100%; re-flip restarts fade from current exposure; neutral fades to zero",
     "source_ref": f"{SPEC_REF} (Reversal Fade)", "implementation_status": "REGISTERED"},
    {"id": "A1.F18.DRAWDOWN", "name": "drawdown overlay",
     "equation": "DD = 1 - NAV/max NAV; zones <0.12 full, 0.12-0.18 linear, 0.18-0.195 reflector "
                 "-0.50, >=0.195 terminal flatten",
     "source_ref": f"{SPEC_REF} (Drawdown Overlay)", "implementation_status": "REGISTERED"},
    {"id": "A1.F19.LEG_STOP", "name": "per-leg stop",
     "equation": "(LE_t - LE_{t-6})/NAV_t < -0.02 -> leg target 0, 12-bar execution ban; "
                 "signal continues; rolling clock not reset by resizing",
     "source_ref": f"{SPEC_REF} (Per-Leg Stop)", "implementation_status": "REGISTERED"},
]


def species_register_dict() -> dict:
    return {
        "schema_version": "1.0",
        "program_id": PROGRAM_ID,
        "program_version": PROGRAM_VERSION,
        "species": SPECIES_REGISTER,
        "registered_species_ids": sorted(SPECIES_IDS),
    }


def formula_register_dict() -> dict:
    return {
        "schema_version": "1.0",
        "program_id": PROGRAM_ID,
        "formula_count": len(FORMULA_REGISTER),
        "formulas": FORMULA_REGISTER,
    }
