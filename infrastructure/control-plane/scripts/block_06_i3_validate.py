#!/usr/bin/env python3
"""B6-I3 conformance validator: operator truth and authority.

Standard library only, offline, no secret, no network, no wall clock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import block_06_stage_scope as stage_scope  # noqa: E402

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I3_"
BASE_SHA = "018b164f249bbf075334d5d03ad37e80dcbbede0"
BASE_TREE = "65c3713ad70e527a6a5657347c53f8663a2ccb20"
I2_HEAD = "9bf76df45dca676ae7cafc4877f117a7dd64c3d2"
TESTS = "infrastructure/control-plane/tests"
SCRIPTS = "infrastructure/control-plane/scripts"
FORBIDDEN_TOKENS = ("B6_I3_RATIFIED", "B6_I3_MERGED", "MERGE_AUTHORIZED = true",
                    "BOOK_6_COMPLETE = true", "PACKAGE_PUBLISHED")
PROHIBITED = ("packages/", "dist/", "build/", "pyproject.toml", "package.json", "uv.lock",
              "poetry.lock", "infrastructure/control-plane/src/", "infrastructure/console/src/",
              f"{DOCS}/OCE_BLOCK_06_P0_", f"{DOCS}/OCE_BLOCK_06_I0_",
              f"{DOCS}/OCE_BLOCK_06_I1_", f"{DOCS}/OCE_BLOCK_06_I2_",
              "oce/api/", "oce/sdk/", "oce/templates/", "oce/harness/")


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def git(root: pathlib.Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


class Checker:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.checks: list[str] = []
        self.failures: list[str] = []

    def need(self, name: str, ok: bool, detail=None) -> None:
        self.checks.append(name)
        if not ok:
            self.failures.append(f"{name}: {detail}")

    def load(self, name: str) -> dict:
        return json.loads((self.root / DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def check_packet(c: Checker) -> None:
    files = sorted(p.name for p in (c.root / DOCS).glob(f"{PREFIX}*.json"))
    c.need("packet/count", len(files) == 9, files)
    for name in files:
        raw = (c.root / DOCS / name).read_bytes()
        c.need(f"packet/canonical/{name}", raw == canonical(json.loads(raw)))
        c.need(f"packet/lf/{name}", b"\r\n" not in raw and raw.endswith(b"\n"))
    scope = c.load("SCOPE_DERIVATION_v1.0.json")
    contract = c.load("IMPLEMENTATION_CONTRACT_v1.0.json")
    c.need("stage/identity", scope["stage"] == contract["stage"] == "B6-I3")
    c.need("stage/sections", scope["sections"] == ["C2.S1", "C2.S2", "C2.S3"])
    c.need("stage/purpose", scope["purpose"] == "C2 capability, approval and evidence views")
    c.need("stage/surfaces", scope["implementation_surfaces"] == ["operator_surface"])
    c.need("stage/gate", scope["exit_gate"] == "operator truth and authority tests pass")
    c.need("stage/non_goal", scope["non_goals"] == ["incident and cost"])
    c.need("stage/stop", scope["stop_conditions"] == ["stop on self-approval"])
    c.need("stage/base", scope["base_sha"] == contract["base_sha"] == BASE_SHA
           and scope["base_tree"] == contract["base_tree"] == BASE_TREE)
    c.need("contract/frozen", contract["status"] == "FROZEN"
           and contract["frozen_before_results"] is True)
    c.need("contract/floors", contract["implementation_floor"]
           == {"mutations": 6, "source_mutation_floor": 3, "test_nodes": 28})
    c.need("contract/paired", contract["paired_comparison"]
           == {"base_only_expected": 0, "base_sha": BASE_SHA, "common_floor": 208,
               "head_only_expected": 27})
    symbols = {row["symbol"] for row in c.load("OPERATOR_SURFACE_CONTRACT_v1.0.json")["symbols"]}
    c.need("surface/symbols", symbols == {"oce.operator.capability_view",
                                          "oce.operator.approval_inbox", "oce.operator.decide",
                                          "oce.operator.reconcile_chain"})
    sys.path.insert(0, str(c.root))
    from oce.operator import CODES  # noqa: PLC0415
    declared = {row["code"] for row in contract["refusals"]}
    c.need("contract/refusals_bound", declared <= set(CODES), sorted(declared - set(CODES)))
    c.need("contract/refusals_unique", len(declared) == len(contract["refusals"]))


def check_registry(c: Checker) -> None:
    registry = c.load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    nodes = registry["inventory"]["nodes"]
    c.need("registry/total", registry["requirements_total"] == len(nodes) == 28)
    c.need("registry/unique", len(set(nodes)) == 28)
    c.need("registry/modules", len(registry["inventory"]["modules"]) == 4)
    c.need("registry/bindings", {r["binding_node"] for r in registry["requirements"]} == set(nodes))
    c.need("registry/sections", {r["section"] for r in registry["requirements"]}
           == {"C2.S1", "C2.S2", "C2.S3"})
    c.need("registry/no_later", not [n for n in nodes if "i4" in n])
    defined = set()
    for module in sorted((c.root / TESTS).glob("test_block_06_i3_*.py")):
        for line in module.read_text(encoding="utf-8").splitlines():
            if line.startswith("def test_"):
                defined.add(f"{module.name}::{line[4:line.index('(')]}")
    c.need("registry/declared_equals_defined", defined == set(nodes), sorted(defined ^ set(nodes)))
    compat = c.load("COMPATIBILITY_MATRIX_v1.0.json")
    c.need("compat/rows", {row["surface"] for row in compat["rows"]}
           == {"C2.S1", "C2.S2", "C2.S3"})
    c.need("compat/no_silent_latest", compat["refusal"]["silent_latest"] is False)


def check_failures(c: Checker) -> None:
    proofs = c.load("FAILURE_AND_THREAT_PROOFS_v1.0.json")
    nodes = set(c.load("REQUIREMENT_TEST_REGISTRY_v1.0.json")["inventory"]["nodes"])
    c.need("failures/classes", {row["id"] for row in proofs["failure_classes"]}
           == {"F03", "F11", "F23"})
    c.need("failures/bound", all(row["proof_state"] == "BOUND" for row in proofs["failure_classes"]))
    c.need("failures/nodes", all(n in nodes for row in proofs["failure_classes"]
                                 for n in row["nodes"]))
    c.need("threats", {row["id"] for row in proofs["threats"]}
           == {"T02", "T06", "T10", "T13", "T19"})
    c.need("policy", all(proofs["policy"].values()))


def check_registration(c: Checker) -> None:
    registration = c.load("STAGE_SCOPE_REGISTRATION_v1.0.json")
    this = registration["this_stage"]
    c.need("registration/frozen", registration["status"] == "FROZEN"
           and registration["frozen_before_results"] is True)
    c.need("registration/prior", registration["prior_stages"]["B6-I2"]["head"] == I2_HEAD)
    c.need("registration/base", this["base"] == BASE_SHA and this["base_tree"] == BASE_TREE)
    c.need("registration/operator", "oce/operator/" in this["allowed_prefixes"])
    c.need("registration/locks", all(registration["locks"][f"B6-I{i}"] == "LOCKED"
                                     for i in range(4, 10)))
    scope = c.load("SCOPE_DERIVATION_v1.0.json")
    c.need("locks/book6", scope["locks"]["BOOK_6_COMPLETE"] is False)
    c.need("locks/holds", scope["locks"]["MERGE_AUTHORIZED"] is False
           and scope["locks"]["RATIFICATION_AUTHORIZED"] is False)
    c.need("locks/g16", scope["locks"]["G16"] == "OPEN")
    c.need("cost", scope["cost_usd"] == 0 and scope["capital_authority"] == "none")


def check_manifest(c: Checker) -> None:
    manifest = c.load("MANIFEST_v1.0.json")
    c.need("manifest/status", manifest["status"] == "FROZEN")
    c.need("manifest/base", manifest["base_sha"] == BASE_SHA)
    c.need("manifest/totals", manifest["totals"] == {"artifacts": 8, "code": 11},
           manifest["totals"])
    for row in manifest["artifacts"] + manifest["code"]:
        path = c.root / row["path"]
        c.need(f"manifest/exists/{row['path']}", path.is_file())
        if path.is_file():
            data = path.read_bytes()
            c.need(f"manifest/hash/{row['path']}",
                   row["sha256"] == hashlib.sha256(data).hexdigest() and row["bytes"] == len(data))
    c.need("manifest/no_self", all(not row["path"].endswith("MANIFEST_v1.0.json")
                                   for row in manifest["artifacts"]))


def check_boundary(c: Checker) -> None:
    if not (c.root / ".git").exists():
        c.need("boundary/git", False, "not a checkout")
        return
    code, status = git(c.root, "status", "--porcelain")
    c.need("boundary/clean", code == 0 and status == "", status[:300])
    code, out = git(c.root, "diff", "--name-only", f"{BASE_SHA}..HEAD")
    changed = [line for line in out.splitlines() if line.strip()]
    c.need("boundary/changed", bool(changed), changed)
    try:
        resolved = stage_scope.resolve(c.root, "auto")
        c.need("stage/resolver", resolved["mode"] == "i3" and resolved["stage"] == "B6-I3",
               resolved.get("mode"))
        allowed = tuple(resolved["allowed"])
        outside = [p for p in changed if not p.startswith(allowed)]
        c.need("boundary/only_allowed", not outside, outside)
        c.need("boundary/operator", "oce/operator/" in allowed)
    except stage_scope.StageScopeError as exc:
        c.need("stage/resolver", False, f"{exc.check}: {exc.detail}")
    blocked = [p for p in changed if p.startswith(PROHIBITED)]
    c.need("boundary/no_prohibited", not blocked, blocked)
    for label in ("I0", "I1", "I2"):
        code, diff = git(c.root, "diff", "--name-only", f"{I2_HEAD}..HEAD", "--", DOCS)
        frozen = [p for p in diff.splitlines() if f"OCE_BLOCK_06_{label}_" in p]
        c.need(f"boundary/{label}_packet_frozen", not frozen, frozen)
    for rel in (f"{TESTS}/test_block_06_i0_stage_contract.py",
                f"{TESTS}/test_block_06_i1_authority_and_boundary.py"):
        code, _ = git(c.root, "diff", "--quiet", f"{BASE_SHA}..HEAD", "--", rel)
        c.need(f"boundary/prior_test/{rel.rsplit('/', 1)[-1]}", code == 0)
    code, later = git(c.root, "ls-tree", "-r", "--name-only", "HEAD")
    forbidden = [p for p in later.splitlines()
                 if any(f"OCE_BLOCK_06_I{i}_" in p for i in range(4, 10))]
    c.need("boundary/no_later_stage", not forbidden, forbidden)


def check_text(c: Checker) -> None:
    for path in sorted((c.root / DOCS).glob(f"{PREFIX}*")):
        text = path.read_text(encoding="utf-8")
        bad = [token for token in FORBIDDEN_TOKENS if token in text]
        c.need(f"text/no_claim/{path.name}", not bad, bad)
        c.need(f"text/no_abs_path/{path.name}",
               "C:\\" not in text and "/home/" not in text and "/Users/" not in text)
    for module in sorted((c.root / "oce/operator").glob("*.py")):
        text = module.read_text(encoding="utf-8").lower()
        c.need(f"code/no_later/{module.name}",
               "block_06_i4" not in text and "block_06_i5" not in text)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    root = (pathlib.Path(args.root).resolve() if args.root
            else pathlib.Path(__file__).resolve().parents[3])
    c = Checker(root)
    for check in (check_packet, check_registry, check_failures, check_registration,
                  check_manifest, check_boundary, check_text):
        try:
            check(c)
        except Exception as exc:  # a missing artifact is a failure, not a crash
            c.need(f"{check.__name__}/exception", False, repr(exc))
    status = "PASS" if not c.failures else "FAIL"
    doc = {"status": status, "stage": "B6-I3", "checks": len(c.checks),
           "failures": len(c.failures), "detail": c.failures[:12],
           "base_sha": BASE_SHA, "cost_usd": 0, "capital_authority": "none"}
    text = json.dumps(doc, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print("\n".join(f"FAIL {row}" for row in c.failures))
    print(f"{status} {len(c.checks) - len(c.failures)}/{len(c.checks)} checks")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
