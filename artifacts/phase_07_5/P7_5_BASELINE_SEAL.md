# P7.5 Baseline Seal — CR-P7.5-ROUTING-BASELINE-SEAL-01

**Base:** db9f8c62 · **Date:** 2026-08-15

## Accepted

- **Family A** — EUR accumulation → JPY weakness — STRONG
- **Family B** — EUR liquidation → JPY strength — STRONG

## Conditional / Watchlist

Family C is NOT strategy-promoted: preserved as a validated factor relationship; its pair-space trading baseline is **MARGINAL / WATCHLIST** (untouched expectancy ~1.17 bps, PF ~1.05, Sharpe ~0.22). No new independent evidence yet.

## Frozen Execution Rules

| Family | Pair | Delay | Hold | Trade |
|--------|------|-------|------|-------|
| A | USDJPY | 2h | 6h | long |
| B | USDJPY | 1h | 6h | short |

- **Frozen execution policy:** P0 (selected on development only; see P7_5_POLICY_COMPARISON.csv)
  - selection basis: expectancy_per_raw_event_bps on inner_sel+inner_val
    - P0: per-event +8.714 bps (total +5315.3 bps)
    - P1: per-event +7.283 bps (total +4442.9 bps)
    - P2: per-event +8.714 bps (total +5315.3 bps)
    - P3: per-event +7.283 bps (total +4442.9 bps)

## Validation Status

- The 2025-07..2026-05 segment is **RELATIONSHIP_CONFIRMED_OOS**: untouched wrt Phase-7 execution-parameter selection but NOT untouched wrt relationship discovery/promotion. Final independent holdout is NOT claimed.
- **FORWARD_OOS_PENDING:** no price/event data after 2026-05-31; move to shadow observation.

## Verdicts

| Family | Verdict | Dev exp/bps | OOS exp/bps | OOS PF | OOS win |
|--------|---------|-------------|-------------|--------|---------|
| A | **STRONG** | +9.38 | +10.13 | 2.38908280488973 | 0.604 |
| B | **STRONG** | +8.12 | +6.18 | 1.809766078013067 | 0.574 |
| A+B | **STRONG** | +8.71 | +8.21 | 2.101296093029243 | 0.589 |

## Concurrency (raw event book, all splits)

- raw events: 890 · executed trades: 890
- simultaneous-position hours: 585 · opposite-direction overlap hours: 228
- max concurrent positions: 3 · max |net| exposure: 18.19

## Cost Stress (break-even multiplier)

- A: break-even cost multiplier 3.0
- B: break-even cost multiplier 3.0
- A+B: break-even cost multiplier 3.0

## Stop

Sealed baseline produced. No CEREBUS overlay, no Kelly sizing, no pyramiding, no deployment, no MT5 execution.