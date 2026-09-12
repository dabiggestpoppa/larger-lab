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
from qcae.core.ports.knowledge_registry import (
    NegativeKnowledgeRepository,
    PositiveKnowledgeRepository,
    ReceiptRepository,
    RegistryQuery,
)
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
    """Composes the repositories into the 9.7 retrieval-order query."""

    def __init__(
        self,
        receipts: SqliteReceiptRepository,
        positive: SqlitePositiveKnowledgeRepository,
        negative: SqliteNegativeKnowledgeRepository,
        evidence_freshness,  # LifecycleLogRepository
        capability_registry=None,  # CapabilityRegistryPort (P1-R1 §11)
        repository_registry=None,  # RepositoryRegistryPort (P1-R1 continuation §8)
    ) -> None:
        self._receipts = receipts
        self._positive = positive
        self._negative = negative
        self._freshness = evidence_freshness
        self._capabilities = capability_registry
        self._repositories = repository_registry

    def decision_reuse_findings(self, capability_id: str, contract_id: str, contract_version: str) -> dict:
        active = self._receipts.active_for_capability(capability_id)
        matched_receipts = [
            r for r in active
            if r.contract_id == contract_id and r.contract_version == contract_version
        ]
        pos = [
            k for k in self._positive.find_by_contract(contract_id, contract_version)
            if k.material
        ]
        blocks = [
            n for n in self._negative.active() if not n.retry_allowed
        ]
        stale = [
            ev_id for ev_id in self._stale_evidence_ids()
        ]
        return {
            "active_receipts": [r.receipt_id for r in matched_receipts],
            "positive_knowledge": [k.record_id for k in pos],
            "negative_blocks": [n.record_id for n in blocks],
            "stale_evidence": stale,
            "sufficient_without_discovery": bool(matched_receipts) and bool(pos) and not blocks,
        }

    def known_capability_state(self, capability_id: str) -> dict:
        """P1-R1 §11: structured inventory for the future discovery planner.

        Pure retrieval over durable registries; never mutates, never searches
        externally, never invents capability semantics.
        """
        state: dict = {
            "contract_versions": [],
            "latest_contract_version": None,
            "atom_ids": [],
            "composite_member_count": None,
            "candidate_refs": [],
        }
        if self._capabilities is None:
            return state
        contracts = self._capabilities.list_contract_versions(capability_id)
        state["contract_versions"] = [c.contract_version for c in contracts]
        state["latest_contract_version"] = (
            max(state["contract_versions"]) if state["contract_versions"] else None
        )
        atoms = self._capabilities.list_atoms_for_capability(capability_id)
        state["atom_ids"] = sorted({a.atom_id for a in atoms})
        if state["latest_contract_version"] is not None:
            composite = self._capabilities.get_composite(
                capability_id, state["latest_contract_version"])
            if composite is not None:
                state["composite_member_count"] = len(composite.members)
        candidate_ids = set()
        for atom_id in state["atom_ids"]:
            for cand in self._capabilities.list_candidates_for_atom(atom_id):
                candidate_ids.add(cand.candidate_id)
        state["candidate_refs"] = sorted(candidate_ids)
        # repository revisions the known candidates are located in (ADR-0007)
        repo_revisions: dict = {}
        if self._repositories is not None:
            for atom_id in state["atom_ids"]:
                for cand in self._capabilities.list_candidates_for_atom(atom_id):
                    ref = cand.source_ref
                    if ref.startswith("repo:"):
                        repo_id = ref[len("repo:"):]
                        revs = self._repositories.list_revisions(repo_id)
                        if revs:
                            repo_revisions[repo_id] = sorted(
                                r.revision for r in revs)
        state["repository_revisions"] = repo_revisions
        return state

    def internal_first_findings(self, capability_id: str, contract_id: str,
                                contract_version: str) -> dict:
        """P1-R1 continuation §9: structured A–F internal-first classification.
        Pure retrieval; the P3 planner decides what to do with it."""
        categories: List[str] = []
        detail: dict = {}

        # A — capability active
        active = self._receipts.active_for_capability(capability_id) \
            if self._receipts is not None else []
        matched = [r for r in active
                   if r.contract_id == contract_id
                   and r.contract_version == contract_version]
        if matched:
            categories.append("CAPABILITY_ACTIVE")
            detail["CAPABILITY_ACTIVE"] = [r.receipt_id for r in matched]

        # B — evidence stale
        stale = self._stale_evidence_ids()
        if stale:
            categories.append("EVIDENCE_STALE")
            detail["EVIDENCE_STALE"] = stale

        # C — candidate previously failed
        blocked: List[str] = []
        if self._capabilities is not None:
            atoms = self._capabilities.list_atoms_for_capability(capability_id)
            atom_ids = sorted({a.atom_id for a in atoms})
            for n in self._negative.active():
                if not n.retry_allowed and n.subject_id in atom_ids:
                    blocked.append(n.record_id)
            if blocked:
                categories.append("CANDIDATE_PREVIOUSLY_FAILED")
                detail["CANDIDATE_PREVIOUSLY_FAILED"] = blocked

            # D — revision changed (ADR-0007): candidate's claimed revision is
            # absent from the located repository's stored revisions
            revision_changed: List[str] = []
            if self._repositories is not None:
                for atom_id in atom_ids:
                    for cand in self._capabilities.list_candidates_for_atom(atom_id):
                        ref = cand.source_ref
                        if not ref.startswith("repo:"):
                            continue
                        repo_id = ref[len("repo:"):]
                        stored = {r.revision
                                  for r in self._repositories.list_revisions(repo_id)}
                        if stored and cand.revision not in stored:
                            revision_changed.append(cand.candidate_id)
            if revision_changed:
                categories.append("REVISION_CHANGED")
                detail["REVISION_CHANGED"] = sorted(set(revision_changed))

            # E — definition without implementation
            if atom_ids and not any(
                self._capabilities.list_candidates_for_atom(a) for a in atom_ids
            ):
                categories.append("DEFINITION_WITHOUT_IMPLEMENTATION")
                detail["DEFINITION_WITHOUT_IMPLEMENTATION"] = atom_ids
        else:
            atom_ids = []

        # F — no internal knowledge at all
        contracts_known = (
            self._capabilities.list_contract_versions(capability_id)
            if self._capabilities is not None else []
        )
        if not categories and not contracts_known:
            categories.append("NO_INTERNAL_KNOWLEDGE")
            detail["NO_INTERNAL_KNOWLEDGE"] = []

        return {"capability_id": capability_id, "categories": categories,
                "detail": detail}

    def _stale_evidence_ids(self) -> List[str]:
        rows = self._conn_freshness_rows()
        return [r for r in rows]

    def _conn_freshness_rows(self) -> List[str]:
        # Freshness log holds only non-current states as latest entries.
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
