"""Book 3 Worker Fabric — facade.

Re-exports the chapter modules that build the fabric:

* :mod:`worker_identity`  — B3-C1 worker identity + OCE admission authority
* :mod:`worker_contracts` — B3-C1 versioned contract catalogue
* :mod:`worker_sessions`  — B3-C2 authenticated outbound worker sessions
* :mod:`worker_leases`    — B3-C3 fenced leases + duplicate-safe delivery

Keeping a single entrypoint lets consumers import ``oce_control.worker_fabric``
while the implementation stays split by chapter (granular chapter commits).
"""
from .worker_identity import (WorkerIdentity, CapabilityRegistry, WorkerAuthority,
                              AdmissionRequest, CapabilityAdmissionError)
from .worker_contracts import (SUPPORTED_PROTOCOLS, SUPPORTED_TASK_TYPES,
                               KNOWN_CAPABILITIES, Contract, validate)
from .worker_sessions import (SessionHost, OutboundSession, SessionError,
                              SessionExpired, SessionRevoked, WorkerDraining,
                              _hmac_sign, _hash_secret)
from .worker_leases import (LeaseStore, InMemoryLeaseStore, FabricScheduler,
                            JobEnvelope, LeaseFencingError, StaleFence,
                            UnknownLease, LateResult, DuplicateEffect)

__all__ = [
    "WorkerIdentity", "CapabilityRegistry", "WorkerAuthority", "AdmissionRequest",
    "CapabilityAdmissionError",
    "SUPPORTED_PROTOCOLS", "SUPPORTED_TASK_TYPES", "KNOWN_CAPABILITIES",
    "Contract", "validate",
    "SessionHost", "OutboundSession", "SessionError", "SessionExpired",
    "SessionRevoked", "WorkerDraining",
    "LeaseStore", "InMemoryLeaseStore", "FabricScheduler", "JobEnvelope",
    "LeaseFencingError", "StaleFence", "UnknownLease", "LateResult",
    "DuplicateEffect",
]