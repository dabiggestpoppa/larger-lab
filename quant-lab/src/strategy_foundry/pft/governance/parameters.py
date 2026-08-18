"""Parameter classification and the parameter register.

Classification per program constitution 7.3:
  AUTHOR_CONSTANT        - supplied by model author; frozen for RAW
  RESEARCH_CONSTANT      - preregistered by the lab before PnL
  DATA_DERIVED           - estimated causally from allowed development info
  TWIN_PARAMETER         - belongs to a separately registered twin
  FORBIDDEN_OPTIMIZATION - chosen because historical PnL improved
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

PARAMETER_CLASSES = {
    "AUTHOR_CONSTANT",
    "RESEARCH_CONSTANT",
    "DATA_DERIVED",
    "TWIN_PARAMETER",
    "FORBIDDEN_OPTIMIZATION",
}

# RAW implementations may only reference AUTHOR_CONSTANT and RESEARCH_CONSTANT.
RAW_ALLOWED_CLASSES = {"AUTHOR_CONSTANT", "RESEARCH_CONSTANT"}


class ParameterRegistryError(RuntimeError):
    pass


class ForbiddenParameterUse(RuntimeError):
    pass


@dataclass(frozen=True)
class Parameter:
    id: str
    name: str
    value: Any
    parameter_class: str
    source_ref: str
    unit: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.name:
            raise ParameterRegistryError("parameter id and name are required")
        if self.parameter_class not in PARAMETER_CLASSES:
            raise ParameterRegistryError(
                f"invalid parameter class {self.parameter_class!r}; "
                f"allowed: {sorted(PARAMETER_CLASSES)}"
            )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "parameter_class": self.parameter_class,
            "source_ref": self.source_ref,
            "unit": self.unit,
            "notes": self.notes,
        }

    def assert_usable_in_raw(self) -> None:
        """Fail closed when a parameter is not permitted in a RAW implementation."""
        if self.parameter_class not in RAW_ALLOWED_CLASSES:
            raise ForbiddenParameterUse(
                f"parameter {self.id} has class {self.parameter_class}; "
                f"not usable in RAW implementations (allowed: {sorted(RAW_ALLOWED_CLASSES)})"
            )

    def assert_frozen(self) -> None:
        """AUTHOR_CONSTANT values are frozen for RAW; mutation must be refused."""
        if self.parameter_class == "AUTHOR_CONSTANT":
            raise ForbiddenParameterUse(
                f"parameter {self.id} is an AUTHOR_CONSTANT; its value is frozen for RAW"
            )


class ParameterRegister:
    """Validated register of parameters. Ids must be unique."""

    def __init__(self) -> None:
        self._parameters: dict[str, Parameter] = {}

    def add(self, parameter: Parameter) -> None:
        if parameter.id in self._parameters:
            existing = self._parameters[parameter.id]
            if existing.value != parameter.value:
                raise ParameterRegistryError(
                    f"duplicate parameter id {parameter.id!r} with conflicting value"
                )
            raise ParameterRegistryError(f"duplicate parameter id {parameter.id!r}")
        self._parameters[parameter.id] = parameter

    def get(self, param_id: str) -> Parameter:
        try:
            return self._parameters[param_id]
        except KeyError:
            raise ParameterRegistryError(f"unknown parameter {param_id!r}") from None

    def all(self) -> list:
        return [self._parameters[k] for k in sorted(self._parameters)]

    def by_class(self, parameter_class: str) -> list:
        return [p for p in self.all() if p.parameter_class == parameter_class]

    def assert_complete_for_raw(self, required_ids: set) -> None:
        """Every parameter id the RAW implementation references must be registered."""
        missing = required_ids - set(self._parameters)
        if missing:
            raise ParameterRegistryError(
                f"RAW implementation references unregistered parameters: {sorted(missing)}"
            )

    def to_register(self) -> dict:
        return {
            "parameter_class_taxonomy": sorted(PARAMETER_CLASSES),
            "raw_allowed_classes": sorted(RAW_ALLOWED_CLASSES),
            "count": len(self._parameters),
            "parameters": [p.to_dict() for p in self.all()],
        }
