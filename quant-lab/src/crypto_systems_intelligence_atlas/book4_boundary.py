"""Structural Book 4 / Book 5 boundary policy for the dependency kernel.

The relation allowlist is the canonical boundary. Keyword screening is
defense-in-depth only and may never authorize a record.
"""

from __future__ import annotations

from typing import Final

from .architecture_relations import ArchitectureRelationType
from .relationships import EdgeType

BOOK4_DEPENDENCY_RELATION_ALLOWLIST: Final[
    frozenset[EdgeType | ArchitectureRelationType]
] = frozenset(
    {
        # Book 1 technical dependency and infrastructure relations
        EdgeType.DEPENDS_ON,
        EdgeType.INTEGRATES_WITH,
        EdgeType.BUILT_WITH,
        EdgeType.RUNS_ON,
        EdgeType.HOSTS,
        EdgeType.ORACLE_FOR,
        EdgeType.DATA_FROM,
        EdgeType.BRIDGES_TO,
        EdgeType.MESSAGES_TO,
        EdgeType.ROUTED_THROUGH,
        EdgeType.OPERATED_BY,
        EdgeType.OWNED_BY,
        EdgeType.SECURED_BY,
        EdgeType.VALIDATED_BY,
        EdgeType.SETTLES_TO,
        EdgeType.PRICES,
        # Book 3 local architecture relations (reused, never duplicated)
        ArchitectureRelationType.EXECUTES_WITH,
        ArchitectureRelationType.USES_DA,
        ArchitectureRelationType.SEQUENCED_BY,
    }
)
"""Relations faithful to technical dependency, service, and route mechanics."""

BOOK5_ECONOMIC_RELATIONS: Final[frozenset[EdgeType]] = frozenset(
    {
        EdgeType.COLLATERAL_IN,
        EdgeType.LIQUIDITY_ON,
        EdgeType.STAKED_IN,
        EdgeType.RESTAKED_IN,
        EdgeType.REDEEMS_FOR,
        EdgeType.ISSUED_ON,
        EdgeType.NATIVE_TO,
        EdgeType.WRAPS,
    }
)
"""Book 1 economic relations that may never authorize a Book 4 record."""

BOOK5_TERMS: Final[tuple[str, ...]] = (
    "total value locked",
    "capital routing",
    "liquidity depth",
    "collateral value",
    "stablecoin supply",
    "credit risk",
    "yield",
    "staking economics",
    "derivative position",
    "value locked",
    "capital concentration",
)


class BOOK4ScopeError(ValueError):
    """Book 5 capital-field content attempted to cross the Book 4 boundary."""


def assert_book4_technical_scope(value: str) -> None:
    """Defense-in-depth lexical screen; never the primary boundary."""

    normalized = value.lower()
    if any(term in normalized for term in BOOK5_TERMS):
        raise BOOK4ScopeError(f"Book 5 capital-field claim rejected from Book 4: {value}")


class Book4RelationSupportPolicy:
    """Structural allowlist authority for Book 4 dependency records."""

    @staticmethod
    def is_supported(relation: EdgeType | ArchitectureRelationType) -> bool:
        return relation in BOOK4_DEPENDENCY_RELATION_ALLOWLIST

    @staticmethod
    def require_supported(relation: EdgeType | ArchitectureRelationType) -> None:
        if relation in BOOK4_DEPENDENCY_RELATION_ALLOWLIST:
            return
        if relation in BOOK5_ECONOMIC_RELATIONS:
            raise ValueError(
                "Book 5 economic relations may not authorize a Book 4 dependency record"
            )
        raise ValueError(
            f"relation {relation.value} is outside the Book 4 technical dependency allowlist"
        )


__all__ = [
    "BOOK4_DEPENDENCY_RELATION_ALLOWLIST",
    "BOOK4ScopeError",
    "BOOK5_ECONOMIC_RELATIONS",
    "BOOK5_TERMS",
    "Book4RelationSupportPolicy",
    "assert_book4_technical_scope",
]
