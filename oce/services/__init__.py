"""Shared services for B6-I4: identity (C3.S1) and workflow (C3.S2).

Deterministic, offline, provider-neutral. No wall clock, no randomness, no network; every time
value is an explicit integer supplied by the caller.
"""
from .identity import identity_registry, resolve_identity
from .refusals import CODES
from .workflow import (
    acquire_lease,
    advance_run,
    cancel_run,
    define_workflow,
    retry_run,
    start_run,
)

__all__ = [
    "CODES",
    "acquire_lease",
    "advance_run",
    "cancel_run",
    "define_workflow",
    "identity_registry",
    "resolve_identity",
    "retry_run",
    "start_run",
]
