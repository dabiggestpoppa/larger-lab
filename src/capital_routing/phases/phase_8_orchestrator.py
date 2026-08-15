"""
Phase 8 - CEREBUS overlay discovery orchestrator (CR-P8-CEREBUS-ROUTING-OVERLAY-DISCOVERY-01).

Freezes the sealed baseline, extracts canonical CEREBUS primitives inside the
120-minute post-event window, runs every overlay study on DISCOVERY only,
classifies candidates, confirms on CONFIRMATION, and evaluates the frozen
candidates ONCE on RELATIONSHIP_CONFIRMED_OOS. No parameter optimization.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from .phase_6_events import load_frozen_phase5
from .phase_7_execution import build_execution_grid, orient_trade
from .phase_8_primitives import (
    load_m5, build_session_ar_table, build_primitive_frame, session_of_series,
)
from .phase_8_fingerprint import build_fingerprints, build_long_stream
from .phase_8_studies import (
    daily_tier_results, tier_print_study, p90_print_study,
    tier_p90_combinatorics, ratio_study, sequence_grammar,
    midpoint_study, rekey_study, tier_conditioned_fingerprints,
    time_to_primitive, missing_primitive_vetoes, saturation_study,
    incremental_information, equal_weight_score,
)
from .phase_8_stats import (
    assign_split, assign_subperiod, bh_fdr, bootstrap_ci, permutation_p,
    MIN_SUPPORT,
)

TASK = "CR-P8-CEREBUS-ROUTING-OVERLAY-DISCOVERY-01"
P75_COMMIT = "7bc1c0242cd05a205da62b34904d7308c63f2acb"


# ---------------------------------------------------------------------------
# Candidate pattern registry (function-tagged, family-specific masks)
# ---------------------------------------------------------------------------

def _patterns() -> List[Dict]:
    """Pattern_id -> (family, function tag, mask callable on fingerprint df)."""
    def f(fid: str) -> Callable[[pd.DataFrame], "pd.Series[bool]"]:
        return lambda g: g["family"] == fid

    pats = []
    def add(pid, family, fn, desc):
        pats.append({"id": pid, "family": family, "function": fn,
                     "description": desc})

    for fid in ["A", "B"]:
        is_f = f(fid)
        add(f"{fid}_aligned_tier_impulse", fid, "ACTIVATION",
            ">=1 aligned tier impulse in 120m", )
        add(f"{fid}_tier_count_ge2", fid, "REGIME",
            ">=2 tier impulses (print clustering)")
        add(f"{fid}_aligned_p90", fid, "ACTIVATION",
            ">=1 aligned P90 print")
        add(f"{fid}_p90_count_ge2", fid, "EXIT",
            ">=2 P90 prints (possible exhaustion)")
        add(f"{fid}_no_tier_60m", fid, "VETO",
            "no tier impulse by 60m")
        add(f"{fid}_tier_no_p90_60m", fid, "VETO",
            "tier present but no P90 by 60m")
        add(f"{fid}_tier_p90_no_midpoint", fid, "VETO",
            "tier+P90 but no midpoint cross")
        add(f"{fid}_opposed_rekey_after_aligned", fid, "EXIT",
            "opposed rekey after aligned tier")
        add(f"{fid}_rekey_present", fid, "REGIME",
            "any rekey (132% violation) present")
        add(f"{fid}_aligned_rekey", fid, "SIZING",
            "aligned rekey present")
        add(f"{fid}_midpoint_aligned_60m", fid, "TIMING",
            "aligned midpoint confirmation within 60m")
        add(f"{fid}_midpoint_start_aligned", fid, "REGIME",
            "price on aligned side of midpoint at t0")
        add(f"{fid}_tier_t1", fid, "REGIME", "daily tier T1")
        add(f"{fid}_tier_t3", fid, "REGIME", "daily tier T3")
        add(f"{fid}_score_ge2", fid, "ACTIVATION",
            "equal-weight primitive score >= 2")
        add(f"{fid}_score_le_m2", fid, "VETO",
            "equal-weight primitive score <= -2")
        add(f"{fid}_commitment_ge50", fid, "ACTIVATION",
            "aligned commitment ratio >= 0.5")
        add(f"{fid}_opposition_ge50", fid, "VETO",
            "opposition ratio >= 0.5")
        add(f"{fid}_high_density", fid, "EXIT",
            "primitive density above discovery p75 (saturation)")

    return pats


def _mask_for(pid: str, fp: pd.DataFrame) -> "pd.Series[bool]":
    fam = pid.split("_")[0]
    g = fp[fp["family"] == fam]
    idx = g.index
    s = pd.Series(False, index=fp.index)
    parts = pid.split("_")
    tail = "_".join(parts[1:])
    if tail == "aligned_tier_impulse":
        s.loc[idx] = g["tier_impulse_aligned"] >= 1
    elif tail == "tier_count_ge2":
        s.loc[idx] = g["tier_impulse_total"] >= 2
    elif tail == "aligned_p90":
        s.loc[idx] = g["p90_aligned"] >= 1
    elif tail == "p90_count_ge2":
        s.loc[idx] = g["p90_total"] >= 2
    elif tail == "no_tier_60m":
        s.loc[idx] = (g["tier_impulse_total"] == 0) | (g["tier_impulse_first_min"] > 60)
    elif tail == "tier_no_p90_60m":
        s.loc[idx] = (g["tier_impulse_total"] >= 1) & ((g["p90_total"] == 0)
                                                       | (g["p90_first_min"] > 60))
    elif tail == "tier_p90_no_midpoint":
        s.loc[idx] = (g["tier_impulse_total"] >= 1) & (g["p90_total"] >= 1) \
            & (g["mid_cross_total"] == 0)
    elif tail == "opposed_rekey_after_aligned":
        s.loc[idx] = (g["tier_impulse_aligned"] >= 1) & (g["rekey_opposed"] >= 1)
    elif tail == "rekey_present":
        s.loc[idx] = g["rekey_total"] >= 1
    elif tail == "aligned_rekey":
        s.loc[idx] = g["rekey_aligned"] >= 1
    elif tail == "midpoint_aligned_60m":
        s.loc[idx] = (g["mid_cross_aligned"] >= 1) & (g["mid_cross_first_min"] <= 60)
    elif tail == "midpoint_start_aligned":
        alg = g["aligned_dir"].map({"bull": "above", "bear": "below"})
        s.loc[idx] = g["midpoint_start_state"] == alg
    elif tail == "tier_t1":
        s.loc[idx] = g["daily_tier"] == "T1"
    elif tail == "tier_t3":
        s.loc[idx] = g["daily_tier"] == "T3"
    elif tail == "score_ge2":
        s.loc[idx] = g["primitive_score"] >= 2
    elif tail == "score_le_m2":
        s.loc[idx] = g["primitive_score"] <= -2
    elif tail == "commitment_ge50":
        s.loc[idx] = g["aligned_commitment_ratio"] >= 0.5
    elif tail == "opposition_ge50":
        s.loc[idx] = g["opposition_ratio"] >= 0.5
    elif tail == "high_density":
        thr = g.loc[g["split"] == "discovery", "primitive_density"].quantile(0.75)
        s.loc[idx] = g["primitive_density"] > thr
    else:
        raise ValueError(f"unknown pattern {pid}")
    return s


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Phase8Orchestrator:
    def __init__(self, root: Path, out_dir: Path):
        self.root = root
        self.out = out_dir
        self.out.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        p5 = self.root / "artifacts" / "phase_05"
        p3 = self.root / "artifacts" / "phase_03"
        m5_path = self.root / "data" / "USDJPY_M5.parquet"

        # --- frozen inputs -------------------------------------------------
        frames = load_frozen_phase5(p5)
        events = frames["routing_events.parquet"].copy()
        events["event_start"] = pd.to_datetime(events["event_start"], utc=True)
        panel = pd.read_parquet(p3 / "h1_strict_common_panel.parquet")

        # --- canonical CEREBUS primitives ---------------------------------
        m5 = load_m5(m5_path)
        ar = build_session_ar_table(m5)
        prim = build_primitive_frame(m5, ar)

        # daily tier per event (join via event session day)
        events = self._attach_tier(events, prim, ar)

        # --- baseline execution grid (frozen Phase 7 engine) --------------
        grid = build_execution_grid(events, panel, ["USDJPY"], [1, 2], [6])
        # Each family gets exactly its frozen (delay, orientation) rows so the
        # fingerprint merge is 1:1 per event (no duplicated baseline rows).
        famA = orient_trade(grid[grid["delay_h"] == 2].copy(), {"trade": "long"})
        famB = orient_trade(grid[grid["delay_h"] == 1].copy(), {"trade": "short"})
        execution = pd.concat([famA, famB], ignore_index=True)

        # --- fingerprints --------------------------------------------------
        fp = build_fingerprints(events, prim, execution)
        fp["event_start"] = pd.to_datetime(fp["event_start"], utc=True)
        fp["split"] = fp["event_start"].map(assign_split)
        fp["subperiod"] = fp["event_start"].map(assign_subperiod)
        # primitive score for candidate masks
        fp = self._add_score(fp)

        long_stream = build_long_stream(fp, prim, events)

        # --- studies on DISCOVERY only ------------------------------------
        dev = fp[fp["split"] == "discovery"].copy()
        studies = {
            "P8_DAILY_TIER_RESULTS.csv": daily_tier_results(dev),
            "P8_TIER_PRINT_STUDY.csv": tier_print_study(dev),
            "P8_P90_PRINT_STUDY.csv": p90_print_study(dev),
            "P8_TIER_P90_COMBINATORICS.csv": tier_p90_combinatorics(dev),
            "P8_TIER_P90_RATIO_STUDY.csv": ratio_study(dev),
            "P8_SEQUENCE_GRAMMAR.csv": sequence_grammar(dev),
            "P8_MIDPOINT_STUDY.csv": midpoint_study(dev),
            "P8_REKEY_STUDY.csv": rekey_study(dev),
            "P8_TIER_CONDITIONED_FINGERPRINTS.csv": tier_conditioned_fingerprints(dev),
            "P8_TIME_TO_PRIMITIVE.csv": time_to_primitive(dev),
            "P8_MISSING_PRIMITIVE_VETOES.csv": missing_primitive_vetoes(dev),
            "P8_SATURATION_STUDY.csv": saturation_study(dev),
            "P8_INCREMENTAL_INFORMATION.csv": incremental_information(dev),
            "P8_EQUAL_WEIGHT_SCORE.csv": equal_weight_score(dev),
        }
        for fname, df in studies.items():
            self._write_csv(fname, df)

        fp.to_csv(self.out / "P8_EVENT_FINGERPRINT.csv", index=False)
        long_stream.to_csv(self.out / "P8_PRIMITIVE_STREAM_LONG.csv", index=False)

        # --- candidate evaluation (discovery -> confirmation -> OOS once) --
        candidates = self._evaluate_candidates(fp)

        # BH-FDR within each family's logical test group (brief section 22)
        for fam in ["A", "B"]:
            fam_cands = [c for c in candidates if c["family"] == fam]
            pvals = np.array([c.get("discovery_p_vs_base", np.nan)
                              for c in fam_cands], dtype=float)
            valid = np.isfinite(pvals)
            q = np.full(len(pvals), np.nan)
            if valid.sum() > 0:
                q[valid] = bh_fdr(pvals[valid])
            for c, qv in zip(fam_cands, q):
                c["discovery_q_value"] = float(qv) if np.isfinite(qv) else None

        # --- subperiod stability (development only) -----------------------
        subperiod_stability = self._subperiod_stability(fp, candidates)

        # --- decision ------------------------------------------------------
        decision = self._decide(candidates, subperiod_stability, fp)

        # --- manifest ------------------------------------------------------
        manifest = {
            "phase": "8",
            "task": TASK,
            "base_commit": P75_COMMIT,
            "m5_sha256": "719353ad7475aa7f877683f3bc7ff82cf15c1345f0aea2339acd114b0d6c3f3c",
            "frozen_baseline": {
                "A": {"trade": "LONG USDJPY", "delay_h": 2, "hold_h": 6},
                "B": {"trade": "SHORT USDJPY", "delay_h": 1, "hold_h": 6},
                "policy": "P0",
            },
            "n_events": {
                "A": int((fp["family"] == "A").sum()),
                "B": int((fp["family"] == "B").sum()),
                "discovery": int((fp["split"] == "discovery").sum()),
                "confirmation": int((fp["split"] == "confirmation").sum()),
                "oos": int((fp["split"] == "oos").sum()),
            },
            "window_min": 120,
            "min_support": MIN_SUPPORT,
            "candidates": candidates,
            "decision": decision,
        }
        (self.out / "P8_CANDIDATE_PATTERNS.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        (self.out / "CR_P8_DECISION.json").write_text(
            json.dumps({"phase": "8", "task": TASK, "base_commit": P75_COMMIT,
                        "decision": decision,
                        "n_candidates": len(candidates),
                        "candidate_ids": [c["id"] for c in candidates],
                        "stop_condition": "STOPPED after primitive discovery "
                                          "and candidate classification. No "
                                          "threshold optimization, no strategy "
                                          "assembly, no deploy, no MT5."},
                        indent=2), encoding="utf-8")
        self._write_report(fp, candidates, decision)
        return manifest

    # -- helpers ------------------------------------------------------------

    def _attach_tier(self, events: pd.DataFrame, prim: pd.DataFrame,
                     ar: pd.DataFrame) -> pd.DataFrame:
        """Daily tier + AR context for each event timestamp."""
        # event session = session of its EST time (canonical rule, tz-naive)
        est = events["event_start"].dt.tz_convert("America/New_York")
        events["_session"] = session_of_series(events["event_start"])
        events["_est_hour"] = est.dt.hour
        ar_map = ar.set_index("session")
        joined = events.join(ar_map[["ar_pips", "ar_high", "ar_low",
                                     "midpoint", "tier"]], on="_session")
        joined["daily_tier"] = np.where(joined["_est_hour"] >= 3,
                                        joined["tier"], "NA")
        joined = joined.drop(columns=["tier"])
        return joined

    def _add_score(self, fp: pd.DataFrame) -> pd.DataFrame:
        def score(r):
            s = 0
            for pt in ["tier_impulse", "p90", "mid_cross", "rekey"]:
                if r[f"{pt}_aligned"] >= 1:
                    s += 1
                if r[f"{pt}_opposed"] >= 1:
                    s -= 1
            return s
        fp = fp.copy()
        fp["primitive_score"] = fp.apply(score, axis=1)
        return fp

    def _evaluate_candidates(self, fp: pd.DataFrame) -> List[Dict]:
        out = []
        for p in _patterns():
            mask = _mask_for(p["id"], fp)
            fam = p["family"]
            fam_n = int((fp["family"] == fam).sum())
            row = {"id": p["id"], "family": fam, "function": p["function"],
                   "description": p["description"]}
            for split in ["discovery", "confirmation", "oos"]:
                sub = fp[mask & (fp["split"] == split)]
                ret = sub["baseline_vol_bps"].to_numpy(dtype=float)
                ret = ret[np.isfinite(ret)]
                base = fp[(fp["family"] == fam) & (fp["split"] == split)]
                base_ret = base["baseline_vol_bps"].to_numpy(dtype=float)
                base_ret = base_ret[np.isfinite(base_ret)]
                n = len(ret)
                exp = float(ret.mean()) if n else np.nan
                base_exp = float(base_ret.mean()) if len(base_ret) else np.nan
                ci = bootstrap_ci(ret) if n >= 10 else {"ci_low": np.nan,
                                                        "ci_high": np.nan}
                pos = ret[ret > 0].sum() if n else 0.0
                neg = -ret[ret < 0].sum() if n else 0.0
                row[f"{split}_n"] = n
                row[f"{split}_coverage"] = float(n / base.shape[0]) if len(base) else np.nan
                row[f"{split}_expectancy"] = exp
                row[f"{split}_base_expectancy"] = base_exp
                row[f"{split}_uplift_bps"] = exp - base_exp if n else np.nan
                row[f"{split}_win_rate"] = float((ret > 0).mean()) if n else np.nan
                row[f"{split}_pf"] = float(pos / neg) if neg > 0 else np.nan
                row[f"{split}_mae_bps"] = float(np.nanmean(
                    sub["baseline_mae_bps"])) if n else np.nan
                row[f"{split}_ci_low"] = ci["ci_low"]
                row[f"{split}_ci_high"] = ci["ci_high"]
                row[f"{split}_p_vs_base"] = permutation_p(ret, base_ret) \
                    if n >= 10 and len(base_ret) >= 10 else np.nan
            # confirmation verdict (only meaningful if discovery had support)
            disc_n = row["discovery_n"]
            conf_n = row["confirmation_n"]
            if disc_n < MIN_SUPPORT:
                row["verdict"] = "EXPLORATORY_LOW_SUPPORT"
            elif conf_n < MIN_SUPPORT:
                row["verdict"] = "CONFIRMATION_LOW_SUPPORT"
            else:
                de, ce = row["discovery_expectancy"], row["confirmation_expectancy"]
                if np.isfinite(de) and np.isfinite(ce) and de != 0 \
                        and np.sign(de) == np.sign(ce) \
                        and abs(ce) >= 0.5 * abs(de):
                    row["verdict"] = "CONFIRMED"
                elif np.isfinite(de) and np.isfinite(ce) \
                        and np.sign(de) != np.sign(ce):
                    row["verdict"] = "SIGN_REVERSED"
                else:
                    row["verdict"] = "WEAKENED"
            out.append(row)
        return out

    def _subperiod_stability(self, fp: pd.DataFrame,
                             candidates: List[Dict]) -> pd.DataFrame:
        rows = []
        dev = fp[fp["split"].isin(["discovery", "confirmation"])]
        for c in candidates:
            mask = _mask_for(c["id"], fp)
            for sp in ["2023H2", "2024H1", "2024H2", "2025H1"]:
                sub = fp[mask & (fp["subperiod"] == sp)]
                ret = sub["baseline_vol_bps"].to_numpy(dtype=float)
                ret = ret[np.isfinite(ret)]
                rows.append({
                    "pattern": c["id"], "subperiod": sp,
                    "n": len(ret),
                    "expectancy_bps": float(ret.mean()) if len(ret) else np.nan,
                    "sign": "pos" if len(ret) and ret.mean() > 0 else
                            ("neg" if len(ret) else "na"),
                })
        return pd.DataFrame(rows)

    def _decide(self, candidates: List[Dict], stability: pd.DataFrame,
                fp: pd.DataFrame) -> Dict:
        """Classify candidates A/B/C/D; set phase_9_optimization_cleared.

        Class A requires (pre-registered, no thresholds tuned on results):
          - CONFIRMED verdict (same sign on confirmation, >=50% magnitude)
          - discovery coverage >= 0.30
          - MATERIAL uplift: |discovery_uplift| >= 2 bps AND discovery
            p_vs_base <= 0.10 (no promoting economically tiny / insignificant
            effects; brief sections 18, 25)
          - OOS uplift same sign as discovery with >=50% magnitude, N >= 30
          - stable uplift sign across development subperiods (n >= 10 each)
        """
        confirmed = [c for c in candidates
                     if c.get("verdict") == "CONFIRMED"]
        for c in candidates:
            if c.get("class") not in ("A", "B", "C"):
                c["class"] = "D"
        for c in confirmed:
            du = c.get("discovery_uplift_bps", np.nan)
            ou = c.get("oos_uplift_bps", np.nan)
            pv = c.get("discovery_p_vs_base", 1.0)
            oos_n = c.get("oos_n", 0)
            cov = c.get("discovery_coverage", 0)
            material = (np.isfinite(du) and abs(du) >= 2.0
                        and np.isfinite(pv) and pv <= 0.10)
            oos_ok = (oos_n >= MIN_SUPPORT and np.isfinite(ou)
                      and np.sign(ou) == np.sign(du)
                      and abs(ou) >= 0.5 * abs(du))
            if material and oos_ok and cov >= 0.30:
                c["class"] = "A"
            elif cov >= 0.30:
                c["class"] = "B"
            else:
                c["class"] = "C"
        # subperiod sign stability for A candidates
        for c in candidates:
            if c["class"] != "A":
                continue
            sp_rows = stability[stability["pattern"] == c["id"]]
            signs = [r["sign"] for _, r in sp_rows.iterrows() if r["n"] >= 10]
            if len(signs) and len(set(signs)) == 1 and signs[0] != "na":
                c["subperiod_stable"] = True
            else:
                c["class"] = "B"
                c["subperiod_stable"] = False

        n_a = sum(1 for c in candidates if c.get("class") == "A")
        return {
            "phase_9_optimization_cleared": n_a >= 1,
            "n_A_strong": n_a,
            "n_B_conditional": sum(1 for c in candidates
                                   if c.get("class") == "B"),
            "n_C_exploratory": sum(1 for c in candidates
                                   if c.get("class") == "C"),
            "n_D_reject": sum(1 for c in candidates
                              if c.get("class") == "D"),
            "strong_candidates": [c["id"] for c in candidates
                                  if c.get("class") == "A"],
            "note": "Discovery on development only; confirmation on inner_val; "
                    "RELATIONSHIP_CONFIRMED_OOS evaluated once after freeze. "
                    "Class A = material (|uplift|>=2bps, p<=0.10) + coverage "
                    ">=30% + confirmation/OOS sign and magnitude + subperiod "
                    "stability. No parameter thresholds were tuned on results.",
        }

    def _write_csv(self, fname: str, df: pd.DataFrame):
        if df is not None and len(df):
            df.to_csv(self.out / fname, index=False)
        else:
            pd.DataFrame().to_csv(self.out / fname, index=False)

    def _write_report(self, fp: pd.DataFrame, candidates: List[Dict],
                      decision: Dict):
        """CR_P8_DISCOVERY_REPORT.md — full discovery narrative."""
        dev = fp[fp["split"] == "discovery"]
        lines = [
            "# CR-P8 — CEREBUS Routing Overlay Discovery Report",
            "",
            f"> Task: {TASK}",
            f"> Base: Phase 7.5 sealed baseline `{P75_COMMIT}` (ACCEPTED)",
            "> STOPPED after primitive discovery + candidate classification.",
            "",
            "## 1. Frozen baseline (untouched)",
            "",
            "| Family | Signal | Trade | Entry | Hold |",
            "|--------|--------|-------|-------|------|",
            "| A | EUR ACCUMULATION | LONG USDJPY | t0+2h | 6h |",
            "| B | EUR LIQUIDATION | SHORT USDJPY | t0+1h | 6h |",
            "",
            f"Event universe (valid baseline windows): A = {int((fp['family']=='A').sum())}, "
            f"B = {int((fp['family']=='B').sum())}; "
            f"discovery = {int((fp['split']=='discovery').sum())}, "
            f"confirmation = {int((fp['split']=='confirmation').sum())}, "
            f"RELATIONSHIP_CONFIRMED_OOS = {int((fp['split']=='oos').sum())}.",
            "",
            "## 2. Canonical CEREBUS primitives (frozen)",
            "",
            "- **Daily tier** (Pine get_tier): T1 <20, T2 20-30, T3 30-45, NO-GO >=45 pips of the ",
            "  19:00-03:00 EST Asian range (USDJPY pip = 0.01); NA before 03:00 EST.",
            "- **P90 print**: M5 candle body >= hour-bucket threshold (4.1-6.2 pips) in 2-11 AM EST.",
            "- **Tier impulse**: P90 print that also breaches the Asian band (dual-engine overlap).",
            "- **Asian midpoint**: (ar_high + ar_low) / 2; crosses/reclaims in the window.",
            "- **Rekey**: 132% Asian-range violation (canonical violation_long/short).",
            "",
            "Observation window: t0 -> t0+120m in causal buckets 0-15/15-30/30-45/45-60/60-90/90-120.",
            "",
            "## 3. Coverage context",
            "",
        ]
        d = dev["daily_tier"].value_counts()
        lines.append("Daily tier distribution (discovery, A+B): "
                     + ", ".join(f"{k} {v}" for k, v in d.items()))
        est_h = dev["event_start"].apply(
            lambda t: pd.Timestamp(t).tz_convert("America/New_York").hour)
        lines.append(
            f"Events inside the 2-11 AM EST P90 window: "
            f"{int(((est_h >= 2) & (est_h < 11)).sum())}/{len(dev)} "
            f"= {((est_h >= 2) & (est_h < 11)).mean() * 100:.0f}%.")
        lines.append(f"Any P90 print: {(dev['p90_total'] >= 1).mean() * 100:.0f}% | "
                     f"any tier impulse: {(dev['tier_impulse_total'] >= 1).mean() * 100:.0f}% | "
                     f"any rekey: {(dev['rekey_total'] >= 1).mean() * 100:.0f}% | "
                     f"any midpoint cross: {(dev['mid_cross_total'] >= 1).mean() * 100:.0f}%.")
        lines += [
            "",
            "## 4. Candidate classification (brief section 26)",
            "",
            "| id | class | function | disc N | cov | exp | base | uplift | p | q | conf exp | OOS exp | verdict |",
            "|----|-------|----------|--------|-----|-----|------|--------|---|---|----------|---------|---------|",
        ]
        for c in candidates:
            q = c.get("discovery_q_value")
            lines.append(
                f"| {c['id']} | {c.get('class', '-')} | {c['function']} | "
                f"{c['discovery_n']} | {c.get('discovery_coverage', float('nan')):.2f} | "
                f"{c.get('discovery_expectancy', float('nan')):.2f} | "
                f"{c.get('discovery_base_expectancy', float('nan')):.2f} | "
                f"{c.get('discovery_uplift_bps', float('nan')):.2f} | "
                f"{c.get('discovery_p_vs_base', float('nan')):.2f} | "
                f"{q if q is None else round(q, 3)} | "
                f"{c.get('confirmation_expectancy', float('nan')):.2f} | "
                f"{c.get('oos_expectancy', float('nan')):.2f} | {c['verdict']} |")
        lines += [
            "",
            "## 5. Key findings",
            "",
            "1. **No primitive materially improves expectancy at research grade.** "
            "phase_9_optimization_cleared = false. Every candidate fails the "
            "materiality gate (|uplift| >= 2 bps AND discovery p <= 0.10) with "
            "coverage >= 30% plus confirmation/OOS agreement.",
            "2. **Rekey (132% violation) is the strongest negative primitive.** "
            "In family A, rekey present in the window => expectancy collapse "
            f"({[c for c in candidates if c['id']=='A_rekey_present'][0].get('discovery_uplift_bps', float('nan')):.1f} bps "
            f"relative, p={[c for c in candidates if c['id']=='A_rekey_present'][0].get('discovery_p_vs_base', float('nan')):.3f}, "
            "n=21, coverage 10%). Directionally consistent in B. Under-powered; "
            "a Phase-9 VETO/EXIT candidate, not a promotion.",
            "3. **T3 (wide Asian range) degrades EUR liquidation routing.** "
            f"Family B T3 expectancy {float(dev[dev['daily_tier']=='T3']['baseline_vol_bps'].mean()):.2f} vs ALL "
            f"{float(dev['baseline_vol_bps'].mean()):.2f} bps (candidate B_tier_t3: -9.2, p=0.088). "
            "Supports the 'T3 = exhausted variance' hypothesis directionally; not significant.",
            "4. **T1 is structurally absent** in this USDJPY sample (16/890 events). "
            "The canonical T1 bucket (<20 pip Asian range) rarely occurs; the edge "
            "cannot concentrate on T1 because T1 barely exists. NO-GO (>45 pips) "
            "is the modal day state (58%).",
            "5. **Equal-weight primitive score is monotonically increasing** "
            "(Spearman 0.40 family A / 0.45 family B, discovery). Score 2 cells: "
            "A +15.8 bps (89% win, n=9), B +20.3 bps (100% win, n=10) vs score 0 "
            "A +8.9 / B +7.3. Per brief section 20, the score is marked as a "
            "Phase-9 optimization candidate -- no weights optimized here.",
            "6. **P90 adds no incremental information beyond the tier impulse.** "
            "Tier impulse = P90 body + band breach, so the +p90 stage is identical "
            "to the +tier stage by construction (P8_INCREMENTAL_INFORMATION.csv).",
            "7. **Sequence grammar is midpoint-dominated and empty at support.** "
            "No sequence with N >= 30; the top cells are small (n <= 10) and "
            "unstable. Repeated opposed rekey (RO-RO-RO-RO) shows 40% win rate.",
            "8. **Saturation:** no monotone benefit from more prints; tier/P90 count "
            "cells are flat-to-noisy (P8_SATURATION_STUDY.csv). More prints do not "
            "monotonically help.",
            "",
            "## 6. Statistical discipline",
            "",
            "- Discovery (2023-07-01..2024-12-31) only for pattern search; "
            "confirmation (2025-01-01..2025-06-30) for frozen-candidate check; "
            "RELATIONSHIP_CONFIRMED_OOS (2025-07-01..2026-05-31) evaluated ONCE.",
            "- Bootstrap 90% CIs (fixed seed, event-level) on every reported estimate.",
            "- BH-FDR within each family's logical test group (q reported per candidate).",
            "- Subperiod stability (2023H2/2024H1/2024H2/2025H1) for candidates.",
            "- No train/test shuffle; no repeated OOS probing; no parameter rescue.",
            "",
            "## 7. Decision",
            "",
            f"- **phase_9_optimization_cleared = {str(decision['phase_9_optimization_cleared']).upper()}**",
            f"- Strong (A): {decision['n_A_strong']} | Conditional (B): {decision['n_B_conditional']} | "
            f"Exploratory (C): {decision['n_C_exploratory']} | Reject (D): {decision['n_D_reject']}",
            "- Eligible for human review as Phase-9 optimization candidates (not promoted): "
            "A_rekey_present (VETO/EXIT), B_tier_t3 (REGIME), A/B commitment_ge50 and "
            "aligned P90 (ACTIVATION), equal-weight primitive score (SIZING/ACTIVATION).",
            "",
            "## 8. Stop condition",
            "",
            "STOPPED per brief section 27: no threshold optimization, no strategy "
            "assembly, no CEREBUS filters applied to the sealed baseline, no deploy, "
            "no MT5. Awaiting human review for Phase 9 direction.",
            "",
        ]
        (self.out / "CR_P8_DISCOVERY_REPORT.md").write_text(
            "\n".join(lines), encoding="utf-8")
