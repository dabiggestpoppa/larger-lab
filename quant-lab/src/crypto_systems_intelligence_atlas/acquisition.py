"""CSIA Book 2 — Bloc 2C: acquisition contracts (data only, no fetching)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .temporal import normalize_utc


class AcquisitionType(str, Enum):
    DOCUMENT = "DOCUMENT"
    REST_API = "REST_API"
    GRAPHQL = "GRAPHQL"
    RPC = "RPC"
    EXPLORER = "EXPLORER"
    REPOSITORY = "REPOSITORY"
    GOVERNANCE = "GOVERNANCE"
    STATUS_PAGE = "STATUS_PAGE"
    DATASET = "DATASET"
    NEWS = "NEWS"
    SOCIAL = "SOCIAL"


class RetrievalSemantics(str, Enum):
    POINT_IN_TIME = "POINT_IN_TIME"
    RANGE = "RANGE"
    PAGINATED = "PAGINATED"
    STREAMED = "STREAMED"
    EVENT = "EVENT"


class SnapshotPolicy(str, Enum):
    CAPTURE_ON_CHANGE = "CAPTURE_ON_CHANGE"
    CAPTURE_EVERY_POLL = "CAPTURE_EVERY_POLL"
    CAPTURE_ON_VERSION = "CAPTURE_ON_VERSION"


class SchemaDriftBehavior(str, Enum):
    RAW_FIRST_CAPTURE_AND_EVENT = "RAW_FIRST_CAPTURE_AND_EVENT"
    FAIL_CLOSED = "FAIL_CLOSED"


class AuthenticationKind(str, Enum):
    NONE = "NONE"
    API_KEY_REFERENCE = "API_KEY_REFERENCE"
    OAUTH_REFERENCE = "OAUTH_REFERENCE"
    SIGNATURE_REFERENCE = "SIGNATURE_REFERENCE"
    SESSION_REFERENCE = "SESSION_REFERENCE"


class FailureState(str, Enum):
    UNREACHABLE = "UNREACHABLE"
    AUTH_FAILURE = "AUTH_FAILURE"
    SCHEMA_DRIFT = "SCHEMA_DRIFT"
    RATE_LIMITED = "RATE_LIMITED"
    PARTIAL = "PARTIAL"
    EMPTY = "EMPTY"


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_attempts: int = Field(ge=1)
    backoff_seconds: tuple[int, ...] = ()
    preserve_failure_records: bool = True

    @model_validator(mode="after")
    def _backoff_length(self) -> "RetryPolicy":
        if len(self.backoff_seconds) not in (0, self.max_attempts - 1):
            raise ValueError("backoff tuple must contain one value between attempts")
        if any(value < 0 for value in self.backoff_seconds):
            raise ValueError("backoff values cannot be negative")
        return self


class RateLimitPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_limit: int = Field(ge=1)
    window_seconds: int = Field(ge=1)
    backoff_seconds: int = Field(default=0, ge=0)


class AuthenticationMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: AuthenticationKind
    reference: str = Field(min_length=1)

    @model_validator(mode="after")
    def _reference_only(self) -> "AuthenticationMetadata":
        if self.kind is AuthenticationKind.NONE and self.reference not in ("", "none"):
            raise ValueError("NONE authentication cannot carry a credential reference")
        return self


class CostMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    unit: str = Field(min_length=1)
    estimated_cost: float = Field(ge=0)
    currency: str = Field(min_length=1)


class AcquisitionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    acquisition_type: AcquisitionType
    request_identity: str = Field(min_length=1)
    retrieval_semantics: RetrievalSemantics
    snapshot_policy: SnapshotPolicy
    freshness_expectation: str = Field(min_length=1)
    retry_semantics: RetryPolicy
    rate_limit_semantics: RateLimitPolicy
    schema_drift_behavior: SchemaDriftBehavior
    authentication: AuthenticationMetadata
    cost: CostMetadata
    failure_states: tuple[FailureState, ...] = tuple(FailureState)

    @model_validator(mode="after")
    def _failure_states(self) -> "AcquisitionContract":
        if not self.failure_states:
            raise ValueError("acquisition contracts must represent failure states")
        return self


class AcquisitionObservation(BaseModel):
    """A successful/failed retrieval fact; no network call is performed."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    attempted_at: datetime
    succeeded: bool
    failure_state: FailureState | None = None
    evidence_refs: tuple[str, ...] = ()
    detail: str | None = None

    def model_post_init(self, __context: object) -> None:
        normalize_utc(self.attempted_at)

    @model_validator(mode="after")
    def _outcome_is_explicit(self) -> "AcquisitionObservation":
        if self.succeeded and self.failure_state is not None:
            raise ValueError("successful observations cannot carry failure_state")
        if not self.succeeded and self.failure_state is None:
            raise ValueError("failed observations require failure_state")
        return self


class AcquisitionContractBook:
    """In-memory contract registry used by tests and future orchestration."""

    def __init__(self) -> None:
        self._contracts: dict[str, AcquisitionContract] = {}
        self._observations: list[AcquisitionObservation] = []

    def register(self, contract: AcquisitionContract) -> AcquisitionContract:
        if contract.contract_id in self._contracts:
            raise ValueError(f"contract {contract.contract_id} already exists")
        self._contracts[contract.contract_id] = contract
        return contract

    def require(self, contract_id: str) -> AcquisitionContract:
        try:
            return self._contracts[contract_id]
        except KeyError as exc:
            raise KeyError(f"unknown acquisition contract {contract_id}") from exc

    def record(self, observation: AcquisitionObservation) -> AcquisitionObservation:
        self.require(observation.contract_id)
        if observation.succeeded and not observation.evidence_refs:
            raise ValueError("successful retrieval must reference captured evidence")
        self._observations.append(observation)
        return observation

    @property
    def observations(self) -> tuple[AcquisitionObservation, ...]:
        return tuple(self._observations)

    @property
    def contracts(self) -> dict[str, AcquisitionContract]:
        return dict(self._contracts)


__all__ = [
    "AcquisitionContract",
    "AcquisitionContractBook",
    "AcquisitionObservation",
    "AcquisitionType",
    "AuthenticationKind",
    "AuthenticationMetadata",
    "CostMetadata",
    "FailureState",
    "RateLimitPolicy",
    "RetrievalSemantics",
    "RetryPolicy",
    "SchemaDriftBehavior",
    "SnapshotPolicy",
]
