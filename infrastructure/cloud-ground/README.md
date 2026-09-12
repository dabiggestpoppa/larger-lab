# Cloud Ground — B1-I1 Infrastructure Skeleton

**Stage:** B1-I1 (static infrastructure repository skeleton)
**Authorization:** B1-I1 only — no cloud purchase, provisioning, deployment, or exposure
**Branch:** `oce/block-1-i1-cloud-ground`

## What This Is

This directory contains the **static skeleton** for the OCE Golden System Block 1 Cloud Ground infrastructure. It provides:

- Architecture documentation describing the target topology
- Ansible roles for host baseline configuration
- Docker Compose foundation for PostgreSQL and Redis
- Machine-readable JSON Schema contracts for worker admission, artifact manifests, etc.
- Policy-as-data files encoding ratified cost, network, and retention thresholds
- Static validation scripts that run deterministic checks without provisioning
- Operator runbooks explaining what is and is not proven

## What This Is NOT

- **This is not a deployed system.** No server has been provisioned.
- **This is not proof of capability.** B1-I1 validates structure and syntax only.
- **This does not authorize B1-I2+** deployment or purchase.
- **No real credentials exist in this skeleton.** All secrets are placeholder references.

## Directory Structure

```
cloud-ground/
├── README.md                          # This file
├── architecture/                      # Target topology documentation
│   ├── topology.md                    # System architecture diagram and description
│   ├── trust-boundary.md              # Network trust zones and access rules
│   ├── data-boundary.md               # Data storage, backup, and retention
│   └── decision-map.md                # Key architectural decisions and rationale
├── ansible/                           # Host baseline automation
│   ├── ansible.cfg                    # Ansible configuration
│   ├── inventories/example/           # Example inventory with placeholder values
│   ├── playbooks/                     # Top-level playbooks
│   └── roles/                         # Ansible roles for host configuration
├── compose/                           # Docker Compose service definitions
│   ├── compose.foundation.yml         # PostgreSQL and Redis foundation
│   ├── compose.observability.yml      # Observability stack (future)
│   ├── config/                        # Service configuration templates
│   └── examples/                      # Example .env files with placeholders
├── contracts/                         # JSON Schema machine-readable contracts
│   ├── worker-task-envelope.schema.json
│   ├── worker-capability-manifest.schema.json
│   ├── worker-admission-report.schema.json
│   ├── artifact-manifest.schema.json
│   ├── service-identity.schema.json
│   ├── cost-ledger.schema.json
│   └── evidence-manifest.schema.json
├── policy/                            # Policy-as-data files
│   ├── network-access.yml             # Network role definitions
│   ├── resource-classes.yml           # Resource classes and hard ceilings
│   ├── retention-classes.yml          # Data retention and disposition classes
│   └── cost-guardrails.yml            # Cost thresholds and approval gates
├── scripts/                           # Validation and utility scripts
│   ├── doctor                         # Environment prerequisite check
│   ├── validate-static                # Main static validation command
│   ├── render-config                  # Config template rendering (placeholder)
│   └── collect-evidence               # Evidence collection script
├── tests/                             # Static validation tests
├── evidence/templates/                # Evidence report templates
└── runbooks/                          # Operator documentation
```

## How to Run Validation

```bash
# Check prerequisites
./infrastructure/cloud-ground/scripts/doctor

# Run static validation
./infrastructure/cloud-ground/scripts/validate-static
```

## Current Status

| Layer | Status | Notes |
|-------|--------|-------|
| Architecture docs | IMPLEMENTED_UNVERIFIED | Static documentation |
| Ansible skeleton | IMPLEMENTED_UNVERIFIED | Roles have tasks but untested on live host |
| Compose foundation | IMPLEMENTED_UNVERIFIED | Syntactically valid, unrendered |
| JSON Schema contracts | IMPLEMENTED_UNVERIFIED | Schemas validate fixtures |
| Policy files | IMPLEMENTED_UNVERIFIED | Data files, enforcement future |
| Static validation | IMPLEMENTED_UNVERIFIED | Runs deterministic checks |
| Operator runbooks | IMPLEMENTED_UNVERIFIED | Documentation only |

**No feature in this skeleton is promoted beyond IMPLEMENTED_UNVERIFIED.** All claims are bounded by the B1-I1 static validation scope.

## Cost Impact

- **New recurring cost:** $0
- **Burst cost:** $0
- **Cloud mutations:** None
- **Public exposure:** None

## Evidence Location

- Validation results: `infrastructure/cloud-ground/evidence/`
- Build learning: `infrastructure/cloud-ground/evidence/BUILD_LEARNING_LEDGER.md`
- Reality inventory: `infrastructure/cloud-ground/evidence/REALITY_INVENTORY.md`
