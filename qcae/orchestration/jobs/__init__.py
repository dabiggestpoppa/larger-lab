"""QCAE — Quant Lab Capability Acquisition Engine.

Standalone now. OCE-compatible by contract. OCE-governed later.

Do not find repositories. Find reusable capability.
"""

__version__ = "0.1.0"
CANON_VERSION = "0.1"

"""Job/Step runtime, queue, leases (P2)."""

from qcae.orchestration.jobs.graph import StepGraph, validate_step_graph
from qcae.orchestration.jobs.runtime import (
    FailureClass,
    JobEvent,
    JobEventType,
    LeaseInfo,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
    assert_job_transition,
    assert_step_transition,
    is_terminal_job,
    is_terminal_step,
    legal_job_transitions,
    legal_step_transitions,
)

__all__ = [
    "StepGraph",
    "validate_step_graph",
    "FailureClass",
    "JobEvent",
    "JobEventType",
    "LeaseInfo",
    "RuntimeJob",
    "RuntimeJobStatus",
    "RuntimeStep",
    "RuntimeStepStatus",
    "assert_job_transition",
    "assert_step_transition",
    "is_terminal_job",
    "is_terminal_step",
    "legal_job_transitions",
    "legal_step_transitions",
]
