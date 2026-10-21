"""The negative control: restore the R47 shape and show it IS vulnerable.

A weakened copy reverts TWO things the R48 repair changed:

  1. the record read goes back to a PATHNAME read (`_load_transition_record`);
  2. the one-directory-generation coherence check is removed.

If the control does NOT reproduce the mixed-generation verdict, then the
shipped proof proves nothing -- it would pass for an engine that was never
vulnerable in the first place.
"""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = Path(os.path.abspath(os.path.join(HERE, "..")))
CLI = ROOT / "infrastructure" / "local-ground" / "scripts" / "pg-recovery.py"
TESTS = ROOT / "infrastructure" / "local-ground" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, HERE)

from repro import OPID, build, load, swap_directory  # noqa: E402

NEW_RECORD_READ = """        record_name = _derive_record_coordinate_name(operation_id)
        try:
            record_snapshot = _read_record_snapshot_admitted(
                operation_id, governed, record_name, dir_fd, identity)
            admitted_record = record_snapshot.record
        except (OSError, ValueError, RuntimeError, TypeError,
                _ExecutionAuthorityConflict):
            admitted_record = None
            record_snapshot = RecordSnapshot(
                operation_id=operation_id, transition_dir=governed,
                canonical_path=os.path.join(governed, record_name),
                present=False, governed_device=identity[0],
                governed_inode=identity[1], device=0, inode=0, size=0, mode=0,
                link_count=0, record=None, record_digest=None,
                raw_digest=None, read_error="refused")"""

# R47's exact shape: the record is read by PATHNAME, with no descriptor-relative
# admission and no bundle-level coherence proof.
OLD_RECORD_READ = """        record_name = _derive_record_coordinate_name(operation_id)
        admitted_record = None
        try:
            admitted_record = _load_transition_record(operation_id)
        except (OSError, ValueError, RuntimeError, TypeError):
            admitted_record = None
        record_snapshot = RecordSnapshot(
            operation_id=operation_id, transition_dir=governed,
            canonical_path=os.path.join(governed, record_name),
            present=admitted_record is not None,
            governed_device=identity[0], governed_inode=identity[1],
            device=0, inode=0, size=0, mode=0, link_count=0,
            record=admitted_record,
            record_digest=(_receipt_digest(admitted_record)
                           if isinstance(admitted_record, dict) else None),
            raw_digest=None, read_error=None)"""

COHERENCE_CALL = """        _assert_one_directory_generation(
            operation_id, governed, dir_fd, identity, record_snapshot, selector)
"""


def weakened(tmp_path):
    source = CLI.read_text(encoding="utf-8")
    assert NEW_RECORD_READ in source, "R48R1 record-read anchor missing"
    assert COHERENCE_CALL in source, "R48R1 coherence anchor missing"
    changed = source.replace(NEW_RECORD_READ, OLD_RECORD_READ)
    changed = changed.replace(COHERENCE_CALL, "")
    assert changed != source
    path = tmp_path / "weakened-pg-recovery.py"
    path.write_text(changed, encoding="utf-8")
    return path


def load_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print("=" * 72)
    print("NEGATIVE CONTROL: the R47 shape must still be exploitable")
    print("=" * 72)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw) / "state"
        root.mkdir()
        transitions, promote, _digest = build(root, "PROMOTED", "rollback")
        weak_path = weakened(Path(raw))
        mod = load_path(weak_path, "r48_weak")
        mod._bind_test_recovery_root(str(root))

        real_selector = mod._read_selector_snapshot_admitted
        fired = []

        def swap_then_read(operation_id, governed, name, dir_fd, identity):
            if not fired:
                fired.append(True)
                swap_directory(transitions, OPID, "finalize")
            return real_selector(operation_id, governed, name, dir_fd, identity)

        mod._read_selector_snapshot_admitted = swap_then_read
        try:
            try:
                authority = mod._acquire_recovery_authority(OPID, promote)
                state = (authority.record or {}).get("state")
                transition = (authority.selector.claim or {}).get("transition")
                verdict = "ACQUIRED record_state=%r selector=%r" % (state,
                                                                  transition)
            except Exception as exc:            # noqa: BLE001
                verdict = "FAILED_CLOSED %s: %s" % (type(exc).__name__, exc)
        finally:
            mod._read_selector_snapshot_admitted = real_selector

        print("swap fired                       :", bool(fired))
        print("weakened verdict                 :", verdict)
        mixed = ("ACQUIRED" in verdict and "PROMOTED" in verdict
                 and "finalize" in verdict)
        print("mixed-generation accepted        :", mixed)
        print()
        if mixed:
            print("CONTROL IS SOUND: the R47 shape combines generation A's")
            print("record with generation B's selector, so the shipped")
            print("coherence proof is discriminating.")
            return 0
        print("CONTROL FAILED: the weakened engine did NOT reproduce the")
        print("mixed-generation verdict, so the shipped proof proves nothing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())