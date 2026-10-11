"""SENSOR-B5-I05 - revision modes and pure AS_KNOWN_THEN selection.

Frozen authority: bloc_05/02 section 10 (revision statuses and the no-inplace-
overwrite rule), section 11 (the six research revision modes; only
``AS_KNOWN_THEN`` and ``LATEST_VERIFIED`` carry frozen definitions), section 12
(later corrections must not leak into an earlier replay, and an unavailable
original yields ``PIT_REVISION_UNCERTAIN``), section 15.4 (the revision policy
must be compatible with the replay cutoff) and bloc_05/06 s13 rows 3-4.

Scope law (I05 directive phase F): this is SELECTION over caller-supplied
revision records -- pure functions, no store, no supersession graph, no
persistence.  A revision database is B5-I07 work and building one here would
be an unauthorized expansion, so the only state that exists is the tuple the
caller passes in and the tuple that comes back.

Two implemented modes and four honest refusals:

* ``AS_KNOWN_THEN`` selects only records whose knowledge window covers the
  cutoff (``known_from <= cutoff < known_to`` -- the same boundary semantics
  the I03 resolver was ratified with), so a 2025 correction can never appear
  in a 2022 replay.  When the selection contains no ``ORIGINAL`` record, the
  result is marked ``pit_uncertain``: section 12 says such a row may stay
  useful for retrospective science but must not masquerade as exact
  contemporaneous truth, and the replay gate turns that into
  ``BLOCKED_REVISION``.
* ``LATEST_VERIFIED`` selects the newest record regardless of cutoff and is
  ALWAYS ``pit_safe = False`` -- section 11 calls it "not automatically
  PIT-safe", and a mode that answered otherwise would be a silent leak.
* the other four modes RAISE :class:`UnsupportedRevisionMode`.  The plan names
  them and defines none of them; inventing their semantics is B5-I07.

Determinism: selection is ordered by ``(known_from, source_revision_id)``, so
the same inputs give byte-identical output regardless of input order.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

import yaml
from pydantic import Field, model_validator

from ...contracts.base import coerce_utc
from ..models import OpaqueIdentifier
from .enums import RevisionMode, RevisionStatus
from .models import TimeEvidenceBase, UtcTimestamp

__all__ = [
    "RevisionPolicy",
    "RevisionPolicyCatalog",
    "RevisionRecord",
    "RevisionSelection",
    "UnsupportedRevisionMode",
    "parse_revision_policies_yaml",
    "select_revisions",
    "serialize_revision_policies_yaml",
]


class UnsupportedRevisionMode(ValueError):
    """Raised for a frozen mode this checkpoint does not implement.

    Refusing is the fail-closed answer: a silently wrong selection would be
    indistinguishable from a correct one, while an exception is visible.
    """


class RevisionRecord(TimeEvidenceBase):
    """One revision of one T1 observation, with its KNOWING window.

    Fields: section 10's four (``source_revision_id``,
    ``normalization_generation``, ``supersedes_t1_record_id``,
    ``revision_status``) plus the dual-clock knowledge window
    ``known_from``/``known_to`` from bloc_05/01 section 5 -- section 11's
    "available by replay cutoff" is meaningless without a knowledge time, and
    that is the frozen vocabulary for one.

    Laws: knowledge window orders forward where finite; generation is a
    non-negative integer; identifiers are non-blank and unpadded.
    """

    source_revision_id: OpaqueIdentifier
    normalization_generation: int = Field(ge=0)
    supersedes_t1_record_id: OpaqueIdentifier | None = None
    revision_status: RevisionStatus
    known_from: UtcTimestamp
    known_to: UtcTimestamp | None = None

    @model_validator(mode="after")
    def _check_window(self) -> RevisionRecord:
        if self.known_to is not None and self.known_to <= self.known_from:
            raise ValueError(
                "known_to must be strictly after known_from "
                f"({self.known_to.isoformat()} <= {self.known_from.isoformat()})"
            )
        return self

    def known_at(self, cutoff: datetime) -> bool:
        """``known_from <= cutoff < known_to`` (the ratified I03 boundary)."""
        if self.known_from > cutoff:
            return False
        if self.known_to is not None and cutoff >= self.known_to:
            return False
        return True


class RevisionPolicy(TimeEvidenceBase):
    """One declared research revision mode.

    ``definition`` is the verbatim frozen prose of section 11 where the plan
    provides it (the two implemented modes) and ``None`` where it does not --
    a written-for-this-checkpoint definition would be an invented policy.
    """

    mode: RevisionMode
    definition: str | None = None
    source: str

    @model_validator(mode="after")
    def _check_definition(self) -> RevisionPolicy:
        implemented = (RevisionMode.AS_KNOWN_THEN, RevisionMode.LATEST_VERIFIED)
        if self.mode in implemented:
            if not (self.definition or "").strip():
                raise ValueError(
                    f"{self.mode.value} requires the verbatim frozen definition "
                    "(bloc_05/02 section 11)"
                )
        elif self.definition is not None:
            raise ValueError(
                f"{self.mode.value} has no frozen definition in bloc_05/02 "
                "section 11; writing one would invent a policy"
            )
        return self


_ORDER = [mode.value for mode in RevisionMode]


class RevisionPolicyCatalog(TimeEvidenceBase):
    """The complete frozen mode set as declared configuration."""

    schema_version: str
    policies: tuple[RevisionPolicy, ...]

    @model_validator(mode="before")
    @classmethod
    def _canonicalize(cls, payload: object) -> object:
        if not isinstance(payload, dict):
            return payload
        rows = payload.get("policies")
        if isinstance(rows, list):
            def rank(row: object) -> int:
                value = str(row.get("mode", "")) if isinstance(row, dict) else ""
                return _ORDER.index(value) if value in _ORDER else len(_ORDER)

            payload = {**payload, "policies": sorted(rows, key=rank)}
        return payload

    @model_validator(mode="after")
    def _check_coverage(self) -> RevisionPolicyCatalog:
        modes = [policy.mode for policy in self.policies]
        if len(set(modes)) != len(modes):
            raise ValueError("duplicate revision policy mode in configuration")
        if set(modes) != set(RevisionMode):
            missing = sorted(mode.value for mode in set(RevisionMode) - set(modes))
            raise ValueError(
                f"configuration must declare every frozen revision mode; missing {missing}"
            )
        return self

    def policy_for(self, mode: RevisionMode) -> RevisionPolicy:
        for policy in self.policies:
            if policy.mode is mode:
                return policy
        raise ValueError(f"no policy declared for {mode.value}")  # pragma: no cover


class RevisionSelection(TimeEvidenceBase):
    """The outcome of one selection: what was chosen, what was withheld.

    ``pit_safe`` answers "may this selection be presented as point-in-time
    truth?"; ``pit_uncertain`` answers section 12's narrower question ("was
    the ORIGINAL even available?").  They are independent on purpose: an
    ``AS_KNOWN_THEN`` selection can be pit-safe yet uncertain when the
    original never existed in the input.
    """

    mode: RevisionMode
    selected: tuple[RevisionRecord, ...]
    excluded: tuple[RevisionRecord, ...]
    pit_safe: bool
    pit_uncertain: bool


def _order(records: Iterable[RevisionRecord]) -> tuple[RevisionRecord, ...]:
    return tuple(
        sorted(records, key=lambda record: (record.known_from, record.source_revision_id))
    )


def select_revisions(
    revisions: tuple[RevisionRecord, ...],
    policy: RevisionPolicy,
    replay_cutoff: datetime,
) -> RevisionSelection:
    """Pure selection under ``policy`` at ``replay_cutoff``.

    No wall clock: the cutoff is always an explicit argument, because a
    default cutoff would be a replay-safety decision made by accident.
    """
    cutoff = coerce_utc(replay_cutoff)
    ids = [record.source_revision_id for record in revisions]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate source_revision_id in one selection call")

    if policy.mode is RevisionMode.AS_KNOWN_THEN:
        chosen = [record for record in revisions if record.known_at(cutoff)]
        withheld = [record for record in revisions if not record.known_at(cutoff)]
        return RevisionSelection(
            mode=policy.mode,
            selected=_order(chosen),
            excluded=_order(withheld),
            pit_safe=True,
            pit_uncertain=not any(
                record.revision_status is RevisionStatus.ORIGINAL for record in chosen
            ),
        )

    if policy.mode is RevisionMode.LATEST_VERIFIED:
        if not revisions:
            return RevisionSelection(
                mode=policy.mode,
                selected=(),
                excluded=(),
                pit_safe=False,
                pit_uncertain=False,
            )
        ordered = _order(revisions)
        newest = ordered[-1]
        return RevisionSelection(
            mode=policy.mode,
            selected=(newest,),
            excluded=tuple(record for record in ordered if record is not newest),
            pit_safe=False,
            pit_uncertain=False,
        )

    raise UnsupportedRevisionMode(
        f"revision mode {policy.mode.value} is frozen in bloc_05/02 section 11 "
        "but has no frozen definition and no authorized implementation "
        "(B5-I07); refusing instead of improvising a selection"
    )


def parse_revision_policies_yaml(text: str) -> RevisionPolicyCatalog:
    """Parse configuration TEXT.  No path is read here, ever."""
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid revision policies YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "revision policies document must be a mapping with schema_version "
            "and policies"
        )
    return RevisionPolicyCatalog.model_validate(payload)


def serialize_revision_policies_yaml(catalog: RevisionPolicyCatalog) -> str:
    """Deterministic YAML: frozen mode order, fixed key order."""
    payload = {
        "schema_version": catalog.schema_version,
        "policies": [
            {
                "mode": policy.mode.value,
                "definition": policy.definition,
                "source": policy.source,
            }
            for policy in catalog.policies
        ],
    }
    return yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=100,
    )
