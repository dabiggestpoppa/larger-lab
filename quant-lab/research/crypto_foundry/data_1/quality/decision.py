"""
Crypto Foundry DATA-1.3: Fail-Closed Decision Engine

determine_data_foundation_decision() emits PASS only when:
- no blocking FAIL
- no blocking BLOCKED
- every canonical dataset has a manifest
- every required live lane has actual persisted data
- every required applicable gate executed
- no report/manifest count contradiction

Unit-tested: AMM swap count = 0 => cannot PASS; manifest row_count=0
for a required canonical dataset => cannot PASS; pool only CODE_EXISTS
=> cannot PASS; missing applicable gate => cannot PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

PASS = "PASS_CANONICAL_CRYPTO_DATA_FOUNDATION"
PARTIAL = "PARTIAL_CRYPTO_DATA_FOUNDATION"
FAIL = "FAIL_CRYPTO_DATA_FOUNDATION"

# Datasets that MUST be valid and persisted for a full PASS.
REQUIRED_CANONICAL_DATASETS = [
    "bn_btcusdt_spot_5m",
    "bn_ethusdt_spot_5m",
    "hl_btc_perp_state_5m",
    "hl_eth_perp_state_5m",
    "hl_btc_funding_hourly",
    "hl_eth_funding_hourly",
    "eth_weth_usdc_swap",
    "eth_wbtc_usdc_swap",   # may be formally demoted
    "base_weth_usdc_swap",
]

# Gates that must have evidence per applicable dataset family.
APPLICABLE_GATE_BY_FAMILY = {
    "SPOT_BAR_REFERENCE": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q14", "Q15", "Q16", "Q17"],
    "PERP_STATE": ["Q1", "Q2", "Q3", "Q6", "Q7", "Q9", "Q14", "Q15", "Q16"],
    "PERP_FUNDING": ["Q1", "Q2", "Q8", "Q14", "Q15", "Q16"],
    "AMM_SWAP": ["Q1", "Q2", "Q10", "Q11", "Q12", "Q14", "Q15", "Q16"],
}


@dataclass
class DecisionInput:
    """All evidence the decision engine consumes."""
    dataset_statuses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    manifest_completeness: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    gate_results: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    lane_requirements: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    demotions: Dict[str, str] = field(default_factory=dict)


@dataclass
class DecisionOutput:
    decision: str
    reasons: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    evidence_ok: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def determine_data_foundation_decision(inp: DecisionInput) -> DecisionOutput:
    """
    Fail-closed decision logic.

    PASS requires:
    - no blocking FAIL
    - no blocking BLOCKED
    - every canonical dataset has manifest
    - every required live lane has actual persisted data
    - every required applicable gate executed
    - no report/manifest count contradiction
    """
    reasons: List[str] = []
    blocking: List[str] = []

    # 1. Dataset statuses: FAIL or BLOCKED on a canonical dataset is blocking.
    for ds_id, st in inp.dataset_statuses.items():
        status = st.get("status", "UNKNOWN")
        if status == "FAIL":
            blocking.append(f"{ds_id}: status=FAIL ({st.get('reason', 'no reason')})")
        elif status == "BLOCKED":
            blocking.append(f"{ds_id}: status=BLOCKED")
    if not blocking:
        reasons.append("No canonical dataset has status FAIL or BLOCKED")

    # 2. Manifest completeness: every canonical dataset (not demoted) must
    #    have a manifest with row_count > 0 and sha256 present.
    for ds_id in REQUIRED_CANONICAL_DATASETS:
        if ds_id in inp.demotions:
            reasons.append(f"{ds_id}: formally demoted ({inp.demotions[ds_id]})")
            continue
        mf = inp.manifest_completeness.get(ds_id)
        if mf is None:
            blocking.append(f"{ds_id}: no manifest")
            continue
        row_count = mf.get("row_count", 0)
        sha = mf.get("sha256")
        if not row_count or row_count <= 0:
            blocking.append(f"{ds_id}: manifest row_count={row_count} (must be > 0)")
        if not sha:
            blocking.append(f"{ds_id}: manifest missing sha256")
        if mf.get("status") in ("PARTIAL", "FAILED"):
            blocking.append(f"{ds_id}: manifest status={mf.get('status')}")
    if not any(b.startswith(d + ":") for d in REQUIRED_CANONICAL_DATASETS for b in blocking):
        reasons.append("All required canonical datasets have valid manifests")

    # 3. Gate coverage: every applicable gate per family must have executed
    #    (PASS or documented non-blocking), not missing.
    for family, gates in APPLICABLE_GATE_BY_FAMILY.items():
        executed = set(inp.gate_results.get(family, []))
        missing = [g for g in gates if g not in executed]
        if missing:
            blocking.append(f"{family}: applicable gates not executed: {missing}")
    if not any("applicable gates not executed" in b for b in blocking):
        reasons.append("All applicable Q1-Q17 gates executed")

    # 4. Lane requirements.
    for lane, req in inp.lane_requirements.items():
        if req.get("required") and not req.get("met"):
            blocking.append(f"{lane}: required but not met ({req.get('reason', '')})")
    if not any(l in b for b in blocking for l in inp.lane_requirements if inp.lane_requirements[l].get("required")):
        reasons.append("All required lanes met")

    # 5. Count contradiction: manifest row_count must not be 0 when a report
    #    claims live data. Checked per dataset via manifest_completeness.
    for ds_id, mf in inp.manifest_completeness.items():
        if mf.get("status") == "VALID" and (not mf.get("row_count") or mf.get("row_count", 0) <= 0):
            blocking.append(f"{ds_id}: status=VALID but row_count={mf.get('row_count')} (contradiction)")

    evidence_ok = len(blocking) == 0
    if evidence_ok:
        decision = PASS
        reasons.append("All evidence gates satisfied")
    else:
        decision = FAIL
        reasons.append("Blocking issues present: cannot PASS")

    return DecisionOutput(decision=decision, reasons=reasons, blocking_issues=blocking, evidence_ok=evidence_ok)
