"""Transition waivers: policy-justified skips of waivable evidence gates.

Canon 0.5.10 permits the DOMAIN_VERIFIED gate to be "marked NOT_APPLICABLE with
policy justification". This module is the durable form of that justification.
Waivers are first-class evidence-scoped records so gate skipping is never
implicit (constitution: "skipping a gate must be policy-driven and recorded").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.lifecycle.state import WAIVABLE_GATES, LifecycleState
from qcae.core.serialization import SerializableRecord

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _require_identifier(value: str, what: str) -> None:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise QcaeValidationError(f"{what} must be a short identifier string, got {value!r}")


def _require_non_empty(value: str, what: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QcaeValidationError(f"{what} must be a non-empty string")


@dataclass(frozen=True)
class TransitionWaiver(SerializableRecord):
    """A durable, attributable justification for skipping one waivable gate."""

    SCHEMA_VERSION = 1

    waived_gate: LifecycleState
    justification: str
    policy_ref: str
    authority_id: str
    decided_at: str

    def validate(self) -> None:
        if self.waived_gate not in WAIVABLE_GATES:
            raise QcaeValidationError(
                f"gate {self.waived_gate} is not waivable; waivable gates: "
                + ", ".join(sorted(g.value for g in WAIVABLE_GATES))
            )
        _require_non_empty(self.justification, "justification")
        _require_identifier(self.policy_ref, "policy_ref")
        _require_identifier(self.authority_id, "authority_id")
        _require_non_empty(self.decided_at, "decided_at")
        if self.policy_ref == "unspecified":
            raise QcaeValidationError(
                "policy_ref='unspecified' is reserved for objects with no waiver; "
                "real waivers must cite a real policy"
            )
