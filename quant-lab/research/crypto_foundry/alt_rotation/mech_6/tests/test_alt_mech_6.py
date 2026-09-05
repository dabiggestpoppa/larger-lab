#!/usr/bin/env python
"""MECH-6 integrity tests: semantic verification, not file existence.

Verifies the scientific content of each required artifact: row counts,
column presence, logical identities, and the verdict consistency chain.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]  # mech_6/
M5_ROOT = ROOT.parent / "mech_5"

SUCCESS_LABELS = {"BROAD_RISK_EXPANSION", "LARGE_ALT_ROTATION",
                  "MID_CAP_ROTATION", "ETH_BROADENING"}
FAILURE_LABELS = {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"}

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
    else:
        FAIL.append(f"{name}: {detail}")


def load_csv(name):
    return pd.read_csv(ROOT / name)


def main():
    # --- cohort reconciliation (02/04 vs MECH-5) ---
    seq5 = pd.read_csv(M5_ROOT / "15_FAILURE_SEQUENCE_MAP.csv")
    counts = load_csv("04_SEQUENCE_COUNTS.csv")
    n_events = counts.event_id.nunique()
    check("04 events == 125", n_events == 125, f"got {n_events}")
    check("04 all events match MECH-5 ledger",
          set(counts.event_id) == set(seq5.event_id))

    # --- 03 atlas ---
    panel = pd.read_parquet(ROOT / "03_MICROSTATE_EVENT_PANEL.parquet")
    check("03 panel rows == 125*10 minus OOR",
          len(panel) >= 1100, f"got {len(panel)}")
    check("03 has atom columns",
          {"canonical_state", "micro_state", "breadth_axis", "rank_axis",
           "conc_axis", "eth_axis", "btc_axis", "leadership_width"} <=
          set(panel.columns))
    check("03 horizons complete", set(panel.horizon_d) == set(
        [0, 1, 2, 3, 5, 7, 10, 14, 21, 30]))

    # --- 07 atlas: exactly 2 promoted LOCAL_SEQUENCE, panel breadth oscillation ---
    atlas = load_csv("07_LOCAL_SEQUENCE_ATLAS.csv")
    prom = atlas[atlas.classification == "LOCAL_SEQUENCE"]
    check("07 exactly 2 promoted", len(prom) == 2, f"got {len(prom)}")
    prom_seqs = set(prom.seq)
    check("07 promoted are breadth oscillation",
          prom_seqs == {"BREADTH_EXPANSION->BREADTH_FADE->BREADTH_EXPANSION",
                        "BREADTH_FADE->BREADTH_EXPANSION->BREADTH_FADE"},
          f"got {prom_seqs}")
    check("07 promoted n>=50", (prom.n_effective >= 50).all())
    check("07 promoted >=3 subperiods", (prom.n_subperiods >= 3).all())
    check("07 promoted lift>=1.25", (prom.lift >= 1.25).all())

    # --- 05/06 FDR columns present ---
    e5 = load_csv("05_SEQUENCE_BASELINE_LIFTS.csv")
    check("05 has FDR columns", {"p_fdr", "significant_fdr"} <= set(e5.columns))
    s6 = load_csv("06_SEQUENCE_SUBPERIOD_STABILITY.csv")
    check("06 has FDR + effective counts",
          {"p_fdr", "n_effective", "n_subperiods"} <= set(s6.columns))
    check("06 no NaN lifts among tested", s6.lift.notna().all())

    # --- 08 breadth lattice: all 7 questions, Q1 non-empty ---
    lat = load_csv("08_BREADTH_TRANSMISSION_LATTICE.csv")
    qs = set(lat.question)
    check("08 all questions present",
          {"Q1_first_change", "Q2_best_discriminator", "Q3_sufficiency",
           "Q4_stall_before_failure", "Q5_accel_beyond_level",
           "Q6_late_decay", "Q7_class_signature"} <= qs,
          f"missing {sorted({'Q1_first_change','Q2_best_discriminator','Q3_sufficiency','Q4_stall_before_failure','Q5_accel_beyond_level','Q6_late_decay','Q7_class_signature'} - qs)}")
    q1 = lat[lat.question == "Q1_first_change"]
    check("08 Q1 earliest >=3 coordinates", len(q1) >= 3, f"got {len(q1)}")
    check("08 Q2 level AUC > 0.7 at t0",
          float(lat[(lat.question == "Q2_best_discriminator") &
                    (lat.coordinate == "level") &
                    (lat.statistic == "auc_tp0")].value.iloc[0]) > 0.7)

    # --- 09 breadth sequence panel ---
    b9 = load_csv("09_BREADTH_SEQUENCE_ANALYSIS.csv")
    check("09 123 primary events", len(b9) == 123, f"got {len(b9)}")
    check("09 has axis/breadth/rank columns",
          {"axis_tp0", "breadth_tp0", "vel_tp0", "rank_axis_tp0"} <= set(b9.columns))

    # --- 10/11 motif refinement sample sizes ---
    e10 = load_csv("10_EARLY_SNAPBACK_REFINEMENT.csv")
    e11 = load_csv("11_BREADTH_FADE_REFINEMENT.csv")
    check("10 ES n == 28", len(e10) == 28, f"got {len(e10)}")
    check("11 BF n == 23", len(e11) == 23, f"got {len(e11)}")
    check("10 ES days_to_reentry median <= 3",
          float(e10.days_to_reentry.median()) <= 3)

    # --- 12/13/14 competing risk ---
    h12 = load_csv("12_COMPETING_RISK_HAZARDS.csv")
    c13 = load_csv("13_CUMULATIVE_INCIDENCE.csv")
    c30 = c13[c13.horizon_d == 30]
    cif_sum = c30.cumulative_incidence.sum()
    check("13 CIF sums to ~1.0 (all resolved within 30D)",
          abs(cif_sum - 1.0) < 0.01, f"sum={cif_sum:.4f}")
    cif = dict(zip(c30.cause, c30.cumulative_incidence))
    check("13 two-clock: reentry CIF > propagation CIF",
          cif.get("REENTRY", 0) > cif.get("PROPAGATION", 0) + 0.05,
          f"{cif}")
    check("13 reentry CIF ~0.416", abs(cif.get("REENTRY", 0) - 52 / 125) < 0.01)
    check("13 propagation CIF ~0.216", abs(cif.get("PROPAGATION", 0) - 27 / 125) < 0.01)
    c14 = load_csv("14_STATE_CONDITIONED_HAZARDS.csv")
    check("14 has condition/window/cause cols",
          {"condition", "window_d", "cause", "p_cause_by_window"} <= set(c14.columns))
    check("14 non-empty", len(c14) > 20)

    # --- 15 termination microsequences ---
    t15 = load_csv("15_TERMINATION_MICROSEQUENCES.csv")
    check("15 n == 27 success events", len(t15) == 27, f"got {len(t15)}")
    check("15 BREADTH_FIRST dominant", t15.termination_signature.value_counts().idxmax() == "BREADTH_FIRST")
    check("15 signatures exhaustive",
          set(t15.termination_signature) <= {"BREADTH_FIRST", "ETH_FIRST",
                                             "CONC_REBUILD_FIRST", "DISP_FIRST",
                                             "VOL_FIRST", "BTC_FIRST",
                                             "RANK_FIRST", "ABRUPT"})

    # --- 16 conditional audit ---
    c16 = load_csv("16_CONDITIONAL_LOCAL_RULE_AUDIT.csv")
    check("16 has FDR columns", {"p_fdr", "significant_fdr"} <= set(c16.columns))
    check("16 non-empty", len(c16) >= 50, f"got {len(c16)}")

    # --- 17 alpha-role registry ---
    r17 = load_csv("17_ALPHA_ROLE_REGISTRY.csv")
    check("17 has role taxonomy cols",
          {"statistic", "roles", "causal_level", "status"} <= set(r17.columns))
    no_strategy = not r17.roles.astype(str).str.contains(
        "PNL|ENTRY|EXIT_THRESHOLD|POSITION_SIZE|KELLY", case=False).any()
    check("17 no strategy/PnL role tags", no_strategy)

    # --- 18 node graph ---
    n18 = load_csv("18_NODE_EDGE_UPDATE.csv")
    check("18 nodes non-empty", len(n18) >= 20, f"got {len(n18)}")
    check("18 has node schema cols",
          {"node_id", "node_type", "causal_level", "status", "alpha_role"} <= set(n18.columns))

    # --- 19 node operations ---
    n19 = load_csv("19_NEW_NODE_MERGE_DISSOLVE.csv")
    check("19 contains promoted sequences",
          n19.node.str.contains("BREADTH_EXPANSION->BREADTH_FADE").any())
    check("19 has NEW_NODE operations",
          (n19.operation == "NEW_NODE").sum() >= 5)

    # --- 20 nulls retained ---
    n20 = load_csv("20_NULL_AND_FAILED_RESULTS.csv")
    check("20 nulls retained", len(n20) >= 100, f"got {len(n20)}")

    # --- 21/22 verdict consistency ---
    s21 = (ROOT / "21_MECH6_SUMMARY.md").read_text(encoding="utf-8")
    d22 = (ROOT / "22_MECH6_DECISION.md").read_text(encoding="utf-8")
    import re
    v22 = re.search(r"VERDICT:\s*(\S+)", d22)
    v21 = re.search(r"Verdict:\*+\s*(\S+)", s21)
    check("22 verdict present", v22 is not None)
    check("21/22 verdict vocabulary consistent",
          v21 is not None and v22 is not None and v21.group(1) == v22.group(1),
          f"21={v21.group(1) if v21 else None} 22={v22.group(1) if v22 else None}")
    check("22 human_review flag", "human_review_required = TRUE" in d22)
    check("22 no checkpoint authorization", "next_checkpoint_authorized = FALSE" in d22)

    print(f"\nMECH-6 TESTS: {len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print("  FAIL:", f)
    if FAIL:
        sys.exit(1)
    print("ALL MECH-6 INTEGRITY TESTS PASSED")


if __name__ == "__main__":
    main()
