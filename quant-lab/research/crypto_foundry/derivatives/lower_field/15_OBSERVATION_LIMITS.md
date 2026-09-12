# CRYPTO-ALT-LOWER-FIELD-0 — OBSERVATION LIMITS

**Checkpoint:** `CRYPTO-ALT-LOWER-FIELD-0`
**Agent:** AGENT 2
Per the Constitution: never claim more resolution than the observation layer
supports. This document states exactly what the lower-field observation layer
can and cannot see, and how every claim in this checkpoint is bounded.

## 1. Observation layer (what we actually measured)

| Observable | Status | Notes |
|---|---|---|
| Rank (CMC global) | OBSERVED | dated CMC snapshots, PIT by construction |
| Market cap (USD) | OBSERVED | snapshot quote, USD (convertId 2781); cross-venue CMC aggregation |
| Price (USD) | OBSERVED | snapshot close (lastUpdated 23:59Z semantics) |
| Volume 24h | PARTIAL | CMC-reported venue aggregation; fake-volume risk UNVERIFIED below top tiers |
| Exchange coverage | PARTIAL | CMC aggregates undisclosed venue set; single-venue pricing possible below rank 1000 |
| Chain membership | PARTIAL | platform field present for tokens; absent for native coins; CURRENT_APPROXIMATION for lower ranks |
| Sector/subsector | PARTIAL | CMC tags = HISTORICAL_APPROXIMATION (inherited frozen status from canonical panel); tag coverage grows over time |
| Listing age | OBSERVED | CMC dateAdded |
| Liquidity | PARTIAL | only dollar-volume proxy; true depth/order-book liquidity UNOBSERVED |
| TVL / stablecoin context / bridge / DEX | UNOBSERVED | outside this checkpoint's panel (canonical flow tables cover Top-500 chain level only) |
| Perp/spot availability | UNOBSERVED | per-asset venue eligibility below rank 500 not collected (canonical ledger is Top-500) |
| Tokenomics / supply state | PARTIAL | circulating/total/max supply present; unlock schedules UNOBSERVED |
| Delisting events | PARTIAL | dead assets remain in dated snapshots while ranked; post-delisting tail UNOBSERVED |

## 2. Structural data risks (lower field, explicit)

1. **Stale pricing** — many lower-rank assets update price irregularly. Detected
   via `flag_stale_price` (price unchanged on days with |market move| > 0.5%).
   Rate reported by band. Key results re-run with stale rows excluded (P3).
2. **Thin volume** — zero-volume days are common below rank 750. Flagged;
   results reported raw and clean.
3. **Fake volume** — undetectable from CMC aggregates; `flag_suspicious_volume`
   is a heuristic (volume burst without price move), recorded, never asserted
   as fact.
4. **Single-venue pricing** — a lower-rank asset may trade on one venue; CMC
   aggregate price inherits that venue's distortions. UNVERIFIED at this layer.
5. **Listing-day distortions** — new listings enter ranked snapshots with
   volatile prints; `flag_listing_day` (age ≤ 3d) flags these; P-sensitivity
   reported.
6. **Rebrands / token swaps** — preserved via stable CMC `id`; symbol changes
   recorded in identity map. Swap-adjusted returns NOT reconstructible from
   snapshots alone (price discontinuity risk; flagged where detected).
7. **Snapshot gaps** — CMC-side short dates (rows < 2000) are persisted with a
   `complete` flag and documented in 04; no backfill.
8. **Survivorship** — none by construction (dated snapshots include assets
   later delisted/collapsed). The panel is not a modern-survivor universe.
9. **Rank instability** — high churn at ranks 501-2000 is real field behavior
   AND a source of unbalanced panels per asset; minimum-observation rules
   (≥120 days) applied.
10. **API coverage changes** — CMC added/removed coins from tracking over time;
   early-years (2020-2022) coverage below rank 1000 is thinner; reported by
   year in 03.

## 3. Claim-level bounds

| Claim type | Allowed evidence ceiling |
|---|---|
| Rank-dependent response amplitude | L0-L1 descriptive (co-movement + temporal ordering of snapshots). No causality claim. |
| Horizon information structure | L0 descriptive; incremental R² is not predictive causality. |
| Asymmetry (down > up) | L0 descriptive, cross-regime stability reported (L4 only if sign stable across subperiods AND perturbations). |
| Explanatory hierarchy | L0-L1; variance decomposition is descriptive, not causal. |
| Participant/horizon interpretation ("shorter-horizon speculative capital") | Hypothesis language ONLY; never asserted as fact from price behavior. |
| Chain/sector residual structure | L0 descriptive; chain field is CURRENT_APPROXIMATION — treated as lens, not identity. |
| Hidden-state / HMM structure | Gated in Phase L; any latent model labelled hypothesis; states never named from outcomes. |

## 4. What this checkpoint does NOT claim

- No claim about actual trader identity, intent, or holding period.
- No claim about exploitable predictability (no strategy evaluation of any kind).
- No claim that CMC rank = investable universe (liquidity unverified).
- No claim below the observation layer's resolution (per Constitution).

## 5. Repair paths (for Agent 1 / later checkpoints)

- Per-venue historical pricing for lower ranks (Binance/OKX archive) → would
  resolve single-venue pricing and fake-volume unknowns.
- CoinPaprika/CG current registry cross-join for chain membership verification.
- DefiLlama chain-level flow already canonical for Top-500; extension to lower
  field requires per-asset TVL history (UNOBSERVED here).
