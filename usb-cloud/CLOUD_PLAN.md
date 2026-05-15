# Free Cloud Tier Strategy — 16GB+ RAM Target

> **Goal:** Accumulate as much free cloud compute as possible to run agent rigs (OpenClaw + Hermes + MT5 tools).
> **Last Updated:** May 14, 2026

---

## The Definitive Free Cloud Compute List

### Tier 1: Always Free (No Expiration, No Credit Card Charges)

| Provider | Instance | RAM | CPU | Storage | Notes |
|----------|----------|-----|-----|---------|-------|
| **Oracle Cloud** | VM.Standard.A1.Flex | **24 GB** | 4 OCPU ARM | 200 GB | **BEST OPTION.** Always free. Ampere A1. |
| **Oracle Cloud** | VM.Standard.E2.1.Micro x2 | 1 GB each | 1/8 OCPU AMD | 50 GB each | Always free. Good for lightweight tasks. |
| **Google Cloud** | e2-micro | 1 GB | 0.25 vCPU | 30 GB HDD | Always free. 1 per month. |
| **AWS** | t2.micro / t3.micro | 1 GB | 1 vCPU | 30 GB EBS | Free for 12 months. |
| **Azure** | B1s | 1 GB | 1 vCPU | 64 GB | Free for 12 months. |

**Always-Free Subtotal: ~28 GB RAM (Oracle 26GB + GCP 1GB + AWS 1GB)**

### Tier 2: Free Trial Credits (Time-Limited but Generous)

| Provider | Credits | Duration | Max Instance | RAM | Notes |
|----------|---------|----------|--------------|-----|-------|
| **Oracle Cloud** | $300 | 30 days | Any paid shape | Up to 192 GB | Trial credits on top of always-free |
| **Google Cloud** | $300 | 90 days | e2-standard-8 | 32 GB | Can run multiple instances |
| **AWS** | $100-300 | Varies | t3.large | 8 GB | Promotional credits |
| **Azure** | $200 | 30 days | D2s_v3 | 8 GB | Trial credits |

### Tier 3: Free Tiers from Smaller Providers

| Provider | Instance | RAM | CPU | Notes |
|----------|----------|-----|-----|-------|
| **Hetzner** | CX22 (trial) | 4 GB | 2 vCPU | €20 free credits on signup |
| **Hetzner** | CAX11 (ARM) | 4 GB | 2 vCPU | €20 free credits |
| **Northflank** | Starter | 512 MB | 0.1 vCPU | Always free (2 services) |
| **Railway** | Starter | 512 MB | 0.1 vCPU | $5 credit/month always free |
| **Render** | Web Service | 512 MB | 0.1 vCPU | Always free tier |
| **Fly.io** | Shared-cpu-1x | 256 MB | 1 vCPU | Always free (3 apps) |
| **Koyeb** | Nano | 256 MB | 0.1 vCPU | Always free |

---

## Recommended Agent Rig Setup

### Primary: Oracle Cloud Always Free (24GB RAM) — MAIN RIG
- **Shape:** VM.Standard.A1.Flex (4 OCPU, 24GB RAM)
- **OS:** Ubuntu 24.04 LTS
- **Cost:** $0/month forever
- **Use:** Main agent rig — OpenClaw + Hermes + workspace + MT5 MCP
- **Storage:** 200GB block volume (always free)
- **Network:** 10TB outbound/month
- **Setup:** Run `cloud-server-setup.sh`

### Secondary: Oracle Cloud Micro x2 (2GB RAM total)
- **Shape:** VM.Standard.E2.1.Micro (2 instances)
- **Cost:** $0/month forever
- **Use:** Monitoring, cron jobs, backup agent, lightweight tasks

### Tertiary: GCP Free Trial ($300, 90 days) — BURST
- **Shape:** e2-standard-4 (4 vCPU, 16GB RAM) or e2-standard-8 (32GB RAM)
- **Cost:** $0 for 90 days with $300 credit
- **Use:** Burst workloads, heavy backtests, parallel agent instances
- **After trial:** Falls back to e2-micro (1GB, always free)

### Quaternary: AWS Free Tier (1GB RAM, 12 months)
- **Shape:** t2.micro or t3.micro
- **Cost:** $0 for 12 months
- **Use:** Hermes Telegram bot, notifications, lightweight always-on tasks

### Quinary: Azure Free Tier (1GB RAM, 12 months)
- **Shape:** B1s
- **Cost:** $0 for 12 months
- **Use:** Additional always-on agent, testing

---

## Total Free Compute Budget

| Phase | RAM | Duration | Cost |
|-------|-----|----------|------|
| **Always Free** | 28 GB | Forever | $0 |
| **Oracle Trial** | +192 GB possible | 30 days | $0 |
| **GCP Trial** | +32 GB | 90 days | $0 |
| **AWS Trial** | +8 GB | 12 months | $0 |
| **Azure Trial** | +8 GB | 30 days | $0 |
| **Peak (all trials active)** | **~268 GB** | First 30 days | $0 |
| **Sustainable (after trials)** | **28 GB** | Forever | $0 |

---

## Sign-Up Requirements & Strategy

### Email Strategy
Use free email providers for sign-ups:
- **ProtonMail:** https://proton.me/mail (encrypted, free, unlimited aliases)
- **Tutanota:** https://tuta.com (encrypted, free)
- **SimpleLogin:** https://simplelogin.io (email forwarding, free tier)

Create dedicated emails:
- `largerlab.oracle@proton.me`
- `largerlab.gcp@proton.me`
- `largerlab.aws@proton.me`
- `largerlab.azure@proton.me`

### Credit Card Strategy
- Oracle Cloud: Needs card for verification only (not charged for always-free)
- GCP: Needs card for verification only (not charged during trial)
- AWS: Needs card for verification only (not charged during free tier)
- Azure: Needs card for verification only (not charged during trial)
- **Use the same card for all** — they only verify identity

### Sign-Up Order (Priority)
1. **Oracle Cloud** → https://cloud.oracle.com/free (biggest always-free)
2. **Google Cloud** → https://cloud.google.com/free ($300 trial)
3. **AWS** → https://aws.amazon.com/free (12-month free tier)
4. **Azure** → https://azure.microsoft.com/free ($200 trial)
5. **Hetzner** → https://www.hetzner.com/cloud (€20 trial credits)

---

## Deployment Plan

### Step 1: Oracle Cloud (Do This First)
1. Sign up at https://cloud.oracle.com/free
2. Create VM.Standard.A1.Flex instance (4 OCPU, 24GB RAM)
3. SSH in and run `cloud-server-setup.sh`
4. Configure OpenClaw + Hermes
5. Clone workspace from GitHub
6. **Result:** 24GB RAM agent rig running 24/7 for free

### Step 2: GCP Free Trial
1. Sign up at https://cloud.google.com/free
2. Create e2-standard-4 instance (16GB RAM)
3. Deploy workspace copy
4. Use for burst workloads
5. **Result:** Additional 16GB RAM for 90 days

### Step 3: AWS Free Tier
1. Sign up at https://aws.amazon.com/free
2. Create t2.micro instance
3. Deploy Hermes Telegram bot
4. **Result:** Always-on Telegram bot for 12 months

### Step 4: Agent Distribution
| Machine | Agent | Role | RAM |
|---------|-------|------|-----|
| Oracle ARM (24GB) | OpenClaw + Hermes | Main agent rig, MT5 MCP, strategy building | 24 GB |
| Oracle Micro x2 | OpenClaw (light) | Monitoring, cron jobs, backups | 2 GB |
| GCP (16GB) | OpenClaw | Burst workloads, heavy backtests | 16 GB |
| AWS (1GB) | Hermes (light) | Telegram bot, notifications | 1 GB |
| Azure (1GB) | OpenClaw (light) | Testing, additional tasks | 1 GB |
| Local | Claude Code + OpenClaw | Development, coding, git | — |

---

## Cost Summary

| Provider | Monthly Cost | RAM | Duration |
|----------|-------------|-----|----------|
| Oracle Cloud (always free) | **$0** | 26 GB | Forever |
| Oracle Cloud (trial) | **$0** | +192 GB possible | 30 days |
| GCP (trial) | **$0** | 16 GB | 90 days |
| AWS (free tier) | **$0** | 1 GB | 12 months |
| Azure (trial) | **$0** | 1 GB | 30 days |
| **Total Sustainable** | **$0/mo** | **28 GB** | **Forever** |
| **Total Peak** | **$0** | **~236 GB** | **First 30 days** |

---

## Security Notes
- Each cloud account gets its own API keys (least privilege)
- SSH keys per machine, no password auth
- Firewall: only ports 22 (SSH), 18789 (OpenClaw gateway), 443 (HTTPS)
- No secrets in cloud console — use environment variables
- Nightly GitHub backup of workspace + memory files
- Use ProtonMail for all cloud account emails
