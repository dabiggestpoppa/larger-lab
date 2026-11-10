"""Provider-neutral immutable approval binding (P2-R5R §10-15).

One approval authorizes exactly one binding. The binding is the semantic
identity of what an operator approved; both sides of the gate (the live
authority verdict and the durable approved decision) serialize the SAME
object, so a stale or widened grant digest-mismatches instead of admitting.

Canonical serialization is JSON with sorted keys and no whitespace — never
``'|'``-joined string concatenation (a field containing the separator would
silently alias another binding).

POLICY_VERSION_BOUND (operator law, this phase): an approval is bound to the
policy version under which the request was evaluated. A policy-version change
requires fresh approval unless a later canon amendment explicitly permits
semantic-version-independent grants.

This module lives in ``qcae.core`` because it is shared by the orchestrator
(which must never import ``qcae.governance.standalone``) and the governance
stack.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_non_empty_str

__all__ = ["ApprovalBinding", "POLICY_VERSION_BOUND", "LEGACY_APPROVAL_NOTICE"]

#: Operator law for this phase (see module docstring).
POLICY_VERSION_BOUND = (
    "POLICY_VERSION_BOUND: an approval is bound to the policy version under "
    "which the request was evaluated. A policy-version change requires a "
    "fresh approval unless a later canon amendment explicitly permits "
    "semantic-version-independent grants."
)

#: Approvals written before the strengthened schema are historical evidence
#: only: they may be read, but never authorize a new execution.
LEGACY_APPROVAL_NOTICE = (
    "legacy/incomplete approval binding: historical evidence only; a fresh "
    "approval under the strengthened R5R law is required"
)


@dataclass(frozen=True)
class ApprovalBinding(SerializableRecord):
    """The seven semantic fields one approval authorizes."""

    SCHEMA_VERSION = 1

    principal: str
    action: str
    resource: str
    scope: str
    budget_ref: str
    authority_requirement: str
    policy_version: str
    constraints: Tuple[str, ...] = ()

    def canonical_dict(self) -> dict:
        return {
            "action": self.action,
            "authority_requirement": self.authority_requirement,
            "budget_ref": self.budget_ref,
            "constraints": list(self.constraints),
            "policy_version": self.policy_version,
            "principal": self.principal,
            "resource": self.resource,
            "scope": self.scope,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.canonical_dict(), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        )

    def binding_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def is_complete(self) -> bool:
        """Whether this binding may authorize under the strengthened law.

        ``authority_requirement`` may legitimately be empty (the step declares
        no requirement, so its action IS the baseline). An empty
        ``budget_ref`` or ``policy_version`` marks a legacy/incomplete record:
        those never authorize.
        """
        return all((
            self.principal, self.action, self.resource, self.scope,
            self.budget_ref, self.policy_version,
        ))

    def validate(self) -> None:
        require_non_empty_str(self.principal, "principal")
        require_non_empty_str(self.action, "action")
        require_non_empty_str(self.resource, "resource")
        require_non_empty_str(self.scope, "scope")
        require_non_empty_str(self.budget_ref, "budget_ref")
        require_non_empty_str(self.policy_version, "policy_version")
        for item in self.constraints:
            if not isinstance(item, str) or not item.strip():
                raise QcaeValidationError(
                    "approval binding constraints must be non-empty strings"
                )
