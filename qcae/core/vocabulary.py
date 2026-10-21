"""Frozen core vocabulary shared across QCAE subsystems.

These enums are constitutional vocabulary (canon Book I). They live in core so
adapters can never invent their own variants (Book V 15.2 invariant 4).
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceClass(StrEnum):
    """Evidence tiers E0–E9 (canon Book I 0.4.2), strongest last."""

    E0_CLAIM = "E0_CLAIM"
    E1_DOCUMENTATION = "E1_DOCUMENTATION"
    E2_SOURCE = "E2_SOURCE"
    E3_UPSTREAM_TEST = "E3_UPSTREAM_TEST"
    E4_INDEPENDENT_RUNTIME = "E4_INDEPENDENT_RUNTIME"
    E5_INDEPENDENT_CONTRACT = "E5_INDEPENDENT_CONTRACT"
    E6_BENCHMARK = "E6_BENCHMARK"
    E7_DOMAIN_VALIDATION = "E7_DOMAIN_VALIDATION"
    E8_INTEGRATION = "E8_INTEGRATION"
    E9_PRODUCTION_OBSERVATION = "E9_PRODUCTION_OBSERVATION"


class AcquisitionForm(StrEnum):
    """Acquisition spectrum (canon 0.5.12 / master prompt §17)."""

    USE_DIRECT = "USE_DIRECT"
    USE_DEPENDENCY = "USE_DEPENDENCY"
    WRAP_LIBRARY = "WRAP_LIBRARY"
    WRAP_SERVICE = "WRAP_SERVICE"
    FORK = "FORK"
    VENDOR = "VENDOR"
    EXTRACT_COMPONENT = "EXTRACT_COMPONENT"
    EXTRACT_ALGORITHM = "EXTRACT_ALGORITHM"
    EXTRACT_SCHEMA = "EXTRACT_SCHEMA"
    EXTRACT_TESTS = "EXTRACT_TESTS"
    REIMPLEMENT_FROM_SPEC = "REIMPLEMENT_FROM_SPEC"
    REIMPLEMENT_FROM_PAPER = "REIMPLEMENT_FROM_PAPER"
    USE_AS_REFERENCE = "USE_AS_REFERENCE"
    USE_AS_ARCHITECTURAL_PRIOR = "USE_AS_ARCHITECTURAL_PRIOR"
    DEFER = "DEFER"
    REJECT = "REJECT"


#: Evidence classes ranked from weakest to strongest claim support.
EVIDENCE_STRENGTH_ORDER: tuple = tuple(EvidenceClass)


class VerificationLevel(StrEnum):
    """Verification states for graph edges and claims (canon Book I 1.3.13).

    These levels are never collapsed into a single "true" status: a claim's
    label records how far independent verification has progressed.
    """

    DISCOVERED = "DISCOVERED"
    DOCUMENTED = "DOCUMENTED"
    SOURCE_LOCATED = "SOURCE_LOCATED"
    CODE_VERIFIED = "CODE_VERIFIED"
    RUNTIME_VERIFIED = "RUNTIME_VERIFIED"
    CONTRACT_VERIFIED = "CONTRACT_VERIFIED"
    DOMAIN_VERIFIED = "DOMAIN_VERIFIED"
