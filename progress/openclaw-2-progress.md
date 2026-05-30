# OC2 Progress -- OWL (OpenClaw-2)

> **Last Updated:** 2026-05-30 14:15 EDT

## Phase 1 -- PROP SNIPER ENGINE: Shallow Well Build

### COMPLETED (Direct Build by OWL)

**New Modules Created:**
1. `quant-lab/sniper/ontology_mapper.py` -- Ontology Translation Layer
   - PropFirmOntology dataclass (30+ fields: cost, DD, trailing type, consistency, FF, etc.)
   - OntologyMapper.from_propfirm_match() -- maps raw scrape → clean ontology
   - TrailingType, DDType enums with proper classification
   - Cost of Capital (CoC) calculation with latency decay and consistency penalty

2. `quant-lab/sniper/scraper_engine.py` -- Real Scraper
   - PropFirmMatchScraper: Scrapling StealthyFetcher primary, requests+bs4 fallback
   - PayoutJunctionScraper: payout verification data
   - Regex-based data extraction (sizes, promos, DD rules, consistency, payout)
   - Change detection via content hashing + snapshot comparison

3. `quant-lab/sniper/ff_matrix.py` -- F&F Matrix + Deployment Router
   - FFScalingMatrix: Exponential CoC decay via F&F fragmentation
   - find_optimal_fragmentation() -- optimal account size × quantity
   - CapitalDeploymentRouter: Ranks all firms → DeploymentDirective per firm
   - Full JSON output: prop_firm_matrix.json

**Skills Created:**
4. `skills/tools/scrapling/SKILL.md` -- Scrapling stealth scraping tool reference

**Infrastructure Fixes:**
- Fixed all relative imports in sniper package (was blocking `python -m` usage)
- Created `quant_lab` junction → `quant-lab` directory for Python package imports
- Cleared all __pycache__ files

**Test Results:**
- All 4 test firms ranked: MFF #1 (PES 2.205), Topstep #2 (1.537), TickFunded #3 (0.625), Apex #4 (0.624)
- Lethal trailing DD detection: TickFundedTrader correctly flagged
- Consistency bypass: Working for FF-enabled firms
- JSON matrix output: configs/prop_firm_matrix.json

### KNOWN ISSUES (to fix in Phase 2)
- Cost model: linear scaling produces unrealistic per-account fees at small sizes (needs floor pricing)
- Scraper: regex-based extraction needs calibration against actual PropFirmMatch DOM
- PayoutJunction: placeholder only — needs real scraping

### Metadata
- CEREBUS edge for PES calc: WR 85.7%, 2.0 trades/day, Sharpe 8.5, monthly R 15, PF 8.0
- Target bandwidth: $50,000
- PropFirmMatch URL: https://propfirmmatch.com/futures
- PayoutJunction URL: https://payoutjunction.com/
