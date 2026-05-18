# OC3 VPS Deployment Plan — Phase A
> **Created:** 2026-05-17 15:22 EDT
> **Target:** Deploy OC3 to remote VPS via Docker
> **Provider:** OctaSpace (cheapest, decentralized GPU cloud)
> **MAD Action Required:** Create OctaSpace account + get API key

---

## Prerequisites (MAD needs to do)
1. Create account at https://octa.space
2. Get API key from dashboard
3. Send API key to OWL (or set OCTASPACE_API_KEY env var)

## Deployment Steps (OWL executes tonight)

### Step 1: Install OctaSpace SDK
```
pip install octaspace
```

### Step 2: Spawn VPS Instance
Using cloud-burst.py:
```
python tools/cloud-burst.py spawn --provider octaspace --gpu RTX_4070 --hours 720 --task "OC3 OpenClaw twin pillar"
```
- RTX 4070: $0.04/hr = ~$29/mo
- 720 hours = 30 days always-on
- Docker container with Ubuntu 22.04

### Step 3: Install OpenClaw on VPS
Via SSH into the OctaSpace container:
```bash
# Install Node.js 26
curl -fsSL https://deb.nodesource.com/setup_26.x | bash -
apt-get install -y nodejs

# Install OpenClaw
npm install -g openclaw

# Create OC3 config directory
mkdir -p ~/.openclaw-3
```

### Step 4: Configure OC3
- Copy OC3 config to VPS
- Use laguna-m.1:free model (lightweight, free)
- Same Discord + Telegram tokens as OC2
- Port 18791

### Step 5: Bridge OC2 ↔ OC3
- Set up WireGuard tunnel between local OC2 and remote OC3
- Update twin_bridge.py to use network heartbeat instead of file-based
- H3 Hermes runs locally, monitors both

### Step 6: Test & Validate
- OC3 gateway responds on VPS
- Discord + Telegram connected
- Twin heartbeat flowing
- Failover test: kill local OC3, verify remote OC3 takes over

## Cost Estimate
- OctaSpace RTX 4070: $0.04/hr × 720hr = $28.80/month
- Bandwidth: minimal (heartbeat + API calls only)
- Total: ~$30/month

## Fallback Plan
If OctaSpace doesn't work out:
- DigitalOcean droplet: $6/month (1GB RAM, 1 vCPU)
- Vultr: $5/month (1GB RAM, 1 vCPU)
- Hetzner: €4/month (2GB RAM, 1 vCPU) — best value

## Tonight's Checklist
- [ ] MAD creates OctaSpace account
- [ ] MAD sends API key
- [ ] OWL installs octaspace SDK
- [ ] OWL spawns VPS instance
- [ ] OWL installs OpenClaw on VPS
- [ ] OWL configures OC3
- [ ] OWL sets up WireGuard bridge
- [ ] OWL tests twin-pillar continuity
- [ ] MAD verifies OC3 is live
