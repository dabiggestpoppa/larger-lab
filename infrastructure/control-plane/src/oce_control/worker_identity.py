"""Book 3 Worker Fabric — worker identity and OCE admission authority (B3-C1).

Workers cannot self-authorize: their identity and capability set are issued
by OCE only after operator (PO) approval of an AdmissionRequest. Capabilities
must be operator-admitted; unknown capabilities and unsupported protocol
versions fail closed. Identity is immutable and separate from any temporary
worker instance/session.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from . import worker_contracts as WC


class CapabilityAdmissionError(PermissionError):
    """Raised when a capability is unknown or not operator-admitted."""


@dataclass(frozen=True)
class WorkerIdentity:
    """Immutable, versioned identity of a worker fabric node."""
    worker_id: str
    admission_nonce: str
    protocol_version: str
    host_os_class: str
    runtime_class: str
    trust_zone: str
    worker_version: str
    capabilities: tuple[str, ...] = ()
    sandbox_profile: str = "default"

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "admission_nonce": self.admission_nonce,
            "protocol_version": self.protocol_version,
            "host_os_class": self.host_os_class,
            "runtime_class": self.runtime_class,
            "trust_zone": self.trust_zone,
            "worker_version": self.worker_version,
            "sandbox_profile": self.sandbox_profile,
            "capabilities": list(self.capabilities),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorkerIdentity":
        return cls(
            worker_id=d["worker_id"],
            admission_nonce=d["admission_nonce"],
            protocol_version=d["protocol_version"],
            host_os_class=d["host_os_class"],
            runtime_class=d["runtime_class"],
            trust_zone=d["trust_zone"],
            worker_version=d["worker_version"],
            capabilities=tuple(d.get("capabilities", [])),
            sandbox_profile=d.get("sandbox_profile", "default"),
        )


class CapabilityRegistry:
    """OCE-admitted capabilities. Unknown capabilities fail closed.

    Only the operator (PO via the boundary layer) may admit a capability; a
    worker may declare only a subset of admitted capabilities and can never
    invent one. Hermes calling ``admit_capability`` is rejected upstream.
    """

    def __init__(self, admitted: Optional[list[str]] = None):
        self._admitted: dict[str, dict] = {}
        for cap in (admitted or []):
            self._admitted[cap] = {"admitted_by": "operator:ratified", "admitted_at": ""}

    def admit_capability(self, capability: str, actor: str) -> dict:
        if not capability or not isinstance(capability, str):
            raise ValueError("capability must be a non-empty string")
        if capability not in WC.KNOWN_CAPABILITIES:
            raise CapabilityAdmissionError(
                f"capability '{capability}' is not in the known capability catalogue")
        rec = self._admitted.get(capability)
        if rec is None:
            rec = {"admitted_by": actor, "admitted_at": WC.utcnow_iso()}
            self._admitted[capability] = rec
        return dict(rec)

    def is_admitted(self, capability: str) -> bool:
        return capability in self._admitted

    def admitted(self) -> list[str]:
        return sorted(self._admitted)

    def check(self, required: list[str]) -> None:
        for cap in (required or []):
            if not self.is_admitted(cap):
                raise CapabilityAdmissionError(
                    f"capability '{cap}' is not operator-admitted; job refused")


@dataclass
class AdmissionRequest:
    worker_id: str
    public_key_or_nonce: str
    requested_capabilities: list[str]
    protocol_version: str
    host_os_class: str
    runtime_class: str
    trust_zone: str
    worker_version: str
    sandbox_profile: str = "default"
    requested_at: str = field(default_factory=WC.utcnow_iso)

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "public_key_or_nonce": self.public_key_or_nonce,
            "requested_capabilities": list(self.requested_capabilities),
            "protocol_version": self.protocol_version,
            "host_os_class": self.host_os_class,
            "runtime_class": self.runtime_class,
            "trust_zone": self.trust_zone,
            "worker_version": self.worker_version,
            "sandbox_profile": self.sandbox_profile,
            "requested_at": self.requested_at,
        }


class WorkerAuthority:
    """The OCE admission authority for the fabric.

    A worker cannot self-authorize; approved identities are immutable and
    carry capabilities that are a strict subset of the operator-admitted
    catalogue. Every admitted worker gets an immutable audit trail.
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self._registry = registry or CapabilityRegistry()
        self._identities: dict[str, WorkerIdentity] = {}
        self._audit: list[dict] = []

    @property
    def registry(self) -> CapabilityRegistry:
        return self._registry

    def approve(self, request: AdmissionRequest, actor: str) -> WorkerIdentity:
        WC.ensure_supported_protocol(request.protocol_version, actor)
        WC.ensure_valid_os(request.host_os_class, actor)
        WC.ensure_valid_runtime(request.runtime_class, actor)
        WC.ensure_valid_trust_zone(request.trust_zone, actor)
        WC.ensure_valid_sandbox(request.sandbox_profile, actor)
        self._registry.check(request.requested_capabilities)
        if not request.worker_id or not request.public_key_or_nonce:
            raise ValueError("admission request must carry worker_id and credential material")
        ident = WorkerIdentity(
            worker_id=request.worker_id,
            admission_nonce=request.public_key_or_nonce,
            protocol_version=request.protocol_version,
            host_os_class=request.host_os_class,
            runtime_class=request.runtime_class,
            trust_zone=request.trust_zone,
            worker_version=request.worker_version,
            capabilities=tuple(request.requested_capabilities),
            sandbox_profile=request.sandbox_profile,
        )
        self._identities[request.worker_id] = ident
        self._audit.append({"worker_id": request.worker_id, "actor": actor,
                            "action": "admit", "at": WC.utcnow_iso(),
                            "capabilities": list(ident.capabilities)})
        return ident

    def get(self, worker_id: str) -> Optional[WorkerIdentity]:
        return self._identities.get(worker_id)

    def revoke_identity(self, worker_id: str, actor: str) -> WorkerIdentity:
        if worker_id not in self._identities:
            raise KeyError(f"worker '{worker_id}' has no admitted identity")
        ident = self._identities.pop(worker_id)
        self._audit.append({"worker_id": worker_id, "actor": actor,
                            "action": "revoke", "at": WC.utcnow_iso()})
        return ident

    def identities(self) -> dict[str, WorkerIdentity]:
        return dict(self._identities)

    def audit_trail(self, worker_id: str) -> list[dict]:
        return [a for a in self._audit if a["worker_id"] == worker_id]

    def opportunities_pending(self) -> list:
        return []


# Re-export the identity dump helpers for the fabric facade.
IdentityDict = dict