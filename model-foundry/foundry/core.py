"""Core primitives for the Larger Lab Model Foundry substrate.

Governing doctrine (MF-B0):

    MODEL OUTPUT != INSTITUTIONAL TRUTH
    WEIGHTS != CANONICAL MEMORY
    CAPABILITY != AUTHORITY
    ACCESS != RIGHTS
    AVAILABLE DATA != TRAINABLE DATA
    PROVIDER OFFER != GUARANTEE
    REGISTERED SOURCE != CLEAN SOURCE

This module holds only mechanics shared by MF-B0..MF-B4: deterministic
fingerprints, immutable containers, fail-closed policy errors, noncanonical
OCE test-double declarations, and receipt writing. It deliberately contains no
authority engine, no identity system, no generic evidence constitution, no
scheduler, and no generic artifact store (One-OCE boundary).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NONCANONICAL_MARKER = "NONCANONICAL_OCE_TEST_DOUBLE"

FOUNDRY_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Canonical serialization / fingerprints
# --------------------------------------------------------------------------


def _plain(value: Any) -> Any:
    """Convert a value into a plain JSON-compatible structure, deterministically."""

    if isinstance(value, FrozenMap):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        # Sets are rejected: canonical ordering of unordered collections is
        # ambiguous, and ambiguity in a fingerprint is a truth defect.
        raise TypeError("sets are not canonical; use a sorted list or FrozenMap")
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def canonical_json(value: Any) -> str:
    """Deterministic JSON: sorted keys, no insignificant whitespace."""

    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )


def fingerprint(value: Any) -> str:
    """Content fingerprint of a material scientific object."""

    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def digest_of_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


class FrozenMap(Mapping[str, Any]):
    """Immutable mapping with no supported path back to a mutable backing store.

    The backing dict is created and handed to ``MappingProxyType`` inside
    ``__init__`` and is never stored on the instance, so nested mutation through
    public attributes is not possible. The retained claim (tested) is:

        immutable through all supported/public access paths.

    This is not a claim of invulnerability to arbitrary ``ctypes``/GC
    introspection, and no such claim is made anywhere in the evidence package.
    """

    __slots__ = ("_proxy",)

    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        from types import MappingProxyType

        rebuilt = {str(k): _freeze(v) for k, v in dict(data or {}).items()}
        object.__setattr__(self, "_proxy", MappingProxyType(rebuilt))

    def __getitem__(self, key: str) -> Any:
        return self._proxy[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._proxy)

    def __len__(self) -> int:
        return len(self._proxy)

    def __contains__(self, key: object) -> bool:
        return key in self._proxy

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"FrozenMap({dict(self._proxy)!r})"

    def to_dict(self) -> dict[str, Any]:
        return {k: _thaw(v) for k, v in self._proxy.items()}


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return FrozenMap(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        raise TypeError("sets are not canonical; use a sorted list or FrozenMap")
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, FrozenMap):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


# --------------------------------------------------------------------------
# Policy / fail-closed errors
# --------------------------------------------------------------------------


class FoundryError(Exception):
    """Base class for Foundry errors."""


class PolicyBlocked(FoundryError):
    """A governed policy refused an operation. Fail closed, never downgrade."""

    def __init__(self, code: str, detail: str, **context: Any) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail, "context": self.context}


class Unauthorized(FoundryError):
    """An action attempted to exceed the Foundry authority ceiling."""

    def __init__(self, code: str, detail: str, **context: Any) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail, "context": self.context}


class Contradiction(FoundryError):
    """Two governed commitments cannot both hold."""


# --------------------------------------------------------------------------
# One-OCE boundary: noncanonical test doubles
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class OceTestDouble:
    """Declaration that a local service is a temporary, noncanonical stand-in.

    Every generic-looking local fixture must carry one of these. A fixture
    without a declared replacement path is a permanent second-OCE risk and is
    rejected by :meth:`assert_replaceable`.
    """

    fixture: str
    canonical_oce_target: str
    replacement_condition: str
    retirement_evidence: str
    noncanonical: bool = True

    def __post_init__(self) -> None:
        for name in (
            "fixture",
            "canonical_oce_target",
            "replacement_condition",
            "retirement_evidence",
        ):
            if not str(getattr(self, name)).strip():
                raise PolicyBlocked(
                    "NONCANONICAL_DECLARATION_INCOMPLETE",
                    f"{self.fixture!r} is missing {name}",
                )
        if self.noncanonical is not True:
            raise PolicyBlocked(
                "NONCANONICAL_FLAG_REQUIRED",
                f"{self.fixture!r} must declare noncanonical=true",
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["marker"] = NONCANONICAL_MARKER
        return payload


# --------------------------------------------------------------------------
# Receipts
# --------------------------------------------------------------------------


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class Receipt:
    """Truthful record of what a Foundry operation actually did."""

    kind: str
    subject: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        body = {
            "kind": self.kind,
            "subject": self.subject,
            **self.payload,
        }
        body.setdefault("recorded_utc", utc_now_iso())
        body["receipt_fingerprint"] = fingerprint(
            {k: v for k, v in body.items() if k != "recorded_utc"}
        )
        return body


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_plain(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_receipt(directory: Path, name: str, receipt: Receipt) -> Path:
    return write_json(directory / f"{name}.json", receipt.to_dict())


# --------------------------------------------------------------------------
# Versioned, immutable registry
# --------------------------------------------------------------------------


@dataclass
class VersionedEntry:
    record: Any
    version: int
    reason: str
    actor: str
    predecessor_fingerprint: str | None
    recorded_utc: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        record = self.record.to_dict() if hasattr(self.record, "to_dict") else self.record
        return {
            "version": self.version,
            "reason": self.reason,
            "actor": self.actor,
            "predecessor_fingerprint": self.predecessor_fingerprint,
            "recorded_utc": self.recorded_utc,
            "record_fingerprint": fingerprint(record),
            "record": record,
        }


class VersionedRegistry:
    """Append-only registry: a change creates a new version, never a silent overwrite.

    This is a Foundry-local domain registry (sources, datasets, artifacts,
    benchmarks). It is *not* a generic institutional identity or evidence
    service; see :data:`GENERIC_SERVICE_DOUBLES`.
    """

    def __init__(self, name: str, double: OceTestDouble) -> None:
        self.name = name
        self.double = double
        self._history: dict[str, list[VersionedEntry]] = {}

    def put(self, key: str, record: Any, *, actor: str, reason: str) -> VersionedEntry:
        if not str(actor).strip():
            raise PolicyBlocked("ACTOR_REQUIRED", f"{self.name}: actor is required")
        if not str(reason).strip():
            raise PolicyBlocked("REASON_REQUIRED", f"{self.name}: reason is required")
        history = self._history.setdefault(key, [])
        predecessor = (
            fingerprint(_record_payload(history[-1])) if history else None
        )
        entry = VersionedEntry(
            record=record,
            version=len(history) + 1,
            reason=reason,
            actor=actor,
            predecessor_fingerprint=predecessor,
        )
        history.append(entry)
        return entry

    def get(self, key: str) -> Any:
        history = self._history.get(key)
        if not history:
            raise PolicyBlocked("RECORD_UNRESOLVED", f"{self.name}: no record {key!r}")
        return history[-1].record

    def resolve(self, key: str) -> bool:
        return bool(self._history.get(key))

    def history(self, key: str) -> tuple[VersionedEntry, ...]:
        return tuple(self._history.get(key, ()))

    def keys(self) -> tuple[str, ...]:
        return tuple(self._history)

    def version(self, key: str) -> int:
        return len(self._history.get(key, ()))

    def digest(self) -> str:
        return fingerprint(
            {
                key: [entry.to_dict() for entry in entries]
                for key, entries in self._history.items()
            }
        )


def _record_payload(entry: VersionedEntry) -> Any:
    record = entry.record
    return record.to_dict() if hasattr(record, "to_dict") else record


# Generic institutional services that must NOT be rebuilt permanently inside the
# Foundry. Each local stand-in is declared, replaceable, and test-visible.
GENERIC_SERVICE_DOUBLES: dict[str, OceTestDouble] = {
    "identity": OceTestDouble(
        fixture="FoundryLocalIdentity",
        canonical_oce_target="OCE identity / actor registry",
        replacement_condition="replace when convergence branch exposes canonical identity service",
        retirement_evidence="Foundry actor references resolve through OCE identity adapter",
    ),
    "authority": OceTestDouble(
        fixture="FoundryLocalAuthorityProjection",
        canonical_oce_target="OCE AuthorityState / capability grants (A-009/A-010 lineage)",
        replacement_condition="replace when canonical OCE authority projection is available",
        retirement_evidence="no Foundry-local grant may authorize an action once OCE projection is bound",
    ),
    "evidence": OceTestDouble(
        fixture="FoundryLocalEvidenceLedger",
        canonical_oce_target="OCE EvidenceGraph / evidence registry",
        replacement_condition="replace when convergence branch exposes canonical evidence graph",
        retirement_evidence="evidence refs carry canonical OCE envelope ids",
    ),
    "artifacts": OceTestDouble(
        fixture="FoundryLocalArtifactStore",
        canonical_oce_target="OCE artifact registry + artifact-manifest envelope",
        replacement_condition="replace when OCE artifact service is exposed on the convergence branch",
        retirement_evidence="artifact digests resolve through OCE artifact registry",
    ),
    "negative_knowledge": OceTestDouble(
        fixture="FoundryLocalNegativeKnowledge",
        canonical_oce_target="OCE NegativeKnowledge with governed reopen semantics (A-004/A-009 lineage)",
        replacement_condition="replace when canonical NegativeKnowledge service is consumable",
        retirement_evidence="reopen conditions evaluated by canonical lifecycle, not locally",
    ),
    "workflow": OceTestDouble(
        fixture="FoundryLocalRunLifecycle",
        canonical_oce_target="OCE WorkGraph / governed workflow",
        replacement_condition="replace when generic workflow service exists",
        retirement_evidence="experiment runs admitted through canonical workflow nodes",
    ),
    "resource_intelligence": OceTestDouble(
        fixture="FoundryLocalOfferNormalizer",
        canonical_oce_target="OCE B10 Resource Intelligence (COMPUTE.GPU.RENT)",
        replacement_condition="replace when B10 exposes provider-neutral offer/routing",
        retirement_evidence="Foundry submits ComputeRequest to B10 and consumes routing receipts",
    ),
    "evaluation_governance": OceTestDouble(
        fixture="FoundryLocalEvaluationFreeze",
        canonical_oce_target="OCE B6 Evaluation Service / CEREBUS-governed evaluator freeze (G6 lineage)",
        replacement_condition="replace when OCE owns evaluator freeze/ratification authority",
        retirement_evidence="protocol freeze receipts are issued by the canonical evaluator service",
    ),
    "recovery": OceTestDouble(
        fixture="FoundryLocalCheckpointRecovery",
        canonical_oce_target="OCE recovery/resume service",
        replacement_condition="replace when generic recovery exists",
        retirement_evidence="provider-loss recovery runs through canonical recovery service",
    ),
    "budget": OceTestDouble(
        fixture="FoundryLocalBudgetLedger",
        canonical_oce_target="OCE resource budget service",
        replacement_condition="replace when OCE budget authority is consumable",
        retirement_evidence="budget holds are issued by canonical budget service",
    ),
}


# --------------------------------------------------------------------------
# Independence
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class IndependenceVector:
    """Multi-axis independence. UNKNOWN is never favorable.

    Dimensions are recorded as ``VERIFIED`` / ``ABSENT`` / ``UNKNOWN`` so that
    unknown ancestry can never be silently counted as independence.
    """

    axes: FrozenMap

    UNKNOWN = "UNKNOWN"
    VERIFIED = "VERIFIED"
    ABSENT = "ABSENT"

    @classmethod
    def build(cls, **axes: str) -> IndependenceVector:
        normalized = {k: str(v).upper() for k, v in axes.items()}
        for key, value in normalized.items():
            if value not in {cls.VERIFIED, cls.ABSENT, cls.UNKNOWN}:
                raise PolicyBlocked(
                    "INDEPENDENCE_STATE_INVALID",
                    f"{key}={value!r} is not one of VERIFIED/ABSENT/UNKNOWN",
                )
        return cls(axes=FrozenMap(normalized))

    def state(self, axis: str) -> str:
        return str(self.axes.get(axis, self.UNKNOWN))

    @property
    def verified_axes(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.axes.items() if v == self.VERIFIED))

    @property
    def unknown_axes(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.axes.items() if v == self.UNKNOWN))

    def is_independent_on(self, axis: str) -> bool:
        return self.state(axis) == self.VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "axes": dict(self.axes),
            "verified_axes": list(self.verified_axes),
            "unknown_axes": list(self.unknown_axes),
        }
