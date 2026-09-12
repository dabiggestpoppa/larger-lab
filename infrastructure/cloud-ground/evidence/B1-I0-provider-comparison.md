# B1-I0 — Durable Provider Comparison (Research Only)

**Date:** 2026-08-26 · **AUTHORIZED_STAGE:** B1-I0 (decision research and planning only — NO purchase)
**Currency:** EUR/USD assumed ≈ 1.10 (observations ranged ~1.05–1.17 across sources) — all EUR prices shown ex-VAT unless noted

This is re-priced research for the durable Cloud Ground host, the off-provider
backup/object store, and (separately, untrusted) burst/GPU workers for B1-I7.
No provider has been contacted, no account created, no credential requested.

---

## 1. Durable Cloud Ground provider — netcup RS 4000 G12 (named product)

| Field | Value |
|---|---|
| Exact product | netcup RS 4000 G12 ("ip iv" = IPv4 + IPv6), root server |
| CPU | 12 dedicated vCores, AMD EPYC 9645 (some sources list EPYC 9634); guaranteed CPU/RAM/SSD |
| RAM | 32 GB DDR5 ECC |
| Storage | 1 TB NVMe, hardware RAID controller |
| Included transfer | Unmetered (fair use) |
| Port speed | 1 Gbit/s |
| Region | Europe — AT / DE / NL (auto-location or selectable) |
| IPv4 / IPv6 | Both included |
| Setup fee | Small one-time fee — confirm at order (historically ~€5–30; vouchers can offset) |
| Monthly price | **€32.49** ex-VAT, monthly contract (vpsbenchmarks, Aug 2026); €27.08 ex-VAT with 12-month commitment; G2 lists €33.04 |
| Taxes / VAT | 19% German VAT unless VAT-registered; ex-VAT shown |
| Billing cadence | Monthly or 12-month; contracts auto-renew — cancel with notice before term end |
| Cancellation | Notice before end of contract period; data deleted |
| Backup / snapshot | Built-in backup system + remote KVM console included; separate object storage available (price confirm at order) |
| Object storage | netcup Object Storage exists (S3-compatible) — price confirm at order |
| Expected recurring | ~€32.49/mo (≈$36); +€5.99 backup = ~€38.48/mo (≈$42) |
| First-month total | ~€43.48–68.48 (monthly + setup €5–30 + backup) ≈ $48–75 |
| Worst-case monthly | ~€45.79 incl 19% VAT (≈$50) |
| Upgrade path | Larger RS tiers (RS 5000 / RS 6000 etc.) |
| Limitations | Availability constrained ("currently unavailable at this location" on product page — supply risk); German provider, EU data; price increase effective 2026-05-01 |
| Evidence URL | https://www.netcup.com/en/server/root-server/rs-4000-g12-ip-iv-12m ; https://www.vpsbenchmarks.com/hosters/netcup/plans/rs-4000-g12 |
| Evidence retrieved | 2026-08-26 |
| Confidence | High on specs/price; Medium on immediate availability (site shows stock constraints) |
| Unresolved unknowns | Exact current setup fee; exact backup-space size; exact contract cancellation window |

## 2. OVHcloud VPS-4 (current equivalent — "VPS 2027" range)

| Field | Value |
|---|---|
| Exact product | OVHcloud VPS-4 (2027 range; replaces the discontinued 8 vCPU/32 GB/640 GB VPS-4) |
| CPU | 8 vCores (shared, 2 GHz+) |
| RAM | 24 GB |
| Storage | 200 GB NVMe |
| Included transfer | Unlimited traffic |
| Port speed | 3 Gbps public bandwidth |
| Region | Many (EU: Paris, Strasbourg, Frankfurt, London, Warsaw…; US, CA, APAC) |
| IPv4 / IPv6 | Dedicated IPv4 + IPv6 included |
| Setup fee | None; no commitment |
| Monthly price | **from $23.37** ex-VAT (US site) |
| Taxes / VAT | Per-country (ex-VAT shown on US site) |
| Billing cadence | Monthly |
| Cancellation | Cancel anytime; downgrade requires new plan + data migration (upgrade is 1-click) |
| Backup / snapshot | Daily backup of previous 24 h INCLUDED (7 rolling); Premium backup from $1.40/mo; snapshots from $0.40/mo |
| Object storage | OVH Object Storage / additional disks available (price on demand) |
| Expected recurring | ~$23.37/mo + optional premium backup ≈ $25/mo |
| First-month total | ~$23.37–26/mo (no setup) |
| Worst-case monthly | ~$30 with premium backup + VAT where applicable |
| Upgrade path | 1-click scale to larger models |
| Limitations | Shared vCPU; new range renames models (VPS-1 is now the entry at 2 vCPU/4 GB); some features (monitoring, load balancer) excluded in Local Zones |
| Evidence URL | https://us.ovhcloud.com/vps/ |
| Evidence retrieved | 2026-08-26 |
| Confidence | High (official pricing page) |
| Unresolved unknowns | EU-region price for VPS-4 (shown on US page); exact Local-Zone availability |

## 3. Hetzner — closest suitable alternatives (post-June-2026 adjustment)

| Field | Value |
|---|---|
| Exact products | Cloud CX43 (8 shared vCPU / 16 GB / 160 GB NVMe) — **€15.99/mo**; CX53 (16 shared / 32 GB / 320 GB) — **€29.49/mo**; CCX23 (4 dedicated / 16 GB / 160 GB) — **€85.99/mo**; CCX33 (8 dedicated / 32 GB / 240 GB) — **€138.49/mo** |
| CPU | Shared (CX) or dedicated (CCX) AMD vCPU |
| RAM / Storage | 16–32 GB / 160–320 GB NVMe |
| Included transfer | 20 TB included (EU); overage extra |
| Port speed | 10 Gbit/s infrastructure (per Hetzner) |
| Region | FSN/NBG/HEL (Germany/Finland); ASH/HIL (US); SIN (Singapore) |
| IPv4 / IPv6 | IPv6 included; IPv4 charged extra (~€0.50–3.50/mo — confirm) |
| Setup fee | None; hourly billing with monthly cap, no commitment |
| Taxes / VAT | 19% German VAT for consumers unless VAT-registered |
| Cancellation | Delete instance anytime (hourly) |
| Backup | Cloud volume snapshots (paid); Storage Box BX11 1 TB = €3.20/mo; Object Storage base €5.99–6.49/mo (1 TB + 1 TB egress) |
| Object storage | Hetzner Object Storage (S3-compatible) |
| Expected recurring | CX43 ≈ €15.99 + IPv4; CX53 ≈ €29.49 + IPv4 |
| First-month total | ≈ monthly + IPv4 (no setup) |
| Worst-case monthly | CCX23 €85.99 + IPv4 (dedicated tier no longer value) |
| Upgrade path | Rescale hourly; cap protects monthly bill |
| Limitations | **June 15 2026 price adjustment: CCX +2.1–2.73x, CPX +2.4–2.75x, CX/CAX +1.3–1.4x** — dedicated vCPU (CCX) is no longer competitive; new orders pay new prices |
| Evidence URL | https://www.hetzner.com/cloud/general-purpose/ ; https://northflank.com/blog/hetzner-cloud-server-price-increases |
| Evidence retrieved | 2026-08-26 |
| Confidence | High |
| Unresolved unknowns | Exact IPv4 fee at order; whether CX tier suits a durable DB host (shared CPU) |

## 4. Contabo Core VPS — low-cost fallback

| Field | Value |
|---|---|
| Exact products | Cloud VPS 8 (8 vCPU / 24 GB / 300 GB SSD) — **€14.00 incl / €11.20 excl VAT** (first 24 months); Cloud VPS 12 (12 vCPU / 48 GB / 400 GB) — €25.00 / €20.00 |
| CPU | 8–12 shared vCPU |
| RAM / Storage | 24–48 GB / 300–400 GB SSD |
| Included transfer | Unlimited traffic |
| Port speed | 600 Mbps – 1 Gbit/s |
| Region | EU (DE, US, SE, SG…) |
| IPv4 / IPv6 | Dedicated IPv4 + IPv6 included |
| Setup fee | None advertised; Auto Backup add-on |
| Monthly price | €11.20–20.00 excl VAT (first 24 months; reverts after promo) |
| Taxes / VAT | Shown incl/excl; EU VAT per country |
| Cancellation | Monthly; no long commitment |
| Backup / snapshot | 1–3 snapshots included; Auto Backup add-on (price confirm) |
| Object storage | Contabo Object Storage available (price confirm) |
| Expected recurring | ≈ €11.20/mo (VPS 8, first 24 months) |
| First-month total | ≈ monthly |
| Worst-case monthly | Promo expiry raises price; oversubscription risk under load |
| Upgrade path | Larger Core VPS tiers |
| Limitations | Reputation for performance variability/oversubscription under sustained load; modest port speeds; promo pricing is temporary |
| Evidence URL | https://contabo.com/en-us/vps/ |
| Evidence retrieved | 2026-08-26 |
| Confidence | High on price; Medium on sustained performance |
| Unresolved unknowns | Post-promo price for VPS 8; Auto Backup add-on price |

---

## 5. Off-provider backup / object storage (separate from durable provider)

| Option | Storage | Egress | Notes |
|---|---|---|---|
| Backblaze B2 | ~$6–6.95/TB/mo | free up to 3× monthly storage, then $0.01/GB | S3-compatible; recommended off-provider target |
| Hetzner Object Storage | €5.99–6.49/mo base (1 TB + 1 TB egress incl) | ~€1.20/TB after | S3-compatible; EU data (aligns with GDPR posture) |
| Hetzner Storage Box BX11 | 1 TB — €3.20/mo | included | rsync/SFTP; simple off-provider backup target |

Recommended off-provider backup: **Backblaze B2 or Hetzner Object Storage** — deliberately a different provider from the durable host (off-provider means not the same vendor as the Cloud Ground host).

## 6. Burst / GPU workers — B1-I7 candidates (UNTRUSTED, NOT durable Cloud Ground)

| Provider | Indicative pricing | Classification |
|---|---|---|
| RunPod | RTX 4090 ~$0.34–0.74/hr; RTX A6000 ~$0.33–0.53/hr | Burst GPU worker candidate for B1-I7 experiments only |
| OctaSpace | GPU/CPU marketplace, hourly (~$0.2–1.0/GPU-hr typical) | Burst worker candidate for B1-I7 experiments only |

These are **not** candidates for the durable Cloud Ground provider. They are evaluated and admitted (or rejected) in B1-I7.
