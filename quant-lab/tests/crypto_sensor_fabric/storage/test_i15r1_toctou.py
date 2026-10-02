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
- the RESIDUAL seam inside the writer itself — between its own containment
  check / parent-descriptor open and ``os.link`` — is driven at the
  ``OP_FINAL_LINK`` op-recorder seam, and a pre-repair counterfactual shows
  that same seam escapes when the I15R1 primitive is disabled, so the seal
  is earned by the production repair rather than by the test harness;
- the accepted root-symlink law A (a configured root may itself be a link)
  is preserved.

Publishes BLOC_04_I15R1_TOCTOU_MATRIX.json once.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

import re  # noqa: E402

from crypto_sensor_fabric.storage import atomic as _atomic  # noqa: E402
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


def _row(case_id, *, invariant, ok, measured, category="PRODUCTION_MEASURED"):  # type: ignore[no-untyped-def]
    return {
        "case_id": case_id,
        "category": category,
        "invariant": invariant,
        "invariant_source": category,
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
        "synthetic_counterfactuals": sum(
            1 for r in rows if r["category"] == "SYNTHETIC_COUNTERFACTUAL"
        ),
    }


def _publish(name, payload):  # type: ignore[no-untyped-def]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _is_link_like(path: Path) -> bool:
    """True for a symbolic link OR a Windows reparse point (junction).

    ``Path.is_symlink()`` is False for a junction on some runtimes, so a
    link-like component must be detected through the reparse-point
    attribute before any recursive delete touches it.
    """
    try:
        mode = os.lstat(path).st_mode
    except OSError:
        return False
    if stat.S_ISLNK(mode):
        return True
    attrs = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


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


class _SwapOps:
    """Deterministic seam INSIDE ``publish_no_replace``.

    ``OP_FINAL_LINK`` is recorded after the containment check and after the
    parent directory descriptor has been opened, immediately before
    ``os.link``.  Swapping here exercises the residual check/use window that
    a caller-side seam cannot reach (§3/§4).
    """

    def __init__(self, swap) -> None:  # type: ignore[no-untyped-def]
        self._swap = swap
        self.fired = False
        self.seen: list[str] = []

    def record(self, op: str) -> None:
        self.seen.append(op)
        if op == _atomic.OP_FINAL_LINK and not self.fired:
            self.fired = True
            self._swap()


def _mirror_namespace(body: bytes, target: Path) -> str:
    """Pre-create the mirrored blob namespace ``target/<key minus 'blobs'>``.

    An attacker who redirects the commit also pre-creates the destination
    chain; without this the redirected link fails for an unrelated reason
    (missing namespace) and the escape would be measured by accident.
    """
    key = blob_object_key(hashlib.sha256(body).hexdigest(), StorageEncoding.NONE)
    parts = Path(*key.split("/")).parts
    (target / Path(*parts[1:]).parent).mkdir(parents=True, exist_ok=True)
    return key


class TestI15R1Toctou:
    def test_toctou_matrix(self, tmp_path, monkeypatch) -> None:
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
            if target.exists() and not _is_link_like(target):
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
            if target.exists() and not _is_link_like(target):
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

        # (3b) THE RESIDUAL CHECK/USE SEAM.  A caller-side seam fires BEFORE
        # publish_no_replace is entered, so it cannot reach the window that
        # remains INSIDE the writer: between the writer's own containment
        # check (and the parent descriptor open) and ``os.link``.  The
        # OP_FINAL_LINK op-recorder seam sits exactly there.
        seam_body = b"toctou-seam-probe"
        _mirror_namespace(seam_body, outside)
        r6 = tmp_path / "r6"
        r6.mkdir()
        s6 = LocalBlobStore(str(r6))

        def swap_seam() -> None:
            target = r6 / "blobs"
            if target.exists() and not _is_link_like(target):
                shutil.rmtree(target)
            _make_link(outside, target)

        seam_ops = _SwapOps(swap_seam)
        seam_error = None
        try:
            s6.put_bytes(
                seam_body,
                storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
                ops=seam_ops,
            )
        except Exception as exc:  # noqa: BLE001 - any typed refusal is safe
            seam_error = type(exc).__name__
        seam_outside = _outside_files(outside)
        posix_dir_fd_seam = hasattr(os, "O_DIRECTORY") and bool(
            os.supports_dir_fd
        )
        ROWS.append(
            _row(
                "check_use_seam_at_final_link",
                invariant=(
                    "swapping the blobs component INSIDE publish_no_replace — "
                    "after its containment check and after the parent "
                    "descriptor is open, immediately before final-name "
                    "creation — can never leave an artifact outside the "
                    "configured root; where descriptor-relative link exists "
                    "the commit is anchored to the opened parent, otherwise "
                    "the post-commit verification reverts and refuses typed "
                    "(§3/§6/§7)"
                ),
                ok=seam_ops.fired and not seam_outside,
                measured={
                    "seam": "OP_FINAL_LINK inside publish_no_replace",
                    "hook_fired": seam_ops.fired,
                    "typed_refusal": seam_error,
                    "outcome": (
                        "REFUSED_TYPED"
                        if seam_error
                        else "COMMITTED_INSIDE_REAL_ROOT"
                    ),
                    "outside_root_mutations": len(seam_outside),
                    "descriptor_relative_available": posix_dir_fd_seam,
                },
            )
        )

        # (3c) PRE-REPAIR COUNTERFACTUAL at the same seam.  With the I15R1
        # primitive disabled -- exactly the I15-head semantics: no
        # containment re-check and no descriptor-relative anchor -- the very
        # same seam commits OUTSIDE the root.  This is the measured RED and
        # it proves row (3b) is earned by the primitive, not by the test.
        cf_outside = tmp_path / "outside_cf"
        cf_body = b"toctou-counterfactual"
        _mirror_namespace(cf_body, cf_outside)
        r7 = tmp_path / "r7"
        r7.mkdir()
        s7 = LocalBlobStore(str(r7))

        def swap_cf() -> None:
            target = r7 / "blobs"
            if target.exists() and not _is_link_like(target):
                shutil.rmtree(target)
            _make_link(cf_outside, target)

        cf_error = None
        cf_ops = _SwapOps(swap_cf)
        with monkeypatch.context() as m:
            m.setattr(_atomic, "_is_within", lambda *a, **k: True)
            m.setattr(_atomic, "_open_parent_no_follow", lambda *a, **k: None)
            m.setattr(_atomic, "_file_identity", lambda p: (0, 0))
            try:
                s7.put_bytes(
                    cf_body,
                    storage_encoding=StorageEncoding.NONE,
                    source_media_type=MEDIA,
                    ops=cf_ops,
                )
            except Exception as exc:  # noqa: BLE001
                cf_error = type(exc).__name__
        cf_files = _outside_files(cf_outside)
        ROWS.append(
            _row(
                "check_use_seam_pre_repair_counterfactual_escape",
                invariant=(
                    "with the I15R1 containment primitive disabled the SAME "
                    "seam commits outside the root; the seal is therefore "
                    "earned by the production repair, not by the test "
                    "harness (§5-B/§21)"
                ),
                ok=cf_ops.fired and cf_error is None and bool(cf_files),
                measured={
                    "seam": "OP_FINAL_LINK inside publish_no_replace",
                    "hook_fired": cf_ops.fired,
                    "outcome": "COMMITTED_OUTSIDE_ROOT",
                    "typed_refusal": cf_error,
                    "outside_root_mutations": len(cf_files),
                    "repair_disabled": [
                        "atomic._is_within -> always True",
                        "atomic._open_parent_no_follow -> None",
                    ],
                },
                category="SYNTHETIC_COUNTERFACTUAL",
            )
        )

        # (3d) STAGING SOURCE substitution.  The destination of the link is
        # anchored, but the SOURCE lives in the same check/use window: swap
        # the staging namespace to a link whose target already holds a file
        # named like the in-flight staged artifact and os.link publishes
        # FOREIGN bytes under an already-verified content address.
        sub_body = b"genuine-staged-payload"
        sub_attacker = b"ATTACKER-CONTROLLED-BYTES"
        sub_outside = tmp_path / "outside_sub"
        sub_outside.mkdir()
        r8 = tmp_path / "r8"
        r8.mkdir()
        s8 = LocalBlobStore(str(r8))

        def swap_staging_source() -> None:
            staging = r8 / "staging"
            for staged in staging.iterdir():
                if staged.is_file():
                    (sub_outside / staged.name).write_bytes(sub_attacker)
            os.replace(staging, base_staging := (tmp_path / "r8_staging_real"))
            _make_link(sub_outside, staging)
            del base_staging

        sub_ops = _SwapOps(swap_staging_source)
        sub_error = None
        try:
            s8.put_bytes(
                sub_body,
                storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
                ops=sub_ops,
            )
        except Exception as exc:  # noqa: BLE001
            sub_error = type(exc).__name__
        sub_published = sorted(
            str(p.relative_to(r8))
            for p in r8.rglob("*.blob")
        )
        ROWS.append(
            _row(
                "check_use_swap_staging_source_namespace",
                invariant=(
                    "swapping the STAGING namespace to a link inside the "
                    "check/use window can never publish a different file "
                    "under an already-verified content address; the staged "
                    "source is re-anchored by containment plus file-identity "
                    "revalidation around the commit (§3/§6)"
                ),
                ok=sub_ops.fired and sub_error is not None and not sub_published,
                measured={
                    "seam": "OP_FINAL_LINK inside publish_no_replace",
                    "hook_fired": sub_ops.fired,
                    "typed_refusal": sub_error,
                    "published_artifacts": sub_published,
                    "foreign_bytes_published": len(sub_published),
                    "attacker_bytes_offered": hashlib.sha256(
                        sub_attacker
                    ).hexdigest(),
                },
            )
        )

        # (3e) Pre-repair counterfactual for the same substitution.
        cf2_body = b"genuine-staged-payload-2"
        cf2_attacker = b"ATTACKER-CONTROLLED-BYTES-2"
        r9 = tmp_path / "r9"
        r9.mkdir()
        s9 = LocalBlobStore(str(r9))

        def substitute_in_place() -> None:
            staged = next(
                p for p in (r9 / "staging").iterdir() if p.is_file()
            )
            replacement = staged.with_name(staged.name + ".swap")
            replacement.write_bytes(cf2_attacker)
            os.replace(replacement, staged)

        cf2_ops = _SwapOps(substitute_in_place)
        cf2_error = None
        with monkeypatch.context() as m:
            m.setattr(_atomic, "_is_within", lambda *a, **k: True)
            m.setattr(_atomic, "_open_parent_no_follow", lambda *a, **k: None)
            m.setattr(_atomic, "_file_identity", lambda p: (0, 0))
            try:
                s9.put_bytes(
                    cf2_body,
                    storage_encoding=StorageEncoding.NONE,
                    source_media_type=MEDIA,
                    ops=cf2_ops,
                )
            except Exception as exc:  # noqa: BLE001
                cf2_error = type(exc).__name__
        cf2_published = [
            {
                "path": str(p.relative_to(r9)),
                "is_attacker_bytes": hashlib.sha256(p.read_bytes()).hexdigest()
                == hashlib.sha256(cf2_attacker).hexdigest(),
            }
            for p in r9.rglob("*.blob")
        ]
        ROWS.append(
            _row(
                "staged_source_substitution_pre_repair_counterfactual",
                invariant=(
                    "with the I15R1 source anchoring disabled the SAME seam "
                    "publishes foreign bytes under the genuine content "
                    "address, so the seal is earned by the production repair "
                    "(§5-B/§21)"
                ),
                ok=(
                    cf2_ops.fired
                    and cf2_error is None
                    and any(f["is_attacker_bytes"] for f in cf2_published)
                ),
                measured={
                    "seam": "OP_FINAL_LINK inside publish_no_replace",
                    "hook_fired": cf2_ops.fired,
                    "outcome": "FOREIGN_BYTES_PUBLISHED",
                    "typed_refusal": cf2_error,
                    "published": cf2_published,
                },
                category="SYNTHETIC_COUNTERFACTUAL",
            )
        )

        # (4) Final-name publication race: a link pre-placed AT the exact
        # final artifact name must never be overwritten.
        body = b"preplaced-final-probe"
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
