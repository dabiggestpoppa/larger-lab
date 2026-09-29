"""Larger Lab Model Foundry — governed scientific substrate (MF-B0..MF-B4).

This package builds the *laboratory*, not a trained model:

* :mod:`foundry.constitution` / :mod:`foundry.boundary` — MF-B0 constitution and
  the 20-attack adversarial gate;
* :mod:`foundry.resources` / :mod:`foundry.providers` — MF-B1 provider-neutral
  compute planning and cost-to-close;
* :mod:`foundry.data` — MF-B2 data constitution, rights, roles, contamination;
* :mod:`foundry.refinery` — MF-B3 dataset refinery and corpus architecture;
* :mod:`foundry.evaluation` — MF-B4 frozen evaluation institution;
* :mod:`foundry.oce_boundary` — the One-OCE boundary: every temporary fixture is
  declared with a replacement condition and retirement evidence.

Nothing in this package owns institutional truth, authority, identity, capital,
or production deployment, and no code path here rents paid compute.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .boundary import mf_b0_gate_report, run_mf_b0_adversarial_suite
from .constitution import CONSTITUTION, FOUNDRY_DOCTRINE, ResourceBudget, DEFAULT_BUDGET
from .core import (
    Contradiction,
    FrozenMap,
    OceTestDouble,
    PolicyBlocked,
    Receipt,
    Unauthorized,
    fingerprint,
    write_json,
    write_receipt,
)
from .data import (
    ContaminationGraph,
    ContaminationRelation,
    RightsDisposition,
    SourceRecord,
    SourceRegistry,
)
from .evaluation import (
    CapabilityAssessment,
    EvaluationProtocol,
    EvaluationRun,
    NegativeKnowledgeStore,
    NegativeResult,
    SealedEvaluationStore,
    SealedPayload,
    assess_capability,
    freeze_protocol,
    submit_for_oce_review,
)
from .oce_boundary import assert_boundary_complete, boundary_registry, declaration_payload
from .providers import ADAPTERS, RawProviderObservation, normalize_offer
from .refinery import (
    DEFAULT_RECIPE,
    DatasetManifest,
    DatasetRefinery,
    RawItem,
    RefineryRecipe,
)
from .resources import (
    BudgetLedger,
    ComputeOffer,
    ComputeRequest,
    OperatorGrant,
    PortableCheckpoint,
    assert_checkpoint_portable,
    estimate_cost_to_close,
    simulate_launch,
    simulate_placement,
)

__all__ = [
    "ADAPTERS",
    "CONSTITUTION",
    "DEFAULT_BUDGET",
    "DEFAULT_RECIPE",
    "FOUNDRY_DOCTRINE",
    "BudgetLedger",
    "CapabilityAssessment",
    "ComputeOffer",
    "ComputeRequest",
    "ContaminationGraph",
    "ContaminationRelation",
    "Contradiction",
    "DatasetManifest",
    "DatasetRefinery",
    "EvaluationProtocol",
    "EvaluationRun",
    "FrozenMap",
    "NegativeKnowledgeStore",
    "NegativeResult",
    "OceTestDouble",
    "OperatorGrant",
    "PolicyBlocked",
    "PortableCheckpoint",
    "RawItem",
    "RawProviderObservation",
    "Receipt",
    "RefineryRecipe",
    "ResourceBudget",
    "RightsDisposition",
    "SealedEvaluationStore",
    "SealedPayload",
    "SourceRecord",
    "SourceRegistry",
    "Unauthorized",
    "__version__",
    "assert_boundary_complete",
    "assert_checkpoint_portable",
    "assess_capability",
    "boundary_registry",
    "declaration_payload",
    "estimate_cost_to_close",
    "fingerprint",
    "freeze_protocol",
    "mf_b0_gate_report",
    "normalize_offer",
    "run_mf_b0_adversarial_suite",
    "simulate_launch",
    "simulate_placement",
    "submit_for_oce_review",
    "write_json",
    "write_receipt",
]
