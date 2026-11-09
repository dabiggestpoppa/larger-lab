#!/usr/bin/env python3
"""B6-I1 conformance validator.

Checks the frozen packet, the API/SDK contract, the compatibility window, the registry, the
manifest, the changed-file boundary and the stage locks. Standard library only, offline.

Usage:
  python infrastructure/control-plane/scripts/block_06_i1_validate.py
  python infrastructure/control-plane/scripts/block_06_i1_validate.py --json out.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

DOCS = "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I1_"
BASE_SHA = "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e"
BASE_TREE = "3c2e2a6676e16415a1e2bd326c1fc147e51c2a6d"
TESTS = "infrastructure/control-plane/tests"
AMENDMENT_DOC = f"{DOCS}/OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json"
AMENDMENT_SURFACES = (
    AMENDMENT_DOC,
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    f"{TESTS}/block_06_i0_support.py",
    f"{TESTS}/test_block_06_i0_stage_contract.py",
    f"{TESTS}/stage_scope/test_i0_stage_scope_amendment_controls.py",
    f"{TESTS}/test_block_06_i0_book5_regression.py",
    ".github/workflows/block-06-i0-validation.yml",
)
ALLOWED_PREFIXES = (
    f"{DOCS}/{PREFIX}",
    "infrastructure/control-plane/scripts/block_06_i1_",
    f"{TESTS}/test_block_06_i1_",
    f"{TESTS}/block_06_i1_support.py",
    ".github/workflows/block-06-i1-validation.yml",
    ".github/workflows/block-06-i1-paired-comparison.yml",
    "oce/api/", "oce/sdk/", "oce/compat/",
) + AMENDMENT_SURFACES
FORBIDDEN_PREFIXES = (
    "packages/", "dist/", "build/", "pyproject.toml", "uv.lock", "poetry.lock", "package.json",
    "infrastructure/control-plane/src/", "infrastructure/console/src/",
    f"{DOCS}/OCE_BLOCK_06_P0_", f"{DOCS}/OCE_BLOCK_06_I0_",
)
FORBIDDEN_TOKENS = ("B6_I1_RATIFIED", "B6_I1_MERGED", "PACKAGE_PUBLISHED",
                    "BOOK_6_COMPLETE = true", "MERGE_AUTHORIZED = true")
LEDGER_TOKENS = ("B6I1", "G16", "B5I8-DF05", "PASS", "READY_FOR_OPERATOR_REVIEW",
                 "NOT MERGE AUTHORIZED")


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def git(root: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True).stdout.strip()


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
    c.need("packet/present", len(files) >= 7, files)
    for name in files:
        raw = (c.root / DOCS / name).read_bytes()
        c.need(f"packet/canonical/{name}", raw == canonical(json.loads(raw)))
        c.need(f"packet/lf/{name}", b"\r\n" not in raw and raw.endswith(b"\n"))
    scope = c.load("SCOPE_DERIVATION_v1.0.json")
    contract = c.load("IMPLEMENTATION_CONTRACT_v1.0.json")
    c.need("stage/identity", scope["identity"]["stage_name"] == "C1 API and SDK")
    c.need("stage/sections", scope["identity"]["sections"] == ["C1.S1", "C1.S2"])
    c.need("stage/surfaces", scope["identity"]["surfaces"] == ["api", "sdk"])
    c.need("stage/gate", scope["identity"]["gate"] == "canonical path and compatibility pass")
    c.need("stage/no_extraction", scope["identity"]["authorizes_source_extraction"] is False)
    c.need("stage/no_packaging", scope["identity"]["authorizes_packaging"] is False)
    c.need("stage/no_publication", scope["identity"]["authorizes_publication"] is False)
    c.need("stage/non_goal_templates", "templates" in scope["non_goals"])
    c.need("stage/base", scope["base_sha"] == BASE_SHA and scope["base_tree"] == BASE_TREE)
    c.need("contract/frozen", contract["status"] == "FROZEN"
           and contract["frozen_before_results"] is True)
    c.need("contract/floors", contract["implementation_floor"]["test_nodes"] == 42
           and contract["implementation_floor"]["mutations"] == 6
           and contract["implementation_floor"]["source_mutation_floor"] == 3)
    c.need("contract/version", contract["api_version"] == "v1" and contract["path_versioned"])
    c.need("contract/scope_set", set(contract["scopes"]["declared"]) == {"read", "propose", "decide"}
           and contract["scopes"]["wildcard"] is False
           and contract["scopes"]["client_supplied_authority"] is False)
    c.need("contract/no_stable", contract["public_stable"] == 0)
    c.need("contract/holds", contract["locks"]["MERGE_AUTHORIZED"] is False
           and contract["locks"]["RATIFICATION_AUTHORIZED"] is False
           and contract["locks"]["BOOK_6_COMPLETE"] is False)
    c.need("contract/g16", contract["locks"]["G16"] == "OPEN")
    c.need("contract/cost", contract["cost_usd"] == 0
           and contract["capital_authority"] == "none")


def check_api(c: Checker) -> None:
    api = c.load("API_AND_SDK_CONTRACT_v1.0.json")
    ops = api["operations"]
    c.need("api/operations", len(ops) == 10)
    symbols = [row["symbol"] for row in ops]
    c.need("api/unique_symbols", len(symbols) == len(set(symbols)))
    firewall = json.loads((c.root / DOCS / "OCE_BLOCK_06_P0_PUBLIC_PRIVATE_API_FIREWALL_v1.0.json")
                          .read_text(encoding="utf-8"))
    reserved = {row["symbol"] for row in firewall["symbols"]
                if row.get("version_introduced") == "B6-I1"}
    c.need("api/firewall_symbols", reserved <= set(symbols), sorted(reserved - set(symbols)))
    for row in ops:
        c.need(f"api/scope/{row['symbol']}", row["scope_required"] in ("read", "propose", "decide"))
        c.need(f"api/typed/{row['symbol']}", isinstance(row["typed_outputs"], list)
               and bool(row["typed_outputs"]))
        c.need(f"api/classification/{row['symbol']}",
               row["classification"] == "public_experimental")
    c.need("api/deny_by_default", api["deny_by_default"] is True)
    c.need("api/no_secret", any("secret" in p for p in api["prohibitions"]))
    c.need("api/in_process", "in-process" in api["transport"])
    c.need("api/sdk_single_path", api["sdk"]["invokes"].startswith("the canonical dispatcher"))


def check_compat(c: Checker) -> None:
    compat = c.load("COMPATIBILITY_MATRIX_v1.0.json")
    c.need("compat/window", compat["supported_window"]["min"] == "v1"
           and compat["supported_window"]["max"] == "v1")
    c.need("compat/rows", len(compat["rows"]) == 3
           and {r["section"] for r in compat["rows"]} == {"C1.S1", "C1.S2", "C1.S5"})
    c.need("compat/proven", all(r["state"] == "PROVEN" for r in compat["rows"]))
    c.need("compat/unknown_refused", compat["refusal"]["unknown_version"] == "REFUSED")
    c.need("compat/unsupported_refused", compat["refusal"]["unsupported_version"] == "REFUSED")
    c.need("compat/no_silent_latest", compat["refusal"]["silent_latest"] is False)
    rest = compat["unproven_elsewhere"]
    c.need("compat/remaining_unproven",
           rest["block_6_sections_total"] == 25 and rest["proven_in_this_stage"] == 3)


def check_registry(c: Checker) -> None:
    registry = c.load("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    c.need("registry/requirements", registry["requirements_total"] == 12)
    c.need("registry/sections", {r["section"] for r in registry["requirements"]}
           == {"C1.S1", "C1.S2", "C1.S5"})
    c.need("registry/modules", len(registry["inventory"]["modules"]) == 6)
    c.need("registry/nodes", registry["inventory"]["expected_nodes"] == 42)
    c.need("registry/mutation_floor", registry["mutation_floor"] == {"source": 3, "stage": 6})
    c.need("registry/threats", {t["id"] for t in registry["threats"]}
           == {"T04", "T05", "T07", "T08", "T09", "T14", "T20"})
    c.need("registry/failures", registry["failure_classes"]
           == ["F05", "F06", "F07", "F08", "F09", "F10"])


def check_failures(c: Checker) -> None:
    proofs = c.load("FAILURE_AND_THREAT_PROOFS_v1.0.json")
    classes = {row["id"] for row in proofs["classes"]}
    c.need("failures/classes", {"F07", "F09", "F10"} <= classes)
    c.need("failures/bound", all(row["bound"] for row in proofs["classes"]))
    c.need("failures/controls", len(proofs["negative_controls"]) >= 6)
    c.need("failures/threats", len(proofs["threat_controls"]) == 7)


def check_manifest(c: Checker) -> None:
    manifest = c.load("MANIFEST_v1.0.json")
    c.need("manifest/status", manifest["status"] == "FROZEN")
    c.need("manifest/entries", len(manifest["artifacts"]) >= 6)
    for row in manifest["artifacts"] + manifest.get("code", []):
        path = c.root / row["path"]
        c.need(f"manifest/exists/{row['path']}", path.exists())
        if path.exists():
            data = path.read_bytes()
            c.need(f"manifest/hash/{row['path']}",
                   row["sha256"] == hashlib.sha256(data).hexdigest() and row["bytes"] == len(data))


def check_boundary(c: Checker) -> None:
    changed = [p for p in git(c.root, "diff", "--name-only", f"{BASE_SHA}..HEAD").splitlines() if p]
    c.need("boundary/changed", bool(changed), changed)
    outside = [p for p in changed if not p.startswith(ALLOWED_PREFIXES)]
    c.need("boundary/only_allowed_paths", not outside, outside)
    blocked = [p for p in changed
               if p.startswith(FORBIDDEN_PREFIXES) and p not in AMENDMENT_SURFACES]
    c.need("boundary/no_prohibited_surface", not blocked, blocked)
    c.need("boundary/p0_untouched",
           not [p for p in changed
                if (f"{DOCS}/OCE_BLOCK_06_P0_" in p
                    or (f"{DOCS}/OCE_BLOCK_06_I0_" in p and p not in AMENDMENT_SURFACES))])
    c.need("boundary/no_dependency", not [p for p in changed
                                          if p in ("pyproject.toml", "uv.lock", "package.json")])


def check_locks_and_text(c: Checker) -> None:
    ledger = (c.root / DOCS / f"{PREFIX}PROGRESS_EVIDENCE_LEDGER_v1.0.md").read_text(encoding="utf-8")
    for token in LEDGER_TOKENS:
        c.need(f"ledger/token/{token}", token in ledger)
    scope = c.load("SCOPE_DERIVATION_v1.0.json")
    for stage in ("B6-I2", "B6-I3", "B6-I4", "B6-I5", "B6-I6", "B6-I7", "B6-I8", "B6-I9"):
        c.need(f"locks/{stage}", scope["locks"][stage] == "LOCKED")
    c.need("locks/book6", scope["locks"]["BOOK_6_COMPLETE"] is False)
    c.need("locks/g16", scope["locks"]["G16"] == "OPEN"
           and scope["locks"]["G16_OWNER"] == "B5I8-DF05")
    c.need("locks/evaluation", scope["locks"]["evaluation_system"] == "RESERVED_NOT_AUTHORIZED")
    c.need("locks/cost", scope["cost_usd"] == 0 and scope["capital_authority"] == "none")
    for path in sorted((c.root / DOCS).glob(f"{PREFIX}*")):
        text = path.read_text(encoding="utf-8")
        bad = [t for t in FORBIDDEN_TOKENS if t in text]
        c.need(f"text/no_claim/{path.name}", not bad, bad)
        c.need(f"text/no_abs_path/{path.name}", "C:\\" not in text and "/home/" not in text)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve() if args.root else pathlib.Path(__file__).resolve().parents[3]
    c = Checker(root)
    for check in (check_packet, check_api, check_compat, check_registry, check_failures,
                  check_manifest, check_boundary, check_locks_and_text):
        try:
            check(c)
        except Exception as exc:  # a missing artifact is a failure, not a crash
            c.need(f"{check.__name__}/exception", False, repr(exc))
    status = "PASS" if not c.failures else "FAIL"
    doc = {"status": status, "checks": len(c.checks), "failures": len(c.failures),
           "detail": c.failures[:10], "root": str(root)}
    text = json.dumps(doc, sort_keys=True, indent=2) + "\n"
    if args.json:
        pathlib.Path(args.json).write_text(text, encoding="utf-8", newline="\n")
    print("\n".join(f"FAIL {f}" for f in c.failures))
    print(f"{status} {len(c.checks) - len(c.failures)}/{len(c.checks)} checks")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
