"""QL-EXEC-R1 — deterministic, validated static registries.

Static configuration only. Dynamic READY/CONNECTED truth is a runtime record,
never stored here as if it were configuration authority.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from .account import AccountProfile
from .binding import StrategyAccountBinding
from .exceptions import (
    DuplicateAccountError,
    DuplicateBindingError,
    DuplicatePortfolioGroupError,
    DuplicateRuntimeError,
)
from .portfolio import PortfolioGroup
from .profiles import (
    RuntimeProfile,
    assert_no_path_collision,
    canonical_runtime_id,
)

T = TypeVar("T")


class _Registry(Generic[T]):
    def __init__(self, name: str) -> None:
        self._name = name
        self._items: dict[str, T] = {}

    def register(self, key: str, item: T, exc: type[Exception]) -> T:
        if key in self._items:
            raise exc(f"{self._name} already contains {key!r}")
        self._items[key] = item
        return item

    def get(self, key: str) -> T | None:
        return self._items.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._items

    def __len__(self) -> int:
        return len(self._items)

    def all(self) -> tuple[T, ...]:
        return tuple(self._items.values())


class AccountRegistry(_Registry[AccountProfile]):
    def __init__(self) -> None:
        super().__init__("account registry")

    def register(self, profile: AccountProfile) -> AccountProfile:
        return super().register(profile.account_id, profile, DuplicateAccountError)


class PortfolioGroupRegistry(_Registry[PortfolioGroup]):
    def __init__(self) -> None:
        super().__init__("portfolio group registry")

    def register(self, group: PortfolioGroup) -> PortfolioGroup:
        return super().register(
            group.portfolio_group_id, group, DuplicatePortfolioGroupError
        )

    def authority_violations(self) -> list[str]:
        """One portfolio group -> one account -> one capital authority.

        Returns human-readable violations of the shared-portfolio invariant.
        """
        by_account: dict[str, set[str]] = {}
        by_group: dict[str, str] = {}
        violations: list[str] = []
        for g in self._items.values():
            by_group[g.portfolio_group_id] = g.capital_policy_id
            by_account.setdefault(g.account_id, set()).add(g.capital_policy_id)

        for account_id, policies in by_account.items():
            if len(policies) > 1:
                violations.append(
                    f"account {account_id!r} has multiple capital authorities: "
                    f"{sorted(policies)}"
                )
        return violations


class BindingRegistry(_Registry[StrategyAccountBinding]):
    def __init__(self) -> None:
        super().__init__("binding registry")

    def register(self, binding: StrategyAccountBinding) -> StrategyAccountBinding:
        return super().register(binding.binding_id, binding, DuplicateBindingError)

    def for_strategy(self, strategy_id: str) -> tuple[StrategyAccountBinding, ...]:
        return tuple(b for b in self._items.values() if b.strategy_id == strategy_id)


class RuntimeProfileRegistry(_Registry[RuntimeProfile]):
    def __init__(self) -> None:
        super().__init__("runtime profile registry")
        self._canonical: dict[str, str] = {}

    def register(self, profile: RuntimeProfile) -> RuntimeProfile:
        key = canonical_runtime_id(profile.runtime_id)
        if key in self._canonical:
            raise DuplicateRuntimeError(
                f"runtime_id {profile.runtime_id!r} collides with "
                f"{self._canonical[key]!r} after normalization"
            )
        self._canonical[key] = profile.runtime_id
        return super().register(profile.runtime_id, profile, DuplicateRuntimeError)

    def assert_no_path_collisions(self) -> None:
        assert_no_path_collision([p.runtime_id for p in self._items.values()])
