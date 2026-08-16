# CR-RISK-BLOCK-II — Intermediate Seal (R5 + R6 synthesis)

**Task:** CR-RISK-BLOCK-II-INTERMEDIATE-SEAL · **Base:** 0cb3b510 · R6 1e8cc01f ·
R5 150a93de · Block-I 8ca072d0 · branch `capital-routing`

## 1. Status
R5 PASS/ACCEPTED · R6 PASS/ACCEPTED (incl. correction 0cb3b510) ·
this seal: **PASS** (integrity recheck: True).

## 2. Integrity recheck (frozen artifacts only)
- Events: **890** (A 432 /
  B 458) · Episodes: **482** ·
  Max concurrency: **3** (R1: 3).
- H0 baselines: 50/50 f=1% 71.21%
  / 5.19% DD; f=2%
  190.31% /
  10.17%; 70/30
  74.57% /
  6.97%; 100/0
  79.15% /
  10.3% — matches sealed prior math.
- R6 corrected MC: zero duplicate (policy, scheme, alloc, f) keys
  (0); schemes ['block', 'episode', 'iid']; H0 block-MC
  50/50 f=1% **DOMINATED** (corrected frontier).
- Single-position share of in-DD hourly loss: **84.7%**;
  multi-position: **15.3%** (14.3% at
  2 concurrent, 1.0% at 3+).

## 3. R5 frozen family truth
- A: mean 0.393R · PF 2.31 · WR
  63.9% · breach -1R 10.4% ·
  solo max DD at f=1% 10.3%.
- B: mean 0.308R · PF 1.94 · WR
  61.4% · breach -1R 13.8% ·
  solo max DD at f=1% 11.1%.
- B is the capital limiter (deep-loss frequency + streaks, not extremes);
  same-day corr ~-0.085; P(B loss|A loss) 12% vs 23% unconditional;
  co-tail coincidence 0% in sample. A-only stays positive at 50% edge,
  B-only goes negative.

## 4. R6 overlap / heat truth
- 71% of events sit in multi-event episodes; 27% enter with an active
  position; only 20 in-market hours carry 3 positions.
- Portfolio DD is NOT mainly an overlap problem; overlap worsens
  single-day/24h tails.
- Simple 1.0x gross cap at 70/30: block-MC p95 DD
  9.5% -> 6.26%, P(DD>=10%)
  3.6% -> 0.0% at
  ~5.4pp median-CAGR cost. At 50/50 the cap barely binds
  (14 events).

## 5. Component classification
See CR_RISK_BLOCK2_COMPONENT_CLASSIFICATION.csv. Headline: static family
allocation SUPPORTED; simple gross cap SUPPORTED; same-direction
SUPPORTED_BUT_NOT_INCREMENTAL; B-family SUPPORTED_NOT_REQUIRED; episode
budget REDUNDANT; combined H5 OPTIONAL; DD-adaptive / Kelly / hybrid /
deployment / MT5 DEFERRED.

## 6. Supported design region (NOT a production pick)
Allocation references 50/50 · 70/30 · 100/0 A (0/100 B diagnostic); heat H0
diagnostic + H1 gross (1.0x-3.0x) + H2/H3 secondary; base total-f band
0.25%-2.00% (3.00% outer stress). No best allocation / heat policy / size
selected.

## 7. Complexity pruning
LEVEL 0 H0 keep-diagnostic · LEVEL 1 H1 ADOPT · LEVEL 2 H2 PRUNE_REDUNDANT,
H3 KEEP_SECONDARY · LEVEL 3 H4 PRUNE_REDUNDANT · LEVEL 4 H5
OPTIONAL_ONLY_WITH_INCREMENTAL_GAIN · dynamic sizing DEFERRED.

## 8. Edge-retention warning
Edge retention is the BINDING constraint. At 50% retained edge the
portfolio is fragile (H0 50/50 f=1% exp CAGR ~+3%, p95 DD ~23%); at 25% it
is not viable. Risk controls shape losses; they do not create expectancy.

## 9. R7 necessity
**R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT.** 84.7% of in-DD loss is
single-position; static caps already solve the overlap tail; edge retention
dominates outcome; no unresolved state-dependent mechanism demonstrated.
r7_scientifically_justified = false · r7_authorized = false.

## 10. Architecture
ALPHA -> FAMILY QUALITY -> STATIC FAMILY ALLOCATION -> SIMPLE SIMULTANEOUS-
HEAT LIMIT -> PORTFOLIO (see CR_RISK_BLOCK2_PORTFOLIO_ARCHITECTURE.md).

## 11. Evidence status
See CR_RISK_BLOCK2_EVIDENCE_STATUS_MATRIX.csv (14 findings).

## 12. Decision
`cr_risk_block2_intermediate_seal_pass = true` · best_allocation_selected =
false · best_heat_policy_selected = false · best_size_selected = false ·
dd_adaptive/kelly/hybrid/deployment/mt5 = false · r7_authorized = false ·
human_review_required = true.

## 13. Next checkpoint
CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL (Case A: static structure
sufficient). R7 does NOT start until human review.
