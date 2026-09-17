"""
CRYPTO-MECH-1: Fail-closed decision engine.

Emits PASS_MECHANISM_ANATOMY only when all frozen pass conditions hold:
1. freeze parent verifies
2. no causal violations
3. event segmentation reproducible
4. at least one meaningful basis anatomy produced
5. funding/OI behavior characterized (honest limits)
6. BTC/ETH comparison produced
7. null comparisons completed
8. AMM findings labeled according to actual depth
9. failures/negative mechanisms retained
10. no strategy PnL/optimization performed
11. mechanism registry produced
12. no unsupported alpha claim
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

PASS = "PASS_MECHANISM_ANATOMY"
PARTIAL = "PARTIAL_MECHANISM_ANATOMY"
FAIL = "FAIL_MECHANISM_ANATOMY"


@dataclass
class MechDecisionInput:
    freeze_verified: bool = False
    freeze_reason: str = ""
    causal_violations: List[str] = field(default_factory=list)
    segmentation_reproducible: bool = False
    basis_anatomy_rows: int = 0
    funding_anatomy_rows: int = 0
    oi_anatomy_present: bool = False
    cross_asset_present: bool = False
    null_models_completed: List[str] = field(default_factory=list)
    amm_findings_labelled: bool = False
    negative_mechanisms_retained: bool = False
    strategy_pnl_computed: bool = False
    optimization_performed: bool = False
    mechanism_registry_present: bool = False
    unsupported_alpha_claim: bool = False
    amm_evidence_class: str = ""


@dataclass
class MechDecisionOutput:
    decision: str
    reasons: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    evidence_ok: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def determine_mech1_decision(inp: MechDecisionInput) -> MechDecisionOutput:
    reasons: List[str] = []
    blocking: List[str] = []

    # 1. Freeze parent
    if not inp.freeze_verified:
        blocking.append(f"freeze parent not verified: {inp.freeze_reason}")
    else:
        reasons.append("Freeze parent verified (all 9 raw hashes match)")

    # 2. Causal violations
    if inp.causal_violations:
        blocking.append(f"causal violations: {inp.causal_violations[:3]}")
    else:
        reasons.append("No causal violations (same-bucket/nearest-prior alignment)")

    # 3. Segmentation reproducible
    if not inp.segmentation_reproducible:
        blocking.append("event segmentation not reproducible")
    else:
        reasons.append("Event segmentation reproducible")

    # 4. Basis anatomy
    if inp.basis_anatomy_rows <= 0:
        blocking.append("no basis anatomy produced")
    else:
        reasons.append(f"Basis anatomy produced ({inp.basis_anatomy_rows} rows)")

    # 5. Funding/OI
    if inp.funding_anatomy_rows <= 0:
        blocking.append("no funding anatomy produced")
    else:
        reasons.append(f"Funding anatomy produced ({inp.funding_anatomy_rows} rows)")
    if not inp.oi_anatomy_present:
        blocking.append("OI anatomy missing")
    else:
        reasons.append("OI anatomy present (snapshot-level, honest limits)")

    # 6. BTC/ETH comparison
    if not inp.cross_asset_present:
        blocking.append("BTC/ETH cross-asset comparison missing")
    else:
        reasons.append("BTC/ETH cross-asset comparison produced")

    # 7. Null models
    required_nulls = ["unconditional_future_basis_change",
                      "random_timestamps_matched_by_volatility_regime",
                      "shuffled_event_labels_preserving_time_blocks",
                      "ar1_mean_reversion_expectation"]
    missing = [n for n in required_nulls if n not in inp.null_models_completed]
    if missing:
        blocking.append(f"null models not completed: {missing}")
    else:
        reasons.append("All four null models completed")

    # 8. AMM findings labelled
    if not inp.amm_findings_labelled:
        blocking.append("AMM findings not labelled by actual depth")
    else:
        reasons.append(f"AMM findings labelled ({inp.amm_evidence_class or 'set'})")

    # 9. Negative mechanisms retained
    if not inp.negative_mechanisms_retained:
        blocking.append("negative/falsified mechanisms not retained")
    else:
        reasons.append("Negative mechanisms retained in registry")

    # 10. No PnL / optimization
    if inp.strategy_pnl_computed:
        blocking.append("strategy PnL computed (prohibited)")
    else:
        reasons.append("No strategy PnL computed")
    if inp.optimization_performed:
        blocking.append("optimization performed (prohibited)")
    else:
        reasons.append("No optimization performed")

    # 11. Mechanism registry
    if not inp.mechanism_registry_present:
        blocking.append("mechanism registry missing")
    else:
        reasons.append("Mechanism registry produced")

    # 12. No alpha claim
    if inp.unsupported_alpha_claim:
        blocking.append("unsupported alpha claim made")
    else:
        reasons.append("No unsupported alpha claim")

    evidence_ok = len(blocking) == 0
    decision = PASS if evidence_ok else (PARTIAL if len(blocking) <= 4 else FAIL)
    return MechDecisionOutput(decision=decision, reasons=reasons,
                              blocking_issues=blocking, evidence_ok=evidence_ok)
