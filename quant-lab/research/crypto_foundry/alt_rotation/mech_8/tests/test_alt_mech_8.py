#!/usr/bin/env python
"""MECH-8 semantic integrity tests — verify content, not just file existence."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name} {detail}")


# ---- required files exist ----
REQUIRED = [
    "01_PREREGISTRATION.md", "02_HARMONIZED_EVENT_SCHEMA.md",
    "03_ISOLATED_DOWN_PRE30_CONTEXT.parquet",
    "04_ISOLATED_DOWN_EFFECT_CURVES.csv",
    "05_ISOLATED_DOWN_PRE_EVENT_SEQUENCE_ATLAS.csv",
    "06_BRD_DISP_4STATE_TRANSITION_MATRIX.csv",
    "07_BRD_DISP_STATE_AGE.csv",
    "08_HH_FULL_LIFECYCLE.csv",
    "09_HH_TRANSITION_LATTICE.csv",
    "10_BREADTH_ARCHITECTURE_COMPONENTS.csv",
    "11_BREADTH_ARCHITECTURE_CLASSES.csv",
    "12_BREADTH_LEVEL_VS_ARCHITECTURE_AUDIT.csv",
    "13_PRICE_RANK_HEALTH_MATRIX.csv",
    "14_PRICE_RANK_TEMPORAL_ORDER.csv",
    "15_FAILED_RECOVERY_STRESS_RESPONSE.csv",
    "16_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv",
    "17_SHMC_SHHM_FIELD_RECHECK.csv",
    "18_VOLATILITY_PARKED_ROLE_CHECK.csv",
    "19_AGENT1_AGENT2_DEFINITION_RECONCILIATION.csv",
    "20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet",
    "20b_CROSS_AGENT_FIELD_CONTEXT_MECH8_SCHEMA.md",
    "21_DEAD_SUBTLE_NODE_AUDIT.csv",
    "22_PROMOTE_MERGE_DISSOLVE.csv",
    "23_NULL_AND_FAILED_RESULTS.csv",
    "24_MECH8_SUMMARY.md",
    "25_MECH8_DECISION.md",
]
for f in REQUIRED:
    check(f"exists:{f}", (OUT / f).exists())

# ---- 03: pre30 panel semantics ----
p30 = pd.read_parquet(OUT / "03_ISOLATED_DOWN_PRE30_CONTEXT.parquet")
check("03 non-empty", len(p30) > 1000, f"rows={len(p30)}")
check("03 has lags", set(p30["lag_d"].unique()) == set([-30, -21, -14, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10, 14]),
      f"lags={sorted(p30['lag_d'].unique())}")
check("03 isolated-down only",
      set(p30["family"].unique()) == {"ISOLATED_DOWNSIDE_EXTREME"})
check("03 outcome col present", "price_outcome" in p30.columns)
check("03 pre_rank_state present", "pre_rank_state" in p30.columns)
# 03 is the analysis panel (legitimately carries outcome cols for classification);
# the no-leakage requirement applies to the cross-agent EXPORT (20).

# ---- 04: effect curves ----
e4 = pd.read_csv(OUT / "04_ISOLATED_DOWN_EFFECT_CURVES.csv")
check("04 non-empty", len(e4) > 100, f"rows={len(e4)}")
check("04 has p_fdr", "p_fdr" in e4.columns and e4["p_fdr"].notna().all())
check("04 finite p", np.isfinite(e4["ranksum_p"]).all() and (e4["ranksum_p"] > 0).all())
# consistency: rank_depth_rel pre-event signal exists (raw p < 0.05 at -21)
r21 = e4[(e4["variable"] == "rank_depth_rel") & (e4["lag_d"] == -21)]
check("04 rank_depth_rel -21D raw sig", len(r21) > 0 and r21["ranksum_p"].iloc[0] < 0.05,
      f"p={r21['ranksum_p'].iloc[0] if len(r21) else 'NA'}")
# honest null: dispersion -14D should NOT be FDR-sig (documented correction vs M7)
d14 = e4[(e4["variable"] == "top500_dispersion_30d") & (e4["lag_d"] == -14)]
check("04 disp -14D not FDR-sig", len(d14) == 0 or d14["p_fdr"].iloc[0] >= 0.1,
      f"q={d14['p_fdr'].iloc[0] if len(d14) else 'NA'}")

# ---- 05: sequence atlas ----
s5 = pd.read_csv(OUT / "05_ISOLATED_DOWN_PRE_EVENT_SEQUENCE_ATLAS.csv")
check("05 non-empty", len(s5) > 5, f"rows={len(s5)}")
check("05 has p_fdr", "p_fdr" in s5.columns)

# ---- 06: transition matrix ----
t6 = pd.read_csv(OUT / "06_BRD_DISP_4STATE_TRANSITION_MATRIX.csv")
check("06 non-empty", len(t6) >= 12, f"rows={len(t6)}")
cells = set(t6["from"]) | set(t6["to"])
check("06 4 cells present", len(cells) == 4, f"cells={sorted(cells)}")
check("06 probabilities valid (sums may be <1 where low-n transitions dropped)",
      all(g["p"].between(0, 1).all() and g["p"].sum() <= 1.0 + 1e-9 for _, g in t6.groupby("from")))
# HH persistence should be highest (MECH-7: HH most persistent)
hh_diag = t6[(t6["from"] == "HIGH_BREADTH_HIGH_DISP") & (t6["to"] == "HIGH_BREADTH_HIGH_DISP")]
ll_diag = t6[(t6["from"] == "LOW_BREADTH_LOW_DISP") & (t6["to"] == "LOW_BREADTH_LOW_DISP")]
check("06 HH most persistent",
      len(hh_diag) > 0 and len(ll_diag) > 0 and
      hh_diag["p"].iloc[0] >= ll_diag["p"].iloc[0])

# ---- 07: state age ----
a7 = pd.read_csv(OUT / "07_BRD_DISP_STATE_AGE.csv")
check("07 non-empty", len(a7) > 10, f"rows={len(a7)}")
check("07 age buckets", set(a7["age_bucket"]) <= {"DAY_1", "DAY_2_3", "DAY_4_7", "DAY_8_14", "DAY_15_PLUS"})
# HH state age: fwd7_prop should increase with age (maturity effect)
hh = a7[a7["cell"] == "HIGH_BREADTH_HIGH_DISP"].sort_values("age_bucket")
if len(hh) >= 3:
    order = {"DAY_1": 1, "DAY_2_3": 2, "DAY_4_7": 3, "DAY_8_14": 4, "DAY_15_PLUS": 5}
    hh["_o"] = hh["age_bucket"].map(order)
    hh = hh.sort_values("_o")
    check("07 HH fwd7_prop rises with age", hh["fwd7_prop"].is_monotonic_increasing or
          (hh["fwd7_prop"].iloc[-1] > hh["fwd7_prop"].iloc[0]))

# ---- 08/09: HH lifecycle ----
l8 = pd.read_csv(OUT / "08_HH_FULL_LIFECYCLE.csv")
check("08 non-empty", len(l8) > 5, f"rows={len(l8)}")
check("08 has episode counts", "n_episodes" in l8.columns and l8["n_episodes"].sum() > 100)

# ---- 10/11: architecture ----
c10 = pd.read_csv(OUT / "10_BREADTH_ARCHITECTURE_COMPONENTS.csv")
check("10 non-empty", len(c10) > 50, f"rows={len(c10)}")
check("10 cohorts", set(c10["cohort"]) == {"rank_layer", "age", "liquidity", "vol", "rank_health", "move_magnitude"},
      f"cohorts={sorted(c10['cohort'].unique())}")
c11 = pd.read_csv(OUT / "11_BREADTH_ARCHITECTURE_CLASSES.csv")
check("11 classes exist", len(c11) >= 1, f"rows={len(c11)}")
if len(c11):
    check("11 classes >=50 days", c11["n_days"].min() >= 50)
    check("11 classes >=3 subperiods", c11["n_subperiods"].min() >= 3)

# ---- 12: level vs architecture ----
x12 = pd.read_csv(OUT / "12_BREADTH_LEVEL_VS_ARCHITECTURE_AUDIT.csv")
check("12 non-empty", len(x12) >= 8, f"rows={len(x12)}")
m0 = x12[x12["model"] == "M0_level"]
check("12 M0 present", len(m0) == 1)
if len(x12):
    comps = x12[x12["model"] != "M0_level"]
    # breadth level dominates: no composition block should beat level by a lot on AUC
    check("12 level dominant (no comp delta_auc > +0.03)",
          comps["delta_auc"].max() < 0.03, f"max delta_auc={comps['delta_auc'].max()}")

# ---- 13/14: price-rank health ----
m13 = pd.read_csv(OUT / "13_PRICE_RANK_HEALTH_MATRIX.csv")
check("13 non-empty", len(m13) >= 10, f"rows={len(m13)}")
for rs in ["RANK_IMPROVING", "RANK_DETERIORATING"]:
    sub = m13[m13["pre_rank_state"] == rs]
    check(f"13 {rs} present", len(sub) >= 4)
det = m13[(m13["pre_rank_state"] == "RANK_DETERIORATING") & (m13["cross_state"] != "TOTAL")]
check("13 det rows non-empty", len(det) >= 4)
# key: RANK_DETERIORATING has price-recovery/rank-decay population
prd = m13[(m13["pre_rank_state"] == "RANK_DETERIORATING") & (m13["cross_state"] == "PRICE_RECOVERY_RANK_DECAY")]
check("13 price-recover/rank-decay population exists", len(prd) > 0 and prd["n"].iloc[0] > 50,
      f"n={prd['n'].iloc[0] if len(prd) else 'NA'}")

o14 = pd.read_csv(OUT / "14_PRICE_RANK_TEMPORAL_ORDER.csv")
check("14 non-empty", len(o14) > 800, f"rows={len(o14)}")
check("14 has price_recovery_day", "price_recovery_day" in o14.columns)

# ---- 15: stress response ----
s15 = pd.read_csv(OUT / "15_FAILED_RECOVERY_STRESS_RESPONSE.csv")
check("15 non-empty", len(s15) >= 1, f"rows={len(s15)}")
if len(s15):
    check("15 has response cols", "p_responds" in s15.columns and "p_rank_recovers" in s15.columns)

# ---- 16: liquidity ----
l16 = pd.read_csv(OUT / "16_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv")
check("16 non-empty", len(l16) >= 1, f"rows={len(l16)}")
check("16 has perm_p", "perm_p" in l16.columns and (l16["perm_p"] > 0).all(),
      "finite-sample perm p > 0")
if len(l16):
    check("16 perm p not zero", (l16["perm_p"].fillna(1.0) >= 1 / (300 + 1) - 1e-12).all())

# ---- 17: SHMC/SHHM ----
s17 = pd.read_csv(OUT / "17_SHMC_SHHM_FIELD_RECHECK.csv")
check("17 has 2 groups", len(s17) == 2, f"rows={len(s17)}")
if len(s17) == 2:
    check("17 reversal p present", "reversal_ranksum_p" in s17.columns)

# ---- 18: volatility ----
v18 = pd.read_csv(OUT / "18_VOLATILITY_PARKED_ROLE_CHECK.csv")
check("18 non-empty", len(v18) >= 4, f"rows={len(v18)}")

# ---- 19: reconciliation ----
r19 = pd.read_csv(OUT / "19_AGENT1_AGENT2_DEFINITION_RECONCILIATION.csv")
check("19 non-empty", len(r19) >= 4, f"rows={len(r19)}")
check("19 has verdicts", "verdict" in r19.columns and r19["verdict"].notna().all())

# ---- 20: cross-agent export ----
e20 = pd.read_parquet(OUT / "20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet")
check("20 non-empty", len(e20) > 100000, f"rows={len(e20)}")
check("20 keys", {"event_id", "asset_id", "date"} <= set(e20.columns))
check("20 no target leakage",
      not any("fwd" in c for c in e20.columns if c not in ["event_id"]))
check("20 has lagged coords", any(c.endswith("_lag-14") for c in e20.columns))
check("20b schema exists", (OUT / "20b_CROSS_AGENT_FIELD_CONTEXT_MECH8_SCHEMA.md").exists())

# ---- 21-23 ----
n21 = pd.read_csv(OUT / "21_DEAD_SUBTLE_NODE_AUDIT.csv")
check("21 non-empty", len(n21) >= 8, f"rows={len(n21)}")
n22 = pd.read_csv(OUT / "22_PROMOTE_MERGE_DISSOLVE.csv")
check("22 non-empty", len(n22) >= 8, f"rows={len(n22)}")
n23 = pd.read_csv(OUT / "23_NULL_AND_FAILED_RESULTS.csv")
check("23 non-empty", len(n23) >= 5, f"rows={len(n23)}")

# ---- summary/decision consistency ----
s24 = (OUT / "24_MECH8_SUMMARY.md").read_text(encoding="utf-8")
s25 = (OUT / "25_MECH8_DECISION.md").read_text(encoding="utf-8")
check("24 verdict", "PASS_MECH8_FIELD_STATE_DEEPENING" in s24)
check("25 verdict", "PASS_MECH8_FIELD_STATE_DEEPENING" in s25)
check("24 human review", "human_review_required = TRUE" in s24)
check("25 no strategy", "NO STRATEGY" in s25.upper())
ver = json.loads((OUT / "_verdicts.json").read_text())
check("verdicts json", ver.get("verdict") == "PASS_MECH8_FIELD_STATE_DEEPENING")
for ws in ["ws1_pre30", "ws2_effect_curves", "ws3_transition_matrix", "ws8_price_rank",
           "ws13_reconcile", "ws15_export"]:
    check(f"verdicts {ws}", ver.get(ws) == "COMPLETE")

print(f"\n{FAIL} failures, {PASS} passed")
sys.exit(1 if FAIL else 0)
