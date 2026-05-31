# HEARTBEAT.md - OC2 Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/>.
Max 4000 chars.

## Current Status (2026-05-30 23:45 EDT)
- **MAD last interaction:** msg #5364 — confirmed Forex tab = CFD, dual-tab scrape done
- **PHASES 1-5 COMPLETE** | Phase 6 desktop app pending MAD signal for PM/CC handoff

## Phase 5 FULL BUILD — COMPLETE
- API server: `sniper-dashboard/api_server.py` (FastAPI, port 8090, 8 endpoints, live data)
- **32 firms in DB** (15 Futures + 15 Forex/CFD + 2 legacy), PES snapshots stored for all
- Dashboard `api.ts` connected to real API (no more mock data), build passes
- Top 5: Apex Trader Funding $5K (0.44), FundedNext Futures $25K (0.068), E8 Futures $25K (0.046), Funded Futures Family $50K (0.046), My Funded Futures $25K (0.046)
- Dashboard build: `npm run build` passes clean (4/4 static pages)
- Dual-tab scraper: `scrape(category="futures")` + `scrape(category="forex")` + `scrape_both_tabs()`

## Scraper Engine — UPDATED
- `scraper_engine.py` now supports both Futures and Forex (CFD) tabs
- 28 firm slugs in `KNOWN_FIRM_SLUGS`
- Fresh snapshot: `sniper/snapshots/propfirmmatch_20260530_232056.json`
- Real pricing scraped from /challenge pages (activation + challenge fee)
- PES calculator now uses TRUE cost via `_dict_to_firm_profile` (reads true_cost_per_size first)
- DB updated: true_cost_per_size, activation_fees, billing_types columns added
- Results: Lucid Trading 100K (PES 13.52) → #1, not Apex
- Files: true_pes.py, real_pricing.py, update_true_costs.py

## Phase 6 — Desktop App Handoff Package
- Meditation file: `meditation-room/desktop-app-meditation.md` (823 lines, Tauri)
- All P1-5 source code ready for PM/CC dev team
- Awaiting MAD signal to pass off

## DEPLOYED — CEREBUS FX v4.0
- **Symmetry Trap (B):** EURUSD.PRO | Magic 20260531 | Lot 0.03 | 2:00 AM EST
- **P90 CASCADE (A):** USDCHF.PRO | Magic 20260532 | Lot 0.01 | 9:00 AM EST

## DEPLOYED — Prop Firm Sniper Engine v1.0
- **13 Python modules** in `quant-lab/sniper/` (all compile OK, ~350KB)
- Dashboard: `sniper-dashboard/` (Next.js 14, 6 components, build OK)

## Active Cron Jobs
| Job | Time (EST) | Status |
|-----|------------|--------|
| ST Executor | 2:00 AM | OK |
| P90 CASCADE | 9:00 AM | OK |
| Overnight Report | 5:00 AM | OK |
| Mid-Day Monitor | 8/10/12PM | 1 error (watching) |
| STRUCT/PULSE/ECHO | 6-6:30 AM | Fleet OK |
| DRIFT | Sun/Wed/Sat 6:45AM | OK |

## Notes
- Scrapling not installed — live PropFirmMatch uses snapshot data
- Dashboard shows real firm data + PES scores
- Next: MAD signals Phase 6 handoff to PM/CC dev team
