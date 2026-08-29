#!/usr/bin/env bash
#
# generate-cloud-plan.sh — deterministic, NON-mutating cloud deployment plan.
# No provider is contacted. No external state is touched. Used by
# `oce-ctl deploy validate|plan --target cloud`.
#
# Usage: generate-cloud-plan.sh [--mode validate|plan]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MODE="${1:-plan}"

echo "# OCE Cloud Deployment Plan (A-003) — falls closed"
echo ""
echo "mode: ${MODE} (read-only; zero provider contact; zero external mutation)"
echo "runtime_target: ${OCE_RUNTIME_TARGET:-local}"
echo "cloud_activation_state: DEFERRED_BY_OPERATOR"
echo ""

# Deterministic reconciliation input: the frozen local-ground contract.
python3 - "$BASE_DIR/contracts/local-ground-contract.json" "$BASE_DIR" <<'PY'
import json, os, sys
contract = json.load(open(sys.argv[1], encoding="utf-8"))
base = sys.argv[2]
ledger = contract["ledger_model"]
provider = contract["provider_policy"]
lines = [
    "## Contract summary",
    f"- local_ground_state:     {ledger['local_ground_state']}",
    f"- cloud_plan_state:       {ledger['cloud_plan_state']}",
    f"- cloud_activation_state: {ledger['cloud_activation_state']}",
    f"- cloud_deployment_state: {ledger['cloud_deployment_state']}",
    f"- cloud_cost_state:       {ledger['cloud_cost_state']}",
    f"- operator_hold_reason:   {ledger['operator_hold_reason']}",
    "",
    "## Future activation profile (deferred; never auto-applied)",
    f"- approved future target provider: {provider['approved_future_target_provider']}",
    f"- approved future target product:  {provider['approved_future_target_product']}",
    f"- provider values are adapter-only: {provider['provider_values_in_deployment_adapters_only']}",
    "",
    "## Apply prerequisites (missing any one => DENIED)",
    " - AUTHORIZED_STAGE",
    " - CLOUD_AUTHORIZATION_ENVELOPE",
    " - CLOUD_PROVIDER + CLOUD_PROVIDER_IDENTITY",
    " - CLOUD_COST_APPROVED_USD",
    " - PUBLIC_EXPOSURE_APPROVED",
    "",
    "## This plan performed NO mutations",
    " - provider contacts: 0",
    " - resources changed: 0",
    " - cost incurred: ZERO",
]
print("\n".join(lines))
PY