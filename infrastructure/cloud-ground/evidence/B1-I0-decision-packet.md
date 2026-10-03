# B1-I0 — Purchase Decision Packet (Hold Point)

**Date:** 2026-08-26 · **AUTHORIZED_STAGE:** B1-I0 (decision research and planning only)
**Decision:** **RECOMMEND_PURCHASE_PENDING_OPERATOR_APPROVAL**
**Currency:** EUR/USD assumed ≈ 1.10 (observations ranged ~1.05–1.17 across sources) — all EUR prices shown ex-VAT unless noted

---

## 1. Current requirements (from ratified Block 1 plan)

- One durable EU host for Cloud Ground: Ubuntu 24.04 baseline (B1-I2), PostgreSQL + Redis data plane (B1-I3), encrypted off-server backup (B1-I4), runtime/observability services (B1-I5).
- Local-first: development and validation run locally (Windows dev host + Linux-capable validation where platform support permits); CI provides authoritative clean-environment validation; cloud is for deployment, durability, remote availability, observability, and operational insight — never a basic functional dependency for ordinary development.
- Off-provider backup: encrypted backups stored with a **different** provider than the durable host.
- Burst/GPU compute (B1-I7): separate, untrusted, hourly — OctaSpace/RunPod candidates, NOT the durable provider.

## 2. Local-first / cloud role boundary

- Ordinary OCE development and validation stay local; the complete validation pipeline runs locally where the platform permits (on this Windows host ansible-core/ansible-lint are Linux-controller-only, so the shared runner honestly reports BLOCKED there — CI provides the authoritative green).
- The durable host is the first **deployment** target. Nothing about Cloud Ground makes local work depend on it.

## 3. Verified provider comparison (see B1-I0-provider-comparison.md)

| Provider / product | CPU | RAM | Disk | Monthly (ex-VAT) | Notes |
|---|---|---|---|---|---|
| **netcup RS 4000 G12** | 12 dedicated vCore (EPYC) | 32 GB ECC | 1 TB NVMe RAID | **€32.49** (€27.08 12-mo) | Named product; best dedicated value; availability-constrained |
| OVH VPS-4 (2027) | 8 shared vCore | 24 GB | 200 GB NVMe | **$23.37** | Reliable, backup included, no setup |
| Hetzner CX53 | 16 shared vCore | 32 GB | 320 GB NVMe | **€29.49** | Shared CPU; June-2026 increase |
| Hetzner CCX33 | 8 dedicated vCore | 32 GB | 240 GB NVMe | **€138.49** | Dedicated tier no longer competitive (2.2x increase) |
| Contabo Cloud VPS 8 | 8 shared vCore | 24 GB | 300 GB SSD | **€11.20** (promo 24 mo) | Cheapest; performance-variability reputation |

## 4. Recommended durable provider

**netcup RS 4000 G12** — best value for a durable, dedicated-CPU EU host:
- 12 dedicated vCores / 32 GB ECC / 1 TB NVMe at €32.49/mo — dramatically cheaper than Hetzner's dedicated tier (CCX33 €138.49) for comparable resources.
- Hardware RAID, KVM console, backup system, IPv4+IPv6 included, unmetered traffic.
- **Risk:** current availability constraint ("unavailable at this location" on the product page). Mitigation: order with location flexibility (AT/DE/NL auto-selection) or fall back to OVH.

## 5. Recommended fallback

**OVHcloud VPS-4 (2027 range), $23.37/mo** — reputable, EU/US regions, daily backup included, no setup fee, 1-click upgrade. Use if netcup availability fails or the operator prefers a larger provider.
Budget fallback: **Contabo Cloud VPS 8 (€11.20/mo promo)** if cost is the dominant constraint and modest, variable performance is acceptable.

## 6. Recommended off-provider backup

**Backblaze B2 (~$6/TB/mo, S3-compatible, free egress up to 3× storage)** or **Hetzner Object Storage (€5.99–6.49/mo base, EU data)** — explicitly a different vendor from the durable host. Encrypted (age/restic) backups with RPO/RTO evidenced in B1-I4.

## 7. Minimum viable configuration

- 1 × netcup RS 4000 G12 (12 vCPU / 32 GB / 1 TB) — comfortably hosts Postgres, Redis, and observability with headroom.
- 1 × off-provider object store (B2 or Hetzner OS), 1 TB class.
- No additional IPs, no load balancer, no managed DB (self-hosted per plan).

## 8. Expected monthly cost (recurring)

- Host: €32.49 (~$36) + backup: ~€5.99–6.00 (~$6.60) ≈ **~€38.5/mo (~$42/mo)**.

## 9. First-month maximum

- €32.49 + setup (~€5–30) + backup ≈ **€43.5–68.5 (~$48–75)**.

## 10. Hard spending ceiling (recommendation for operator approval)

- **$60/mo recurring, $100 first-month maximum.** Covers host + backup + VAT headroom + one snapshot experiment.

## 11. Cancellation and rollback implications

- netcup: cancel with notice before contract-term end; monthly contract minimizes lock-in; host is rebuilt from scratch by the B1-I2 playbook — rollback is a clean redeploy (that is the design point).
- OVH: cancel anytime; downgrade requires migration.
- All data is reproducible from the repo + off-provider encrypted backup; no irreversible infrastructure is created before B1-I2 playbook completion.

## 12. Security and jurisdiction risks

- netcup: German provider, EU data centers, GDPR-aligned; 19% DE VAT for non-VAT-registered customers.
- OVH: EU + US regions; choose EU region for the Cloud Ground host.
- All backups encrypted at rest before upload (age/restic); no real credentials in the repo; Tailscale private network per plan; firewall deny-all except SSH via Tailscale (B1-I2).
- Burst/GPU providers (OctaSpace/RunPod) are untrusted by policy — isolated, no credentials, B1-I7 experiments only.

## 13. Contradictions and unknowns

- netcup product page currently shows availability constraints while pricing pages list the product — must be confirmed at order time (could push to OVH).
- 2026 was a price-increase year (netcup May 2026, Hetzner June 2026, OVH Feb/Mar 2026) — all figures are point-in-time; re-confirm the exact quote at order.
- netcup exact setup fee and backup-space size not published on the landing page — confirm before order.
- Hetzner IPv4 fee and post-adjustment CX-tier suitability for a DB host unconfirmed.
- Contabo post-promo price unknown.
- EUR/USD assumed 1.10.

## 14. What becomes possible in B1-I2 (after operator approval + purchase)

- Authoritative clean-host baseline: Ubuntu 24.04, Tailscale private network, firewall, Docker Engine + Compose, storage layout (B1-I2).
- Then B1-I3 data plane (Postgres/Redis + durability tests), B1-I4 backup/restore with real RPO/RTO evidence, B1-I5 runtime/observability, B1-I6 local worker admission, B1-I7 burst-worker experiments, B1-I8 Windows boundary, B1-I9 block gate.

## 15. Explicit purchase hold point

**STOP.** No purchase has been made. No account created. No credential requested. No cloud resource exists.

The operator must separately authorize execution with:

```
AUTHORIZED_STAGE=B1-I2
APPROVED_PROVIDER=<provider>
APPROVED_PRODUCT=<product>
APPROVED_MAX_FIRST_MONTH_USD=<amount>
APPROVED_MAX_MONTHLY_USD=<amount>
```

Recommended approval values for the hold: provider `netcup`, product `RS 4000 G12`, first month ≤ $100, monthly ≤ $60.
