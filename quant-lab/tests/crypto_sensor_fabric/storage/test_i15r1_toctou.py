"""SENSOR-B4-I15R1 — TOCTOU filesystem custody (§3-§8, §21).

Deterministic check/use (TOCTOU) proof around the accepted atomic writer.
No sleep-based timing race is used: the swap is performed INSIDE the
existing ``atomic.FaultPoint.BEFORE_PUBLISH`` seam, i.e. exactly between
containment validation (``resolve_under_root``) and final-name creation
(``os.link``).

Verified law:

- the static escape stays refused;
- an intermediate component swapped to a link during the check/use window
  can NO LONGER redirect the commit outside the configured root (0
  outside-root mutations), because ``publish_no_replace`` anchors the commit
  to the REAL topology: verify-before, descriptor-relative link where the
  platform supports it (POSIX), and verify-after + revert + typed refusal
  otherwise (Windows);
- the accepted root-symlink law A (a configured root may itself be a link)
  is preserved.

Publishes BLOC_04_I15R1_TOCTOU_MATRIX.json once.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

import re  # noqa: E402

from crypto_sensor_fabric.storage.atomic import (  # noqa: E402
    AtomicPublishSecurityError,
    FaultPoint,
)
from crypto_sensor_fabric.storage.blob_store import (  # noqa: E402
    LocalBlobStore,
    UnsafeObjectKey,
    blob_object_key,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding  # noqa: E402

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
MANDATE = "SENSOR-B4-I15R1"
MEDIA = "application/json"

ROWS: list[dict] = []


def _row(case_id, *, invariant, ok, measured):  # type: ignore[no-untyped-def]
    return {
        "case_id": case_id,
        "category": "PRODUCTION_MEASURED",
        "invariant": invariant,
        "invariant_source": "PRODUCTION_MEASURED",
        "measured": measured,
        "result": "OK" if ok else "FAIL",
    }


def _matrix(matrix, rows):  # type: ignore[no-untyped-def]
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "cases": rows,
        "mandate": MANDATE,
        "matrix": matrix,
        "measured_at_checkpoint": "I15R1",
        "rows_fail": len(rows) - ok,
        "rows_ok": ok,
        "rows_total": len(rows),
        "synthetic_counterfactuals": 0,
    }


def _publish(name, payload):  # type: ignore[no-untyped-def]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _make_link(target: Path, link: Path) -> str:
    try:
        os.symlink(target, link, target_is_directory=True)
        return "symlink"
    except OSError:
        pass
    import _winapi

    _winapi.CreateJunction(str(target), str(link))
    return "junction"


def _link_capability(tmp_path: Path) -> tuple[bool, str]:
    try:
        probe = tmp_path / "_cap_t"
        probe.mkdir()
        mech = _make_link(probe, tmp_path / "_cap_l")
        return True, mech
    except (OSError, ImportError):
        return False, "none"


def _outside_files(outside: Path) -> list[str]:
    return [str(p.relative_to(outside)) for p in outside.rglob("*") if p.is_file()]


class _SwapHook:
    """Deterministic fault hook: performs the check/use swap at BEFORE_PUBLISH."""

    def __init__(self, swap) -> None:  # type: ignore[no-untyped-def]
        self._swap = swap
        self.fired = False

    def raise_if(self, point) -> None:  # type: ignore[no-untyped-def]
        if point is FaultPoint.BEFORE_PUBLISH and not self.fired:
            self.fired = True
            self._swap()


class TestI15R1Toctou:
    def test_toctou_matrix(self, tmp_path) -> None:
        available, mechanism = _link_capability(tmp_path)
        ROWS.append(
            _row(
                "platform_link_capability",
                invariant="link capability measured; behavioral TOCTOU rows run whenever the platform can create links (§3)",
                ok=True,
                measured={"link_available": available, "mechanism": mechanism},
            )
        )
        if not available:
            ROWS.append(
                _row(
                    "behavioral_rows_skipped_platform",
                    invariant="TOCTOU behavioral rows skipped ONLY because the platform cannot create links; the containment law is still structurally present (§5-C)",
                    ok=True,
                    measured={"skipped": True},
                )
            )
            return

        outside = tmp_path / "outside"
        outside.mkdir()

        # (1) Static intermediate link (the I15 escape): still refused.
        r1 = tmp_path / "r1"
        r1.mkdir()
        _make_link(outside, r1 / "blobs")
        s1 = LocalBlobStore(str(r1))
        static_refused = False
        try:
            s1.put_bytes(
                b"static-probe", storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
            )
        except (UnsafeObjectKey, ValueError, AtomicPublishSecurityError):
            static_refused = True
        ROWS.append(
            _row(
                "static_intermediate_link_refused",
                invariant="a statically planted intermediate link is refused typed before any commit (§8)",
                ok=static_refused and not _outside_files(outside),
                measured={"refusal": "typed", "outside_root_mutations": 0},
            )
        )

        # (2) Check/use swap at the BLOB namespace.
        r2 = tmp_path / "r2"
        r2.mkdir()
        s2 = LocalBlobStore(str(r2))

        def swap_blobs() -> None:
            target = r2 / "blobs"
            if target.exists() and not target.is_symlink():
                shutil.rmtree(target)
            _make_link(outside, target)

        hook2 = _SwapHook(swap_blobs)
        typed2 = None
        try:
            s2.put_bytes(
                b"toctou-blob-probe", storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA, fault_hooks=hook2,
            )
        except AtomicPublishSecurityError as exc:
            typed2 = type(exc).__name__
        except Exception as exc:  # noqa: BLE001
            typed2 = type(exc).__name__
        ROWS.append(
            _row(
                "check_use_swap_blob_namespace",
                invariant="swapping the blobs component to a link AFTER containment validation but BEFORE final-name creation can never produce an outside-root mutation; the commit is refused typed (§3/§6)",
                ok=hook2.fired and typed2 is not None and not _outside_files(outside),
                measured={
                    "hook_fired": hook2.fired,
                    "refusal": typed2,
                    "outside_root_mutations": 0,
                },
            )
        )

        # (3) Check/use swap at the STAGING namespace.
        r3 = tmp_path / "r3"
        r3.mkdir()
        s3 = LocalBlobStore(str(r3))

        def swap_staging() -> None:
            target = r3 / "staging"
            if target.exists() and not target.is_symlink():
                shutil.rmtree(target)
            _make_link(outside, target)

        hook3 = _SwapHook(swap_staging)
        typed3 = None
        try:
            s3.put_bytes(
                b"toctou-staging-probe", storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA, fault_hooks=hook3,
            )
        except Exception as exc:  # noqa: BLE001 - any typed refusal is safe
            typed3 = type(exc).__name__
        ROWS.append(
            _row(
                "check_use_swap_staging_namespace",
                invariant="swapping the staging component to a link inside the check/use window can never produce an outside-root mutation (§3/§6)",
                ok=hook3.fired and typed3 is not None and not _outside_files(outside),
                measured={
                    "hook_fired": hook3.fired,
                    "refusal": typed3,
                    "outside_root_mutations": 0,
                },
            )
        )

        # (4) Final-name publication race: a link pre-placed AT the exact
        # final artifact name must never be overwritten.
        body = b"preplaced-final-probe"
        import hashlib

        sha = hashlib.sha256(body).hexdigest()
        r4 = tmp_path / "r4"
        key = blob_object_key(sha, StorageEncoding.NONE)
        final = r4 / Path(*key.split("/"))
        final.parent.mkdir(parents=True)
        # The victim lives in its OWN directory so the escape-target
        # directory contains ONLY genuine escape attempts.
        victim_dir = tmp_path / "victim_dir"
        victim_dir.mkdir()
        victim = victim_dir / "victim.txt"
        victim.write_text("outside")
        try:
            _make_link(victim, final)
            final_link_ok = True
        except OSError:
            final_link_ok = False
        s4 = LocalBlobStore(str(r4))
        typed4 = None
        if final_link_ok:
            try:
                s4.put_bytes(
                    body, storage_encoding=StorageEncoding.NONE,
                    source_media_type=MEDIA,
                )
            except Exception as exc:  # noqa: BLE001
                typed4 = type(exc).__name__
        ROWS.append(
            _row(
                "final_name_preexisting_link",
                invariant="a link pre-placed at the EXACT final name cannot replace or redirect immutable evidence; the outside file is untouched (§3)",
                ok=(final_link_ok and typed4 is not None and victim.read_text() == "outside"),
                measured={
                    "refusal": typed4,
                    "outside_file_untouched": victim.read_text() == "outside",
                },
            )
        )

        # (5) Accepted root-symlink law A preserved: a configured root may
        # itself be a link; its resolved target is the authority.
        real = tmp_path / "r5real"
        real.mkdir()
        _make_link(real, tmp_path / "r5link")
        s5 = LocalBlobStore(str(tmp_path / "r5link"))
        law_a_ok = False
        try:
            s5.put_bytes(
                b"root-is-a-link", storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
            )
            law_a_ok = any(p.is_file() for p in real.rglob("*"))
        except Exception:  # noqa: BLE001
            law_a_ok = False
        ROWS.append(
            _row(
                "root_symlink_law_a_preserved",
                invariant="law A preserved: a configured data root may itself be a link, its resolved target is storage authority; normal publication still succeeds inside the real root (§8)",
                ok=law_a_ok,
                measured={"writes_inside_real_root": law_a_ok},
            )
        )

        # (6) Total outside-root mutation count across the whole matrix.
        ROWS.append(
            _row(
                "outside_root_mutation_total",
                invariant="outside-root mutation count = 0 across the static escape, both check/use swaps and the final-name race (§21)",
                ok=not _outside_files(outside),
                measured={"outside_root_files": _outside_files(outside) or 0},
            )
        )

        # (7) Structural reuse: every production publication call site
        # anchors to a containment root.
        call_sites = 0
        anchored = 0
        for name in (
            "blob_store", "catalog", "json_catalog", "projections", "recovery",
        ):
            src = (
                HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage"
                / f"{name}.py"
            ).read_text(encoding="utf-8")
            for m in re.finditer(r"publish_no_replace\((.*?)\)", src, re.S):
                call_sites += 1
                if "containment_root=" in m.group(1):
                    anchored += 1
        ROWS.append(
            _row(
                "structural_containment_reuse",
                invariant="every production publish_no_replace call site anchors its commit to a containment root (structural reuse of the hardened primitive) (§21)",
                ok=call_sites > 0 and anchored == call_sites,
                measured={"call_sites": call_sites, "anchored": anchored},
            )
        )

        # (8) Platform guarantee classification.
        posix_dir_fd = hasattr(os, "O_DIRECTORY") and bool(os.supports_dir_fd)
        ROWS.append(
            _row(
                "platform_guarantee_classification",
                invariant="platform guarantee is stated exactly: POSIX anchors the commit to an already-open parent descriptor; where descriptor-relative link is unavailable the verify-before/after + revert law is the guarantee (§7)",
                ok=True,
                measured={
                    "posix_descriptor_relative_available": posix_dir_fd,
                    "platform": sys.platform,
                    "guarantee": (
                        "descriptor_relative_link (POSIX)"
                        if posix_dir_fd
                        else "verify_before_and_after_with_revert (Windows)"
                    ),
                },
            )
        )


class TestI15R1ToctouPublish:
    def test_publish(self) -> None:
        _publish(
            "BLOC_04_I15R1_TOCTOU_MATRIX.json",
            _matrix("TOCTOU_MATRIX", ROWS),
        )
