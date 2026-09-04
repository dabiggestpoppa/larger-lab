"""G5 — quant / crypto / CEREBUS domain resilience (S14–S19).

CLASS C domain simulations. These are NOT strategy-performance projects; they
test promotion discipline, domain authority, source semantics, data-resolution
boundaries, ontology expansion, doctrine amendment, transfer validity and the
preservation of negative/unresolved knowledge.

Governing doctrine (enforced, not asserted):
  OBSERVE BEFORE PREDICT            — claims follow observable artifacts
  STATE BEFORE ACTION               — dispositions precede execution authority
  CONSTRAINTS BEFORE DIRECTION      — B7 gates are constraints, not steering
  POTENTIAL != REALIZATION          — PnL never purchases epistemic promotion
  PROFIT != VALIDATION              — high economic value only changes priority
  ANALOGY != TRANSFER               — name similarity does not validate a domain transfer
  MISSING DATA != NEGATIVE EVIDENCE — DATA_BLOCKED is not falsification
  AUTHORITATIVE MANUAL != IMMUNE FROM CONTRADICTION — evidence may challenge
                                  doctrine without rewriting it
  CONTRADICTION != SILENT REWRITE   — contradictions open explicit records

Deterministic, local-first, model-free. Everything here runs on synthetic /
fixture evidence; no broker/exchange/live-model/production/cloud/capital
contact. All identifiers derive deterministically from content.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

# --------------------------------------------------------------------------- #
# vocabularies
# --------------------------------------------------------------------------- #
DOMAINS = ("CRYPTO", "FX", "REGIME_STATE", "GENERIC")
CLAIM_TYPES = ("ALPHA_CANDIDATE", "MECHANISM_HYPOTHESIS", "DOCTRINE_CLAIM",
               "PROVIDER_OBSERVATION", "TRANSFER_HYPOTHESIS", "UNRESOLVED_PATTERN")
AUTHORITY_CLASSES = ("CEREBUS_MANUAL", "B7_VALIDATION", "QUANT_WATCH", "CRYPTO_SENSOR_FABRIC",
                     "CRYPTO_FOUNDRY", "OCE", "OPERATOR")
VALIDATION_GATE_IDS = ("PIT_INTEGRITY", "EXECUTION_REALISM", "COST_SENSITIVITY",
                       "OOS_WALK_FORWARD", "MECHANISM_PLAUSIBILITY", "FAMILY_MULTIPLICITY",
                       "REPRODUCIBILITY", "SENSITIVITY_STRESS")
DATA_AVAILABILITY_STATUSES = ("AVAILABLE", "PARTIAL", "CURRENT_ONLY",
                              "HISTORICAL_LIMITED", "UNAVAILABLE", "UNKNOWN")
SENSOR_REQUIREMENT_KEYS = (
    "LIQUIDATION_STATE", "OPEN_INTEREST_STATE", "FUNDING_STATE", "ORDER_FLOW_STATE",
    "LIQUIDITY_STATE", "AGGRESSOR_FLOW_STATE", "HISTORICAL_LIQUIDATION_DETAIL",
    "POSITIONING_STATE", "MECHANICAL_BOOK_STATE",
)
S18_REQUIRED_SENSORS = ("AGGRESSOR_FLOW_STATE", "HISTORICAL_LIQUIDATION_DETAIL")

# canonical diagnostic layers, in the ONLY order S17 may proceed (source first)
SOURCE_DIAGNOSTIC_LAYERS = (
    "provider_semantics", "instrument_identity", "adapter", "normalization",
    "time_semantics", "quality", "disagreement_surface",
)

FAILURE_ATOM_IDS = ("LOOKAHEAD_LEAKAGE", "UNREALISTIC_FILL_MODEL",
                    "SURVIVORSHIP_BIAS", "DATA_QUALITY", "MECHANISM_MISSING",
                    "SENSOR_UNAVAILABLE", "UNIT_MISMATCH", "INSTRUMENT_MISMATCH",
                    "ADAPTER_MISMATCH", "TIME_WINDOW_MISMATCH", "FAMILY_MULTIPLICITY",
                    "OOS_DEGRADATION")


class DomainDisposition(str, Enum):
    """TEST-ONLY dispositions the shared G5 policy may yield for CLASS C
    scenarios. Mapped onto existing M4/M5 semantics where applicable; these
    labels are NOT new constitutional states."""

    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    REJECTED_NEGATIVE_KNOWLEDGE = "REJECTED_NEGATIVE_KNOWLEDGE"
    UNRESOLVED_PATTERN = "UNRESOLVED_PATTERN"
    ONTOLOGY_EXPLORATION_CANDIDATE = "ONTOLOGY_EXPLORATION_CANDIDATE"
    CONTRADICTION_OPEN = "CONTRADICTION_OPEN"
    MANUAL_PRESERVED = "MANUAL_PRESERVED"
    SOURCE_DIAGNOSTIC_REQUIRED = "SOURCE_DIAGNOSTIC_REQUIRED"
    SOURCE_DISAGREEMENT_PRESERVED = "SOURCE_DISAGREEMENT_PRESERVED"
    DATA_BLOCKED = "DATA_BLOCKED"
    TRANSFER_HYPOTHESIS_ONLY = "TRANSFER_HYPOTHESIS_ONLY"
    DOMAIN_VALIDATION_REQUIRED = "DOMAIN_VALIDATION_REQUIRED"
    DOMAIN_VALIDATED = "DOMAIN_VALIDATED"
    ANALOGY_ONLY = "ANALOGY_ONLY"
    TRANSFER_REJECTED = "TRANSFER_REJECTED"
    REPRODUCTION_REJECTED = "REPRODUCTION_REJECTED"
    PRIORITY_HIGH = "PRIORITY_HIGH"
    PRIORITY_NORMAL = "PRIORITY_NORMAL"
    REOPEN_CANDIDATE = "REOPEN_CANDIDATE"


# --------------------------------------------------------------------------- #
# G5R-16 — structured duration/history representation
# --------------------------------------------------------------------------- #
HISTORY_ANCHOR = "2026-01-01T00:00:00Z"   # fixed provisional anchor for SINCE spans


@dataclass(frozen=True)
class HistorySpan:
    """Small deterministic structured duration/history representation. Never
    naive string equality for durations: '12m' == 12 months, '2021-06-01..' is
    months-since the fixed provisional HISTORY_ANCHOR (a deterministic
    convention, not wall-clock truth)."""

    kind: str                        # MONTHS | SINCE | NONE
    value: int = 0
    start_label: str = ""

    @classmethod
    def from_string(cls, raw: str) -> "HistorySpan":
        raw = (raw or "").strip()
        if not raw:
            return cls(kind="NONE")
        m = re.match(r"^(\d+)m$", raw)
        if m:
            return cls(kind="MONTHS", value=int(m.group(1)))
        if raw.endswith(".."):
            start = raw[:-2].strip()
            months = _months_since(start)
            return cls(kind="SINCE", value=months, start_label=start)
        raise ValueError(f"unparseable history span {raw!r}")

    def satisfies(self, required: "HistorySpan") -> bool:
        if required.kind == "NONE":
            return True
        if self.kind == "NONE":
            return False
        return self.value >= required.value

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "value": self.value, "start_label": self.start_label}


def _months_since(start_iso: str) -> int:
    import datetime as _dt

    start = _dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    anchor = _dt.datetime.fromisoformat(HISTORY_ANCHOR.replace("Z", "+00:00"))
    return max(0, (anchor.year - start.year) * 12 + (anchor.month - start.month))


# --------------------------------------------------------------------------- #
# G5R-25 — B7 gate materiality contract (OCE-B7-PLAN-001)
# --------------------------------------------------------------------------- #
GATE_MATERIALITY = ("BLOCKING", "ADVISORY", "CONDITIONAL")


@dataclass(frozen=True)
class B7GateContract:
    """Versioned declaration of each B7 gate's materiality + condition, from
    the authoritative OCE-B7-PLAN-001. No hidden hardcoded materiality: the
    kernel reads every gate's class from this contract.

    * BLOCKING    — a failed/absent required gate rejects the candidate.
    * ADVISORY    — failure is preserved and demotes; it never certifies.
    * CONDITIONAL — required for promotion but not an integrity rejection.
    * NOT_EXECUTED— declared from doctrine but not executed in this fixture;
                    surfaced in every result, never silently passed.
    """

    contract_id: str
    version: str
    source_doc_ref: str
    gates: Tuple[Tuple[str, str, str], ...]   # (gate_id, materiality, condition)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "B7GateContract":
        gates = []
        for g in data.get("gates", []):
            gid = str(g["gate_id"])
            mat = str(g.get("materiality", "ADVISORY"))
            if mat not in GATE_MATERIALITY and mat != "NOT_EXECUTED":
                raise ValueError(f"unknown B7 gate materiality {mat!r}")
            gates.append((gid, mat, str(g.get("condition", ""))))
        return cls(contract_id=str(data["contract_id"]), version=str(data.get("version", "1.0")),
                   source_doc_ref=str(data.get("source_doc_ref", "")),
                   gates=tuple(gates))

    def materiality(self, gate_id: str) -> str:
        for gid, mat, _ in self.gates:
            if gid == gate_id:
                return mat
        return "ADVISORY"    # unknown gates are never BLOCKING by default

    def condition(self, gate_id: str) -> str:
        for gid, _, cond in self.gates:
            if gid == gate_id:
                return cond
        return ""

    def not_executed_gates(self) -> Tuple[str, ...]:
        return tuple(gid for gid, mat, _ in self.gates if mat == "NOT_EXECUTED")

    def to_dict(self) -> Dict[str, Any]:
        return {"contract_id": self.contract_id, "version": self.version,
                "source_doc_ref": self.source_doc_ref,
                "gates": [{"gate_id": g[0], "materiality": g[1], "condition": g[2]}
                          for g in self.gates]}


B7_GATE_CONTRACT_DATA: Dict[str, Any] = {
    "contract_id": "B7_GATE_CONTRACT",
    "version": "1.0",
    "source_doc_ref": "docs/oce-golden-system/OCE_BLOCK_07_QUANT_FOUNDATION_PLAN_v1.0.md (OCE-B7-PLAN-001)",
    "gates": [
        {"gate_id": "PIT_INTEGRITY", "materiality": "BLOCKING",
         "condition": "B7.C1.S5 — availability before decision; look-ahead/survivorship mutations are rejected"},
        {"gate_id": "EXECUTION_REALISM", "materiality": "BLOCKING",
         "condition": "B7.C2.S4 — impossible fills rejected; optimistic zero-cost/guaranteed-fill cases are explicit simulations only"},
        {"gate_id": "OOS_WALK_FORWARD", "materiality": "BLOCKING",
         "condition": "B7.C3.S2/S3/S5 — pre-registered holdout + walk-forward surfaces required for promotion"},
        {"gate_id": "REPRODUCIBILITY", "materiality": "NOT_EXECUTED",
         "condition": "B7.C2.S5 — repeated run matches tolerances; divergence blocks promotion (kernel not executed in this fixture; surfaced, never silently passed)"},
        {"gate_id": "COST_SENSITIVITY", "materiality": "ADVISORY",
         "condition": "B7.C3.S4 — edge dependent on narrow/optimistic cost assumptions is demoted, not hard-rejected"},
        {"gate_id": "FAMILY_MULTIPLICITY", "materiality": "ADVISORY",
         "condition": "B7.C3.S5 — narrow parameter optimum demotes"},
        {"gate_id": "SENSITIVITY_STRESS", "materiality": "NOT_EXECUTED",
         "condition": "B7.C3.S4 — stress/sensitivity robustness cube (kernel not executed in this fixture; surfaced, never silently passed)"},
        {"gate_id": "MECHANISM_PLAUSIBILITY", "materiality": "CONDITIONAL",
         "condition": "B7.C2.S1 — mechanism frozen in spec; required for promotion, not an integrity rejection"},
    ],
}

DEFAULT_B7_GATE_CONTRACT = B7GateContract.from_data(B7_GATE_CONTRACT_DATA)


# --------------------------------------------------------------------------- #
# G5R-15 — disagreement tolerance contract (S17)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DisagreementToleranceContract:
    """PROVISIONAL per-metric/units tolerance contract. Deterministic; values
    are NOT constitutionalized — the contract itself is versioned data."""

    contract_id: str
    metric: str = "*"
    units: str = "*"
    absolute_tolerance: float = 0.0
    relative_tolerance: float = 0.0
    basis_points_tolerance: float = 0.0

    @classmethod
    def make(cls, seq, metric="*", units="*", absolute_tolerance=0.0,
             relative_tolerance=0.0, basis_points_tolerance=0.0) -> "DisagreementToleranceContract":
        return cls(contract_id=deterministic_hex("tol", seq, metric, units),
                   metric=metric, units=units, absolute_tolerance=absolute_tolerance,
                   relative_tolerance=relative_tolerance,
                   basis_points_tolerance=basis_points_tolerance)

    def to_dict(self) -> Dict[str, Any]:
        return {"contract_id": self.contract_id, "metric": self.metric, "units": self.units,
                "absolute_tolerance": self.absolute_tolerance,
                "relative_tolerance": self.relative_tolerance,
                "basis_points_tolerance": self.basis_points_tolerance}


@dataclass(frozen=True)
class ProviderSemanticsContract:
    """Semantic contract for one provider+metric (G5R-10): indexed by the
    (provider, metric) key, never provider alone."""

    provider: str
    metric: str
    canonical_instrument: str = ""
    contract_type: str = ""

    def key(self) -> Tuple[str, str]:
        return (self.provider, self.metric)

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "metric": self.metric,
                "canonical_instrument": self.canonical_instrument,
                "contract_type": self.contract_type}


# --------------------------------------------------------------------------- #
# S14 — strategy candidate / B7 validation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FeatureUse:
    """One feature usage with observable PIT timestamps. A feature whose
    availability_time > decision_time leaks the future into the decision."""

    feature_id: str
    observation_time: int          # when the underlying event occurred
    availability_time: int         # when the feature is physically available
    decision_time: int             # when the strategy uses it
    pct: int = 0                   # fraction [0..100] of portfolio size it drives

    def leaks(self) -> bool:
        return self.availability_time > self.decision_time

    def to_dict(self) -> Dict[str, Any]:
        return {"feature_id": self.feature_id, "observation_time": self.observation_time,
                "availability_time": self.availability_time, "decision_time": self.decision_time,
                "pct": self.pct, "leaks": self.leaks()}


@dataclass(frozen=True)
class FillRecord:
    """One synthetic fill with observable execution artifacts."""

    fill_id: str
    signal_time: int               # when the strategy signal triggered
    fill_time: int                 # when the fill is timestamped
    spread_state: str              # NORMAL / WIDE / IMPOSSIBLE
    depth_available: int           # book depth available at that tick
    size: int                      # size filled
    slippage_bps: float            # realized slippage in bps
    low_liquidity: bool = False    # observable regime flag

    def impossible(self) -> bool:
        if self.fill_time < self.signal_time:
            return True                       # fill before signal availability
        if self.spread_state == "IMPOSSIBLE":
            return True                       # fill inside an impossible spread
        if self.low_liquidity and self.slippage_bps == 0.0 and self.size > 0:
            return True                       # zero slippage during illiquidity
        if self.size > self.depth_available:
            return True                       # full size at unavailable depth
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {"fill_id": self.fill_id, "signal_time": self.signal_time,
                "fill_time": self.fill_time, "spread_state": self.spread_state,
                "depth_available": self.depth_available, "size": self.size,
                "slippage_bps": self.slippage_bps, "low_liquidity": self.low_liquidity,
                "impossible": self.impossible()}


@dataclass(frozen=True)
class PerformanceReport:
    """Reported (naive) performance. Magnitude is observable but carries NO
    epistemic authority: PnL may raise research priority only."""

    sharpe: float
    cumulative_return: float
    max_drawdown: float
    win_rate: float
    sample_years: float = 1.0

    @property
    def economic_value_class(self) -> str:
        r = self.cumulative_return
        if r >= 50.0:
            return "EXTREME"
        if r >= 5.0:
            return "HIGH"
        if r >= 0.5:
            return "MODERATE"
        return "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {"sharpe": self.sharpe, "cumulative_return": self.cumulative_return,
                "max_drawdown": self.max_drawdown, "win_rate": self.win_rate,
                "sample_years": self.sample_years,
                "economic_value_class": self.economic_value_class}


@dataclass(frozen=True)
class StrategyCandidate:
    """A registered strategy candidate carrying ONLY observable artifacts."""

    candidate_id: str
    family: str
    specification_ref: str
    performance: PerformanceReport
    features: Tuple[FeatureUse, ...]
    fills: Tuple[FillRecord, ...]
    data_lineage: str = ""
    dataset_ref: str = ""
    parameter_count: int = 0
    sample_count: int = 0
    holdout_ref: str = ""
    walk_forward_ref: str = ""
    cost_model_ref: str = ""

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any], seq: int = 0) -> "StrategyCandidate":
        return cls(
            candidate_id=str(data.get("candidate_id") or deterministic_hex("s14_cand", seq)),
            family=str(data.get("family", "")),
            specification_ref=str(data.get("specification_ref", "")),
            performance=PerformanceReport(**{
                k: data["performance"][k] for k in ("sharpe", "cumulative_return",
                                                    "max_drawdown", "win_rate")
                if k in data.get("performance", {})}),
            features=tuple(FeatureUse(**f) for f in data.get("features", [])),
            fills=tuple(FillRecord(**f) for f in data.get("fills", [])),
            data_lineage=str(data.get("data_lineage", "")),
            dataset_ref=str(data.get("dataset_ref", "")),
            parameter_count=int(data.get("parameter_count", 0)),
            sample_count=int(data.get("sample_count", 0)),
            holdout_ref=str(data.get("holdout_ref", "")),
            walk_forward_ref=str(data.get("walk_forward_ref", "")),
            cost_model_ref=str(data.get("cost_model_ref", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"candidate_id": self.candidate_id, "family": self.family,
                "specification_ref": self.specification_ref,
                "performance": self.performance.to_dict(),
                "features": [f.to_dict() for f in self.features],
                "fills": [f.to_dict() for f in self.fills],
                "data_lineage": self.data_lineage, "dataset_ref": self.dataset_ref,
                "parameter_count": self.parameter_count, "sample_count": self.sample_count,
                "holdout_ref": self.holdout_ref, "walk_forward_ref": self.walk_forward_ref,
                "cost_model_ref": self.cost_model_ref}


@dataclass(frozen=True)
class FailureAtom:
    """A reusable, named failure with the observable evidence that triggered it."""

    failure_id: str
    failing_surface: str
    artifact_refs: Tuple[str, ...]
    detail: str = ""
    severity: str = "MATERIAL"

    def to_dict(self) -> Dict[str, Any]:
        return {"failure_id": self.failure_id, "failing_surface": self.failing_surface,
                "artifact_refs": list(self.artifact_refs), "detail": self.detail,
                "severity": self.severity}


@dataclass(frozen=True)
class ValidationGateResult:
    gate_id: str
    passed: bool
    material: bool
    detail: str
    failure_atoms: Tuple[FailureAtom, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"gate_id": self.gate_id, "passed": self.passed,
                "material": self.material, "detail": self.detail,
                "failure_atoms": [a.to_dict() for a in self.failure_atoms]}


@dataclass(frozen=True)
class B7ValidationResult:
    """The FULL gate vector plus a deterministic promotion verdict. Gate
    materiality comes from the versioned B7GateContract (OCE-B7-PLAN-001), not
    hidden hardcoded tuples. A material (BLOCKING) hard failure rejects
    regardless of any other surface (B7.C3.S5: no single Sharpe/win rate can
    approve; uncertainty stays explicit)."""

    candidate_id: str
    gates: Tuple[ValidationGateResult, ...]
    material_failures: Tuple[str, ...]
    terminal: str            # VALIDATION_PASS | REJECTED
    failure_atoms: Tuple[FailureAtom, ...]
    promotion_packet_ref: str = ""
    gate_contract_id: str = ""
    not_executed_gates: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"candidate_id": self.candidate_id,
                "gates": [g.to_dict() for g in self.gates],
                "material_failures": list(self.material_failures),
                "terminal": self.terminal,
                "failure_atoms": [a.to_dict() for a in self.failure_atoms],
                "promotion_packet_ref": self.promotion_packet_ref,
                "gate_contract_id": self.gate_contract_id,
                "not_executed_gates": list(self.not_executed_gates)}


class B7ValidationGate:
    """Generic B7 (Quant Foundation, OCE-B7-PLAN-001) validation kernel. Gates
    inspect ONLY observable artifacts — PIT timestamps, fill artifacts, cost
    model, holdout/WF refs, mechanism spec, parameter/family multiplicity.
    Hidden ground truth is never consulted; the gates must discover the failure
    from the timestamps themselves. Materiality is read from the versioned
    B7GateContract (G5R-25): BLOCKING failures reject; ADVISORY failures are
    preserved and demote; NOT_EXECUTED doctrine gates are surfaced, never
    silently passed."""

    def run(self, candidate: StrategyCandidate,
            contract: Optional[B7GateContract] = None,
            cost_sensitivity_bad: bool = False,
            oos_degraded: bool = False,
            mechanism_plausible: bool = True,
            family_multiple_peak: bool = False) -> B7ValidationResult:
        contract = contract or DEFAULT_B7_GATE_CONTRACT
        gates: List[ValidationGateResult] = []

        # PIT (B7.C1.S5): reject future leakage from observable timestamps
        leaking = [f for f in candidate.features if f.leaks()]
        pit_pass = not leaking and bool(candidate.features)
        gates.append(ValidationGateResult(
            gate_id="PIT_INTEGRITY", passed=pit_pass, material=not pit_pass,
            detail=(f"{len(leaking)} feature(s) used before availability: "
                    f"{[f.feature_id for f in leaking]}") if leaking
                   else "all features available before decision time",
            failure_atoms=tuple(FailureAtom("LOOKAHEAD_LEAKAGE", "PIT_INTEGRITY",
                                            tuple(f.feature_id for f in leaking),
                                            "feature availability_time > decision_time")
                                for f in leaking)))

        # Execution realism (B7.C2.S4): reject impossible fills from artifacts
        bad_fills = [f for f in candidate.fills if f.impossible()]
        exec_pass = not bad_fills and bool(candidate.fills)
        gates.append(ValidationGateResult(
            gate_id="EXECUTION_REALISM", passed=exec_pass, material=not exec_pass,
            detail=(f"{len(bad_fills)} impossible fill(s): "
                    f"{[f.fill_id for f in bad_fills]}") if bad_fills
                   else "fills consistent with spread/depth/liquidity artifacts",
            failure_atoms=tuple(FailureAtom("UNREALISTIC_FILL_MODEL", "EXECUTION_REALISM",
                                            (f.fill_id,), "fill violates observable market artifacts")
                                for f in bad_fills)))

        # Cost sensitivity — surface present; a material result degrades gate
        cost_pass = not cost_sensitivity_bad
        gates.append(ValidationGateResult(
            gate_id="COST_SENSITIVITY", passed=cost_pass, material=False,
            detail="cost model applied; sensitivity surface retained",
            failure_atoms=()))

        # OOS / walk-forward — surface must exist; material degradation recorded
        oos_pass = candidate.holdout_ref and candidate.walk_forward_ref and not oos_degraded
        gates.append(ValidationGateResult(
            gate_id="OOS_WALK_FORWARD", passed=oos_pass, material=oos_degraded,
            detail=("holdout + walk-forward surfaces present" if oos_pass
                    else "OOS/WF surface missing or degraded"),
            failure_atoms=tuple([FailureAtom("OOS_DEGRADATION", "OOS_WALK_FORWARD",
                                             (candidate.holdout_ref,), "OOS degraded")])
            if oos_degraded else ()))

        # Mechanism plausibility
        mech_pass = mechanism_plausible
        gates.append(ValidationGateResult(
            gate_id="MECHANISM_PLAUSIBILITY", passed=mech_pass, material=False,
            detail="mechanism stated and plausible" if mech_pass else "mechanism missing/implausible",
            failure_atoms=tuple([FailureAtom("MECHANISM_MISSING", "MECHANISM_PLAUSIBILITY",
                                             (candidate.family,), "no mechanism card")])
            if not mech_pass else ()))

        # Family/parameter multiplicity — narrow optimum cannot certify
        family_pass = not (family_multiple_peak or
                           (candidate.parameter_count > 0 and candidate.sample_count > 0
                            and candidate.sample_count / max(candidate.parameter_count, 1) < 20))
        gates.append(ValidationGateResult(
            gate_id="FAMILY_MULTIPLICITY", passed=family_pass, material=False,
            detail=("sample/parameter ratio adequate" if family_pass
                    else "parameter family multiplicity risk"),
            failure_atoms=tuple([FailureAtom("FAMILY_MULTIPLICITY", "FAMILY_MULTIPLICITY",
                                             (candidate.specification_ref,),
                                             "narrow parameter optimum")])
            if not family_pass else ()))

        material = [g.gate_id for g in gates if not g.passed
                    and contract.materiality(g.gate_id) == "BLOCKING"]
        atoms = [a for g in gates for a in g.failure_atoms]
        terminal = "REJECTED" if material else "VALIDATION_PASS"
        return B7ValidationResult(candidate_id=candidate.candidate_id,
                                  gates=tuple(gates),
                                  material_failures=tuple(sorted(material)),
                                  terminal=terminal, failure_atoms=tuple(atoms),
                                  gate_contract_id=contract.contract_id,
                                  not_executed_gates=contract.not_executed_gates())


@dataclass(frozen=True)
class ResearchPriorityRecord:
    """PnL may raise research priority; it may NOT change truth rules."""

    priority_id: str
    claim_ref: str
    priority: str                    # PRIORITY_LOW | PRIORITY_NORMAL | PRIORITY_HIGH
    rationale: str = ""
    pnl_class_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"priority_id": self.priority_id, "claim_ref": self.claim_ref,
                "priority": self.priority, "rationale": self.rationale,
                "pnl_class_used": self.pnl_class_used}


@dataclass(frozen=True)
class PromotionDecision:
    """Separate from ResearchPriorityRecord — promotion requires the B7 gates.
    G5R-24 vocabulary: the validation result (VALIDATION_PASS / REJECTED) is a
    DIFFERENT layer from the research promotion decision (PROMOTION_CANDIDATE /
    REJECTED / HOLD), which is a DIFFERENT layer again from execution authority
    (always NONE here — promotion to validation is never execution)."""

    decision_id: str
    claim_ref: str
    decision: str                    # PROMOTION_CANDIDATE | REJECTED | HOLD
    validation_terminal: str = ""    # VALIDATION_PASS | REJECTED
    execution_authority: str = "NONE"
    authority_class: str = "B7_VALIDATION"
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"decision_id": self.decision_id, "claim_ref": self.claim_ref,
                "decision": self.decision,
                "validation_terminal": self.validation_terminal,
                "execution_authority": self.execution_authority,
                "authority_class": self.authority_class,
                "rationale": self.rationale}


# --------------------------------------------------------------------------- #
# S15 — unresolved pattern -> mechanism -> frozen protocol
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class UnresolvedPatternRecord:
    """A residual that does not fit known families (trend / mean reversion /
    carry / microstructure). UNKNOWN_FAMILY is legal — nearest-family forcing
    is prohibited. NEVER auto-generates a strategy (forbidden transition)."""

    pattern_id: str
    domain: str
    observations: Tuple[str, ...]
    conditions: Tuple[str, ...]
    data_quality_passed: bool
    known_family_fit_attempts: Tuple[str, ...]
    residual_behavior: str
    independence_evidence_refs: Tuple[str, ...]
    falsifiers: Tuple[str, ...]
    what_remains_unexplained: str
    family_label: str = "UNKNOWN_FAMILY"
    required_sensor: str = ""
    evidence_lineages: int = 0    # LEGACY DISPLAY ONLY — no decision authority (G5R-01)

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "UnresolvedPatternRecord":
        return cls(pattern_id=str(data["pattern_id"]), domain=str(data.get("domain", "")),
                   observations=tuple(data.get("observations", [])),
                   conditions=tuple(data.get("conditions", [])),
                   data_quality_passed=bool(data.get("data_quality_passed", True)),
                   known_family_fit_attempts=tuple(data.get("known_family_fit_attempts", [])),
                   residual_behavior=str(data.get("residual_behavior", "")),
                   independence_evidence_refs=tuple(data.get("independence_evidence_refs", [])),
                   falsifiers=tuple(data.get("falsifiers", [])),
                   what_remains_unexplained=str(data.get("what_remains_unexplained", "")),
                   family_label=str(data.get("family_label", "UNKNOWN_FAMILY")),
                   required_sensor=str(data.get("required_sensor", "")),
                   evidence_lineages=int(data.get("evidence_lineages", 0)))

    def to_dict(self) -> Dict[str, Any]:
        return {"pattern_id": self.pattern_id, "domain": self.domain,
                "observations": list(self.observations), "conditions": list(self.conditions),
                "data_quality_passed": self.data_quality_passed,
                "known_family_fit_attempts": list(self.known_family_fit_attempts),
                "residual_behavior": self.residual_behavior,
                "independence_evidence_refs": list(self.independence_evidence_refs),
                "falsifiers": list(self.falsifiers),
                "what_remains_unexplained": self.what_remains_unexplained,
                "family_label": self.family_label, "required_sensor": self.required_sensor,
                "evidence_lineages": self.evidence_lineages}


@dataclass(frozen=True)
class AnomalyCluster:
    """Deterministic grouping of unresolved observations on explicit
    feature/causal similarity only — no ML clustering."""

    cluster_id: str
    pattern_refs: Tuple[str, ...]
    similarity_signature: str
    independent_observations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"cluster_id": self.cluster_id, "pattern_refs": list(self.pattern_refs),
                "similarity_signature": self.similarity_signature,
                "independent_observations": self.independent_observations}


@dataclass(frozen=True)
class MechanismCard:
    """Mechanism hypothesis != strategy. Carries falsifiers and alternative
    explanations; no execution objects."""

    mechanism_id: str
    proposed_mechanism: str
    observable_inputs: Tuple[str, ...]
    constraints: Tuple[str, ...]
    state_transition_hypothesis: str
    realization_conditions: Tuple[str, ...]
    failure_conditions: Tuple[str, ...]
    domain: str
    evidence_refs: Tuple[str, ...]
    alternative_explanations: Tuple[str, ...]
    falsifiers: Tuple[str, ...]

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "MechanismCard":
        return cls(mechanism_id=str(data["mechanism_id"]),
                   proposed_mechanism=str(data.get("proposed_mechanism", "")),
                   observable_inputs=tuple(data.get("observable_inputs", [])),
                   constraints=tuple(data.get("constraints", [])),
                   state_transition_hypothesis=str(data.get("state_transition_hypothesis", "")),
                   realization_conditions=tuple(data.get("realization_conditions", [])),
                   failure_conditions=tuple(data.get("failure_conditions", [])),
                   domain=str(data.get("domain", "")),
                   evidence_refs=tuple(data.get("evidence_refs", [])),
                   alternative_explanations=tuple(data.get("alternative_explanations", [])),
                   falsifiers=tuple(data.get("falsifiers", [])))

    def to_dict(self) -> Dict[str, Any]:
        return {"mechanism_id": self.mechanism_id,
                "proposed_mechanism": self.proposed_mechanism,
                "observable_inputs": list(self.observable_inputs),
                "constraints": list(self.constraints),
                "state_transition_hypothesis": self.state_transition_hypothesis,
                "realization_conditions": list(self.realization_conditions),
                "failure_conditions": list(self.failure_conditions),
                "domain": self.domain, "evidence_refs": list(self.evidence_refs),
                "alternative_explanations": list(self.alternative_explanations),
                "falsifiers": list(self.falsifiers)}


@dataclass(frozen=True)
class FrozenExperimentProtocol:
    """Frozen BEFORE any result evaluation. Post-hoc threshold changes are
    prohibited; criteria cannot change after results exist. G5R-21: a frozen
    target-domain protocol additionally carries the target_domain it was frozen
    for, so a hypothesis can only authorize DOMAIN_VALIDATION_REQUIRED against a
    protocol whose registered domain matches."""

    protocol_id: str
    mechanism_ref: str
    dataset_ref: str
    time_range: str
    features: Tuple[str, ...]
    metrics: Tuple[str, ...]
    falsification_criteria: Tuple[str, ...]
    holdout_ref: str
    cost_execution_assumptions: Tuple[str, ...]
    promotion_criteria: Tuple[str, ...]
    target_domain: str = ""
    fingerprint: str = ""

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "FrozenExperimentProtocol":
        obj = cls(protocol_id=str(data["protocol_id"]),
                  mechanism_ref=str(data.get("mechanism_ref", "")),
                  dataset_ref=str(data.get("dataset_ref", "")),
                  time_range=str(data.get("time_range", "")),
                  features=tuple(data.get("features", [])),
                  metrics=tuple(data.get("metrics", [])),
                  falsification_criteria=tuple(data.get("falsification_criteria", [])),
                  holdout_ref=str(data.get("holdout_ref", "")),
                  cost_execution_assumptions=tuple(data.get("cost_execution_assumptions", [])),
                  promotion_criteria=tuple(data.get("promotion_criteria", [])),
                  target_domain=str(data.get("target_domain", "")))
        object.__setattr__(obj, "fingerprint", deterministic_hex("frozen_protocol", obj.to_dict()))
        return obj

    def to_dict(self) -> Dict[str, Any]:
        return {"protocol_id": self.protocol_id, "mechanism_ref": self.mechanism_ref,
                "dataset_ref": self.dataset_ref, "time_range": self.time_range,
                "features": list(self.features), "metrics": list(self.metrics),
                "falsification_criteria": list(self.falsification_criteria),
                "holdout_ref": self.holdout_ref,
                "cost_execution_assumptions": list(self.cost_execution_assumptions),
                "promotion_criteria": list(self.promotion_criteria),
                "target_domain": self.target_domain,
                "fingerprint": self.fingerprint}


# --------------------------------------------------------------------------- #
# S16 — CEREBUS manual doctrine / reproduction / contradiction / amendment
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DoctrineClaimRecord:
    """Exact, machine-representable manual claim. Parameters are NOT
    paraphrased; the manual file itself is never modified."""

    claim_id: str
    doctrine: str                  # CEREBUS
    manual_version: str
    source_path: str
    section: str
    page: str
    source_fingerprint: str
    exact_claim_representation: str
    numeric_parameters: Mapping[str, Any]
    structural_conditions: Tuple[str, ...]
    authority_class: str = "CEREBUS_MANUAL"
    current_status: str = "AUTHORITATIVE"

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "DoctrineClaimRecord":
        return cls(claim_id=str(data["claim_id"]), doctrine=str(data.get("doctrine", "CEREBUS")),
                   manual_version=str(data.get("manual_version", "")),
                   source_path=str(data.get("source_path", "")),
                   section=str(data.get("section", "")), page=str(data.get("page", "")),
                   source_fingerprint=str(data.get("source_fingerprint", "")),
                   exact_claim_representation=str(data.get("exact_claim_representation", "")),
                   numeric_parameters=dict(data.get("numeric_parameters", {})),
                   structural_conditions=tuple(data.get("structural_conditions", [])),
                   authority_class=str(data.get("authority_class", "CEREBUS_MANUAL")),
                   current_status=str(data.get("current_status", "AUTHORITATIVE")))

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_id": self.claim_id, "doctrine": self.doctrine,
                "manual_version": self.manual_version, "source_path": self.source_path,
                "section": self.section, "page": self.page,
                "source_fingerprint": self.source_fingerprint,
                "exact_claim_representation": self.exact_claim_representation,
                "numeric_parameters": dict(self.numeric_parameters),
                "structural_conditions": list(self.structural_conditions),
                "authority_class": self.authority_class, "current_status": self.current_status}


@dataclass(frozen=True)
class ReproductionRecord:
    """A reproduction is SEPARATE from the doctrine claim — never overwrites it.
    The protocol must be frozen BEFORE result evaluation."""

    reproduction_id: str
    claim_id: str
    dataset_lineage: str
    implementation_version: str
    exact_conditions: Tuple[str, ...]
    pit_status: str
    execution_assumptions: Tuple[str, ...]
    sample_size: int
    result: str
    uncertainty: str
    protocol_fingerprint: str
    independence_lineage: str
    known_deviations: Tuple[str, ...]

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "ReproductionRecord":
        return cls(reproduction_id=str(data["reproduction_id"]),
                   claim_id=str(data.get("claim_id", "")),
                   dataset_lineage=str(data.get("dataset_lineage", "")),
                   implementation_version=str(data.get("implementation_version", "")),
                   exact_conditions=tuple(data.get("exact_conditions", [])),
                   pit_status=str(data.get("pit_status", "")),
                   execution_assumptions=tuple(data.get("execution_assumptions", [])),
                   sample_size=int(data.get("sample_size", 0)),
                   result=str(data.get("result", "")),
                   uncertainty=str(data.get("uncertainty", "")),
                   protocol_fingerprint=str(data.get("protocol_fingerprint", "")),
                   independence_lineage=str(data.get("independence_lineage", "")),
                   known_deviations=tuple(data.get("known_deviations", [])))

    def deviates_from(self, claim: DoctrineClaimRecord) -> bool:
        """REPRODUCTION_REJECTED when the reproduction deviated from the
        governed claim conditions (definition mismatch, timestamp leakage,
        wrong session/tier/boundary...)."""
        return bool(self.known_deviations)

    def contradicts(self, claim: DoctrineClaimRecord) -> bool:
        if self.deviates_from(claim):
            return False
        return self.result == "CONTRADICTS_CLAIM"

    def to_dict(self) -> Dict[str, Any]:
        return {"reproduction_id": self.reproduction_id, "claim_id": self.claim_id,
                "dataset_lineage": self.dataset_lineage,
                "implementation_version": self.implementation_version,
                "exact_conditions": list(self.exact_conditions),
                "pit_status": self.pit_status,
                "execution_assumptions": list(self.execution_assumptions),
                "sample_size": self.sample_size, "result": self.result,
                "uncertainty": self.uncertainty,
                "protocol_fingerprint": self.protocol_fingerprint,
                "independence_lineage": self.independence_lineage,
                "known_deviations": list(self.known_deviations)}


@dataclass(frozen=True)
class DoctrineContradictionRecord:
    """A contradiction is a RELATION between two preserved objects. It never
    rewrites the doctrine claim or the manual."""

    contradiction_id: str
    claim_id: str
    reproduction_id: str
    contradiction_summary: str
    reproduction_confidence: str
    scope: str
    route: str = "MANUAL_PRESERVED + CONTRADICTION_OPEN"

    def to_dict(self) -> Dict[str, Any]:
        return {"contradiction_id": self.contradiction_id, "claim_id": self.claim_id,
                "reproduction_id": self.reproduction_id,
                "contradiction_summary": self.contradiction_summary,
                "reproduction_confidence": self.reproduction_confidence,
                "scope": self.scope, "route": self.route}


@dataclass(frozen=True)
class AmendmentProposal:
    """NOT a direct mutation. Only the governed doctrine-amendment authority
    (OPERATOR) may ratify; until ratified the manual remains canonical."""

    amendment_id: str
    original_claim_id: str
    contradicting_evidence_refs: Tuple[str, ...]
    scope: str
    possible_explanations: Tuple[str, ...]
    reproduction_confidence: str
    affected_surface: str
    dependent_strategies: Tuple[str, ...]
    requested_amendment: str
    rollback_implications: str
    operator_required: bool = True
    ratified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"amendment_id": self.amendment_id, "original_claim_id": self.original_claim_id,
                "contradicting_evidence_refs": list(self.contradicting_evidence_refs),
                "scope": self.scope, "possible_explanations": list(self.possible_explanations),
                "reproduction_confidence": self.reproduction_confidence,
                "affected_surface": self.affected_surface,
                "dependent_strategies": list(self.dependent_strategies),
                "requested_amendment": self.requested_amendment,
                "rollback_implications": self.rollback_implications,
                "operator_required": self.operator_required, "ratified": self.ratified}


# --------------------------------------------------------------------------- #
# S17 — provider observations / source-layer diagnosis
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ProviderObservation:
    """One provider-native packet. Provider identity is preserved; native and
    normalized values are kept separate (never averaged away)."""

    observation_id: str
    provider: str
    instrument_native_id: str
    instrument_canonical_id: str
    metric: str
    contract_type: str
    units: str
    timestamp_value: int
    time_window: str
    event_time: int
    receive_time: int
    mode: str                       # HISTORICAL | LIVE
    native_value: float
    normalized_value: Optional[float]  # G5R-12: absent normalized value stays UNKNOWN, never 0.0
    quality_state: str
    adapter_version: str

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "ProviderObservation":
        norm = data.get("normalized_value")
        return cls(observation_id=str(data["observation_id"]),
                   provider=str(data.get("provider", "")),
                   instrument_native_id=str(data.get("instrument_native_id", "")),
                   instrument_canonical_id=str(data.get("instrument_canonical_id", "")),
                   metric=str(data.get("metric", "")),
                   contract_type=str(data.get("contract_type", "")),
                   units=str(data.get("units", "")),
                   timestamp_value=int(data.get("timestamp_value", 0)),
                   time_window=str(data.get("time_window", "")),
                   event_time=int(data.get("event_time", 0)),
                   receive_time=int(data.get("receive_time", 0)),
                   mode=str(data.get("mode", "HISTORICAL")),
                   native_value=float(data.get("native_value", 0.0)),
                   normalized_value=float(norm) if norm is not None else None,
                   quality_state=str(data.get("quality_state", "OK")),
                   adapter_version=str(data.get("adapter_version", "")))

    @property
    def has_normalized_value(self) -> bool:
        return self.normalized_value is not None

    def to_dict(self) -> Dict[str, Any]:
        return {"observation_id": self.observation_id, "provider": self.provider,
                "instrument_native_id": self.instrument_native_id,
                "instrument_canonical_id": self.instrument_canonical_id,
                "metric": self.metric, "contract_type": self.contract_type,
                "units": self.units, "timestamp_value": self.timestamp_value,
                "time_window": self.time_window, "event_time": self.event_time,
                "receive_time": self.receive_time, "mode": self.mode,
                "native_value": self.native_value, "normalized_value": self.normalized_value,
                "quality_state": self.quality_state, "adapter_version": self.adapter_version}


@dataclass(frozen=True)
class ProviderSemanticsRecord:
    """Semantic contract for one provider+metric. The S17 diagnosis order is:
    provider semantics -> instrument identity -> adapter -> normalization ->
    time semantics -> quality -> disagreement surface."""

    provider: str
    metric: str
    native_units: str
    canonical_units: str
    instrument_mapping_ok: bool
    adapter_version: str
    time_window: str
    timestamp_semantics: str        # EVENT | RECEIVE | WINDOW_START
    quality_state: str
    normalization_valid: bool = True   # adapter converts native -> canonical correctly
    methodology_notes: str = ""
    canonical_instrument: str = ""    # G5R-13: registered canonical instrument identity
    contract_type: str = ""           # G5R-13: PERP_LINEAR / SPOT / QUARTERLY ...
    compatible_adapter_versions: Tuple[str, ...] = ()  # G5R-11: explicit compatible-version contract

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "ProviderSemanticsRecord":
        return cls(provider=str(data["provider"]), metric=str(data["metric"]),
                   native_units=str(data.get("native_units", "")),
                   canonical_units=str(data.get("canonical_units", "")),
                   instrument_mapping_ok=bool(data.get("instrument_mapping_ok", True)),
                   adapter_version=str(data.get("adapter_version", "")),
                   time_window=str(data.get("time_window", "")),
                   timestamp_semantics=str(data.get("timestamp_semantics", "EVENT")),
                   quality_state=str(data.get("quality_state", "OK")),
                   normalization_valid=bool(data.get("normalization_valid", True)),
                   methodology_notes=str(data.get("methodology_notes", "")),
                   canonical_instrument=str(data.get("canonical_instrument", "")),
                   contract_type=str(data.get("contract_type", "")),
                   compatible_adapter_versions=tuple(data.get("compatible_adapter_versions", [])))

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "metric": self.metric,
                "native_units": self.native_units, "canonical_units": self.canonical_units,
                "instrument_mapping_ok": self.instrument_mapping_ok,
                "adapter_version": self.adapter_version, "time_window": self.time_window,
                "timestamp_semantics": self.timestamp_semantics,
                "quality_state": self.quality_state,
                "methodology_notes": self.methodology_notes,
                "canonical_instrument": self.canonical_instrument,
                "contract_type": self.contract_type,
                "compatible_adapter_versions": list(self.compatible_adapter_versions)}


@dataclass(frozen=True)
class SourceDiagnosisStep:
    layer: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"layer": self.layer, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class SourceDiagnosisResult:
    """The localized cause, discovered strictly in canonical layer order. A
    failure at layer k blocks all later layers (source first).

    Terminals (G5R-14): REPAIRABLE_SOURCE_MISMATCH | GENUINE_SOURCE_DISAGREEMENT |
    NO_DISAGREEMENT | DATA_INSUFFICIENT. NO_DISAGREEMENT never terminates as
    GENUINE_SOURCE_DISAGREEMENT.
    """

    disagreement_id: str
    steps: Tuple[SourceDiagnosisStep, ...]
    cause: str                       # UNIT_MISMATCH | INSTRUMENT_MISMATCH |
                                     # CONTRACT_TYPE_MISMATCH | ADAPTER_MISMATCH |
                                     # NORMALIZATION_MISMATCH | NORMALIZATION_MISSING |
                                     # TIME_WINDOW_MISMATCH | QUALITY_FAILURE |
                                     # SEMANTIC_CONTRACT_MISSING | GENUINE_SOURCE_DISAGREEMENT |
                                     # NO_DISAGREEMENT
    provider_a: str
    provider_b: str
    terminal: str                    # REPAIRABLE_SOURCE_MISMATCH | GENUINE_SOURCE_DISAGREEMENT |
                                     # NO_DISAGREEMENT | DATA_INSUFFICIENT

    def to_dict(self) -> Dict[str, Any]:
        return {"disagreement_id": self.disagreement_id,
                "steps": [s.to_dict() for s in self.steps], "cause": self.cause,
                "provider_a": self.provider_a, "provider_b": self.provider_b,
                "terminal": self.terminal}


def diagnose_provider_disagreement(
    obs_a: ProviderObservation, obs_b: ProviderObservation,
    sem_a: ProviderSemanticsRecord, sem_b: ProviderSemanticsRecord,
    tolerance: Optional[DisagreementToleranceContract] = None,
) -> SourceDiagnosisResult:
    """Deterministic source-layer diagnosis. Only AFTER layers 1..6 pass may
    higher-level market-field interpretation be challenged (layer 7).

    G5R-11 adapter versions must MATCH (or an explicit compatible-version
    contract); G5R-12 absent normalized values stay MISSING (never 0.0) and
    block the comparison; G5R-13 time window, quality contract, contract type
    and canonical instrument identity are each validated; G5R-14 equal clean
    values terminate NO_DISAGREEMENT (never genuine); G5R-15 materiality uses
    the explicit tolerance contract, not raw float inequality alone."""
    steps: List[SourceDiagnosisStep] = []

    def add(layer: str, ok: bool, detail: str = "") -> bool:
        steps.append(SourceDiagnosisStep(layer, ok, detail))
        return ok

    def result(cause: str, terminal: str) -> SourceDiagnosisResult:
        return SourceDiagnosisResult(
            disagreement_id=deterministic_hex("src_diag", obs_a.observation_id,
                                              obs_b.observation_id),
            steps=tuple(steps), cause=cause,
            provider_a=obs_a.provider, provider_b=obs_b.provider,
            terminal=terminal)

    # 0 provider semantics contract present (G5R-10 fail closed handled at the
    # runner level; the kernel still refuses to compare without both contracts)
    if sem_a is None or sem_b is None:
        add("provider_semantics", False, "semantic contract missing")
        return result("SEMANTIC_CONTRACT_MISSING", "DATA_INSUFFICIENT")
    # 1 provider semantics (units + methodology)
    ok = add("provider_semantics", obs_a.units == sem_a.native_units
             and obs_b.units == sem_b.native_units,
             f"A={sem_a.native_units} B={sem_b.native_units}")
    if not ok:
        return result("UNIT_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH")
    # 2 instrument identity (canonical instrument + contract type in ONE step)
    canon_ok = (obs_a.instrument_canonical_id == obs_b.instrument_canonical_id
                and sem_a.instrument_mapping_ok and sem_b.instrument_mapping_ok)
    if canon_ok and sem_a.canonical_instrument:
        canon_ok = (obs_a.instrument_canonical_id == sem_a.canonical_instrument
                    and obs_b.instrument_canonical_id == sem_b.canonical_instrument)
    ct_ok = True
    if (sem_a.contract_type or sem_b.contract_type) and canon_ok:
        # G5R-13: contract-type compatibility is BOTH per-provider (each
        # observation matches its own registered semantic contract) AND
        # pairwise (the two observations must be on the same contract type —
        # a SPOT and a PERP_LINEAR reading of the same metric are not
        # comparable even when each matches its own contract).
        ct_ok = (obs_a.contract_type == sem_a.contract_type
                 and obs_b.contract_type == sem_b.contract_type
                 and obs_a.contract_type == obs_b.contract_type)
    ok = add("instrument_identity", canon_ok and ct_ok,
             f"canonical A={obs_a.instrument_canonical_id} B={obs_b.instrument_canonical_id}; "
             f"contract A={obs_a.contract_type}/{sem_a.contract_type} "
             f"B={obs_b.contract_type}/{sem_b.contract_type}")
    if not ok:
        if ct_ok and not canon_ok:
            cause, terminal = "INSTRUMENT_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH"
        elif canon_ok and not ct_ok:
            cause, terminal = "CONTRACT_TYPE_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH"
        else:
            cause, terminal = "INSTRUMENT_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH"
        return result(cause, terminal)
    # 3 adapter — version must MATCH the registered semantic contract (or an
    # explicit compatible-version contract exists)
    def _adapter_ok(obs: ProviderObservation, sem: ProviderSemanticsRecord) -> bool:
        if not obs.adapter_version or not sem.adapter_version:
            return False
        if obs.adapter_version == sem.adapter_version:
            return True
        return obs.adapter_version in (sem.compatible_adapter_versions or ())

    ok = add("adapter", _adapter_ok(obs_a, sem_a) and _adapter_ok(obs_b, sem_b),
             f"A={obs_a.adapter_version}/{sem_a.adapter_version} "
             f"B={obs_b.adapter_version}/{sem_b.adapter_version}")
    if not ok:
        return result("ADAPTER_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH")
    # 4 normalization (canonical units agree AND each adapter's native->canonical
    # conversion is valid AND normalized values are actually present)
    if (not obs_a.has_normalized_value) or (not obs_b.has_normalized_value):
        add("normalization", False, "normalized value missing (never coerced to 0.0)")
        return result("NORMALIZATION_MISSING", "DATA_INSUFFICIENT")
    ok = add("normalization", sem_a.canonical_units == sem_b.canonical_units
             and sem_a.normalization_valid and sem_b.normalization_valid
             and obs_a.has_normalized_value and obs_b.has_normalized_value,
             f"canonical A={sem_a.canonical_units} B={sem_b.canonical_units}")
    if not ok:
        return result("NORMALIZATION_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH")
    # 5 time semantics — observation window must match the provider semantic
    # window AND the two observations must share the window semantics
    ok = add("time_semantics",
             obs_a.time_window == sem_a.time_window
             and obs_b.time_window == sem_b.time_window
             and sem_a.timestamp_semantics == sem_b.timestamp_semantics,
             f"windows A={obs_a.time_window}/{sem_a.time_window} "
             f"B={obs_b.time_window}/{sem_b.time_window}")
    if not ok:
        return result("TIME_WINDOW_MISMATCH", "REPAIRABLE_SOURCE_MISMATCH")
    # 6 quality — observation quality must meet the semantic contract's
    # required quality state
    ok = add("quality",
             obs_a.quality_state == sem_a.quality_state
             and obs_b.quality_state == sem_b.quality_state,
             f"quality A={obs_a.quality_state}/{sem_a.quality_state} "
             f"B={obs_b.quality_state}/{sem_b.quality_state}")
    if not ok:
        return result("QUALITY_FAILURE", "REPAIRABLE_SOURCE_MISMATCH")
    # 7 disagreement surface — only reached when source layers are clean.
    # Materiality uses the explicit tolerance contract (G5R-15); equal clean
    # values terminate NO_DISAGREEMENT, never GENUINE (G5R-14).
    va, vb = obs_a.normalized_value, obs_b.normalized_value
    assert va is not None and vb is not None
    tol = tolerance or DisagreementToleranceContract(
        contract_id="default", metric=obs_a.metric, units=obs_a.units)
    if va == vb or not disagreement_is_material(va, vb, tol):
        add("disagreement_surface", True,
            f"equal/within-tolerance normalized values ({va} vs {vb}); no disagreement")
        return result("NO_DISAGREEMENT", "NO_DISAGREEMENT")
    add("disagreement_surface", True,
        f"persistent disagreement under clean semantics ({va} vs {vb})")
    return result("GENUINE_SOURCE_DISAGREEMENT", "GENUINE_SOURCE_DISAGREEMENT")


def disagreement_is_material(a: float, b: float, tol: DisagreementToleranceContract) -> bool:
    """Raw float inequality is NOT the universal disagreement definition (G5R-15).
    Materiality is decided by the explicit provisional tolerance contract:
    absolute, relative or basis-point tolerance. Deterministic; values are NOT
    constitutionalized. Public API (re-exported by engine.g5r)."""
    diff = abs(a - b)
    if diff == 0.0:
        return False
    scale = max(abs(a), abs(b), 1e-9)
    if tol.absolute_tolerance and diff <= tol.absolute_tolerance:
        return False
    if tol.relative_tolerance and (diff / scale) <= tol.relative_tolerance:
        return False
    if tol.basis_points_tolerance and (diff / scale * 1e4) <= tol.basis_points_tolerance:
        return False
    return True


@dataclass(frozen=True)
class SourceDisagreementRecord:
    """Preserved source-layer disagreement — never averaged into consensus."""

    disagreement_id: str
    provider_a: str
    provider_b: str
    metric: str
    value_a: Optional[float]
    value_b: Optional[float]
    diagnosis: SourceDiagnosisResult
    preserved: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"disagreement_id": self.disagreement_id, "provider_a": self.provider_a,
                "provider_b": self.provider_b, "metric": self.metric,
                "value_a": self.value_a, "value_b": self.value_b,
                "diagnosis": self.diagnosis.to_dict(), "preserved": self.preserved}


# --------------------------------------------------------------------------- #
# S18 — sensor requirements / availability / search demand
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SensorRequirement:
    """What a claim/mechanism NEEDS to observe; alternative evidence is
    explicitly insufficient."""

    requirement_id: str
    claim_ref: str
    required_observable: str
    resolution: str
    history_depth: str
    instrument_coverage: Tuple[str, ...]
    time_semantics: str
    quality_minimum: str
    why_required: str
    alternative_insufficient: str

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "SensorRequirement":
        return cls(requirement_id=str(data["requirement_id"]),
                   claim_ref=str(data.get("claim_ref", "")),
                   required_observable=str(data.get("required_observable", "")),
                   resolution=str(data.get("resolution", "")),
                   history_depth=str(data.get("history_depth", "")),
                   instrument_coverage=tuple(data.get("instrument_coverage", [])),
                   time_semantics=str(data.get("time_semantics", "")),
                   quality_minimum=str(data.get("quality_minimum", "")),
                   why_required=str(data.get("why_required", "")),
                   alternative_insufficient=str(data.get("alternative_insufficient", "")))

    def to_dict(self) -> Dict[str, Any]:
        return {"requirement_id": self.requirement_id, "claim_ref": self.claim_ref,
                "required_observable": self.required_observable,
                "resolution": self.resolution, "history_depth": self.history_depth,
                "instrument_coverage": list(self.instrument_coverage),
                "time_semantics": self.time_semantics,
                "quality_minimum": self.quality_minimum,
                "why_required": self.why_required,
                "alternative_insufficient": self.alternative_insufficient}


@dataclass(frozen=True)
class DataAvailabilityRecord:
    """From actual/synthetic Sensor Fabric capability declarations. UNKNOWN is
    NOT AVAILABLE. PARTIAL/CURRENT_ONLY never satisfies historical coverage.
    G5R-16/17: adequacy checks the FULL requirement vector (observable, status,
    verified, resolution, history, instrument coverage, time semantics, quality
    minimum, provenance/certification) — never status+history alone."""

    observable: str
    status: str
    history_depth: str = ""
    instrument_coverage: Tuple[str, ...] = ()
    claimed: bool = False
    verified: bool = False
    source: str = "CRYPTO_SENSOR_FABRIC"
    resolution: str = ""            # G5R-16
    time_semantics: str = ""        # G5R-16
    quality_state: str = ""         # G5R-16
    certification: str = ""         # G5R-17 provenance: AUTHORITATIVE_SYNTHETIC_SENSOR_FIXTURE | CRYPTO_SENSOR_FABRIC_CERTIFICATION

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "DataAvailabilityRecord":
        status = str(data.get("status", "UNKNOWN"))
        if status not in DATA_AVAILABILITY_STATUSES:
            raise ValueError(f"unknown data availability status {status!r}")
        return cls(observable=str(data["observable"]), status=status,
                   history_depth=str(data.get("history_depth", "")),
                   instrument_coverage=tuple(data.get("instrument_coverage", [])),
                   claimed=bool(data.get("claimed", False)),
                   verified=bool(data.get("verified", False)),
                   source=str(data.get("source", "CRYPTO_SENSOR_FABRIC")),
                   resolution=str(data.get("resolution", "")),
                   time_semantics=str(data.get("time_semantics", "")),
                   quality_state=str(data.get("quality_state", "")),
                   certification=str(data.get("certification", "")))

    def adequate_history(self, requirement: SensorRequirement) -> bool:
        """AVAILABLE != ADEQUATE. Full-vector adequacy under the provisional
        contract (G5R-16/17): observable match, status AVAILABLE, verified,
        known provenance, sufficient resolution, sufficient history, required
        instrument coverage, compatible time semantics, quality minimum."""
        if self.observable != requirement.required_observable:
            return False
        if self.status != "AVAILABLE":
            return False
        if not self.verified:
            return False
        if not self.certification or not self.source \
                or str(self.certification).strip().upper() == "UNKNOWN":
            return False                     # UNKNOWN provenance => not adequate
        if requirement.resolution and self.resolution != requirement.resolution:
            return False
        if not HistorySpan.from_string(self.history_depth).satisfies(
                HistorySpan.from_string(requirement.history_depth)):
            return False
        if not set(requirement.instrument_coverage) <= set(self.instrument_coverage):
            return False
        if requirement.time_semantics and self.time_semantics != requirement.time_semantics:
            return False
        if requirement.quality_minimum == "VERIFIED":
            if not self.verified:
                return False
        elif requirement.quality_minimum and self.quality_state != requirement.quality_minimum:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"observable": self.observable, "status": self.status,
                "history_depth": self.history_depth,
                "instrument_coverage": list(self.instrument_coverage),
                "claimed": self.claimed, "verified": self.verified, "source": self.source,
                "resolution": self.resolution, "time_semantics": self.time_semantics,
                "quality_state": self.quality_state, "certification": self.certification}


@dataclass(frozen=True)
class SearchDemand:
    """Endogenous institutional search demand. NOT claim validation; a SearchDemand
    fires because the institution cannot currently adjudicate the claim.
    G5R-19: required instruments are SEPARATE from acceptable provider/source
    classes — an instrument id is never stored as if it were a provider.
    (`acceptable_sources` is a LEGACY DISPLAY field retained only for old-call
    compatibility; decision semantics live in required_instruments /
    acceptable_source_classes.)"""

    demand_id: str
    blocked_claim: str
    required_sensor: str
    reason: str
    required_instruments: Tuple[str, ...] = ()
    acceptable_source_classes: Tuple[str, ...] = ()
    history_requirement: str = ""
    quality_requirement: str = ""
    value_of_information_class: str = "HIGH"
    status: str = "OPEN"
    reopen_condition: str = ""
    acceptable_sources: Tuple[str, ...] = ()   # LEGACY DISPLAY ONLY (G5R-19)

    def to_dict(self) -> Dict[str, Any]:
        return {"demand_id": self.demand_id, "blocked_claim": self.blocked_claim,
                "required_sensor": self.required_sensor, "reason": self.reason,
                "required_instruments": list(self.required_instruments),
                "acceptable_source_classes": list(self.acceptable_source_classes),
                "history_requirement": self.history_requirement,
                "quality_requirement": self.quality_requirement,
                "value_of_information_class": self.value_of_information_class,
                "status": self.status, "reopen_condition": self.reopen_condition,
                "acceptable_sources_legacy": list(self.acceptable_sources)}


# --------------------------------------------------------------------------- #
# S19 — domain transfer
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TransferInvariantMap:
    """Explicit structural mapping. A name match alone is insufficient; every
    invariant axis must be mapped or explicitly broken."""

    source_domain: str
    target_domain: str
    source_definition: str
    target_candidate_definition: str
    source_observables: Tuple[str, ...]
    target_observables: Tuple[str, ...]
    units_scales: Tuple[str, ...]
    state_semantics: Tuple[str, ...]
    market_structure_assumptions: Tuple[str, ...]
    mechanism_invariants: Tuple[str, ...]
    known_broken_assumptions: Tuple[str, ...]
    required_sensors: Tuple[str, ...]
    falsifiers: Tuple[str, ...]

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "TransferInvariantMap":
        return cls(source_domain=str(data["source_domain"]),
                   target_domain=str(data["target_domain"]),
                   source_definition=str(data.get("source_definition", "")),
                   target_candidate_definition=str(data.get("target_candidate_definition", "")),
                   source_observables=tuple(data.get("source_observables", [])),
                   target_observables=tuple(data.get("target_observables", [])),
                   units_scales=tuple(data.get("units_scales", [])),
                   state_semantics=tuple(data.get("state_semantics", [])),
                   market_structure_assumptions=tuple(data.get("market_structure_assumptions", [])),
                   mechanism_invariants=tuple(data.get("mechanism_invariants", [])),
                   known_broken_assumptions=tuple(data.get("known_broken_assumptions", [])),
                   required_sensors=tuple(data.get("required_sensors", [])),
                   falsifiers=tuple(data.get("falsifiers", [])))

    def structurally_sound(self) -> bool:
        return (not self.known_broken_assumptions
                and bool(self.mechanism_invariants)
                and bool(self.source_observables)
                and bool(self.target_observables))

    def to_dict(self) -> Dict[str, Any]:
        return {"source_domain": self.source_domain, "target_domain": self.target_domain,
                "source_definition": self.source_definition,
                "target_candidate_definition": self.target_candidate_definition,
                "source_observables": list(self.source_observables),
                "target_observables": list(self.target_observables),
                "units_scales": list(self.units_scales),
                "state_semantics": list(self.state_semantics),
                "market_structure_assumptions": list(self.market_structure_assumptions),
                "mechanism_invariants": list(self.mechanism_invariants),
                "known_broken_assumptions": list(self.known_broken_assumptions),
                "required_sensors": list(self.required_sensors),
                "falsifiers": list(self.falsifiers)}


@dataclass(frozen=True)
class DomainTransferHypothesis:
    """A transfer is never an FX strategy — at most a hypothesis to be tested
    under a frozen target-domain protocol."""

    hypothesis_id: str
    source_concept: str
    source_domain: str
    target_domain: str
    source_evidence_refs: Tuple[str, ...]
    transfer_map: TransferInvariantMap
    frozen_target_protocol_ref: str = ""

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "DomainTransferHypothesis":
        return cls(hypothesis_id=str(data["hypothesis_id"]),
                   source_concept=str(data.get("source_concept", "")),
                   source_domain=str(data.get("source_domain", "")),
                   target_domain=str(data.get("target_domain", "")),
                   source_evidence_refs=tuple(data.get("source_evidence_refs", [])),
                   transfer_map=TransferInvariantMap.from_fixture(data["transfer_map"]),
                   frozen_target_protocol_ref=str(data.get("frozen_target_protocol_ref", "")))

    def to_dict(self) -> Dict[str, Any]:
        return {"hypothesis_id": self.hypothesis_id,
                "source_concept": self.source_concept,
                "source_domain": self.source_domain, "target_domain": self.target_domain,
                "source_evidence_refs": list(self.source_evidence_refs),
                "transfer_map": self.transfer_map.to_dict(),
                "frozen_target_protocol_ref": self.frozen_target_protocol_ref}


@dataclass(frozen=True)
class DomainClaimRecord:
    """Every G5 claim retains its full lineage: source domain, target domain if
    transfer, evidence refs, source/validation authority, lifecycle state,
    disposition, epoch, dependent objects, falsifiers, reopen conditions."""

    claim_id: str
    claim_type: str
    domain: str
    source_authority: str
    validation_authority: str
    evidence_refs: Tuple[str, ...]
    current_lifecycle_state: str
    current_disposition: str
    epoch: str = ""
    target_domain: str = ""
    dependent_objects: Tuple[str, ...] = ()
    falsifiers: Tuple[str, ...] = ()
    reopen_conditions: Tuple[str, ...] = ()

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "DomainClaimRecord":
        return cls(claim_id=str(data["claim_id"]),
                   claim_type=str(data.get("claim_type", "ALPHA_CANDIDATE")),
                   domain=str(data.get("domain", "")),
                   source_authority=str(data.get("source_authority", "")),
                   validation_authority=str(data.get("validation_authority", "")),
                   evidence_refs=tuple(data.get("evidence_refs", [])),
                   current_lifecycle_state=str(data.get("current_lifecycle_state", "CANDIDATE")),
                   current_disposition=str(data.get("current_disposition", "")),
                   epoch=str(data.get("epoch", "")),
                   target_domain=str(data.get("target_domain", "")),
                   dependent_objects=tuple(data.get("dependent_objects", [])),
                   falsifiers=tuple(data.get("falsifiers", [])),
                   reopen_conditions=tuple(data.get("reopen_conditions", [])))

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_id": self.claim_id, "claim_type": self.claim_type,
                "domain": self.domain, "source_authority": self.source_authority,
                "validation_authority": self.validation_authority,
                "evidence_refs": list(self.evidence_refs),
                "current_lifecycle_state": self.current_lifecycle_state,
                "current_disposition": self.current_disposition, "epoch": self.epoch,
                "target_domain": self.target_domain,
                "dependent_objects": list(self.dependent_objects),
                "falsifiers": list(self.falsifiers),
                "reopen_conditions": list(self.reopen_conditions)}