"""
Phase 7 - alpha promotion gate (brief section 1).

Combines the static criteria (1-5) computed in phase_7_families with criterion 6
(no dependence on one exact horizon), which needs the Phase 7 execution plateau
analysis. Family C (single validated horizon) is assessed via the hold-sweep:
if neighbors at 36h/60h show the same sign as 48h on inner_sel, the response is
a plateau rather than an isolated horizon.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_7_families import FAMILIES, HOLDOUT_N_MIN


def evaluate_criterion6(family: Dict, plateau: Dict, delay_surface: pd.DataFrame,
                        family_id: Optional[str] = None) -> Dict:
    """
    No dependence on one exact horizon.
    - Families A/B: >= 2 validated adjacent horizons exist by construction
      (checked from the family definition) AND the execution plateau has >= 2
      adjacent positive holds.
    - Family C: hold-sweep plateau across 24..72h with the 48h response embedded
      in a same-sign neighborhood on inner_sel.
    """
    fam_id = family_id or family.get("family_id", "")
    horizons = family["horizons"]
    multi_horizon_definition = len(horizons) >= 2
    plateau_ok = bool(plateau and plateau.get("plateaus"))

    if fam_id == "C":
        # hold-sweep sign coherence around 48h
        sel = delay_surface[(delay_surface["split"] == "inner_sel") &
                            (delay_surface["delay_h"] == 0)]
        sub = sel[sel["hold_h"].isin([36, 48, 60])]
        if len(sub) == 0:
            return {"pass": False, "detail": "no hold-sweep rows for Family C"}
        signs = sub["mean_net_bps"]
        coherent = bool((signs > 0).all() or (signs < 0).all())
        return {
            "pass": coherent,
            "detail": "36/48/60h same sign on inner_sel"
            if coherent else "hold-sweep sign not coherent",
            "holds_36_48_60_mean_net_bps": signs.round(4).tolist(),
        }
    return {
        "pass": bool(multi_horizon_definition and plateau_ok),
        "detail": f"{len(horizons)} validated horizons; "
                  f"{'execution plateau found' if plateau_ok else 'no execution plateau'}",
        "multi_horizon_definition": multi_horizon_definition,
        "plateau_found": plateau_ok,
    }


def build_alpha_gate(static: Dict, plateau: Dict,
                     delay_surface: pd.DataFrame) -> Dict:
    """
    Assemble the ALPHA_PROMOTION_GATE for one family. static comes from
    phase_7_families.evaluate_static_criteria; plateau/delay_surface from
    the execution analysis.
    """
    checks = dict(static["checks"])
    fam_id = static.get("_family_id", "A")
    c6 = evaluate_criterion6(FAMILIES[fam_id], plateau, delay_surface,
                             family_id=fam_id)
    checks["6_no_single_horizon_dependence"] = c6
    promoted = bool(static["static_pass"] and c6["pass"])
    return {
        "family": static["family"],
        "trade": static["trade"],
        "promoted": promoted,
        "checks": checks,
        "note": "Phase 6 gate remains RESEARCH_GATE. This is the ALPHA_PROMOTION_GATE "
                "for Phase 7 eligibility.",
    }


def write_alpha_gate(gates: Dict, out_dir: Path) -> Path:
    payload = {
        "phase": "7",
        "task": "CR-P7-ROUTING-TRANSLATION-01",
        "gate": "ALPHA_PROMOTION_GATE",
        "criteria": [
            "1 same holdout sign", "2 holdout effect >= 50% dev",
            "3 bootstrap CI excludes zero", "4 adequate holdout N",
            "5 no collapse under overlap cooldowns",
            "6 no single-horizon dependence",
        ],
        "families": gates,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "P7_ALPHA_PROMOTION_GATE.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
