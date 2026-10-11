"""SENSOR-B5-I05 - Bloc 5 time semantics, availability and interval conventions.

The frozen seven-module surface of bloc_05/02 section 17:

* ``enums``            -- the four vocabularies this checkpoint owns
                          (timestamp roles, revision statuses, revision modes,
                          replay eligibility);
* ``models``           -- canonical timestamp evidence, the frozen role/field
                          map, and the availability resolution;
* ``semantics_registry`` -- provider/family time semantics, text-in/text-out,
                          fail closed on anything undeclared;
* ``availability``     -- conservative ``market_available_at`` derivation that
                          never consults ``ingested_at``;
* ``intervals``        -- declared boundary conventions and the completion law
                          (a closed interval is available at its close, never
                          at its start);
* ``revision_policy``  -- pure ``AS_KNOWN_THEN`` / ``LATEST_VERIFIED``
                          selection over caller-supplied revisions;
* ``replay_gate``      -- section 15's six admission conditions, in order.

What this package deliberately does NOT do:

* no T1 row assembly and no write to the ratified ``ObservationTimeEnvelope``
  -- the B5-I01 envelope is consumed read-only (its ``availability_confidence``
  gap stays an open operator question, recorded in ``BLOC_05_I01_TYPE_SCOPE_
  MATRIX.json`` as NOT FROZEN);
* no revision database, supersession engine or persistence -- B5-I07;
* no full market-availability methodology across provider latency policies,
  no golden-frame replay acceptance -- B5-I06 and beyond;
* no network, no filesystem, no wall clock, no hashing: configuration arrives
  as TEXT and leaves as TEXT, exactly like the I02 identity registry.

Symbols are exposed from ``crypto_sensor_fabric.normalization.time`` only: the
top-level normalization surface stays exactly the 24 ratified B5-I01 public
symbols (B5-I02/I03/I04 directive 29 precedent).
"""

from __future__ import annotations

from .enums import (
    RevisionMode,
    RevisionStatus,
    ReplayEligibility,
    STRICT_REPLAY_ELIGIBLE,
    TimestampRole,
)
from .models import (
    TIMESTAMP_ROLE_FIELD,
    AvailabilityConfidenceToken,
    AvailabilityResolution,
    CanonicalTimestamp,
    EvidenceRef,
    TimeEvidenceBase,
)
from .semantics_registry import (
    ProviderTimeSemantics,
    ProviderTimeSemanticsRegistry,
    UnknownProviderTimeSemantics,
    parse_provider_time_semantics_yaml,
    serialize_provider_time_semantics_yaml,
)
from .intervals import (
    IntervalWindow,
    UndecidableIntervalBoundary,
    earliest_justified_availability_from,
)
from .availability import (
    AcquisitionMetadata,
    derive_market_available_at,
)
from .revision_policy import (
    RevisionPolicy,
    RevisionPolicyCatalog,
    RevisionRecord,
    RevisionSelection,
    UnsupportedRevisionMode,
    parse_revision_policies_yaml,
    select_revisions,
    serialize_revision_policies_yaml,
)
from .replay_gate import (
    ReplayEvaluation,
    ReplayEvidence,
    UnassessableReplayEvidence,
    assess_replay_eligibility,
)

__all__ = [
    "TIMESTAMP_ROLE_FIELD",
    "AcquisitionMetadata",
    "AvailabilityConfidenceToken",
    "AvailabilityResolution",
    "CanonicalTimestamp",
    "EvidenceRef",
    "IntervalWindow",
    "ProviderTimeSemantics",
    "ProviderTimeSemanticsRegistry",
    "RevisionMode",
    "RevisionPolicy",
    "RevisionPolicyCatalog",
    "RevisionRecord",
    "RevisionSelection",
    "RevisionStatus",
    "ReplayEligibility",
    "ReplayEvaluation",
    "ReplayEvidence",
    "STRICT_REPLAY_ELIGIBLE",
    "TimeEvidenceBase",
    "TimestampRole",
    "UndecidableIntervalBoundary",
    "UnassessableReplayEvidence",
    "UnknownProviderTimeSemantics",
    "UnsupportedRevisionMode",
    "assess_replay_eligibility",
    "derive_market_available_at",
    "earliest_justified_availability_from",
    "parse_provider_time_semantics_yaml",
    "parse_revision_policies_yaml",
    "select_revisions",
    "serialize_provider_time_semantics_yaml",
    "serialize_revision_policies_yaml",
]
