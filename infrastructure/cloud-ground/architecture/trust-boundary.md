# Cloud Ground Architecture — Trust Boundary

**Document ID:** B1-ARCH-TRUST-001
**Version:** 1.0
**Status:** SPECIFIED

---

## Trust Zones

### Zone 1: Operator (Full Authority)
- Operator device via Tailscale
- Full administrative access
- Can stop, restart, and configure all services
- Authentication: Tailscale identity + key-based SSH

### Zone 2: Control Plane (Service Authority)
- PostgreSQL, Redis, Observability
- Private network only — no public ports
- Each service has a distinct least-privilege identity
- Database credentials are service-scoped

### Zone 3: Workers (Scoped Task Authority)
- Local worker, burst workers, Windows/MT5 worker
- **Never** receive direct PostgreSQL, Redis, SSH, or admin credentials
- Task-scoped, time-limited credentials only
- Outbound connections only (inbound blocked)

### Zone 4: External Storage (Ephemeral)
- Object storage (R2/B2) for artifacts and backups
- Scoped upload/download credentials with expiry
- No administrative access to compute resources

## Access Matrix

| From → To | Operator | PostgreSQL | Redis | Object Storage | Worker |
|-----------|----------|------------|-------|----------------|--------|
| Operator | — | Full (private) | Full (private) | Full (private) | Admin (private) |
| PostgreSQL | N/A | — | None | None | None |
| Redis | N/A | None | — | None | None |
| Object Storage | N/A | None | None | — | Scoped r/w |
| Worker (local) | N/A | **DENIED** | **DENIED** | Scoped r/w | N/A |
| Worker (burst) | N/A | **DENIED** | **DENIED** | Scoped r/w | N/A |
| Worker (windows) | N/A | **DENIED** | **DENIED** | Scoped r/w | N/A |

## Invariants

1. No worker receives persistent database credentials
2. No worker can reach PostgreSQL, Redis, or SSH directly
3. Burst workers receive zero standing secrets
4. Revocation of a worker credential stops new work immediately
5. Break-glass access is auditable and triggers rotation
6. No service uses shared credentials across environments

## Network Rules (Block 1)

- **All services:** Tailscale-only access
- **No public ingress** on any port
- **SSH:** Key-based, non-root only, private network only
- **PostgreSQL:** 5432 internal only
- **Redis:** 6379 internal only
- **Metrics:** Internal only (future)
