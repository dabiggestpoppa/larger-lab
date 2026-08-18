"""QL-EXEC-R1 — strategy/account binding (static contract)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .enums import AccountRole, ExecutionMode
from .ownership import OwnershipNamespace


@dataclass(frozen=True)
class StrategyAccountBinding:
    """Where and how a strategy executes. No credentials."""

    binding_id: str
    strategy_id: str
    runtime_id: str
    account_id: str
    account_role: AccountRole
    execution_mode: ExecutionMode = ExecutionMode.SHADOW
    metadata_version: int = 1

    portfolio_group_id: str | None = None
    ownership_namespace: OwnershipNamespace | None = None
    strategy_adapter_id: str = ""
    capital_policy_adapter_id: str | None = None
    capital_translation_adapter_id: str | None = None
    allowed_symbols: tuple[str, ...] = field(default_factory=tuple)
    deployment_generation: str = ""
    operator_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.binding_id or not self.binding_id.strip():
            raise ValueError("binding_id must be non-empty")
        if not self.strategy_id or not self.strategy_id.strip():
            raise ValueError("strategy_id must be non-empty")
        if not self.account_id or not self.account_id.strip():
            raise ValueError("account_id must be non-empty")
        if self.metadata_version < 1:
            raise ValueError("metadata_version must be >= 1")
        if self.account_role is AccountRole.PORTFOLIO_MASTER:
            if not self.portfolio_group_id:
                raise ValueError(
                    "PORTFOLIO_MASTER binding requires portfolio_group_id"
                )
            if not self.capital_policy_adapter_id:
                raise ValueError(
                    "PORTFOLIO_MASTER binding requires capital_policy_adapter_id"
                )
        if (
            self.account_role is AccountRole.EXCLUSIVE_STRATEGY_MASTER
            and self.portfolio_group_id
        ):
            raise ValueError(
                "EXCLUSIVE_STRATEGY_MASTER binding must not set portfolio_group_id"
            )
