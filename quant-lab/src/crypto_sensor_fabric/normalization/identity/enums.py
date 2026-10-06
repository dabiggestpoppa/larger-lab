"""SENSOR-B5-I03 - the three frozen I03 vocabularies (bloc_05/01 section 6/8/9).

Audited in ``BLOC_05_I03_VOCABULARY_AUTHORITY_MATRIX.json``: exactly these three
member sets are frozen by the plan (LifecycleState: section 6 + bloc_05/07 F4;
AliasType: section 8; IdentityResolutionStatus: section 9).  Everything else an
I03 record carries is an opaque validated token or the reused B5-I01 enum
objects - nothing speculative is named here.

Same freeze discipline as ``normalization.enums`` (B5-I01): members copied from
the frozen planning documents, declaration order canonical, and adding a member
is a plan change requiring operator review, never a convenience.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "BLOCKING_IDENTITY_RESOLUTION_STATUSES",
    "AliasType",
    "IdentityResolutionStatus",
    "LifecycleState",
]


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class LifecycleState(_StrEnum):
    """Listing-lifecycle state of an instrument (bloc_05/01 section 6; F4).

    Exact frozen member set and order.  Section 6 forbids collapsing
    PRE_LISTING / DELISTED / UNKNOWN into one "absence" state: pre-listing
    absence is NOT_YET_LISTED evidence, post-delisting absence is DELISTED
    evidence, and UNKNOWN is unverified lifecycle evidence that must NOT
    become ACTIVE by default (I03 directive 34).
    """

    PRE_LISTING = "PRE_LISTING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELISTING_ANNOUNCED = "DELISTING_ANNOUNCED"
    DELISTED = "DELISTED"
    RELISTED_NEW_INSTANCE = "RELISTED_NEW_INSTANCE"
    UNKNOWN = "UNKNOWN"


class AliasType(_StrEnum):
    """Registered alias kinds (bloc_05/01 section 8).

    Exact frozen member set and order.  MANUAL / FUZZY / CANONICAL are
    deliberately absent: no frozen source defines them (I03 directive 5), and
    fuzzy matching may never become canonical truth (section 10).  Curated
    manual mappings ride this frozen vocabulary as evidence-backed
    InstrumentAlias rows (vocabulary matrix, directive 29 path A).
    """

    API_SYMBOL = "API_SYMBOL"
    ARCHIVE_SYMBOL = "ARCHIVE_SYMBOL"
    WEBSOCKET_SYMBOL = "WEBSOCKET_SYMBOL"
    DISPLAY_SYMBOL = "DISPLAY_SYMBOL"
    LEGACY_SYMBOL = "LEGACY_SYMBOL"
    PROVIDER_INTERNAL_ID = "PROVIDER_INTERNAL_ID"


class IdentityResolutionStatus(_StrEnum):
    """Outcome vocabulary of the PIT identity resolver (bloc_05/01 section 9).

    Exact frozen member set and order.  The four members of
    :data:`BLOCKING_IDENTITY_RESOLUTION_STATUSES` are the ones section 9
    states must not silently yield economically normalized identity.
    """

    RESOLVED_EXACT = "RESOLVED_EXACT"
    RESOLVED_ALIAS = "RESOLVED_ALIAS"
    RESOLVED_WITH_WARNING = "RESOLVED_WITH_WARNING"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_YET_LISTED = "NOT_YET_LISTED"
    DELISTED = "DELISTED"
    UNKNOWN_SYMBOL = "UNKNOWN_SYMBOL"
    TERMS_UNVERIFIED = "TERMS_UNVERIFIED"
    PIT_KNOWLEDGE_BLOCKED = "PIT_KNOWLEDGE_BLOCKED"


#: The section 9 blockers: statuses that block T1 economic normalization.
BLOCKING_IDENTITY_RESOLUTION_STATUSES: frozenset[IdentityResolutionStatus] = frozenset(
    {
        IdentityResolutionStatus.AMBIGUOUS,
        IdentityResolutionStatus.UNKNOWN_SYMBOL,
        IdentityResolutionStatus.TERMS_UNVERIFIED,
        IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED,
    }
)
