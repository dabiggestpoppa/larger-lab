# Trading Sector

Hermes-operated commercial trading-research and engineering vertical built on OCE Opportunity Exchange, Quant Lab, Research Mesh and QCAE.

**Branch:** `agent/trading-sector-hermes-program`  
**Launch posture:** Python/Pine first; NinjaTrader pilot; MT5/MQL5 decline-by-default.  
**Commercial posture:** normal project floor ~$150; dominate $300–$1,200 middle market; selectively pursue $900–$5,000+ research/infrastructure work.

---

## Canonical Reading Order

1. [`TRADING_SECTOR_R0_CHARTER_v0.1.md`](./TRADING_SECTOR_R0_CHARTER_v0.1.md)  
   Product identity, market bands, technical boundaries, IP doctrine and launch invariants.

2. [`TRADING_SECTOR_R0_BRANCH_ARCHAEOLOGY_AND_CAPABILITY_SALVAGE_v0.1.md`](./TRADING_SECTOR_R0_BRANCH_ARCHAEOLOGY_AND_CAPABILITY_SALVAGE_v0.1.md)  
   Current capability inventory across main, Quant Lab, CEREBUS, Crypto Foundry, Grant Sector and OCE; explicit no-rebuild discipline.

3. [`TRADING_SERVICE_CATALOG_PRICING_AND_PACKAGES_v0.1.md`](./TRADING_SERVICE_CATALOG_PRICING_AND_PACKAGES_v0.1.md)  
   Human-readable packages, price bands, add-ons, scope escalation and decline rules.

4. [`TRADING_SERVICE_PACKAGE_REGISTRY_v0.1.json`](./TRADING_SERVICE_PACKAGE_REGISTRY_v0.1.json)  
   Machine-readable package registry and global gates.

5. [`TRADING_HERMES_OPERATOR_PROGRAM_v0.1.md`](./TRADING_HERMES_OPERATOR_PROGRAM_v0.1.md)  
   Hermes roles, worker contracts, morning market routine, qualification, proposal, QA, revision and closeout workflows.

6. [`TRADING_JOB_SPEC.schema.json`](./TRADING_JOB_SPEC.schema.json)  
   Machine-readable normalized client/job contract.

7. [`TRADING_SECTOR_MASTER_BUILD_AND_LAUNCH_PLAN_v0.1.md`](./TRADING_SECTOR_MASTER_BUILD_AND_LAUNCH_PLAN_v0.1.md)  
   TS-B0 through TS-B10 build/launch roadmap.

8. [`TRADING_SECTOR_CONTINUOUS_EXECUTION_MASTER_PROMPT_v0.1.md`](./TRADING_SECTOR_CONTINUOUS_EXECUTION_MASTER_PROMPT_v0.1.md)  
   Primary prompt/operating contract to hand to Hermes once the runtime is installed and connected to the authorized workspace.

---

## Program Identity

Trading Sector is not a signal shop or cheap Pine-script service.

It sells:

```text
TRADER IDEA / CODE / BROKEN SYSTEM
              ↓
       deterministic scope
              ↓
   research / engineering / audit
              ↓
       reproducible validation
              ↓
       code + evidence packet
```

Primary product moat:

- Python + Pine capability together;
- strategy formalization;
- robust backtesting/validation;
- lookahead/repaint/data/timing forensics;
- state/regime research;
- provenance/falsification discipline;
- cross-platform semantic equivalence;
- existing Quant Lab/OCE/QCAE institutional infrastructure.

---

## Launch Packages

| ID | Package | Launch Range |
|---|---|---:|
| TS-PKG-01 | Pine Quick Build / Repair | $150–$300 |
| TS-PKG-02 | Custom TradingView Indicator Pro | $300–$650 |
| TS-PKG-03 | Indicator → Strategy / Strategy Engineering | $400–$850 |
| TS-PKG-04 | Python Backtest & Strategy Validation | $500–$1,200 |
| TS-PKG-05 | Strategy Audit / Forensic Debug | $350–$900 |
| TS-PKG-06 | Pine ↔ Python Translation + Equivalence | $500–$1,200 |
| TS-PKG-07 | NinjaTrader Translation Pilot | $750–$1,500+ |
| TS-PKG-08 | Quant Research Sprint | $900–$2,000 |
| TS-PKG-09 | Quant Research Infrastructure Build | $1,500–$5,000+ |
| TS-PKG-10 | Ongoing Research / Engineering Retainer | $750–$2,500+/month |

Prices are launch hypotheses. Recalibration occurs from actual proposal conversion, labor, revisions, platform fees and realized margin—not anxiety or competitor undercutting.

---

## Supported Technology Policy

### Core

- Python
- Pine Script / TradingView
- research/backtesting
- data/provenance work
- statistical/market-state analysis
- Pine ↔ Python translation

### Pilot

- NinjaTrader / NinjaScript through QCAE qualification.

### Decline by default

- MT5
- MQL5
- EA development/maintenance

Only the operator can reopen the excluded class.

---

## First Build / Launch Milestones

```text
TS-B0  Reality Lock / Capability Proof
TS-B1  Commercial Product Constitution
TS-B2  Portfolio & Proof Pack
TS-B3  Client Intake & Job Contract
TS-B4  Market Operations
TS-B5  Delivery Engines
TS-B6  Research / QA Constitution
TS-B7  QCAE Capability Extension
TS-B8  First 5–10 Paid Jobs
TS-B9  Pricing / Market Recalibration
TS-B10 Retainers & High-Ticket Expansion
```

The immediate practical path is:

```text
Reality Lock
→ Portfolio Proof
→ Job Spec / Delivery Kernels
→ Upwork + Fiverr setup
→ First paid pilot batch
→ Reprice from evidence
→ Expand high-ticket / retainer work
```

---

## Hermes Boot Instruction

Once Hermes is installed:

1. give it `TRADING_SECTOR_CONTINUOUS_EXECUTION_MASTER_PROMPT_v0.1.md` as the operating contract;
2. point it to this branch;
3. require the canonical reading order above before changes;
4. authorize only the desired build/market stage;
5. retain operator confirmation for platform contract/financial actions until authority is explicitly widened;
6. review first deliveries in each package family;
7. keep client/IP/economic experience boundaries intact.

Hermes must operate the Trading Sector program; it must not replace OCE/Quant Lab/QCAE/Research Mesh with its own ad-hoc versions.

---

## Parent / Peer Systems

- **OCE / Institution:** authority, objectives, state, Opportunity Exchange and economic learning.
- **Research Mesh:** external epistemic acquisition.
- **Quant Lab:** empirical trading research and validation substrate.
- **CEREBUS:** advanced internal trading-research lineage; proprietary logic remains protected.
- **Crypto Foundry / Sensor Fabric:** provenance, falsification, state research, adapter and evidence-engineering patterns.
- **QCAE:** capability acquisition / build-borrow-buy-rent decisions.
- **Grant Sector:** reusable Hermes/commercial-agent operating patterns only; no grant-domain logic is inherited.

---

## Hard Invariants

- reuse before rebuild;
- Python/Pine first;
- MT5/MQL decline-by-default;
- no guaranteed performance claims;
- no client-capital custody or managed-account activity in this program;
- no proprietary CEREBUS leakage;
- no client-confidential strategy reuse without rights;
- no vague project proceeds to implementation without normalized scope;
- no research result is altered merely to please a client;
- no new capability is silently acquired without pricing its burden;
- no marketplace technical access grants authority beyond current OCE/platform rules.
