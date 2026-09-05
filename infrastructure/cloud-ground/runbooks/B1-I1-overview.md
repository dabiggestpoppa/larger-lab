# B1-I1 Operator Runbook — Overview

## What B1-I1 Does

B1-I1 creates the **static infrastructure skeleton** for OCE Cloud Ground. This means:

1. Architecture documentation describing the target topology
2. Ansible roles for host configuration (tasks exist but are untested)
3. Docker Compose files for PostgreSQL and Redis (syntactically valid, not rendered)
4. Machine-readable JSON Schema contracts for worker admission, artifacts, etc.
5. Policy files encoding ratified cost, network, and retention thresholds
6. Static validation scripts that check structure and syntax
7. Operator runbooks explaining what is and is not proven

## What B1-I1 Does NOT Prove

- ❌ No server has been provisioned
- ❌ No private network has been tested on a real host
- ❌ No database durability or restore has been proven
- ❌ No local/burst/Windows worker has been admitted
- ❌ No OCE/PO runtime capability has been reality-sealed
- ❌ Block 1 is NOT GATED_COMPLETE
- ❌ No real credentials exist in this skeleton

## How to Run Validation

```bash
# Check what tools are available
./infrastructure/cloud-ground/scripts/doctor

# Run static validation (deterministic checks)
./infrastructure/cloud-ground/scripts/validate-static

# Collect evidence for review
./infrastructure/cloud-ground/scripts/collect-evidence
```

## How to Read Results

| Result | Meaning |
|--------|---------|
| PASS | Check passed with evidence |
| FAIL | Check failed — must be addressed |
| BLOCKED | Tool not available — check skipped |
| UNKNOWN | Cannot determine result |

## How Future B1-I2 Deployment Will Be Authorized

1. You review B1-I1 evidence
2. You decide to approve, revise, quarantine, or stop
3. You separately authorize B1-I0 (purchase decision) or B1-I2 (deployment)
4. Each stage requires explicit `AUTHORIZED_STAGE=B1-Ix`

## How to Stop Before Spending

- **No purchase has been made** — B1-I1 costs $0
- **No cloud resources exist** — nothing to tear down
- **No exposure occurred** — all files are local
- To remove B1-I1: `git branch -D oce/block-1-i1-cloud-ground`

## Where Evidence Lives

- Validation results: `infrastructure/cloud-ground/evidence/`
- Build learning: `infrastructure/cloud-ground/evidence/BUILD_LEARNING_LEDGER.md`
- File manifest: `infrastructure/cloud-ground/evidence/file-manifest.json`
- Tool manifest: `infrastructure/cloud-ground/evidence/tool-manifest.json`
- Stage status: `infrastructure/cloud-ground/evidence/stage-status.json`

## How to Inspect Differences from the Ratified Plan

Compare this skeleton against `docs/oce-golden-system/OCE_BLOCK_01_CLOUD_GROUND_PLAN_v1.0.md` Part IX (Implementation Staging Plan). B1-I1 scope is:
- Architecture documentation ✓
- Ansible host baseline skeleton ✓
- Compose foundation ✓
- Machine-readable contracts ✓
- Policy as data ✓
- Static validation ✓
- Operator runbooks ✓
