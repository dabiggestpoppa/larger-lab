"""Positive/negative knowledge memory — Book IV 9.3, 9.4.

Negative knowledge (9.4) is first-class engineering intelligence: every
record stores *why* something failed, for what identity/revision, under what
contract, and the conditions under which it must or must not be retried.
"repo bad" is not storable; "v2.4 fails ordering clause C-17 on duplicate
events" is.

Positive knowledge (9.3) is evidence-linked reusable findings. Unsupported
agent summaries are Notes (``material=False``), never canonical verified
knowledge — the ``material`` flag and mandatory evidence refs enforce that.

Both are append-oriented: a new revision does not overwrite a rejection; it
supersedes it under explicit changed conditions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_identifier, require_non_empty_str, require_str_list

__all__ = [
    "NegativeKnowledgeType",
    "ReconsiderationCondition",
    "NegativeKnowledge",
    "PositiveKnowledge",
    "make_negative_knowledge",
    "make_positive_knowledge",
]


class NegativeKnowledgeType(str, Enum):
    """Canon failure categories (Book IV 9.4)."""

    NOT_FOUND = "NOT_FOUND"
    NOT_CAPABLE = "NOT_CAPABLE"
    CONTRACT_FAILURE = "CONTRACT_FAILURE"
    BUILD_FAILURE = "BUILD_FAILURE"
    SECURITY_REJECTION = "SECURITY_REJECTION"
    LICENSE_REJECTION = "LICENSE_REJECTION"
    QUANT_INVALIDATION = "QUANT_INVALIDATION"
    PERFORMANCE_FAILURE = "PERFORMANCE_FAILURE"
    EXCESSIVE_BURDEN = "EXCESSIVE_BURDEN"
    DUPLICATE_CAPABILITY = "DUPLICATE_CAPABILITY"
    ABANDONED_PATH = "ABANDONED_PATH"


@dataclass(frozen=True)
class ReconsiderationCondition(SerializableRecord):
    """One explicit condition under which a negative result may be re-examined."""

    SCHEMA_VERSION = 1

    condition: str
    detail: str = ""

    def validate(self) -> None:
        require_non_empty_str(self.condition, "condition")


@dataclass(frozen=True)
class NegativeKnowledge(SerializableRecord):
    """A durable, causal, scoped rejection/failure record (Book IV 9.4)."""

    SCHEMA_VERSION = 1

    record_id: str
    failure_type: NegativeKnowledgeType
    subject_id: str
    source_revision: str
    contract_id: str
    contract_version: str
    acquisition_form: str
    causal_detail: str
    evidence_ids: Tuple[str, ...]
    reconsideration: Tuple[ReconsiderationCondition, ...]
    scope_summary: str
    created_at: str
    owner: str = ""
    superseded_by: str = ""
    retry_allowed: bool = False

    _COERCIONS = {
        "failure_type": lambda v: NegativeKnowledgeType(v) if isinstance(v, str) and v in {t.value for t in NegativeKnowledgeType} else v,
        "evidence_ids": tuple,
        "reconsideration": tuple,
    }

    _NESTED_RECORDS = {"reconsideration": ReconsiderationCondition}

    def validate(self) -> None:
        require_identifier(self.record_id, "record_id")
        require_identifier(self.subject_id, "subject_id")
        require_identifier(self.contract_id, "contract_id")
        if not isinstance(self.failure_type, NegativeKnowledgeType):
            raise QcaeValidationError(
                f"failure_type must be a NegativeKnowledgeType, got {self.failure_type!r}"
            )
        require_non_empty_str(self.source_revision, "source_revision")
        require_non_empty_str(self.contract_version, "contract_version")
        require_non_empty_str(self.acquisition_form, "acquisition_form")
        require_non_empty_str(self.scope_summary, "scope_summary")
        require_non_empty_str(self.created_at, "created_at")

        # Causal detail: not "repo bad" (9.4 Failure Detail). Minimum substance.
        if len(self.causal_detail.strip()) < 20:
            raise QcaeValidationError(
                "causal_detail must explain what failed and why (>= 20 chars); "
                "'repo bad'-style rejections are not durable knowledge"
            )
        if not self.evidence_ids:
            raise QcaeValidationError(
                "negative knowledge must cite supporting evidence ids"
            )
        if not self.reconsideration:
            raise QcaeValidationError(
                "reconsideration conditions are mandatory (9.4 Reconsideration)"
            )


@dataclass(frozen=True)
class PositiveKnowledge(SerializableRecord):
    """An evidence-linked reusable finding (Book IV 9.3)."""

    SCHEMA_VERSION = 1

    record_id: str
    statement: str
    subject_id: str
    evidence_ids: Tuple[str, ...]
    created_at: str
    material: bool = True
    source_revision: str = ""
    contract_id: str = ""
    contract_version: str = ""
    known_limitation: str = ""
    superseded_by: str = ""

    _COERCIONS = {"evidence_ids": tuple}

    def validate(self) -> None:
        require_identifier(self.record_id, "record_id")
        require_identifier(self.subject_id, "subject_id")
        require_non_empty_str(self.statement, "statement")
        require_non_empty_str(self.created_at, "created_at")
        # 9.3 Invariant 1: material positive memory is evidence-linked. A
        # non-material record is a Note/hypothesis and may not claim verified
        # standing via required fields it doesn't carry.
        if self.material and not self.evidence_ids:
            raise QcaeValidationError(
                "material positive knowledge must link evidence; store "
                "unsupported summaries with material=False (Notes, not knowledge)"
            )
        if self.material:
            require_non_empty_str(self.source_revision, "source_revision")
            require_non_empty_str(self.contract_id, "contract_id")
            require_non_empty_str(self.contract_version, "contract_version")
        if self.superseded_by:
            require_identifier(self.superseded_by, "superseded_by")


def make_negative_knowledge(**kwargs) -> NegativeKnowledge:
    record = NegativeKnowledge(**kwargs)
    record.validate()
    return record


def make_positive_knowledge(**kwargs) -> PositiveKnowledge:
    record = PositiveKnowledge(**kwargs)
    record.validate()
    return record
