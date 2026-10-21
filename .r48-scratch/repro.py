"""Direct reproduction of the post-R47 authority-coherence defect.

Builds a governed transitions directory, then forces a WHOLE-DIRECTORY
replacement to land between the record read and the selector read. The shipped
implementation must either stay pinned to the original generation or fail
closed. A deliberately weakened, pathname-record implementation must reproduce
the mixed-generation verdict.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
CLI = ROOT / "infrastructure" / "local-ground" / "scripts" / "pg-recovery.py"
TESTS = ROOT / "infrastructure" / "local-ground" / "tests"
sys.path.insert(0, str(TESTS))

OPID = "a" * 32
FOREIGN = "b" * 64


def load():
    spec = importlib.util.spec_from_file_location("r48_probe", CLI)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(root, state, transition, opid=OPID):
    transitions = root / "transitions"
    transitions.mkdir(parents=True, exist_ok=True)
    os.chmod(transitions, 0o700)
    promote = {
        "format": "oce-pg-recovery-receipt-v1",
        "operation_phase": "promote",
        "exit_status": 0,
        "promoted": True,
        "operation_id": opid,
        "database": "app", "user": "oce", "container": "oce-pg",
        "run_id": "run-1", "stamp": "abc123abc123",
        "quarantine_database": "q_db", "staging_database": "s_db",
        "source_commit": "c" * 40, "source_tree": "d" * 40,
        "source_archive_sha256": "e" * 64, "inventory_sha256": "f" * 64,
    }
    canonical = json.dumps(promote, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    record = {"format": "oce-pg-recovery-transition-v1", "state": state,
              "operation_id": opid, "receipt_sha256": digest,
              "selected_transition": "rollback"}
    (transitions / f"{opid}.json").write_text(json.dumps(record, indent=2),
                                              encoding="utf-8")
    os.chmod(transitions / f"{opid}.json", 0o600)
    if transition:
        claim = {"format": "oce-pg-recovery-claim-v1", "operation_id": opid,
                 "transition": transition, "receipt_sha256": digest}
        (transitions / f"{opid}.claim").write_text(json.dumps(claim),
                                                    encoding="utf-8")
        os.chmod(transitions / f"{opid}.claim", 0o600)
    receipt = root / "promote-receipt.json"
    receipt.write_text(json.dumps(promote, indent=2), encoding="utf-8")
    os.chmod(receipt, 0o600)
    return transitions, promote, digest


def swap_directory(transitions, opid, new_transition):
    """Rename the whole governed directory aside and build a fresh one."""
    generation = root_counter(transitions)
    aside = transitions.with_name(transitions.name + ".old-%d" % generation)
    os.rename(transitions, aside)
    fresh = transitions
    fresh.mkdir(mode=0o700)
    # the replacement generation carries a DIFFERENT selector
    digest = json.loads((aside / ("%s.json" % opid)).read_text())["receipt_sha256"]
    claim = {"format": "oce-pg-recovery-claim-v1", "operation_id": opid,
             "transition": new_transition, "receipt_sha256": digest}
    (fresh / ("%s.claim" % opid)).write_text(json.dumps(claim),
                                             encoding="utf-8")
    os.chmod(fresh / ("%s.claim" % opid), 0o600)
    shutil.rmtree(aside, ignore_errors=True)
    return fresh


_COUNTER = [0]


def root_counter(_t):
    _COUNTER[0] += 1
    return _COUNTER[0]


def main():
    print("=" * 72)
    print("ATTACK: whole-directory replacement between the record and selector")
    print("=" * 72)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw) / "state"
        root.mkdir()
        transitions, promote, digest = build(root, "PROMOTED", "rollback")
        mod = load()
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
                verdict = ("ACQUIRED record_state=%r selector=%r"
                           % ((authority.record or {}).get("state"),
                              (authority.selector.claim or {}).get("transition")))
            except Exception as exc:            # noqa: BLE001 - shape probe
                verdict = "FAILED_CLOSED %s: %s" % (type(exc).__name__, exc)
        finally:
            mod._read_selector_snapshot_admitted = real_selector

        print("swap fired                    :", bool(fired))
        print("shipped verdict               :", verdict)
        mixed = ("ACQUIRED" in str(verdict)
                 and "PROMOTED" in str(verdict)
                 and "finalize" in str(verdict))
        print("mixed-generation accepted     :", mixed)
        print()
        print("VERDICT: shipped engine is", "STILL VULNERABLE"
              if mixed else "COHERENT (pinned or fail-closed)")
        return 1 if mixed else 0


if __name__ == "__main__":
    sys.exit(main())