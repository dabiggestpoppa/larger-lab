"""CapabilityAtom — the smallest independently meaningful behavior.

Canon Book I 1.2. Atoms are behavioral, not code-size objects (1.2.25): the
atom is the stable comparison object across implementations, and its identity
survives implementation replacement (1.2.25 invariant 8).

Record fields follow canon 1.2.22. References to other entities (parents,
candidates, dependencies) are stable internal IDs (canon 1.3.16), not embedded
objects, so atoms remain independently serializable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_no_duplicates,
    require_non_empty_str,
    require_str_list,
)


class AtomType(StrEnum):
    """Atom classes (canon 1.2.9)."""

    COMPUTATIONAL = "COMPUTATIONAL"
    DATA = "DATA"
    PROTOCOL = "PROTOCOL"
    STORAGE = "STORAGE"
    EXECUTION = "EXECUTION"
    VALIDATION = "VALIDATION"
    OBSERVABILITY = "OBSERVABILITY"
    INTERFACE = "INTERFACE"
    RESEARCH = "RESEARCH"
    ARCHITECTURE = "ARCHITECTURE"


class AtomCoupling(StrEnum):
    """Operational coupling classes between conceptually separate atoms (canon 1.2.14)."""

    NONE = "NONE"
    WEAK = "WEAK"
    SHARED_LIBRARY = "SHARED_LIBRARY"
    SHARED_STATE = "SHARED_STATE"
    SHARED_RUNTIME = "SHARED_RUNTIME"
    SHARED_SERVICE = "SHARED_SERVICE"
    INSEPARABLE_IN_CURRENT_IMPLEMENTATION = "INSEPARABLE_IN_CURRENT_IMPLEMENTATION"


class AtomStatus(StrEnum):
    """Atom lifecycle status (P0 derivation; see progress ledger unresolved #4)."""

    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class AtomProvenance(StrEnum):
    """How an acquired atom came to exist (canon 1.2.16)."""

    DIRECTLY_IMPORTED = "DIRECTLY_IMPORTED"
    ADAPTED = "ADAPTED"
    VENDORED = "VENDORED"
    EXTRACTED = "EXTRACTED"
    REIMPLEMENTED_FROM_SPEC = "REIMPLEMENTED_FROM_SPEC"
    REIMPLEMENTED_FROM_PAPER = "REIMPLEMENTED_FROM_PAPER"
    INSPIRED_BY_PRIOR_ART = "INSPIRED_BY_PRIOR_ART"
    INTERNALLY_DEVELOPED = "INTERNALLY_DEVELOPED"


@dataclass(frozen=True)
class CapabilityAtom(SerializableRecord):
    SCHEMA_VERSION = 1

    atom_id: str
    atom_version: int
    name: str
    atom_type: AtomType
    description: str

    parent_capabilities: Tuple[str, ...] = ()
    inputs: Tuple[str, ...] = ()
    outputs: Tuple[str, ...] = ()
    state: str = ""
    acceptance_conditions: Tuple[str, ...] = ()
    implementation_candidates: Tuple[str, ...] = ()
    dependencies: Tuple[str, ...] = ()
    coupling: AtomCoupling = AtomCoupling.NONE
    security_class: str = "unspecified"
    domain: str = "general"
    provenance: AtomProvenance = AtomProvenance.INTERNALLY_DEVELOPED
    status: AtomStatus = AtomStatus.PROPOSED

    _COERCIONS = {
        "atom_type": lambda v: coerce_enum(v, AtomType),
        "coupling": lambda v: coerce_enum(v, AtomCoupling),
        "provenance": lambda v: coerce_enum(v, AtomProvenance),
        "status": lambda v: coerce_enum(v, AtomStatus),
    }

    def validate(self) -> None:
        require_identifier(self.atom_id, "atom_id")
        if not isinstance(self.atom_version, int) or isinstance(self.atom_version, bool) \
                or self.atom_version < 1:
            raise QcaeValidationError(
                f"atom_version must be a positive integer, got {self.atom_version!r}"
            )
        require_non_empty_str(self.name, "name")
        require_non_empty_str(self.description, "description")
        if not isinstance(self.atom_type, AtomType):
            raise QcaeValidationError(
                f"atom_type must be an AtomType member, got {self.atom_type!r}"
            )
        if not self.acceptance_conditions:
            raise QcaeValidationError(
                "acceptance_conditions must not be empty: an atom without an "
                "observable acceptance condition has no independent acquisition "
                "value (canon 1.2.2, 1.2.5)"
            )
        require_str_list(self.acceptance_conditions, "acceptance_conditions")
        require_no_duplicates(self.acceptance_conditions, "acceptance_conditions")
        for refs, what in (
            (self.parent_capabilities, "parent_capabilities"),
            (self.implementation_candidates, "implementation_candidates"),
            (self.dependencies, "dependencies"),
        ):
            require_str_list(refs, what)
            for ref in refs:
                require_identifier(ref, f"{what} entry")
        if not isinstance(self.coupling, AtomCoupling):
            raise QcaeValidationError(
                f"coupling must be an AtomCoupling member, got {self.coupling!r}"
            )
        if not isinstance(self.provenance, AtomProvenance):
            raise QcaeValidationError(
                f"provenance must be an AtomProvenance member, got {self.provenance!r}"
            )
        if not isinstance(self.status, AtomStatus):
            raise QcaeValidationError(
                f"status must be an AtomStatus member, got {self.status!r}"
            )
        require_non_empty_str(self.domain, "domain")
