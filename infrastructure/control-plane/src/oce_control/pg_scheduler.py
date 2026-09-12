"""PostgreSQL-persisted scheduler (B2-R4).

Closes audit gap 15 for the durable path: schedules live in the
`schedules` table; a restarting scheduler recovers its full state from
PostgreSQL (not from memory), reconciles next runs per the miss policy,
and fires due jobs through PgJobStore. Duplicate firing is prevented
per schedule with a PostgreSQL advisory lock (runtime-contract
`scheduler.duplicate_firing_prevention`).

The in-memory Scheduler remains the fast unit-test model; this is the
authoritative PostgreSQL path.
"""
from __future__ import annotations
import hashlib
import json
import struct
from datetime import datetime, timedelta
from typing import Optional

from .clocks import get_clock
from .hashes import generate_id
from .scheduler import Schedule
from .pg_store import PgJobStore


def advisory_lock_key(schedule_id: str) -> int:
    """Deterministic int64 advisory-lock key for a schedule (per schedule)."""
    digest = hashlib.sha256(schedule_id.encode("utf-8")).digest()[:8]
    return struct.unpack(">q", digest)[0]


def _to_dt(iso: Optional[str]):
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return None


def _fmt(dt) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


class PgScheduler:
    """PostgreSQL-persisted scheduler with restart recovery (B2-R4)."""

    def __init__(self, conn, job_store: PgJobStore):
        self._conn = conn
        self._job_store = job_store
        self._schedules: dict[str, Schedule] = {}
        self._submitted_ticks: set = set()
        self._missed_runs: list[dict] = []

    # -- persistence helpers -------------------------------------------------

    def _execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return cur.fetchall()
                return []
        except Exception:
            self._conn.rollback()
            raise

    @staticmethod
    def _row_to_schedule(row: tuple) -> Schedule:
        (schedule_id, job_type, payload, recurring, interval_seconds, scheduled_at,
         last_run_at, next_run_at, max_concurrent, miss_policy, paused, timezone,
         created_by, grant_id, created_at, submitting_actor, resource_scope,
         environment, priority) = row
        return Schedule(
            schedule_id=schedule_id,
            job_type=job_type,
            payload=payload or {},
            recurring=bool(recurring),
            interval_seconds=interval_seconds,
            scheduled_at=_fmt(scheduled_at),
            last_run_at=_fmt(last_run_at),
            next_run_at=_fmt(next_run_at),
            max_concurrent=max_concurrent,
            miss_policy=miss_policy,
            paused=bool(paused),
            timezone=timezone,
            created_by=created_by,
            grant_id=grant_id,
            submitting_actor=submitting_actor or created_by,
            resource_scope=resource_scope,
            environment=environment,
            priority=priority,
        )

    def _insert(self, sched: Schedule) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO schedules (schedule_id, job_type, payload,
                         recurring, interval_seconds, scheduled_at, last_run_at,
                         next_run_at, max_concurrent, miss_policy, paused,
                         timezone, created_by, grant_id, submitting_actor,
                         resource_scope, environment, priority)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (sched.schedule_id, sched.job_type, json.dumps(sched.payload),
                     sched.recurring, sched.interval_seconds,
                     _to_dt(sched.scheduled_at), _to_dt(sched.last_run_at),
                     _to_dt(sched.next_run_at), sched.max_concurrent,
                     sched.miss_policy, sched.paused, sched.timezone,
                     sched.created_by, sched.grant_id, sched.submitting_actor,
                     sched.resource_scope, sched.environment, sched.priority),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _update(self, sched: Schedule) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE schedules SET paused=%s, last_run_at=%s, next_run_at=%s "
                    "WHERE schedule_id=%s",
                    (sched.paused, _to_dt(sched.last_run_at),
                     _to_dt(sched.next_run_at), sched.schedule_id),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _delete(self, schedule_id: str) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM schedules WHERE schedule_id = %s", (schedule_id,))
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _try_lock(self, schedule_id: str) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_try_advisory_lock(%s)", (advisory_lock_key(schedule_id),))
                return bool(cur.fetchone()[0])
        except Exception:
            return False

    def _unlock(self, schedule_id: str) -> None:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_unlock(%s)", (advisory_lock_key(schedule_id),))
        except Exception:
            pass

    # -- creation ------------------------------------------------------------

    def create_immediate(self, *, job_type: str, payload: dict, grant_id: str,
                         submitting_actor: str, **kwargs) -> Schedule:
        clock = get_clock()
        now = clock.now()
        sched = Schedule(
            schedule_id=generate_id(),
            job_type=job_type,
            payload=payload,
            scheduled_at=now.isoformat(),
            recurring=False,
            grant_id=grant_id,
            submitting_actor=submitting_actor,
            created_by=submitting_actor,
            resource_scope=kwargs.get("resource_scope", "default"),
            environment=kwargs.get("environment", "local"),
            priority=kwargs.get("priority", "normal"),
            max_concurrent=kwargs.get("max_concurrent", 1),
            next_run_at=now.isoformat(),
        )
        self._insert(sched)
        self._schedules[sched.schedule_id] = sched
        return sched

    def create_delayed(self, *, job_type: str, payload: dict, grant_id: str,
                       submitting_actor: str, delay_seconds: int, **kwargs) -> Schedule:
        clock = get_clock()
        now = clock.now()
        run_at = now + timedelta(seconds=delay_seconds)
        sched = Schedule(
            schedule_id=generate_id(),
            job_type=job_type,
            payload=payload,
            scheduled_at=run_at.isoformat(),
            recurring=False,
            grant_id=grant_id,
            submitting_actor=submitting_actor,
            created_by=submitting_actor,
            resource_scope=kwargs.get("resource_scope", "default"),
            environment=kwargs.get("environment", "local"),
            priority=kwargs.get("priority", "normal"),
            max_concurrent=kwargs.get("max_concurrent", 1),
            next_run_at=run_at.isoformat(),
        )
        self._insert(sched)
        self._schedules[sched.schedule_id] = sched
        return sched

    def create_recurring(self, *, job_type: str, payload: dict, grant_id: str,
                         submitting_actor: str, interval_seconds: int, **kwargs) -> Schedule:
        clock = get_clock()
        now = clock.now()
        sched = Schedule(
            schedule_id=generate_id(),
            job_type=job_type,
            payload=payload,
            interval_seconds=interval_seconds,
            recurring=True,
            grant_id=grant_id,
            submitting_actor=submitting_actor,
            created_by=submitting_actor,
            resource_scope=kwargs.get("resource_scope", "default"),
            environment=kwargs.get("environment", "local"),
            priority=kwargs.get("priority", "normal"),
            max_concurrent=kwargs.get("max_concurrent", 1),
            miss_policy=kwargs.get("miss_policy", "run_once"),
            scheduled_at=now.isoformat(),
            next_run_at=now.isoformat(),
        )
        self._insert(sched)
        self._schedules[sched.schedule_id] = sched
        return sched

    # -- lifecycle -------------------------------------------------------------

    def tick(self) -> list:
        """Process due schedules. Returns submitted jobs."""
        clock = get_clock()
        now = clock.now()
        submitted = []
        running_counts = self._job_store.running_counts_by_type()

        for sched in self._schedules.values():
            if sched.paused:
                continue
            next_run = sched.next_run_at
            if next_run is None:
                continue
            next_dt = datetime.fromisoformat(next_run)
            if next_dt > now:
                continue
            if running_counts.get(sched.job_type, 0) >= sched.max_concurrent:
                continue
            dedup_key = f"{sched.schedule_id}:{next_run}"
            if dedup_key in self._submitted_ticks:
                continue
            # Duplicate firing prevention: one advisory lock per schedule.
            if not self._try_lock(sched.schedule_id):
                continue  # another scheduler instance is firing this schedule
            try:
                self._submitted_ticks.add(dedup_key)
                if sched.last_run_at:
                    last_dt = datetime.fromisoformat(sched.last_run_at)
                    if next_dt < last_dt:
                        if sched.miss_policy == "skip":
                            next_after = sched.compute_next_run(now)
                            sched.next_run_at = next_after.isoformat() if next_after else None
                            self._update(sched)
                            continue
                        elif sched.miss_policy == "fail":
                            self._missed_runs.append({
                                "schedule_id": sched.schedule_id,
                                "missed_at": next_run,
                                "detected_at": now.isoformat(),
                            })
                            next_after = sched.compute_next_run(now)
                            sched.next_run_at = next_after.isoformat() if next_after else None
                            self._update(sched)
                            continue
                job = self._job_store.submit_job(
                    job_type=sched.job_type,
                    submitting_actor=sched.submitting_actor,
                    grant_id=sched.grant_id,
                    payload=sched.payload,
                    resource_scope=sched.resource_scope,
                    environment=sched.environment,
                    priority=sched.priority,
                )
                submitted.append(job)
                sched.last_run_at = next_run
                next_after = sched.compute_next_run(now)
                sched.next_run_at = next_after.isoformat() if next_after else None
                self._update(sched)
            finally:
                self._unlock(sched.schedule_id)
        return submitted

    def pause(self, schedule_id: str) -> None:
        sched = self._schedules.get(schedule_id)
        if sched:
            sched.paused = True
            self._update(sched)

    def resume(self, schedule_id: str) -> None:
        sched = self._schedules.get(schedule_id)
        if sched:
            sched.paused = False
            clock = get_clock()
            now = clock.now()
            next_run = sched.compute_next_run(now)
            sched.next_run_at = next_run.isoformat() if next_run else None
            self._update(sched)

    def cancel(self, schedule_id: str) -> None:
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
        self._delete(schedule_id)

    # -- restart recovery (audit gap 15) ---------------------------------------

    def recover_after_restart(self) -> int:
        """Load all schedules from PostgreSQL and reconcile next runs.

        Returns the number of schedules whose next run was reconciled
        (missed-run detection / next-run recomputation).
        """
        clock = get_clock()
        now = clock.now()
        recovered = 0
        rows = self._execute("SELECT * FROM schedules")
        self._schedules = {}
        for row in rows:
            sched = self._row_to_schedule(row)
            self._schedules[sched.schedule_id] = sched
            if sched.paused or not sched.next_run_at:
                continue
            next_dt = datetime.fromisoformat(sched.next_run_at)
            if next_dt >= now:
                continue
            if sched.recurring:
                # Past-due recurring schedule: recompute next run per miss policy
                # so the next tick fires it exactly once.
                next_after = sched.compute_next_run(now)
                sched.next_run_at = next_after.isoformat() if next_after else None
                recovered += 1
                self._update(sched)
            else:
                # Past-due one-shot: record the miss; it will not fire again.
                self._missed_runs.append({
                    "schedule_id": sched.schedule_id,
                    "missed_at": sched.next_run_at,
                    "detected_at": now.isoformat(),
                })
                sched.next_run_at = None
                recovered += 1
                self._update(sched)
        return recovered

    @property
    def schedules(self) -> dict:
        return dict(self._schedules)

    @property
    def missed_runs(self) -> list:
        return list(self._missed_runs)
