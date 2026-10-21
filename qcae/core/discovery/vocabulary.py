"""Discovery vocabulary shared by every Block 2 record and adapter — canon 2.1.5/2.1.8.

Book II's discovery vocabulary lives here, in one place, for the same reason
Book I's constitutional vocabulary lives in :mod:`qcae.core.vocabulary`: every
record and every adapter must speak one canonical set, and no adapter may invent
its own variants (Book V 15.1 invariant 5, 15.2 invariant 4).

Two enums are *vocabulary* rather than plan structure, so they live here:

- :class:`SourceClass` — the source portfolio classes (canon 2.1.5). The
  portfolio is a set of classes, not a vendor list: ``github`` is an adapter
  beneath ``GITHUB_REPOSITORY_CODE`` (Book V 15.1), not a class of its own.
- :class:`CostTier` — progressive discovery cost tiers (canon 2.1.8).

Both previously lived in :mod:`qcae.core.discovery.plan`, which forced every
consumer — including ``core.ports.discovery`` — to import the plan domain module
merely to name a source class. They do not belong in
:mod:`qcae.core.vocabulary` either: that module is Book I's constitutional
vocabulary (canon 0.4.2/0.5.12) and is declared frozen, and the freeze manifests
attest the Book I enums they enumerate through ``vocabulary_digest``. Block 2
vocabulary is P3's own, so it lives beside the Block 2 records that speak it.
This module defines them; it re-exports nothing and depends on nothing but the
stdlib.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum

__all__ = ["CostTier", "SourceClass"]


class SourceClass(StrEnum):
    """Discovery source classes (canon 2.1.5 source portfolio).

    The portfolio is a set of classes, not a vendor list (Book V 15.1: folders
    and classes reflect responsibility; ``github`` is an adapter beneath the
    ``GITHUB_REPOSITORY_CODE`` class).
    """

    INTERNAL_REGISTRY_CODE = "INTERNAL_REGISTRY_CODE"
    GITHUB_REPOSITORY_CODE = "GITHUB_REPOSITORY_CODE"
    CURATED_SENSOR = "CURATED_SENSOR"
    PACKAGE_ECOSYSTEM = "PACKAGE_ECOSYSTEM"
    RESEARCH_LITERATURE = "RESEARCH_LITERATURE"
    STANDARDS_SPECIFICATIONS = "STANDARDS_SPECIFICATIONS"
    PROJECT_DOCUMENTATION = "PROJECT_DOCUMENTATION"
    WEB_DISCOVERY = "WEB_DISCOVERY"


class CostTier(IntEnum):
    """Progressive discovery cost tiers (canon 2.1.8)."""

    TIER_0_MEMORY_LOOKUP = 0
    TIER_1_METADATA_SNIPPETS = 1
    TIER_2_DOCS_PACKAGE_METADATA = 2
    TIER_3_SOURCE_TREE = 3
    TIER_4_REPOSITORY_INTELLIGENCE = 4
    TIER_5_CAPABILITY_FORENSICS = 5
    TIER_6_PROVING_LAB = 6
