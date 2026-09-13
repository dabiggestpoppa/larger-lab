# Cloud Ground Architecture — Data Boundary

**Document ID:** B1-ARCH-DATA-001
**Version:** 1.0
**Status:** SPECIFIED

---

## Data Classification

| Class | Examples | Storage | Retention | Backup |
|-------|----------|---------|-----------|--------|
| Durable Truth | Job state, identities, decisions, manifests | PostgreSQL | Indefinite (migrated) | WAL + full |
| Transient Transport | Task notifications, leases, caches | Redis | Voluntary expiry | None required |
| Artifact | Build outputs, models, reports | Object storage (R2) | Per class policy | Cross-provider |
| Configuration | Ansible, Compose, policy | Git repository | Indefinite | Git remote |
| Logs | Service logs, audit trails | Host filesystem | 30 days | Optional |
| Backup Metadata | Backup manifests, restore logs | PostgreSQL | Indefinite | Included |

## Storage Targets

### PostgreSQL (Durable Truth)
- All accepted job state, service identities, decisions, manifests
- Schema versioned via migrations
- Connections: private network, TLS where applicable
- Not for: large binaries, model files, bulk datasets, logs

### Redis (Transport Only)
- Task notifications, short-lived leases, rate limiting, caches
- **Prohibited:** sole copy of any accepted intent, final result, approval, capital state, audit evidence
- Can be destroyed and rebuilt from PostgreSQL

### Object Storage (Artifacts)
- S3-compatible: Cloudflare R2 initially, Backblaze B2 for backup diversity
- All artifacts: ID, type, producer, hash, size, retention class, lineage
- Workers receive scoped, expiring upload/download grants
- Secrets and broker credentials are **prohibited** as artifacts

### Host Filesystem
- System, container data, logs, work staging, backup staging — logically distinct
- Quotas and alerts prevent disk exhaustion
- Large immutable artifacts route to object storage

## Backup Policy

- **RPO:** 15 minutes (continuous WAL archive)
- **RTO:** 4 hours (control-plane core), 24 hours (cold artifacts)
- **Database:** pgBackRest or equivalent — continuous WAL, weekly full, daily incremental
- **Files:** restic or equivalent — 7 daily, 4 weekly, 6 monthly snapshots
- **Copies:** Primary on server; encrypted off-server; periodic offline bundle
- **Restore:** Mandatory clean-room drill for Block 1 gate

## Retention Classes

| Class | Disposition | Typical Use |
|-------|-------------|-------------|
| CRITICAL | Retain indefinitely with audit | Capital records, constitutional decisions |
| OPERATIONAL | Retain 1 year, then review | Job state, service logs |
| ARTIFACT | Retain 90 days unless promoted | Build outputs, reports |
| TRANSIENT | Retain 7 days | Debug logs, temporary staging |
| HAZARDOUS | Redact/expire/delete with tombstone | Secrets, credentials, sensitive data |
