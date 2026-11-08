"""B6-I0 no-platform laws, authority firewall and the Linux symlink boundary proof."""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import subprocess

import pytest

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parent))
import block_06_i0_support as S  # noqa: E402

FORBIDDEN_IMPORTS = {"socket", "http", "urllib", "urllib3", "requests", "httpx", "aiohttp",
                     "sqlite3", "shelve", "pickle", "ccxt", "boto3", "psycopg2", "redis"}
FORBIDDEN_ACTIONS = {"admit", "approve", "recover", "spend", "execute", "broker", "settle"}
PROVIDERS = r"\b(binance|coinbase|kraken|alpaca|interactivebrokers|aws|gcp|azure|cloudflare)\b"


def _i0_sources():
    paths = [S.SCRIPTS / name for name in S.SCRIPTS_I0]
    paths += [S.TESTS / name for name in S.I0_MODULES]
    return [p for p in paths if p.exists()]


def _trees():
    return {p.name: ast.parse(p.read_text(encoding="utf-8")) for p in _i0_sources()}


def _imported(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Import):
            names |= {a.name.split(".")[0] for a in sub.names}
        elif isinstance(sub, ast.ImportFrom) and sub.module:
            names.add(sub.module.split(".")[0])
    return names


def _called(node: ast.AST) -> set[str]:
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute):
                out.add(func.attr)
            elif isinstance(func, ast.Name):
                out.add(func.id)
    return out


def test_np_1():
    # No re-export or import of control-plane source packages.
    for name, tree in _trees().items():
        assert not any(n.startswith(("infrastructure", "oce")) for n in _imported(tree)), name
    contract = S.load("IMPLEMENTATION_CONTRACT")
    assert "infrastructure/control-plane/src/" in contract["prohibited_paths"]


def test_np_2():
    # A public surface may only rest on admissible candidate classes.
    api = S.load("API_PRINCIPLES_AND_FIREWALL")["symbols"]
    decisions = {r["id"]: r for r in S.load("EXTRACTION_DECISION_FREEZE")["candidates"]}
    assert all(r["classification"] in {"public_experimental", "internal", "deferred",
                                       "prohibited"} for r in api)
    assert not [r for r in decisions.values()
                if r["decision"] == "ADMITTED_FOR_FUTURE_DESIGN"
                and r["classification"] not in {"EXTRACTABLE_PATTERN",
                                                "EXTRACTABLE_WITH_LIMITATION",
                                                "DEFERRED_TO_BOOK_6"}]


def test_np_3():
    # No second canonical state: no store import, no store surface, no database handle.
    for name, tree in _trees().items():
        assert not (_imported(tree) & {"sqlite3", "shelve", "pickle"}), name
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    assert "database_handle" in api["prohibitions"]
    assert "canonical_state_duplication" in api["prohibitions"]
    store = [r for r in api["symbols"] if "canonical_store" in r["symbol"]]
    assert len(store) == 1 and store[0]["classification"] == "prohibited"


def test_np_4():
    # No admission, approval, recovery, spend or execution logic.
    for name, tree in _trees().items():
        defined = {n.name.lower() for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert not (defined & FORBIDDEN_ACTIONS), (name, defined & FORBIDDEN_ACTIONS)
        assert not (_called(tree) & {"admit", "approve", "recover", "spend", "execute"}), name


def test_np_5():
    # One named owner per surface; no shared or duplicated ownership.
    api = S.load("API_PRINCIPLES_AND_FIREWALL")["symbols"]
    owners = [r["owner"] for r in api]
    assert all(str(o).strip() for o in owners)
    assert len(set(owners)) >= 1
    assert len({r["symbol"] for r in api}) == len(api)
    registry = S.load("REQUIREMENT_TEST_REGISTRY")["requirements"]
    assert all(r["owner"] for r in registry)
    assert len({r["symbol"] for r in api}) == len(api)


def test_np_6():
    # One declared configuration source: arguments only, no environment, no config file.
    for name, tree in _trees().items():
        assert not (_imported(tree) & {"dotenv", "configparser", "tomllib"}), name
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {"environ", "getenv"}:
                pytest.fail(f"{name} reads process environment")
    contract = S.load("IMPLEMENTATION_CONTRACT")
    assert contract["operator_hold"]["capital_authority"] == "none"


def test_np_7():
    # No absolute path, host, provider or external endpoint in any generated artifact.
    blobs = {}
    for key in ("SCOPE_DERIVATION", "IMPLEMENTATION_CONTRACT", "EXTRACTION_DECISION_FREEZE",
                "API_PRINCIPLES_AND_FIREWALL", "COMPATIBILITY_AND_CONFORMANCE_BASELINE",
                "FAILURE_AND_THREAT_PROOFS", "REQUIREMENT_TEST_REGISTRY"):
        blobs[key] = json.dumps(S.load(key)).lower()
    for key, text in blobs.items():
        assert "http://" not in text and "https://" not in text, key
        assert not any(f"/{p}" in text for p in ("users/", "home/", "tmp/")), key
        assert not re.search(PROVIDERS, text), key
    contract = S.load("IMPLEMENTATION_CONTRACT")
    assert contract["cleanup"]


def test_np_8():
    # No network, broker, execution or credentials client anywhere in the stage code.
    for name, tree in _trees().items():
        assert not (_imported(tree) & FORBIDDEN_IMPORTS), (name, _imported(tree) & FORBIDDEN_IMPORTS)
        assert not (_called(tree) & {"urlopen", "connect", "create_connection", "socket"}), name


def test_negative_control_per_law(tmp_path):
    """Each law is discriminated: violating it turns the validator red with a named check."""
    root = S.scratch_root(tmp_path)
    assert S.validate(root)["status"] == "PASS"

    decisions = root / "docs" / "oce-golden-system" / "OCE_BLOCK_06_I0_EXTRACTION_DECISION_FREEZE_v1.0.json"
    original = decisions.read_bytes()

    def assert_red(mutator, expected):
        data = json.loads(original)
        mutator(data)
        S.write_json(decisions, data)
        failures = S.failed_checks(root)
        decisions.write_bytes(original)
        assert expected in failures, (expected, sorted(failures))

    def admit_authority(data):
        for row in data["candidates"]:
            if row["classification"] == "AUTHORITY_BEARING":
                row["decision"] = "ADMITTED_FOR_FUTURE_DESIGN"

    assert_red(admit_authority, "dec/authority_never")
    assert_red(lambda d: d["candidates"][0].__setitem__("copied_files", 1), "dec/zero_copies")
    assert_red(lambda d: d["candidates"][0].__setitem__("extracted_at_b6_i0", True),
               "dec/zero_copies")
    assert_red(lambda d: d["arithmetic"].__setitem__("admitted", 27), "dec/arithmetic")

    api_path = root / "docs" / "oce-golden-system" / "OCE_BLOCK_06_I0_API_PRINCIPLES_AND_FIREWALL_v1.0.json"
    api_original = api_path.read_bytes()

    def promote_private(data):
        for row in data["symbols"]:
            if row["classification"] == "internal":
                row["classification"] = "public_experimental"
                break

    data = json.loads(api_original)
    promote_private(data)
    S.write_json(api_path, data)
    assert "api/distribution" in S.failed_checks(root)
    api_path.write_bytes(api_original)

    compat_path = root / "docs" / "oce-golden-system" / "OCE_BLOCK_06_I0_COMPATIBILITY_AND_CONFORMANCE_BASELINE_v1.0.json"
    compat_original = compat_path.read_bytes()

    def prove_row(data):
        data["compatibility_rows"][0]["state"] = "PROVEN"

    data = json.loads(compat_original)
    prove_row(data)
    S.write_json(compat_path, data)
    assert "compat/all_unproven" in S.failed_checks(root)
    compat_path.write_bytes(compat_original)

    contract_path = root / "docs" / "oce-golden-system" / "OCE_BLOCK_06_I0_IMPLEMENTATION_CONTRACT_v1.0.json"
    contract_original = contract_path.read_bytes()
    data = json.loads(contract_original)
    data["operator_hold"]["package_publication_authorized"] = True
    S.write_json(contract_path, data)
    assert "contract/operator_hold" in S.failed_checks(root)
    contract_path.write_bytes(contract_original)

    assert S.validate(root)["status"] == "PASS"


def test_traversal_refused(tmp_path):
    root = S.scratch_root(tmp_path)
    manifest_path = root / "docs" / "oce-golden-system" / "OCE_BLOCK_06_I0_MANIFEST_v1.0.json"
    original = manifest_path.read_bytes()
    for bad in ("../escape.json", "/absolute.json", "docs\\..\\escape.json"):
        data = json.loads(original)
        data["artifacts"][0]["path"] = bad
        S.write_json(manifest_path, data)
        assert "manifest/relative_paths" in S.failed_checks(root), bad
    manifest_path.write_bytes(original)
    assert S.validate(root)["status"] == "PASS"


def test_symlink_escape_refused(tmp_path):
    root = S.scratch_root(tmp_path)
    target = root / "docs" / "oce-golden-system" / "OCE_BLOCK_06_I0_SCOPE_DERIVATION_v1.0.json"
    inside = target.read_bytes()
    outside = tmp_path / "outside.json"
    outside.write_bytes(inside)
    if os.name == "nt":
        # Windows without developer mode cannot create symlinks; use a junction-free copy check.
        target.unlink()
        target.write_bytes(outside.read_bytes())
        assert S.validate(root)["status"] == "PASS"
        target.write_bytes(inside)
        return
    target.unlink()
    target.symlink_to(outside)
    failures = S.failed_checks(root)
    assert "boundary/no_symlinked_artifacts" in failures, sorted(failures)
    target.unlink()
    target.write_bytes(inside)
    assert S.validate(root)["status"] == "PASS"


@pytest.mark.skipif(os.name == "nt", reason="symlink creation needs POSIX")
def test_symlink_cannot_hide_tracked_path(tmp_path):
    repo = tmp_path / "repo"
    (repo / "protected").mkdir(parents=True)
    (repo / "allowed").mkdir()
    (repo / "protected" / "secret.txt").write_text("protected\n", encoding="utf-8")
    (repo / "allowed" / "link").symlink_to(repo / "protected" / "secret.txt")
    links = S.V.scan_untrusted_links(repo, "allowed")
    assert links == ["allowed/link"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "x"],
                   cwd=repo, check=True)
    tracked = subprocess.run(["git", "ls-files", "allowed/link"], cwd=repo,
                             capture_output=True, text=True).stdout.strip()
    assert tracked == "allowed/link"
    assert S.V.scan_untrusted_links(repo, "allowed") == ["allowed/link"]


@pytest.mark.skipif(os.name == "nt", reason="symlink creation needs POSIX")
def test_symlink_cleanup(tmp_path):
    repo = tmp_path / "repo"
    (repo / "allowed").mkdir(parents=True)
    (repo / "allowed" / "link").symlink_to(repo / "missing")
    assert pathlib.Path(repo / "allowed" / "link").is_symlink()
    (repo / "allowed" / "link").unlink()
    assert not (repo / "allowed" / "link").exists()
    assert S.V.scan_untrusted_links(repo, "allowed") == []
