"""SQLite adapters: knowledge + receipt repositories, decision-reuse query.

All adapters follow the P1-C03 store conventions: payload JSON + canonical
digest with read-back verification, INSERT-only, parameterized SQL.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.knowledge import NegativeKnowledge, PositiveKnowledge
from qcae.core.knowledge.memory import NegativeKnowledgeType
from qcae.core.ports.capability_registry import CapabilityRegistryPort
from qcae.core.ports.evidence_registry import LifecycleLogRepository
from qcae.core.ports.knowledge_registry import (
    NegativeKnowledgeRepository,
    PositiveKnowledgeRepository,
    ReceiptRepository,
    RegistryQuery,
)
from qcae.core.ports.repository_registry import RepositoryRegistryPort
from qcae.core.receipts import CapabilityReceipt, ReceiptState

__all__ = [
    "SqliteNegativeKnowledgeRepository",
    "SqlitePositiveKnowledgeRepository",
    "SqliteReceiptRepository",
    "SqliteRegistryQuery",
    "KNOWLEDGE_DDL",
]

KNOWLEDGE_DDL = """
CREATE TABLE IF NOT EXISTS negative_knowledge (
    record_id      TEXT PRIMARY KEY,
    subject_id     TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    failure_type   TEXT NOT NULL,
    payload_json   TEXT NOT NULL,
    payload_digest TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_neg_subject ON negative_knowledge(subject_id, source_revision);
CREATE INDEX IF NOT EXISTS ix_neg_type ON negative_knowledge(failure_type);

CREATE TABLE IF NOT EXISTS positive_knowledge (
    record_id      TEXT PRIMARY KEY,
    subject_id     TEXT NOT NULL,
    contract_id    TEXT NOT NULL,
    payload_json   TEXT NOT NULL,
    payload_digest TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pos_subject ON positive_knowledge(subject_id);
CREATE INDEX IF NOT EXISTS ix_pos_contract ON positive_knowledge(contract_id);

CREATE TABLE IF NOT EXISTS capability_receipt (
    receipt_id      TEXT PRIMARY KEY,
    capability_id   TEXT NOT NULL,
    state           TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_rcpt_capability ON capability_receipt(capability_id);
CREATE INDEX IF NOT EXISTS ix_rcpt_state ON capability_receipt(state);
"""


def _repo_id(source_ref: str) -> Optional[str]:
    """Repository id from a ``repo:<id>`` candidate source ref, else ``None``."""
    return source_ref[len("repo:"):] if source_ref.startswith("repo:") else None


def _decode(row, record_id: str, builder):
    payload_json, payload_digest = row
    data = json.loads(payload_json)
    record = builder.from_dict(data)
    if record.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored record {record_id!r} failed integrity check (digest mismatch)"
        )
    return record


class SqliteNegativeKnowledgeRepository(NegativeKnowledgeRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, record: NegativeKnowledge) -> str:
        payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
        try:
            self._conn.execute(
                "INSERT INTO negative_knowledge (record_id, subject_id, source_revision,"
                " failure_type, payload_json, payload_digest) VALUES (?, ?, ?, ?, ?, ?)",
                (record.record_id, record.subject_id, record.source_revision,
                 record.failure_type.value, payload, record.digest()),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"negative knowledge {record.record_id!r} already stored "
                "(append-only: supersede under changed conditions instead)"
            ) from exc
        return record.record_id

    def get(self, record_id: str) -> Optional[NegativeKnowledge]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM negative_knowledge WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return _decode(row, record_id, NegativeKnowledge) if row else None

    def _rows(self, where: str, params: tuple) -> List[NegativeKnowledge]:
        rows = self._conn.execute(
            "SELECT record_id, payload_json, payload_digest FROM negative_knowledge"
            f" WHERE {where} ORDER BY record_id",
            params,
        ).fetchall()
        return [_decode((r[1], r[2]), r[0], NegativeKnowledge) for r in rows]

    def find_by_subject(self, subject_id: str, source_revision: str = "") -> List[NegativeKnowledge]:
        if source_revision:
            return self._select_helper(subject_id, source_revision)
        return self._rows("subject_id = ?", (subject_id,))

    def _select_helper(self, subject_id: str, source_revision: str) -> List[NegativeKnowledge]:
        return self._rows("subject_id = ? AND source_revision = ?", (subject_id, source_revision))

    def find_by_failure_type(self, failure_type: NegativeKnowledgeType) -> List[NegativeKnowledge]:
        return self._rows("failure_type = ?", (failure_type.value,))

    def active(self) -> List[NegativeKnowledge]:
        return self._rows(
            "json_extract(payload_json, '$.superseded_by') = ''"
            " OR json_extract(payload_json, '$.superseded_by') IS NULL", ()
        )


class SqlitePositiveKnowledgeRepository(PositiveKnowledgeRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, record: PositiveKnowledge) -> str:
        payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
        try:
            self._conn.execute(
                "INSERT INTO positive_knowledge (record_id, subject_id, contract_id,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?, ?)",
                (record.record_id, record.subject_id, record.contract_id, payload,
                 record.digest()),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"positive knowledge {record.record_id!r} already stored "
                "(append-only: supersede with a new record)"
            ) from exc
        return record.record_id

    def get(self, record_id: str) -> Optional[PositiveKnowledge]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM positive_knowledge WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return _decode(row, record_id, PositiveKnowledge) if row else None

    def _rows(self, where: str, params: tuple) -> List[PositiveKnowledge]:
        rows = self._conn.execute(
            "SELECT record_id, payload_json, payload_digest FROM positive_knowledge"
            f" WHERE {where} ORDER BY record_id",
            params,
        ).fetchall()
        return [_decode((r[1], r[2]), r[0], PositiveKnowledge) for r in rows]

    def find_by_subject(self, subject_id: str) -> List[PositiveKnowledge]:
        return self._rows("subject_id = ?", (subject_id,))

    def find_by_contract(self, contract_id: str, contract_version: str = "") -> List[PositiveKnowledge]:
        if contract_version:
            return self._rows(
                "contract_id = ? AND json_extract(payload_json, '$.contract_version') = ?",
                (contract_id, contract_version),
            )
        return self._rows("contract_id = ?", (contract_id,))

    def material(self) -> List[PositiveKnowledge]:
        return self._rows(
            "json_extract(payload_json, '$.material') = 1", ()
        )


class SqliteReceiptRepository(ReceiptRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, receipt: CapabilityReceipt) -> str:
        payload = json.dumps(receipt.to_dict(), ensure_ascii=False, sort_keys=True)
        try:
            self._conn.execute(
                "INSERT INTO capability_receipt (receipt_id, capability_id, state,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?, ?)",
                (receipt.receipt_id, receipt.capability_id, receipt.state.value,
                 payload, receipt.digest()),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"receipt {receipt.receipt_id!r} already stored "
                "(state transitions create new receipt records, never rewrites)"
            ) from exc
        return receipt.receipt_id

    def get(self, receipt_id: str) -> Optional[CapabilityReceipt]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_receipt WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
        return _decode(row, receipt_id, CapabilityReceipt) if row else None

    def _rows(self, where: str, params: tuple) -> List[CapabilityReceipt]:
        rows = self._conn.execute(
            "SELECT receipt_id, payload_json, payload_digest FROM capability_receipt"
            f" WHERE {where} ORDER BY receipt_id",
            params,
        ).fetchall()
        return [_decode((r[1], r[2]), r[0], CapabilityReceipt) for r in rows]

    def find_by_capability(self, capability_id: str) -> List[CapabilityReceipt]:
        return self._rows("capability_id = ?", (capability_id,))

    def find_by_state(self, state: ReceiptState) -> List[CapabilityReceipt]:
        return self._rows("state = ?", (state.value,))

    def active_for_capability(self, capability_id: str) -> List[CapabilityReceipt]:
        return self._rows("capability_id = ? AND state = ?",
                          (capability_id, ReceiptState.ACTIVE.value))

    def superseded_by(self, receipt_id: str) -> List[CapabilityReceipt]:
        return self._rows(
            "json_extract(payload_json, '$.supersedes_receipt') = ?", (receipt_id,)
        )


class SqliteRegistryQuery(RegistryQuery):
    """Composes the repositories into the 9.7 retrieval-order query.

    Every component is optional, because **partial wiring is a valid shape**
    (P1-R1 continuation §9/§11): a query assembled with only some repositories
    present answers with empty findings for the absent ones rather than raising.
    That rule has exactly one owner, :meth:`_optional_call`, so no retrieval
    method branches on wiring and none can forget to. The shared derivations
    below (matched receipts, contract versions, atom ids, repository revisions)
    are likewise defined once and read by every method that needs them.

    Deferred debt (P1-R1 freeze manifest, MINOR): the freshness lookup reads
    the lifecycle log's connection directly, because the frozen
    ``LifecycleLogRepository`` port exposes no enumeration.
    """

    def __init__(
        self,
        receipts: Optional[ReceiptRepository],
        positive: Optional[PositiveKnowledgeRepository],
        negative: Optional[NegativeKnowledgeRepository],
        evidence_freshness: Optional[LifecycleLogRepository],
        capability_registry: Optional[CapabilityRegistryPort] = None,
        repository_registry: Optional[RepositoryRegistryPort] = None,
    ) -> None:
        self._receipts = receipts
        self._positive = positive
        self._negative = negative
        self._freshness = evidence_freshness
        self._capabilities = capability_registry
        self._repositories = repository_registry

    # -- partial-wiring policy, in one place ---------------------------------

    @staticmethod
    def _optional_call(component, method: str, *args, default=()):
        """Ask an optional component; absent wiring contributes ``default``."""
        if component is None:
            return default
        return getattr(component, method)(*args)

    # -- shared derivations --------------------------------------------------

    def _matched_active_receipts(self, capability_id: str, contract_id: str,
                                 contract_version: str) -> List[CapabilityReceipt]:
        """Active receipts of this capability issued under this exact contract."""
        return [
            r for r in self._optional_call(
                self._receipts, "active_for_capability", capability_id)
            if r.contract_id == contract_id and r.contract_version == contract_version
        ]

    def _contract_versions(self, capability_id: str) -> List[str]:
        return [
            c.contract_version for c in self._optional_call(
                self._capabilities, "list_contract_versions", capability_id)
        ]

    def _atom_ids(self, capability_id: str) -> List[str]:
        """Atoms defining this capability, de-duplicated and ordered."""
        atoms = self._optional_call(
            self._capabilities, "list_atoms_for_capability", capability_id)
        return sorted({a.atom_id for a in atoms})

    def _candidates_for_atom(self, atom_id: str) -> list:
        return list(self._optional_call(
            self._capabilities, "list_candidates_for_atom", atom_id))

    def _stored_revisions(self, repo_id: str) -> List[str]:
        """Revisions this repository registry holds for one repository."""
        return sorted(
            r.revision for r in self._optional_call(
                self._repositories, "list_revisions", repo_id)
        )

    def _repository_revisions(self, atom_ids: List[str]) -> dict:
        """Revisions stored for the repositories the known candidates sit in."""
        revisions: dict = {}
        for atom_id in atom_ids:
            for cand in self._candidates_for_atom(atom_id):
                repo_id = _repo_id(cand.source_ref)
                if repo_id is None:
                    continue
                stored = self._stored_revisions(repo_id)
                if stored:
                    revisions[repo_id] = stored
        return revisions

    def decision_reuse_findings(self, capability_id: str, contract_id: str,
                                contract_version: str) -> dict:
        """9.7 retrieval-order layers for one request."""
        matched = self._matched_active_receipts(
            capability_id, contract_id, contract_version)
        positive = [
            k for k in self._optional_call(
                self._positive, "find_by_contract", contract_id, contract_version)
            if k.material
        ]
        blocking = [
            n for n in self._optional_call(self._negative, "active")
            if not n.retry_allowed
        ]
        return {
            "active_receipts": [r.receipt_id for r in matched],
            "positive_knowledge": [k.record_id for k in positive],
            "negative_blocks": [n.record_id for n in blocking],
            "stale_evidence": self._stale_evidence_ids(),
            "sufficient_without_discovery": (
                bool(matched) and bool(positive) and not blocking),
        }

    def known_capability_state(self, capability_id: str) -> dict:
        """P1-R1 §11: structured inventory for the future discovery planner.

        Pure retrieval over durable registries; never mutates, never searches
        externally, never invents capability semantics.
        """
        versions = self._contract_versions(capability_id)
        latest = max(versions) if versions else None
        atom_ids = self._atom_ids(capability_id)
        composite = None
        if latest is not None:
            composite = self._optional_call(
                self._capabilities, "get_composite", capability_id, latest,
                default=None)
        # Every wiring shape returns the same keys, absent components included:
        # callers read this inventory without branching on configuration.
        return {
            "contract_versions": versions,
            "latest_contract_version": latest,
            "atom_ids": atom_ids,
            "composite_member_count": (
                len(composite.members) if composite is not None else None),
            "candidate_refs": sorted({
                cand.candidate_id
                for atom_id in atom_ids
                for cand in self._candidates_for_atom(atom_id)
            }),
            "repository_revisions": self._repository_revisions(atom_ids),
        }

    def internal_evidence_by_atom(self, capability_id: str, contract_id: str,
                                  contract_version: str) -> dict:
        """Per-atom attribution over the same records the other methods report.

        Pure retrieval: each record is attributed by its own declared scope, so a
        consumer can claim exactly the atoms the evidence names instead of the
        whole capability. Built from the derivations above rather than new
        queries, so absent components contribute nothing (partial wiring).
        """
        evidence: dict = {}

        for atom_id in self._atom_ids(capability_id):
            for candidate in self._candidates_for_atom(atom_id):
                evidence.setdefault(atom_id, set()).add(candidate.candidate_id)

        for receipt in self._matched_active_receipts(
                capability_id, contract_id, contract_version):
            for atom_id in receipt.atom_ids:
                evidence.setdefault(atom_id, set()).add(receipt.receipt_id)

        return {atom_id: tuple(sorted(refs))
                for atom_id, refs in sorted(evidence.items())}

    def internal_first_findings(self, capability_id: str, contract_id: str,
                                contract_version: str) -> dict:
        """P1-R1 continuation §9: structured A–F internal-first classification.

        Pure retrieval; the P3 planner decides what to do with it.
        """
        categories: List[str] = []
        detail: dict = {}

        # A — capability active under this contract
        matched = self._matched_active_receipts(
            capability_id, contract_id, contract_version)
        if matched:
            categories.append("CAPABILITY_ACTIVE")
            detail["CAPABILITY_ACTIVE"] = [r.receipt_id for r in matched]

        # B — evidence stale
        stale = self._stale_evidence_ids()
        if stale:
            categories.append("EVIDENCE_STALE")
            detail["EVIDENCE_STALE"] = stale

        atom_ids = self._atom_ids(capability_id)

        # C — candidate previously failed for one of this capability's atoms
        blocked = [
            n.record_id
            for n in self._optional_call(self._negative, "active")
            if not n.retry_allowed and n.subject_id in atom_ids
        ]
        if blocked:
            categories.append("CANDIDATE_PREVIOUSLY_FAILED")
            detail["CANDIDATE_PREVIOUSLY_FAILED"] = blocked

        # D — revision changed (ADR-0007): a candidate's claimed revision is
        # absent from the located repository's stored revisions
        revision_changed: List[str] = []
        for atom_id in atom_ids:
            for cand in self._candidates_for_atom(atom_id):
                repo_id = _repo_id(cand.source_ref)
                if repo_id is None:
                    continue
                stored = set(self._stored_revisions(repo_id))
                if stored and cand.revision not in stored:
                    revision_changed.append(cand.candidate_id)
        if revision_changed:
            categories.append("REVISION_CHANGED")
            detail["REVISION_CHANGED"] = sorted(set(revision_changed))

        # E — definition without implementation
        if atom_ids and not any(self._candidates_for_atom(a) for a in atom_ids):
            categories.append("DEFINITION_WITHOUT_IMPLEMENTATION")
            detail["DEFINITION_WITHOUT_IMPLEMENTATION"] = atom_ids

        # F — no internal knowledge at all
        if not categories and not self._contract_versions(capability_id):
            categories.append("NO_INTERNAL_KNOWLEDGE")
            detail["NO_INTERNAL_KNOWLEDGE"] = []

        return {"capability_id": capability_id, "categories": categories,
                "detail": detail}

    def _stale_evidence_ids(self) -> List[str]:
        """Evidence whose latest logged freshness is stale/revalidation-required.

        The log holds only non-current states as latest entries, so current
        evidence has no qualifying row. Reads the log's connection directly
        because the frozen ``LifecycleLogRepository`` port exposes no
        enumeration (P1-R1 freeze manifest, MINOR).
        """
        conn = getattr(self._freshness, "_conn", None)
        if conn is None:
            return []
        rows = conn.execute(
            "SELECT DISTINCT evidence_id FROM freshness_log f"
            " WHERE seq = (SELECT MAX(seq) FROM freshness_log g"
            "              WHERE g.evidence_id = f.evidence_id)"
            " AND to_state IN ('STALE','REVALIDATION_REQUIRED')"
        ).fetchall()
        return [r[0] for r in rows]
