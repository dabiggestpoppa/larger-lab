#!/usr/bin/env bash
#
# doctor.sh — capture an environment fingerprint (A-003). Every optional tool
# probe is platform-safe: missing commands are recorded truthfully (absent),
# never raise, and WSL is probed only when the executable exists on a
# supporting host. Fingerprint generation always completes unless the output
# cannot be written.
set -uo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$BASE_DIR/var/environment-fingerprint.json}"
mkdir -p "$(dirname "$OUT")"

python3 - "$OUT" <<'PY'
import json, os, platform, shutil, subprocess, sys

def probe(exe, args=("--version",)):
    """Return a truthful tool state. Distinguishes absent from failed."""
    found = shutil.which(exe)
    if found is None:
        return "absent"
    try:
        r = subprocess.run([found] + list(args), capture_output=True, timeout=10)
        out = (r.stdout or b"").decode("utf-8", errors="replace")
        err = (r.stderr or b"").decode("utf-8", errors="replace")
        text = (out + err).strip().splitlines()
        if r.returncode == 0 and text:
            return text[0][:120]
        return "present"  # executable exists but --version failed or empty
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "absent"

def probe_wsl():
    """Probe WSL only when wsl exists; never decode UTF-16 as text."""
    if shutil.which("wsl") is None:
        return "absent"
    try:
        r = subprocess.run(["wsl", "-l", "-v"], capture_output=True, timeout=10)
        return "installed" if r.returncode == 0 else "not-installed"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "not-installed"

fp = {
    "os": platform.system(),
    "platform_release": platform.release(),
    "machine": platform.machine(),
    "runtime_target": os.environ.get("OCE_RUNTIME_TARGET", "local"),
    "tools": {
        "python": probe("python3"),
        "git": probe("git"),
        "docker": probe("docker"),
        "docker_compose": probe("docker", ("compose", "version")),
        "ansible": probe("ansible-playbook"),
        "ansible_lint": probe("ansible-lint"),
        "shellcheck": probe("shellcheck"),
        "gitleaks": probe("gitleaks"),
        "wsl": probe_wsl(),
    },
}
try:
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(fp, f, indent=2)
    print("fingerprint ->", sys.argv[1])
except OSError as e:
    print("FATAL: cannot write fingerprint:", e, file=sys.stderr)
    raise SystemExit(3)
PY