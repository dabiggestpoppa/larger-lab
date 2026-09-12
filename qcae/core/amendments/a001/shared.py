"""Shared A-001 amendment vocabulary (canon remains frozen; A-001 is additive).

Amendment identity: QCAE-AMEND-A001 v1.0 — Research Mesh Boundary and
Economic Experience. These constants are the single source for amendment-aware
manifests and drift guards.
"""

from __future__ import annotations

from enum import StrEnum

#: Amendment register identity (qcae/amendments/QCAE_AMEND_A001_...).
A001_AMENDMENT_ID = "QCAE-AMEND-A001"
A001_AMENDMENT_VERSION = "1.0"

#: The A-001 JSON interface schemas declare schema_version as the string "1.0".
A001_SCHEMA_VERSION = "1.0"


class DataRights(StrEnum):
    """Data-rights classification (A-001 handoff + economic-experience schemas)."""

    PUBLIC = "PUBLIC"
    LICENSED = "LICENSED"
    CLIENT_CONFIDENTIAL = "CLIENT_CONFIDENTIAL"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


#: Rights classes that cannot default into cross-domain reuse (A-001 §11:
#: client-protected content is excluded from cross-domain reuse unless explicit
#: rights exist).
PROTECTED_DATA_RIGHTS: frozenset = frozenset(
    {DataRights.CLIENT_CONFIDENTIAL, DataRights.RESTRICTED}
)
