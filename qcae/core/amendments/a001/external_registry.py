"""Cross-registry references (A-001 §6, §15 invariant 2; reconciliation §7).

QCAE must be able to reference Research Mesh evidence/knowledge objects,
Economic Experience records, and institutional learning candidates without
owning, copying, or governing their lifecycle. ``ExternalRegistryRef`` carries
only stable identity plus ownership/domain metadata; P1 will persist provenance
over these references. No federation is built at P0.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier, require_non_empty_str


class ExternalRegistry(StrEnum):
    """Registry domains QCAE may reference but not govern (A-001 §6)."""

    RESEARCH_MESH = "RESEARCH_MESH"
    ECONOMIC_EXPERIENCE = "ECONOMIC_EXPERIENCE"
    INSTITUTIONAL_LEARNING = "INSTITUTIONAL_LEARNING"


class ExternalLifecycleRole(StrEnum):
    """What QCAE may do with a referenced external object.

    QCAE may OBSERVE (read) or SUBMIT (hand evidence in). It may never GOVERN:
    external lifecycle authority stays with the owning registry (A-001 §6:
    ownership and lifecycle authority do not merge).
    """

    OBSERVE = "OBSERVE"
    SUBMIT = "SUBMIT"


@dataclass(frozen=True)
class ExternalRegistryRef(SerializableRecord):
    SCHEMA_VERSION = 1

    registry: ExternalRegistry
    external_id: str

    # Owner domain of the referenced object, e.g. "research-mesh:synthesis",
    # "institution:transformation-governor", "oce:opportunity-exchange".
    owner_domain: str

    # QCAE's declared relationship to the object (OBSERVE or SUBMIT only).
    lifecycle_role: ExternalLifecycleRole = ExternalLifecycleRole.OBSERVE

    # Optional digest of the referenced external artifact for provenance.
    external_digest: str = ""

    referenced_at: str = ""

    _COERCIONS = {
        "registry": lambda v: coerce_enum(v, ExternalRegistry),
        "lifecycle_role": lambda v: coerce_enum(v, ExternalLifecycleRole),
    }

    def validate(self) -> None:
        if not isinstance(self.registry, ExternalRegistry):
            raise QcaeValidationError(
                f"registry must be an ExternalRegistry member, got {self.registry!r}"
            )
        require_identifier(self.external_id, "external_id")
        require_non_empty_str(self.owner_domain, "owner_domain")
        if not isinstance(self.lifecycle_role, ExternalLifecycleRole):
            raise QcaeValidationError(
                f"lifecycle_role must be an ExternalLifecycleRole member, "
                f"got {self.lifecycle_role!r}"
            )
        if self.external_digest and (not isinstance(self.external_digest, str) or len(self.external_digest) < 8):
            raise QcaeValidationError(
                f"external_digest must be a content digest, got {self.external_digest!r}"
            )


def make_external_registry_ref(**kwargs) -> ExternalRegistryRef:
    ref = ExternalRegistryRef(**kwargs)
    ref.validate()
    return ref
