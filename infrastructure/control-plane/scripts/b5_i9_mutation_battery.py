#!/usr/bin/env python3
"""B5-I9 mutation battery — the 10 frozen mutations, executed on copies only.

For every mutation in the frozen registry the battery:

1. copies the inputs it needs into a scratch directory outside the repository,
2. records the pre-mutation SHA-256,
3. applies the mutation to the copy,
4. requires the named discriminator invariant to raise,
5. restores the original bytes and verifies byte identity,
6. after all mutations, re-runs every invariant on the pristine copy and requires green.

A mutation that is applied but does not discriminate is reported as a defect and blocks
the stage. The repository is never mutated: the tracked tree is clean before and after.

    python infrastructure/control-plane/scripts/b5_i9_mutation_battery.py --json out.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile

import b5_i9_gate as gate  # noqa: E402


def sha(data):
    return hashlib.sha256(data).hexdigest()


def copy_inputs(destination, repo):
    """Copy the docs directory and the committed packet into an isolated scratch root."""
    destination = pathlib.Path(destination)
    shutil.copytree(repo.docs, destination / gate.DOCS_DIR)
    if repo.packet.exists():
        shutil.copytree(repo.packet, destination / gate.PACKET_DIR)
    return gate.Repo(destination)


def mutate_text(path, old, new):
    body = path.read_bytes().decode("utf-8")
    if old not in body:
        raise RuntimeError("mutation target not present in {}".format(path.name))
    path.write_bytes(body.replace(old, new, 1).encode("utf-8"))


def mutate_json(path, func):
    doc = json.loads(path.read_bytes().decode("utf-8"))
    func(doc)
    path.write_bytes(gate.canon(doc))


def build_mutations(scratch):
    """Ten frozen mutations, each with a real byte-level edit on a scratch copy."""
    registries = scratch.docs / gate.REGISTRY
    boundary = scratch.docs / gate.BOUNDARY
    packet = scratch.packet / "factory-gate-packet.json"

    def m03(doc):  # duplicate one requirement id
        doc["requirements"][1]["id"] = doc["requirements"][0]["id"]

    def m04(doc):  # a PASS claim
        doc["requirements"][2]["state"] = "PASS"

    def m05(doc):  # remove one binding
        doc["requirements"][3]["binding"] = ""

    def m06(doc):  # point at a nonexistent node
        for row in doc["requirements"]:
            if row["binding"] == "test":
                row["node"] = "TestGhost::test_missing"
                break

    def m07(doc):
        doc["base_sha"] = "0" * 40

    def m08(doc):
        doc["packaging"]["owner"] = "C:/scratch/platform"

    def m09(doc):
        doc["locks"]["book_6_authorized"] = True

    def m10(doc):
        doc["locks"]["g16"]["status"] = "CLOSED"

    return [
        ("M01", "test_private_interfaces_never_promoted", "classification copy",
         lambda: mutate_text(boundary, "| `infrastructure/control-plane/src/oce_control/job_store.py`, `infrastructure/control-plane/src/oce_control/worker_leases.py` | `PLATFORM_INTERNAL`",
                             "| `infrastructure/control-plane/src/oce_control/job_store.py`, `infrastructure/control-plane/src/oce_control/worker_leases.py` | `EXTRACTABLE_PATTERN`")),
        ("M02", "test_authority_bearing_items_are_never_extractable", "classification copy",
         lambda: mutate_text(boundary, "| `infrastructure/control-plane/src/oce_control/authority.py` | `AUTHORITY_BEARING`",
                             "| `infrastructure/control-plane/src/oce_control/authority.py` | `EXTRACTABLE_PATTERN`")),
        ("M03", "test_requirement_ids_unique", "registry copy",
         lambda: mutate_json(registries, m03)),
        ("M04", "test_zero_pass_claims", "registry copy",
         lambda: mutate_json(registries, m04)),
        ("M05", "test_every_requirement_has_one_binding", "registry copy",
         lambda: mutate_json(registries, m05)),
        ("M06", "test_every_test_requirement_maps_to_a_planned_node", "registry copy",
         lambda: mutate_json(registries, m06)),
        ("M07", "test_base_sha_is_the_merged_main", "artifact copy",
         lambda: mutate_json(packet, m07)),
        ("M08", "test_no_environment_specific_paths", "artifact copy",
         lambda: mutate_json(packet, m08)),
        ("M09", "test_book6_states_remain_false", "locks copy",
         lambda: mutate_json(registries, m09)),
        ("M10", "test_g16_remains_open_with_owner", "locks copy",
         lambda: mutate_json(registries, m10)),
    ]


def run(repo):
    rows = []
    with tempfile.TemporaryDirectory(prefix="b5i9-mutations-") as tmp:
        scratch = copy_inputs(tmp, repo)
        mutations = build_mutations(scratch)
        for mutation_id, discriminator, target, apply in mutations:
            paths = {p.name: p for p in [scratch.docs / gate.REGISTRY,
                                         scratch.docs / gate.BOUNDARY,
                                         scratch.packet / "factory-gate-packet.json"]}
            before = {name: path.read_bytes() for name, path in paths.items()}
            apply()
            after = {name: path.read_bytes() for name, path in paths.items()}
            changed = [name for name in before if before[name] != after[name]]
            applied = bool(changed)
            observed = None
            red = False
            try:
                gate.CHECKS[discriminator](gate.ctx(scratch))
            except gate.GateViolation as exc:
                red = exc.check == discriminator
                observed = exc.check
            finally:
                for name, path in paths.items():
                    path.write_bytes(before[name])
            restored = {name: path.read_bytes() for name, path in paths.items()}
            exact = all(restored[name] == before[name] for name in before)
            rows.append({
                "id": mutation_id,
                "target": target,
                "discriminator": discriminator,
                "changed_files": changed,
                "applied": applied,
                "pre_sha256": {name: sha(before[name]) for name in sorted(before)},
                "mutated_sha256": {name: sha(after[name]) for name in sorted(after)},
                "observed_check": observed,
                "red": red,
                "restored_byte_exact": exact,
            })
        pristine = gate.run_checks(gate.ctx(scratch))
        pristine_green = all(r["status"] == "PASS" for r in pristine)
        pristine_checks = len(pristine)
    deterministic = gate.diff_packet(repo, repo.packet)
    return {
        "tool": "b5_i9_mutation_battery.py",
        "mutations_total": len(rows),
        "discriminated": sum(1 for r in rows if r["red"]),
        "applied": sum(1 for r in rows if r["applied"]),
        "restored_byte_exact": all(r["restored_byte_exact"] for r in rows),
        "pristine_checks": pristine_checks,
        "pristine_green": pristine_green,
        "packet_deterministic": not deterministic,
        "rows": rows,
        "verdict": "PASS" if (len(rows) == 10
                              and all(r["red"] and r["applied"] and r["restored_byte_exact"] for r in rows)
                              and pristine_green and not deterministic) else "FAIL",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", metavar="PATH", default=None)
    parser.add_argument("--root", default=None)
    args = parser.parse_args(argv)
    result = run(gate.Repo(args.root))
    body = json.dumps(result, indent=2, sort_keys=True)
    if args.json:
        path = pathlib.Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((body + "\n").encode("utf-8"))
    print("B5-I9 mutation battery: {} ({}/{} discriminated, restored={}, pristine={})".format(
        result["verdict"], result["discriminated"], result["mutations_total"],
        result["restored_byte_exact"], result["pristine_green"]))
    if result["verdict"] != "PASS":
        for row in result["rows"]:
            if not (row["red"] and row["applied"] and row["restored_byte_exact"]):
                print("  {} discriminator={} red={} applied={} exact={}".format(
                    row["id"], row["discriminator"], row["red"], row["applied"],
                    row["restored_byte_exact"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
