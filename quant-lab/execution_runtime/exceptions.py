"""QL-EXEC-R1 — domain exceptions."""
from __future__ import annotations


class ExecutionRuntimeError(Exception):
    """Base class for all execution-runtime domain errors."""


class ValidationError(ExecutionRuntimeError):
    """A static contract failed validation."""


class DuplicateAccountError(ValidationError):
    """Duplicate account_id in the account registry."""


class DuplicatePortfolioGroupError(ValidationError):
    """Duplicate portfolio_group_id in the portfolio group registry."""


class DuplicateBindingError(ValidationError):
    """Duplicate binding_id in the strategy-account binding registry."""


class DuplicateRuntimeError(ValidationError):
    """Duplicate (normalized) runtime_id in the runtime profile registry."""


class InvalidRuntimeId(ValidationError):
    """runtime_id failed path-safety validation."""


class PathCollisionError(ValidationError):
    """Two runtime ids resolve to the same mutable path."""


class InvalidStateTransition(ValidationError):
    """A reservation state transition is not in the frozen graph."""


class SecretRequiredError(ValidationError):
    """An authenticated transport requires a secret reference."""


class RoutingError(ExecutionRuntimeError):
    """Account routing could not resolve an unambiguous route."""
