"""QL-EXEC-R4 — TB full nonregression migration harness (side-by-side parity).

This package contains the TB-specific parity harness. It reuses the canonical
TB strategy science (sealed P5/P6/P7 engine) and execution translation rather
than reimplementing them, and drives the generic runtime contracts
(StrategyAdapter / CapitalTranslationAdapter / BrokerSession / durable store /
ownership / reconciliation) plus the new multi-leg basket orchestration layer.

NOTHING here modifies active TB, connects real MT5, or submits real orders.
"""
from __future__ import annotations

from .adapters import (
    TBStrategyAdapter,
    TBTranslationAdapter,
    TBCapitalPolicyAdapter,
)
from .basket import (
    BasketOrchestrator,
    BasketPlanState,
    BasketResult,
    LegOutcome,
    LegPlan,
    MultiLegExecutionPlan,
    leg_intent_id,
    basket_ownership_tag,
)
from .parity import (
    ParityTier,
    ParityVerdict,
    compare_traces,
    compare_legs,
    compare_state_snapshot,
    normalize_trace,
)
from .shadow import (
    ReadOnlyBrokerSession,
    ShadowExecutionPlan,
    ShadowLeg,
    ShadowRuntimeAuthority,
    ShadowWriteForbiddenError,
    SHADOW_OBSERVE_ONLY,
)
from .shadow_feed import (
    ShadowExportFeed,
    ShadowFeedError,
    validate_record,
    content_hash,
)
from .shadow_parity import (
    ShadowMismatchClass,
    LiveParityVerdict,
    compare_live_record,
    SHADOW_EXPORT_SCHEMA_VERSION,
)
from .shadow_runner import (
    ShadowRuntime,
    ShadowCounters,
    build_snapshot,
    build_tri_bar,
)
from .harness import (
    LegacyTBHarness,
    GenericTBHarness,
    ParityReport,
    ParityRunner,
    BarFixture,
    make_control_fixture,
    make_snapshot,
    make_tri_bar,
    BASKET_NOTIONAL_USD,
)

__all__ = [
    "TBStrategyAdapter",
    "TBTranslationAdapter",
    "TBCapitalPolicyAdapter",
    "BasketOrchestrator",
    "BasketPlanState",
    "BasketResult",
    "LegOutcome",
    "LegPlan",
    "MultiLegExecutionPlan",
    "leg_intent_id",
    "basket_ownership_tag",
    "ParityTier",
    "ParityVerdict",
    "ParityReport",
    "ParityRunner",
    "compare_traces",
    "compare_legs",
    "compare_state_snapshot",
    "normalize_trace",
    "LegacyTBHarness",
    "GenericTBHarness",
    "BarFixture",
    "make_control_fixture",
    "make_snapshot",
    "make_tri_bar",
    "BASKET_NOTIONAL_USD",
    "ReadOnlyBrokerSession",
    "ShadowExecutionPlan",
    "ShadowLeg",
    "ShadowRuntimeAuthority",
    "ShadowWriteForbiddenError",
    "SHADOW_OBSERVE_ONLY",
    "ShadowExportFeed",
    "ShadowFeedError",
    "validate_record",
    "content_hash",
    "ShadowMismatchClass",
    "LiveParityVerdict",
    "compare_live_record",
    "SHADOW_EXPORT_SCHEMA_VERSION",
    "ShadowRuntime",
    "ShadowCounters",
    "build_snapshot",
    "build_tri_bar",
]
