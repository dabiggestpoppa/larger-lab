"""CompositeCapability — a capability composed of atoms (canon Book I 1.2.10).

Composition members are atom references (stable IDs). Member roles mirror the
canon's mandatory/optional structure (1.2.11), including ALTERNATIVE groups
(exactly one member required, e.g. "parquet-storage OR timeseries-database").
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
)


class CompositionRole(StrEnum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    ALTERNATIVE = "ALTERNATIVE"


@dataclass(frozen=True)
class CompositionMember(SerializableRecord):
    """One atom's role inside a composite."""

    SCHEMA_VERSION = 1

    atom_id: str
    role: CompositionRole

    _COERCIONS = {"role": lambda v: coerce_enum(v, CompositionRole)}

    def validate(self) -> None:
        require_identifier(self.atom_id, "atom_id")
        if not isinstance(self.role, CompositionRole):
            raise QcaeValidationError(
                f"role must be a CompositionRole member, got {self.role!r}"
            )


@dataclass(frozen=True)
class CompositeCapability(SerializableRecord):
    SCHEMA_VERSION = 1

    capability_id: str
    contract_version: int
    name: str
    members: Tuple[CompositionMember, ...]

    _NESTED_RECORDS = {"members": CompositionMember}

    def validate(self) -> None:
        require_identifier(self.capability_id, "capability_id")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError(
                f"contract_version must be a positive integer, got {self.contract_version!r}"
            )
        require_non_empty_str(self.name, "name")
        if not self.members:
            raise QcaeValidationError(
                "composite must contain at least one member atom"
            )
        require_no_duplicates(self.members, "members")

        for member in self.members:
            member.validate()

        # An alternative group of one is indistinguishable from REQUIRED.
        alt_members = [m for m in self.members if m.role == CompositionRole.ALTERNATIVE]
        if len(alt_members) == 1:
            raise QcaeValidationError(
                f"single-member ALTERNATIVE group is meaningless: {alt_members[0].atom_id!r}; "
                "declare the atom REQUIRED instead"
            )

        # Required atoms must not also sit inside the alternative group
        # (an atom cannot be both always-present and one-of-several).
        required_ids = {m.atom_id for m in self.members if m.role == CompositionRole.REQUIRED}
        alt_ids = {m.atom_id for m in alt_members}
        overlap = sorted(required_ids & alt_ids)
        if overlap:
            raise QcaeValidationError(
                f"atoms cannot be both REQUIRED and ALTERNATIVE: {overlap}"
            )

        # Canon 1.2.11 requires at least one mandatory element of composition.
        if not required_ids and not alt_members:
            raise QcaeValidationError(
                "composite with only OPTIONAL members has no guaranteed behavior"
            )


def make_composite(
    capability_id: str,
    contract_version: int,
    name: str,
    members: Tuple[CompositionMember, ...],
) -> CompositeCapability:
    """Build and validate a composite in one call."""
    composite = CompositeCapability(
        capability_id=capability_id,
        contract_version=contract_version,
        name=name,
        members=members,
    )
    composite.validate()
    return composite
