"""B6-I0 determinism, independent manifest verification and workflow structure."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parent))
import block_06_i0_support as S  # noqa: E402

ARTIFACT_NAMES = {
    "scope": "SCOPE_DERIVATION",
    "contract": "IMPLEMENTATION_CONTRACT",
    "decisions": "EXTRACTION_DECISION_FREEZE",
    "api": "API_PRINCIPLES_AND_FIREWALL",
    "compat": "COMPATIBILITY_AND_CONFORMANCE_BASELINE",
    "failures": "FAILURE_AND_THREAT_PROOFS",
    "registry": "REQUIREMENT_TEST_REGISTRY",
    "manifest": "MANIFEST",
}
ENV_FIELDS = ("timestamp", "generated_at", "hostname", "username", "user", "tmpdir",
              "temp_path", "random_seed")
WORKFLOW = S.ROOT / ".github" / "workflows" / "block-06-i0-validation.yml"


def _emit(dst: pathlib.Path) -> dict:
    out = subprocess.run([sys.executable, str(S.SCRIPTS / "block_06_i0_generate.py"),
                          "--out", str(dst)], cwd=str(S.ROOT), capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-2000:]
    return {p.relative_to(dst).as_posix(): p.read_bytes()
            for p in sorted(dst.rglob("*.json"))}


def test_double_generation_identical(tmp_path):
    first = _emit(tmp_path / "one")
    second = _emit(tmp_path / "two")
    assert set(first) == set(second)
    assert {k.rsplit("/", 1)[-1] for k in first} == {
        f"OCE_BLOCK_06_I0_{n}_v1.0.json" for n in ARTIFACT_NAMES.values()}
    for name in first:
        assert first[name] == second[name], name
    by_name = {k.rsplit("/", 1)[-1]: v for k, v in first.items()}
    for base in ARTIFACT_NAMES.values():
        assert by_name[f"OCE_BLOCK_06_I0_{base}_v1.0.json"] == S.artifact_path(base).read_bytes(), base


def test_manifest_independent_verify():
    manifest = S.load("MANIFEST")
    seen = set()
    for row in manifest["artifacts"]:
        path = S.ROOT / row["path"]
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["sha256"], row["path"]
        assert len(raw) == row["size"], row["path"]
        seen.add(row["path"])
    expected = {S.artifact_path(base).relative_to(S.ROOT).as_posix()
                for key, base in ARTIFACT_NAMES.items() if key != "manifest"}
    assert seen == expected
    assert S.artifact_path("MANIFEST").relative_to(S.ROOT).as_posix() not in seen


def test_no_environment_fields():
    def walk(obj, parent=""):
        found = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ENV_FIELDS and parent not in ("forbidden", "forbidden_fields"):
                    found.append(key)
                if key in ("forbidden", "forbidden_fields", "fields", "required"):
                    continue
                found.extend(walk(value, key))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(walk(item, parent))
        return found

    for name in ARTIFACT_NAMES.values():
        assert walk(S.load(name)) == [], name


def test_canonical_bytes():
    for base in ARTIFACT_NAMES.values():
        raw = S.artifact_path(base).read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        assert raw == (json.dumps(parsed, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        assert raw.endswith(b"\n") and b"\r\n" not in raw


def test_p0_validator_green_at_its_head(tmp_path):
    """The P0 validator is stage-scoped: it is re-run over the unchanged P0 packet.

    Its git checks compare origin/main with the P0 base, which has moved on by design, so the
    packet is copied without a repository and the git layer self-reports as skipped. P0 bytes are
    proven unchanged by test_p0_packet_unchanged, so the content verdict is the recorded one.
    """
    root = tmp_path / "p0"
    shutil.copytree(S.DOCS, root / "docs" / "oce-golden-system")
    S.normalize(root)
    (root / "infrastructure/control-plane/scripts").mkdir(parents=True)
    shutil.copy2(S.SCRIPTS / "block_06_p0_validate.py",
                 root / "infrastructure/control-plane/scripts/block_06_p0_validate.py")
    for rel in ("infrastructure/control-plane/evidence/b5-i9/g16-limitation.json",
                "infrastructure/control-plane/evidence/b5-i9/handoff-input-readiness.json"):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(S.ROOT / rel, dst)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "block_06_p0_validate", root / "infrastructure/control-plane/scripts/block_06_p0_validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checker = module.Checker(root)
    for fn in (module.check_packet_files, module.check_canonical_json,
               module.check_identity_and_locks, module.check_requirements,
               module.check_candidates, module.check_api, module.check_sequence,
               module.check_failures_and_threats, module.check_compat, module.check_handoff,
               module.check_text_hygiene, module.check_secrets_and_urls,
               module.check_docs_tokens, module.check_acceptance_matrix,
               module.check_ratification):
        fn(checker)
    assert checker.failures == [], checker.failures[:5]
    assert len(checker.checks) > 100, len(checker.checks)
    diff = S.git("diff", "--name-only", S.P0_SHA, "--", "docs/oce-golden-system")
    assert [p for p in diff.stdout.splitlines() if "OCE_BLOCK_06_P0_" in p] == []


def test_workflow_present():
    assert WORKFLOW.exists()
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "name: B6-I0 Validation" in text
    assert "pull_request:" in text
    assert "permissions:" in text and "contents: read" in text
    assert "runs-on: ubuntu-latest" in text


def test_pinned_actions():
    text = WORKFLOW.read_text(encoding="utf-8")
    uses = re.findall(r"uses:\s*(\S+)", text)
    assert uses, "no actions referenced"
    for ref in uses:
        assert re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}", ref), ref


def test_no_secrets_or_providers():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "${{ secrets." not in text
    assert "secrets:" not in text
    assert "aws-actions" not in text and "azure/" not in text and "google-github-actions" not in text
    assert "curl " not in text and "wget " not in text
    for pattern in ("AKIA", "sk-", "BEGIN RSA"):
        assert pattern not in text


def test_node_inventory_selected():
    registry = S.load("REQUIREMENT_TEST_REGISTRY")
    text = WORKFLOW.read_text(encoding="utf-8")
    for module in S.I0_MODULES:
        assert module in text, module
    assert "block_06_i0_validate.py" in text
    assert "block_06_i0_mutation_battery.py" in text
    assert "72" in text or "node_total" in text
    assert registry["inventory"]["node_total"] == 72


def test_failure_evidence_uploaded():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "upload-artifact@" in text
    assert "if: always()" in text
    assert "if-no-files-found: error" in text
    assert "retention-days:" in text


def test_linux_symlink_job():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "test_block_06_i0_authority_and_boundary.py" in text
    assert "runs-on: ubuntu-latest" in text
    assert "symlink" in text.lower()
    assert "os.name" not in text
