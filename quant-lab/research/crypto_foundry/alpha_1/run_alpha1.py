"""
CRYPTO-ALPHA-1 — Mechanism-to-Strategy Hypothesis Generation.

Clusters MECH-2 PROMOTE_TO_ALPHA states into mechanism families,
generates frozen strategy contracts (<=25 total), controls, cost/funding/split
contracts, and writes all required artifacts.

NO strategy PnL. NO optimization. NO ML. NO execution.
"""
from __future__ import annotations

import csv, hashlib, json, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

OUT = Path(__file__).resolve().parent
CRYPTO = OUT.parent
MECH2 = CRYPTO / "mech_2"
MECH2_ANALYSIS = MECH2 / "analysis"

sys.path.insert(0, str(MECH2_ANALYSIS))


def load_promoted_states() -> List[Dict]:
    """Return only PROMOTE_TO_ALPHA rows from MECH_2_PROMOTION_REGISTRY.csv."""
    rows = []
    with open(MECH2 / "MECH_2_PROMOTION_REGISTRY.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("status") == "PROMOTE_TO_ALPHA":
                rows.append(r)
    return rows


def load_state_registry() -> Dict[str, Dict]:
    """Build {state_id: row} from MECH_2_STATE_REGISTRY.csv."""
    reg = {}
    with open(MECH2 / "MECH_2_STATE_REGISTRY.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            reg[r["state_id"]] = r
    return reg


def load_definitions() -> Dict:
    return json.load(open(MECH2 / "MECH_2_STATE_DEFINITIONS.json", encoding="utf-8"))


# ---------------------------------------------------------------------------
# Mechanism family clustering
# ---------------------------------------------------------------------------

def cluster_into_families(promoted: List[Dict], registry: Dict[str, Dict]) -> List[Dict]:
    """
    Cluster promoted states into mechanism families.
    States that describe the same mechanism get grouped.
    Each family gets ONE strategy lineage (with variants as needed).
    """
    families = {
        "FAM_A": {
            "family_id": "FAM_A",
            "name": "EXTREME_NEGATIVE_BASIS_DISLOCATION",
            "mechanism": "perp below spot beyond p90_abs. Arbitrage capital constrained.",
            "constraint": "arbitrage capital bandwidth; spot-perp convergence friction",
            "expected_resolution_path": "basis drifts to normal band; slow, may expand first",
            "candidate_execution_objects": ["perp", "spot", "spot+perp hedge"],
            "expected_horizon": "4h-24h",
            "failure_mode": "basis expands; funding doesn't confirm; systemic overrides",
            "reason_for_test": "strongest L1 basis state (ER=0.69-0.75 bits)",
            "asset": "BTC_ETH",
            "source_states": [],
        },
        "FAM_B": {
            "family_id": "FAM_B",
            "name": "NEGATIVE_BASIS_CROWDING_CONFIRMED",
            "mechanism": "extreme neg basis + neg funding. Crowded short-perp positioning.",
            "constraint": "perpetual short pressure; funding+basis joint signal",
            "expected_resolution_path": "basis normalizes; FAST or EXPANSION_FIRST",
            "candidate_execution_objects": ["perp", "spot+perp hedge", "BTC/ETH relative"],
            "expected_horizon": "1h-24h",
            "failure_mode": "crowding intensifies; funding stays extreme and basis expands",
            "reason_for_test": "highest ER (0.94-1.02 bits); most information-rich signal",
            "asset": "BTC_ETH",
            "source_states": [],
        },
        "FAM_C": {
            "family_id": "FAM_C",
            "name": "BASIS_FUNDING_VOLATILITY_COMPOSITE",
            "mechanism": "basis+funding extreme + high vol. Triple confirmation.",
            "constraint": "vol-amplified marking pressure; triple confirmation reduces noise",
            "expected_resolution_path": "vol compresses first, then basis/funding follow",
            "candidate_execution_objects": ["perp", "spot+perp hedge"],
            "expected_horizon": "8h-24h",
            "failure_mode": "vol stays elevated; triple dislocation persists",
            "reason_for_test": "L3 incremental ER over L2; vol conditioning filters noise",
            "asset": "BTC_ETH",
            "source_states": [],
        },
        "FAM_D": {
            "family_id": "FAM_D",
            "name": "ETH_LED_RELATIVE_DISLOCATION",
            "mechanism": "ETH dislocated relative to BTC. Capital rotation creates RV.",
            "constraint": "cross-asset capital; BTC/ETH relative basis",
            "expected_resolution_path": "ETH normalizes relative to BTC; ETH leads, BTC follows",
            "candidate_execution_objects": ["ETH perp", "BTC perp", "BTC/ETH relative basket"],
            "expected_horizon": "4h-24h",
            "failure_mode": "ETH stress becomes systemic; narrows via BTC dislocation",
            "reason_for_test": "cross-asset ER=0.10-0.34; measurable asset-specific info",
            "asset": "ETH",
            "source_states": [],
        },
        "FAM_E": {
            "family_id": "FAM_E",
            "name": "NORMAL_BASIS_EXTREME_FUNDING_PRE_DISLOCATION",
            "mechanism": "funding extreme while basis normal. May PRECEDE stress.",
            "constraint": "funding pressure as leading indicator",
            "expected_resolution_path": "ambiguous: funding normalizes OR basis dislocates (delayed)",
            "candidate_execution_objects": ["perp directional", "spot+perp pre-positioning"],
            "expected_horizon": "1h-8h",
            "failure_mode": "funding normalizes without basis move; or basis dislocates wrong way",
            "reason_for_test": "MECH-2 promoted; carries anticipatory information",
            "asset": "BTC_ETH",
            "source_states": [],
        },
    }

    # Assign promoted states to families
    for s in promoted:
        sid = s["state_id"]
        asset = s["asset"]
        state_val = s.get("state", "")

        # FAM_A: pure extreme negative basis (L1)
        if state_val in ("B4_EXTREME_NEGATIVE", "B3_ELEVATED_NEGATIVE") and s.get("level") == "L1":
            families["FAM_A"]["source_states"].append(sid)
            continue

        # FAM_B: extreme neg basis + neg funding (L2, no vol)
        state_has_extreme_basis = "B4_EXTREME_NEGATIVE" in state_val or "B3_ELEVATED_NEGATIVE" in state_val
        state_has_neg_funding = "F_NEG" in state_val
        state_has_vol = "V_" in state_val
        if state_has_extreme_basis and state_has_neg_funding and not state_has_vol:
            families["FAM_B"]["source_states"].append(sid)
            continue

        # FAM_C: L3 composites (basis + funding + vol)
        if s.get("level") == "L3" and state_has_vol:
            families["FAM_C"]["source_states"].append(sid)
            continue

        # FAM_D: ETH-led / ETH-specific / systemic
        if asset == "ETH" and state_val in ("ETH_LED", "ETH_SPECIFIC", "SYSTEMIC_STRESS"):
            families["FAM_D"]["source_states"].append(sid)
            continue

        # FAM_E: normal basis + extreme funding
        if "B0_NORMAL" in state_val and ("F_NEG_EXTREME" in state_val or "F_NEG_ELEVATED" in state_val):
            families["FAM_E"]["source_states"].append(sid)
            continue

    # FAM_X: any remaining promoted states (control baseline)
    assigned = set()
    for f in families.values():
        for sid in f["source_states"]:
            assigned.add(sid)
    unassigned = [s for s in promoted if s["state_id"] not in assigned]
    if unassigned:
        families["FAM_X"] = {
            "family_id": "FAM_X",
            "name": "NORMAL_BASIS_TRANSITION_CONTROL",
            "mechanism": "normal basis state. MECH-2 promoted statistically but mechanism-trivial. CONTROL.",
            "constraint": "none (no dislocation)",
            "expected_resolution_path": "basis stays normal",
            "candidate_execution_objects": ["perp directional (control)"],
            "expected_horizon": "4h",
            "failure_mode": "N/A",
            "reason_for_test": "statistical promotion; CONTROL only",
            "asset": "BTC",
            "source_states": [s["state_id"] for s in unassigned],
        }

    return [f for f in families.values() if f["source_states"]]


def write_family_registry(families: List[Dict]):
    """Write ALPHA_1_MECHANISM_FAMILY_REGISTRY.csv."""
    fields = ["family_id", "name", "source_states", "n_source_states", "asset",
              "mechanism", "constraint", "expected_resolution_path",
              "candidate_execution_objects", "expected_horizon",
              "failure_mode", "reason_for_test"]
    rows = []
    for f in families:
        row = {k: f.get(k, "") for k in fields}
        row["source_states"] = "; ".join(f["source_states"])
        row["n_source_states"] = str(len(f["source_states"]))
        row["candidate_execution_objects"] = "; ".join(f.get("candidate_execution_objects", []))
        rows.append(row)

    with open(OUT / "ALPHA_1_MECHANISM_FAMILY_REGISTRY.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"  Family registry: {len(rows)} families written")


# ─── MAIN ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== ALPHA-1 Hypothesis Generator ===")

    promoted = load_promoted_states()
    registry = load_state_registry()
    print(f"Loaded {len(promoted)} promoted states from MECH-2")

    families = cluster_into_families(promoted, registry)
    print(f"Clustered into {len(families)} families")
    for f in families:
        print(f"  {f['family_id']}: {len(f['source_states'])} states")

    write_family_registry(families)

    from build_artifacts import build_all
    contracts, decision = build_all()

    print(f"\nDecision: {decision['decision']}")
    print(f"Next checkpoint: {decision['next_checkpoint']}")