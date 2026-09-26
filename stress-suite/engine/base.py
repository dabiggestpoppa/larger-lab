"""Shared primitives for the OCE Institutional Stress Suite harness.

G1 scope: deterministic, local-first, model-free. Nothing in this package may
mutate production/cloud/capital, call a model, or depend on wall-clock time for
correctness. All identifiers are derived deterministically from content so that
replay is byte-stable across runs and machines.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Versioning
HARNESS_VERSION = "0.1.0"
PHASE_EDGE_TABLE_CONTRACT = "1.0.0"
LIFECYCLE_EDGE_TABLE_CONTRACT = "1.0.0"
EVALUATION_CONTRACT_VERSION = "1.0.0"

# A-009 does not fully specify the lifecycle edge table; it is a provisional
# test contract, not constitutional truth. See G0-pack AMB-06. Replacing it
# later MUST NOT rewrite historical traces (see lifecycle.replace_edge_table).
PROVISIONAL = "PROVISIONAL_TEST_CONTRACT"

_DEFAULT_SCHEMA_ID_BASE = "https://github.com/dabiggestpoppa/larger-lab/schema/stress-suite/"


def deterministic_hex(*parts: Any, length: int = 16) -> str:
    """Stable hex digest from canonical parts (no randomness or clock)."""
    blob = "\x1f".join(_canon(p) for p in parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:length]


def _canon(value: Any) -> str:
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        return json.dumps([_canon(v) for v in value], sort_keys=True)
    if isinstance(value, Enum):
        return value.value
    return str(value)


def schema_id(name: str) -> str:
    return _DEFAULT_SCHEMA_ID_BASE + name + ".json"


# --------------------------------------------------------------------------- #
# Determinism helpers
# --------------------------------------------------------------------------- #

def deterministic_timestamp(seq: int, epoch_anchor: str = "2000-01-01T00:00:00Z") -> str:
    """Fake but stable timestamp derived only from seq (for reproducible replay).

    Real clocks would break deterministic replay; scenario runs use an injected
    clock or these seq-derived stamps. Lifting an existing EpochManifest anchor
    is handled by callers.
    """
    import datetime as _dt

    base = _dt.datetime.fromisoformat(epoch_anchor.replace("Z", "+00:00"))
    return (base + _dt.timedelta(seconds=seq)).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ReplayClock:
    """Deterministic clock source. A real-replay run uses seq increments."""
    epoch_anchor: str = "2000-01-01T00:00:00Z"

    def stamp(self, seq: int) -> str:
        return deterministic_timestamp(seq, self.epoch_anchor)


# --------------------------------------------------------------------------- #
# Shared enums
# --------------------------------------------------------------------------- #

class MutationClass(str, Enum):
    """Structural class of a proposed side effect (A-010 §3, Constitution §7.6)."""
    READ_ONLY = "READ_ONLY"
    REVERSIBLE = "REVERSIBLE"
    HOMEOSTATIC_REPAIR = "HOMEOSTATIC_REPAIR"
    ONTOLOGY_MUTATION = "ONTOLOGY_MUTATION"
    ARCHITECTURE_MUTATION = "ARCHITECTURE_MUTATION"
    AUTHORITY_MUTATION = "AUTHORITY_MUTATION"
    CAPITAL_MUTATION = "CAPITAL_MUTATION"
    IRREVERSIBLE = "IRREVERSIBLE"


class AuthorityLevel(str, Enum):
    OBSERVER = "OBSERVER"
    WORKER = "WORKER"
    PO = "PO"
    GOVERNOR = "GOVERNOR"
    OPERATOR = "OPERATOR"


class KnowledgeLifecycleState(str, Enum):
    OBSERVED = "OBSERVED"
    CANDIDATE = "CANDIDATE"
    TESTED = "TESTED"
    PROMOTED = "PROMOTED"
    ACTIVE = "ACTIVE"
    CHALLENGED = "CHALLENGED"
    REVALIDATED = "REVALIDATED"
    DEMOTED = "DEMOTED"
    DORMANT = "DORMANT"
    REACTIVATED = "REACTIVATED"
    SUPERSEDED = "SUPERSEDED"


class PhaseState(str, Enum):
    STABLE = "STABLE"
    WATCH = "WATCH"
    ESCALATION_REVIEW = "ESCALATION_REVIEW"
    HOMEOSTATIC_REPAIR = "HOMEOSTATIC_REPAIR"
    TRANSFORMATION_CANDIDATE = "TRANSFORMATION_CANDIDATE"
    TRANSFORMATION_WINDOW = "TRANSFORMATION_WINDOW"
    RECONSOLIDATION = "RECONSOLIDATION"
    NEW_STABLE = "NEW_STABLE"
    ROLLBACK = "ROLLBACK"
    NO_CHANGE = "NO_CHANGE"
    UNRESOLVED = "UNRESOLVED"
    PLURAL_MODEL_STATE = "PLURAL_MODEL_STATE"
    OPERATOR_HOLD = "OPERATOR_HOLD"
    DATA_BLOCKED = "DATA_BLOCKED"
    AUTHORITY_BLOCKED = "AUTHORITY_BLOCKED"


class CapabilityTruthLabel(str, Enum):
    """Constitution Article II labels. Kept SEPARATE from M4 (AMB-07)."""
    IDEA = "IDEA"
    SPECIFIED = "SPECIFIED"
    SCAFFOLDED = "SCAFFOLDED"
    IMPLEMENTED_UNVERIFIED = "IMPLEMENTED_UNVERIFIED"
    VERIFIED_ISOLATED = "VERIFIED_ISOLATED"
    VERIFIED_INTEGRATED = "VERIFIED_INTEGRATED"
    VERIFIED_E2E = "VERIFIED_E2E"
    OPERATIONALLY_PROVEN = "OPERATIONALLY_PROVEN"
    QUARANTINED = "QUARANTINED"
    FALSIFIED = "FALSIFIED"
    DEPRECATED = "DEPRECATED"


class EvidenceChannel(str, Enum):
    """A-010 §4 evidence channels. Kept as a vector, never a mandated scalar."""
    RELIABILITY_DEGRADATION = "reliability_degradation"
    EXCEPTION_BURDEN = "exception_burden"
    INDEPENDENT_CONTRADICTION = "independent_contradiction"
    UNRESOLVED_PATTERN_DENSITY = "unresolved_pattern_density"
    DEPENDENCY_CENTRALITY = "dependency_centrality"
    EXTERNAL_ENVIRONMENT_SHIFT = "external_environment_shift"
    OPPORTUNITY_COST_OF_STABILITY = "opportunity_cost_of_stability"
    COST_AND_REVERSIBILITY = "cost_and_reversibility"


# --------------------------------------------------------------------------- #
# Shared base types
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Provenance:
    """Attributable origin; must NEVER be deleted by a lifecycle transition."""
    source_kind: str            # STIMULUS / OBSERVATION / EXPERIMENT / FIXTURE / OPERATOR / DETERMINISTIC / AGENT_CLAIM
    source_label: str
    producing_actor: str = ""
    assigning_actor: str = ""   # allocator origin (G0 Q3) — observable, not disqualifying
    task_ref: str = ""
    source_lineage: str = ""
    retrieval_lineage: str = ""
    prior_conclusion_exposure: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TransitionRecord:
    """One attributed state transition. Shared by M4 and M5 (identical shape,
    but each machine owns its own records — see separation tests).

    G1R-05: legality is carried EXPLICITLY (allowed / applied / violation) so an
    illegal attempted self-transition can never be misread as allowed by
    comparing final to initial state.
    """
    transition_id: str
    machine: str                # "phase" | "lifecycle"
    object_id: Optional[str]
    from_state: str
    to_state: str
    reason: str
    evidence_refs: List[str]
    actor: str
    authority_basis: str
    authority_level: str
    contract_version: str
    seq: int
    timestamp: str
    allowed: bool = True
    applied: bool = True
    violation: Optional[str] = None
    cycle: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
