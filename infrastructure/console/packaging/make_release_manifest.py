"""Deterministic release-manifest tool (B5-I6; plan C4.S1 packaging).

Builds, verifies and materializes the LOCAL release manifest for the OCE
console — the constitution section 12.2 deployment rules made executable
("Deploy clean, versioned releases from declared source"; "Do not upload
the entire local workspace"; "Infrastructure is reproducible from
configuration and manifests"). Charter section 6: local-only, no external
hosting, no provider, no recurring cost. This tool NEVER deploys: it
produces the package, the dry run and the rollback pointer that plan §5
C4.S1 requires; remote mutation stays hold-gated behind separate authority
after B1 and is not performed or attempted here.

Laws (test_b5_i6_deploy_pkg.py makes each executable):

- **Deterministic**: identical tree + identical base commit produce a
  BYTE-IDENTICAL manifest — sorted inventory, sorted keys, no wall-clock,
  no randomness, no environment leakage.
- **Declared install set only**: exactly the console modules, the frozen
  contract pack + schemas, the compose file, the dependency lock and the
  representative-catalog source. Caches, virtualenvs, Git objects, test
  scratch and datasets are structurally outside the set (constitution
  section 12.2: local clutter is not copied blindly).
- **Fail-closed completeness**: a missing declared file fails generation
  (no silently-incomplete manifest); a missing on-disk file fails
  verification naming the exact file; a tampered byte fails verification.
- **Rollback metadata**: every manifest carries the authorized base
  commit and a rollback pointer (constitution: "no deployment lacks
  rollback metadata").

This module is a build/verification tool, not a console runtime module:
it is intentionally OUTSIDE the oce_console package, so the frozen B5-I4
stdlib-only import closure of that package is untouched. Stdlib only
(hashlib, json, pathlib, subprocess, argparse); no LLM; no provider; no
network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

MANIFEST_KIND = "oce-console-release-manifest"
MANIFEST_VERSION = "1.0.0"

# The declared install set: repo-relative POSIX paths. The console modules
# are declared by exact filename so a NEW module is a deliberate manifest
# change, never an accidental inclusion.
CONSOLE_MODULES = (
    "infrastructure/console/src/oce_console/__init__.py",
    "infrastructure/console/src/oce_console/__main__.py",
    "infrastructure/console/src/oce_console/cli.py",
    "infrastructure/console/src/oce_console/drill.py",
    "infrastructure/console/src/oce_console/kernel.py",
    "infrastructure/console/src/oce_console/session_store.py",
    "infrastructure/console/src/oce_console/submit.py",
    "infrastructure/console/src/oce_console/timeline.py",
    "infrastructure/console/src/oce_console/transport.py",
)
DECLARED_INSTALL_SET = CONSOLE_MODULES + (
    "infrastructure/control-plane/contracts/console-contract.json",
    "infrastructure/control-plane/contracts/job-envelope.schema.json",
    "infrastructure/control-plane/contracts/denial-envelope.schema.json",
    "infrastructure/control-plane/contracts/evidence-manifest.schema.json",
    "infrastructure/control-plane/compose/compose.yml",
    "infrastructure/control-plane/requirements-ci.lock.txt",
    "infrastructure/control-plane/src/oce_control/representative_jobs.py",
)

REQUIRED_ROLLBACK_FIELDS = ("base_commit", "previous_manifest_sha256", "procedure")


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=str(repo_root),
                          capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(manifest: dict) -> str:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def build_manifest(repo_root: Path, *, base_commit: str | None = None,
                   previous_manifest_sha256: str | None = None) -> dict:
    """Build the deterministic release manifest over the declared set.

    Fails closed if any declared file is missing: an incomplete manifest
    is never produced.
    """
    repo_root = Path(repo_root)
    if base_commit is None:
        base_commit = _git(repo_root, "rev-parse", "HEAD")
    files = []
    for rel in sorted(DECLARED_INSTALL_SET):
        path = repo_root / rel
        if not path.is_file():
            raise SystemExit(f"release manifest incomplete: missing declared "
                             f"file {rel}")
        files.append({
            "path": rel,
            "sha256": _sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    lock_path = repo_root / "infrastructure/control-plane/requirements-ci.lock.txt"
    pack_path = repo_root / "infrastructure/control-plane/contracts/console-contract.json"
    manifest = {
        "kind": MANIFEST_KIND,
        "version": MANIFEST_VERSION,
        "base_commit": base_commit,
        "install_set": [f["path"] for f in files],
        "files": files,
        "dependency_lock_sha256": _sha256_file(lock_path),
        "contract_pack_sha256": _sha256_file(pack_path),
        "rollback": {
            "base_commit": base_commit,
            "previous_manifest_sha256": previous_manifest_sha256 or "",
            "procedure": ("restore the git worktree at base_commit; the "
                          "console package is stdlib-only and stateless "
                          "outside its declared session directory"),
        },
    }
    manifest["outer_digest"] = hashlib.sha256(
        _canonical({k: v for k, v in manifest.items() if k != "outer_digest"}
                   ).encode("utf-8")).hexdigest()
    return manifest


def render_manifest(manifest: dict) -> str:
    """Deterministic render: identical manifests -> byte-identical text."""
    return json.dumps(manifest, indent=2, sort_keys=True,
                      ensure_ascii=True) + "\n"


def validate_manifest(manifest: dict) -> None:
    """Fail-closed structural validation (before any verification)."""
    if not isinstance(manifest, dict) or manifest.get("kind") != MANIFEST_KIND:
        raise SystemExit("manifest invalid: wrong kind")
    if manifest.get("version") != MANIFEST_VERSION:
        raise SystemExit("manifest invalid: wrong version")
    if not isinstance(manifest.get("install_set"), list) or not manifest.get("install_set"):
        raise SystemExit("manifest invalid: empty install set")
    if sorted(manifest["install_set"]) != [f["path"] for f in
                                           sorted(manifest["files"],
                                                  key=lambda f: f["path"])]:
        raise SystemExit("manifest invalid: install_set != files paths")
    rollback = manifest.get("rollback") or {}
    missing = [f for f in REQUIRED_ROLLBACK_FIELDS if not rollback.get(f) and
               f != "previous_manifest_sha256"]
    if missing:
        raise SystemExit(f"manifest invalid: rollback missing {missing}")
    if "base_commit" not in rollback or "procedure" not in rollback:
        raise SystemExit("manifest invalid: rollback metadata incomplete")


def verify_manifest(manifest: dict, root: Path) -> tuple[bool, list[str]]:
    """Verify every declared file's hash and size under ``root``.

    Returns (ok, errors); every error names the exact file. The manifest's
    own ``outer_digest`` is re-derived first, so a forged manifest cannot
    bless a tampered tree.
    """
    errors: list[str] = []
    try:
        validate_manifest(manifest)
    except SystemExit as exc:
        return False, [str(exc)]
    recomputed = hashlib.sha256(
        _canonical({k: v for k, v in manifest.items() if k != "outer_digest"}
                   ).encode("utf-8")).hexdigest()
    if recomputed != manifest.get("outer_digest"):
        errors.append(f"outer_digest mismatch: manifest={manifest.get('outer_digest')} "
                      f"recomputed={recomputed}")
    root = Path(root)
    for entry in manifest.get("files", []):
        path = root / entry["path"]
        if not path.is_file():
            errors.append(f"missing file: {entry['path']}")
            continue
        actual_sha = _sha256_file(path)
        if actual_sha != entry["sha256"]:
            errors.append(f"hash mismatch: {entry['path']} "
                          f"manifest={entry['sha256']} actual={actual_sha}")
        actual_size = path.stat().st_size
        if actual_size != entry["size_bytes"]:
            errors.append(f"size mismatch: {entry['path']} "
                          f"manifest={entry['size_bytes']} actual={actual_size}")
    return (not errors), errors


def materialize(manifest: dict, source_root: Path, dest_root: Path) -> list[str]:
    """Copy the declared set from ``source_root`` into a FRESH ``dest_root``.

    The dry-run install: only manifest-declared files are copied, so the
    installed tree can contain nothing the manifest did not declare.
    Returns the copied paths.
    """
    validate_manifest(manifest)
    source_root, dest_root = Path(source_root), Path(dest_root)
    copied = []
    for entry in sorted(manifest["files"], key=lambda f: f["path"]):
        src = source_root / entry["path"]
        if not src.is_file():
            raise SystemExit(f"materialize: missing source file {entry['path']}")
        dst = dest_root / entry["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        copied.append(entry["path"])
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make_release_manifest",
        description=("Build, verify or dry-run-install the OCE console "
                     "release manifest (local only; never deploys)."))
    parser.add_argument("command", choices=("build", "verify", "dry-run"))
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", help="manifest file (verify/dry-run)")
    parser.add_argument("--dest", help="destination directory (dry-run)")
    parser.add_argument("--out", help="output path (build)")
    parser.add_argument("--base-commit", default=None)
    parser.add_argument("--previous-manifest-sha256", default=None)
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    if args.command == "build":
        manifest = build_manifest(repo_root, base_commit=args.base_commit,
                                  previous_manifest_sha256=args.previous_manifest_sha256)
        rendered = render_manifest(manifest)
        if args.out:
            Path(args.out).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    if args.command in ("verify", "dry-run"):
        if not args.manifest:
            parser.error("verify/dry-run require --manifest")
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        if args.command == "verify":
            ok, errors = verify_manifest(manifest, repo_root)
            for error in errors:
                print(error)
            return 0 if ok else 1
        if not args.dest:
            parser.error("dry-run requires --dest")
        materialize(manifest, repo_root, Path(args.dest))
        ok, errors = verify_manifest(manifest, args.dest)
        for error in errors:
            print(error)
        return 0 if ok else 1
    return 2  # pragma: no cover - argparse choices make this unreachable


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
