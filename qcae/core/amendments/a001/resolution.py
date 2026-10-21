"""CapabilityResolutionMode — A-001's higher-level institutional resolution layer.

A-001 §8 expands capability-gap resolution to a coarse institutional decision:
USE / BORROW / RENT / BUY / ACQUIRE / BUILD / RESEARCH / DECLINE.

Design (operator-approved direction in the reconciliation prompt §4):

- ``CapabilityResolutionMode`` is the HIGHER-LEVEL institutional/economic
  resolution of a capability gap.
- ``AcquisitionForm`` (core vocabulary, canon 0.5.12) remains the LOWER-LEVEL
  implementation/acquisition form (USE_DEPENDENCY, VENDOR, EXTRACT_*,
  REIMPLEMENT_*, ...).

One resolution mode is realized through zero or more acquisition forms; e.g.
RENT may be realized by WRAP_SERVICE, ACQUIRE by EXTRACT_COMPONENT or VENDOR.
Neither vocabulary replaces the other; no silent mapping is imposed at P0.
The full economic decision engine comparing these modes is P8 scope (A-001
§13); P0 ships the vocabulary and its reference semantics only.
"""

from __future__ import annotations

from enum import StrEnum


class CapabilityResolutionMode(StrEnum):
    """Institutional economic resolution of a capability gap (A-001 §8)."""

    USE = "USE"
    BORROW = "BORROW"
    RENT = "RENT"
    BUY = "BUY"
    ACQUIRE = "ACQUIRE"
    BUILD = "BUILD"
    RESEARCH = "RESEARCH"
    DECLINE = "DECLINE"


#: Modes whose decision evidence is external procurement (A-001 §8: RENT/BUY
#: consume external supply surfaces). P8 extends acquisition decisions to these.
EXTERNAL_PROCUREMENT_MODES: frozenset = frozenset(
    {CapabilityResolutionMode.RENT, CapabilityResolutionMode.BUY}
)

#: Mode that routes unresolved knowledge to Research Mesh (A-001 §8 RESEARCH;
#: P0 semantics: this is a routing decision, not a research implementation).
RESEARCH_ROUTING_MODE: CapabilityResolutionMode = CapabilityResolutionMode.RESEARCH
