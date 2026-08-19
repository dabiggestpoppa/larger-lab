"""QL-EXEC-R1 — broker capability tri-state model.

UNKNOWN is deliberately different from FALSE. An unknown REQUIRED capability
fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import CapabilityState


@dataclass(frozen=True)
class BrokerCapabilities:
    """R5-expanded provider capability tri-state model.

    Every field defaults to UNKNOWN so an unproven provider fails closed. The
    fields added in R5 (stop orders, partial close, modify, native SL/TP,
    multi-account session, history, quotes) let a provider advertise truth
    without contaminating GenericRuntime with provider-specific branches.
    """

    supports_market_order: CapabilityState = CapabilityState.UNKNOWN
    supports_limit_order: CapabilityState = CapabilityState.UNKNOWN
    supports_stop_order: CapabilityState = CapabilityState.UNKNOWN
    supports_cancel: CapabilityState = CapabilityState.UNKNOWN
    supports_partial_fill_reporting: CapabilityState = CapabilityState.UNKNOWN
    supports_partial_close: CapabilityState = CapabilityState.UNKNOWN
    supports_modify_order: CapabilityState = CapabilityState.UNKNOWN
    supports_native_sl_tp: CapabilityState = CapabilityState.UNKNOWN
    supports_trailing_stop: CapabilityState = CapabilityState.UNKNOWN
    supports_client_order_id: CapabilityState = CapabilityState.UNKNOWN
    supports_hedging: CapabilityState = CapabilityState.UNKNOWN
    supports_netting: CapabilityState = CapabilityState.UNKNOWN
    supports_order_check: CapabilityState = CapabilityState.UNKNOWN
    supports_client_tag: CapabilityState = CapabilityState.UNKNOWN
    supports_deal_history: CapabilityState = CapabilityState.UNKNOWN
    supports_margin_estimate: CapabilityState = CapabilityState.UNKNOWN
    supports_symbol_activation: CapabilityState = CapabilityState.UNKNOWN
    supports_multi_account_session: CapabilityState = CapabilityState.UNKNOWN
    supports_history: CapabilityState = CapabilityState.UNKNOWN
    supports_streaming_quotes: CapabilityState = CapabilityState.UNKNOWN
    supports_rest_quotes: CapabilityState = CapabilityState.UNKNOWN

    def is_supported(self, cap: CapabilityState) -> bool:
        """True only for SUPPORTED. UNKNOWN and UNSUPPORTED both fail closed."""
        return cap is CapabilityState.SUPPORTED

    def is_known(self, cap: CapabilityState) -> bool:
        return cap is not CapabilityState.UNKNOWN

    def require(self, cap: CapabilityState, what: str) -> list[str]:
        """Return blocking reasons if a required capability is not SUPPORTED."""
        if self.is_supported(cap):
            return []
        if cap is CapabilityState.UNKNOWN:
            return [f"required capability unknown: {what}"]
        return [f"required capability unsupported: {what}"]
