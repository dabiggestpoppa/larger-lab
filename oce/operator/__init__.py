"""Operator truth surface: capability, approval and evidence views.

Read-only projections over caller-supplied governed records. No wall clock, no randomness, no
network, no later-stage import and no client-supplied authority.
"""
from .approvals import approval_inbox, decide
from .capability import capability_view
from .evidence import reconcile_chain, sample_nodes
from .model import OperatorRefusal, canonical, digest, object_digest
from .refusals import CODES

__all__ = [
    "CODES",
    "OperatorRefusal",
    "approval_inbox",
    "canonical",
    "capability_view",
    "decide",
    "digest",
    "object_digest",
    "reconcile_chain",
    "sample_nodes",
]
