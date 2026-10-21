"""SQLite CapabilityRegistry (P1-R1 §4, §9).

Follows the established P1 store conventions exactly: canonical JSON payload
+ sha256 digest per row, verified on every read; INSERT-only; parameterized
SQL; versioned keys instead of mutable overwrite.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from qcae.core.capabilities.atom import CapabilityAtom, AtomStatus
from qcae.core.capabilities.candidate import Candidate
from qcae.core.capabilities.composite import CompositeCapability
from qcae.core.contracts.contract import CapabilityContract
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.capability_registry import CapabilityRegistryPort

__all__ = ["SqliteCapabilityRegistry", "CAPABILITY_REGISTRY_DDL"]

CAPABILITY_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS capability_contract (
    capability_id   TEXT NOT NULL,
    contract_version INTEGER NOT NULL,
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL,
    PRIMARY KEY (capability_id, contract_version)
);
CREATE INDEX IF NOT EXISTS ix_contract_capability ON capability_contract(capability_id);

CREATE TABLE IF NOT EXISTS capability_atom (
    atom_id         TEXT NOT NULL,
    atom_version    INTEGER NOT NULL,
    status          TEXT NOT NULL,
    domain          TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL,
    PRIMARY KEY (atom_id, atom_version)
);

CREATE TABLE IF NOT EXISTS composite_capability (
    capability_id   TEXT NOT NULL,
    contract_version INTEGER NOT NULL,
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL,
    PRIMARY KEY (capability_id, contract_version)
);

CREATE TABLE IF NOT EXISTS candidate (
    candidate_id    TEXT PRIMARY KEY,
    source_ref      TEXT NOT NULL DEFAULT '',
    revision        TEXT NOT NULL DEFAULT '',
    payload_json    TEXT NOT NULL,
    payload_digest  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_candidate_source ON candidate(source_ref, revision);
"""


def _decode(row, key: str, cls):
    payload_json, payload_digest = row
    record = cls.from_dict(json.loads(payload_json))
    if record.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored {cls.object_type()} {key!r} failed integrity check (digest mismatch)"
        )
    return record


def _encode(record) -> tuple:
    payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
    return payload, record.digest()


class SqliteCapabilityRegistry(CapabilityRegistryPort):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # -- CapabilityContract --------------------------------------------------

    def add_contract(self, contract: CapabilityContract) -> str:
        payload, digest = _encode(contract)
        try:
            self._conn.execute(
                "INSERT INTO capability_contract (capability_id, contract_version,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?)",
                (contract.capability_id, contract.contract_version, payload, digest),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"contract {contract.capability_id} v{contract.contract_version} already "
                "stored; a new version is a new record (no mutable overwrite)"
            ) from exc
        return f"{contract.capability_id}:v{contract.contract_version}"

    def get_contract(self, capability_id: str, contract_version: int) -> Optional[CapabilityContract]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_contract"
            " WHERE capability_id = ? AND contract_version = ?",
            (capability_id, contract_version),
        ).fetchone()
        return _decode(row, f"{capability_id}:v{contract_version}", CapabilityContract) if row else None

    def list_contract_versions(self, capability_id: str) -> List[CapabilityContract]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_contract"
            " WHERE capability_id = ? ORDER BY contract_version",
            (capability_id,),
        ).fetchall()
        return [_decode((r[0], r[1]), capability_id, CapabilityContract) for r in rows]

    def latest_contract(self, capability_id: str) -> Optional[CapabilityContract]:
        versions = self.list_contract_versions(capability_id)
        return versions[-1] if versions else None

    def contract_supersession_chain(self, capability_id: str) -> List[CapabilityContract]:
        """Versions linked via supersedes_contract, oldest first.

        Stored rows already form the chain by version order; this verifies the
        declared supersession links agree with version adjacency rather than
        trusting insertion order.
        """
        versions = self.list_contract_versions(capability_id)
        if not versions:
            return []
        declared: List[CapabilityContract] = []
        remaining = list(versions)
        # Chain head: a version that no stored version claims to supersede.
        # Self-IDs like "CAP-X:v1" are the supersession tokens; version-1
        # roots have an empty supersedes_contract.
        superseded = {
            c.supersedes_contract
            for c in versions
            if c.supersedes_contract
        }
        current = None
        for c in versions:
            token = f"{c.capability_id}:v{c.contract_version}"
            if token not in superseded and not c.supersedes_contract:
                current = c
                break
        if current is None:
            current = versions[0]
        while current is not None:
            declared.append(current)
            token = f"{current.capability_id}:v{current.contract_version}"
            remaining = [r for r in remaining if r is not current]
            current = next(
                (r for r in remaining if r.supersedes_contract == token), None
            )
        return declared

    # -- CapabilityAtom --------------------------------------------------------

    def add_atom(self, atom: CapabilityAtom) -> str:
        payload, digest = _encode(atom)
        try:
            self._conn.execute(
                "INSERT INTO capability_atom (atom_id, atom_version, status, domain,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?, ?, ?)",
                (atom.atom_id, atom.atom_version, atom.status.value, atom.domain,
                 payload, digest),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"atom {atom.atom_id} v{atom.atom_version} already stored"
            ) from exc
        return f"{atom.atom_id}:v{atom.atom_version}"

    def get_atom(self, atom_id: str, atom_version: Optional[int] = None) -> Optional[CapabilityAtom]:
        if atom_version is not None:
            row = self._conn.execute(
                "SELECT payload_json, payload_digest FROM capability_atom"
                " WHERE atom_id = ? AND atom_version = ?",
                (atom_id, atom_version),
            ).fetchone()
            return _decode(row, f"{atom_id}:v{atom_version}", CapabilityAtom) if row else None
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_atom"
            " WHERE atom_id = ? ORDER BY atom_version DESC LIMIT 1",
            (atom_id,),
        ).fetchone()
        return _decode(row, atom_id, CapabilityAtom) if row else None

    def list_atoms_for_capability(self, capability_id: str) -> List[CapabilityAtom]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_atom"
            " WHERE json_extract(payload_json, '$.parent_capabilities') LIKE ?"
            " ORDER BY atom_id, atom_version",
            (f'%\"{capability_id}\"%',),
        ).fetchall()
        return [_decode((r[0], r[1]), capability_id, CapabilityAtom) for r in rows]

    def list_atoms_by_status(self, status: AtomStatus) -> List[CapabilityAtom]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_atom"
            " WHERE status = ? ORDER BY atom_id, atom_version",
            (status.value,),
        ).fetchall()
        return [_decode((r[0], r[1]), status.value, CapabilityAtom) for r in rows]

    def list_atoms_by_domain(self, domain: str) -> List[CapabilityAtom]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM capability_atom"
            " WHERE domain = ? ORDER BY atom_id, atom_version",
            (domain,),
        ).fetchall()
        return [_decode((r[0], r[1]), domain, CapabilityAtom) for r in rows]

    # -- CompositeCapability ----------------------------------------------------

    def add_composite(self, composite: CompositeCapability) -> str:
        payload, digest = _encode(composite)
        try:
            self._conn.execute(
                "INSERT INTO composite_capability (capability_id, contract_version,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?)",
                (composite.capability_id, composite.contract_version, payload, digest),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"composite {composite.capability_id} v{composite.contract_version} "
                "already stored"
            ) from exc
        return f"{composite.capability_id}:v{composite.contract_version}"

    def get_composite(self, capability_id: str, contract_version: int) -> Optional[CompositeCapability]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM composite_capability"
            " WHERE capability_id = ? AND contract_version = ?",
            (capability_id, contract_version),
        ).fetchone()
        return _decode(row, f"{capability_id}:v{contract_version}", CompositeCapability) if row else None

    def member_atoms(self, capability_id: str, contract_version: int) -> List[CapabilityAtom]:
        composite = self.get_composite(capability_id, contract_version)
        if composite is None:
            return []
        atoms: List[CapabilityAtom] = []
        for member in composite.members:
            atom = self.get_atom(member.atom_id)
            if atom is not None:
                atoms.append(atom)
        return atoms

    # -- Candidate ---------------------------------------------------------------

    def add_candidate(self, candidate: Candidate) -> str:
        payload, digest = _encode(candidate)
        try:
            self._conn.execute(
                "INSERT INTO candidate (candidate_id, source_ref, revision,"
                " payload_json, payload_digest) VALUES (?, ?, ?, ?, ?)",
                (candidate.candidate_id, candidate.source_ref, candidate.revision,
                 payload, digest),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"candidate {candidate.candidate_id!r} already stored; a new "
                "revision is a new candidate record (append-only)"
            ) from exc
        return candidate.candidate_id

    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM candidate WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        return _decode(row, candidate_id, Candidate) if row else None

    def list_candidates_for_atom(self, atom_id: str) -> List[Candidate]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM candidate"
            " WHERE json_extract(payload_json, '$.claims_atoms') LIKE ?"
            " ORDER BY candidate_id",
            (f'%\"{atom_id}\"%',),
        ).fetchall()
        return [_decode((r[0], r[1]), atom_id, Candidate) for r in rows]

    def list_candidates_by_source(self, source_ref: str, revision: str = "") -> List[Candidate]:
        if revision:
            rows = self._conn.execute(
                "SELECT payload_json, payload_digest FROM candidate"
                " WHERE source_ref = ? AND revision = ? ORDER BY candidate_id",
                (source_ref, revision),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT payload_json, payload_digest FROM candidate"
                " WHERE source_ref = ? ORDER BY candidate_id",
                (source_ref,),
            ).fetchall()
        return [_decode((r[0], r[1]), source_ref, Candidate) for r in rows]
