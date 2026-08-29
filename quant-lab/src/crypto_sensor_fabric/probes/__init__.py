"""Bloc 2 capability-probe harness (T-1 infrastructure evidence).

Subsystem layout:

    enums.py      controlled probe vocabularies
    models.py     request / attempt / claim / coverage / failure models
    failures.py   failure taxonomy + retry/hard-block + missingness mapping
    redaction.py  secret redaction for evidence
    planner.py    historical checkpoint planning (recent-control-first)
    runner.py     deterministic run lifecycle over provider executors
    evidence.py   immutable evidence store + claim synthesis
    coverage.py   coverage vectors, redundancy, matrices
    scoring.py    capability dimension scoring + composite
    reports.py    human/machine report rendering
"""

from __future__ import annotations

from .enums import (
    AccessMode,
    AuthMode,
    CapabilityMissingness,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    FreeOnlyStatus,
    Granularity,
    HistoricalBoundaryConfidence,
    PITReadiness,
    ProbeFailureClass,
    ProbeFailureFamily,
    ProbeRunStatus,
    ProviderRole,
    QueryMode,
    RedundancyClass,
    ResponseStatusClass,
)
from .failures import (
    classify_http_status,
    failure_family,
    failure_to_bloc1_missing_reason,
    failure_to_missingness,
    is_hard_block,
    is_retryable,
)
from .models import (
    CapabilityClaim,
    CapabilityProbeAttempt,
    CapabilityProbeRequest,
    DocumentationRuntimeContradiction,
    FailureRecord,
    ProbeRunResult,
    ProviderProbeSummary,
    ProviderSensorCoverage,
    SensorRedundancySummary,
    missingness_to_bloc1_reason,
)
from .redaction import redact_mapping, redact_url, redact_value, scrub_secrets

__all__ = [
    "AccessMode",
    "AuthMode",
    "CapabilityClaim",
    "CapabilityMissingness",
    "CapabilityProbeAttempt",
    "CapabilityProbeRequest",
    "CapabilityStatus",
    "ContradictionResolutionStatus",
    "ContradictionSeverity",
    "DocumentationRuntimeContradiction",
    "EvidenceLevel",
    "FailureRecord",
    "FreeOnlyStatus",
    "Granularity",
    "HistoricalBoundaryConfidence",
    "PITReadiness",
    "ProbeFailureClass",
    "ProbeFailureFamily",
    "ProbeRunResult",
    "ProbeRunStatus",
    "ProviderProbeSummary",
    "ProviderRole",
    "ProviderSensorCoverage",
    "QueryMode",
    "RedundancyClass",
    "ResponseStatusClass",
    "SensorRedundancySummary",
    "classify_http_status",
    "failure_family",
    "failure_to_bloc1_missing_reason",
    "failure_to_missingness",
    "is_hard_block",
    "is_retryable",
    "missingness_to_bloc1_reason",
    "redact_mapping",
    "redact_url",
    "redact_value",
    "scrub_secrets",
]
