#!/usr/bin/env bash
#
# bootstrap-local.sh — idempotent B1-LOCAL bootstrap (A-003).
# Validates prerequisites, checks secrets, ensures the deterministic var/,
# builds the compose .env from the example if absent (never overwrites),
# and brings the default local runtime up when docker is available.
#
# Idempotent: rerunning is safe and produces equivalent state.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_DIR="$BASE_DIR/compose"
VAR_DIR="$BASE_DIR/var"

echo "==============================================================="
echo "  OCE Local Ground bootstrap (A-003)"
echo "  runtime_target=${OCE_RUNTIME_TARGET:-local}"
echo "==============================================================="

missing=""
for t in python3 git; do
  if ! command -v "$t" >/dev/null 2>&1; then missing="$missing $t"; fi
done
if [ -n "$missing" ]; then
  echo "BLOCKED: missing mandatory tools:${missing}" >&2
  exit 3
fi

# Deterministic working dir (gitignored via var/)
mkdir -p "$VAR_DIR"
test -w "$VAR_DIR" || { echo "BLOCKED: $VAR_DIR not writable" >&2; exit 3; }

# Compose .env: create from example only if absent; NEVER overwrite existing.
mkdir -p "$COMPOSE_DIR"
if [ ! -f "$COMPOSE_DIR/.env" ]; then
  if [ -f "$COMPOSE_DIR/examples/oce.env.example" ]; then
    cp "$COMPOSE_DIR/examples/oce.env.example" "$COMPOSE_DIR/.env"
    echo "created placeholder $COMPOSE_DIR/.env (EDIT BEFORE USE; never commit)"
  else
    echo "WARN: no example env; operator must provide $COMPOSE_DIR/.env" >&2
  fi
else
  echo "exists: $COMPOSE_DIR/.env (left untouched)"
fi

# Startup validation: fail closed on missing secrets. Secrets may be
# injected securely via the environment (preferred) or compose/.env.
python3 - "$COMPOSE_DIR/.env" <<'PY'
import os, sys
env = sys.argv[1]
required = ["POSTGRES_PASSWORD", "ARTIFACT_SECRET_KEY"]
vals = {k: os.environ.get(k, "") for k in required}
if os.path.exists(env):
    with open(env, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("="); vals.setdefault(k.strip(), v.strip())
for k in required:
    v = vals.get(k, "")
    if not v or "change-me" in v:
        print(f"FAIL_CLOSED: secret '{k}' not set (or still a placeholder)"); raise SystemExit(3)
print("secret preflight OK (redacted; values not echoed)")
PY
rc=$?
[ $rc -ne 0 ] && { echo "bootstrap halted at secret guard" >&2; exit $rc; }

# Optional: bring the runtime up when docker exists.
if command -v docker >/dev/null 2>&1; then
  bash "$SCRIPT_DIR/oce-ctl" local up
  rc=$?
  echo "bootstrap: docker present, runtime start exit=$rc"
  exit $rc
fi

echo "bootstrap: docker absent — environment ready, container runtime available via CI."
echo "           Re-run after installing Docker Desktop/WSL2 (docked by operator)."
exit 0