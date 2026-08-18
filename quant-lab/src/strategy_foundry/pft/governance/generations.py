"""Immutable run records and the run registry.

Completed runs are never deleted or edited. A repaired implementation
becomes a new generation with a parent link. Bugged runs are invalidated,
not erased.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .identity import ExperimentFingerprint

RUN_STATUSES = {"COMPLETED", "INVALIDATED", "SUPERSEDED"}


class RunRegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunRecord:
    """One immutable run record."""

    run_id: str
    experiment_id: str
    fingerprint: ExperimentFingerprint
    status: str
    created_at: str
    parent_run_id: Optional[str] = None
    reason: str = ""
    files_changed: list = field(default_factory=list)
    defect_class: str = ""

    def __post_init__(self) -> None:
        if self.status not in RUN_STATUSES:
            raise RunRegistryError(f"invalid run status {self.status!r}")
        if not self.run_id or not self.experiment_id:
            raise RunRegistryError("run_id and experiment_id are required")

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "fingerprint_hex": self.fingerprint.fingerprint_hex(),
            "status": self.status,
            "created_at": self.created_at,
            "parent_run_id": self.parent_run_id,
            "reason": self.reason,
            "files_changed": list(self.files_changed),
            "defect_class": self.defect_class,
        }

    def with_status(self, status: str, reason: str = "", defect_class: str = "") -> "RunRecord":
        """Return a NEW record with an updated status. The original is untouched."""
        return RunRecord(
            run_id=self.run_id,
            experiment_id=self.experiment_id,
            fingerprint=self.fingerprint,
            status=status,
            created_at=self.created_at,
            parent_run_id=self.parent_run_id,
            reason=reason,
            files_changed=list(self.files_changed),
            defect_class=defect_class,
        )


class RunRegistry:
    """Append-only registry of immutable run records (JSONL)."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, RunRecord] = {}
        if self._path.exists():
            for line in self._path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                rec = RunRecord(
                    run_id=data["run_id"],
                    experiment_id=data["experiment_id"],
                    fingerprint=ExperimentFingerprint(
                        spec_gen=data["fingerprint"]["spec_gen"],
                        data_gen=data["fingerprint"]["data_gen"],
                        engine_gen=data["fingerprint"]["engine_gen"],
                        cost_gen=data["fingerprint"]["cost_gen"],
                        exec_gen=data["fingerprint"]["exec_gen"],
                        code_sha=data["fingerprint"]["code_sha"],
                        seed=data["fingerprint"].get("seed"),
                        extra=data["fingerprint"].get("extra", {}),
                    ),
                    status=data["status"],
                    created_at=data["created_at"],
                    parent_run_id=data.get("parent_run_id"),
                    reason=data.get("reason", ""),
                    files_changed=data.get("files_changed", []),
                    defect_class=data.get("defect_class", ""),
                )
                self._records[rec.run_id] = rec

    def _append(self, record: RunRecord) -> None:
        payload = record.to_dict()
        # Persist full fingerprint (not just hex) so the record is self-describing.
        payload["fingerprint"] = {
            "spec_gen": record.fingerprint.spec_gen,
            "data_gen": record.fingerprint.data_gen,
            "engine_gen": record.fingerprint.engine_gen,
            "cost_gen": record.fingerprint.cost_gen,
            "exec_gen": record.fingerprint.exec_gen,
            "code_sha": record.fingerprint.code_sha,
            "seed": record.fingerprint.seed,
            "extra": record.fingerprint.extra,
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True) + "\n")

    def register(
        self,
        experiment_id: str,
        fingerprint: ExperimentFingerprint,
        reason: str = "",
        parent_run_id: Optional[str] = None,
        files_changed: Optional[list] = None,
        defect_class: str = "",
    ) -> RunRecord:
        """Register a completed run. Refuses to overwrite an existing run id."""
        run_id = f"RUN-{uuid.uuid4().hex[:12]}"
        record = RunRecord(
            run_id=run_id,
            experiment_id=experiment_id,
            fingerprint=fingerprint,
            status="COMPLETED",
            created_at=datetime.now(timezone.utc).isoformat(),
            parent_run_id=parent_run_id,
            reason=reason,
            files_changed=list(files_changed or []),
            defect_class=defect_class,
        )
        self._append(record)
        self._records[run_id] = record
        return record

    def invalidate(self, run_id: str, reason: str, defect_class: str = "") -> RunRecord:
        """Mark a completed run INVALIDATED (immutable history: original preserved)."""
        record = self.get(run_id)
        if record.status != "COMPLETED":
            raise RunRegistryError(f"run {run_id} is already {record.status}")
        updated = record.with_status("INVALIDATED", reason=reason, defect_class=defect_class)
        self._append(updated)
        self._records[run_id] = updated
        return updated

    def supersede(self, run_id: str, new_fingerprint: ExperimentFingerprint, reason: str) -> RunRecord:
        """Mark a completed run SUPERSEDED and register its replacement generation."""
        record = self.get(run_id)
        if record.status != "COMPLETED":
            raise RunRegistryError(f"run {run_id} is already {record.status}")
        self.invalidate(run_id, reason, defect_class="SUPERSEDED_GENERATION")
        return self.register(
            experiment_id=record.experiment_id,
            fingerprint=new_fingerprint,
            reason=reason,
            parent_run_id=run_id,
        )

    def get(self, run_id: str) -> RunRecord:
        try:
            return self._records[run_id]
        except KeyError:
            raise RunRegistryError(f"unknown run {run_id!r}") from None

    def all(self) -> list:
        return [self._records[k] for k in sorted(self._records)]
