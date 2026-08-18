"""QL-EXEC-R1 — portfolio group (one account, one capital authority)."""
from __future__ import annotations

from dataclasses import dataclass

from .enums import OwnershipMode


@dataclass(frozen=True)
class PortfolioGroup:
    """Strategies sharing one capital policy/account.

    For a PORTFOLIO_MASTER: one account, one portfolio group, one capital
    policy authority, one reservation authority. No H1 engine here.
    """

    portfolio_group_id: str
    account_id: str
    strategy_ids: tuple[str, ...]
    capital_policy_id: str
    metadata_version: int = 1

    heat_policy_id: str = ""
    ownership_mode: OwnershipMode = OwnershipMode.SINGLE_RUNTIME_MULTI_ADAPTER
    enabled: bool = False

    def __post_init__(self) -> None:
        if not self.portfolio_group_id or not self.portfolio_group_id.strip():
            raise ValueError("portfolio_group_id must be non-empty")
        if not self.account_id or not self.account_id.strip():
            raise ValueError("account_id must be non-empty")
        if not self.capital_policy_id or not self.capital_policy_id.strip():
            raise ValueError("capital_policy_id must be non-empty")
        if not self.strategy_ids:
            raise ValueError("strategy_ids must be non-empty")
        if len(set(self.strategy_ids)) != len(self.strategy_ids):
            raise ValueError("strategy_ids must be unique")
        if self.metadata_version < 1:
            raise ValueError("metadata_version must be >= 1")
