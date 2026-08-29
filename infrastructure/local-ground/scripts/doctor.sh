#!/usr/bin/env bash
#
# doctor.sh — capture an environment fingerprint (A-003). Used to record
# tool versions, runtime target, and detected local stack for evidence.
set -uo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$BASE_DIR/var/environment-fingerprint.json}"
mkdir -p "$(dirname "$OUT")"

python3 - "$OUT" <<'PY'
import json, os, platform, subprocess, sys

def ver(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = (r.stdout + r.stderr).strip().splitlines()
        return out[0][:120] if out else None
    except Exception:
        return None

fp = {
    "os": platform.system(),
    "platform_release": platform.release(),
    "machine": platform.machine(),
    "runtime_target": os.environ.get("OCE_RUNTIME_TARGET", "local"),
    "python": ver(["python3", "--version"]),
    "git": ver(["git", "--version"]),
    "docker": ver(["docker", "--version"]),
    "docker_compose": ver(["docker", "compose", "version"]),
    "ansible": ver(["ansible-playbook", "--version"]),
    "ansible_lint": ver(["ansible-lint", "--version"]),
    "shellcheck": ver(["shellcheck", "--version"]),
    "gitleaks": ver(["gitleaks", "version"]),
    "wsl": subprocess.run(["wsl", "-l", "-v"], capture_output=True, text=True, timeout=10).returncode == 0,
}
try:
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(fp, f, indent=2)
    print("fingerprint ->", sys.argv[1])
except Exception as e:
    print("FATAL: cannot write fingerprint:", e, file=sys.stderr)
    raise SystemExit(3)
PY