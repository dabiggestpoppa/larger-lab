# CSIA — BOOK 6 METRIC CANDIDATE MATRIX v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phase 27 — the governed candidate set. Every metric family named
> in the roadmap and in the Book 6 sub-documents is classified here with
> KEEP / REVISE / DEFER / REJECT.
> **A KEEP means "may be defined in a future implementation"** — not that a
> value exists today.

Column key — Native domain · Type · Unit · Window · Num · Den · Method
(own method ref required) · Sources · Book dep · Comparability class ·
Missingness · Normalization eligible · State-vector eligible · Status.

---

## 1. Chain-native metrics (6A.1)

| Metric | Native domain | Type | Unit | Window | Num/Den | Method | Sources | Book dep | Comparability | Missingness | Norm eligible | State eligible | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| executed transactions | chain | RATE | tx/family-unit | block/epoch or daily | n/a | family tx-unit + success rule | native chain | B3, B2 | per-family only | NOT_SUPPORTED if no tx notion | PER_TIME, PER_BLOCK | activity | **KEEP** |
| successful executions | chain | RATE | exec | per family | n/a | success semantics pinned | native chain | B3, B2 | per-family | as above | as above | activity | **KEEP** |
| active accounts | chain | COUNT | accounts | rolling declared | num only | identity rule (account/wallet/entity) + sybil filter | native chain | B1, B2, B3 | cohort-pinned | NOT_SUPPORTED if no account notion | PER_USER, SHARE_OF_TOTAL | activity (D2-6-gated) | **REVISE** (identity rule must be ratified first) |
| fees paid | chain | STOCK/FLOW | family fee unit | per block/day | n/a | fee model per family | native chain | B3, B2 | per-family | NOT_APPLICABLE if no fee model | PER_TIME, PER_TX | activity/value | **KEEP** |
| issuance | chain/token | FLOW | native amount | per day/month | n/a | native issuance events | native chain | B3, B5, B2 | per family | NOT_APPLICABLE | PER_TIME, GROWTH | token_utility | **KEEP** |
| burn | chain/token | FLOW | native amount | per day/month | n/a | native burn events | native chain | B3, B5, B2 | per family | NOT_APPLICABLE | as above | token_utility | **KEEP** |
| validator/producer count | chain | STOCK | entities/keys/seats | instant + history | n/a | counting unit pinned | native chain | B3, B2 | **NOT_COMPARABLE across consensus models** | NOT_SUPPORTED if no such role | SHARE_OF_TOTAL (within model) | economic_security | **KEEP** (model-scoped) |
| stake bonded | chain | STOCK | native stake | instant | n/a | native stake definition | native chain | B3, B5, B2 | model-scoped | NOT_APPLICABLE if PoW | SHARE_OF_TOTAL | economic_security | **KEEP** |
| security budget | chain | FLOW | native amount | per day | issuance − burn-down | method pinned | native chain | B3, B2 | model-scoped | NOT_APPLICABLE if PoW | PER_TIME | economic_security | **KEEP** |
| block/slot production rate | chain | RATE | blocks/slots/epoch | per time | n/a | cadence per family | native chain | B3, B2 | per-family | n/a | PER_TIME | activity | **KEEP** |
| throughput | chain | RATE | work/time | per time | n/a | family work-unit | native chain | B3, B2 | **layer-gated (NOT_COMPARABLE L1 vs rollup)** | per-family | PER_TIME | activity | **KEEP** (layer-pinned) |
| finality | chain | STATE-like | n/a | instant | n/a | family finality notion | native chain | B3 | descriptive, not a rate | n/a | none | economic_security | **KEEP** (descriptive) |
| DA usage | chain | STOCK/RATE | family DA unit | per time | n/a | family DA model | native chain | B3, B2 | modular-gated | NOT_SUPPORTED if none | PER_TIME | activity | **KEEP** |
| state growth | chain | STOCK | bytes/units | per time | n/a | family state model | native chain | B3 | per-family | per-family | GROWTH_RATE | activity | **KEEP** |
| MEV | chain | FLOW | family MEV unit | per day | n/a | MEV surface per family | native chain | B3, B7 | per-family | **NOT_SUPPORTED if no MEV surface** | PER_TIME | value_capture | **KEEP** (surface-gated) |

## 2. Protocol-native metrics (6A.2)

| Metric | Native domain | Type | Unit | Window | Num/Den | Method | Sources | Book dep | Comparability | Missingness | Norm eligible | State | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| protocol users | protocol | COUNT | users | rolling | n/a | user identity + sybil rule | protocol/native | B1, B2, B3 | cohort-pinned | NOT_SUPPORTED if custodial-only | PER_USER | activity (D2-6-gated) | **DEFER** (identity rule research pending) |
| interactions/tx | protocol | RATE | interactions | per day | n/a | per-model interaction unit | native protocol | B2, B3 | **per economic model** | per model | PER_TIME, PER_USER | activity | **KEEP** |
| deposits | protocol | STOCK | native amount | instant | n/a | Book 5 records | native + Book 5 | **B5** | same-unit | Book 5 missingness | PER_CAPITAL, PER_USER | capital | **KEEP** (measures over B5) |
| borrows | protocol | STOCK | native amount | instant | n/a | Book 5 records | Book 5 | **B5** | same-unit | Book 5 | PER_CAPITAL | capital | **KEEP** |
| swaps | protocol | FLOW | native amount | per day | n/a | venue-native swap definition | native | B3, B5 | **per venue model** | per model | PER_TIME, SHARE_OF_TOTAL | activity | **KEEP** |
| volume | protocol | FLOW | native amount | per day | n/a | gross/net + wash filter (explicit) | native | B2, B3, B5 | conditional (routing methodology) | per venue | PER_TIME, GROWTH | activity | **REVISE** (gross vs net must be a definition choice) |
| fees | protocol | FLOW | native amount | per day | n/a | paid-fee definition | native | B2, B3 | per model | per model | PER_TIME, PER_USER | value_capture | **KEEP** |
| revenue | protocol | FLOW | native amount | per day | n/a | revenue split methodology (post-cut) | native | B2, B3, B5 | conditional | per model | PER_TIME, SHARE_OF_TOTAL | value_capture | **REVISE** (split method must be ratified) |
| liquidity (reserves) | protocol | STOCK | native amount | instant | n/a | Book 5 reserves | Book 5 | **B5** | per venue model | Book 5 | SHARE_OF_TOTAL | liquidity | **KEEP** |
| executable depth | protocol | STOCK | native amount | instant | n/a | tick/liquidity model + range rules | native | B3, B5 | conditional | **PARTIAL_COVERAGE** likely | SHARE_OF_TOTAL | liquidity | **DEFER** (depth methodology not ratified) |
| utilization | protocol | RATIO | ratio | per window | borrowed / supplied | denominator = supplied (not deposits) | Book 5 | **B5**, B2 | per model | denominator states | none (already a ratio) | capital | **KEEP** |
| collateral | protocol | STOCK | native amount | instant | n/a | Book 5 collateral records | Book 5 | **B5** | same-unit | Book 5 | PER_CAPITAL, SHARE | capital | **KEEP** |
| liquidations | protocol | FLOW | native amount | per day | n/a | Book 5 liquidation events | Book 5 + B7 | **B5**, B7 | per model | per model | PER_TIME | capital | **KEEP** |
| integration count | protocol/chain | COUNT | integrations | per window | n/a | deployed-vs-used evidence (D2-6) | Book 1/4/5 truth | B1, B4, B5 | cohort-pinned | NOT_COLLECTED vs 0 | GROWTH_RATE, SHARE | integration | **KEEP** (used-gated by D2-6) |

## 3. Token-native metrics (6A.3)

| Metric | Native domain | Type | Unit | Window | Num/Den | Method | Sources | Book dep | Comparability | Missingness | Norm | State | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| token supply | token | STOCK | native token units | instant | n/a | native supply definition | native chain | B1, B5, B3 | per token | NOT_APPLICABLE | GROWTH_RATE, SHARE | token_utility | **KEEP** |
| token issuance/burn | token | FLOW | native units | per day | n/a | native ops | native chain | B3, B5 | per token | per model | PER_TIME | token_utility | **KEEP** |
| staked amount | token | STOCK | native units | instant | n/a | staking definition per model | native | B3, B5 | per model | per model | SHARE_OF_TOTAL | token_utility | **KEEP** |
| locked amount | token | STOCK | native units | instant | n/a | lock definition | native + Book 5 | B3, B5 | per model | per model | SHARE_OF_TOTAL | token_utility | **KEEP** |
| circulating realizations | token | STOCK | native units (bridged/native split) | instant | n/a | Book 5 realization records | Book 5 | **B5**, B1 | per token | Book 5 | SHARE_OF_TOTAL | token_utility | **KEEP** |
| utility participation | token | COUNT/RATE | users | rolling | n/a | role-specific identity | native | B1, B2, B3 | role-scoped | NOT_SUPPORTED if no role | PER_USER, GROWTH | token_utility | **REVISE** (role taxonomy required) |
| governance participation | token | RATE | voters/proposals | per window | num/den | governance model per protocol | native | B2, B3 | per model | per model | PER_TIME, PER_USER | token_utility | **KEEP** |
| token holders | token | COUNT | holders | instant | n/a | holder identity (sybil-sensitive) | native | B1, B2 | cohort-pinned | sybil | SHARE_OF_TOTAL | **none directly** | **REJECT as "users" proxy** (corpus #13); keep only as a distinct holders metric |
| "protocol health score" | — | — | — | — | — | — | — | — | — | — | — | — | **REJECT** (composite score) |
| "ecosystem ranking" | — | — | — | — | — | — | — | — | — | — | — | **REJECT** (prescriptive) |

## 4. Capital metrics (6A.4) — Book 5 consumers

| Metric | Native domain | Type | Unit | Window | Num/Den | Method | Book dep | Comparability | Missingness | Norm | State | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| same-unit capital stock | capital | STOCK | native unit | instant | n/a | Book 5 same-unit aggregate | **B5** | same-unit only | Book 5 | GROWTH_RATE | capital | **KEEP** |
| capital flow | capital | FLOW | native unit | per day | n/a | Book 5 flow ledger | **B5** | same-unit | Book 5 | PER_TIME | capital | **KEEP** |
| capital concentration | capital | DISTRIBUTION | share/Gini | instant | n/a | component set + attribution | **B5** | per venue model | coverage | SHARE_OF_TOTAL | capital | **KEEP** |
| capital-route activity | capital | FLOW | native unit | per day | n/a | Book 5 flows | **B5** | same-unit | Book 5 | PER_TIME | capital | **KEEP** |
| credit ratio | capital | RATIO | ratio | instant | obligations / assets | Book 5 obligations | **B5** | per model | denominator states | none | capital | **KEEP** |
| staking ratio | capital | RATIO | ratio | instant | staked / supply | Book 5 stake records | **B5**, B3 | per model | per model | none | capital | **KEEP** |
| common-value capital total | capital | SCALAR-QUANTITY | numeraire | instant | n/a | **numeraire + price + coverage** (ValuationObservation) | **B5** + Book 6 valuation | heterogeneous vector → total only under method | coverage + price staleness | none (already valued) | capital | **KEEP** (strictly Book 6, explicit numeraire) |
| "TVL" as one number | — | — | — | — | — | merges AMM/lending/restaking/perp | — | **NOT_COMPARABLE** | — | — | — | **REJECT as one metric** (corpus #6/7); keep per-construct metrics |

## 5. Developer metrics (6A.5)

| Metric | Native domain | Type | Unit | Window | Num/Den | Method | Sources | Book dep | Comparability | Missingness | Norm | State | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| repositories | developer | COUNT | repos | instant | n/a | repo identity | GitHub (E3) | B1, B2 | off-chain cohort | SOURCE_UNAVAILABLE | GROWTH_RATE | developer | **KEEP** (source-tagged) |
| contributors | developer | COUNT | contributors | per window | n/a | person vs org identity | GitHub (E3) | B1, B2 | cohort-pinned | identity ambiguity | GROWTH_RATE, PER_REPO | developer | **REVISE** (identity rule) |
| commits | developer | FLOW | commits | per week | n/a | repo scope + bot filter | GitHub (E3) | B1, B2 | cohort-pinned | bot inflation | PER_TIME | developer | **KEEP** |
| releases | developer | FLOW | releases | per window | n/a | release definition | GitHub (E3) | B1, B2 | cohort-pinned | per model | PER_TIME | developer | **KEEP** |
| deployed apps | developer/chain | COUNT | deployments | per window | n/a | structural deployment evidence | native chains | B1, B3, B4 | cohort-pinned | NOT_COLLECTED | GROWTH_RATE | developer | **KEEP** (closer to structural than GitHub) |
| SDK/package usage | developer | RATE | installs/calls | per window | n/a | package identity | registries (E3) | B1, B2 | cohort-pinned | SOURCE_UNAVAILABLE | PER_TIME | developer | **DEFER** (source quality) |
| "developer health" | — | — | — | — | — | composite/judgment | — | — | — | — | — | **REJECT** (health judgment, D2-6) |

## 6. Cross-cutting verdict

```text
KEEP    = the metric is definable in a future implementation as specified
REVISE  = definable only after a sub-definition is ratified (identity rule,
          gross/net, revenue split, role taxonomy)
DEFER   = blocked on empirical research or a methodology decision
          (usage identity, depth methodology, package-source quality, D2-6)
REJECT  = constitutionally invalid (composite score, ranking, single "TVL",
          holders-as-users)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE (no metric is implemented)
```

No threshold, weight, or band appears anywhere in this matrix. Every DEFER is
paired with the specific decision or research that would unblock it.
