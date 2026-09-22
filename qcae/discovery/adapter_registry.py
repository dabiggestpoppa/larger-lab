"""Composition wiring from source class to configured adapter — Book V 15.3.

This is an **implementation**, not a port: it holds configuration state (which
adapter serves which source class) and is built by whatever composes a discovery
run. It lived in ``core.ports.discovery`` until that container was recognised as
the only implementation in a module that otherwise declares interfaces — every
other member of every ``core.ports.*`` module is an ABC/Protocol or a frozen
record.

It lives here, beside the adapter packages it wires, for the same reason
``store_factory`` lives beside the repositories it wires.

Why a registry exists at all: "GitHub is not the universe" (canon 2.2.15). A
source class with no configured adapter must be *reportable as missing* rather
than as an empty search, so an unconfigured surface is never mistaken for a
capability absence (canon 2.1.13).

Closing is part of the adapter contract (``DiscoverySourceAdapter.close``), so
:meth:`DiscoveryAdapterRegistry.close_all` releases adapters through their own
interface instead of probing for a hook that may or may not exist.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from qcae.core.discovery.plan import DiscoveryPlan
from qcae.core.discovery.vocabulary import SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import DiscoverySourceAdapter

__all__ = ["DiscoveryAdapterRegistry"]


class DiscoveryAdapterRegistry:
    """Composition-wired map from source class to configured adapter (15.3).

    A single adapter serves exactly one source class, and an unregistered class
    is representable as missing rather than as an empty search: the planner must
    be able to report a gap in coverage instead of reporting a finished search
    (canon 2.2.15 "GitHub is not the universe", 2.1.13).
    """

    def __init__(self) -> None:
        self._adapters: Dict[SourceClass, DiscoverySourceAdapter] = {}

    def register(self, adapter: DiscoverySourceAdapter) -> None:
        """Register an adapter, refusing silent replacement of an existing one."""
        if not isinstance(adapter, DiscoverySourceAdapter):  # pragma: no cover - misuse guard
            raise QcaeValidationError("only DiscoverySourceAdapter instances may be registered")
        if adapter.source_class in self._adapters:
            raise QcaeValidationError(
                f"source class {adapter.source_class.value} already has adapter "
                f"{self._adapters[adapter.source_class].adapter_id!r}; "
                "replacing it must be an explicit composition decision"
            )
        if not adapter.adapter_id.strip():  # pragma: no cover - adapter contract
            raise QcaeValidationError("adapter_id must be non-empty")
        self._adapters[adapter.source_class] = adapter

    def adapter_for(self, source_class: SourceClass) -> Optional[DiscoverySourceAdapter]:
        """The adapter for a source class, or None when none is configured."""
        return self._adapters.get(source_class)

    def configured_source_classes(self) -> Tuple[SourceClass, ...]:
        """Every source class with a configured adapter, in registration order."""
        return tuple(self._adapters)

    def missing_source_classes(self, plan: DiscoveryPlan) -> Tuple[SourceClass, ...]:
        """Enabled plan source classes with no adapter — reported, never faked.

        The planner uses this to emit coverage gaps (``NOT_CONFIGURED``) so that
        an unconfigured surface is never mistaken for a capability absence.
        """
        return tuple(
            source_class
            for source_class in plan.enabled_source_classes()
            if source_class not in self._adapters
        )

    def close_all(self) -> List[str]:
        """Release every configured adapter, returning the ids that were closed.

        ``close`` is declared on the adapter contract, so each adapter is closed
        through its own interface: no probing for a hook, and no adapter silently
        omitted from the result because its cleanup looked different.
        """
        closed: List[str] = []
        for adapter in self._adapters.values():
            adapter.close()
            closed.append(adapter.adapter_id)
        return closed
