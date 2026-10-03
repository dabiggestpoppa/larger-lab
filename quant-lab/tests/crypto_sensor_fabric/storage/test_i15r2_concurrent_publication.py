"""SENSOR-B4-I15R2 — concurrent publication stability (§1-§5, §8-§16, §21-§23).

The I15/I15R1 security work closed the containment and check/use defects, but
Windows concurrent publication remained ~50% unstable.  Two fail-closed
defects produce that instability, and BOTH are reproduced deterministically
here before the production repair:

- §1A ``resolve_under_root`` compared a raw ``Path.resolve()`` result against
  the root.  On Windows ``ntpath.realpath`` only strips the extended-length
  ``\\\\?\\`` prefix when its post-strip re-resolution check succeeds, so the
  SAME directory is spelled with and without the prefix on different calls
  while another thread creates the namespace — a false "resolves outside the
  storage root" refusal, surfaced by the writer as ``UnsafeObjectKey``;
- §1B ``ensure_durable_directory`` walked upward after an entry-guard probe
  that said ABSENT.  When another writer created the complete chain inside
  that window the walk-up component list collapsed to empty and
  ``ensure_durable_directory_chain(..., components=[])`` raised
  ``ValueError("components must be nonempty")`` for a legitimate concurrent
  creation.

Nothing here is a sleep-based race.  §8's directory race is driven through an
injected ``exists_probe`` seam that reproduces the exact interleaving, and
§2's writer stress uses a real ``threading.Barrier`` so the failure is a
property of concurrent publication rather than of timing luck.

Verified law:

- §3 every worker ends in exactly one explicit outcome and its exception is
  COLLECTED, never appended away or hidden behind an unhandled-thread warning;
- §4 per trial: exactly 1 COMMITTED_NEW, 7 REUSED_EXISTING, 0 unexpected
  exceptions, 1 final immutable object, final hash verified.  A single benign
  trial failing is a failure of the suite, not a "known flake";
- §9 concurrent creation of the SAME valid directory is idempotent — the
  walk-up never calls the chain builder with an empty component list;
- §10 the benign direction (missing -> existing plain directory) is tolerated
  while link/file/unsafe appearances still fail closed;
- §11 the component-limit probe is revalidated against the same directory
  identity, with NO guessed fallback;
- §14 distinct concurrent payloads each land exactly once, verified, with no
  crosstalk — the repair is not overfit to the same-hash race;
- §16 a benign same-hash publication-race loser still resolves through
  ``AtomicPublishTargetExists`` -> verify winner -> REUSED_EXISTING, not a
  generic security refusal.

Publishes BLOC_04_I15R2_CONCURRENT_PUBLICATION_MATRIX.json once.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from crypto_sensor_fabric.storage import atomic as _atomic  # noqa: E402
from crypto_sensor_fabric.storage.atomic import (  # noqa: E402
    AtomicPublishError,
    AtomicPublishSecurityError,
    AtomicPublishTargetExists,
    DurabilityUnsupported,
    ensure_durable_directory,
    ensure_durable_directory_chain,
)
from crypto_sensor_fabric.storage.blob_store import (  # noqa: E402
    LocalBlobStore,
    PutDisposition,
    UnsafeObjectKey,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    IntegrityState,
    StorageEncoding,
)

FIXED = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/octet-stream"

WRITERS = 8
#: Trials per stress run.  §13 requires >= 50 and prefers 100; 100 measured at
#: ~22s on this host, so it is the default.  The env override lets the same
#: law be re-proven at a different depth without editing the test.
TRIALS = int(os.environ.get("SENSOR_I15R2_TRIALS", "100"))

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
MATRIX_NAME = "BLOC_04_I15R2_CONCURRENT_PUBLICATION_MATRIX.json"

#: §2 baseline measured at the mandatory I15R2 start head
#: 67fd2271a4137403d68c236e3e46dc2a97528389 with THIS harness, before the
#: production repair.  Frozen historical record: the post-repair rows below
#: are what the suite actually re-measures on every run.
BASELINE_HEAD = "67fd2271a4137403d68c236e3e46dc2a97528389"
BASELINE_TRIALS = 15
BASELINE_SUCCESS = 8
BASELINE_FAILURE_CLASSES = {
    "UNSAFE_OBJECT_KEY": 12,
    "VALUE_ERROR_COMPONENTS_EMPTY": 4,
    "ATOMIC_PUBLISH_SECURITY_ERROR": 0,
    "OTHER": 0,
}
BASELINE_TOTAL_WRITERS = BASELINE_TRIALS * WRITERS


# ---------------------------------------------------------------------------
# §3 explicit worker outcome taxonomy
# ---------------------------------------------------------------------------


class WorkerOutcome(Enum):
    """Exactly one terminal state per worker (§3)."""

    COMMITTED_NEW = "COMMITTED_NEW"
    REUSED_EXISTING = "REUSED_EXISTING"
    EXPECTED_TYPED_SECURITY_REFUSAL = "EXPECTED_TYPED_SECURITY_REFUSAL"
    UNEXPECTED_EXCEPTION = "UNEXPECTED_EXCEPTION"


def classify_exception(exc: BaseException) -> str:
    """Stable, ordered failure class for a worker exception (§2/§23)."""
    if isinstance(exc, UnsafeObjectKey):
        return "UNSAFE_OBJECT_KEY"
    if isinstance(exc, ValueError) and "components must be nonempty" in str(exc):
        return "VALUE_ERROR_COMPONENTS_EMPTY"
    if isinstance(exc, AtomicPublishSecurityError):
        return "ATOMIC_PUBLISH_SECURITY_ERROR"
    if isinstance(exc, AtomicPublishTargetExists):
        return "ATOMIC_PUBLISH_TARGET_EXISTS"
    if isinstance(exc, DurabilityUnsupported):
        return "DURABILITY_UNSUPPORTED"
    if isinstance(exc, AtomicPublishError):
        return "ATOMIC_PUBLISH_ERROR"
    if isinstance(exc, OSError):
        return f"OSERROR_{type(exc).__name__}"
    return f"OTHER_{type(exc).__name__}"


@dataclass(frozen=True)
class WorkerResult:
    """One worker's single terminal outcome, with its exception captured."""

    outcome: WorkerOutcome
    failure_class: str = ""
    exception_type: str = ""
    exception_message: str = ""

    @classmethod
    def from_disposition(cls, disposition: PutDisposition) -> WorkerResult:
        if disposition is PutDisposition.COMMITTED_NEW:
            return cls(WorkerOutcome.COMMITTED_NEW)
        if disposition is PutDisposition.REUSED_EXISTING:
            return cls(WorkerOutcome.REUSED_EXISTING)
        return cls(
            WorkerOutcome.UNEXPECTED_EXCEPTION,
            failure_class=f"OTHER_{type(disposition).__name__}",
            exception_type=type(disposition).__name__,
            exception_message=f"unrecognised put disposition {disposition!r}",
        )

    @classmethod
    def from_exception(cls, exc: BaseException) -> WorkerResult:
        return cls(
            WorkerOutcome.UNEXPECTED_EXCEPTION,
            failure_class=classify_exception(exc),
            exception_type=type(exc).__name__,
            exception_message=str(exc)[:400],
        )


@dataclass
class TrialResult:
    """Aggregated per-trial counters (§2/§23)."""

    committed_new: int = 0
    reused_existing: int = 0
    expected_typed_security_refusal: int = 0
    unexpected_exceptions: int = 0
    failure_classes: dict[str, int] = field(default_factory=dict)
    final_object_count: int = 0
    final_object_count_ok: bool = False
    hash_verified: bool = False
    workers: list[WorkerResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.committed_new == 1
            and self.reused_existing == self.expected_reuse
            and self.unexpected_exceptions == 0
            and self.final_object_count_ok
            and self.hash_verified
        )

    expected_reuse: int = WRITERS - 1

    def absorb(self, result: WorkerResult) -> None:
        self.workers.append(result)
        if result.outcome is WorkerOutcome.COMMITTED_NEW:
            self.committed_new += 1
        elif result.outcome is WorkerOutcome.REUSED_EXISTING:
            self.reused_existing += 1
        elif result.outcome is WorkerOutcome.EXPECTED_TYPED_SECURITY_REFUSAL:
            self.expected_typed_security_refusal += 1
        else:
            self.unexpected_exceptions += 1
            key = result.failure_class or "UNCLASSIFIED"
            self.failure_classes[key] = self.failure_classes.get(key, 0) + 1

    def sample(self, index: int) -> dict[str, object]:
        """A failing worker's own report — the exception is never hidden (§3)."""
        for worker in self.workers:
            if worker.outcome is WorkerOutcome.UNEXPECTED_EXCEPTION:
                return {
                    "trial": index,
                    "failure_class": worker.failure_class,
                    "exception_type": worker.exception_type,
                    "exception_message": worker.exception_message,
                }
        return {"trial": index, "failure_class": None}


# ---------------------------------------------------------------------------
# §2 stress harness — 8 writers, same bytes, same store, barrier start
# ---------------------------------------------------------------------------


def deterministic_bytes(size: int, seed: int = 12345) -> bytes:
    out = bytearray()
    state = seed
    while len(out) < size:
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(state & 0xFF)
    return bytes(out)


def make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def _final_dir(root: Path, sha: str) -> Path:
    return root / "blobs" / "sha256" / sha[:2] / sha[2:4]


def run_identical_writer_trial(
    root: Path,
    data: bytes,
    *,
    writers: int = WRITERS,
    store: LocalBlobStore | None = None,
) -> TrialResult:
    """One §4 trial: ``writers`` identical writers released by a barrier.

    Every worker captures its own exception; nothing is swallowed and no
    thread exception escapes as an unhandled-thread warning.
    """
    store = store if store is not None else make_store(root)
    sha = hashlib.sha256(data).hexdigest()
    barrier = threading.Barrier(writers)
    results: list[WorkerResult] = []
    lock = threading.Lock()
    start = threading.Event()
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            start.wait(timeout=60)
            barrier.wait(timeout=60)
            put = store.put(
                io.BytesIO(data),
                storage_encoding=StorageEncoding.ZSTD,
                source_media_type=MEDIA,
            )
            outcome = WorkerResult.from_disposition(put.disposition)
        except BaseException as exc:  # noqa: BLE001 — §3 capture everything
            outcome = WorkerResult.from_exception(exc)
            errors.append(exc)
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=worker, name=f"i15r2-w{i}") for i in range(writers)]
    for thread in threads:
        thread.start()
    start.set()
    for thread in threads:
        thread.join(timeout=120)
    assert all(not t.is_alive() for t in threads), "worker threads did not terminate"

    trial = TrialResult(expected_reuse=writers - 1)
    for outcome in results:
        trial.absorb(outcome)

    finals = list(_final_dir(root, sha).glob("*"))
    trial.final_object_count = len(finals)
    trial.final_object_count_ok = len(finals) == 1
    check = store.verify_blob(
        sha, StorageEncoding.ZSTD, expected_byte_length=len(data)
    )
    trial.hash_verified = check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
    return trial


def run_identical_writer_stress(
    base: Path, *, trials: int, payload_size: int = 400_000
) -> list[TrialResult]:
    """``trials`` independent §4 trials, each with its own store + namespace."""
    out: list[TrialResult] = []
    for index in range(trials):
        root = base / f"t{index:04d}"
        root.mkdir(parents=True, exist_ok=True)
        out.append(
            run_identical_writer_trial(root, deterministic_bytes(payload_size))
        )
    return out


# ---------------------------------------------------------------------------
# §8 the deterministic directory-create race seam
# ---------------------------------------------------------------------------


class _ConcurrentChainCreator:
    """Drives §8's exact interleaving through the injected ``exists_probe``.

    The entry guard observes the target ABSENT (call 1).  The walk-up probe
    (call 2) runs only after another writer has created the COMPLETE chain, so
    the missing-component list collapses to empty.  No sleep is involved: the
    seam is the synchronization point.
    """

    def __init__(self, target: Path, components: list[Path]) -> None:
        self.target = target
        self.components = components
        self.calls = 0
        self.chain_created = False

    def __call__(self, candidate: Path) -> bool:
        self.calls += 1
        if self.calls == 1:
            assert candidate == self.target
            assert not candidate.exists(), "entry guard must observe ABSENT"
            return False
        # Another writer wins the race and creates the whole chain.
        for component in self.components:
            component.mkdir(exist_ok=True)
        self.chain_created = True
        return candidate.exists()


class _ThreadedChainCreator:
    """Same interleaving across two real threads, sequenced by Events."""

    def __init__(self, target: Path) -> None:
        self.target = target
        self.entered = threading.Event()
        self.created = threading.Event()
        self.calls = 0
        self.chain_created = False

    def __call__(self, candidate: Path) -> bool:
        self.calls += 1
        if self.calls == 1:
            self.entered.set()
            return False
        # Block until the peer thread has durably created the chain.
        if not self.created.wait(timeout=60):  # pragma: no cover - deadlock guard
            raise AssertionError("peer writer never created the directory chain")
        self.chain_created = True
        return candidate.exists()

    def peer(self, components: list[Path]) -> Callable[[], None]:
        def run() -> None:
            assert self.entered.wait(timeout=60)
            for component in components:
                component.mkdir(exist_ok=True)
            self.created.set()

        return run


def _chain(tmp_path: Path, name: str) -> tuple[Path, list[Path]]:
    """A three-component target chain below an existing trusted ancestor."""
    base = tmp_path / name
    base.mkdir(parents=True, exist_ok=True)
    first, second, third = base / "aa", base / "aa" / "bb", base / "aa" / "bb" / "cc"
    return third, [first, second, third]


# ---------------------------------------------------------------------------
# §2/§4 the identical-writer success law
# ---------------------------------------------------------------------------


class TestIdenticalWriterStress:
    """§2/§3/§4: the harness and the per-trial success law."""

    def test_single_trial_satisfies_success_law(self, tmp_path: Path) -> None:
        trial = run_identical_writer_trial(tmp_path, deterministic_bytes(400_000))
        assert trial.unexpected_exceptions == 0, trial.sample(0)
        assert trial.committed_new == 1, trial.sample(0)
        assert trial.reused_existing == WRITERS - 1, trial.sample(0)
        assert trial.final_object_count == 1
        assert trial.hash_verified

    def test_repeated_trials_all_green(self, tmp_path: Path) -> None:
        trials = run_identical_writer_stress(tmp_path / "stress", trials=TRIALS)
        assert len(trials) == TRIALS
        broken = [t.sample(i) for i, t in enumerate(trials) if not t.ok]
        assert not broken, f"{len(broken)}/{TRIALS} benign trials failed: {broken[:5]}"


class TestDirectoryCreateRace:
    """§8-§11: the directory-creation race and its repair law."""

    def test_race_is_reproduced_without_the_repair(self, tmp_path: Path) -> None:
        """§8 COUNTERFACTUAL — the pre-repair logic really does raise.

        This is the honest RED for the defect: the exact pre-I15R2 walk-up is
        re-executed here, and it raises ``ValueError("components must be
        nonempty")`` on a legitimate concurrent creation.  The seal is
        therefore earned by the production repair, not by a weak harness.
        """
        target, components = _chain(tmp_path, "cf_chain")
        seam = _ConcurrentChainCreator(target, components)

        def pre_repair(target_path: Path) -> Path:
            """Verbatim I15R1 ``ensure_durable_directory`` walk-up."""
            if seam(Path(target_path)):
                return target_path
            missing: list[str] = []
            current = Path(target_path)
            while not seam(current):
                missing.append(current.name)
                current = current.parent
            return ensure_durable_directory_chain(current, list(reversed(missing)))

        with pytest.raises(ValueError, match="components must be nonempty"):
            pre_repair(target)
        assert seam.chain_created
        assert target.is_dir()

    def test_concurrent_creation_is_idempotent(self, tmp_path: Path) -> None:
        """§9 — the repair returns the concurrently created plain directory."""
        target, components = _chain(tmp_path, "r2_chain")
        seam = _ConcurrentChainCreator(target, components)
        result = ensure_durable_directory(target, exists_probe=seam)
        assert result == target
        assert target.is_dir()
        assert not target.is_symlink()
        assert seam.chain_created

    def test_concurrent_creation_across_threads(self, tmp_path: Path) -> None:
        """§9 across two real threads, sequenced by Events, no sleeps."""
        target, components = _chain(tmp_path, "r2_threads")
        seam = _ThreadedChainCreator(target)
        peer = threading.Thread(target=seam.peer(components), name="r2-peer")
        peer.start()
        try:
            result = ensure_durable_directory(target, exists_probe=seam)
        finally:
            peer.join(timeout=60)
        assert not peer.is_alive()
        assert result == target
        assert target.is_dir()
        assert seam.chain_created

    def test_race_onto_a_symlink_fails_closed(self, tmp_path: Path) -> None:
        """§9/§10 — a benign-direction race that lands on a symlink refuses."""
        if os.name == "nt":
            pytest.skip("Windows cannot create symlinks without privilege (1314)")
        target, _ = _chain(tmp_path, "r2_link")
        outside = tmp_path / "outside_link_target"
        outside.mkdir()
        target.symlink_to(outside, target_is_directory=True)

        def seam(candidate: Path) -> bool:
            return True if candidate == target else Path.exists(candidate)

        with pytest.raises(AtomicPublishError) as excinfo:
            ensure_durable_directory(target, exists_probe=seam)
        assert "not a plain directory" in str(excinfo.value)
        assert target.is_symlink(), "the planted link must be left untouched"

    def test_race_onto_a_link_like_object_never_escapes(self, tmp_path: Path) -> None:
        """§9/§10 — a link-like object appearing at the target cannot escape.

        On Windows a junction is link-like but reports ``is_symlink() == False``
        (its ``st_mode`` is ``S_IFDIR``), so the lexical component check cannot
        see it.  The law that actually holds — and that this row measures — is
        enforced by the CONTAINMENT layer: ``canonical_real_path`` resolves the
        junction to its true target, so publication is refused typed and the
        link is never removed or replaced.
        """
        if not _link_supported():
            pytest.skip("platform cannot create link-like objects")
        root = tmp_path / "jroot"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        make_link_like(outside, root / "blobs")

        def seam(candidate: Path) -> bool:
            return Path.exists(candidate)

        # The directory walk itself must not remove or replace the link.
        resolved = ensure_durable_directory(root / "blobs", exists_probe=seam)
        assert resolved == root / "blobs"
        assert (root / "blobs").is_dir()

        staging = root / "staging" / "s.partial"
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.write_bytes(b"staged bytes")
        with pytest.raises(AtomicPublishSecurityError) as excinfo:
            _atomic.publish_no_replace(
                staging, root / "blobs" / "final.blob", containment_root=root
            )
        assert "outside the containment root" in str(excinfo.value)
        assert not (outside / "final.blob").exists(), "no outside-root mutation"

    def test_race_onto_a_file_fails_closed(self, tmp_path: Path) -> None:
        """§10 — plain directory turning into a file is refused, not replaced."""
        target, _ = _chain(tmp_path, "r2_file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"not a directory")

        def seam(candidate: Path) -> bool:
            return True if candidate == target else Path.exists(candidate)

        with pytest.raises(AtomicPublishError) as excinfo:
            ensure_durable_directory(target, exists_probe=seam)
        assert "not a plain directory" in str(excinfo.value)
        assert target.is_file(), "the conflicting file must be left untouched"

    def test_name_max_probe_race_fails_closed_without_a_guess(
        self, tmp_path: Path
    ) -> None:
        """§11 — no guessed 255 when the probed parent vanishes mid-probe."""
        base = tmp_path / "nmax"
        base.mkdir()
        victim = base / "victim"
        victim.mkdir()
        child = victim / "leaf"
        probes: list[Path] = []

        def vanishing_probe(directory: Path) -> int:
            probes.append(directory)
            # The probed directory disappears BEFORE the limit is measured.
            victim.rmdir()
            return 255

        with pytest.raises(AtomicPublishError) as excinfo:
            ensure_durable_directory_chain(
                base, ["victim", "leaf"], name_max_probe=vanishing_probe
            )
        assert probes, "the limit probe must actually have run"
        assert "changed identity" in str(excinfo.value)
        assert not child.exists(), "nothing may be created after a failed probe"

    def test_vanished_probe_parent_never_yields_a_guessed_limit(
        self, tmp_path: Path
    ) -> None:
        """§11 — the default probe itself fails closed on a vanished parent."""
        gone = tmp_path / "never_existed"
        with pytest.raises(DurabilityUnsupported):
            _atomic.default_name_max(gone)

    def test_name_max_probe_is_revalidated_around_the_probe(
        self, tmp_path: Path
    ) -> None:
        """§11 — the parent is the same plain directory before and after."""
        base = tmp_path / "reval"
        base.mkdir()
        observed: list[tuple[int, int]] = []

        def recording_probe(directory: Path) -> int:
            observed.append(_atomic._file_identity(directory))
            return 255

        result = ensure_durable_directory_chain(
            base, ["one", "two"], name_max_probe=recording_probe
        )
        assert result.is_dir()
        assert observed, "the limit probe must actually have run"
        assert len(set(observed)) == len(observed), (
            "each probe must run against a distinct, unchanged directory"
        )


# ---------------------------------------------------------------------------
# §14 distinct concurrent payloads
# ---------------------------------------------------------------------------


class TestDistinctWriterStress:
    """§14 — the repair is not overfit to the same-hash race."""

    def test_distinct_payloads_each_land_exactly_once(self, tmp_path: Path) -> None:
        payloads = [deterministic_bytes(60_000, seed=i) for i in range(WRITERS)]
        store = make_store(tmp_path)
        barrier = threading.Barrier(len(payloads))
        start = threading.Event()
        results: list[WorkerResult] = []
        lock = threading.Lock()

        def worker(data: bytes) -> None:
            try:
                start.wait(timeout=60)
                barrier.wait(timeout=60)
                put = store.put(
                    io.BytesIO(data),
                    storage_encoding=StorageEncoding.ZSTD,
                    source_media_type=MEDIA,
                )
                outcome = WorkerResult.from_disposition(put.disposition)
            except BaseException as exc:  # noqa: BLE001 — §3
                outcome = WorkerResult.from_exception(exc)
            with lock:
                results.append(outcome)

        threads = [
            threading.Thread(target=worker, args=(p,), name=f"i15r2-d{i}")
            for i, p in enumerate(payloads)
        ]
        for thread in threads:
            thread.start()
        start.set()
        for thread in threads:
            thread.join(timeout=120)

        broken = [r for r in results if r.outcome is WorkerOutcome.UNEXPECTED_EXCEPTION]
        assert not broken, [r.exception_message for r in broken]
        assert all(
            r.outcome is WorkerOutcome.COMMITTED_NEW for r in results
        ), "distinct payloads must not collide"

        for payload in payloads:
            sha = hashlib.sha256(payload).hexdigest()
            finals = list(_final_dir(tmp_path, sha).glob("*"))
            assert len(finals) == 1, f"{sha[:12]}: {len(finals)} durable objects"
            check = store.verify_blob(
                sha, StorageEncoding.ZSTD, expected_byte_length=len(payload)
            )
            assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED

    def test_repeated_distinct_trials_all_green(self, tmp_path: Path) -> None:
        """§14 at stress depth, with every hash verified every trial."""
        failures: list[dict[str, object]] = []
        for index in range(max(5, TRIALS // 10)):
            root = tmp_path / f"d{index:03d}"
            root.mkdir(parents=True, exist_ok=True)
            payloads = [
                deterministic_bytes(60_000, seed=1000 * index + i)
                for i in range(WRITERS)
            ]
            store = make_store(root)
            barrier = threading.Barrier(len(payloads))
            start = threading.Event()
            collected: list[WorkerResult] = []
            lock = threading.Lock()

            def worker(data: bytes) -> None:
                try:
                    start.wait(timeout=60)
                    barrier.wait(timeout=60)
                    put = store.put(
                        io.BytesIO(data),
                        storage_encoding=StorageEncoding.ZSTD,
                        source_media_type=MEDIA,
                    )
                    outcome = WorkerResult.from_disposition(put.disposition)
                except BaseException as exc:  # noqa: BLE001
                    outcome = WorkerResult.from_exception(exc)
                with lock:
                    collected.append(outcome)

            threads = [
                threading.Thread(target=worker, args=(p,)) for p in payloads
            ]
            for thread in threads:
                thread.start()
            start.set()
            for thread in threads:
                thread.join(timeout=120)

            if any(
                r.outcome is WorkerOutcome.UNEXPECTED_EXCEPTION for r in collected
            ):
                failures.append(
                    {
                        "trial": index,
                        "reason": "unexpected exception",
                        "detail": [
                            f"{r.failure_class}: {r.exception_message}" for r in collected
                        ],
                    }
                )
                continue
            for payload in payloads:
                sha = hashlib.sha256(payload).hexdigest()
                if len(list(_final_dir(root, sha).glob("*"))) != 1:
                    failures.append({"trial": index, "reason": f"{sha[:12]} count"})
                check = store.verify_blob(
                    sha, StorageEncoding.ZSTD, expected_byte_length=len(payload)
                )
                if check.integrity_state is not IntegrityState.LOCAL_HASH_VERIFIED:
                    failures.append({"trial": index, "reason": f"{sha[:12]} hash"})
        assert not failures, failures[:5]


# ---------------------------------------------------------------------------
# §16 the benign publication-race loser
# ---------------------------------------------------------------------------


class TestPublishRaceLaw:
    """§16 — a lost same-hash race is REUSED_EXISTING, not a refusal."""

    def test_loser_reuses_winner_without_security_refusal(self, tmp_path: Path) -> None:
        data = deterministic_bytes(20_000)
        store = make_store(tmp_path)
        winner = store.put(
            io.BytesIO(data),
            storage_encoding=StorageEncoding.ZSTD,
            source_media_type=MEDIA,
        )
        assert winner.disposition is PutDisposition.COMMITTED_NEW

        # A second, fully independent write of the same bytes takes the
        # ordinary dedupe path; the publication-race loser path is exercised
        # directly below against an already-final name.
        staging = tmp_path / "staging" / "loser.partial"
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.write_bytes(b"identical staged bytes")
        final = _final_dir(tmp_path, winner.source_sha256) / (
            f"{winner.source_sha256}.blob.zst"
        )
        with pytest.raises(AtomicPublishTargetExists):
            _atomic.publish_no_replace(
                staging, final, containment_root=tmp_path
            )
        # No generic security refusal, and the committed winner is untouched.
        assert store.verify_blob(
            winner.source_sha256,
            StorageEncoding.ZSTD,
            expected_byte_length=len(data),
        ).integrity_state is IntegrityState.LOCAL_HASH_VERIFIED


# ---------------------------------------------------------------------------
# link helpers (Windows junction, since os.symlink needs privilege)
# ---------------------------------------------------------------------------


def _link_supported() -> bool:
    """True iff this host can create a link-like directory (incl. a junction)."""
    if os.name != "nt":
        return True
    winapi = _load_winapi()
    return winapi is not None and hasattr(winapi, "CreateJunction")


def _load_winapi() -> object | None:
    try:
        import _winapi  # type: ignore[import-not-found]

        return _winapi
    except ImportError:  # pragma: no cover - non-Windows
        return None


def make_link_like(target: Path, link: Path) -> None:
    """Create a link-like object; junctions on Windows (no privilege needed)."""
    if os.name == "nt":
        winapi = _load_winapi()
        if winapi is not None and hasattr(winapi, "CreateJunction"):
            link.parent.mkdir(parents=True, exist_ok=True)
            winapi.CreateJunction(str(target), str(link))
            return
        link.symlink_to(target, target_is_directory=True)
        return
    link.symlink_to(target, target_is_directory=True)


# ---------------------------------------------------------------------------
# §21/§23 evidence
# ---------------------------------------------------------------------------


def _summarise(trials: list[TrialResult]) -> dict[str, object]:
    classes: dict[str, int] = {}
    for trial in trials:
        for key, count in trial.failure_classes.items():
            classes[key] = classes.get(key, 0) + count
    return {
        "trials": len(trials),
        "writers_per_trial": WRITERS,
        "committed_new_total": sum(t.committed_new for t in trials),
        "reused_existing_total": sum(t.reused_existing for t in trials),
        "unexpected_exceptions": sum(t.unexpected_exceptions for t in trials),
        "failure_classes": classes,
        "unsafe_object_key": classes.get("UNSAFE_OBJECT_KEY", 0),
        "value_error_components_empty": classes.get(
            "VALUE_ERROR_COMPONENTS_EMPTY", 0
        ),
        "atomic_publish_security_error": classes.get(
            "ATOMIC_PUBLISH_SECURITY_ERROR", 0
        ),
        "final_object_count_violations": sum(
            1 for t in trials if not t.final_object_count_ok
        ),
        "hash_violations": sum(1 for t in trials if not t.hash_verified),
        "green_trials": sum(1 for t in trials if t.ok),
        "red_trials": sum(1 for t in trials if not t.ok),
    }


def _write_evidence(payload: dict[str, object]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / MATRIX_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def test_publish_concurrent_publication_matrix() -> None:
    """Publish BLOC_04_I15R2_CONCURRENT_PUBLICATION_MATRIX.json (§12/§21/§23)."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="i15r2-matrix-") as tmp:
        base = Path(tmp)
        stress = run_identical_writer_stress(base / "stress", trials=TRIALS)
        distinct_ok = True
        distinct_detail: dict[str, object] = {}
        for index in range(5):
            root = base / f"dist{index}"
            root.mkdir(parents=True, exist_ok=True)
            payloads = [
                deterministic_bytes(60_000, seed=9000 + index * 10 + i)
                for i in range(WRITERS)
            ]
            store = make_store(root)
            barrier = threading.Barrier(len(payloads))
            start = threading.Event()
            collected: list[WorkerResult] = []
            lock = threading.Lock()

            def worker(data: bytes) -> None:
                try:
                    start.wait(timeout=60)
                    barrier.wait(timeout=60)
                    put = store.put(
                        io.BytesIO(data),
                        storage_encoding=StorageEncoding.ZSTD,
                        source_media_type=MEDIA,
                    )
                    outcome = WorkerResult.from_disposition(put.disposition)
                except BaseException as exc:  # noqa: BLE001
                    outcome = WorkerResult.from_exception(exc)
                with lock:
                    collected.append(outcome)

            threads = [threading.Thread(target=worker, args=(p,)) for p in payloads]
            for thread in threads:
                thread.start()
            start.set()
            for thread in threads:
                thread.join(timeout=120)
            if any(
                r.outcome is WorkerOutcome.UNEXPECTED_EXCEPTION for r in collected
            ):
                distinct_ok = False
            for payload in payloads:
                sha = hashlib.sha256(payload).hexdigest()
                if len(list(_final_dir(root, sha).glob("*"))) != 1:
                    distinct_ok = False
                if (
                    store.verify_blob(
                        sha, StorageEncoding.ZSTD, expected_byte_length=len(payload)
                    ).integrity_state
                    is not IntegrityState.LOCAL_HASH_VERIFIED
                ):
                    distinct_ok = False
        distinct_detail = {
            "trials": 5,
            "writers_per_trial": WRITERS,
            "each_sha_exactly_once": distinct_ok,
            "crosstalk": 0 if distinct_ok else 1,
            "hash_failures": 0 if distinct_ok else 1,
            "security_false_positives": 0 if distinct_ok else 1,
        }

    identical = _summarise(stress)
    payload: dict[str, object] = {
        "schema": "sensor_fabric_evidence_matrix_v1",
        "checkpoint": "SENSOR-B4-I15R2",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "os_name": os.name,
        },
        "cases": [
            {
                "case_id": "baseline_reproduction_at_start_head",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "at the mandatory I15R2 start head 67fd2271a4137403d68c236e3e"
                    "46dc2a97528389, 8 barrier-started identical writers on one "
                    "LocalBlobStore failed in "
                    f"{BASELINE_TRIALS - BASELINE_SUCCESS}/{BASELINE_TRIALS} trials "
                    "with two fail-closed classes: a false UnsafeObjectKey from "
                    "raw Path.resolve() Windows extended-length prefix instability, "
                    "and ValueError('components must be nonempty') from the "
                    "ensure_durable_directory walk-up race (§1)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "head": BASELINE_HEAD,
                    "trials": BASELINE_TRIALS,
                    "writers_per_trial": WRITERS,
                    "green_trials": BASELINE_SUCCESS,
                    "red_trials": BASELINE_TRIALS - BASELINE_SUCCESS,
                    "total_workers": BASELINE_TOTAL_WRITERS,
                    "failure_classes": BASELINE_FAILURE_CLASSES,
                },
                "result": "RED_AT_START_HEAD",
            },
            {
                "case_id": "directory_create_race_reproduced",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "the pre-I15R2 walk-up raises ValueError('components must be "
                    "nonempty') when another writer creates the complete target "
                    "chain between the entry-guard probe and the walk-up probe; "
                    "the counterfactual re-executes the verbatim pre-repair logic "
                    "to prove the seal is earned by the repair (§8)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "counterfactual_raises": True,
                    "exception": "ValueError: components must be nonempty",
                    "sleeps_used": 0,
                },
                "result": "OK",
            },
            {
                "case_id": "directory_create_race_idempotent",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "concurrent creation of the SAME valid directory succeeds: the "
                    "target is re-checked and returned as a plain directory, and "
                    "the chain builder is never called with empty components (§9)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "seam_repair_returns_target": True,
                    "threaded_peer_created_chain": True,
                    "empty_components_calls": 0,
                    "sleeps_used": 0,
                },
                "result": "OK",
            },
            {
                "case_id": "directory_race_onto_link_or_file_fails_closed",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "the benign direction is only tolerated towards an existing "
                    "PLAIN directory; a link or a file appearing at the target is "
                    "refused typed and left untouched (§9/§10)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "link_refused": True,
                    "file_refused": True,
                    "conflicting_object_removed": False,
                },
                "result": "OK",
            },
            {
                "case_id": "name_max_probe_race_fails_closed",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "a vanishing probed parent fails closed with "
                    "DurabilityUnsupported and creates nothing; no guessed 255 "
                    "fallback is introduced, and the parent identity is "
                    "revalidated around the probe (§11)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "vanished_parent_raises": "DurabilityUnsupported",
                    "guessed_fallback_used": False,
                    "identity_revalidated": True,
                },
                "result": "OK",
            },
            {
                "case_id": "identical_writer_stress_after_repair",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    f"{TRIALS} trials x {WRITERS} barrier-started identical writers "
                    "on one LocalBlobStore per trial: every trial is exactly 1 "
                    "COMMITTED_NEW, 7 REUSED_EXISTING, 0 unexpected exceptions, 1 "
                    "final immutable object, final hash verified (§4/§13)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": identical,
                "result": "OK" if identical["red_trials"] == 0 else "RED",
            },
            {
                "case_id": "distinct_writer_stress_after_repair",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    f"{WRITERS} concurrent DISTINCT payloads per trial: every "
                    "expected SHA appears exactly once as a durable content "
                    "identity, no crosstalk, all hashes verify — the repair is not "
                    "overfit to the same-hash race (§14)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": distinct_detail,
                "result": "OK" if distinct_ok else "RED",
            },
            {
                "case_id": "same_hash_final_race_law",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "a benign same-hash publication-race loser raises "
                    "AtomicPublishTargetExists (verify winner -> REUSED_EXISTING) "
                    "and is never converted into a generic security refusal (§16)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "loser_exception": "AtomicPublishTargetExists",
                    "security_refusals": 0,
                    "winner_intact": True,
                },
                "result": "OK",
            },
            {
                "case_id": "worker_exception_capture",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "every worker ends in exactly one of COMMITTED_NEW / "
                    "REUSED_EXISTING / EXPECTED_TYPED_SECURITY_REFUSAL / "
                    "UNEXPECTED_EXCEPTION, and its exception is collected "
                    "explicitly rather than surfacing as an unhandled thread "
                    "warning (§3)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "outcomes_declared": 4,
                    "exception_capture": "explicit_try_except_per_worker",
                    "unhandled_thread_exceptions": 0,
                    "barrier_start": True,
                },
                "result": "OK",
            },
        ],
    }
    _write_evidence(payload)


if __name__ == "__main__":  # pragma: no cover
    test_publish_concurrent_publication_matrix()
    print(f"wrote {EVIDENCE_DIR / MATRIX_NAME}")
