#!/usr/bin/env python3
"""
OCE Cloud Ground — Validation Engine
B1-I1R3C — Evidence Isolation and Final Gate Closure
Version: 3.3.0

Mandatory checks: 29
- SOURCE-IDENTITY (first, fail-closed)
- YAML-PARSE, JSON-PARSE, SCHEMA-VALID, SCHEMA-FIXTURES
- NO-LATEST-TAGS, DIGEST-LOCK, NO-DB-PORTS, NO-PRIV, NO-SOCKET, NO-SECRETS
- HEALTH-CHECKS, COST-THRESHOLDS
- WORKER-DENY, WORKER-NO-DB, SECURITY-OPTS, NO-EXTERNAL-NET
- ROLES-TASKS, EVIDENCE-DIR, RUNBOOKS, SINGLE-ROOT
- ANSIBLE-SYNTAX, ANSIBLE-LINT, COMPOSE-RENDER, SHELLCHECK, GITLEAKS
- SCAFFOLD-SCAN, TOTALS-CONSIST, FAIL-CLOSED, EVIDENCE-CONSISTENCY

SOURCE-IDENTITY aborts before all other checks on failure.
"""

import json
import os
import re
import subprocess
import sys
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
import shutil

VERSION = "3.3.0"
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
REPO_ROOT = BASE_DIR.parent.parent  # infrastructure/cloud-ground -> repo root
EVIDENCE_DIR = BASE_DIR / "evidence"
CONTRACTS_DIR = BASE_DIR / "contracts"
COMPOSE_DIR = BASE_DIR / "compose"
POLICY_DIR = BASE_DIR / "policy"
ANSIBLE_DIR = BASE_DIR / "ansible"
IDENTITY_DATA = CONTRACTS_DIR / "checkpoint-identity-data.json"


def run_id():
    return uuid.uuid4().hex[:12]


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
    info = {}
    for key, cmd in [("branch", ["branch", "--show-current"]),
                      ("commit", ["rev-parse", "HEAD"]),
                      ("tree", ["rev-parse", "HEAD^{tree}"]),
                      ("remote_url", ["remote", "get-url", "origin"]),
                      ("repo_root", ["rev-parse", "--show-toplevel"])]:
        info[key] = git_cmd(["-C", str(REPO_ROOT)] + cmd) or "unknown"
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
    def __init__(self, target_commit=None, target_tree=None, target_branch=None, authoritative=False, evidence_dir=None):
        self.results = []
        self.run_uid = run_id()
        self.start_time = utc_now()
        self.source_identity_passed = False
        self.target_commit = target_commit  # expected impl SHA (for --target-commit)
        self.target_tree = target_tree
        self.target_branch = target_branch
        self.authoritative = authoritative
        self.evidence_dir_override = Path(evidence_dir) if evidence_dir else None

    def add(self, check_id, description, mandatory, result, evidence="", output=""):
        self.results.append(CheckResult(check_id, description, mandatory, result, evidence, output))

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

    # ===== SOURCE-IDENTITY (CHECK 1 — MANDATORY FIRST) =====
    def check_source_identity(self):
        """Positively prove repository, branch, commit, tree, path, workflow identity.
        Every mismatch is a mandatory failure. Abort all other checks on failure."""
        git = get_git_info()
        errors = []

        # Load identity contract
        if not IDENTITY_DATA.exists():
            self.add("SOURCE-IDENTITY", "Source identity verification", True,
                     "BLOCKED", "checkpoint-identity-data.json not found", "")
            return

        try:
            contract = json.loads(IDENTITY_DATA.read_text(encoding="utf-8"))
        except Exception as e:
            self.add("SOURCE-IDENTITY", "Source identity verification", True,
                     "BLOCKED", f"Cannot parse identity contract: {e}", "")
            return

        # 1. Repository identity — check owner, name, and full_name separately
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

        # 2. Remote identity — strip .git suffix properly (not rstrip which strips individual chars)
        remote_url = git.get("remote_url", "")
        accepted = contract.get("accepted_origins", [])
        def strip_git_suffix(s):
            return s[:-4] if s.endswith(".git") else s
        remote_normalized = strip_git_suffix(remote_url) if remote_url else ""
        accepted_normalized = [strip_git_suffix(o) for o in accepted]
        if remote_normalized not in accepted_normalized and remote_url not in accepted:
            errors.append(f"REMOTE: '{remote_url}' not in accepted origins {accepted}")

        # 3. Branch identity
        actual_branch = git.get("branch", "")
        expected_branch = self.target_branch or contract.get("authorized_branch", "")
        if expected_branch and actual_branch != expected_branch:
            errors.append(f"BRANCH: expected '{expected_branch}', got '{actual_branch}'")

        # 4. Implementation commit identity
        actual_commit = git.get("commit", "")
        expected_commit = self.target_commit or contract.get("expected_implementation_commit_source", "")
        if expected_commit and expected_commit.strip() and actual_commit != expected_commit:
            errors.append(f"COMMIT: expected '{expected_commit[:12]}', got '{actual_commit[:12]}'")

        # 5. Tree identity
        actual_tree = git.get("tree", "")
        expected_tree = self.target_tree or contract.get("expected_tree_sha", "")
        if expected_tree and expected_tree.strip() and actual_tree != expected_tree:
            errors.append(f"TREE: expected '{expected_tree[:12]}', got '{actual_tree[:12]}'")

        # 6. Project root
        expected_root = contract.get("expected_project_root", "")
        actual_root_rel = str(BASE_DIR.relative_to(REPO_ROOT)).replace('\\', '/')
        if expected_root and actual_root_rel != expected_root:
            errors.append(f"PROJECT_ROOT: expected '{expected_root}', got '{actual_root_rel}'")

        # 7. Authoritative base SHA — HEAD must be base or descendant of base
        expected_base = contract.get("authoritative_base_sha", "")
        if expected_base and expected_base.strip() and actual_commit:
            if actual_commit != expected_base:
                # HEAD is not the base itself — check if base is ancestor of HEAD
                r = subprocess.run(
                    ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", expected_base, actual_commit],
                    capture_output=True, text=True, timeout=10
                )
                if r.returncode != 0:
                    errors.append(f"BASE_SHA: {actual_commit[:12]} is not a descendant of base {expected_base[:12]}")

        # 8. CI environment (GitHub Actions)
        gha_repo = os.environ.get("GITHUB_REPOSITORY", "")
        gha_ref = os.environ.get("GITHUB_REF_NAME", "")
        gha_sha = os.environ.get("GITHUB_SHA", "")
        if gha_repo:
            # Running in CI — enforce strict matching
            if gha_repo != "dabiggestpoppa/larger-lab":
                errors.append(f"GITHUB_REPOSITORY: expected dabiggestpoppa/larger-lab, got {gha_repo}")
            if gha_sha and actual_commit and gha_sha != actual_commit:
                errors.append(f"GITHUB_SHA: {gha_sha[:12]} does not match HEAD {actual_commit[:12]}")
            if gha_ref:
                expected_branch_ci = self.target_branch or contract.get("authorized_branch", "")
                if expected_branch_ci and gha_ref != expected_branch_ci:
                    errors.append(f"GITHUB_REF_NAME: expected '{expected_branch_ci}', got '{gha_ref}'")

        # 9. Authoritative mode — strict identity proof
        if self.authoritative:
            # All identity inputs are mandatory
            if not self.target_commit or not self.target_commit.strip():
                errors.append("AUTHORITATIVE: --target-commit is mandatory in authoritative mode")
            if not self.target_tree or not self.target_tree.strip():
                errors.append("AUTHORITATIVE: --target-tree is mandatory in authoritative mode")
            if not self.target_branch or not self.target_branch.strip():
                errors.append("AUTHORITATIVE: --target-branch is mandatory in authoritative mode")

            # HEAD must equal target commit
            if actual_commit and self.target_commit and actual_commit != self.target_commit:
                errors.append(f"AUTHORITATIVE: HEAD {actual_commit[:12]} != target commit {self.target_commit[:12]}")

            # HEAD^{{tree}} must equal target tree
            if actual_tree and self.target_tree and actual_tree != self.target_tree:
                errors.append(f"AUTHORITATIVE: tree {actual_tree[:12]} != target tree {self.target_tree[:12]}")

            # CI-specific authoritative checks
            if gha_repo:
                if gha_sha and actual_commit and gha_sha != actual_commit:
                    errors.append(f"AUTHORITATIVE: GITHUB_SHA {gha_sha[:12]} != HEAD {actual_commit[:12]}")
                if gha_ref and self.target_branch and gha_ref != self.target_branch:
                    errors.append(f"AUTHORITATIVE: GITHUB_REF_NAME '{gha_ref}' != '{self.target_branch}'")
                if gha_repo != "dabiggestpoppa/larger-lab":
                    errors.append(f"AUTHORITATIVE: GITHUB_REPOSITORY '{gha_repo}' != 'dabiggestpoppa/larger-lab'")

            # Ancestry from authoritative_base_sha
            expected_base = contract.get("authoritative_base_sha", "")
            if expected_base and expected_base.strip() and actual_commit:
                if actual_commit != expected_base:
                    r = subprocess.run(
                        ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", expected_base, actual_commit],
                        capture_output=True, text=True, timeout=10
                    )
                    if r.returncode != 0:
                        errors.append(f"AUTHORITATIVE: HEAD is not descendant of base {expected_base[:12]}")

            # Worktree must be clean
            r = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                capture_output=True, text=True, timeout=10
            )
            if r.stdout.strip():
                errors.append(f"AUTHORITATIVE: worktree not clean — {len(r.stdout.strip().splitlines())} dirty files")

        if errors:
            self.add("SOURCE-IDENTITY", "Source identity verification", True,
                     "FAIL", f"{len(errors)} mismatches", "\n".join(errors))
        else:
            evidence_parts = [
                f"repo={expected_full}",
                f"branch={actual_branch}",
                f"commit={actual_commit[:12]}",
                f"tree={actual_tree[:12]}",
                f"root={actual_root_rel}",
            ]
            if gha_repo:
                evidence_parts.append(f"gha_repo={gha_repo}")
                evidence_parts.append(f"gha_sha={gha_sha[:12]}")
            self.add("SOURCE-IDENTITY", "Source identity verification", True,
                     "PASS", ", ".join(evidence_parts), "All identity checks passed")

        self.source_identity_passed = any(r.check_id == "SOURCE-IDENTITY" and r.result == "PASS"
                                          for r in self.results)

    # ===== STATIC CHECKS (CHECKS 2-18) =====
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
            self.add("YAML-PARSE", "YAML files parse correctly", True, "FAIL", f"{passed}/{total}", "\n".join(details[:10]))

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
            self.add("JSON-PARSE", "JSON contract files parse", True, "FAIL", f"{passed}/{total}", "\n".join(details[:10]))

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
                self.add("SCHEMA-VALID", "JSON Schemas valid Draft 2020-12", True, "BLOCKED", "jsonschema not installed", "")
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
            self.add("SCHEMA-VALID", "JSON Schemas valid Draft 2020-12", True, "FAIL", f"{passed}/{total}", "\n".join(details))

    def check_schema_fixtures(self):
        fixtures_dir = BASE_DIR / "tests" / "fixtures"
        if not fixtures_dir.exists():
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "BLOCKED", "No fixtures dir", "")
            return
        try:
            import jsonschema
        except ImportError:
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "BLOCKED", "jsonschema not installed", "")
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
            self.add("SCHEMA-FIXTURES", "Schema fixture tests pass", True, "FAIL", f"{passed}/{total}", "\n".join(details))

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
            self.add("NO-LATEST-TAGS", "No :latest image tags", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-LATEST-TAGS", "No :latest image tags", True, "PASS", "0 violations", "Clean")

    def check_digest_lock(self):
        """Verify all image references use @sha256: digests, not tag-only."""
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
        """Verify compose digests match real registry-proven digests in evidence."""
        # Read canonical image-digests from the base evidence dir (not override)
        evidence_path = EVIDENCE_DIR / "image-digests.json"
        if not evidence_path.exists():
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True,
                     "BLOCKED", "image-digests.json not found", "Generate digest evidence first")
            return
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                evidence = json.load(f)
        except Exception as e:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True,
                     "BLOCKED", f"Cannot parse image-digests.json: {e}", "")
            return

        # Build evidence digest map
        evidence_digests = {}
        for img in evidence.get("images", []):
            evidence_digests[img["name"]] = img.get("digest", "")
        verified_digests = {}
        for img in evidence.get("images", []):
            if img.get("verified_digest", False):
                verified_digests[img["name"]] = img.get("digest", "")

        # Check compose images against evidence
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True,
                     "BLOCKED", "compose.foundation.yml not found", "")
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
                # Extract image name from ref like postgres@sha256:...
                parts = img_ref.split("@")
                img_name = parts[0] if parts else ""
                img_digest = parts[1] if len(parts) > 1 else ""
                if img_name in evidence_digests:
                    expected_digest = evidence_digests[img_name]
                    if img_digest != expected_digest:
                        violations.append(
                            f"{img_name}: compose={img_digest[:20]}... evidence={expected_digest[:20]}...")
                elif img_name:
                    violations.append(f"{img_name}: no digest proof in image-digests.json")

        # Check all evidence images are verified
        unverified = [name for name, digest in evidence_digests.items()
                      if name not in verified_digests]

        if violations:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True,
                     "FAIL", f"{len(violations)} mismatches", "\n".join(violations))
        elif unverified:
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True,
                     "FAIL", f"{len(unverified)} unverified", f"Unverified: {', '.join(unverified)}")
        else:
            verified_count = len(verified_digests)
            self.add("DIGEST-PROOF", "Image digests match registry evidence", True,
                     "PASS", f"{verified_count} verified digests",
                     "All compose digests match registry-proven evidence")

    def check_digest_registry(self):
        """Verify image digests resolve against the registry using available tools."""
        # Read canonical image-digests from the base evidence dir (not override)
        evidence_path = EVIDENCE_DIR / "image-digests.json"
        if not evidence_path.exists():
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True,
                     "BLOCKED", "image-digests.json not found", "")
            return
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                evidence = json.load(f)
        except Exception as e:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True,
                     "BLOCKED", f"Cannot parse image-digests.json: {e}", "")
            return

        # Try available tools in order: docker buildx imagetools inspect, docker manifest inspect, skopeo
        verify_cmd = None
        verify_format = None
        for cmd, fmt in [
            ("docker", "buildx-inspect"),
            ("skopeo", "skopeo"),
        ]:
            try:
                r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    verify_cmd = cmd
                    verify_format = fmt
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if not verify_cmd:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True,
                     "BLOCKED", "No registry verification tool available (need docker or skopeo)",
                     "Install docker or skopeo for real-time digest verification")
            return

        images = evidence.get("images", [])
        resolved, failed, details = 0, 0, []
        for img in images:
            name = img.get("name", "")
            digest = img.get("digest", "")
            if not digest:
                failed += 1
                details.append(f"{name}: no digest in evidence")
                continue

            full_ref = f"{name}@{digest}"
            try:
                if verify_format == "buildx-inspect":
                    r = subprocess.run(
                        ["docker", "buildx", "imagetools", "inspect", full_ref],
                        capture_output=True, text=True, timeout=30
                    )
                elif verify_format == "skopeo":
                    r = subprocess.run(
                        ["skopeo", "inspect", f"docker://{full_ref}"],
                        capture_output=True, text=True, timeout=30
                    )
                else:
                    r = subprocess.CompletedProcess([], 1)

                if r.returncode == 0 and ("Manifests" in r.stdout or "MediaType" in r.stdout or "SchemaVersion" in r.stdout):
                    resolved += 1
                    details.append(f"{name}@{digest[:20]}...: RESOLVED")
                else:
                    failed += 1
                    details.append(f"{name}@{digest[:20]}...: FAILED ({r.stderr[:100] if r.stderr else 'no match in output'})")
            except subprocess.TimeoutExpired:
                failed += 1
                details.append(f"{name}@{digest[:20]}...: TIMEOUT")
            except FileNotFoundError:
                failed += 1
                details.append(f"{name}@{digest[:20]}...: TOOL NOT FOUND")

        if failed > 0:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True,
                     "FAIL", f"{failed}/{len(images)} failed",
                     "\n".join(details))
        elif resolved == 0:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True,
                     "BLOCKED", "No images to verify", "")
        else:
            self.add("DIGEST-REGISTRY", "Image digests resolve against registry", True,
                     "PASS", f"{resolved}/{len(images)} resolved",
                     "\n".join(details))

    def check_host_key_checking(self):
        """Verify ansible.cfg has host_key_checking = True (not False)."""
        cfg_path = ANSIBLE_DIR / "ansible.cfg"
        if not cfg_path.exists():
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True,
                     "BLOCKED", "ansible.cfg not found", "")
            return
        content = self._read_file(cfg_path)
        lines = content.split("\n")
        violations = []
        found = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "host_key_checking" in stripped.lower():
                found = True
                if "false" in stripped.lower() or "= 0" in stripped or "=no" in stripped.lower():
                    violations.append(f"Line {i}: {stripped}")
                elif "true" in stripped.lower() or "= 1" in stripped or "=yes" in stripped.lower():
                    pass  # Good
                else:
                    violations.append(f"Line {i}: unrecognised value: {stripped}")
        if not found:
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True,
                     "FAIL", "host_key_checking not set in ansible.cfg",
                     "Must explicitly set host_key_checking = True")
        elif violations:
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True,
                     "FAIL", f"{len(violations)} violations",
                     "\n".join(violations))
        else:
            self.add("HOST-KEY-CHECKING", "Ansible host_key_checking is True", True,
                     "PASS", "host_key_checking = True", "Verified")

    def check_no_published_ports(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("NO-DB-PORTS", "No published DB/cache ports", True, "BLOCKED", "compose.foundation.yml not found", "")
            return
        content = self._read_file(foundation)
        violations = []
        in_services = False
        current_service = ""
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
            self.add("NO-DB-PORTS", "No published DB/cache ports", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-DB-PORTS", "No published DB/cache ports", True, "PASS", "0 violations", "Clean")

    def check_no_privileged(self):
        compose_files = self._find_files(COMPOSE_DIR, "*.yml")
        violations = []
        for f in compose_files:
            content = self._read_file(f)
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "privileged:" in stripped and "true" in stripped:
                    violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {stripped}")
        if violations:
            self.add("NO-PRIV", "No privileged containers", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-PRIV", "No privileged containers", True, "PASS", "0 violations", "Clean")

    def check_no_socket_mount(self):
        compose_files = self._find_files(COMPOSE_DIR, "*.yml")
        violations = []
        for f in compose_files:
            content = self._read_file(f)
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "docker.sock" in stripped:
                    violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {stripped}")
        if violations:
            self.add("NO-SOCKET", "No Docker socket mounts", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
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
                content = self._read_file(f)
                for i, line in enumerate(content.split("\n"), 1):
                    stripped = line.lstrip()
                    if stripped.startswith("#"):
                        continue
                    if any(kw in stripped.upper() for kw in ["PLACEHOLDER", "CHANGE_ME", "REPLACE", "EXAMPLE"]):
                        continue
                    if re.search(pattern, stripped, re.IGNORECASE):
                        violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {desc}")
                        break
        if violations:
            self.add("NO-SECRETS", "No embedded secrets", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-SECRETS", "No embedded secrets", True, "PASS", "0 violations", "Clean")

    def check_health_checks(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("HEALTH-CHECKS", "Health checks on foundation services", True, "BLOCKED", "compose.foundation.yml not found", "")
            return
        content = self._read_file(foundation)
        hc_count = content.count("healthcheck:")
        if hc_count >= 2:
            self.add("HEALTH-CHECKS", "Health checks on foundation services", True, "PASS", f"{hc_count} health checks", "Both services")
        else:
            self.add("HEALTH-CHECKS", "Health checks on foundation services", True, "FAIL", f"{hc_count} health checks", f"Need 2+, found {hc_count}")

    def check_cost_thresholds(self):
        cost_file = POLICY_DIR / "cost-guardrails.yml"
        if not cost_file.exists():
            self.add("COST-THRESHOLDS", "Cost thresholds match ratification", True, "FAIL", "cost-guardrails.yml not found", "")
            return
        content = self._read_file(cost_file)
        checks = [
            ("fixed_baseline_warning: 60", "$60 warning"),
            ("burst_hard_stop: 50", "$50 burst stop"),
            ("total_approval_gate: 100", "$100 total gate"),
        ]
        missing = [desc for pattern, desc in checks if pattern not in content]
        if missing:
            self.add("COST-THRESHOLDS", "Cost thresholds match ratification", True, "FAIL", f"Missing: {', '.join(missing)}", "")
        else:
            self.add("COST-THRESHOLDS", "Cost thresholds match ratification", True, "PASS", "All thresholds", "$60/$50/$100")

    def check_worker_deny(self):
        """Verify 14+ worker denial rules: 3 classes × 4 services (postgresql, redis, ssh, docker) + admin rules."""
        policy = POLICY_DIR / "network-access.yml"
        if not policy.exists():
            self.add("WORKER-DENY", "Workers denied DB/Redis/SSH/Docker", True, "FAIL", "network-access.yml not found", "")
            return
        content = self._read_file(policy)
        deny_count = content.count("action: DENY")
        if deny_count >= 12:
            self.add("WORKER-DENY", "Workers denied DB/Redis/SSH/Docker", True, "PASS",
                     f"{deny_count} DENY rules", f"{deny_count} denial rules")
        else:
            self.add("WORKER-DENY", "Workers denied DB/Redis/SSH/Docker", True, "FAIL",
                     f"{deny_count} DENY rules", f"Need 12+, found {deny_count}")

    def check_worker_no_db_access(self):
        """Verify YAML-parsed worker denial: each worker class denied postgresql, redis, ssh, docker."""
        policy = POLICY_DIR / "network-access.yml"
        if not policy.exists():
            self.add("WORKER-NO-DB", "Workers denied direct DB access (YAML-parsed)", True, "FAIL", "network-access.yml not found", "")
            return
        try:
            import yaml
            with open(policy, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except ImportError:
            self.add("WORKER-NO-DB", "Workers denied direct DB access (YAML-parsed)", True, "BLOCKED", "pyyaml not installed", "")
            return
        except Exception as e:
            self.add("WORKER-NO-DB", "Workers denied direct DB access (YAML-parsed)", True, "FAIL", f"Parse error: {e}", "")
            return

        rules = data.get("rules", []) if data else []
        required = []
        for worker in ["worker-local", "worker-burst", "worker-windows"]:
            for service in ["postgresql", "redis", "ssh", "docker"]:
                required.append((worker, service))

        found = 0
        missing = []
        for worker, service in required:
            found_rule = False
            for rule in rules:
                if (rule.get("from") == worker and rule.get("to") == service and rule.get("action") == "DENY"):
                    found_rule = True
                    break
            if found_rule:
                found += 1
            else:
                missing.append(f"{worker}->{service}")

        total = len(required)
        if found >= total:
            self.add("WORKER-NO-DB", "Workers denied direct DB access (YAML-parsed)", True, "PASS",
                     f"{found}/{total} rules", "All worker classes denied all protected services")
        else:
            self.add("WORKER-NO-DB", "Workers denied direct DB access (YAML-parsed)", True, "FAIL",
                     f"{found}/{total} rules", f"Missing: {', '.join(missing)}")

    def check_security_opts(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("SECURITY-OPTS", "Security options present", True, "BLOCKED", "compose.foundation.yml not found", "")
            return
        content = self._read_file(foundation)
        count = content.count("no-new-privileges")
        if count >= 2:
            self.add("SECURITY-OPTS", "Security options (no-new-privileges)", True, "PASS", f"{count} declarations", "Both hardened")
        else:
            self.add("SECURITY-OPTS", "Security options (no-new-privileges)", True, "FAIL", f"{count} declarations", f"Need 2+, found {count}")

    def check_no_external_networks(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("NO-EXTERNAL-NET", "No external networks", True, "BLOCKED", "compose.foundation.yml not found", "")
            return
        content = self._read_file(foundation)
        violations = []
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "external:" in stripped and "true" in stripped:
                violations.append(f"Line {i}: {stripped}")
        if violations:
            self.add("NO-EXTERNAL-NET", "No external networks", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("NO-EXTERNAL-NET", "No external networks", True, "PASS", "0 violations", "Clean")

    def check_roles_have_tasks(self):
        roles_dir = ANSIBLE_DIR / "roles"
        if not roles_dir.exists():
            self.add("ROLES-TASKS", "All Ansible roles have tasks", True, "BLOCKED", "No roles dir", "")
            return
        empty = []
        for role in sorted(roles_dir.iterdir()):
            if role.is_dir() and not (role / "tasks" / "main.yml").exists():
                empty.append(role.name)
        total = len([d for d in roles_dir.iterdir() if d.is_dir()])
        if empty:
            self.add("ROLES-TASKS", "All Ansible roles have tasks", True, "FAIL", f"{len(empty)} empty", f"Empty: {', '.join(empty)}")
        else:
            self.add("ROLES-TASKS", "All Ansible roles have tasks", True, "PASS", f"{total} roles", "All have tasks/main.yml")

    def check_evidence_structure(self):
        has_dir = EVIDENCE_DIR.is_dir()
        has_templates = (EVIDENCE_DIR / "templates").is_dir()
        if has_dir and has_templates:
            self.add("EVIDENCE-DIR", "Evidence directory with templates", True, "PASS", "evidence/ and templates/", "Structure present")
        else:
            self.add("EVIDENCE-DIR", "Evidence directory with templates", True, "FAIL", f"dir={has_dir} templates={has_templates}", "Missing")

    def check_runbooks(self):
        rb_dir = BASE_DIR / "runbooks"
        if rb_dir.exists():
            count = len(list(rb_dir.glob("*.md")))
            if count >= 1:
                self.add("RUNBOOKS", "Operator runbooks present", True, "PASS", f"{count} runbooks", "Present")
            else:
                self.add("RUNBOOKS", "Operator runbooks present", True, "FAIL", "0 runbooks", "No .md in runbooks/")
        else:
            self.add("RUNBOOKS", "Operator runbooks present", True, "FAIL", "No runbooks dir", "Missing")

    def check_single_infra_root(self):
        roots = list(REPO_ROOT.rglob("cloud-ground"))
        roots = [r for r in roots if r.is_dir()]
        if len(roots) <= 1:
            self.add("SINGLE-ROOT", "Single infrastructure root", True, "PASS", f"{len(roots)} roots", "Single canonical root")
        else:
            self.add("SINGLE-ROOT", "Single infrastructure root", True, "FAIL", f"{len(roots)} roots", "Duplicate roots")

    def check_ansible_syntax(self):
        site_yml = ANSIBLE_DIR / "playbooks" / "site.yml"
        hosts_yml = ANSIBLE_DIR / "inventories" / "example" / "hosts.yml"
        if not site_yml.exists():
            self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "BLOCKED", "site.yml not found", "")
            return
        try:
            args = ["ansible-playbook", "--syntax-check", str(site_yml)]
            if hosts_yml.exists():
                args.extend(["-i", str(hosts_yml)])
            r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=str(BASE_DIR))
            if r.returncode == 0:
                self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "PASS", "syntax-check passed", r.stdout[:200])
            else:
                self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "FAIL", "syntax-check failed", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "BLOCKED", "ansible-playbook not installed", "")
        except subprocess.TimeoutExpired:
            self.add("ANSIBLE-SYNTAX", "Ansible playbook syntax valid", True, "BLOCKED", "timeout", "")

    def check_ansible_lint(self):
        try:
            r = subprocess.run(["ansible-lint", str(ANSIBLE_DIR / "playbooks" / "site.yml")],
                               capture_output=True, text=True, timeout=60, cwd=str(ANSIBLE_DIR))
            if r.returncode == 0:
                self.add("ANSIBLE-LINT", "Ansible lint passes", True, "PASS", "ansible-lint clean", r.stdout[:200])
            else:
                self.add("ANSIBLE-LINT", "Ansible lint passes", True, "FAIL", "ansible-lint found issues", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("ANSIBLE-LINT", "Ansible lint passes", True, "BLOCKED", "ansible-lint not installed", "")
        except subprocess.TimeoutExpired:
            self.add("ANSIBLE-LINT", "Ansible lint passes", True, "BLOCKED", "timeout", "")

    def check_compose_render(self):
        foundation = COMPOSE_DIR / "compose.foundation.yml"
        if not foundation.exists():
            self.add("COMPOSE-RENDER", "Compose foundation renders", True, "BLOCKED", "compose.foundation.yml not found", "")
            return
        try:
            env = os.environ.copy()
            env["POSTGRES_PASSWORD"] = "test_password_for_validation"
            r = subprocess.run(["docker", "compose", "-f", str(foundation), "config"],
                               capture_output=True, text=True, timeout=30, env=env, cwd=str(COMPOSE_DIR))
            if r.returncode == 0:
                self.add("COMPOSE-RENDER", "Compose foundation renders", True, "PASS", "docker compose config", "Renders OK")
            else:
                self.add("COMPOSE-RENDER", "Compose foundation renders", True, "FAIL", "docker compose config", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("COMPOSE-RENDER", "Compose foundation renders", True, "BLOCKED", "docker not installed", "")
        except subprocess.TimeoutExpired:
            self.add("COMPOSE-RENDER", "Compose foundation renders", True, "BLOCKED", "timeout", "")

    def check_shellcheck(self):
        scripts = list((BASE_DIR / "scripts").glob("*")) + list((BASE_DIR / "tests").glob("*.sh"))
        scripts = [s for s in scripts if s.is_file() and not s.name.endswith(".py")]
        if not scripts:
            self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "BLOCKED", "No shell scripts", "")
            return
        try:
            all_pass, details = True, []
            for s in scripts:
                # Use --severity=error to only fail on actual errors, not style warnings
                r = subprocess.run(
                    ["shellcheck", "-s", "bash", "--severity=error", str(s)],
                    capture_output=True, text=True, timeout=30
                )
                if r.returncode != 0:
                    all_pass = False
                    details.append(f"{s.name}: {r.stderr[:200]}")
            if all_pass:
                self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "PASS", f"{len(scripts)} scripts", "All clean")
            else:
                self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "FAIL", f"{len(details)} issues", "\n".join(details[:5]))
        except FileNotFoundError:
            self.add("SHELLCHECK", "Shell scripts pass shellcheck", True, "BLOCKED", "shellcheck not installed", "")

    def check_gitleaks(self):
        try:
            r = subprocess.run(["gitleaks", "detect", "--source", str(BASE_DIR), "--no-banner", "--report-format", "json"],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "PASS", "gitleaks clean", "No secrets found")
            else:
                self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "FAIL", "gitleaks found secrets", (r.stdout + r.stderr)[:500])
        except FileNotFoundError:
            self.add("GITLEAKS", "Secret scan passes (gitleaks)", True, "BLOCKED", "gitleaks not installed", "")
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
            content = self._read_file(f)
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                for pattern, desc in scaffold_patterns:
                    if re.search(pattern, stripped, re.IGNORECASE):
                        violations.append(f"{f.relative_to(BASE_DIR)}:{i}: {desc}")
                        break
        if violations:
            self.add("SCAFFOLD-SCAN", "No unresolved scaffolds in executables", True, "FAIL", f"{len(violations)} violations", "\n".join(violations))
        else:
            self.add("SCAFFOLD-SCAN", "No unresolved scaffolds in executables", True, "PASS", "0 violations", "Clean")

    # ===== POST-CHECKS (TOTALS, FAIL-CLOSED, EVIDENCE-CONSISTENCY) =====

    def compute_totals(self):
        counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
        for r in self.results:
            if r.result in counts:
                counts[r.result] += 1
        counts["total"] = len(self.results)
        return counts

    def check_totals_consistency(self, totals):
        """Post-serialization integrity check — verifies pre-check totals are self-consistent."""
        expected_total = totals["PASS"] + totals["FAIL"] + totals["BLOCKED"] + totals["SKIPPED"]
        actual_total = totals["total"]

        if actual_total == 0:
            self.add("TOTALS-CONSIST", "Result totals self-consistent", True, "FAIL", "0 results", "No checks executed")
            return

        if actual_total == expected_total:
            self.add("TOTALS-CONSIST", "Result totals self-consistent", True, "PASS",
                     f"{actual_total} results",
                     f"P={totals['PASS']} F={totals['FAIL']} B={totals['BLOCKED']} S={totals['SKIPPED']}")
        else:
            self.add("TOTALS-CONSIST", "Result totals self-consistent", True, "FAIL",
                     f"total={actual_total} computed={expected_total}",
                     "Disagreement between recorded totals and actual count")

    def _evidence_dir(self):
        """Return the active evidence directory (override or canonical)."""
        d = self.evidence_dir_override if self.evidence_dir_override else EVIDENCE_DIR
        d.mkdir(parents=True, exist_ok=True)
        return d

    def check_fail_closed(self):
        """The real fail-closed check: verify adversarial evidence exists and is valid."""
        adv_path = self._evidence_dir() / "adversarial-results.json"
        if not adv_path.exists():
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True,
                     "BLOCKED", "adversarial-results.json not found", "Run adversarial-tests.sh first")
            return

        try:
            with open(adv_path, "r", encoding="utf-8") as f:
                adv = json.load(f)
        except Exception as e:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True,
                     "BLOCKED", f"Cannot parse adversarial results: {e}", "")
            return

        # Verify adversarial structure
        tests = adv.get("tests", [])
        if not tests:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True,
                     "FAIL", "0 adversarial tests", "Empty test suite")
            return

        total_tests = len(tests)
        passed_tests = sum(1 for t in tests if t.get("result") == "PASS")
        failed_tests = sum(1 for t in tests if t.get("result") == "FAIL")
        blocked_tests = sum(1 for t in tests if t.get("result") == "BLOCKED")

        # Validate mutation_result field: must be FAIL (not BLOCKED/SKIPPED)
        bad_mutation_results = []
        bad_mutation_exits = []
        bad_hash_restores = []
        for t in tests:
            mr = t.get("mutation_result", "")
            me = t.get("mutation_exit", 0)
            if mr in ("BLOCKED", "SKIPPED", "ERROR", "NOT_FOUND", "PASS", ""):
                bad_mutation_results.append(f"{t.get('test_id','?')}: mutation_result={mr}")
            if t.get("result") == "PASS" and me == 0 and mr not in ("N/A", ""):
                bad_mutation_exits.append(f"{t.get('test_id','?')}: mutation_exit=0")
            orig = t.get("original_sha256", "")
            rest = t.get("restored_sha256", "")
            if orig and rest and orig != "N/A" and rest != "N/A" and orig != rest:
                bad_hash_restores.append(f"{t.get('test_id','?')}: orig!=rest")

        errors = []
        if failed_tests > 0:
            errors.append(f"{failed_tests}/{total_tests} tests failed")
        if blocked_tests > 0:
            errors.append(f"{blocked_tests}/{total_tests} tests blocked")
        if passed_tests == 0:
            errors.append("0 tests passed")
        if bad_mutation_results:
            errors.append(f"bad mutation_result: {'; '.join(bad_mutation_results[:5])}")
        if bad_mutation_exits:
            errors.append(f"mutation_exit=0 on PASS: {'; '.join(bad_mutation_exits[:5])}")
        if bad_hash_restores:
            errors.append(f"hash restore mismatch: {'; '.join(bad_hash_restores[:5])}")

        if errors:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True,
                     "FAIL", f"{len(errors)} issues",
                     "\n".join(errors))
        else:
            self.add("FAIL-CLOSED", "Adversarial mutations detected and rejected", True,
                     "PASS", f"{passed_tests}/{total_tests} pass",
                     "All mutations correctly rejected with FAIL+nonzero exit")

    def check_evidence_consistency(self):
        """Verify evidence identity matches checkpoint identity."""
        results_path = self._evidence_dir() / "static-validation-results.json"
        if not results_path.exists():
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True,
                     "BLOCKED", "static-validation-results.json not found", "")
            return

        try:
            with open(results_path, "r", encoding="utf-8") as f:
                evidence = json.load(f)
        except Exception as e:
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True,
                     "BLOCKED", f"Cannot parse evidence: {e}", "")
            return

        errors = []
        git = get_git_info()

        # Check commit matches
        ev_commit = evidence.get("tested_commit", "")
        actual_commit = git.get("commit", "")
        if ev_commit and actual_commit and ev_commit != actual_commit:
            errors.append(f"COMMIT: evidence={ev_commit[:12]} actual={actual_commit[:12]}")

        # Check tree matches
        ev_tree = evidence.get("tested_tree", "")
        actual_tree = git.get("tree", "")
        if ev_tree and actual_tree and ev_tree != actual_tree:
            errors.append(f"TREE: evidence={ev_tree[:12]} actual={actual_tree[:12]}")

        # Check branch matches
        ev_branch = evidence.get("tested_branch", "")
        actual_branch = git.get("branch", "")
        if ev_branch and actual_branch and ev_branch != actual_branch:
            errors.append(f"BRANCH: evidence={ev_branch} actual={actual_branch}")

        # Check totals match
        ev_totals = evidence.get("totals", {})
        ev_results = evidence.get("results", [])
        ev_total = ev_totals.get("total", 0)
        if ev_total != len(ev_results):
            errors.append(f"TOTALS: declared={ev_total} actual={len(ev_results)}")

        # Check PASS+FAIL+BLOCKED+SKIPPED = total
        ev_p = ev_totals.get("PASS", 0)
        ev_f = ev_totals.get("FAIL", 0)
        ev_b = ev_totals.get("BLOCKED", 0)
        ev_s = ev_totals.get("SKIPPED", 0)
        if ev_p + ev_f + ev_b + ev_s != ev_total:
            errors.append(f"TOTALS_MATH: P({ev_p})+F({ev_f})+B({ev_b})+S({ev_s}) != total({ev_total})")

        if errors:
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True,
                     "FAIL", f"{len(errors)} mismatches", "\n".join(errors))
        else:
            self.add("EVIDENCE-CONSISTENCY", "Evidence identity matches checkpoint", True,
                     "PASS", "All identity fields match", "Evidence is self-consistent")

    # ===== FULL RUN =====

    def run_all_checks(self):
        """Run all checks in order. SOURCE-IDENTITY must come first and abort on failure."""
        # Phase 1: SOURCE-IDENTITY (fail-closed gate)
        self.check_source_identity()
        if not self.source_identity_passed:
            # Abort: do not run any other checks
            return

        # Phase 2: Static structure checks
        self.check_yaml_parsing()
        self.check_json_parsing()
        self.check_schema_validity()
        self.check_schema_fixtures()

        # Phase 3: Compose/policy checks
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

        # Phase 4: Worker and security checks
        self.check_worker_deny()
        self.check_worker_no_db_access()
        self.check_security_opts()
        self.check_no_external_networks()

        # Phase 5: Ansible/infrastructure
        self.check_roles_have_tasks()
        self.check_evidence_structure()
        self.check_runbooks()
        self.check_single_infra_root()

        # Phase 6: Tool-dependent checks (may be BLOCKED)
        self.check_ansible_syntax()
        self.check_ansible_lint()
        self.check_compose_render()
        self.check_shellcheck()
        self.check_gitleaks()
        self.check_scaffold_scan()

    def run_targeted(self, check_ids):
        """Run only specific checks by ID (for adversarial targeted mode)."""
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
        }

        # SOURCE-IDENTITY always runs first
        self.check_source_identity()
        if not self.source_identity_passed:
            return  # Abort all other checks

        for cid in check_ids:
            if cid == "SOURCE-IDENTITY":
                continue  # Already ran
            if cid in check_map:
                check_map[cid]()

    def write_evidence(self, git_info):
        ev_dir = self._evidence_dir()
        ev_dir.mkdir(parents=True, exist_ok=True)

        # Compute totals (excluding TOTALS-CONSIST, FAIL-CLOSED, EVIDENCE-CONSISTENCY)
        pre_totals = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
        for r in self.results:
            if r.check_id in ("TOTALS-CONSIST", "FAIL-CLOSED", "EVIDENCE-CONSISTENCY"):
                continue
            if r.result in pre_totals:
                pre_totals[r.result] += 1
        pre_totals["total"] = sum(pre_totals.values())

        # Run post-checks
        self.check_totals_consistency(pre_totals)
        self.check_fail_closed()
        self.check_evidence_consistency()

        # Final totals include everything
        totals = self.compute_totals()
        gate = self.determine_gate(totals)

        # Write JSON
        results_data = {
            "schema_version": VERSION,
            "run_id": self.run_uid,
            "validator_version": VERSION,
            "start_time": self.start_time,
            "end_time": utc_now(),
            "tested_commit": git_info.get("commit", "unknown"),
            "tested_tree": git_info.get("tree", "unknown"),
            "tested_branch": git_info.get("branch", "unknown"),
            "repository": "dabiggestpoppa/larger-lab",
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
            "totals": totals,
            "gate": gate,
        }

        results_path = ev_dir / "static-validation-results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        # Write summary MD
        self.write_summary_md(git_info, totals, gate, ev_dir)

        # Write stage status
        self.write_stage_status(git_info, totals, gate, ev_dir)

        return gate, totals

    def write_evidence_targeted(self, git_info):
        """Write evidence in targeted mode — skip FAIL-CLOSED and EVIDENCE-CONSISTENCY."""
        ev_dir = self._evidence_dir()
        ev_dir.mkdir(parents=True, exist_ok=True)

        # Compute totals (excluding post-checks)
        pre_totals = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0}
        for r in self.results:
            if r.check_id in ("TOTALS-CONSIST", "FAIL-CLOSED", "EVIDENCE-CONSISTENCY"):
                continue
            if r.result in pre_totals:
                pre_totals[r.result] += 1
        pre_totals["total"] = sum(pre_totals.values())

        # Only run TOTALS-CONSIST in targeted mode
        self.check_totals_consistency(pre_totals)

        totals = self.compute_totals()
        gate = self.determine_gate(totals)

        # Write JSON
        results_data = {
            "schema_version": VERSION,
            "run_id": self.run_uid,
            "validator_version": VERSION,
            "start_time": self.start_time,
            "end_time": utc_now(),
            "tested_commit": git_info.get("commit", "unknown"),
            "tested_tree": git_info.get("tree", "unknown"),
            "tested_branch": git_info.get("branch", "unknown"),
            "repository": "dabiggestpoppa/larger-lab",
            "command": "validate_engine.py --only",
            "tools": {
                "python": get_tool_version("python3"),
                "ansible": get_tool_version("ansible-playbook"),
                "ansible_lint": get_tool_version("ansible-lint"),
                "docker": get_tool_version("docker"),
                "shellcheck": get_tool_version("shellcheck"),
                "gitleaks": get_tool_version("gitleaks"),
            },
            "results": [r.to_dict() for r in self.results],
            "totals": totals,
            "gate": gate,
        }

        results_path = ev_dir / "static-validation-results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

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
        lines = [
            f"# B1-I1R3C Static Validation Summary",
            f"",
            f"- **Run ID:** `{self.run_uid}`",
            f"- **Validator:** v{VERSION}",
            f"- **Tested commit:** `{git_info.get('commit', 'unknown')}`",
            f"- **Tested branch:** `{git_info.get('branch', 'unknown')}`",
            f"- **Repository:** `dabiggestpoppa/larger-lab`",
            f"- **Start:** {self.start_time}",
            f"- **End:** {utc_now()}",
            f"- **Gate:** `{gate}`",
            f"",
            f"## Totals",
            f"",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total | {totals['total']} |",
            f"| PASS | {totals['PASS']} |",
            f"| FAIL | {totals['FAIL']} |",
            f"| BLOCKED | {totals['BLOCKED']} |",
            f"| SKIPPED | {totals['SKIPPED']} |",
            f"",
            f"## Results",
            f"",
            f"| Check ID | Mandatory | Result | Evidence |",
            f"|----------|-----------|--------|----------|",
        ]
        for r in self.results:
            mand = "yes" if r.mandatory else "no"
            lines.append(f"| `{r.check_id}` | {mand} | {r.result} | {r.evidence} |")

        lines.extend(["", "## Failures and Blocks", ""])
        problems = [r for r in self.results if r.result in ("FAIL", "BLOCKED")]
        if problems:
            for r in problems:
                lines.extend([f"### {r.check_id} — {r.result}", f"- {r.description}", f"- {r.evidence}", f"- {r.output}", ""])
        else:
            lines.extend(["None.", ""])

        lines.extend([
            f"---", f"*Generated by validate_engine.py v{VERSION} — {utc_now()}*",
        ])

        out_path = ev_dir / "static-validation-summary.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def write_stage_status(self, git_info, totals, gate, ev_dir=None):
        ev_dir = ev_dir or self._evidence_dir()
        status = {
            "block": "B1",
            "increment": "B1-I1R3C",
            "implementation_commit": git_info.get("commit", "unknown"),
            "implementation_tree": git_info.get("tree", "unknown"),
            "evidence_commit": None,
            "gate_status": gate,
            "totals": totals,
            "unresolved_blockers": [],
            "cost_impact_usd": 0,
            "cloud_mutations": 0,
            "next_authorized_action": "Operator review of B1-I1R3C evidence",
        }
        for r in self.results:
            if r.result == "BLOCKED":
                status["unresolved_blockers"].append({
                    "check_id": r.check_id,
                    "reason": r.evidence,
                    "dependency": r.output,
                })
        out_path = ev_dir / "stage-status.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OCE Cloud Ground Validation Engine v3.3.0")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--authoritative", action="store_true",
                        help="Authoritative mode: enforce strict identity proof (requires --target-commit, --target-tree, --target-branch)")
    parser.add_argument("--target-commit", type=str, help="Expected implementation SHA")
    parser.add_argument("--target-tree", type=str, help="Expected tree SHA")
    parser.add_argument("--target-branch", type=str, help="Expected branch name")
    parser.add_argument("--evidence-dir", type=str, default=None,
                        help="Override evidence output directory (for isolation during adversarial testing)")
    parser.add_argument("--only", type=str, help="Comma-separated check IDs to run")
    args = parser.parse_args()

    # In authoritative mode, identity inputs are mandatory
    if args.authoritative:
        missing = []
        if not args.target_commit:
            missing.append("--target-commit")
        if not args.target_tree:
            missing.append("--target-tree")
        if not args.target_branch:
            missing.append("--target-branch")
        if missing:
            print(f"ERROR: Authoritative mode requires: {', '.join(missing)}")
            sys.exit(1)

    validator = Validator(
        target_commit=args.target_commit,
        target_tree=args.target_tree,
        target_branch=args.target_branch,
        authoritative=args.authoritative,
        evidence_dir=args.evidence_dir,
    )

    if args.only:
        check_ids = [c.strip() for c in args.only.split(",")]
        validator.run_targeted(check_ids)
        git_info = get_git_info()
        # In targeted mode, write evidence but skip FAIL-CLOSED and EVIDENCE-CONSISTENCY
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

    # Print summary
    print(f"\n{'='*50}")
    print(f"  B1-I1R3C Validation — {gate}")
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
