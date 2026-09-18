"""SQLite runtime store for jobs, steps, events, checkpoints (P2-C02).

Follows the established P1 store conventions exactly: canonical JSON payload
+ sha256 digest per row, verified on every read; parameterized SQL;
INSERT-only factual tables (job status/steps carry operational state that the
canon permits to be mutable; the event log is the append-oriented historical
truth — Book V 12.1, P2 directive §8/§9).

DDL is applied by ``RUNTIME_DDL``; tables are additive in schema v4
(P2-C12 wires the migration).
"""

from __future__ import annotations

import json
import secrets
import sqlite3
from typing import Dict, List, Optional, Tuple

import hashlib
from dataclasses import replace as dataclasses_replace

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import canonical_json_bytes


def _digest_of_payload(payload_json: str) -> str:
    """sha256 over the exact stored payload bytes (no re-encoding drift)."""
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
from qcae.orchestration.jobs.runtime import (
    JobEvent,
    JobEventType,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
)
from qcae.orchestration.orchestrator.execution import (
    ExecutionRecord,
    ExecutionState,
    ReplaySafety,
)

__all__ = [
    "SqliteRuntimeStore",
    "RuntimeTransaction",
    "RUNTIME_DDL",
    "RUNTIME_TABLES",
]


def _encode(record) -> Tuple[str, str]:
    payload = json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True)
    return payload, record.digest()


def _decode(row, key: str, cls):
    payload_json, payload_digest = row
    record = cls.from_dict(json.loads(payload_json))
    if record.digest() != payload_digest:
        raise QcaeValidationError(
            f"stored {cls.object_type()} {key!r} failed integrity check (digest mismatch)"
        )
    return record


RUNTIME_DDL = """
CREATE TABLE IF NOT EXISTS runtime_job (
    job_id            TEXT PRIMARY KEY,
    deterministic_id  TEXT NOT NULL,
    status            TEXT NOT NULL,
    job_type          TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    priority          INTEGER NOT NULL DEFAULT 0,
    queued_at         TEXT NOT NULL DEFAULT '',
    not_before        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_runtime_job_status ON runtime_job(status);
CREATE INDEX IF NOT EXISTS ix_runtime_job_queue ON runtime_job(not_before, priority DESC);

CREATE TABLE IF NOT EXISTS runtime_step (
    step_id           TEXT NOT NULL,
    job_id            TEXT NOT NULL,
    status            TEXT NOT NULL,
    step_type         TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    lease_owner       TEXT NOT NULL DEFAULT '',
    lease_token       TEXT NOT NULL DEFAULT '',
    lease_expires_at  TEXT NOT NULL DEFAULT '',
    not_before        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (step_id)
);
CREATE INDEX IF NOT EXISTS ix_runtime_step_job ON runtime_step(job_id);
CREATE INDEX IF NOT EXISTS ix_runtime_step_status ON runtime_step(status);

CREATE TABLE IF NOT EXISTS runtime_job_event (
    event_seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id          TEXT NOT NULL,
    event_type        TEXT NOT NULL,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL DEFAULT '',
    occurred_at       TEXT NOT NULL,
    actor             TEXT NOT NULL DEFAULT '',
    payload_json      TEXT NOT NULL DEFAULT '',
    event_digest      TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_runtime_event_id ON runtime_job_event(event_id);
CREATE INDEX IF NOT EXISTS ix_runtime_event_job ON runtime_job_event(job_id);

CREATE TABLE IF NOT EXISTS runtime_checkpoint (
    checkpoint_id     TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL DEFAULT '',
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL,
    created_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_checkpoint_job ON runtime_checkpoint(job_id);CREATE TABLE IF NOT EXISTS runtime_idempotency (
    idempotency_key   TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL,
    completed_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_execution (
    idempotency_key   TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    step_id           TEXT NOT NULL,
    state             TEXT NOT NULL,
    replay_safety     TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    payload_digest    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_runtime_execution_job ON runtime_execution(job_id);
"""

RUNTIME_TABLES = (
    "runtime_job",
    "runtime_step",
    "runtime_job_event",
    "runtime_checkpoint",
    "runtime_idempotency",
    "runtime_execution",
)


class RuntimeTransaction:
    """Unit-of-work view over one SQLite transaction (P2-C07R3, §2.3).

    Exposes only the write operations a multi-record commit needs, all on
    the SAME connection, so the group either commits together or not at all.
    """

    def __init__(self, store: "SqliteRuntimeStore") -> None:
        self._store = store

    def add_job(self, job, *, queued_at: str = "", not_before: str = "") -> None:
        self._store.add_job(job, queued_at=queued_at, not_before=not_before)

    def add_step(self, step, *, not_before: str = "") -> None:
        self._store.add_step(step, not_before=not_before)

    def append_event(self, event, payload_json: str = "") -> int:
        return self._store.append_event(event, payload_json=payload_json)


class SqliteRuntimeStore:
    """Durable job/step/event/checkpoint persistence (P2 directive §8)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def transaction(self) -> "RuntimeTransaction":
        """Context manager: all writes inside commit together or not at all.

        Real transaction semantics (BEGIN IMMEDIATE ... COMMIT/ROLLBACK) on
        the store's connection — never fake ones (directive §2.3).
        """
        return _StoreTransaction(self)

    def flush(self) -> None:
        """Make every prior write durable at a semantic boundary (P2-R4-C01).

        This is NOT a global autocommit switch (directive §3 forbids solving
        crash durability by silently changing connection semantics): the
        multi-row atomicity groups still use ``transaction()``. ``flush()``
        is the explicit durability law between phases of one logical
        operation — the engine calls it at the pre-effect boundary (lease /
        RUNNING / attempt / authority admission / idempotency reservation /
        EXECUTING) so an abrupt process death leaves exactly that truth
        recoverable, and again at the post-effect boundary after the worker
        has returned. Crash windows A-I (directive §4) are closed by the
        existence of these two commit points, proven by the process-kill
        acceptance harness (test_p2_process_crash.py).
        """
        self._conn.commit()

    # -- RuntimeJob ----------------------------------------------------------

    def add_job(self, job: RuntimeJob, *, queued_at: str = "", not_before: str = "") -> None:
        payload, digest = _encode(job)
        try:
            self._conn.execute(
                "INSERT INTO runtime_job (job_id, deterministic_id, status, job_type,"
                " payload_json, payload_digest, priority, queued_at, not_before)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job.job_id,
                    job.deterministic_id,
                    job.status.value,
                    job.job_type,
                    payload,
                    digest,
                    job.priority,
                    queued_at,
                    not_before,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"job {job.job_id!r} already exists (duplicate canonical identity)"
            ) from exc

    def get_job(self, job_id: str) -> Optional[RuntimeJob]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_job WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        return _decode(row, job_id, RuntimeJob) if row else None

    def update_job(self, job: RuntimeJob) -> None:
        """Replace the operational row; the event log preserves history."""
        payload, digest = _encode(job)
        cur = self._conn.execute(
            "UPDATE runtime_job SET status = ?, payload_json = ?, payload_digest = ?,"
            " priority = ? WHERE job_id = ?",
            (job.status.value, payload, digest, job.priority, job.job_id),
        )
        if cur.rowcount != 1:
            raise QcaeValidationError(f"job {job.job_id!r} not found")

    def list_jobs(self, *, status: Optional[RuntimeJobStatus] = None) -> List[RuntimeJob]:
        if status is not None:
            rows = self._conn.execute(
                "SELECT payload_json, payload_digest FROM runtime_job"
                " WHERE status = ? ORDER BY job_id",
                (status.value,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT payload_json, payload_digest FROM runtime_job ORDER BY job_id"
            ).fetchall()
        return [_decode((r[0], r[1]), "job", RuntimeJob) for r in rows]

    def deterministic_id_exists(self, deterministic_id: str) -> bool:
        return (
            self._conn.execute(
                "SELECT 1 FROM runtime_job WHERE deterministic_id = ? LIMIT 1",
                (deterministic_id,),
            ).fetchone()
            is not None
        )

    # -- RuntimeStep ---------------------------------------------------------

    def add_step(self, step: RuntimeStep, *, not_before: str = "") -> None:
        payload, digest = _encode(step)
        try:
            self._conn.execute(
                "INSERT INTO runtime_step (step_id, job_id, status, step_type,"
                " payload_json, payload_digest, lease_owner, lease_token,"
                " lease_expires_at, not_before)"
                " VALUES (?, ?, ?, ?, ?, ?, '', '', '', ?)",
                (
                    step.step_id,
                    step.job_id,
                    step.status.value,
                    step.step_type,
                    payload,
                    digest,
                    not_before,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"step {step.step_id!r} already exists (duplicate canonical identity)"
            ) from exc

    def get_step(self, step_id: str) -> Optional[RuntimeStep]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_step WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        return _decode(row, step_id, RuntimeStep) if row else None

    def update_step(self, step: RuntimeStep, *, lease_owner: str = "",
                    lease_token: str = "", lease_expires_at: str = "",
                    not_before: str = "") -> None:
        payload, digest = _encode(step)
        cur = self._conn.execute(
            "UPDATE runtime_step SET status = ?, payload_json = ?, payload_digest = ?,"
            " lease_owner = ?, lease_token = ?, lease_expires_at = ?, not_before = ?"
            " WHERE step_id = ?",
            (
                step.status.value,
                payload,
                digest,
                lease_owner,
                lease_token,
                lease_expires_at,
                not_before,
                step.step_id,
            ),
        )
        if cur.rowcount != 1:
            raise QcaeValidationError(f"step {step.step_id!r} not found")

    def list_steps_for_job(self, job_id: str) -> List[RuntimeStep]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_step"
            " WHERE job_id = ? ORDER BY step_id",
            (job_id,),
        ).fetchall()
        return [_decode((r[0], r[1]), "step", RuntimeStep) for r in rows]

    def steps_in_status(self, status: RuntimeStepStatus) -> List[RuntimeStep]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_step"
            " WHERE status = ? ORDER BY step_id",
            (status.value,),
        ).fetchall()
        return [_decode((r[0], r[1]), "step", RuntimeStep) for r in rows]

    def read_lease_columns(self, step_id: str) -> Optional[Dict[str, str]]:
        row = self._conn.execute(
            "SELECT lease_owner, lease_token, lease_expires_at, not_before"
            " FROM runtime_step WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "lease_owner": row[0],
            "lease_token": row[1],
            "lease_expires_at": row[2],
            "not_before": row[3],
        }

    # -- Job events (append-only) -------------------------------------------

    def append_event(self, event: JobEvent, payload_json: str = "") -> int:
        """Append one runtime fact; the STORE owns identity allocation.

        P2-C07R4 (repair directive §2.4): both the durable monotonic
        ``event_seq`` and the collision-safe ``event_id`` are allocated here,
        from durable state inside the same write — never from row counts held
        by callers. Callers pass ``event_seq=0``; ``event_id`` may be empty,
        in which case a unique ``ev-<seq>-<token>`` id is assigned. Explicit
        non-empty caller ids are honored (unique-index guarded).
        The stored seq is returned and is canonical.
        """
        if event.event_seq != 0:
            raise QcaeValidationError(
                "event_seq is store-assigned; pass 0 and treat the return "
                "value as canonical"
            )
        row = self._conn.execute(
            "SELECT COALESCE(MAX(event_seq), 0) + 1 FROM runtime_job_event"
        ).fetchone()
        seq = int(row[0])
        event_id = event.event_id or f"ev-{seq:08d}-{secrets.token_hex(6)}"
        event = dataclasses_replace(event, event_seq=seq, event_id=event_id)
        event_digest = hashlib.sha256(
            canonical_json_bytes(event.to_dict())
        ).hexdigest()
        try:
            self._conn.execute(
                "INSERT INTO runtime_job_event (event_seq, event_id, event_type, job_id,"
                " step_id, occurred_at, actor, payload_json, event_digest)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    seq,
                    event.event_id,
                    event.event_type.value,
                    event.job_id,
                    event.step_id,
                    event.occurred_at,
                    event.actor,
                    payload_json,
                    event_digest,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise QcaeValidationError(
                f"duplicate event_id {event.event_id!r} (event identity collision)"
            ) from exc
        return seq

    def event_digest_of(self, event_id: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT event_digest FROM runtime_job_event WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return row[0] if row else None

    def events_for_job(self, job_id: str) -> List[Tuple[int, JobEvent, str]]:
        rows = self._conn.execute(
            "SELECT event_seq, event_id, event_type, job_id, step_id, occurred_at,"
            " actor, payload_json, event_digest FROM runtime_job_event"
            " WHERE job_id = ? ORDER BY event_seq",
            (job_id,),
        ).fetchall()
        events: List[Tuple[int, JobEvent, str]] = []
        for r in rows:
            event = JobEvent(
                event_seq=int(r[0]),
                event_id=r[1],
                event_type=JobEventType(r[2]),
                job_id=r[3],
                step_id=r[4],
                occurred_at=r[5],
                actor=r[6],
            )
            event_digest = hashlib.sha256(
                canonical_json_bytes(event.to_dict())
            ).hexdigest()
            if event_digest != r[8]:
                raise QcaeValidationError(
                    f"stored event {r[1]!r} failed integrity check (digest mismatch)"
                )
            events.append((int(r[0]), event, r[7]))
        return events

    # -- Checkpoints ---------------------------------------------------------

    def allocate_checkpoint_id(self, job_id: str) -> str:
        """Store-side durable checkpoint identity (P2-C07R4, §2.4).

        Sequence derived from the durable per-job high-water mark at write
        time; uniqueness guarded by the checkpoint primary key, so a retry
        after a torn write cannot collide with a stored row.
        """
        row = self._conn.execute(
            "SELECT COUNT(*) FROM runtime_checkpoint WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        seq = int(row[0]) + 1
        while True:
            candidate = f"cp-{job_id}-{seq:06d}"
            exists = self._conn.execute(
                "SELECT 1 FROM runtime_checkpoint WHERE checkpoint_id = ?",
                (candidate,),
            ).fetchone()
            if not exists:
                return candidate
            seq += 1

    def put_checkpoint(
        self, checkpoint_id: str, job_id: str, step_id: str, data: dict, created_at: str
    ) -> None:
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
        digest = _digest_of_payload(payload)
        self._conn.execute(
            "INSERT INTO runtime_checkpoint (checkpoint_id, job_id, step_id,"
            " payload_json, payload_digest, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (checkpoint_id, job_id, step_id, payload, digest, created_at),
        )

    def get_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_checkpoint"
            " WHERE checkpoint_id = ?",
            (checkpoint_id,),
        ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        if _digest_of_payload(row[0]) != row[1]:
            raise QcaeValidationError(
                f"stored checkpoint {checkpoint_id!r} failed integrity check"
            )
        return data

    def latest_checkpoint_for_job(self, job_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_checkpoint"
            " WHERE job_id = ? ORDER BY created_at DESC, checkpoint_id DESC LIMIT 1",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        if _digest_of_payload(row[0]) != row[1]:
            raise QcaeValidationError(
                f"stored checkpoint for job {job_id!r} failed integrity check"
            )
        return data

    # -- Idempotency / execution records (P2-C07R2) --------------------------

    def reserve_execution(
        self,
        idempotency_key: str,
        job_id: str,
        step_id: str,
        replay_safety: ReplaySafety,
        reserved_at: str,
    ) -> bool:
        """Durably reserve a key BEFORE execution; False if already reserved.

        Deterministic: the first reservation for a key wins; every later
        reservation of the same key is refused (the boundary for dedup).
        """
        record = ExecutionRecord(
            idempotency_key=idempotency_key,
            job_id=job_id,
            step_id=step_id,
            state=ExecutionState.RESERVED,
            replay_safety=replay_safety,
            reserved_at=reserved_at,
        )
        record.validate()
        payload, digest = _encode(record)
        try:
            self._conn.execute(
                "INSERT INTO runtime_execution (idempotency_key, job_id, step_id,"
                " state, replay_safety, payload_json, payload_digest)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    idempotency_key,
                    job_id,
                    step_id,
                    ExecutionState.RESERVED.value,
                    replay_safety.value,
                    payload,
                    digest,
                ),
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_execution_record(self, idempotency_key: str) -> Optional[ExecutionRecord]:
        row = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_execution"
            " WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        return _decode(row, idempotency_key, ExecutionRecord) if row else None

    def update_execution_record(self, record: ExecutionRecord) -> None:
        """Advance an execution record along its explicit state machine."""
        record.validate()
        current = self.get_execution_record(record.idempotency_key)
        if current is None:
            raise QcaeValidationError(
                f"execution record {record.idempotency_key!r} does not exist"
            )
        if current.state is not record.state:
            from qcae.orchestration.orchestrator.execution import (
                assert_execution_transition,
            )

            assert_execution_transition(current.state, record.state)
        payload, digest = _encode(record)
        cur = self._conn.execute(
            "UPDATE runtime_execution SET state = ?, payload_json = ?,"
            " payload_digest = ? WHERE idempotency_key = ?",
            (record.state.value, payload, digest, record.idempotency_key),
        )
        if cur.rowcount != 1:
            raise QcaeValidationError(
                f"execution record {record.idempotency_key!r} vanished"
            )

    def list_execution_records_for_job(self, job_id: str) -> List[ExecutionRecord]:
        rows = self._conn.execute(
            "SELECT payload_json, payload_digest FROM runtime_execution"
            " WHERE job_id = ? ORDER BY idempotency_key",
            (job_id,),
        ).fetchall()
        return [_decode((r[0], r[1]), "execution", ExecutionRecord) for r in rows]

    def commit_execution(
        self,
        idempotency_key: str,
        result,
        completed_at: str,
    ) -> bool:
        """COMMITTED stores the durable result for crash-window reconstruction.

        Returns False (without effect) if the key was never reserved or is
        already COMMITTED — commit is only legal from RESERVED/EXECUTING.
        """
        current = self.get_execution_record(idempotency_key)
        if current is None:
            return False
        if current.state is ExecutionState.COMMITTED:
            return False
        from qcae.core.serialization import canonical_json_bytes

        result_json = canonical_json_bytes(result.to_dict()).decode("utf-8")
        record = dataclasses_replace(
            current,
            state=ExecutionState.COMMITTED,
            completed_at=completed_at,
            result_json=result_json,
        )
        self.update_execution_record(record)
        return True

    def unresolved_executions_for_job(self, job_id: str) -> List[ExecutionRecord]:
        """Execution records left ambiguous by a crash (RESERVED/EXECUTING)."""
        return [
            r
            for r in self.list_execution_records_for_job(job_id)
            if r.state in (ExecutionState.RESERVED, ExecutionState.EXECUTING)
        ]

    # -- Legacy completion-marker API (back-compat; backed by runtime_idempotency)

    def record_idempotent_completion(
        self, idempotency_key: str, job_id: str, step_id: str, completed_at: str
    ) -> bool:
        """Record a completion; False if the key already exists."""
        try:
            self._conn.execute(
                "INSERT INTO runtime_idempotency (idempotency_key, job_id, step_id,"
                " completed_at) VALUES (?, ?, ?, ?)",
                (idempotency_key, job_id, step_id, completed_at),
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def idempotency_key_used(self, idempotency_key: str) -> bool:
        return (
            self._conn.execute(
                "SELECT 1 FROM runtime_idempotency WHERE idempotency_key = ? LIMIT 1",
                (idempotency_key,),
            ).fetchone()
            is not None
        )


class _StoreTransaction:
    """Explicit BEGIN IMMEDIATE / COMMIT / ROLLBACK around a write group.

    Used by ``SqliteRuntimeStore.transaction()`` so multi-record writes
    (job + steps + initial events) either commit together or not at all
    (P2-C07R3, repair directive §2.3).
    """

    def __init__(self, store: SqliteRuntimeStore) -> None:
        self._store = store
        self._conn = store._conn

    def __enter__(self) -> RuntimeTransaction:
        # A prior DDL executescript / legacy-mode implicit txn can leave the
        # connection inside a transaction on entry. That open txn holds no
        # intended work here (the runtime store has no autocommit writes), so
        # end it explicitly before taking the write lock — otherwise SQLite
        # rejects the nested BEGIN (budget-suite fixtures hit this).
        if self._conn.in_transaction:
            self._conn.commit()
        self._conn.execute("BEGIN IMMEDIATE")
        return RuntimeTransaction(self._store)

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self._conn.execute("COMMIT")
        else:
            self._conn.execute("ROLLBACK")
        return False  # never swallow failures
