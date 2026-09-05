"""
CRYPTO-MECH-2: Fail-closed promotion gate + checkpoint decision engine.

Promotion (PROMOTE_TO_ALPHA) is impossible when ANY of the following hold
(fail-closed):
  SPARSE_STATE / INSUFFICIENT_N  -> event count < 50
  NULL_NOT_BEATEN                -> does not beat the unconditional/vol-matched
                                    null with CI excluding 0
  FUTURE_LEAKAGE                 -> perturbation test fails
  REDUNDANT                      -> a simpler state carries the same information
  TEMPORAL_DEPTH_INSUFFICIENT    -> lane depth too short (e.g. basis lane)
  ONE_PERIOD_DOMINATED           -> effect present in only one subperiod

Checkpoint decision: PASS_STATE_TAXONOMY only when all frozen pass conditions
hold; otherwise PARTIAL_STATE_TAXONOMY (evidence gap) or FAIL_STATE_TAXONOMY.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

PASS = "PASS_STATE_TAXONOMY"
PARTIAL = "PARTIAL_STATE_TAXONOMY"
FAIL = "FAIL_STATE_TAXONOMY"

MIN_PROMOTION_N = 50
PREFERRED_PROMOTION_N = 100
# Materiality bar: information gain must be non-trivial, not merely
# statistically detectable at large N. Fixed a priori (NOT tuned to returns;
# it is a mechanism-signal materiality gate on standardized effect size).
MIN_MATERIAL_SMD = 0.20
MIN_MATERIAL_ER_BITS = 0.02


@dataclass
class PromotionCandidate:
    state_id: str
    event_count: int
    causal: bool = True
    perturbation_passed: bool = True
    entropy_reduction_bits: float = 0.0
    effect_size: float = 0.0
    null_effect: float = 0.0          # observed - null (positive = beats null)
    null_ci_excludes_zero: bool = False
    not_redundant: bool = True
    subperiod_stable: bool = True
    mechanism_interpretation: str = ""
    temporal_depth_ok: bool = True
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_promotion(c: PromotionCandidate) -> Dict[str, Any]:
    """Fail-closed: returns status + blocking reasons.

    Status mapping:
      PROMOTE_TO_ALPHA        -> no blocking reasons
      SPARSE_STATE            -> event count < 20 (mission N<20 tier)
      RESEARCH_ONLY           -> limited N (20..49), insufficient temporal
                                 depth, or no mechanism interpretation
      REDUNDANT               -> simpler state carries the same information
      FALSIFIED               -> null not beaten / future leakage /
                                 non-causal / one-period dominated
    """
    blocking: List[str] = []
    if c.event_count < 20:
        return {"status": "SPARSE_STATE", "blocking": ["SPARSE_STATE"]}
    if c.event_count < MIN_PROMOTION_N:
        blocking.append("INSUFFICIENT_N")
    if not c.causal:
        blocking.append("NON_CAUSAL")
    if not c.perturbation_passed:
        blocking.append("FUTURE_LEAKAGE")
    if not c.null_ci_excludes_zero:
        blocking.append("NULL_NOT_BEATEN")
    if abs(c.effect_size) < MIN_MATERIAL_SMD:
        blocking.append("TRIVIAL_EFFECT_SIZE")
    if c.entropy_reduction_bits < MIN_MATERIAL_ER_BITS:
        blocking.append("TRIVIAL_INFORMATION_GAIN")
    if not c.not_redundant:
        blocking.append("REDUNDANT")
    if not c.temporal_depth_ok:
        blocking.append("TEMPORAL_DEPTH_INSUFFICIENT")
    if not c.subperiod_stable:
        blocking.append("ONE_PERIOD_DOMINATED")
    if not c.mechanism_interpretation:
        blocking.append("NO_MECHANISM_INTERPRETATION")

    if not blocking:
        return {"status": "PROMOTE_TO_ALPHA", "blocking": []}
    if "REDUNDANT" in blocking:
        return {"status": "REDUNDANT", "blocking": blocking}
    if any(b in ("INSUFFICIENT_N", "TEMPORAL_DEPTH_INSUFFICIENT",
                 "NO_MECHANISM_INTERPRETATION") for b in blocking):
        return {"status": "RESEARCH_ONLY", "blocking": blocking}
    # NULL_NOT_BEATEN / TRIVIAL_* / ONE_PERIOD_DOMINATED / FUTURE_LEAKAGE /
    # NON_CAUSAL all falsify the mechanism family for promotion purposes
    return {"status": "FALSIFIED", "blocking": blocking}


@dataclass
class Mech2DecisionInput:
    # 1
    mech1_parent_verified: bool = False
    # 2
    definitions_preregistered: bool = False
    # 3
    future_leakage: List[str] = field(default_factory=list)
    # 4
    transition_matrices_completed: bool = False
    # 5
    path_taxonomy_completed: bool = False
    # 6
    survival_completed: bool = False
    # 7
    information_gain_measured: bool = False
    # 8
    null_comparisons_completed: bool = False
    # 9
    sparse_states_demoted: bool = False
    # 10
    redundant_states_demoted: bool = False
    # 11
    convergence_family_evaluated: bool = False
    # 12
    systemic_states_analyzed: bool = False
    # 13
    strategy_pnl_computed: bool = False
    # 14
    return_optimization_performed: bool = False
    # 15
    ml_performed: bool = False
    # 16
    execution_authorized: bool = False
    # 17
    promotion_registry_produced: bool = False
    # 18
    promoted_or_falsified: bool = False
    # repair
    mark_index_reclassified: bool = False
    # evidence details
    n_promoted: int = 0
    n_falsified: int = 0


@dataclass
class Mech2DecisionOutput:
    decision: str
    reasons: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    evidence_ok: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def determine_mech2_decision(inp: Mech2DecisionInput) -> Mech2DecisionOutput:
    reasons: List[str] = []
    blocking: List[str] = []

    if not inp.mech1_parent_verified:
        blocking.append("MECH-1 parent not verified")
    else:
        reasons.append("MECH-1 parent verified (freeze hashes + PASS decision)")

    if not inp.definitions_preregistered:
        blocking.append("state definitions not preregistered/frozen")
    else:
        reasons.append("State definitions preregistered and frozen")

    if inp.future_leakage:
        blocking.append(f"future leakage detected: {inp.future_leakage[:3]}")
    else:
        reasons.append("No future leakage (perturbation + truncation invariance)")

    if not inp.transition_matrices_completed:
        blocking.append("transition matrices not completed")
    else:
        reasons.append("Transition matrices completed (1h/4h/8h/24h)")

    if not inp.path_taxonomy_completed:
        blocking.append("path taxonomy not completed")
    else:
        reasons.append("Path taxonomy completed")

    if not inp.survival_completed:
        blocking.append("survival analysis not completed")
    else:
        reasons.append("Survival analysis completed (KM, censoring reported)")

    if not inp.information_gain_measured:
        blocking.append("information gain not measured")
    else:
        reasons.append("Information gain measured (entropy reduction, JS, effect size)")

    if not inp.null_comparisons_completed:
        blocking.append("null comparisons not completed")
    else:
        reasons.append("Null comparisons completed (4 null models)")

    if not inp.sparse_states_demoted:
        blocking.append("sparse states not demoted")
    else:
        reasons.append("Sparse states demoted (fail-closed)")

    if not inp.redundant_states_demoted:
        blocking.append("redundant states not demoted")
    else:
        reasons.append("Redundant states demoted (incremental info gate)")

    if not inp.convergence_family_evaluated:
        blocking.append("weak convergence family not truthfully evaluated")
    else:
        reasons.append("Convergence family truthfully evaluated (conditional re-test)")

    if not inp.systemic_states_analyzed:
        blocking.append("BTC/ETH systemic states not analyzed")
    else:
        reasons.append("BTC/ETH systemic states analyzed")

    if inp.strategy_pnl_computed:
        blocking.append("strategy PnL computed (prohibited)")
    else:
        reasons.append("No strategy PnL")
    if inp.return_optimization_performed:
        blocking.append("return optimization performed (prohibited)")
    else:
        reasons.append("No return optimization")
    if inp.ml_performed:
        blocking.append("ML performed (prohibited)")
    else:
        reasons.append("No ML")
    if inp.execution_authorized:
        blocking.append("execution authorized (prohibited)")
    else:
        reasons.append("No execution")

    if not inp.promotion_registry_produced:
        blocking.append("promotion registry not produced")
    else:
        reasons.append("Promotion registry produced")

    if not inp.promoted_or_falsified:
        blocking.append("no state promoted AND major families not truthfully falsified")
    else:
        reasons.append(
            f"Promotion/falsification closure: {inp.n_promoted} promoted, "
            f"{inp.n_falsified} falsified")

    if not inp.mark_index_reclassified:
        blocking.append("MECH-1 MARK_INDEX_STRESS repair not applied")
    else:
        reasons.append("MECH-1 MARK_INDEX_STRESS reclassified (PROVISIONAL_SUPPORTED)")

    evidence_ok = len(blocking) == 0
    decision = PASS if evidence_ok else (
        PARTIAL if len(blocking) <= 4 else FAIL)
    return Mech2DecisionOutput(decision=decision, reasons=reasons,
                               blocking_issues=blocking, evidence_ok=evidence_ok)
