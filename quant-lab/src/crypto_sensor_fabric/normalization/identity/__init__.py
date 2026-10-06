"""SENSOR-B5-I02/I03 - Bloc 5 identity records, registries and resolver.

The five frozen identity objects (:class:`CanonicalAsset`, :class:`Venue`,
:class:`VenueInstrument`, :class:`EconomicContract`,
:class:`ContractInstance`), the minimal versioned registry structures that
store and retrieve them by explicit identity, and - as of SENSOR-B5-I03 - the
frozen lifecycle/alias/resolution vocabulary and the pure PIT identity
resolver over one explicit snapshot.

Layers and what they deliberately do NOT do here:

* resolution is EXACT only: PIT-valid provider-instrument-ID and
  native-symbol/registered-alias evidence over the five-tier frozen order
  (bloc_05/01 section 10); fuzzy/prefix/substring/case-fold candidates are
  never generated here at all (B5-I03 hard law, section 10);
* terms logic and conversion are B5-I04 (no multiplier/exposure/notional
  math exists in this package);
* time-semantics, availability and revision machinery are B5-I05..I07;
* no adapter/network/HTTP import: the law is source-text plus zero
  connections, not module-load.

Symbols are exposed from ``crypto_sensor_fabric.normalization.identity`` only:
the top-level normalization surface stays exactly the 24 ratified B5-I01
public symbols (B5-I02/I03 directive 29).
"""

from __future__ import annotations

from .enums import (
    AliasType,
    IdentityResolutionStatus,
    LifecycleState,
)
from .models import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    SemanticToken,
    Venue,
    VenueInstrument,
)
from .aliases import InstrumentAlias
from .lifecycle import InstrumentLifecycle
from .registry import (
    IdentityRegistrySnapshot,
    parse_identity_registry_yaml,
    serialize_identity_registry_yaml,
    validate_registry_succession,
)
from .resolver import (
    IdentityResolution,
    resolve_instrument,
)

__all__ = [
    "AliasType",
    "CanonicalAsset",
    "ContractInstance",
    "EconomicContract",
    "IdentityRegistrySnapshot",
    "IdentityResolution",
    "IdentityResolutionStatus",
    "InstrumentAlias",
    "InstrumentLifecycle",
    "LifecycleState",
    "SemanticToken",
    "Venue",
    "VenueInstrument",
    "parse_identity_registry_yaml",
    "resolve_instrument",
    "serialize_identity_registry_yaml",
    "validate_registry_succession",
]
