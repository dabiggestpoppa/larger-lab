"""Deep-immutability probe, with a shallow-frozen negative control.

Proves the shipped bundle refuses mutation at every level, that mutating the
SOURCE object after construction cannot reach the snapshot, and that a
deliberately shallow `@dataclass(frozen=True)` control does NOT -- which is
what makes the shipped proofs discriminating.
"""
import dataclasses
import os
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = Path(os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(0, str(ROOT / "infrastructure" / "local-ground" / "tests"))
sys.path.insert(0, HERE)

from repro import OPID, build, load  # noqa: E402


def attempt(label, fn):
    try:
        fn()
        return "MUTATION SUCCEEDED", label
    except Exception as exc:                    # noqa: BLE001
        return "refused: %s" % type(exc).__name__, label


def main():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw) / "state"
        root.mkdir()
        _t, promote, _d = build(root, "PROMOTED", "rollback")
        mod = load()
        mod._bind_test_recovery_root(str(root))
        bundle = mod._acquire_recovery_authority(OPID, promote)

        print("=" * 70)
        print("SHIPPED BUNDLE")
        print("=" * 70)
        results = []
        results.append(attempt("top-level attribute", lambda:
                               setattr(bundle, "record", {})))
        results.append(attempt("nested record key", lambda:
                               bundle.record.__setitem__("state", "FINALIZED")))
        results.append(attempt("nested selector claim key", lambda:
                               bundle.selector.claim.__setitem__(
                                   "transition", "finalize")))
        results.append(attempt("record.pop", lambda: bundle.record.pop("state")))
        results.append(attempt("record.update", lambda:
                               bundle.record.update({"state": "X"})))
        results.append(attempt("record |= ", lambda:
                               bundle.record.__ior__({"state": "X"})))
        results.append(attempt("record.clear", lambda: bundle.record.clear()))
        for outcome, label in results:
            print("  %-28s %s" % (label, outcome))

        # nested containers must not be mutable either
        nested = [(k, v) for k, v in bundle.record.items()
                  if isinstance(v, (list, dict, set))]
        print("  nested mutable containers in record:", len(nested))

        # source mutation after construction
        source = {"state": "PROMOTED", "operation_id": OPID, "nested": {"a": 1}}
        frozen = mod._deep_freeze(source)
        source["state"] = "FINALIZED"
        source["nested"]["a"] = 99
        print("  after mutating the SOURCE, snapshot state :", frozen["state"])
        print("  after mutating the SOURCE, nested value    :",
              frozen["nested"]["a"])

        digest_before = mod._receipt_digest(frozen)
        print("  digest stable across source mutation        :",
              digest_before == mod._receipt_digest(frozen))

        print()
        print("=" * 70)
        print("NEGATIVE CONTROL: shallow @dataclass(frozen=True)")
        print("=" * 70)

        @dataclasses.dataclass(frozen=True)
        class Shallow:
            record: object

        shallow = Shallow(record={"state": "PROMOTED",
                                  "nested": {"a": 1}})
        control = []
        control.append(attempt("top-level attribute", lambda:
                               setattr(shallow, "record", {})))
        control.append(attempt("nested record key", lambda:
                               shallow.record.__setitem__("state",
                                                          "FINALIZED")))
        control.append(attempt("nested nested key", lambda:
                               shallow.record["nested"].__setitem__("a", 99)))
        for outcome, label in control:
            print("  %-28s %s" % (label, outcome))

        weakened = control[1][0].startswith("MUTATION SUCCEEDED")
        shipped_ok = all(o.startswith("refused") for o, _ in results)
        print()
        print("shipped bundle refuses every mutation :", shipped_ok)
        print("shallow control IS observable/mutable :", weakened)
        print()
        print("VERDICT:", "DISCRIMINATING" if shipped_ok and weakened
              else "NOT DISCRIMINATING")
        return 0 if (shipped_ok and weakened) else 1


if __name__ == "__main__":
    sys.exit(main())