#!/usr/bin/env python3
"""
OCE Cloud Ground — Validation Engine
B1-I1R3F — External RUN_ID and Shared-Runner Truth Repair
Version: 3.6.0

One authoritative OCE_RUN_ID per execution, supplied externally.
One final evidence directory. Correct test classification.
Fail-closed meta-test evidence. Shared local and CI runner.

The engine NEVER generates its own RUN_ID in authoritative mode.
It reads OCE_RUN_ID from the environment and fails closed if absent.
"""

import json
import os
import re
import subprocess
import sys
import hashlib
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

VERSION = "3.6.0"
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
REPO_ROOT = BASE_DIR.parent.parent  # infrastructure/cloud-ground -> repo root
EVIDENCE_DIR = BASE_DIR / "evidence"
CONTRACTS_DIR = BASE_DIR / "contracts"
COMPOSE_DIR = BASE_DIR / "compose"
POLICY_DIR = BASE_DIR / "policy"
ANSIBLE_DIR = BASE_DIR / "ansible"
IDENTITY_DATA = CONTRACTS_DIR / "checkpoint-identity-data.json"


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_tool_version(cmd):
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)
        return (r.stdout + r.stderr).strip().split("\n")[0][:120]
    except Exception:
        return "not installed"


def git_cmd(args):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def get_git_info():
    """Capture observed git identity. Never substitutes expected values."""
    info = {}
    for key, cmd in [
        ("branch", ["branch", "--show-current"]),
        ("commit", ["rev-parse", "HEAD"]),
        ("tree", ["rev-parse", "HEAD^{tree}"]),
        ("remote_url", ["remote", "get-url", "origin"]),
        ("repo_root", ["rev-parse", "--show-toplevel"]),
    ]:
        info[key] = git_cmd(["-C", str(REPO_ROOT)] + cmd) or "unknown"
    # In detached HEAD, --show-current returns "". Fallback to HEAD symbolic-ref.
    if not info["branch"] or info["branch"] == "unknown":
        ref = git_cmd(["-C", str(REPO_ROOT), "symbolic-ref", "-q", "HEAD"])
        if ref:
            info["branch"] = ref.replace("refs/heads/", "")
        else:
            info["branch"] = "(detached)"
    return info


class CheckResult:
    def __init__(self, check_id, description, mandatory, result, evidence="", output=""):
        self.check_id = check_id
        self.description = description
        self.mandatory = mandatory
        self.result = result
        self.evidence = evidence
        self.output = output
        self.timestamp = utc_now()

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "description": self.description,
            "mandatory": self.mandatory,
            "result": self.result,
            "evidence": self.evidence,
            "output": self.output,
            "timestamp": self.timestamp,
        }


class Validator:
    def __init__(
        self,
        target_commit=None,
        target_tree=None,
        target_branch=None,
        authoritative=False,
        evidence_dir=None,
        phase=None,
    ):
        # R3G: explicit phase argument. 'initial' runs without adversarial
        # evidence checks; 'final' runs everything including them.
        if phase is not None and phase not in ("initial", "final"):
            print(f"ERROR: invalid phase '{phase}' (must be 'initial' or 'final')", file=sys.stderr)
            sys.exit(1)
        self.phase = phase
        self.results = []
        self.start_time = utc_now()
        self.source_identity_passed = False
        self.target_commit = target_commit
        self.target_tree = target_tree
        self.target_branch = target_branch
        self.authoritative = authoritative
        self.evidence_dir_override = Path(evidence_dir) if evidence_dir else None
        self.observed_branch = None
        self.observed_commit = None
        self.observed_tree = None

        # R3F: Read OCE_RUN_ID from environment. Never generate one.
        env_run_id = os.environ.get("OCE_RUN_ID", "").strip()
        if authoritative:
            if not env_run_id:
                print("ERROR: OCE_RUN_ID is mandatory in authoritative mode", file=sys.stderr)
                sys.exit(1)
            self.run_uid = env_run_id
        else:
            # Non-authoritative mode: use env if present, else generate for unit tests only
            if env_run_id:
                self.run_uid = env_run_id
            else:
                import uuid
                self.run_uid = f"test-{uuid.uuid4().hex[:8]}"

    def add(self, check_id, description, mandatory, result, evidence="", output=""):
        self.results.append(
            CheckResult(check_id, description, mandatory, result, evidence, output)
        )

    def _read_file(self, path):
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return f"ERROR: {e}"

    def _find_files(self, directory, pattern):
        return sorted(directory.rglob(pattern))

    def _yaml_parse(self, path):
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
            return True, "OK"
        except ImportError:
            return False, "BLOCKED: pyyaml not installed"
        except Exception as e:
            return False, f"FAIL: {e}"

    def _json_parse(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            return True, "OK"
        except Exception as e:
            return False, f"FAIL: {e}"

    def _identity_provenance(self):
        """R3G: resolve branch identity from OBSERVATIONS only.
        Never substitute the contract's expected branch into an observed field."""
        git = get_git_info()
        observed = git.get("branch", "unknown")
        detached = observed in ("(detached)", "", "unknown")
        # R3G: the runner may supply a trusted ref (OCE_TRUSTED_REF) for
        # detached checkouts, e.g. the disposable adversarial worktree.
        trusted_ref = (os.environ.get("GITHUB_REF_NAME", "").strip()
                       or os.environ.get("OCE_TRUSTED_REF", "").strip())
        ci_mode = os.environ.get("OCE_CI_MODE", "").lower() == "true"
        prov = {
            "expected_branch": self._get_expected_branch(),
            "observed_git_branch": observed,
            "trusted_ci_ref": trusted_ref or None,
            "checkout_state": "detached" if detached else "attached",
            "branch_provenance": "git-symbolic-ref",
            "identity_branch": observed,
        }
        if detached and trusted_ref:
            prov["branch_provenance"] = "GITHUB_REF_NAME" if ci_mode else "explicit-trusted-ref"
            prov["identity_branch"] = trusted_ref
        elif detached:
            prov["branch_provenance"] = "none"
        return prov

    def _get_expected_branch(self):
        """Return the EXPECTED branch from the contract."""
        try:
            contract = json.loads(IDENTITY_DATA.read_text(encoding="utf-8"))
            cb = contract.get("authorized_branch", "")
            if cb:
                return cb
        except Exception:
            pass
        return ""

    # ===== SOURCE-IDENTITY (CHECK 1 — MANDATORY FIRST) =====
    def check_source_identity(self):
        """Positively prove repository, branch, commit, tree, path, workflow identity.
        R3F: Separate observed vs expected. Never use contract value as observed."""
        git = get_git_info()
        errors = []

        if not IDENTITY_DATA.exists():
            self.add("SOURCE-IDENTITY", "Source identity verification", True, "BLOCKED",
                      "checkpoint-identity-data.json not found", "")
            return

        try:
            contract = json.loads(IDENTITY_DATA.read_text(encoding="utf-8"))
        except Exception as e:
            self.add("SOURCE-IDENTITY", "Source identity verification", True, "BLOCKED",
                      f"Cannot parse identity contract: {e}", "")
            return

        # Repository checks
        repo = contract.get("repository", {})
        expected_owner = repo.get("owner", "")
        expected_name = repo.get("name", "")
        expected_full = repo.get("full_name", "")
        if expected_owner != "dabiggestpoppa":
            errors.append(f"REPOSITORY_OWNER: expected dabiggestpoppa, got {expected_owner}")
        if expected_name != "larger-lab":
            errors.append(f"REPOSITORY_NAME: expected larger-lab, got {expected_name}")
        if expected_full != "dabiggestpoppa/larger-lab":
            errors.append(f"REPOSITORY: expected dabiggestpoppa/larger-lab, got {expected_full}")

        remote_url = git.get("remote_url", "")
        accepted = contract.get("accepted_origins", [])

        def strip_git_suffix(s):
            return s[:-4] if s.endswith(".git") else s

        remote_normalized = strip_git_suffix(remote_url) if remote_url else ""
        accepted_normalized = [strip_git_suffix(o) for o in accepted]
        if remote_normalized not in accepted_normalized and remote_url not in accepted:
            errors.append(f"REMOTE: '{remote_url}' not in accepted origins {accepted}")

        # R3F: OBSERVED branch from git, EXPECTED from contract — never confuse them
        observed_branch = git.get("branch", "")
        expected_branch = self.target_branch or self._get_expected_branch()
        self.observed_branch = observed_branch

        if expected_branch and observed_branch and observed_branch != expected_branch:
            if observed_branch == "(detached)":
                # In CI detached HEAD, the trusted ref comes from GITHUB_REF_NAME;
                # in a disposable worktree, from OCE_TRUSTED_REF.
                gha_ref = (os.environ.get("GITHUB_REF_NAME", "")
                           or os.environ.get("OCE_TRUSTED_REF", ""))
                if gha_ref and gha_ref == expected_branch:
                    pass  # detached CI with correct trusted ref
                else:
                    errors.append(
                        f"BRANCH: detached HEAD without trusted ref "
                        f"(expected '{expected_branch}', GITHUB_REF_NAME='{gha_ref}')"
                    )
            else:
                errors.append(
                    f"BRANCH: expected '{expected_branch}', observed '{observed_branch}'"
                )

        actual_commit = git.get("commit", "")
        self.observed_commit = actual_commit
        expected_commit = self.target_commit or contract.get("expected_implementation_commit_source", "")
        if expected_commit and expected_commit.strip() and actual_commit != expected_commit:
            errors.append(f"COMMIT: expected '{expected_commit[:12]}', got '{actual_commit[:12]}'")

        actual_tree = git.get("tree", "")
        self.observed_tree = actual_tree
        expected_tree = self.target_tree or contract.get("expected_tree_sha", "")
        if expected_tree and expected_tree.strip() and actual_tree != expected_tree:
            errors.append(f"TREE: expected '{expected_tree[:12]}', got '{actual_tree[:12]}'")

        expected_root = contract.get("expected_project_root", "")
        actual_root_rel = str(BASE_DIR.relative_to(REPO_ROOT)).replace("\\", "/")
        if expected_root and actual_root_rel != expected_root:
            errors.append(f"PROJECT_ROOT: expected '{expected_root}', got '{actual_root_rel}'")

        expected_base = contract.get("authoritative_base_sha", "")
        if expected_base and expected_base.strip() and actual_commit:
            if actual_commit != expected_base:
                r = subprocess.run(
                    ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor",
                     expected_base, actual_commit],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode != 0:
                    errors.append(
                        f"BASE_SHA: {actual_commit[:12]} is not a descendant of base {expected_base[:12]}"
                    )

        # GitHub Actions environment
        gha_repo = os.environ.get("GITHUB_REPOSITORY", "")
        # R3G: GITHUB_REF_NAME is authoritative when present; OCE_TRUSTED_REF
        # covers detached disposable worktrees run by the shared runner.
        gha_ref = (os.environ.get("GITHUB_REF_NAME", "")
                   or os.environ.get("OCE_TRUSTED_REF", ""))
        gha_sha = os.environ.get("GITHUB_SHA", "")
        if gha_repo:
            if gha_repo != "dabiggestpoppa/larger-lab":
                errors.append(f"GITHUB_REPOSITORY: expected dabiggestpoppa/larger-lab, got {gha_repo}")
            if gha_sha and actual_commit and gha_sha != actual_commit:
                errors.append(f"GITHUB_SHA: {gha_sha[:12]} does not match HEAD {actual_commit[:12]}")
            if gha_ref:
                if expected_branch and gha_ref != expected_branch:
                    errors.append(
                        f"GITHUB_REF_NAME: expected '{expected_branch}', got '{gha_ref}'"
                    )

        if self.authoritative:
            if not self.target_commit or not self.target_commit.strip():
                errors.append("AUTHORITATIVE: --target-commit is mandatory in authoritative mode")
            if not self.target_tree or not self.target_tree.strip():
                errors.append("AUTHORITATIVE: --target-tree is mandatory in authoritative mode")
            if not self.target_branch or not self.target_branch.strip():
                errors.append("AUTHORITATIVE: --target-branch is mandatory in authoritative mode")
            if actual_commit and self.target_commit and actual_commit != self.target_commit:
                errors.append(f"AUTHORITATIVE: HEAD {actual_commit[:12]} != target commit {self.target_commit[:12]}")
            if actual_tree and self.target_tree and actual_tree != self.target_tree:
                errors.append(f"AUTHORITATIVE: tree {actual_tree[:12]} != target tree {self.target_tree[:12]}")
            if gha_repo:
                if gha_sha and actual_commit and gha_sha != actual_commit:
                    errors.append(f"AUTHORITATIVE: GITHUB_SHA {gha_sha[:12]} != HEAD {actual_commit[:12]}")
                if gha_ref and self.target_branch and gha_ref != self.target_branch:
                    errors.append(f"AUTHORITATIVE: GITHUB_REF_NAME '{gha_ref}' != '{self.target_branch}'")
                if gha_repo != "dabiggestpoppa/larger-lab":
                    errors.append(f"AUTHORITATIVE: GITHUB_REPOSITORY '{gha_repo}' != 'dabiggestpoppa/larger-lab'")
            if expected_base and expected_base.strip() and actual_commit:
                if actual_commit != expected_base:
                    r = subprocess.run(
                        ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor",
                         expected_base, actual_commit],
                        capture_output=True, text=True, timeout=10,
                    )
                    if r.returncode != 0:
                        errors.append(f"AUTHORITATIVE: HEAD is not descendant of base {expected_base[:12]}")
            # In authoritative mode, check worktree is clean (tracked files only)
            r = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                capture_output=True, text=True, timeout=10,
            )
            dirty_lines = [
                l for l in r.stdout.strip().splitlines()
                if l.strip() and not l.startswith("??")
            ]
            if dirty_lines:
                errors.append(
                    f"AUTHORITATIVE: worktree not clean — {len(dirty_lines)} modified tracked files"
                )

        if errors:
            self.add("SOURCE-IDENTITY", "Source identity verification", True, "FAIL",
                      f"{len(errors)} mismatches", "\n".join(errors))
        else:
            evidence_parts = [
                f"repo={expected_full}",
                f"expected_branch={expected_branch}",
                f"observed_branch={observed_branch}",
                f"commit={actual_commit[:12]}",
                f"tree={actual_tree[:12]}",
                f"root={actual_root_rel}",
            ]
            if gha_repo:
                evidence_parts.append(f"gha_repo={gha_repo}")
                evidence_parts.append(f"gha_sha={gha_sha[:12]}")
            self.add("SOURCE-IDENTITY", "Source identity verification", True, "PASS",
                      ", ".join(evidence_parts), "All identity checks passed")

        self.source_identity_passed = any(
            r.check_id == "SOURCE-IDENTITY" and r.result == "PASS"
            for r in self.results
        )

    # ===== STATIC CHECKS =====
    def check_yaml_parsing(self):
        yaml_files = self._find_files(BASE_DIR, "*.yml") + self._find_files(BASE_DIR, "*.yaml")
        yaml_files = [f for f in yaml_files if ".git" not in str(f) and "node_modules" not in str(f)]
        passed, failed, details = 0, 0, []
        for f in yaml_files:
            ok, msg = self._yaml_parse(f)
            rel = str(f.relative_to(BASE_DIR))
            if ok:
                passed += 1
            else:
                failed += 1
                details.append(f"{rel}: {msg}")
        total = passed + failed
        if total == 0:
            self.add("YAML-PARSE", "YAML files parse correctly", True, "BLOCKED", "No YAML files", "0 files")
        elif failed == 0:
            self.add("YAML-PARSE", "YAML files parse correctly", True, "PASS", f"{passed}/{total}", "All parse")
        else:
            self.add("YAML-PARSE", "YAML files parse correctly", True, "FAIL", f"{passed}/{total}",
                      "\n".join(details[:10]))

    def check_json_parsing(self):
        json_files = self._find_files(CONTRACTS_DIR, "*.json")
        passed, failed, details = 0, 0, []
        for f in json_files:
            ok, msg = self._json_parse(f)
            if ok:
                passed += 1
            else:
                failed += 1
                details.append(f"{f.name}: {msg}")
        total = passed + failed
        if total == 0:
            self.add("JSON-PARSE", "JSON contract files parse", True, "BLOCKED", "No JSON files", "0 files")
        elif failed == 0:
            self.add("JSON-PARSE", "JSON contract files parse", True, "PASS", f"{passed}/{total}", "All parse")
        else:
            self.add("JSON-PARSE", "JSON contract files parse", True, "FAIL", f"{passed}/{total}",
                      "\n".join(details[:10]))

    def check_schema_validity(self):
        schemas = self._find_files(CONTRACTS_DIR, "*.schema.json")
        passed, failed, details = 0, 0, []
        for s in schemas:
            try:
                import jsonschema
                with open(s, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.Draft202012Validator.check_schema(schema)
                passed += 1
            except ImportError:
                self.add("SCHEMA-VALID", "JSON Schemas valid Draft 2020-12", True, "BLOCKED",
                          "jsonschema not installed", "")
                return
            except Exception as e:
                failed += 1
                details.append(f"{s.name}: {e}")
        total = passed + failed
        if total == 0:
            self.add("SCHEMA-VALID", "JSON Schemas valid Draft 2020-12", True, "BLOCKED", "No schemas", "0 schemas")
        elif failed == 0:
            self.add("SCHEMA-VALID", "JSON Schemas valid Draft 2020-12", True, "PASS", f"{passed}/{total}", "All valid")
        else:
            self.add("SCHEMA-VALID", "JSON Schemas valid Draft 2020-12", True, "FAIL", f"{passed}/{total}",
                      "\n".join(details))

    def check_schema_fixtures(self):
        fixtures_dir = BASE_DIR / "tests" / "fixtures"
        if not fixtures_dir.exists():
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "BLOCKED", "No fixtures dir", "")
            return
        try:
            import jsonschema
        except ImportError:
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "BLOCKED",
                      "jsonschema not installed", "")
            return
        schemas = {s.stem.replace(".schema", ""): s for s in self._find_files(CONTRACTS_DIR, "*.schema.json")}
        valid_dir = fixtures_dir / "valid"
        invalid_dir = fixtures_dir / "invalid"
        passed, failed, details = 0, 0, []
        if valid_dir.exists():
            for fixture_file in sorted(valid_dir.glob("*.json")):
                schema_name = fixture_file.stem.rsplit(".valid", 1)[0]
                schema_path = None
                for name, sp in schemas.items():
                    if schema_name.startswith(name) or name.startswith(schema_name.split(".")[0]):
                        schema_path = sp
                        break
                if not schema_path:
                    details.append(f"{fixture_file.name}: no matching schema")
                    failed += 1
                    continue
                try:
                    with open(fixture_file) as f:
                        instance = json.load(f)
                    with open(schema_path) as f:
                        schema = json.load(f)
                    jsonschema.validate(instance=instance, schema=schema)
                    passed += 1
                except jsonschema.ValidationError as e:
                    failed += 1
                    details.append(f"VALID fixture {fixture_file.name} rejected: {e.message[:100]}")
                except Exception as e:
                    failed += 1
                    details.append(f"VALID fixture {fixture_file.name} error: {e}")
        if invalid_dir.exists():
            for fixture_file in sorted(invalid_dir.glob("*.json")):
                parts = fixture_file.stem.split(".invalid.")
                schema_name = parts[0]
                schema_path = None
                for name, sp in schemas.items():
                    if schema_name.startswith(name) or name.startswith(schema_name.split(".")[0]):
                        schema_path = sp
                        break
                if not schema_path:
                    details.append(f"{fixture_file.name}: no matching schema")
                    failed += 1
                    continue
                try:
                    with open(fixture_file) as f:
                        instance = json.load(f)
                    with open(schema_path) as f:
                        schema = json.load(f)
                    jsonschema.validate(instance=instance, schema=schema)
                    failed += 1
                    details.append(f"INVALID fixture {fixture_file.name} was accepted")
                except jsonschema.ValidationError:
                    passed += 1
                except Exception as e:
                    failed += 1
                    details.append(f"INVALID fixture {fixture_file.name} error: {e}")
        total = passed + failed
        if total == 0:
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "BLOCKED", "No fixtures", "0 tested")
        elif failed == 0:
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "PASS", f"{passed}/{total}", "All pass")
        else:
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "FAIL", f"{passed}/{total}",
                      "\n".join(details))

    def check_no_latest_tags(self):
        compose_files = self._find_files(COMPOSE_DIR, "*.yml") + self._find_files(COMPOSE_DIR, "*.yaml")
        violations = []
        for f in compose_files:
            content = self._read_file(f)
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if re.search(r"image:.*:latest", stripped):
                    violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {stripped.strip()}")
        if violations:
            self.add("NO-LATEST-TAGS", "No :latest image tags", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-LATEST-TAGS", "No :latest image tags", True, "PASS", "0 violations", "Clean")

    def check_digest_lock(self):
        compose_files = self._find_files(COMPOSE_DIR, "*.yml") + self._find_files(COMPOSE_DIR, "*.yaml")
        violations = []
        for f in compose_files:
            content = self._read_file(f)
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                m = re.match(r"image:\s*(.+)", stripped)
                if m:
                    img = m.group(1).strip().strip('"').strip("'")
                    if img and "@sha256:" not in img:
                        violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {img}")
        if violations:
            self.add("DIGEST-LOCK", "All images use digest pinning", True, "FAIL",
                      f"{len(violations)} tag-only images", "\n".join(violations))
        else:
            self.add("DIGEST-LOCK", "All images use digest pinning", True, "PASS", "0 violations", "All pinned")

    def check_digest_proof(self):
        evidence_path = EVIDENCE_DIR / "image-digests.json"
        if not evidence_path.exists():
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True, "BLOCKED",
                      "image-digests.json not found", "")
            return
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                evidence = json.load(f)
        except Exception as e:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True, "BLOCKED",
                      f"Cannot parse: {e}", "")
            return
        evidence_digests = {}
        verified_digests = {}
        for img in evidence.get("images", []):
            evidence_digests[img["name"]] = img.get("digest", "")
            if img.get("verified_digest", False):
                verified_digests[img["name"]] = img.get("digest", "")
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True, "BLOCKED",
                      "compose.foundation.yml not found", "")
            return
        content = self._read_file(foundation)
        violations = []
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            m = re.match(r"image:\s*(.+)", stripped)
            if m:
                img_ref = m.group(1).strip().strip('"').strip("'")
                parts = img_ref.split("@")
                img_name = parts[0] if parts else ""
                img_digest = parts[1] if len(parts) > 1 else ""
                if img_name in evidence_digests:
                    if img_digest != evidence_digests[img_name]:
                        violations.append(f"{img_name}: compose mismatch")
                elif img_name:
                    violations.append(f"{img_name}: no digest proof")
        unverified = [name for name in evidence_digests if name not in verified_digests]
        if violations:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True, "FAIL",
                      f"{len(violations)} mismatches", "\n".join(violations))
        elif unverified:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True, "FAIL",
                      f"{len(unverified)} unverified", f"Unverified: {', '.join(unverified)}")
        else:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True, "PASS",
                      f"{len(verified_digests)} verified", "All compose digests match")

    def check_digest_registry(self):
        evidence_path = EVIDENCE_DIR / "image-digests.json"
        if not evidence_path.exists():
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True, "BLOCKED",
                      "image-digests.json not found", "")
            return
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                evidence = json.load(f)
        except Exception as e:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True, "BLOCKED",
                      f"Cannot parse: {e}", "")
            return
        verify_cmd = None
        for cmd, fmt in [("docker", "buildx-inspect"), ("skopeo", "skopeo")]:
            try:
                r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    verify_cmd = (cmd, fmt)
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        if not verify_cmd:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True, "BLOCKED",
                      "No registry tool available", "")
            return
        cmd, fmt = verify_cmd
        images = evidence.get("images", [])
        resolved, failed_count, details = 0, 0, []
        for img in images:
            name, digest = img.get("name", ""), img.get("digest", "")
            if not digest:
                failed_count += 1
                details.append(f"{name}: no digest")
                continue
            full_ref = f"{name}@{digest}"
            try:
                if fmt == "buildx-inspect":
                    r = subprocess.run(["docker", "buildx", "imagetools", "inspect", full_ref],
                                        capture_output=True, text=True, timeout=30)
                else:
                    r = subprocess.run(["skopeo", "inspect", f"docker://{full_ref}"],
                                        capture_output=True, text=True, timeout=30)
                if r.returncode == 0 and ("Manifests" in r.stdout or "MediaType" in r.stdout or "SchemaVersion" in r.stdout):
                    resolved += 1
                    details.append(f"{name}: RESOLVED")
                else:
                    failed_count += 1
                    details.append(f"{name}: FAILED")
            except Exception:
                failed_count += 1
                details.append(f"{name}: ERROR")
        if failed_count > 0:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True, "FAIL",
                      f"{failed_count}/{len(images)} failed", "\n".join(details))
        elif resolved == 0:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True, "BLOCKED", "No images", "")
        else:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True, "PASS",
                      f"{resolved}/{len(images)} resolved", "\n".join(details))

    def check_host_key_checking(self):
        cfg_path = ANSIBLE_DIR / "ansible.cfg"
        if not cfg_path.exists():
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True, "BLOCKED",
                      "ansible.cfg not found", "")
            return
        content = self._read_file(cfg_path)
        violations, found = [], False
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "host_key_checking" in stripped.lower():
                found = True
                if "false" in stripped.lower() or "= 0" in stripped or "=no" in stripped.lower():
                    violations.append(f"Line {i}: {stripped}")
        if not found:
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True, "FAIL", "Not set", "")
        elif violations:
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True, "PASS",
                      "host_key_checking = True", "Verified")

    def check_no_published_ports(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("NO-DB-PORTS", "No published DB/cache ports", True, "BLOCKED",
                      "compose.foundation.yml not found", "")
            return
        content = self._read_file(foundation)
        violations, in_services, current_service = [], False, ""
        for i, line in enumerate(content.split("\n"), 1):
            if line.startswith("services:"):
                in_services = True
            elif in_services and not line.startswith(" ") and not line.startswith("#") and line.strip():
                in_services = False
            if in_services and re.match(r"^\s{2}\w", line):
                current_service = line.strip().rstrip(":")
            if in_services and "ports:" in line and not line.lstrip().startswith("#"):
                violations.append(f"Line {i} in {current_service}: {line.strip()}")
        if violations:
            self.add("NO-DB-PORTS", "No published DB/cache ports", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-DB-PORTS", "No published DB/cache ports", True, "PASS", "0 violations", "Clean")

    def check_no_privileged(self):
        violations = []
        for f in self._find_files(COMPOSE_DIR, "*.yml"):
            for i, line in enumerate(self._read_file(f).split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "privileged:" in stripped and "true" in stripped:
                    violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {stripped}")
        if violations:
            self.add("NO-PRIV", "No privileged containers", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-PRIV", "No privileged containers", True, "PASS", "0 violations", "Clean")

    def check_no_socket_mount(self):
        violations = []
        for f in self._find_files(COMPOSE_DIR, "*.yml"):
            for i, line in enumerate(self._read_file(f).split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "docker.sock" in stripped:
                    violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {stripped}")
        if violations:
            self.add("NO-SOCKET", "No Docker socket mounts", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-SOCKET", "No Docker socket mounts", True, "PASS", "0 violations", "Clean")

    def check_no_secrets(self):
        violations = []
        secret_patterns = [
            (r"(?:api[_-]?key|password|secret|token|credential)\s*[:=]\s*['\"][^'\"${}]{8,}", "embedded secret"),
            (r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----", "private key"),
        ]
        scan_dirs = [BASE_DIR / "scripts", BASE_DIR / "tests", ANSIBLE_DIR, COMPOSE_DIR]
        scan_exts = ["*.py", "*.yml", "*.yaml", "*.json", "*.sh", "*.cfg", "*.conf", "*.j2"]
        files = []
        for d in scan_dirs:
            if d.exists():
                for ext in scan_exts:
                    files.extend(d.rglob(ext))
        for pattern, desc in secret_patterns:
            for f in files:
                if ".git" in str(f) or "node_modules" in str(f) or "evidence" in str(f):
                    continue
                for i, line in enumerate(self._read_file(f).split("\n"), 1):
                    stripped = line.lstrip()
                    if stripped.startswith("#"):
                        continue
                    if any(kw in stripped.upper() for kw in ["PLACEHOLDER", "CHANGE_ME", "REPLACE", "EXAMPLE"]):
                        continue
                    if re.search(pattern, stripped, re.IGNORECASE):
                        violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {desc}")
                        break
        if violations:
            self.add("NO-SECRETS", "No embedded secrets", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-SECRETS", "No embedded secrets", True, "PASS", "0 violations", "Clean")

    def check_health_checks(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("HEALTH-CHECKS", "Health checks on foundation services", True, "BLOCKED",
                      "compose.foundation.yml not found", "")
            return
        hc_count = self._read_file(foundation).count("healthcheck:")
        if hc_count >= 2:
            self.add("HEALTH-CHECKS", "Health checks on foundation services", True, "PASS",
                      f"{hc_count} health checks", "Both services")
        else:
            self.add("HEALTH-CHECKS", "Health checks on foundation services", True, "FAIL",
                      f"{hc_count} health checks", f"Need 2+, found {hc_count}")

    def check_cost_thresholds(self):
        cost_file = POLICY_DIR / "cost-guardrails.yml"
        if not cost_file.exists():
            self.add("COST-THRESHOLDS", "Cost thresholds match ratification", True, "FAIL",
                      "cost-guardrails.yml not found", "")
            return
        content = self._read_file(cost_file)
        checks = [
            ("fixed_baseline_warning: 60", "$60 warning"),
            ("burst_hard_stop: 50", "$50 burst stop"),
            ("total_approval_gate: 100", "$100 total gate"),
        ]
        missing = [desc for pattern, desc in checks if pattern not in content]
        if missing:
            self.add("COST-THRESHOLDS", "Cost thresholds match ratification", True, "FAIL",
                      f"Missing: {', '.join(missing)}", "")
        else:
            self.add("COST-THRESHOLDS", "Cost thresholds match ratification", True, "PASS",
                      "All thresholds", "$60/$50/$100")

    def check_worker_deny(self):
        policy = POLICY_DIR / "network-access.yml"
        if not policy.exists():
            self.add("WORKER-DENY", "Workers denied DB/Redis/SSH/Docker", True, "FAIL",
                      "network-access.yml not found", "")
            return
        deny_count = self._read_file(policy).count("action: DENY")
        if deny_count >= 12:
            self.add("WORKER-DENY", "Workers denied DB/Redis/SSH/Docker", True, "PASS",
                      f"{deny_count} DENY rules", f"{deny_count} denial rules")
        else:
            self.add("WORKER-DENY", "Workers denied DB/Redis/SSH/Docker", True, "FAIL",
                      f"{deny_count} DENY rules", f"Need 12+, found {deny_count}")

    def check_worker_no_db_access(self):
        policy = POLICY_DIR / "network-access.yml"
        if not policy.exists():
            self.add("WORKER-NO-DB", "Workers denied direct DB access", True, "FAIL",
                      "network-access.yml not found", "")
            return
        try:
            import yaml
            with open(policy, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except ImportError:
            self.add("WORKER-NO-DB", "Workers denied direct DB access", True, "BLOCKED",
                      "pyyaml not installed", "")
            return
        except Exception as e:
            self.add("WORKER-NO-DB", "Workers denied direct DB access", True, "FAIL",
                      f"Parse error: {e}", "")
            return
        rules = data.get("rules", []) if data else []
        required = [
            (w, s)
            for w in ["worker-local", "worker-burst", "worker-windows"]
            for s in ["postgresql", "redis", "ssh", "docker"]
        ]
        found, missing = 0, []
        for worker, service in required:
            if any(r.get("from") == worker and r.get("to") == service and r.get("action") == "DENY" for r in rules):
                found += 1
            else:
                missing.append(f"{worker}->{service}")
        total = len(required)
        if found >= total:
            self.add("WORKER-NO-DB", "Workers denied direct DB access", True, "PASS",
                      f"{found}/{total} rules", "All denied")
        else:
            self.add("WORKER-NO-DB", "Workers denied direct DB access", True, "FAIL",
                      f"{found}/{total} rules", f"Missing: {', '.join(missing)}")

    def check_security_opts(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("SECURITY-OPTS", "Security options present", True, "BLOCKED",
                      "compose.foundation.yml not found", "")
            return
        count = self._read_file(foundation).count("no-new-privileges")
        if count >= 2:
            self.add("SECURITY-OPTS", "Security options (no-new-privileges)", True, "PASS",
                      f"{count} declarations", "Both hardened")
        else:
            self.add("SECURITY-OPTS", "Security options (no-new-privileges)", True, "FAIL",
                      f"{count} declarations", f"Need 2+, found {count}")

    def check_no_external_networks(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("NO-EXTERNAL-NET", "No external networks", True, "BLOCKED",
                      "compose.foundation.yml not found", "")
            return
        violations = []
        for i, line in enumerate(self._read_file(foundation).split("\n"), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "external:" in stripped and "true" in stripped:
                violations.append(f"Line {i}: {stripped}")
        if violations:
            self.add("NO-EXTERNAL-NET", "No external networks", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-EXTERNAL-NET", "No external networks", True, "PASS", "0 violations", "Clean")

    def check_roles_have_tasks(self):
        roles_dir = ANSIBLE_DIR / "roles"
        if not roles_dir.exists():
            self.add("ROLES-TASKS", "All Ansible roles have tasks", True, "BLOCKED", "No roles dir", "")
            return
        empty = [
            role.name for role in sorted(roles_dir.iterdir())
            if role.is_dir() and not (role / "tasks" / "main.yml").exists()
        ]
        total = len([d for d in roles_dir.iterdir() if d.is_dir()])
        if empty:
            self.add("ROLES-TASKS", "All Ansible roles have tasks", True, "FAIL",
                      f"{len(empty)} empty", f"Empty: {', '.join(empty)}")
        else:
            self.add("ROLES-TASKS", "All Ansible roles have tasks", True, "PASS",
                      f"{total} roles", "All have tasks/main.yml")

    def check_evidence_structure(self):
        has_dir = EVIDENCE_DIR.is_dir()
        has_templates = (EVIDENCE_DIR / "templates").is_dir()
        if has_dir and has_templates:
            self.add("EVIDENCE-DIR", "Evidence directory with templates", True, "PASS",
                      "evidence/ and templates/", "Structure present")
        else:
            self.add("EVIDENCE-DIR", "Evidence directory with templates", True, "FAIL",
                      f"dir={has_dir} templates={has_templates}", "Missing")

    def check_runbooks(self):
        rb_dir = BASE_DIR / "runbooks"
        if rb_dir.exists():
            count = len(list(rb_dir.glob("*.md")))
            if count >= 1:
                self.add("RUNBOOKS", "Operator runbooks present", True, "PASS",
                          f"{count} runbooks", "Present")
            else:
                self.add("RUNBOOKS", "Operator runbooks present", True, "FAIL", "0 runbooks", "No .md")
        else:
            self.add("RUNBOOKS", "Operator runbooks present", True, "FAIL", "No runbooks dir", "Missing")

    def check_single_infra_root(self):
        roots = [r for r in REPO_ROOT.rglob("cloud-ground") if r.is_dir()]
        if len(roots) <= 1:
            self.add("SINGLE-ROOT", "Single infrastructure root", True, "PASS",
                      f"{len(roots)} roots", "Single canonical root")
        else:
            self.add("SINGLE-ROOT", "Single infrastructure root", True, "FAIL",
                      f"{len(roots)} roots", "Duplicate roots")

    def check_ansible_syntax(self):
        site_yml = ANSIBLE_DIR / "playbooks" / "site.yml"
        hosts_yml = ANSIBLE_DIR / "inventories" / "example" / "hosts.yml"
        if not site_yml.exists():
            self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "BLOCKED",
                      "site.yml not found", "")
            return
        try:
            args = ["ansible-playbook", "--syntax-check", str(site_yml)]
            if hosts_yml.exists():
                args.extend(["-i", str(hosts_yml)])
            r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=str(BASE_DIR))
            if r.returncode == 0:
                self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "PASS",
                          "syntax-check passed", r.stdout[:200])
            else:
                self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "FAIL",
                          "syntax-check failed", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "BLOCKED",
                      "ansible-playbook not installed", "")
        except subprocess.TimeoutExpired:
            self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "BLOCKED", "timeout", "")

    def check_ansible_lint(self):
        try:
            r = subprocess.run(
                ["ansible-lint", str(ANSIBLE_DIR / "playbooks" / "site.yml")],
                capture_output=True, text=True, timeout=60, cwd=str(ANSIBLE_DIR),
            )
            if r.returncode == 0:
                self.add("ANSIBLE-LINT", "Ansible lint passes", True, "PASS", "clean", r.stdout[:200])
            else:
                self.add("ANSIBLE-LINT", "Ansible lint passes", True, "FAIL", "found issues",
                          (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("ANSIBLE-LINT", "Ansible lint passes", True, "BLOCKED", "ansible-lint not installed", "")
        except subprocess.TimeoutExpired:
            self.add("ANSIBLE-LINT", "Ansible lint passes", True, "BLOCKED", "timeout", "")

    def check_compose_render(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("COMPOSE-RENDER", "Compose foundation renders", True, "BLOCKED",
                      "compose.foundation.yml not found", "")
            return
        try:
            env = os.environ.copy()
            env["POSTGRES_PASSWORD"] = "test_password_for_validation"
            r = subprocess.run(
                ["docker", "compose", "-f", str(foundation), "config"],
                capture_output=True, text=True, timeout=30, env=env, cwd=str(COMPOSE_DIR),
            )
            if r.returncode == 0:
                self.add("COMPOSE-RENDER", "Compose foundation renders", True, "PASS",
                          "docker compose config", "Renders OK")
            else:
                self.add("COMPOSE-RENDER", "Compose foundation renders", True, "FAIL",
                          "docker compose config", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("COMPOSE-RENDER", "Compose foundation renders", True, "BLOCKED",
                      "docker not installed", "")
        except subprocess.TimeoutExpired:
            self.add("COMPOSE-RENDER", "Compose foundation renders", True, "BLOCKED", "timeout", "")

    def check_shellcheck(self):
        scripts = [
            s for s in list((BASE_DIR / "scripts").glob("*")) + list((BASE_DIR / "tests").glob("*.sh"))
            if s.is_file() and not s.name.endswith(".py")
        ]
        if not scripts:
            self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "BLOCKED", "No shell scripts", "")
            return
        try:
            all_pass, details = True, []
            for s in scripts:
                r = subprocess.run(
                    ["shellcheck", "-s", "bash", "--severity=error", str(s)],
                    capture_output=True, text=True, timeout=30,
                )
                if r.returncode != 0:
                    all_pass = False
                    details.append(f"{s.name}: {r.stderr[:200]}")
            if all_pass:
                self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "PASS",
                          f"{len(scripts)} scripts", "All clean")
            else:
                self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "FAIL",
                          f"{len(details)} issues", "\n".join(details[:5]))
        except FileNotFoundError:
            self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "BLOCKED",
                      "shellcheck not installed", "")

    def check_gitleaks(self):
        try:
            r = subprocess.run(
                ["gitleaks", "detect", "--source", str(BASE_DIR), "--no-banner", "--report-format", "json"],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0:
                self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "PASS",
                          "gitleaks clean", "No secrets found")
            else:
                self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "FAIL",
                          "gitleaks found secrets", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "BLOCKED",
                      "gitleaks not installed", "")
        except subprocess.TimeoutExpired:
            self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "BLOCKED", "timeout", "")

    def check_scaffold_scan(self):
        violations = []
        scaffold_patterns = [
            (r"\bTODO\b", "TODO marker"),
            (r"\bFIXME\b", "FIXME marker"),
            (r"\bNOT\s+IMPLEMENTED\b", "NOT IMPLEMENTED marker"),
        ]
        scan_paths = []
        if (BASE_DIR / "scripts").exists():
            scan_paths.extend(list((BASE_DIR / "scripts").glob("*")))
        if (BASE_DIR / "tests").exists():
            scan_paths.extend(list((BASE_DIR / "tests").glob("*.sh")))
        for f in scan_paths:
            if f.is_dir() or f.suffix in (".py",):
                continue
            for i, line in enumerate(self._read_file(f).split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                for pattern, desc in scaffold_patterns:
                    if re.search(pattern, stripped, re.IGNORECASE):
                        violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {desc}")
                        break
        if violations:
            self.add("SCAFFOLD-SCAN", "No unresolved scaffolds in executables", True, "FAIL",
                      f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("SCAFFOLD-SCAN", "No unresolved scaffolds in executables", True, "PASS",
                      "0 violations", "Clean")

    # ===== POST-CHECKS =====

    def compute_totals(self):
        counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
        for r in self.results:
            if r.result in counts:
                counts[r.result] += 1
        counts["total"] = len(self.results)
        return counts

    def check_totals_consistency(self, totals):
        expected_total = totals["PASS"] + totals["FAIL"] + totals["BLOCKED"] + totals["SKIPPED"]
        actual_total = totals["total"]
        if actual_total == 0:
            self.add("TOTALS-CONSIST", "Result totals self-consistent", True, "FAIL",
                      "0 results", "No checks executed")
        elif actual_total == expected_total:
            self.add("TOTALS-CONSIST", "Result totals self-consistent", True, "PASS",
                      f"{actual_total} results",
                      f"P={totals['PASS']} F={totals['FAIL']} B={totals['BLOCKED']} S={totals['SKIPPED']}")
        else:
            self.add("TOTALS-CONSIST", "Result totals self-consistent", True, "FAIL",
                      f"total={actual_total} computed={expected_total}", "Disagreement")

    def _evidence_dir(self):
        d = self.evidence_dir_override if self.evidence_dir_override else EVIDENCE_DIR
        d.mkdir(parents=True, exist_ok=True)
        return d

    def check_fail_closed(self):
        """Validate adversarial evidence with strict requirements."""
        adv_path = self._evidence_dir() / "adversarial-results.json"
        if not adv_path.exists():
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True, "BLOCKED",
                      "adversarial-results.json not found", "Run adversarial-tests.sh first")
            return
        try:
            with open(adv_path, "r", encoding="utf-8") as f:
                adv = json.load(f)
        except Exception as e:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True, "BLOCKED",
                      f"Cannot parse: {e}", "")
            return

        errors = []

        if adv.get("schema_version", "") != VERSION:
            errors.append(f"SCHEMA_VERSION: {adv.get('schema_version', '')} (expected {VERSION})")
        if adv.get("validator_version", "") != VERSION:
            errors.append(f"VALIDATOR_VERSION: {adv.get('validator_version', '')} (expected {VERSION})")

        adv_run_id = adv.get("run_id", "")
        if not adv_run_id:
            errors.append("RUN_ID: adversarial results have no run_id")
        elif adv_run_id != self.run_uid:
            errors.append(f"RUN_ID: adversarial run_id={adv_run_id} != validator run_id={self.run_uid}")

        negative_tests = adv.get("negative_tests", [])
        meta_tests = adv.get("meta_tests", [])
        if not negative_tests and not meta_tests:
            negative_tests = adv.get("tests", [])

        total_tests = len(negative_tests) + len(meta_tests)

        for t in negative_tests:
            tid = t.get("test_id", "?")
            mr = t.get("mutation_result", "")
            me = t.get("mutation_exit", 0)
            br = t.get("baseline_result", "")
            be = t.get("baseline_exit", 0)
            pr = t.get("post_restore_result", "")
            pe = t.get("post_restore_exit", 0)
            orig = t.get("original_sha256", "")
            rest = t.get("restored_sha256", "")

            if br != "PASS":
                errors.append(f"{tid}: baseline_result={br} (must be PASS)")
            if be != 0:
                errors.append(f"{tid}: baseline_exit={be} (must be 0)")
            if mr != "FAIL":
                errors.append(f"{tid}: mutation_result={mr} (must be exactly FAIL)")
            if me == 0 and mr not in ("N/A", ""):
                errors.append(f"{tid}: mutation_exit=0 (must be nonzero)")
            if pr != "PASS":
                errors.append(f"{tid}: post_restore_result={pr} (must be PASS)")
            if pe != 0:
                errors.append(f"{tid}: post_restore_exit={pe} (must be 0)")
            if not orig or orig == "N/A":
                errors.append(f"{tid}: original_sha256 is empty or N/A")
            if not rest or rest == "N/A":
                errors.append(f"{tid}: restored_sha256 is empty or N/A")
            if orig and rest and orig != "N/A" and rest != "N/A" and orig != rest:
                errors.append(f"{tid}: restored_hash {rest[:16]} != baseline_hash {orig[:16]}")

        for t in meta_tests:
            tid = t.get("test_id", "?")
            for field in ["fixture_type", "invalid_condition", "expected_rejection",
                           "observed_rejection", "rejection_exit"]:
                val = t.get(field, "")
                if not val and val != 0:
                    errors.append(f"{tid}: meta_test missing required field {field}")
            obs = t.get("observed_rejection", "")
            if obs and obs not in ("FAIL", "BLOCKED"):
                errors.append(f"{tid}: observed_rejection={obs} (must be FAIL or BLOCKED to prove rejection)")
            re_exit = t.get("rejection_exit", 0)
            if re_exit == 0:
                errors.append(f"{tid}: rejection_exit=0 (must be nonzero to prove rejection)")
            result = t.get("result", "")
            if result == "PASS" and (not obs or obs not in ("FAIL", "BLOCKED")):
                errors.append(f"{tid}: result=PASS but no rejection evidence")

        suite_result = adv.get("suite_result", "")
        if suite_result != "PASS":
            errors.append(f"suite_result={suite_result}")
        neg_passed = sum(1 for t in negative_tests if t.get("result") == "PASS")
        neg_failed = sum(1 for t in negative_tests if t.get("result") == "FAIL")
        meta_passed = sum(1 for t in meta_tests if t.get("result") == "PASS")
        if neg_failed > 0:
            errors.append(f"{neg_failed}/{len(negative_tests)} negative tests failed")
        if neg_passed == 0 and len(negative_tests) > 0:
            errors.append("0 negative tests passed")
        if len(meta_tests) > 0 and meta_passed == 0:
            errors.append("0 meta tests passed")
        if total_tests == 0:
            errors.append("0 adversarial tests total")

        if errors:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True, "FAIL",
                      f"{len(errors)} issues", "\n".join(errors[:10]))
        else:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True, "PASS",
                      f"{neg_passed} negative + {meta_passed} meta pass",
                      "All mutations correctly rejected; all meta tests prove rejection")

    def check_meta_test_evidence(self):
        adv_path = self._evidence_dir() / "adversarial-results.json"
        if not adv_path.exists():
            self.add("META-TEST-EVIDENCE", "Meta-test rejection evidence complete", True, "BLOCKED",
                      "adversarial-results.json not found", "")
            return
        try:
            with open(adv_path, "r", encoding="utf-8") as f:
                adv = json.load(f)
        except Exception as e:
            self.add("META-TEST-EVIDENCE", "Meta-test rejection evidence complete", True, "BLOCKED",
                      f"Cannot parse: {e}", "")
            return

        meta_tests = adv.get("meta_tests", [])
        if not meta_tests:
            self.add("META-TEST-EVIDENCE", "Meta-test rejection evidence complete", True, "BLOCKED",
                      "No meta tests found", "")
            return

        errors = []
        for t in meta_tests:
            tid = t.get("test_id", "?")
            fixture_type = t.get("fixture_type", "")
            invalid_condition = t.get("invalid_condition", "")
            expected_rejection = t.get("expected_rejection", "")
            observed_rejection = t.get("observed_rejection", "")
            rejection_exit = t.get("rejection_exit", 0)

            if not fixture_type:
                errors.append(f"{tid}: missing fixture_type")
            if not invalid_condition:
                errors.append(f"{tid}: missing invalid_condition")
            if not expected_rejection:
                errors.append(f"{tid}: missing expected_rejection")
            if not observed_rejection:
                errors.append(f"{tid}: missing observed_rejection")
            if not rejection_exit:
                errors.append(f"{tid}: missing rejection_exit")
            elif rejection_exit == 0:
                errors.append(f"{tid}: rejection_exit=0 (must be nonzero)")

            if expected_rejection and observed_rejection:
                if expected_rejection not in ("FAIL", "BLOCKED"):
                    errors.append(f"{tid}: expected_rejection={expected_rejection} (must be FAIL or BLOCKED)")
                if observed_rejection not in ("FAIL", "BLOCKED"):
                    errors.append(f"{tid}: observed_rejection={observed_rejection} (must be FAIL or BLOCKED)")

        if errors:
            self.add("META-TEST-EVIDENCE", "Meta-test rejection evidence complete", True, "FAIL",
                      f"{len(errors)} issues", "\n".join(errors[:10]))
        else:
            self.add("META-TEST-EVIDENCE", "Meta-test rejection evidence complete", True, "PASS",
                      f"{len(meta_tests)} meta tests with complete evidence",
                      "All meta tests have fixture_type, invalid_condition, expected/observed rejection, nonzero exit")

    def check_run_id_consistency(self):
        """Verify one RUN_ID is used consistently across all evidence artifacts."""
        ev_dir = self._evidence_dir()
        errors = []

        for fname, label in [
            ("static-validation-results.json", "static-validation-results"),
            ("adversarial-results.json", "adversarial-results"),
            ("stage-status.json", "stage-status"),
        ]:
            path = ev_dir / fname
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    rid = data.get("run_id", "")
                    if not rid:
                        errors.append(f"{fname}: no run_id")
                    elif rid != self.run_uid:
                        errors.append(f"{fname}: run_id={rid} != {self.run_uid}")
                except Exception:
                    errors.append(f"{fname}: cannot parse")

        if errors:
            self.add("RUN-ID-CONSISTENCY", "One RUN_ID consistent across all evidence", True, "FAIL",
                      f"{len(errors)} mismatches", "\n".join(errors))
        else:
            self.add("RUN-ID-CONSISTENCY", "One RUN_ID consistent across all evidence", True, "PASS",
                      f"run_id={self.run_uid}", "All evidence artifacts use same RUN_ID")

    def check_evidence_consistency(self):
        ev_path = self._evidence_dir() / "static-validation-results.json"
        git = get_git_info()
        errors = []

        actual_commit = git.get("commit", "")
        actual_tree = git.get("tree", "")
        # R3G: evidence's tested_branch records the OBSERVED git branch truth
        # (e.g. "(detached)" inside a disposable worktree); compare against the
        # observation, never against a resolved/substituted identity.
        actual_branch = git.get("branch", "unknown")
        ident = self._identity_provenance()
        if ident["branch_provenance"] == "none":
            errors.append("BRANCH_PROVENANCE: detached HEAD with no trusted ref")

        try:
            with open(ev_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except FileNotFoundError:
            payload = self._build_results_payload(git)
        except Exception as e:
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True, "FAIL",
                      f"Cannot read evidence: {e}", "")
            return

        ev_commit = payload.get("tested_commit", "")
        ev_tree = payload.get("tested_tree", "")
        ev_branch = payload.get("tested_branch", "")

        if ev_commit and actual_commit and ev_commit != actual_commit:
            errors.append(f"COMMIT: evidence={ev_commit[:12]} actual={actual_commit[:12]}")
        if ev_tree and actual_tree and ev_tree != actual_tree:
            errors.append(f"TREE: evidence={ev_tree[:12]} actual={actual_tree[:12]}")
        if ev_branch and actual_branch and ev_branch != actual_branch:
            errors.append(f"BRANCH: evidence={ev_branch} actual={actual_branch}")
        if payload.get("repository", "") != "dabiggestpoppa/larger-lab":
            errors.append(f"REPOSITORY: {payload.get('repository', '')}")
        if payload.get("validator_version", "") != VERSION:
            errors.append(f"VERSION: {payload.get('validator_version', '')} != {VERSION}")

        ev_totals = payload.get("totals", {})
        ev_results = payload.get("results", [])
        ev_total = ev_totals.get("total", 0)
        if ev_total != len(ev_results):
            errors.append(f"TOTALS: declared={ev_total} actual={len(ev_results)}")
        ev_p = (ev_totals.get("PASS", 0) + ev_totals.get("FAIL", 0) +
                ev_totals.get("BLOCKED", 0) + ev_totals.get("SKIPPED", 0))
        if ev_p != ev_total:
            errors.append(f"TOTALS_MATH: {ev_p} != {ev_total}")

        if errors:
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True, "FAIL",
                      f"{len(errors)} mismatches", "\n".join(errors))
        else:
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True, "PASS",
                      "All identity fields match", "Evidence is self-consistent (atomic)")

    def _build_results_payload(self, git_info):
        # R3G: record observed truth plus provenance separately.
        ident = self._identity_provenance()
        payload = {
            "schema_version": VERSION,
            "run_id": self.run_uid,
            "validator_version": VERSION,
            "phase": self.phase or "unspecified",
            "increment": "B1-I1R3H",
            "start_time": self.start_time,
            "end_time": utc_now(),
            "tested_commit": git_info.get("commit", "unknown"),
            "tested_tree": git_info.get("tree", "unknown"),
            "tested_branch": ident["observed_git_branch"],
            "expected_branch": ident["expected_branch"],
            "observed_git_branch": ident["observed_git_branch"],
            "trusted_ci_ref": ident["trusted_ci_ref"],
            "checkout_state": ident["checkout_state"],
            "branch_provenance": ident["branch_provenance"],
            "repository": "dabiggestpoppa/larger-lab",
            "remote_url": git_info.get("remote_url", "unknown"),
            "command": "validate_engine.py --all",
            "tools": {
                "python": get_tool_version("python3"),
                "ansible": get_tool_version("ansible-playbook"),
                "ansible_lint": get_tool_version("ansible-lint"),
                "docker": get_tool_version("docker"),
                "shellcheck": get_tool_version("shellcheck"),
                "gitleaks": get_tool_version("gitleaks"),
            },
            "results": [r.to_dict() for r in self.results],
            "totals": self.compute_totals(),
            "gate": self.determine_gate(self.compute_totals()),
        }
        return payload

    # ===== FULL RUN =====

    def run_all_checks(self):
        self.check_source_identity()
        if not self.source_identity_passed:
            return
        self.check_yaml_parsing()
        self.check_json_parsing()
        self.check_schema_validity()
        self.check_schema_fixtures()
        self.check_no_latest_tags()
        self.check_digest_lock()
        self.check_digest_proof()
        self.check_digest_registry()
        self.check_host_key_checking()
        self.check_no_published_ports()
        self.check_no_privileged()
        self.check_no_socket_mount()
        self.check_no_secrets()
        self.check_health_checks()
        self.check_cost_thresholds()
        self.check_worker_deny()
        self.check_worker_no_db_access()
        self.check_security_opts()
        self.check_no_external_networks()
        self.check_roles_have_tasks()
        self.check_evidence_structure()
        self.check_runbooks()
        self.check_single_infra_root()
        self.check_ansible_syntax()
        self.check_ansible_lint()
        self.check_compose_render()
        self.check_shellcheck()
        self.check_gitleaks()
        self.check_scaffold_scan()

    def run_targeted(self, check_ids):
        check_map = {
            "SOURCE-IDENTITY": self.check_source_identity,
            "YAML-PARSE": self.check_yaml_parsing,
            "JSON-PARSE": self.check_json_parsing,
            "SCHEMA-VALID": self.check_schema_validity,
            "SCHEMA-FIXTURES": self.check_schema_fixtures,
            "NO-LATEST-TAGS": self.check_no_latest_tags,
            "DIGEST-LOCK": self.check_digest_lock,
            "DIGEST-PROOF": self.check_digest_proof,
            "DIGEST-REGISTRY": self.check_digest_registry,
            "HOST-KEY-CHECKING": self.check_host_key_checking,
            "NO-DB-PORTS": self.check_no_published_ports,
            "NO-PRIV": self.check_no_privileged,
            "NO-SOCKET": self.check_no_socket_mount,
            "NO-SECRETS": self.check_no_secrets,
            "HEALTH-CHECKS": self.check_health_checks,
            "COST-THRESHOLDS": self.check_cost_thresholds,
            "WORKER-DENY": self.check_worker_deny,
            "WORKER-NO-DB": self.check_worker_no_db_access,
            "SECURITY-OPTS": self.check_security_opts,
            "NO-EXTERNAL-NET": self.check_no_external_networks,
            "ROLES-TASKS": self.check_roles_have_tasks,
            "EVIDENCE-DIR": self.check_evidence_structure,
            "RUNBOOKS": self.check_runbooks,
            "SINGLE-ROOT": self.check_single_infra_root,
            "ANSIBLE-SYNTAX": self.check_ansible_syntax,
            "ANSIBLE-LINT": self.check_ansible_lint,
            "COMPOSE-RENDER": self.check_compose_render,
            "SHELLCHECK": self.check_shellcheck,
            "GITLEAKS": self.check_gitleaks,
            "SCAFFOLD-SCAN": self.check_scaffold_scan,
            "FAIL-CLOSED": self.check_fail_closed,
            "EVIDENCE-CONSISTENCY": self.check_evidence_consistency,
            "TOTALS-CONSIST": lambda: self.check_totals_consistency({}),
            "RUN-ID-CONSISTENCY": self.check_run_id_consistency,
            "META-TEST-EVIDENCE": self.check_meta_test_evidence,
        }
        self.check_source_identity()
        # R3G: --only must run the REQUESTED checks even when SOURCE-IDENTITY
        # fails (e.g. a local clone with a non-accepted origin). Gating the
        # requested checks on source identity silently turned --only runs into
        # no-ops, breaking the adversarial suite and regression tests.
        for cid in check_ids:
            if cid == "SOURCE-IDENTITY":
                continue
            if cid in check_map:
                check_map[cid]()

    # ===== ATOMIC EVIDENCE WRITING =====

    def _atomic_write(self, path, content):
        dir_path = path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            shutil.move(tmp_path, str(path))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def write_evidence(self, git_info):
        ev_dir = self._evidence_dir()

        pre_totals = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
        for r in self.results:
            if r.check_id in ("TOTALS-CONSIST", "FAIL-CLOSED", "EVIDENCE-CONSISTENCY",
                               "RUN-ID-CONSISTENCY", "META-TEST-EVIDENCE"):
                continue
            if r.result in pre_totals:
                pre_totals[r.result] += 1
        pre_totals["total"] = sum(pre_totals.values())

        self.check_totals_consistency(pre_totals)
        if self.phase != "initial":
            # R3G: adversarial-evidence checks run ONLY in the final phase.
            self.check_fail_closed()
            self.check_meta_test_evidence()
            self.check_run_id_consistency()

        payload = self._build_results_payload(git_info)
        if self.phase != "initial":
            self.check_evidence_consistency()

        payload["results"] = [r.to_dict() for r in self.results]
        payload["totals"] = self.compute_totals()
        payload["gate"] = self.determine_gate(payload["totals"])

        results_json = json.dumps(payload, indent=2, ensure_ascii=False)
        self._atomic_write(ev_dir / "static-validation-results.json", results_json)
        self.write_summary_md(git_info, payload["totals"], payload["gate"], ev_dir)
        self.write_stage_status(git_info, payload["totals"], payload["gate"], ev_dir)
        if self.phase == "final":
            self.write_evidence_manifest(ev_dir)

        return payload["gate"], payload["totals"]

    def write_evidence_manifest(self, ev_dir):
        """R3G: SHA-256 inventory of required evidence artifacts."""
        import hashlib
        required = [
            "static-validation-results.json",
            "static-validation-summary.md",
            "adversarial-results.json",
            "stage-status.json",
            "worktree-cleanup.json",
            "regression-output.txt",
            "stage-log.txt",
        ]
        artifacts = []
        for name in required:
            p = Path(ev_dir) / name
            if not p.exists():
                continue
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            artifacts.append({"path": name, "sha256": h.hexdigest(),
                              "size": p.stat().st_size})
        manifest = {
            "schema_version": VERSION,
            "run_id": self.run_uid,
            "validator_version": VERSION,
            "increment": "B1-I1R3H",
            "generated_at": utc_now(),
            "artifacts": artifacts,
        }
        self._atomic_write(
            Path(ev_dir) / "evidence-manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

    def write_evidence_targeted(self, git_info):
        ev_dir = self._evidence_dir()
        pre_totals = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
        for r in self.results:
            if r.check_id in ("TOTALS-CONSIST", "FAIL-CLOSED", "EVIDENCE-CONSISTENCY",
                               "RUN-ID-CONSISTENCY", "META-TEST-EVIDENCE"):
                continue
            if r.result in pre_totals:
                pre_totals[r.result] += 1
        pre_totals["total"] = sum(pre_totals.values())
        self.check_totals_consistency(pre_totals)
        totals = self.compute_totals()
        gate = self.determine_gate(totals)
        payload = {
            "schema_version": VERSION,
            "run_id": self.run_uid,
            "validator_version": VERSION,
            "start_time": self.start_time,
            "end_time": utc_now(),
            "tested_commit": git_info.get("commit", "unknown"),
            "tested_tree": git_info.get("tree", "unknown"),
            "tested_branch": self._identity_provenance()["observed_git_branch"],
            "repository": "dabiggestpoppa/larger-lab",
            "command": "validate_engine.py --only",
            "tools": {
                k: get_tool_version(v)
                for k, v in [
                    ("python", "python3"), ("ansible", "ansible-playbook"),
                    ("ansible_lint", "ansible-lint"), ("docker", "docker"),
                    ("shellcheck", "shellcheck"), ("gitleaks", "gitleaks"),
                ]
            },
            "results": [r.to_dict() for r in self.results],
            "totals": totals,
            "gate": gate,
        }
        self._atomic_write(
            ev_dir / "static-validation-results.json",
            json.dumps(payload, indent=2, ensure_ascii=False),
        )
        return gate, totals

    def determine_gate(self, totals):
        if totals["total"] == 0:
            return "FAILED"
        if totals["FAIL"] > 0:
            return "FAILED"
        if totals["BLOCKED"] > 0:
            return "BLOCKED"
        return "READY_FOR_OPERATOR_REVIEW"

    def write_summary_md(self, git_info, totals, gate, ev_dir=None):
        ev_dir = ev_dir or self._evidence_dir()
        ident = self._identity_provenance()
        lines = [
            f"# B1-I1R3H Static Validation Summary",
            "",
            f"- **Run ID:** `{self.run_uid}`",
            f"- **Validator:** v{VERSION}",
            f"- **Phase:** `{self.phase or 'unspecified'}`",
            f"- **Tested commit:** `{git_info.get('commit', 'unknown')}`",
            f"- **Observed git branch:** `{ident['observed_git_branch']}`",
            f"- **Trusted CI ref:** `{ident['trusted_ci_ref'] or 'none'}`",
            f"- **Checkout state:** `{ident['checkout_state']}`",
            f"- **Branch provenance:** `{ident['branch_provenance']}`",
            f"- **Expected branch:** `{ident['expected_branch']}`",
            f"- **Repository:** `dabiggestpoppa/larger-lab`",
            f"- **Start:** {self.start_time}",
            f"- **End:** {utc_now()}",
            f"- **Gate:** `{gate}`",
            "",
            "## Totals",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| Total | {totals['total']} |",
            f"| PASS | {totals['PASS']} |",
            f"| FAIL | {totals['FAIL']} |",
            f"| BLOCKED | {totals['BLOCKED']} |",
            f"| SKIPPED | {totals['SKIPPED']} |",
            "",
            "## Results",
            "",
            "| Check ID | Mandatory | Result | Evidence |",
            "|----------|-----------|--------|----------|",
        ]
        for r in self.results:
            lines.append(f"| `{r.check_id}` | {'yes' if r.mandatory else 'no'} | {r.result} | {r.evidence} |")
        lines.extend(["", "## Failures and Blocks", ""])
        problems = [r for r in self.results if r.result in ("FAIL", "BLOCKED")]
        if problems:
            for r in problems:
                lines.extend([f"### {r.check_id} — {r.result}", f"- {r.description}",
                              f"- {r.evidence}", f"- {r.output}", ""])
        else:
            lines.extend(["None.", ""])
        lines.extend([f"---", f"*Generated by validate_engine.py v{VERSION} — {utc_now()}*"])
        self._atomic_write(ev_dir / "static-validation-summary.md", "\n".join(lines) + "\n")

    def write_stage_status(self, git_info, totals, gate, ev_dir=None):
        ev_dir = ev_dir or self._evidence_dir()
        ident = self._identity_provenance()
        status = {
            "block": "B1",
            "increment": "B1-I1R3H",
            "run_id": self.run_uid,
            "validator_version": VERSION,
            "phase": self.phase or "unspecified",
            "implementation_commit": git_info.get("commit", "unknown"),
            "implementation_tree": git_info.get("tree", "unknown"),
            "implementation_branch": ident["identity_branch"],
            "observed_git_branch": ident["observed_git_branch"],
            "trusted_ci_ref": ident["trusted_ci_ref"],
            "branch_provenance": ident["branch_provenance"],
            "checkout_state": ident["checkout_state"],
            "evidence_commit": None,
            "gate_status": gate,
            "totals": totals,
            "unresolved_blockers": [],
            "cost_impact_usd": 0,
            "cloud_mutations": 0,
            "next_authorized_action": "Operator review of B1-I1R3H evidence",
        }
        for r in self.results:
            if r.result == "BLOCKED":
                status["unresolved_blockers"].append({
                    "check_id": r.check_id,
                    "reason": r.evidence,
                    "dependency": r.output,
                })
        self._atomic_write(
            ev_dir / "stage-status.json",
            json.dumps(status, indent=2, ensure_ascii=False),
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(description=f"OCE Cloud Ground Validation Engine v{VERSION}")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--authoritative", action="store_true",
                        help="Authoritative mode: enforce strict identity proof")
    parser.add_argument("--phase", type=str, choices=["initial", "final"], default=None,
                        help="R3G: explicit validation phase (mandatory in authoritative mode)")
    parser.add_argument("--target-commit", type=str, help="Expected implementation SHA")
    parser.add_argument("--target-tree", type=str, help="Expected tree SHA")
    parser.add_argument("--target-branch", type=str, help="Expected branch name")
    parser.add_argument("--evidence-dir", type=str, default=None,
                        help="Override evidence output directory")
    parser.add_argument("--only", type=str, help="Comma-separated check IDs to run")
    parser.add_argument("--version-json", action="store_true",
                        help="Emit machine-readable version info and exit")
    args = parser.parse_args()

    if args.version_json:
        print(json.dumps({"validator_version": VERSION,
                          "supported_schema_versions": [VERSION],
                          "increment": "B1-I1R3H"}))
        sys.exit(0)

    if args.authoritative:
        missing = []
        if not args.target_commit:
            missing.append("--target-commit")
        if not args.target_tree:
            missing.append("--target-tree")
        if not args.target_branch:
            missing.append("--target-branch")
        if not args.phase:
            missing.append("--phase initial|final")
        if not args.evidence_dir:
            missing.append("--evidence-dir (must be outside the repository)")
        if missing:
            print(f"ERROR: Authoritative mode requires: {', '.join(missing)}")
            sys.exit(1)

    validator = Validator(
        target_commit=args.target_commit,
        target_tree=args.target_tree,
        target_branch=args.target_branch,
        authoritative=args.authoritative,
        evidence_dir=args.evidence_dir,
        phase=args.phase,
    )

    if args.only:
        check_ids = [c.strip() for c in args.only.split(",")]
        validator.run_targeted(check_ids)
        git_info = get_git_info()
        gate, totals = validator.write_evidence_targeted(git_info)
        results = validator.results
        has_fail = any(r.result == "FAIL" for r in results)
        sys.exit(1 if has_fail else 0)
    elif args.all:
        validator.run_all_checks()
    else:
        validator.run_all_checks()

    git_info = get_git_info()
    gate, totals = validator.write_evidence(git_info)

    print(f"\n{'='*50}")
    print(f"  B1-I1R3H Validation ({validator.phase or 'unspecified'} phase) — {gate}")
    print(f"{'='*50}")
    print(f"  Run ID:    {validator.run_uid}")
    print(f"  Commit:    {git_info.get('commit', 'unknown')[:12]}")
    print(f"  Total:     {totals['total']}")
    print(f"  PASS:      {totals['PASS']}")
    print(f"  FAIL:      {totals['FAIL']}")
    print(f"  BLOCKED:   {totals['BLOCKED']}")
    print(f"  SKIPPED:   {totals['SKIPPED']}")
    print(f"  Gate:      {gate}")
    print(f"{'='*50}")

    if gate != "READY_FOR_OPERATOR_REVIEW":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
