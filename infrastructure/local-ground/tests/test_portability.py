#!/usr/bin/env python3
"""OCE Local Ground — command portability regressions (B1-LOCAL, A-003).

R12: `oce-ctl` and the subordinate scripts must be executable from a clean
checkout (correct git exec modes) and must resolve paths from the script
location, not the caller's working directory. Both regressions run anywhere
(no Docker required).
"""
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"
REPO_ROOT = BASE_DIR.parents[1]

_BASH = shutil.which("bash") or "bash"


def test_scripts_have_executable_git_modes():
    """All Local Ground scripts carry executable git modes (100755), so a
    clean Linux/CI checkout can run them without 'Permission denied'."""
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "-s",
                        "infrastructure/local-ground/scripts"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    non_exec = []
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            mode, _, _, path = parts[0], parts[1], parts[2], parts[3]
            if not mode.startswith("100755"):
                non_exec.append(path)
    assert not non_exec, f"scripts without executable git mode: {non_exec}"


def test_ctl_works_from_working_dir_outside_repo(tmp_path):
    """oce-ctl resolves subordinate scripts from the script location and works
    when invoked from a working directory outside the repository."""
    import json
    import os
    env = dict(os.environ, OCE_RUNTIME_TARGET="local", PYTHONDONTWRITEBYTECODE="1")
    # state-only scope: the operator-facing default is full (requires the
    # runtime), but this portability proof runs without Docker.
    r = subprocess.run([_BASH, str(SCRIPTS / "oce-ctl"), "backup", "--scope", "state-only",
                        "--out", str(tmp_path / "bk")],
                       cwd=str(tmp_path), env=env, capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "bk" / "BACKUP_MANIFEST.sha256").is_file()
    info = json.loads((tmp_path / "bk" / ".backup-content" / "backup-info.json").read_text(encoding="utf-8"))
    assert info["format"] == "oce-local-ground-backup-v1"
    assert info["scope"] == "state-only" and info["disaster_recovery_capable"] is False
