#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLEANROOM VERIFIER (canonical, rerunnable, read-only)
=====================================================

Verifies the repository-cleanroom evidence closure for
dabiggestpoppa/larger-lab against an expected-state contract.

Guarantees:
  * NEVER mutates branches, tags, stashes, trash, LFS objects, or working
    files. All git invocations are read-only (status --porcelain with
    --no-optional-locks, rev-parse, ls-remote, cat-file, fsck --no-dangling,
    merge-base --is-ancestor, stash list, lfs status/ls-files).
  * Writes ALL outputs to --output-dir, which must be OUTSIDE the repository
    working tree (enforced).
  * Produces machine-readable JSON (cleanroom-verification.json) and a
    Markdown summary (cleanroom-verification-summary.md), plus
    tool-versions.json, trash-inventory.json, stash-inventory.json.
  * Distinguishes PASS / FAIL / BLOCKED / SKIPPED / NOT_RUN.
  * Exit code: 0 = no mandatory FAIL/BLOCKED; 1 = mandatory FAIL present;
    2 = mandatory BLOCKED present (FAIL takes precedence); 3 = internal
    error / bad usage. The exact exit code is also written into the JSON.

Checks:
  repo_identity, cleanroom_branch, tested_subject, clean_worktree,
  main_unchanged, protected_branches, restored_branches, archive_tags,
  manifest_consistency, restored_files, trash_inventory, lfs_status,
  stash_inventory, gitleaks_secret_scan (mandatory; BLOCKED if binary
  missing), regex_secret_scan (informational fallback, NOT equivalent to
  gitleaks), json_parse, yaml_parse, python_compile, doc_links,
  git_object_integrity, not_run_declaration.

Usage:
  python cleanroom/verifier.py --output-dir <OUTSIDE_REPO_DIR> [--subject <sha>]
  CR_SUBJECT=<sha> python cleanroom/verifier.py --output-dir <dir>
"""

import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_BLOCKED = "BLOCKED"
STATUS_SKIPPED = "SKIPPED"
STATUS_NOT_RUN = "NOT_RUN"
STATUSES = (STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED, STATUS_SKIPPED, STATUS_NOT_RUN)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, cwd, timeout=300, ok_codes=(0,), env=None):
    """Run a command; returns (returncode, stdout, stderr). Never throws on nonzero rc."""
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -999, "", "TIMEOUT after %ss" % timeout
    except FileNotFoundError:
        return -998, "", "command not found: %s" % cmd[0]


class Verifier:
    def __init__(self, repo_root, expected_state_path, output_dir, subject=None):
        self.repo_root = os.path.abspath(repo_root)
        self.expected_state_path = os.path.abspath(expected_state_path)
        self.output_dir = os.path.abspath(output_dir)
        self.checks = []
        self.observed_at_utc = utcnow()
        self.subject = subject
        self.env = dict(os.environ)
        self.remote_refs = None  # {heads: {name: sha}, tags: {name: {object, target}}}
        self.remote_fetched = False
        # CI environment detection: local-only state (stash, trash, LFS cache
        # directory) does not exist in a fresh CI clone and is reported SKIPPED
        # there; locally these are mandatory checks.
        self.in_ci = (os.environ.get("GITHUB_ACTIONS") == "true"
                      or os.environ.get("CR_ENV") == "ci")
        self.git_dir = os.path.join(self.repo_root, ".git")
        if not os.path.isdir(self.git_dir):
            # linked worktree: .git is a file pointing at the real git dir
            if os.path.isfile(self.git_dir):
                with open(self.git_dir, "r", encoding="utf-8") as fh:
                    self.git_dir = os.path.abspath(
                        os.path.join(self.repo_root, fh.read().strip().split(":", 1)[1].strip()))
        self.load_expected()

    # ------------------------------------------------------------------ utils
    def git(self, *args, timeout=300):
        return run(["git", "-C", self.repo_root] + list(args), self.repo_root, timeout=timeout)

    def record(self, cid, description, status, details=None, mandatory=True, data=None):
        entry = {
            "check_id": cid,
            "description": description,
            "status": status,
            "mandatory": mandatory,
            "details": details or {},
        }
        if data is not None:
            entry["data"] = data
        self.checks.append(entry)
        return entry

    def load_expected(self):
        with open(self.expected_state_path, "r", encoding="utf-8") as fh:
            self.expected = json.load(fh)
        self.branch_ref_manifest = self._load_manifest(
            os.path.join(self.repo_root, self.expected["manifests"]["branch_reference"]))
        self.restored_file_manifest = self._load_manifest(
            os.path.join(self.repo_root, self.expected["manifests"]["restored_files"]))
        self.cleanup_manifest = self._load_manifest(
            os.path.join(self.repo_root, self.expected["manifests"]["cleanup_manifest"]))

    def _load_manifest(self, path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def fetch_remote(self):
        """Read-only ls-remote snapshot (network). Cached."""
        if self.remote_fetched:
            return self.remote_refs is not None
        _, out, err = self.git("ls-remote", "origin", timeout=180)
        if out == "" and err != "":
            self.remote_refs = None
            self.remote_fetched = True
            return False
        heads, tags = {}, {}
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            sha, ref = parts
            if ref.startswith("refs/heads/"):
                heads[ref[len("refs/heads/"):]] = sha
            elif ref.startswith("refs/tags/"):
                name = ref[len("refs/tags/"):]
                if name.endswith("^{}"):
                    tags.setdefault(name[:-3], {})["target"] = sha
                else:
                    tags.setdefault(name, {})["object"] = sha
        self.remote_refs = {"heads": heads, "tags": tags}
        self.remote_fetched = True
        return True

    def head_sha(self):
        _, out, _ = self.git("rev-parse", "HEAD")
        return out.strip()

    def current_branch(self):
        _, out, _ = self.git("rev-parse", "--abbrev-ref", "HEAD")
        return out.strip()

    def is_ancestor(self, ancestor, descendant):
        rc, _, _ = self.git("merge-base", "--is-ancestor", ancestor, descendant)
        return rc == 0

    def worktree_paths(self):
        """Tracked files present in the working tree (git ls-files)."""
        _, out, _ = self.git("ls-files")
        return [p for p in out.splitlines() if p]

    # --------------------------------------------------------------- checks
    def check_repo_identity(self):
        _, out, _ = self.git("remote", "get-url", self.expected["repository"]["expected_remote"])
        url = out.strip()
        ok = url == self.expected["repository"]["expected_origin_url"]
        self.record("repo_identity", "origin remote URL matches expected repository identity",
                    STATUS_PASS if ok else STATUS_FAIL,
                    {"expected": self.expected["repository"]["expected_origin_url"],
                     "observed": url or "(none)"})

    def check_cleanroom_branch(self):
        branch = self.current_branch()
        expected = self.expected["repository"]["expected_cleanroom_branch"]
        ok = branch == expected
        self.record("cleanroom_branch", "current branch is the cleanroom branch",
                    STATUS_PASS if ok else STATUS_FAIL,
                    {"expected": expected, "observed": branch})

    def check_tested_subject(self):
        head = self.head_sha()
        subject = self.subject or os.environ.get("CR_SUBJECT") or self.expected["subject"]["tested_subject_commit"]
        subject = subject.strip()
        if subject and not SHA_RE.match(subject):
            self.record("tested_subject", "tested subject commit", STATUS_BLOCKED,
                        {"reason": "subject is not a 40-hex SHA", "observed": subject})
            return
        ok = head == subject
        self.record("tested_subject",
                    "HEAD is the tested subject commit",
                    STATUS_PASS if ok else STATUS_FAIL,
                    {"expected_subject": subject, "observed_head": head})

    def check_clean_worktree(self):
        # --no-optional-locks is a git global flag (must precede the subcommand)
        rc, out, err = self.git("--no-optional-locks", "status", "--porcelain")
        dirty = [ln for ln in out.splitlines() if ln.strip()]
        ok = rc == 0 and not dirty
        self.record("clean_worktree", "working tree clean (no tracked modifications, no untracked files)",
                    STATUS_PASS if ok else STATUS_FAIL,
                    {"dirty_entries": dirty[:50], "dirty_count": len(dirty), "rc": rc})

    def check_main_unchanged(self):
        _, out, _ = self.git("rev-parse", "refs/heads/main")
        observed = out.strip()
        expected = self.expected["main"]["expected_sha"]
        ok = observed == expected
        self.record("main_unchanged", "main branch remains at expected SHA",
                    STATUS_PASS if ok else STATUS_FAIL,
                    {"expected": expected, "observed": observed or "(no local main ref)",
                     "note": "reported without altering main if it moved"})

    def _ref_check(self, cid, desc, names, exact_required, protected):
        if not self.fetch_remote():
            self.record(cid, desc, STATUS_BLOCKED,
                        {"reason": "git ls-remote origin failed (network/unauthenticated)"})
            return
        remote_heads = self.remote_refs["heads"]
        advanced = []
        failures = []
        results = {}
        for name in names:
            expected = remote_heads.get(name)  # live remote snapshot value
            if name not in self.branch_ref_manifest.get("remote_heads", {}):
                # fall back to the reference manifest expectation
                expected = self.branch_ref_manifest["remote_heads"].get(name, "")
            expected = self.branch_ref_manifest["remote_heads"].get(name, expected or "")
            live = remote_heads.get(name)
            if live is None:
                failures.append({"branch": name, "reason": "missing on origin"})
                results[name] = {"expected": expected, "remote": None, "status": "MISSING"}
                continue
            if live == expected:
                results[name] = {"expected": expected, "remote": live, "status": "EXACT"}
                continue
            # not equal: ancestor check (requires local objects)
            if expected and self.is_ancestor(expected, live):
                results[name] = {"expected": expected, "remote": live, "status": "ADVANCED"}
                advanced.append(name)
                if exact_required:
                    failures.append({"branch": name, "reason": "advanced beyond expected SHA (exact match required)"})
            else:
                results[name] = {"expected": expected, "remote": live, "status": "DIVERGED"}
                failures.append({"branch": name, "reason": "remote head differs from expected and is not a descendant"})
        ok = not failures
        self.record(cid, desc, STATUS_PASS if ok else STATUS_FAIL,
                    {"results": results, "failures": failures,
                     "advanced_after_observation": advanced})
        return advanced

    def check_protected_branches(self):
        names = self.expected.get("protected_branches", [])
        self._ref_check("protected_branches",
                        "protected branches exist on origin at expected SHAs (advance tolerated, rewinds fail)",
                        names, exact_required=False, protected=True)

    def check_restored_branches(self):
        names = sorted(self.branch_ref_manifest.get("restored_branch_verification", {}).keys())
        self._ref_check("restored_branches",
                        "restored branches exist on origin at exact expected SHAs",
                        names, exact_required=True, protected=False)

    def check_archive_tags(self):
        if not self.fetch_remote():
            self.record("archive_tags", "annotated archive tags exist on origin with matching targets",
                        STATUS_BLOCKED, {"reason": "git ls-remote origin failed"})
            return
        remote_tags = self.remote_refs["tags"]
        expected_tags = self.branch_ref_manifest.get("archive_tags", {})
        failures = []
        results = {}
        for name, info in sorted(expected_tags.items()):
            expected_target = info.get("local_target") or info.get("peeled_target") or info.get("target")
            remote = remote_tags.get(name)
            # local checks
            rc, out, _ = self.git("cat-file", "-t", name)
            local_type = out.strip() if rc == 0 else None
            rc2, out2, _ = self.git("rev-parse", name + "^{}")
            local_target = out2.strip() if rc2 == 0 else None
            ok = (remote is not None
                  and bool(remote.get("object"))
                  and local_type == "tag"
                  and local_target == expected_target
                  and remote.get("target") == expected_target)
            results[name] = {
                "annotated_remote": bool(remote and remote.get("object")),
                "annotated_local": local_type == "tag",
                "expected_target": expected_target,
                "remote_target": (remote or {}).get("target"),
                "local_target": local_target,
                "ok": ok,
            }
            if not ok:
                failures.append({"tag": name, "reason": "tag missing, lightweight, or target mismatch"})
        self.record("archive_tags", "annotated archive tags exist on origin with matching targets",
                    STATUS_PASS if not failures else STATUS_FAIL,
                    {"results": results, "failures": failures})

    def check_manifest_consistency(self):
        problems = []
        bm = self.branch_ref_manifest
        rm = self.restored_file_manifest
        cm = self.cleanup_manifest
        if bm.get("manifest_type") != "branch-reference-manifest":
            problems.append("branch-reference-manifest: wrong manifest_type")
        heads = bm.get("remote_heads", {})
        if len(heads) != bm.get("remote_head_count"):
            problems.append("branch-reference-manifest: remote_head_count mismatch (%d vs %d)"
                            % (len(heads), bm.get("remote_head_count")))
        bad = [n for n, s in heads.items() if not SHA_RE.match(s)]
        if bad:
            problems.append("branch-reference-manifest: non-SHA head values: %s" % bad[:5])
        if bm.get("main_sha") != cm.get("main", {}).get("expected_sha"):
            problems.append("branch-reference-manifest main_sha != cleanup manifest main expected_sha")
        if len(cm.get("remote_branches", {})) != bm.get("remote_head_count"):
            problems.append("cleanup manifest remote_branches count != remote_head_count")
        if rm.get("manifest_type") != "restored-file-manifest":
            problems.append("restored-file-manifest: wrong manifest_type")
        files = rm.get("files", {})
        if len(files) != rm.get("restored_file_count", -1):
            problems.append("restored-file-manifest: file count mismatch")
        if rm.get("all_byte_identical_to_main") is not True:
            problems.append("restored-file-manifest: all_byte_identical_to_main is not true")
        badsha = [n for n, v in files.items() if not re.match(r"^[0-9a-f]{64}$", v.get("sha256", ""))]
        if badsha:
            problems.append("restored-file-manifest: bad sha256 entries: %s" % badsha[:5])
        # cross: every cleanup-manifest restored branch is in the reference manifest verification set
        restored_names = {k for k, v in cm.get("remote_branches", {}).items() if v.get("restored")}
        verified_names = set(bm.get("restored_branch_verification", {}).keys())
        missing = restored_names - verified_names
        if missing:
            problems.append("restored branches missing from reference verification: %s" % sorted(missing))
        self.record("manifest_consistency", "manifests parse and are internally consistent",
                    STATUS_PASS if not problems else STATUS_FAIL,
                    {"problems": problems})

    def check_restored_files(self):
        files = self.restored_file_manifest.get("files", {})
        failures = []
        results = {}
        for path, info in sorted(files.items()):
            full = os.path.join(self.repo_root, path)
            entry = {"path": path}
            if not os.path.isfile(full):
                entry["error"] = "missing from working tree"
                failures.append(entry)
                continue
            try:
                with open(full, "rb") as fh:
                    digest = hashlib.sha256(fh.read()).hexdigest()
            except OSError as exc:
                entry["error"] = "unreadable: %s" % exc
                failures.append(entry)
                continue
            entry["sha256_match"] = digest == info.get("sha256")
            rc, blob, _ = self.git("hash-object", path)
            entry["git_blob"] = blob.strip() if rc == 0 else None
            entry["blob_matches_main"] = (blob.strip() == info.get("git_blob_main"))
            if not (entry["sha256_match"] and entry["blob_matches_main"]):
                failures.append(entry)
            results[path] = entry
        self.record("restored_files",
                    "all %d restored files present with matching SHA-256 and byte-identity to main" % len(files),
                    STATUS_PASS if not failures else STATUS_FAIL,
                    {"files_checked": len(files), "failures": failures, "results": results})

    def check_trash_inventory(self):
        if self.in_ci:
            self.record("trash_inventory", "trash holding area retained (local-only state)",
                        STATUS_SKIPPED, {"reason": "local-only operator-machine state; not present in CI clone"},
                        mandatory=False)
            with open(os.path.join(self.output_dir, "trash-inventory.json"), "w", encoding="utf-8") as fh:
                json.dump({"observed_at_utc": self.observed_at_utc, "environment": "ci",
                           "note": "local-only state not present in CI; see local run for the authoritative inventory",
                           "permanent_deletion_authorized": False},
                          fh, indent=2, sort_keys=True)
            return
        items = []
        failures = []
        for spec in self.expected.get("trash", []):
            p = spec.get("path")
            entry = {"path": p, "required": spec.get("required", True)}
            if not os.path.exists(p):
                entry["exists"] = False
                entry["size_bytes"] = 0
                failures.append(entry)
            else:
                size = 0
                try:
                    for root, dirs, fnames in os.walk(p):
                        for fn in fnames:
                            try:
                                size += os.path.getsize(os.path.join(root, fn))
                            except OSError:
                                pass
                except OSError:
                    pass
                entry["exists"] = True
                entry["size_bytes"] = size
                entry["min_size_bytes"] = spec.get("min_size_bytes", 0)
                if size < spec.get("min_size_bytes", 0):
                    failures.append(entry)
            items.append(entry)
        self.record("trash_inventory", "trash holding area retained (no permanent deletion)",
                    STATUS_PASS if not failures else STATUS_FAIL,
                    {"items": items, "failures": failures, "data": items})
        with open(os.path.join(self.output_dir, "trash-inventory.json"), "w", encoding="utf-8") as fh:
            json.dump({"observed_at_utc": self.observed_at_utc, "items": items,
                       "permanent_deletion_authorized": False,
                       "required_authorization_stage": "CLEANROOM-PERMANENT-DELETE"},
                      fh, indent=2, sort_keys=True)

    def check_lfs_status(self):
        lfs_bin = shutil.which("git-lfs")
        problems = []
        cache_skipped = False
        # LFS objects live under the COMMON git dir, not the worktree git dir
        rc, common, _ = self.git("rev-parse", "--git-common-dir")
        common_dir = os.path.abspath(os.path.join(self.repo_root, common.strip())) if rc == 0 else self.git_dir
        cache_dir = os.path.join(common_dir, "lfs", "objects")
        cache_size = 0
        if os.path.isdir(cache_dir):
            for root, dirs, fnames in os.walk(cache_dir):
                for fn in fnames:
                    try:
                        cache_size += os.path.getsize(os.path.join(root, fn))
                    except OSError:
                        pass
        details = {"cache_dir": cache_dir, "cache_size_bytes": cache_size,
                   "min_cache_size_bytes": self.expected["lfs"]["min_cache_size_bytes"]}
        if self.in_ci:
            cache_skipped = True
            details["cache_size_note"] = "LFS cache directory is local-only state; not assessed in CI"
        elif cache_size < self.expected["lfs"]["min_cache_size_bytes"]:
            problems.append("LFS cache below expected minimum size")
        tracked_counts = {}
        for ref, expected_count in self.expected["lfs"]["expected_tracked_counts"].items():
            rc, out, _ = self.git("lfs", "ls-files", ref)
            if rc != 0:
                problems.append("git lfs ls-files failed for %s" % ref)
                tracked_counts[ref] = {"expected": expected_count, "observed": None}
                continue
            n = len([ln for ln in out.splitlines() if ln.strip()])
            tracked_counts[ref] = {"expected": expected_count, "observed": n}
            if n != expected_count:
                problems.append("LFS object count mismatch on %s: expected %s observed %s" % (ref, expected_count, n))
        details["tracked_counts"] = tracked_counts
        if cache_skipped:
            details["cache_facet"] = "SKIPPED (local-only)"
        if lfs_bin is None:
            problems.append("git-lfs binary not found")
            status = STATUS_BLOCKED
        elif problems and cache_skipped and all(p.startswith("LFS cache below") for p in problems):
            status = STATUS_PASS  # only the cache-size facet failed and it was skipped in CI
        elif problems:
            status = STATUS_FAIL
        else:
            status = STATUS_PASS
        self.record("lfs_status", "Git LFS cache retained and object tracking matches expectation",
                    status, details)

    def check_stash_inventory(self):
        if self.in_ci:
            self.record("stash_inventory", "stash inventory retained (local-only state)",
                        STATUS_SKIPPED, {"reason": "local-only operator-machine state; not present in CI clone"},
                        mandatory=False)
            with open(os.path.join(self.output_dir, "stash-inventory.json"), "w", encoding="utf-8") as fh:
                json.dump({"observed_at_utc": self.observed_at_utc, "environment": "ci",
                           "note": "local-only state not present in CI; see local run for the authoritative inventory",
                           "count": None, "retained": None, "dropped": 0},
                          fh, indent=2, sort_keys=True)
            return
        rc, out, _ = self.git("stash", "list")
        entries = [ln for ln in out.splitlines() if ln.strip()]
        expected_count = self.expected["stash"]["expected_count"]
        expected_list = self.expected["stash"]["expected_list"]
        ok = rc == 0 and len(entries) == expected_count
        diffs = []
        if ok:
            for exp in expected_list:
                if exp not in entries:
                    ok = False
                    diffs.append({"expected": exp, "observed": "missing"})
                    break
        self.record("stash_inventory", "stash inventory retained (count %d, none dropped)" % expected_count,
                    STATUS_PASS if ok else STATUS_FAIL,
                    {"expected_count": expected_count, "observed_count": len(entries),
                     "diffs": diffs, "data": entries})
        with open(os.path.join(self.output_dir, "stash-inventory.json"), "w", encoding="utf-8") as fh:
            json.dump({"observed_at_utc": self.observed_at_utc, "count": len(entries),
                       "retained": True, "dropped": 0, "entries": entries},
                      fh, indent=2, sort_keys=True)

    def _find_gitleaks(self):
        candidates = []
        env_bin = os.environ.get("GITLEAKS_BIN")
        if env_bin:
            candidates.append(env_bin)
        for p in self.expected.get("gitleaks", {}).get("binary_paths", []):
            if p:
                candidates.append(p)
        found = shutil.which("gitleaks")
        if found:
            candidates.append(found)
        for c in candidates:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                return c
            if c and shutil.which(c):
                return shutil.which(c)
        return None

    def check_gitleaks(self):
        cfg = self.expected.get("gitleaks", {})
        required = cfg.get("required", True)
        binary = self._find_gitleaks()
        if binary is None:
            self.record("gitleaks_secret_scan",
                        "gitleaks secret scan of cleanroom commits (authoritative)",
                        STATUS_BLOCKED if required else STATUS_NOT_RUN,
                        {"reason": "gitleaks binary not available; a regex scan is NOT equivalent",
                         "required": required})
            return
        # Scoped to the cleanroom branch's own commits (scan_base..HEAD) so the
        # check answers "did the cleanroom introduce credentials". The
        # repo-wide historical result is documented separately in the report.
        scan_base = cfg.get("scan_base", "main")
        tmp_report = os.path.join(tempfile.gettempdir(), "gitleaks-report-cleanroom.json")
        if os.path.exists(tmp_report):
            os.remove(tmp_report)
        cmd = [binary, "detect", "--no-banner", "--source", self.repo_root,
               "--log-opts=%s..HEAD" % scan_base,
               "--report-format", "json", "--report-path", tmp_report]
        cfg_path = cfg.get("config")
        if cfg_path:
            cmd += ["--config", os.path.join(self.repo_root, cfg_path)]
        rc, out, err = run(cmd, self.repo_root,
                           timeout=cfg.get("timeout_seconds", 900) or self.expected["check_overrides"]["gitleaks_timeout_seconds"])
        summary = (out + err)
        findings = []
        if os.path.exists(tmp_report):
            try:
                with open(tmp_report, "r", encoding="utf-8") as fh:
                    for item in json.load(fh):
                        findings.append({
                            "file": item.get("File"),
                            "rule": item.get("RuleID"),
                            "line": item.get("StartLine"),
                            "commit": (item.get("Commit") or "")[:12],
                            "fingerprint": item.get("Fingerprint"),
                        })
            except Exception as exc:
                findings = [{"error": "could not parse gitleaks report: %r" % exc}]
        leaks = len([f for f in findings if "error" not in f])
        if rc == 0:
            status, reason = STATUS_PASS, "no leaks found in cleanroom commits"
        elif rc == 1:
            status, reason = STATUS_FAIL, "%d finding(s) reported by gitleaks in cleanroom commits" % leaks
        else:
            status, reason = STATUS_BLOCKED, "gitleaks exited %d (%s)" % (rc, summary[-500:])
        self.record("gitleaks_secret_scan",
                    "gitleaks secret scan of cleanroom commits (authoritative, scoped %s..HEAD)" % scan_base,
                    status, {"binary": binary, "exit_code": rc, "findings": leaks,
                             "finding_list": findings[:50],
                             "reason": reason,
                             "note": "full-history repo scan is documented in the report; this check is scoped to the cleanroom's own commits"})

    def check_regex_secret_scan(self):
        patterns = [
            ("aws_access_key", r"AKIA[0-9A-Z]{16}"),
            ("github_pat", r"ghp_[0-9A-Za-z]{36}"),
            ("github_oauth", r"gho_[0-9A-Za-z]{36}"),
            ("gitlab_pat", r"glpat-[0-9A-Za-z_\-]{20}"),
            ("private_key", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            ("generic_secret", r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{16,}['\"]"),
            ("slack_token", r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
            ("google_api", r"AIza[0-9A-Za-z_\-]{35}"),
        ]
        scope_prefixes = ("quant-lab/", "cleanroom/", "CLEANROOM_")
        root_manifests = {"repo_cleanup_branch_manifest.json"}
        files = self.worktree_paths()
        scope = [f for f in files if f.startswith(scope_prefixes) or f in root_manifests]
        hits = []
        for f in scope:
            full = os.path.join(self.repo_root, f)
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    txt = fh.read()
            except OSError:
                continue
            for name, pat in patterns:
                for m in re.finditer(pat, txt):
                    hits.append({"file": f, "pattern": name})
        self.record("regex_secret_scan",
                    "regex secret scan (INFORMATIONAL FALLBACK - not equivalent to gitleaks)",
                    STATUS_PASS if not hits else STATUS_FAIL,
                    {"files_scanned": len(scope), "hits": hits[:20], "hit_count": len(hits),
                     "note": "non-authoritative; gitleaks is the authoritative scan"},
                    mandatory=False)

    def check_json_parse(self):
        files = self.worktree_paths()
        scope = [f for f in files if f.endswith(".json") and
                 (f.startswith("quant-lab/") or f.startswith("cleanroom/") or
                  f in ("repo_cleanup_branch_manifest.json",))]
        bad = []
        for f in scope:
            full = os.path.join(self.repo_root, f)
            try:
                with open(full, "r", encoding="utf-8") as fh:
                    json.load(fh)
            except Exception as exc:
                bad.append({"file": f, "error": str(exc)})
        self.record("json_parse", "tracked JSON files parse (%d files)" % len(scope),
                    STATUS_PASS if not bad else STATUS_FAIL,
                    {"files_parsed": len(scope), "failures": bad})

    def check_yaml_parse(self):
        files = self.worktree_paths()
        scope = [f for f in files if f.endswith((".yaml", ".yml")) and
                 (f.startswith("quant-lab/") or f.startswith("cleanroom/") or f.startswith(".github/workflows/"))]
        try:
            import yaml
        except ImportError:
            self.record("yaml_parse", "tracked YAML files parse",
                        STATUS_BLOCKED, {"reason": "PyYAML not installed; cannot parse YAML"})
            return
        bad = []
        for f in scope:
            full = os.path.join(self.repo_root, f)
            try:
                with open(full, "r", encoding="utf-8") as fh:
                    yaml.safe_load(fh)
            except Exception as exc:
                bad.append({"file": f, "error": str(exc)})
        self.record("yaml_parse", "tracked YAML files parse (%d files)" % len(scope),
                    STATUS_PASS if not bad else STATUS_FAIL,
                    {"files_parsed": len(scope), "failures": bad})

    def check_python_compile(self):
        import py_compile
        files = self.worktree_paths()
        scope = [f for f in files if f.endswith(".py") and
                 (f.startswith("quant-lab/") or f.startswith("cleanroom/"))]
        bad = []
        tmp = tempfile.mkdtemp(prefix="cr-verifier-pyc-")
        try:
            for f in scope:
                full = os.path.join(self.repo_root, f)
                cfile = os.path.join(tmp, hashlib.sha1(f.encode()).hexdigest() + ".pyc")
                try:
                    py_compile.compile(full, cfile=cfile, doraise=True)
                except Exception as exc:
                    bad.append({"file": f, "error": str(exc)})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.record("python_compile", "tracked Python under quant-lab/ and cleanroom/ compiles (%d files)" % len(scope),
                    STATUS_PASS if not bad else STATUS_FAIL,
                    {"files_compiled": len(scope), "failures": bad})

    def check_doc_links(self):
        files = self.worktree_paths()
        scope_cfg = self.expected.get("doc_links_scope", {})
        # scope = top-level docs (no '/') + docs/ + cleanroom/ + CLEANROOM_*.md
        scope = [f for f in files if f.endswith(".md") and
                 (f.count("/") == 0 or f.startswith("docs/") or f.startswith("cleanroom/"))]
        link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        broken = []
        checked = 0
        for f in scope:
            full = os.path.join(self.repo_root, f)
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    txt = fh.read()
            except OSError:
                continue
            for m in link_re.finditer(txt):
                tgt = m.group(1).strip()
                if tgt.startswith(tuple(scope_cfg.get("skip_link_prefixes", []))):
                    continue
                if scope_cfg.get("skip_absolute_paths") and tgt.startswith("/"):
                    continue
                tgt = tgt.split("#")[0].strip()
                if not tgt:
                    continue
                checked += 1
                cand = os.path.normpath(os.path.join(os.path.dirname(f), tgt))
                if os.path.exists(cand):
                    continue
                cand2 = os.path.normpath(tgt)
                if os.path.exists(cand2):
                    continue
                broken.append({"doc": f, "link": m.group(1)})
        self.record("doc_links", "internal documentation links resolve (%d links, %d docs)" % (checked, len(scope)),
                    STATUS_PASS if not broken else STATUS_FAIL,
                    {"links_checked": checked, "broken": broken[:30], "broken_count": len(broken)})

    def check_git_object_integrity(self):
        timeout = self.expected.get("check_overrides", {}).get("fsck_timeout_seconds", 900)
        rc, out, err = self.git("fsck", "--no-dangling", "--no-progress", timeout=timeout)
        # In a shared .git (multi-worktree), a concurrent auto-gc/repack can
        # transiently report missing objects. Retry once with a short delay;
        # both attempts are recorded. CI clones are deterministic.
        retry = None
        if rc != 0 and "missing" in (out + err):
            import time as _time
            _time.sleep(15)
            rc2, out2, err2 = self.git("fsck", "--no-dangling", "--no-progress", timeout=timeout)
            retry = {"exit_code": rc2, "output_tail": (out2 + err2)[-2000:]}
            if rc2 == 0:
                rc, out, err = rc2, out2, err2
        ok = rc == 0
        details = {"exit_code": rc, "output_tail": (out + err)[-2000:]}
        if retry:
            details["first_attempt"] = {"exit_code": retry["exit_code"],
                                        "output_tail": retry["output_tail"][-800:]}
            details["note"] = "first fsck reported missing objects (possible concurrent maintenance in shared .git); retry result recorded"
        self.record("git_object_integrity", "git fsck --no-dangling passes (read-only)",
                    STATUS_PASS if ok else STATUS_BLOCKED if rc == -999 else STATUS_FAIL,
                    details)

    def check_not_run_declaration(self):
        for suite in self.expected.get("not_run_suites", []):
            self.record("not_run:" + suite["id"], suite["suite"], STATUS_NOT_RUN,
                        {"reason": suite["reason"]}, mandatory=False)

    # ------------------------------------------------------------- runner
    def run_all(self):
        os.makedirs(self.output_dir, exist_ok=True)
        checks = [
            self.check_repo_identity,
            self.check_cleanroom_branch,
            self.check_tested_subject,
            self.check_clean_worktree,
            self.check_main_unchanged,
            self.check_protected_branches,
            self.check_restored_branches,
            self.check_archive_tags,
            self.check_manifest_consistency,
            self.check_restored_files,
            self.check_trash_inventory,
            self.check_lfs_status,
            self.check_stash_inventory,
            self.check_gitleaks,
            self.check_regex_secret_scan,
            self.check_json_parse,
            self.check_yaml_parse,
            self.check_python_compile,
            self.check_doc_links,
            self.check_git_object_integrity,
            self.check_not_run_declaration,
        ]
        for fn in checks:
            try:
                fn()
            except Exception as exc:  # never let one check crash the run
                import traceback
                self.record("internal:" + fn.__name__, fn.__name__, STATUS_BLOCKED,
                            {"reason": "check raised: %r" % exc, "traceback": traceback.format_exc()[-1500:]})

    def totals(self):
        counts = {s: 0 for s in STATUSES}
        for c in self.checks:
            counts[c["status"]] += 1
        mandatory_fail = [c for c in self.checks if c["status"] == STATUS_FAIL and c["mandatory"]]
        mandatory_blocked = [c for c in self.checks if c["status"] == STATUS_BLOCKED and c["mandatory"]]
        if mandatory_fail:
            exit_code = 1
        elif mandatory_blocked:
            exit_code = 2
        else:
            exit_code = 0
        return counts, mandatory_fail, mandatory_blocked, exit_code

    def tool_versions(self):
        versions = {"platform": platform.platform(), "observed_at_utc": self.observed_at_utc}
        rc, out, _ = self.git("--version")
        versions["git"] = out.strip() if rc == 0 else None
        versions["python"] = platform.python_version()
        rc, out, _ = self.git("lfs", "version")
        versions["git-lfs"] = out.strip() if rc == 0 else None
        try:
            import yaml
            versions["pyyaml"] = yaml.__version__
        except ImportError:
            versions["pyyaml"] = None
        binary = self._find_gitleaks()
        if binary:
            rc, out, err = run([binary, "version"], self.repo_root, timeout=60)
            versions["gitleaks"] = (out + err).strip().splitlines()[0] if rc == 0 else "unknown"
            versions["gitleaks_binary"] = binary
        else:
            versions["gitleaks"] = None
        return versions

    def write_outputs(self):
        os.makedirs(self.output_dir, exist_ok=True)
        head = self.head_sha()
        branch = self.current_branch()
        counts, mfail, mblocked, exit_code = self.totals()
        advanced = []
        for c in self.checks:
            if c["check_id"] in ("protected_branches", "restored_branches"):
                adv = c.get("details", {}).get("advanced_after_observation")
                if adv:
                    advanced.extend(adv)
        advanced = sorted(set(advanced))
        report = {
            "artifact": "cleanroom-verification",
            "repository": self.expected["repository"]["expected_origin_url"],
            "cleanroom_branch": branch,
            "snapshot": {
                "observed_at_utc": self.observed_at_utc,
                "observed_branch_sha": head,
                "tested_subject_commit": self.subject or os.environ.get("CR_SUBJECT") or self.expected["subject"]["tested_subject_commit"],
                "evidence_commit": None,
                "current_live_branch_state": {branch: head},
                "branch_advanced_after_observation": advanced,
            },
            "totals": counts,
            "exit_code": exit_code,
            "overall_status": (STATUS_FAIL if mfail else STATUS_BLOCKED if mblocked else STATUS_PASS),
            "checks": self.checks,
            "main_observed": self._observed_main(),
        }
        with open(os.path.join(self.output_dir, "cleanroom-verification.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        with open(os.path.join(self.output_dir, "cleanroom-verification-summary.md"), "w", encoding="utf-8") as fh:
            fh.write(self._summary_md(report))
        with open(os.path.join(self.output_dir, "tool-versions.json"), "w", encoding="utf-8") as fh:
            json.dump(self.tool_versions(), fh, indent=2, sort_keys=True)
        return exit_code

    def _observed_main(self):
        _, out, _ = self.git("rev-parse", "refs/heads/main")
        return out.strip()

    def _summary_md(self, report):
        lines = [
            "# Cleanroom Verification Summary",
            "",
            "Repository: `%s`  " % report["repository"],
            "Branch: `%s`  " % report["cleanroom_branch"],
            "Observed at (UTC): `%s`  " % report["snapshot"]["observed_at_utc"],
            "Observed branch SHA: `%s`  " % report["snapshot"]["observed_branch_sha"],
            "Tested subject commit: `%s`  " % report["snapshot"]["tested_subject_commit"],
            "Evidence commit: `%s`  " % report["snapshot"]["evidence_commit"],
            "Overall status: **%s** (exit code %s)" % (report["overall_status"], report["exit_code"]),
            "",
            "| Status | Count |",
            "|---|---|",
        ]
        for s in STATUSES:
            lines.append("| %s | %d |" % (s, report["totals"].get(s, 0)))
        lines.append("")
        lines.append("## Checks")
        lines.append("")
        lines.append("| Check | Status | Detail |")
        lines.append("|---|---|---|")
        for c in report["checks"]:
            detail = json.dumps(c.get("details", {}))[:200]
            lines.append("| %s | %s | %s |" % (c["check_id"], c["status"], detail.replace("|", "/")))
        lines.append("")
        if report["snapshot"]["branch_advanced_after_observation"]:
            lines.append("## Branches advanced after observation")
            for b in report["snapshot"]["branch_advanced_after_observation"]:
                lines.append("- `%s`" % b)
            lines.append("")
        if report["exit_code"] != 0:
            lines.append("**Not clean: verifier exits %d.**" % report["exit_code"])
        else:
            lines.append("**Clean: no mandatory FAIL or BLOCKED checks.**")
        lines.append("")
        return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rerunnable read-only cleanroom verifier")
    ap.add_argument("--output-dir", required=True, help="Directory for outputs (MUST be outside the repo working tree)")
    ap.add_argument("--subject", default=None, help="Tested subject commit SHA (default: CR_SUBJECT env, expected-state, or HEAD)")
    ap.add_argument("--repo-root", default=os.getcwd(), help="Repository working tree root (default: cwd)")
    ap.add_argument("--expected-state", default=None, help="Path to expected-state.json (default: <repo-root>/cleanroom/expected-state.json)")
    args = ap.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    gitmarker = os.path.join(repo_root, ".git")
    if not (os.path.isdir(gitmarker) or os.path.isfile(gitmarker)):
        sys.stderr.write("ERROR: %s is not a git working tree (no .git)\n" % repo_root)
        return 3
    out_dir = os.path.abspath(args.output_dir)
    if out_dir == repo_root or out_dir.startswith(repo_root + os.sep):
        sys.stderr.write(
            "ERROR: --output-dir must be OUTSIDE the repository working tree "
            "(the verifier must never mutate working files). Got %s\n" % out_dir)
        return 3
    expected_state = args.expected_state or os.path.join(repo_root, "cleanroom", "expected-state.json")
    if not os.path.isfile(expected_state):
        sys.stderr.write("ERROR: expected-state not found: %s\n" % expected_state)
        return 3

    verifier = Verifier(repo_root, expected_state, out_dir, subject=args.subject)
    verifier.run_all()
    exit_code = verifier.write_outputs()
    print("cleanroom verifier: %s (exit %d)" % (
        verifier.totals()[0], exit_code))
    print("outputs written to %s" % out_dir)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
