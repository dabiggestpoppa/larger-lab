"""QL-EXEC-R1 — hedging/netting compatibility (pure, fail-closed)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .enums import AccountRole, CompatibilityStatus, HedgingNetting


@dataclass(frozen=True)
class CompatibilityState:
    account_id: str
    status: CompatibilityStatus
    mode_compatible: bool
    same_symbol_overlap: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)


def evaluate_compatibility(
    account_role: AccountRole,
    hedging_netting: HedgingNetting,
    same_symbol_overlap: bool = False,
    account_id: str = "",
) -> CompatibilityState:
    """Pure compatibility evaluation. No virtual allocation ledger built."""

    def result(status: CompatibilityStatus, compatible: bool, *reasons: str) -> CompatibilityState:
        return CompatibilityState(
            account_id=account_id,
            status=status,
            mode_compatible=compatible,
            same_symbol_overlap=same_symbol_overlap,
            blocking_reasons=tuple(reasons),
        )

    # FOLLOWER / MIRROR cannot submit direct orders.
    if account_role in (AccountRole.FOLLOWER, AccountRole.MIRROR):
        return result(
            CompatibilityStatus.FAIL_CLOSED,
            False,
            f"role {account_role.value} cannot execute directly",
        )

    # UNKNOWN account mode fails closed wherever the semantic matters.
    if hedging_netting is HedgingNetting.UNKNOWN:
        return result(
            CompatibilityStatus.FAIL_CLOSED,
            False,
            "unknown account hedging/netting mode",
        )

    if account_role is AccountRole.EXCLUSIVE_STRATEGY_MASTER:
        if hedging_netting is HedgingNetting.HEDGING:
            return result(CompatibilityStatus.SUPPORTED, True)
        # Netting is supported only when ownership stays unambiguous.
        if hedging_netting is HedgingNetting.NETTING:
            if same_symbol_overlap:
                return result(
                    CompatibilityStatus.FAIL_CLOSED,
                    False,
                    "exclusive netting with same-symbol overlap is ambiguous",
                )
            return result(CompatibilityStatus.SUPPORTED, True)

    if account_role is AccountRole.PORTFOLIO_MASTER:
        if hedging_netting is HedgingNetting.HEDGING:
            return result(CompatibilityStatus.SUPPORTABLE_WITH_WORK, True)
        if hedging_netting is HedgingNetting.NETTING:
            if same_symbol_overlap:
                return result(
                    CompatibilityStatus.BLOCKED_PENDING_VIRTUAL_LEDGER,
                    False,
                    "shared netting with same-symbol overlap requires a virtual "
                    "allocation ledger and tested reconciliation model",
                )
            return result(CompatibilityStatus.SUPPORTABLE_WITH_WORK, True)

    return result(CompatibilityStatus.FAIL_CLOSED, False, "unhandled role/mode")
