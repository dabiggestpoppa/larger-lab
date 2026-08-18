"""QL-EXEC-R1 — pure account routing (selection validation only, no broker).

Answers: which configured account is this event permitted to target?
Ambiguous / zero / multiple routes all REJECT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .account import AccountProfile
from .binding import StrategyAccountBinding
from .enums import AccountRole, RoutingDecision
from .portfolio import PortfolioGroup


@dataclass(frozen=True)
class RoutingResult:
    decision: RoutingDecision
    account_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def routed(self) -> bool:
        return self.decision is RoutingDecision.ROUTED


def _reject(*reasons: str) -> RoutingResult:
    return RoutingResult(RoutingDecision.REJECTED, (), reasons)


class AccountRouter:
    """Deterministic account selection for an approved strategy event."""

    def route(
        self,
        strategy_id: str,
        bindings: Iterable[StrategyAccountBinding],
        portfolios: Mapping[str, PortfolioGroup],
        accounts: Mapping[str, AccountProfile],
    ) -> RoutingResult:
        matches = [b for b in bindings if b.strategy_id == strategy_id]
        if not matches:
            return _reject("zero bindings for strategy")

        enabled = [b for b in matches if b.operator_enabled]
        if not enabled:
            return _reject("binding disabled")

        if len(enabled) > 1:
            return _reject("ambiguous routing: multiple enabled bindings")

        binding = enabled[0]

        if binding.account_role is AccountRole.EXCLUSIVE_STRATEGY_MASTER:
            account = accounts.get(binding.account_id)
            if account is None:
                return _reject("bound account not found in registry")
            if account.strategy_allowlist and strategy_id not in account.strategy_allowlist:
                return _reject("strategy not allowlisted for account")
            return RoutingResult(RoutingDecision.ROUTED, (binding.account_id,))

        if binding.account_role is AccountRole.PORTFOLIO_MASTER:
            group = portfolios.get(binding.portfolio_group_id or "")
            if group is None:
                return _reject("portfolio group not found")
            if not group.enabled:
                return _reject("portfolio group disabled")
            if strategy_id not in group.strategy_ids:
                return _reject("strategy not in approved portfolio group")
            account = accounts.get(group.account_id)
            if account is None:
                return _reject("portfolio group account not found in registry")
            if account.strategy_allowlist and strategy_id not in account.strategy_allowlist:
                return _reject("strategy not allowlisted for account")
            return RoutingResult(RoutingDecision.ROUTED, (group.account_id,))

        return _reject(
            f"account role {binding.account_role.value} cannot route direct execution"
        )
