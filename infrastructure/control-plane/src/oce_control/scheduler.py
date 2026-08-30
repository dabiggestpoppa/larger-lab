"""Scheduler for OCE control plane.

B3.C3 / B2-C3 — immediate, delayed, scheduled, recurring jobs;
deterministic next-run; missed-run policy; concurrency limits;
pause/resume/cancellation; time-zone correctness; restart recovery;
duplicate prevention.

Uses test-controlled clocks. No wall-clock sleeps in authoritative tests.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
import hashlib

from .clocks import get_clock
from .hashes import generate_id, payload_hash
from .job_store import JobStore


@dataclass
class Schedule:
    schedule_id: str
    job_type: str
    payload: dict
    cron: Optional[str] = None  # simplified cron for recurring
    interval_seconds: Optional[int] = None  # for interval-based recurring
    scheduled_at: Optional[str] = None  # for one-shot delayed
    recurring: bool = False
    paused: bool = False
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    max_concurrent: int = 1
    miss_policy: str = "run_once"  # run_once, skip, fail
    timezone: str = "UTC"
    created_by: str = ""
    grant_id: str = ""
    submitting_actor: str = ""
    resource_scope: str = "default"
    environment: str = "local"
    priority: str = "normal"

    def compute_next_run(self, after: datetime) -> Optional[datetime]:
        """Deterministic next-run calculation."""
        if self.paused:
            return None
        if self.scheduled_at and not self.recurring:
            # One-shot: no next run after it fires
            scheduled = datetime.fromisoformat(self.scheduled_at)
            if scheduled > after:
                return scheduled
            return None
        if self.interval_seconds and self.recurring:
            base = self.last_run_at or self.scheduled_at
            if base:
                base_dt = datetime.fromisoformat(base)
            else:
                base_dt = after
            next_run = base_dt + timedelta(seconds=self.interval_seconds)
            while next_run <= after:
                next_run += timedelta(seconds=self.interval_seconds)
            return next_run
        return None


class Scheduler:
    """Scheduler with deterministic next-run, concurrency, and recovery."""

    def __init__(self, job_store: JobStore):
        self._job_store = job_store
        self._schedules: dict[str, Schedule] = {}
        self._running_counts: dict[str, int] = {}  # job_type -> running count
        self._missed_runs: list[dict] = []

    def create_immediate(self, *, job_type: str, payload: dict, grant_id: str,
                         submitting_actor: str, **kwargs) -> Schedule:
        """Create an immediate job schedule."""
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
            resource_scope=kwargs.get("resource_scope", "default"),
            environment=kwargs.get("environment", "local"),
            priority=kwargs.get("priority", "normal"),
            max_concurrent=kwargs.get("max_concurrent", 1),
            next_run_at=now.isoformat(),
        )
        self._schedules[sched.schedule_id] = sched
        return sched

    def create_delayed(self, *, job_type: str, payload: dict, grant_id: str,
                       submitting_actor: str, delay_seconds: int, **kwargs) -> Schedule:
        """Create a delayed job schedule."""
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
            resource_scope=kwargs.get("resource_scope", "default"),
            environment=kwargs.get("environment", "local"),
            priority=kwargs.get("priority", "normal"),
            max_concurrent=kwargs.get("max_concurrent", 1),
            next_run_at=run_at.isoformat(),
        )
        self._schedules[sched.schedule_id] = sched
        return sched

    def create_recurring(self, *, job_type: str, payload: dict, grant_id: str,
                         submitting_actor: str, interval_seconds: int, **kwargs) -> Schedule:
        """Create a recurring job schedule (requires authorization)."""
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
            resource_scope=kwargs.get("resource_scope", "default"),
            environment=kwargs.get("environment", "local"),
            priority=kwargs.get("priority", "normal"),
            max_concurrent=kwargs.get("max_concurrent", 1),
            miss_policy=kwargs.get("miss_policy", "run_once"),
            scheduled_at=now.isoformat(),
            next_run_at=now.isoformat(),
        )
        self._schedules[sched.schedule_id] = sched
        return sched

    def tick(self) -> list:
        """Process due schedules. Returns submitted jobs."""
        clock = get_clock()
        now = clock.now()
        submitted = []

        for sched in self._schedules.values():
            if sched.paused:
                continue

            next_run = sched.next_run_at
            if next_run is None:
                continue

            next_dt = datetime.fromisoformat(next_run)
            if next_dt > now:
                continue

            # Check concurrency limit
            running = self._running_counts.get(sched.job_type, 0)
            if running >= sched.max_concurrent:
                continue

            # Check for duplicate (prevent double submission in same tick)
            dedup_key = f"{sched.schedule_id}:{next_run}"
            if hasattr(self, '_submitted_ticks') and dedup_key in self._submitted_ticks:
                continue

            if not hasattr(self, '_submitted_ticks'):
                self._submitted_ticks = set()
            self._submitted_ticks.add(dedup_key)

            # Check missed run policy
            if sched.last_run_at:
                last_dt = datetime.fromisoformat(sched.last_run_at)
                if next_dt < last_dt:
                    # Missed run
                    if sched.miss_policy == "skip":
                        sched.next_run_at = sched.compute_next_run(now).isoformat() if sched.compute_next_run(now) else None
                        continue
                    elif sched.miss_policy == "fail":
                        self._missed_runs.append({
                            "schedule_id": sched.schedule_id,
                            "missed_at": next_run,
                            "detected_at": now.isoformat(),
                        })
                        sched.next_run_at = sched.compute_next_run(now).isoformat() if sched.compute_next_run(now) else None
                        continue

            # Submit the job
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

            # Update schedule
            sched.last_run_at = next_run
            next_after = sched.compute_next_run(now)
            sched.next_run_at = next_after.isoformat() if next_after else None

        return submitted

    def pause(self, schedule_id: str) -> None:
        sched = self._schedules.get(schedule_id)
        if sched:
            sched.paused = True

    def resume(self, schedule_id: str) -> None:
        sched = self._schedules.get(schedule_id)
        if sched:
            sched.paused = False
            clock = get_clock()
            now = clock.now()
            next_run = sched.compute_next_run(now)
            sched.next_run_at = next_run.isoformat() if next_run else None

    def cancel(self, schedule_id: str) -> None:
        self._schedules.pop(schedule_id, None)

    def recover_after_restart(self) -> int:
        """Recover schedules after a restart. Recompute next runs."""
        clock = get_clock()
        now = clock.now()
        recovered = 0
        for sched in self._schedules.values():
            if sched.paused:
                continue
            if sched.next_run_at:
                next_dt = datetime.fromisoformat(sched.next_run_at)
                if next_dt < now and sched.recurring:
                    if sched.miss_policy == "run_once":
                        next_run = sched.compute_next_run(now)
                        sched.next_run_at = next_run.isoformat() if next_run else None
                        recovered += 1
                    elif sched.miss_policy == "skip":
                        next_run = sched.compute_next_run(now)
                        sched.next_run_at = next_run.isoformat() if next_run else None
                        recovered += 1
                elif next_dt < now and not sched.recurring:
                    self._missed_runs.append({
                        "schedule_id": sched.schedule_id,
                        "missed_at": sched.next_run_at,
                        "detected_at": now.isoformat(),
                    })
                    sched.next_run_at = None
                    recovered += 1
        return recovered

    @property
    def schedules(self) -> dict:
        return dict(self._schedules)

    @property
    def missed_runs(self) -> list:
        return list(self._missed_runs)
