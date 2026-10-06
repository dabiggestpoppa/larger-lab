# Cloud Ground Architecture — Decision Map

**Document ID:** B1-ARCH-ADM-001
**Version:** 1.0
**Status:** SPECIFIED

---

## Key Decisions

| ID | Decision | Status | Rationale |
|----|----------|--------|-----------|
| B1-ADR-001 | netcup RS 4000 G12 as baseline | RATIFIED | Dedicated CPU, 32 GB ECC, 1 TB NVMe, low cost |
| B1-ADR-004 | Ubuntu Server 24.04 LTS minimal | RATIFIED | Broad tooling, stable support |
| B1-ADR-005 | Ansible + Docker Compose; no Kubernetes | RATIFIED | Reproducible without orchestration complexity |
| B1-ADR-006 | Tailscale private-first access | RATIFIED | $0 operator tier, tagged worker fabric |
| B1-ADR-007 | No public ingress in Block 1 | RATIFIED | Minimize attack surface |
| B1-ADR-008 | PostgreSQL = truth, Redis = transport | RATIFIED | Durable acceptance, deterministic reconciliation |
| B1-ADR-009 | S3-compatible artifact storage | RATIFIED | Portable artifacts independent of host disk |
| B1-ADR-010 | R2 for artifacts, B2 evaluated for backup | RATIFIED | R2 free egress, B2 capacity pricing |
| B1-ADR-012 | OctaSpace = experimental/untrusted | RATIFIED | Low price but marketplace variability |
| B1-ADR-013 | RunPod as standardized fallback | RATIFIED | Predictable API at higher cost |
| B1-ADR-014 | Windows/MT5 paper/shadow only | RATIFIED | Preserve capital boundary |
| B1-ADR-016 | Cost: $60 warn, $50 burst stop, $100 gate | RATIFIED | Bounded financial exposure |

## Rejected/Deferred

| ID | Item | Disposition | Reason |
|----|------|-------------|--------|
| B1-RJ-002 | Kubernetes in Block 1 | REJECTED | One-user system doesn't justify complexity |
| B1-RJ-003 | Public DB/Redis/SSH exposure | REJECTED | Violates private-first doctrine |
| B1-RJ-005 | OctaSpace as authoritative control plane | REJECTED | Marketplace heterogeneity conflicts with durable truth |
| B1-RJ-007 | Entire workspace copied to server | REJECTED | Preserves entropy, bypasses canonicalization |

## Constitution Alignment

All decisions conform to OCE Constitution 1.1:
- §4 Principles 1-15
- §8 Articles I-XIX
- §12 Cloud and Deployment Doctrine
- §16 Constitutional Build Order

## Downstream Dependencies

Block 1 decisions establish ground capability. They do NOT authorize:
- Block 2 OCE Reality Seal work
- Block 7+ Quant Foundation
- Block 9+ Capital-bearing execution
