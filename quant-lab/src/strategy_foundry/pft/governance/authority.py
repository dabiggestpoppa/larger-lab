"""Agent authority state. Deny-by-default.

B0 default authority (program constitution 7.7) blocks every downstream
authorization until the operator explicitly grants it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

AUTHORITY_KEYS = {
    "economic_testing_authorized",
    "optimization_authorized",
    "confirmation_authorized",
    "holdout_authorized",
    "deployment_authorized",
    "production_capital_authorized",
    "next_checkpoint_authorized",
}


class NotAuthorized(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthorityState:
    economic_testing_authorized: bool = False
    optimization_authorized: bool = False
    confirmation_authorized: bool = False
    holdout_authorized: bool = False
    deployment_authorized: bool = False
    production_capital_authorized: bool = False
    next_checkpoint_authorized: bool = False
    extra: dict = field(default_factory=dict)

    def check(self, key: str) -> None:
        """Deny-by-default: unknown keys are never authorized."""
        if key not in AUTHORITY_KEYS:
            raise NotAuthorized(f"unknown authority key {key!r}; denied by default")
        if not getattr(self, key):
            raise NotAuthorized(f"{key} is not authorized")

    def to_dict(self) -> dict:
        payload = {k: getattr(self, k) for k in sorted(AUTHORITY_KEYS)}
        payload["extra"] = dict(sorted(self.extra.items()))
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> "AuthorityState":
        if not isinstance(data, dict):
            raise ValueError("authority must be a JSON object")
        for k in data:
            if k == "extra":
                continue
            if k not in AUTHORITY_KEYS:
                raise ValueError(f"unknown authority key {k!r}")
            if not isinstance(data[k], bool):
                raise ValueError(f"authority key {k!r} must be boolean")
        extra = data.get("extra", {})
        if not isinstance(extra, dict):
            raise ValueError("authority 'extra' must be an object")
        return cls(
            economic_testing_authorized=data.get("economic_testing_authorized", False),
            optimization_authorized=data.get("optimization_authorized", False),
            confirmation_authorized=data.get("confirmation_authorized", False),
            holdout_authorized=data.get("holdout_authorized", False),
            deployment_authorized=data.get("deployment_authorized", False),
            production_capital_authorized=data.get("production_capital_authorized", False),
            next_checkpoint_authorized=data.get("next_checkpoint_authorized", False),
            extra=extra,
        )


def default_authority() -> AuthorityState:
    """The B0 default: everything denied, next checkpoint not authorized."""
    return AuthorityState()
