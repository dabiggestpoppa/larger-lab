"""
Phase 7 - orchestrator. Runs the whole routing-translation study and writes
every artifact listed in brief section 9.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_events import load_frozen_phase3_panel, load_frozen_phase5
from .phase_7_analysis import (
    basket_surface,
    entry_delay_surface,
    excursion_geometry,
    mirrored_symmetry,
    pair_space_comparison,
    plateau_analysis,
)
from .phase_7_baseline import baseline_csv
from .phase_7_execution import build_execution_grid, equal_risk_basket, orient_trade
from .phase_7_families import (
    FAMILIES,
    SPLIT,
    build_families_json,
    evaluate_static_criteria,
    load_phase6_evidence,
)
from .phase_7_gate import build_alpha_gate, write_alpha_gate
from .phase_7_report import generate_phase7_report, write_decision

TASK = "CR-P7-ROUTING-TRANSLATION-01"


class Phase7RoutingTranslation:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.phase3 = self.root / "artifacts" / "phase_03"
        self.phase5 = self.root / "artifacts" / "phase_05"
        self.phase6 = self.root / "artifacts" / "phase_06"
        self.out = self.root / "artifacts" / "phase_07"
        self.out.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        t0 = time.time()
        steps = {}

        # ---- load frozen inputs ----
        print("[p7] load frozen inputs")
        ev = load_frozen_phase5(self.phase5)["routing_events.parquet"]
        panel = load_frozen_phase3_panel(self.phase3)
        p6ev = load_phase6_evidence(self.phase6)

        # ---- families + static gate ----
        print("[p7] freeze families + static gate")
        families_json = build_families_json(self.phase6, self.out)

        # ---- execution grid per family ----
        print("[p7] build execution grids")
        grids, baskets = {}, {}
        for fid, fam in FAMILIES.items():
            fam_events = ev[
                (ev["origin_currency"] == fam["origin"])
                & (ev["direction"] == fam["direction"])
            ]
            holds = fam["hold_candidates"]
            g = build_execution_grid(fam_events, panel, fam["pairs"],
                                     [0, 1, 2, 3, 4], holds)
            g = orient_trade(g, fam)
            b = equal_risk_basket(g, fam["basket_pairs"])
            grids[fid] = g
            baskets[fid] = b
            print(f"  family {fid}: {len(fam_events)} events, {len(g)} exec rows, "
                  f"{len(b)} basket rows")

        # ---- analysis studies ----
        print("[p7] pair space / delay surfaces / excursions / symmetry")
        pair_space, delay_surfaces, excursions = {}, {}, {}
        decisions = {"plateaus": {}, "configs": {}, "validation": {}}
        for fid, fam in FAMILIES.items():
            g = grids[fid]
            pair_space[fid] = pair_space_comparison(g, fam, split="inner_sel")
            # delay surface on all oriented rows (per split)
            delay_surfaces[fid] = entry_delay_surface(g, fam)
            excursions[fid] = excursion_geometry(g, fam, split="inner_sel")
            plateau = plateau_analysis(delay_surfaces[fid], fam, split="inner_sel")
            decisions["plateaus"][fid] = plateau

        # basket delay surfaces
        for fid in FAMILIES:
            if len(baskets[fid]):
                bsurf = basket_surface(baskets[fid], FAMILIES[fid])
                delay_surfaces[f"{fid}_BASKET"] = bsurf

        symmetry = mirrored_symmetry(grids["A"], grids["B"], FAMILIES["A"],
                                     FAMILIES["B"], split="inner_sel")

        # ---- alpha promotion gate (static + criterion 6) ----
        print("[p7] alpha promotion gate")
        gates = []
        for fid, fam in FAMILIES.items():
            static = evaluate_static_criteria(fam, p6ev["holdout"],
                                              p6ev["overlap"], p6ev["factors"])
            static["_family_id"] = fid
            gate = build_alpha_gate(static, decisions["plateaus"][fid],
                                    delay_surfaces[fid])
            gates.append(gate)
        alpha_gate = {
            "phase": "7", "task": TASK, "gate": "ALPHA_PROMOTION_GATE",
            "families": gates,
        }
        write_alpha_gate(gates, self.out)

        # ---- baseline configs: frozen from inner_sel plateau, no rescue ----
        print("[p7] baselines")
        baseline_configs = {}
        for fid in FAMILIES:
            pl = decisions["plateaus"][fid]
            d = pl.get("recommended_delay", 0)
            h = pl.get("recommended_hold")
            if h is None:
                # fall back to the family's validated horizon (no plateau)
                h = FAMILIES[fid]["horizons"][0]
                d = 0
            # pair: best routing efficiency on inner_sel among candidates
            ps = pair_space[fid]
            if ps is not None and len(ps):
                best = ps[ps["hold_h"] == h].sort_values(
                    "routing_efficiency", ascending=False)
                pair = best.iloc[0]["pair"] if len(best) else FAMILIES[fid]["pairs"][0]
            else:
                pair = FAMILIES[fid]["pairs"][0]
            baseline_configs[fid] = {"delay_h": int(d), "hold_h": int(h), "pair": str(pair)}

        baselines = {}
        for fid, fam in FAMILIES.items():
            cfg = baseline_configs[fid]
            g = grids[fid]
            if cfg["pair"] == "BASKET":
                g = baskets[fid]
            bl = baseline_csv(g, fam, cfg["delay_h"], cfg["hold_h"], cfg["pair"])
            baselines[fid] = bl
            decisions["configs"][fid] = cfg
        # combined output files per brief section 9
        eur_jpy = pd.concat([baselines["A"], baselines["B"]], ignore_index=True)
        eur_jpy.to_csv(self.out / "P7_EUR_JPY_BASELINE_RESULTS.csv", index=False)
        baselines["P7_EUR_JPY_BASELINE"] = eur_jpy
        jpy_chf = baselines["C"]
        jpy_chf.to_csv(self.out / "P7_JPY_CHF_BASELINE_RESULTS.csv", index=False)
        baselines["P7_JPY_CHF_BASELINE"] = jpy_chf

        # ---- write CSVs ----
        print("[p7] write artifacts")
        for fid, df in pair_space.items():
            if df is not None and len(df):
                df.to_csv(self.out / "P7_PAIR_SPACE_COMPARISON.csv", index=False)
                break
        # combined delay surface
        surf_rows = []
        for fid in FAMILIES:
            surf_rows.append(delay_surfaces[fid])
        pd.concat(surf_rows, ignore_index=True).to_csv(
            self.out / "P7_ENTRY_DELAY_SURFACE.csv", index=False)
        exc_rows = []
        for fid in FAMILIES:
            if excursions[fid] is not None and len(excursions[fid]):
                exc_rows.append(excursions[fid])
        pd.concat(exc_rows, ignore_index=True).to_csv(
            self.out / "P7_EXCURSION_GEOMETRY.csv", index=False)
        if symmetry is not None and len(symmetry):
            symmetry.to_csv(self.out / "P7_MIRRORED_SYMMETRY.csv", index=False)

        # ---- gate status + validation summary ----
        promoted = [g for g in gates if g["promoted"]]
        decisions["gate_status"] = "PASS" if len(promoted) == len(gates) else "PARTIAL"

        # validation: untouched-period results per family
        validation = {}
        for fid in FAMILIES:
            bl = baselines[fid]
            if bl is not None and len(bl):
                unt = bl[bl["split"] == "untouched"]
                validation[fid] = {
                    "untouched_n_trades": int(unt["n_trades"].iloc[0]) if len(unt) else 0,
                    "untouched_expectancy_bps": float(unt["expectancy_bps"].iloc[0]) if len(unt) else None,
                    "untouched_win_rate": float(unt["win_rate"].iloc[0]) if len(unt) else None,
                }
        decisions["validation"] = validation
        decisions["notes"] = {
            "validation_policy": "Phase 6 holdout (2025-07..2026-05) used ONCE after rules "
                                 "frozen on nested inner_sel/inner_val within dev.",
            "no_parameter_rescue": True,
            "no_cerebus": True,
            "no_deploy": True,
        }

        # ---- report ----
        print("[p7] report + decision")
        report_baselines = {
            k: v for k, v in baselines.items()
            if k.startswith("P7_EUR_JPY_BASELINE") or k.startswith("P7_JPY_CHF_BASELINE")
        }
        report = generate_phase7_report(
            families_json, alpha_gate, pair_space, delay_surfaces,
            excursions, symmetry, report_baselines, decisions)
        (self.out / "PHASE_7_STRATEGY_STUDY.md").write_text(report, encoding="utf-8")
        write_decision(alpha_gate, decisions, report_baselines, self.out)

        elapsed = time.time() - t0
        print(f"=== PHASE 7 SUMMARY === elapsed {elapsed:.1f}s")
        print(f"gate_status: {decisions['gate_status']}")
        for g in gates:
            print(f"  {g['family']}: promoted={g['promoted']}")
        print(f"configs: {json.dumps(decisions['configs'])}")
        print(f"validation: {json.dumps(validation)}")
        return {
            "gate_status": decisions["gate_status"],
            "promoted": [g["family"] for g in gates if g["promoted"]],
            "configs": decisions["configs"],
            "validation": validation,
            "elapsed_seconds": elapsed,
        }
