#!/usr/bin/env bash
#
# worker-admit.sh — bounded local worker admission gate (A-002/A-003).
#   admit  <envelope.json>   — admits only envelopes that validate AND stay
#                              inside the local allowed scope.
#   reject <envelope.json>   — rejects unconditionally (for negative tests).
#
# Workers are stateless and bounded: they never inherit parent memory,
# credentials, or cloud authority.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCHEMA="$BASE_DIR/contracts/worker-task-envelope.schema.json"
ADMISSIONS="$BASE_DIR/var/worker-admissions.jsonl"

mkdir -p "$(dirname "$ADMISSIONS")"

mode="${1:-}"; env_file="${2:-}"
if [ -z "$mode" ] || [ -z "$env_file" ] || [ ! -f "$env_file" ]; then
  echo "BLOCKED: worker-admit.sh <admit|reject> <envelope.json>" >&2
  exit 3
fi

if [ "$mode" = "reject" ]; then
  echo "REJECTED (unconditional)" 
  exit 1
fi

python3 - "$env_file" "$SCHEMA" "$ADMISSIONS" <<'PY'
import json, os, sys, datetime
env, schema_path, admissions = sys.argv[1], sys.argv[2], sys.argv[3]
env = json.load(open(env, encoding="utf-8"))
schema = json.load(open(schema_path, encoding="utf-8"))

def validate(inst, sch, path="$"):
    if "type" in sch:
        t = sch["type"]
        ok = (t == "object" and isinstance(inst, dict)) or (t == "array" and isinstance(inst, list)) or (t == "string" and isinstance(inst, str)) or (t == "number" and isinstance(inst, (int, float)) and not isinstance(inst, bool)) or (t == "boolean" and isinstance(inst, bool))
        if not ok:
            raise ValueError(f"{path}: expected {t}")
    if isinstance(inst, dict):
        if sch.get("additionalProperties") is False:
            extra = set(inst) - set(sch.get("properties", {}))
            if extra:
                raise ValueError(f"{path}: unexpected properties {sorted(extra)}")
        for k, subs in sch.get("properties", {}).items():
            if k in inst:
                validate(inst[k], subs, f"{path}.{k}")
        for req in sch.get("required", []):
            if req not in inst:
                raise ValueError(f"{path}: missing required '{req}'")
        enums = sch.get("enum")
        if enums and inst not in enums:
            raise ValueError(f"{path}: not in enum")
        mn = sch.get("minimum")
        if mn is not None and isinstance(inst, (int, float)) and inst < mn:
            raise ValueError(f"{path}: below minimum {mn}")
    elif isinstance(inst, list):
        for i, item in enumerate(inst):
            validate(item, sch.get("items", {}), f"{path}[{i}]")

validate(env, schema)

# Local scope guard: a local worker may never touch cloud/credentials/external.
local_allowed_paths_prefix = ["infrastructure/local-ground", "projects", "tests"]
blocked_tools = ["aws", "gcloud", "az", "docker", "kubectl", "terraform", "gitleaks", "gh", "git"]
for p in env.get("allowed_paths", []):
    if not any(p.startswith(pre) for pre in local_allowed_paths_prefix):
        raise ValueError(f"allowed_path '{p}' outside local scope")
for t in env.get("allowed_tools", []):
    if t in blocked_tools:
        raise ValueError(f"tool '{t}' forbidden for local worker")

rec = {"task_id": env["task_id"], "parent_agent": env["parent_agent"],
       "authority": env["authority"], "time_limit_s": env["time_limit_s"],
       "admitted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "decision": "ADMITTED"}
with open(admissions, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec) + "\n")
print("ADMITTED", env["task_id"])
PY