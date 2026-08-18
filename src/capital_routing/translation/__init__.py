"""
Capital Translation Core (pure).

CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 — the PURE deterministic layer
that converts a sealed CapitalDecision + AccountBinding + event pos_t into an
economic exposure target. It owns NO broker/runtime concerns.
"""

from .capital_translation_core import (
    TRANSLATION_VERSION,
    AccountBindingReference,
    BoundAccountSnapshot,
    CapitalDecisionReference,
    EconomicExposureTarget,
    StrategyEventReference,
    TranslationError,
    translate,
)

__all__ = [
    "TRANSLATION_VERSION",
    "StrategyEventReference",
    "CapitalDecisionReference",
    "AccountBindingReference",
    "BoundAccountSnapshot",
    "EconomicExposureTarget",
    "TranslationError",
    "translate",
]
