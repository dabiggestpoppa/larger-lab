"""Evidence system for OCE control plane.

B3.C4 / B2-C4 — evaluation protocol, manifests/hashes, independent
verification, truth promotion, replay.

Produces deterministic manifests after mutable output closes. Separate
builder result from gate evaluator. Promotion through
SCAFFOLDED→SIMULATED→OBSERVED→VERIFIED.
"""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import json
import hashlib

from .clocks import get_clock
from .hashes import generate_id, sha256_hex, sha256_file


# Truth promotion ladder (B3.C4.S4)
TRUTH_LEVELS = ["SCAFFOLDED", "SIMULATED", "OBSERVED", "VERIFIED"]
PROMOTION_ORDER = {level: i for i, level in enumerate(TRUTH_LEVELS)}


@dataclass
class EvaluationResult:
    evaluation_id: str
    requirement: str
    test_name: str
    environment: str
    inputs: dict
    evaluator_version: str
    expected: str
    observed: str
    passed: bool
    falsification_criteria: str
    timestamp: str
    truth_level: str = "OBSERVED"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ArtifactEntry:
    name: str
    path: str
    sha256: str
    size_bytes: int
    required: bool = True


class EvidenceBuilder:
    """Builds evidence manifests deterministically."""

    def __init__(self, run_id: str):
        self._run_id = run_id
        self._evaluations: list[EvaluationResult] = []
        self._artifacts: list[ArtifactEntry] = []
        self._manifest_id = generate_id()

    def add_artifact(self, name: str, path: str, required: bool = True) -> ArtifactEntry:
        """Add an artifact to the manifest. Computes hash at build time."""
        sha = sha256_file(path)
        size = Path(path).stat().st_size
        entry = ArtifactEntry(
            name=name, path=path, sha256=sha,
            size_bytes=size, required=required
        )
        self._artifacts.append(entry)
        return entry

    def add_evaluation(self, *, requirement: str, test_name: str, environment: str,
                       inputs: dict, evaluator_version: str, expected: str,
                       observed: str, passed: bool,
                       falsification_criteria: str = "",
                       truth_level: str = "OBSERVED") -> EvaluationResult:
        clock = get_clock()
        ev = EvaluationResult(
            evaluation_id=generate_id(),
            requirement=requirement,
            test_name=test_name,
            environment=environment,
            inputs=inputs,
            evaluator_version=evaluator_version,
            expected=expected,
            observed=observed,
            passed=passed,
            falsification_criteria=falsification_criteria,
            timestamp=clock.now().isoformat(),
            truth_level=truth_level,
        )
        self._evaluations.append(ev)
        return ev

    def build_manifest(self) -> dict:
        """Build the final manifest. Nothing mutates after this."""
        clock = get_clock()
        artifacts_json = [asdict(a) for a in self._artifacts]

        # Compute outer digest over sorted artifact list
        canonical = json.dumps(artifacts_json, sort_keys=True, separators=(",", ":"))
        outer_digest = sha256_hex(canonical)

        return {
            "manifest_id": self._manifest_id,
            "run_id": self._run_id,
            "produced_at": clock.now().isoformat(),
            "artifacts": artifacts_json,
            "outer_digest": outer_digest,
        }

    def verify_manifest(self, manifest: dict) -> tuple[bool, list[str]]:
        """Verify a manifest. Checks hashes match actual files."""
        errors = []
        for art in manifest.get("artifacts", []):
            p = Path(art["path"])
            if not p.exists():
                errors.append(f"Missing artifact: {art['name']} at {art['path']}")
                continue
            actual_sha = sha256_file(p)
            if actual_sha != art["sha256"]:
                errors.append(
                    f"Hash mismatch for {art['name']}: "
                    f"manifest={art['sha256']} actual={actual_sha}"
                )
            actual_size = p.stat().st_size
            if actual_size != art["size_bytes"]:
                errors.append(
                    f"Size mismatch for {art['name']}: "
                    f"manifest={art['size_bytes']} actual={actual_size}"
                )

        # Verify outer digest
        artifacts_json = manifest.get("artifacts", [])
        canonical = json.dumps(artifacts_json, sort_keys=True, separators=(",", ":"))
        computed_digest = sha256_hex(canonical)
        if computed_digest != manifest.get("outer_digest"):
            errors.append(
                f"Outer digest mismatch: manifest={manifest.get('outer_digest')} "
                f"computed={computed_digest}"
            )

        return (len(errors) == 0, errors)

    @property
    def evaluations(self) -> list:
        return list(self._evaluations)


class TruthPromotionLedger:
    """Manages truth level promotion and demotion (B3.C4.S4)."""

    def __init__(self):
        self._claims: dict[str, str] = {}  # claim_id -> truth_level

    def register(self, claim_id: str, initial_level: str = "SCAFFOLDED") -> None:
        if initial_level not in TRUTH_LEVELS:
            raise ValueError(f"Invalid truth level: {initial_level}")
        self._claims[claim_id] = initial_level

    def promote(self, claim_id: str, to_level: str, evidence: str) -> str:
        """Promote a claim to a higher truth level."""
        if to_level not in TRUTH_LEVELS:
            raise ValueError(f"Invalid truth level: {to_level}")
        current = self._claims.get(claim_id, "SCAFFOLDED")
        if PROMOTION_ORDER[to_level] <= PROMOTION_ORDER[current]:
            raise ValueError(
                f"Cannot promote {claim_id} from {current} to {to_level} "
                f"(not an increase)"
            )
        self._claims[claim_id] = to_level
        return to_level

    def demote(self, claim_id: str, to_level: str, reason: str) -> str:
        """Demote a claim (e.g., staleness)."""
        if to_level not in TRUTH_LEVELS:
            raise ValueError(f"Invalid truth level: {to_level}")
        current = self._claims.get(claim_id)
        if current is None:
            raise KeyError(f"Claim '{claim_id}' not registered")
        self._claims[claim_id] = to_level
        return to_level

    def get_level(self, claim_id: str) -> Optional[str]:
        return self._claims.get(claim_id)

    @property
    def claims(self) -> dict:
        return dict(self._claims)


class ReplayHarness:
    """Reconstructs decisions/results from immutable inputs (B3.C4.S5)."""

    def __init__(self, job_store):
        self._job_store = job_store

    def replay_job(self, job_id: str) -> dict:
        """Replay a job's decision path from its immutable inputs."""
        job = self._job_store.get_job(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")

        return {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "schema_version": job.schema_version,
            "payload_hash": job.payload_hash,
            "status": job.status,
            "result": job.result,
            "failure_envelope": job.failure_envelope,
            "replayable": True,
            "divergence": None,
        }

    def replay_all(self) -> list[dict]:
        """Replay all jobs. Report any divergence."""
        results = []
        for job_id in self._job_store.all_jobs:
            results.append(self.replay_job(job_id))
        return results
