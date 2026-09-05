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

from .coverage import (
    CoverageVector,
    VerifiedSource,
    compute_coverage_vector,
    compute_sensor_redundancy,
    synthesize_coverage,
)
from .enums import (
    AccessMode,
    AuthMode,
    CapabilityMissingness,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    EvidenceSourceClass,
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
from .evidence import (
    CapabilityProbeEvidence,
    derive_evidence_level,
    derive_pit_readiness,
    deterministic_json,
    evidence_from_attempts,
    synthesize_claim,
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
from .reports import (
    FABRIC_VERSION,
    PROBE_VERSION,
    REPORT_FILENAMES,
    blocking_contradictions_csv,
    capability_claims_jsonl,
    failures_jsonl,
    free_only_audit_csv,
    history_boundaries_csv,
    pit_readiness_csv,
    probe_run_manifest,
    provider_coverage_csv,
    role_recommendations_markdown,
    schema_fingerprints_jsonl,
    sensor_gap_csv,
    write_reports,
)
from .scoring import (
    capability_score,
    evaluate_promotion,
    hard_blockers,
    is_blocked,
)

__all__ = [
    "AccessMode",
    "AuthMode",
    "CapabilityClaim",
    "CapabilityMissingness",
    "CapabilityProbeAttempt",
    "CapabilityProbeEvidence",
    "CapabilityProbeRequest",
    "CapabilityStatus",
    "ContradictionResolutionStatus",
    "ContradictionSeverity",
    "CoverageVector",
    "DocumentationRuntimeContradiction",
    "EvidenceLevel",
    "EvidenceSourceClass",
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
    "VerifiedSource",
    "capability_score",
    "classify_http_status",
    "compute_coverage_vector",
    "compute_sensor_redundancy",
    "derive_evidence_level",
    "derive_pit_readiness",
    "deterministic_json",
    "FABRIC_VERSION",
    "PROBE_VERSION",
    "REPORT_FILENAMES",
    "blocking_contradictions_csv",
    "capability_claims_jsonl",
    "evaluate_promotion",
    "evidence_from_attempts",
    "failure_family",
    "failures_jsonl",
    "free_only_audit_csv",
    "history_boundaries_csv",
    "failure_to_bloc1_missing_reason",
    "failure_to_missingness",
    "hard_blockers",
    "is_blocked",
    "is_hard_block",
    "is_retryable",
    "missingness_to_bloc1_reason",
    "pit_readiness_csv",
    "probe_run_manifest",
    "provider_coverage_csv",
    "role_recommendations_markdown",
    "schema_fingerprints_jsonl",
    "sensor_gap_csv",
    "write_reports",
    "redact_mapping",
    "redact_url",
    "redact_value",
    "scrub_secrets",
    "synthesize_claim",
    "synthesize_coverage",
]
