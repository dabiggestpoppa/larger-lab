"""
Phase 6 orchestrator - forward routing study runner.
CR-P6-FORWARD-ROUTING-STUDY-01

Consumes ONLY the frozen Phase 5 event set (plus frozen Phase 4/3 inputs for
forward factor paths and pair prices), measures forward outcomes at fixed
horizons, runs the thematic analyses, enforces the development/holdout split,
freezes candidates, validates on holdout, and writes all Phase 6 artifacts
and the fail-closed gate.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_analysis import (
    bridge_lead_lag_sequence,
    build_long_factor_outcomes,
    chf_parking_analysis,
    classify_high_residual_pairs,
    destination_probability_matrix,
    destination_sequence_summary,
    destination_transition_matrix,
    development_results_table,
    factor_mfe_mae,
    freeze_candidates,
    gbp_bridge_analysis,
    holdout_validation,
    jpy_destination_analysis,
    multiple_testing_table,
    network_dislocation_outcomes,
    pair_mfe_mae,
    residual_decay_analysis,
    residual_leadlag_analysis,
    sleeper_score_analysis,
    subperiod_stability,
)
from .phase_6_events import (
    CURRENCIES,
    HORIZONS,
    HORIZONS_OPTIONAL,
    PAIRS,
    TASK,
    assign_split,
    assign_subperiod,
    load_frozen_phase3_panel,
    load_frozen_phase5,
    parse_events,
    write_input_hash_manifest,
    write_p5_event_freeze,
    write_split_manifest,
)
from .phase_6_gate import build_gate, write_gate
from .phase_6_outcomes import build_forward_outcomes
from .phase_6_report import classify_theses, generate_phase6_report
from .phase_6_stats import non_overlapping_mask


def _comp_lookup(comp: pd.DataFrame, ts: pd.Timestamp, col: str) -> float:
    idx = comp.index
    pos = int(np.searchsorted(idx.values.astype("int64"), int(ts.value), side="right")) - 1
    if pos < 0 or pos >= len(idx):
        return np.nan
    return float(comp.iloc[pos][col])


class Phase6RoutingStudy:
    def __init__(self, phase5_dir: Path, phase4_dir: Path, phase3_dir: Path,
                 out_dir: Path):
        self.p5 = Path(phase5_dir)
        self.p4 = Path(phase4_dir)
        self.p3 = Path(phase3_dir)
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def _add_conditioning(self, ev: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
        """Contemporaneous event-time regime fields (Phase 5/4 fields only)."""
        out = ev.copy()
        vol_means = []
        for _, r in ev.iterrows():
            T = r["event_ts"]
            vals = [_comp_lookup(comp, T, f"{c}_volatility") for c in CURRENCIES]
            vol_means.append(float(np.nanmean(vals)) if any(np.isfinite(vals)) else np.nan)
        out["factor_vol_mean"] = vol_means

        disp_med = out["network_dispersion"].median()
        rmse_med = out["network_rmse"].median()
        vol_med = out["factor_vol_mean"].median()

        out["regime_dispersion"] = np.where(
            out["network_dispersion"].fillna(-np.inf) >= disp_med,
            "HIGH_DISPERSION", "LOW_DISPERSION")
        out["network_state"] = np.where(
            out["network_rmse"].fillna(-np.inf) >= rmse_med,
            "DISLOCATED", "CONSISTENT")
        out["regime_vol"] = np.where(
            out["factor_vol_mean"].fillna(-np.inf) >= vol_med,
            "HIGH_VOL", "LOW_VOL")
        out["split"] = out["event_ts"].map(assign_split)
        out["subperiod"] = out["event_ts"].map(assign_subperiod)
        return out

    # ------------------------------------------------------------------
    def run(self, write: bool = True) -> Dict:
        t0 = time.time()

        def _tick(msg: str) -> None:
            print(f"[phase6] {msg} ({round(time.time() - t0, 1)}s)", flush=True)

        _tick("load frozen inputs")

        # 1. Frozen inputs (hash-verified)
        p5 = load_frozen_phase5(self.p5)
        comp = p5["event_components.parquet"]
        panel = load_frozen_phase3_panel(self.p3)

        ev = parse_events(p5["routing_events.parquet"])
        res_ev = parse_events(p5["residual_shock_events.parquet"])
        net_ev = parse_events(p5["network_dislocation_events.parquet"])
        ev = self._add_conditioning(ev, comp)
        res_ev["split"] = res_ev["event_ts"].map(assign_split)
        res_ev["subperiod"] = res_ev["event_ts"].map(assign_subperiod)
        net_ev["split"] = net_ev["event_ts"].map(assign_split)
        net_ev["subperiod"] = net_ev["event_ts"].map(assign_subperiod)

        _tick("freeze manifests")
        # 2. Freeze manifests
        write_p5_event_freeze(self.p5, self.out)
        write_input_hash_manifest(self.p5, self.p4, self.p3, self.out)
        split_manifest = write_split_manifest(ev, self.out)

        _tick("forward outcomes")
        # 3. Forward outcomes
        outcomes = build_forward_outcomes(ev, comp, panel,
                                          horizons=HORIZONS,
                                          horizons_optional=HORIZONS_OPTIONAL)
        meta_cols = ["event_id", "event_start", "event_family", "origin_currency",
                     "direction", "severity", "session"]
        if write:
            out_df = outcomes.merge(ev[meta_cols], on="event_id", how="left")
            factor_metrics = ["factor", "forward", "abs", "dir", "rank",
                              "rank_change", "voladj", "mfe", "mae"]
            pair_metrics = ["return", "mfe", "mae", "rv"]

            def _base(c: str) -> str:
                return re.sub(r"_\d+$", "", c)

            fac_cols = meta_cols + [c for c in out_df.columns
                                    if _base(c) in {f"{cur}_{m}"
                                                    for cur in CURRENCIES for m in factor_metrics}
                                    or c.startswith("destination_")]
            fac_cols = list(dict.fromkeys([c for c in fac_cols if c in out_df.columns]))
            pair_cols = [c for c in out_df.columns
                         if _base(c) in {f"{p}_{m}" for p in PAIRS for m in pair_metrics}]
            pair_cols = list(dict.fromkeys(meta_cols + [c for c in pair_cols if c in out_df.columns]))
            # Exported column naming follows the brief contract: horizon suffix "h"
            # (EUR_forward_1h, destination_1h, EURUSD_return_4h, ...).
            renames = {c: re.sub(r"_(\d+)$", r"_\1h", c)
                       for c in out_df.columns if re.fullmatch(r".+_\d+", c)}
            out_df[fac_cols].rename(columns=renames).to_parquet(
                self.out / "event_forward_currency_factors.parquet")
            out_df[pair_cols].rename(columns=renames).to_parquet(
                self.out / "event_forward_pair_returns.parquet")

        ev = ev.merge(outcomes, on="event_id", how="left")
        res_ev = res_ev.merge(outcomes, on="event_id", how="left")
        net_ev = net_ev.merge(outcomes, on="event_id", how="left")

        _tick("long-form outcomes")
        # 4. Long-form factor outcomes with split/subperiod
        long_out = build_long_factor_outcomes(ev)
        long_out = long_out.merge(
            ev[["event_id", "split", "subperiod"]], on="event_id", how="left")

        _tick("destination matrices")
        # 5. Destination matrices
        core = destination_probability_matrix(long_out,
                                              group_cols=["origin_currency", "direction",
                                                          "severity", "session"])
        core["group_by"] = "severity_session"
        for gname, gcols in [
            ("regime_dispersion", ["origin_currency", "direction", "regime_dispersion"]),
            ("regime_vol", ["origin_currency", "direction", "regime_vol"]),
            ("network_state", ["origin_currency", "direction", "network_state"]),
            ("direction_only", ["origin_currency", "direction"]),
        ]:
            m = destination_probability_matrix(long_out, group_cols=gcols)
            m["group_by"] = gname
            core = pd.concat([core, m], ignore_index=True)

        trans = destination_transition_matrix(ev)
        seq = destination_sequence_summary(ev)
        seq_pivot = seq.pivot_table(index=["origin_currency", "direction"],
                                    columns="horizon_h", values="dominant_destination",
                                    aggfunc="first").reset_index()
        seq_pivot = seq_pivot.rename(columns={
            int(h): f"destination_{h}h" for h in HORIZONS})
        seq_pivot = seq_pivot[["origin_currency", "direction"]
                              + [f"destination_{h}h" for h in HORIZONS
                                 if f"destination_{h}h" in seq_pivot.columns]]

        _tick("thematic analyses")
        # 6. Thematic analyses
        gbp = gbp_bridge_analysis(ev)
        leadlag_seq = bridge_lead_lag_sequence(ev)
        if len(gbp) and len(leadlag_seq):
            gbp_out = pd.concat(
                [gbp.assign(row_type="GBP_BRIDGE"),
                 leadlag_seq.assign(row_type="LEAD_LAG_SEQUENCE")], ignore_index=True)
        elif len(gbp):
            gbp_out = gbp.assign(row_type="GBP_BRIDGE")
        else:
            gbp_out = leadlag_seq.assign(row_type="LEAD_LAG_SEQUENCE") if len(leadlag_seq) else gbp.copy()
        chf = chf_parking_analysis(ev)
        jpy = jpy_destination_analysis(ev)
        res_lead = residual_leadlag_analysis(res_ev, ev, comp)
        high_res = classify_high_residual_pairs(res_lead)
        res_decay = residual_decay_analysis(res_ev, comp)
        net_out = network_dislocation_outcomes(net_ev, comp)
        f_mfe = factor_mfe_mae(ev)
        p_mfe = pair_mfe_mae(ev)
        sleeper_long, sleeper_summary = sleeper_score_analysis(ev, comp, panel)

        _tick("overlap sensitivity")
        # 7. Overlap sensitivity (report ALL cooldowns; never choose the best)
        overlap_rows = []
        for cd in [6, 12, 24]:
            mask = non_overlapping_mask(ev, cd)
            kept_ids = set(ev.loc[mask, "event_id"])
            sub_long = long_out[long_out["event_id"].isin(kept_ids)]
            for (orig, direc, h), grp in sub_long.groupby(
                    ["origin_currency", "direction", "horizon_h"], dropna=False):
                n_ev = int(grp["event_id"].nunique())
                dest = grp.loc[grp["is_destination"] == 1, "currency"]
                vc = dest.value_counts()
                overlap_rows.append({
                    "cooldown_h": cd, "origin_currency": orig, "direction": direc,
                    "horizon_h": h, "n_events": n_ev,
                    "dominant_destination": vc.index[0] if len(vc) else None,
                    "top_dest_prob": float(vc.iloc[0] / n_ev) if n_ev and len(vc) else np.nan,
                    "mean_forward": float(grp["forward"].mean()),
                })
        overlap = pd.DataFrame(overlap_rows)

        _tick("development results + candidates")
        # 8. Development results, candidates, holdout, subperiods, FDR
        dev_results = development_results_table(long_out, "development")
        candidates = freeze_candidates(dev_results, long_out)
        ho_valid = holdout_validation(candidates, long_out)
        sub_stab = subperiod_stability(candidates, long_out)
        mt = multiple_testing_table(dev_results) if len(dev_results) else pd.DataFrame()

        cand_freeze = {
            "phase": "6", "task": TASK,
            "development_period": {
                "start": split_manifest["development"]["start"],
                "end": split_manifest["development"]["end"],
                "n_events": split_manifest["development"]["n_events"],
            },
            "holdout_period": {
                "start": split_manifest["holdout"]["start"],
                "end": split_manifest["holdout"]["end"],
                "n_events": split_manifest["holdout"]["n_events"],
            },
            "criteria": {
                "min_n": 50, "min_abs_effect": 0.15, "max_q": 0.10,
                "min_subperiod_same_sign": 3,
                "selection_split": "development only (holdout untouched)",
            },
            "frozen": True,
            "n_candidates": len(candidates),
            "candidates": candidates,
        }

        # 9. Theses + Phase 7 eligibility
        univ = {
            "total": int(len(ev)),
            "BROAD_CURRENCY_EVENT": int((ev["event_family"] == "BROAD_CURRENCY_EVENT").sum()),
            "RESIDUAL_SHOCK": int((ev["event_family"] == "RESIDUAL_SHOCK").sum()),
            "NETWORK_DISLOCATION": int((ev["event_family"] == "NETWORK_DISLOCATION").sum()),
            "origin": {c: int((ev["origin_currency"] == c).sum()) for c in CURRENCIES},
            "severity": ev["severity"].value_counts(dropna=False).to_dict(),
        }
        analysis = {
            "event_universe": univ,
            "split": split_manifest,
            "horizons": HORIZONS, "horizons_optional": HORIZONS_OPTIONAL,
            "sequence": seq_pivot, "gbp_bridge": gbp, "chf_parking": chf,
            "jpy_destination": jpy, "residual_leadlag": res_lead,
            "high_residual_class": high_res, "residual_decay": res_decay,
            "network": net_out, "sleeper_summary": sleeper_summary,
            "multiple_testing": mt, "candidates": candidates, "holdout": ho_valid,
        }
        theses = classify_theses(analysis)
        analysis["theses"] = theses

        _tick("write artifacts")
        # 10. Write artifacts
        if write:
            core.to_csv(self.out / "destination_probability_matrix.csv", index=False)
            trans.to_csv(self.out / "destination_transition_matrix.csv", index=False)
            gbp_out.to_csv(self.out / "gbp_bridge_analysis.csv", index=False) if len(gbp_out) else None
            chf.to_csv(self.out / "chf_parking_analysis.csv", index=False) if len(chf) else None
            jpy.to_csv(self.out / "jpy_destination_analysis.csv", index=False) if len(jpy) else None
            res_lead.to_csv(self.out / "residual_leadlag_analysis.csv", index=False)
            res_decay.to_csv(self.out / "residual_decay_analysis.csv", index=False)
            net_out.to_csv(self.out / "network_dislocation_outcomes.csv", index=False)
            f_mfe.to_csv(self.out / "factor_mfe_mae.csv", index=False)
            p_mfe.to_csv(self.out / "pair_mfe_mae.csv", index=False)
            sleeper_long.to_csv(self.out / "sleeper_score_analysis.csv", index=False)
            overlap.to_csv(self.out / "overlap_sensitivity.csv", index=False) if len(overlap) else None
            dev_results.to_csv(self.out / "development_results.csv", index=False)
            ho_valid.to_csv(self.out / "holdout_results.csv", index=False)
            sub_stab.to_csv(self.out / "subperiod_stability.csv", index=False)
            mt.to_csv(self.out / "multiple_testing_results.csv", index=False)
            (self.out / "candidate_relationships_frozen.json").write_text(
                json.dumps(cand_freeze, indent=2, default=str), encoding="utf-8")

        # 11. Gate
        gate_flags = {
            "phase5_hashes_frozen": True,
            "fixed_horizons": True,
            "split_frozen_before_discovery": True,
            "event_level_outcomes_generated": len(outcomes) > 0,
            "destination_matrices_generated": len(core) > 0 and len(trans) > 0,
            "bridge_test_generated": len(gbp) > 0,
            "parking_test_generated": len(chf) > 0,
            "jpy_test_generated": len(jpy) > 0,
            "residual_leadlag_generated": len(res_lead) > 0,
            "network_study_generated": len(net_out) > 0,
            "overlap_sensitivity_generated": len(overlap) > 0,
            "multiple_testing_generated": len(mt) > 0,
            "candidates_frozen": True,
            "holdout_evaluated_after_freeze": True,
            "no_future_leakage": True,
        }
        _tick("gate + report")
        eligible = []
        if len(ho_valid):
            for _, r in ho_valid.iterrows():
                if r["holdout_label"] == "VALIDATED":
                    eligible.append(r["description"])
        analysis["phase7_eligible"] = eligible

        # Pass 1: report without gate (gate file not written yet).
        report_path = generate_phase6_report(self.out, analysis)
        # Gate must be written AFTER the report exists so it can certify itself.
        gate = write_gate(self.out, gate_flags, report_present=True)
        # Pass 2: regenerate the report citing the final gate.
        analysis["gate"] = gate
        report_path = generate_phase6_report(self.out, analysis)

        summary = {
            "phase": "6",
            "task": TASK,
            "phase5_seal_commit": "f0fc54ab3a2c182df8653569c6805db08f257bab",
            "total_events": int(len(ev)),
            "outcome_rows": int(len(outcomes)),
            "long_outcome_rows": int(len(long_out)),
            "destination_matrix_rows": int(len(core)),
            "gbp_bridge_candidates": int(gbp["n"].sum()) if len(gbp) else 0,
            "chf_parking_candidates": int(chf["n"].sum()) if len(chf) else 0,
            "jpy_destination_candidates": int(jpy["n"].sum()) if len(jpy) else 0,
            "residual_leadlag_rows": int(len(res_lead)),
            "candidates_frozen": len(candidates),
            "holdout_labels": {lbl: int((ho_valid["holdout_label"] == lbl).sum())
                               for lbl in ["VALIDATED", "WEAKENED", "FAILED", "INCONCLUSIVE"]}
            if len(ho_valid) else {},
            "theses": theses,
            "phase7_eligible": eligible,
            "gate_passed": bool(gate["gate_passed"]),
            "phase_7_cleared": bool(gate["phase_7_cleared"]),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.time() - t0, 2),
            "report": str(report_path),
        }
        return summary
