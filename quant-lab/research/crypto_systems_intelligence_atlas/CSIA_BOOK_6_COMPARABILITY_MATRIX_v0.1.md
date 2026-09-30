# CSIA — BOOK 6 COMPARABILITY MATRIX v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phases 14–17 — Bloc 6B comparable dimensions, native-before-
> normalized binding, normalization types, cohort doctrine.
> **Nothing here is a normalized value.** This document decides which
> normalizations are *legible*, and which comparisons stay `NOT_COMPARABLE`.

---

## 1. What 6B is for

6A preserves native truth. 6B is the **comparison layer**: it declares which
dimensions may be compared, across which cohorts, under which normalizations,
and — equally important — **which comparisons are structurally invalid**. A
comparison layer that only permits comparisons is a laundering mechanism for
false equivalence.

Rule of the matrix: for every candidate dimension, all seven questions are
answered. An unanswered question makes the dimension `DEFER`, never `KEEP`.

## 2. Candidate comparable dimensions (roadmap list, stressed)

Nine roadmap candidates: activity; capital; liquidity; developer growth;
integration growth; dependency centrality; token utility; value capture;
economic security. Each is decomposed into native measurements feeding it.

### 2.1 The matrix

Columns: native inputs (Book-owned) | architecture support | comparability
destroyers | required denominator | allowed transformation | missingness
propagation | methodology requirement.

| Dimension | Native inputs (owner) | Arch support | Comparability destroyers | Required denominator | Allowed transformation | Missingness propagation | Methodology requirement |
|---|---|---|---|---|---|---|---|
| **Activity** | chain execs/tx (6A.1), protocol interactions (6A.2), active accounts under family identity rule | per family; NOT all families have an "account" | tx unit mismatch (Solana instruction vs EVM tx); sybil inflation; bot traffic; success-rate semantics; rollup vs L1 layering | explicit: per-block? per-user? share of what population? | PER_TIME, PER_USER, SHARE_OF_TOTAL (within cohort), GROWTH_RATE | if active-account identity is NOT_SUPPORTED → dimension = `INSUFFICIENT_DATA`; never zero | identity rule (user/address/actor) + wash/sybil filter + window + success rule, all versioned |
| **Capital** | Book 5 same-unit stocks/flows; valuation products (6A.4) | protocol- and venue-specific; heterogeneous vectors stay vectors | unit heterogeneity (ETH+USDC); venue type (AMM/lending/restaking/perp) not additive; bridged vs native; stale price | for ratios: supplied vs borrowed vs collateral (explicit) | PER_CAPITAL, SHARE_OF_TOTAL (same-unit only), PER_TIME (flow), common-value ONLY with numeraire+price | if a component is unvalued → `PARTIAL_COVERAGE`; if a whole unit class is unmeasured → `INSUFFICIENT_DATA` | Book 5 attribution + same-unit collapse methodology; valuation methodology per ValuationObservation |
| **Liquidity** | Book 5 reserves/components; executable-depth (6A.2/6A.4) | venue-specific | reserves ≠ executable depth; concentrated-range vs full-range; lock/unlock; single-sided | shares of pool (Book 5 fractions) | SHARE_OF_TOTAL, GROWTH_RATE, PER_CAPITAL | missing depth curve → `PARTIAL_COVERAGE`, reserves-only is not depth | depth methodology (tick/liquidity model) + range semantics + lock rules versioned |
| **Developer growth** | commits/contributors/releases (6A.5) | off-chain, not chain-gated | monorepo inflation; bot commits; contributor identity (person vs org); repo ≠ deployed code | contributors per repo? per window (explicit) | PER_TIME, GROWTH_RATE, PER_REPO | GitHub-unavailable → `SOURCE_UNAVAILABLE`, NOT zero | contributor identity rule + repo-scope + window versioned |
| **Integration growth** | Book 5/6 integration counts; deployed apps (6A.5) | chain-gated; dependent on Book 1/4 truth | announced vs deployed vs used (D2-6!); a config change vs a real integration; test deployments | per window (explicit) | COUNT, GROWTH_RATE, SHARE_OF_TOTAL (cohort) | announced-only evidence → the *dimension* stays descriptive; usage = `INSUFFICIENT_DATA` until D2-6 thresholds | deployed/used evidence rule versioned (D2-6-sensitive) |
| **Dependency centrality** | Book 4 dependency graph (4 owns truth) | Book 4-gated | centrality is graph-metric-dependent (degree≠betweenness≠eigen); directionality; shared-security clusters; cycle collapse | normalize by graph size | normalized graph centrality (degree/betweenness), SHARE_OF_TOTAL | Book 4 incompleteness → coverage flag, never invented edges | graph-metric choice + edge-family scope versioned (Book 4 read-only) |
| **Token utility** | token supply/staking/locked/participation (6A.3) | token-gated | gas-token vs governance vs collateral roles differ; a token ≠ its chain (Axiom 2) | active users of the token's role (explicit) | SHARE_OF_TOTAL (role-specific), PER_USER, GROWTH_RATE | role usage not measurable → `INSUFFICIENT_DATA` | role taxonomy + usage identity rule versioned |
| **Value capture** | fees/revenue (6A.2/6A.3), BuybackClaim, flow claims | protocol-gated | fees ≠ revenue; gross ≠ net; wash-trading; MEV share; value to whom (protocol vs token vs validators) | per what (users? tx? stakers?) | SHARE_OF_TOTAL (revenue split), PER_USER, GROWTH_RATE | revenue not separable from fees → `PARTIAL_COVERAGE`/methodology-sensitivity surfaced | fee-vs-revenue definition + wash filter + split rules versioned |
| **Economic security** | stake/validator/security-budget (6A.1) | consensus-gated | PoS vs BFT vs PoW incomparable; validator concentration vs stake concentration; cost-to-attack proxy needs price | validators vs stake (explicit) | SHARE_OF_TOTAL (stake share), Gini/concentration distribution | non-slashing PoS vs PoW → `NOT_COMPARABLE` across families | security-model family + counting unit (entity/key/seat) versioned |

### 2.2 Matrix verdicts

- Dimensions that are structurally comparable only within a declared cohort:
  activity, capital, liquidity, developer growth, token utility, value capture.
- Dimensions structurally `NOT_COMPARABLE` across architecture families:
  economic security (consensus models), and throughput-style activity across
  execution-layer vs rollup vs instruction models.
- dependency centrality is comparable only under a named Book 4 graph metric.
- integration growth is D2-6-sensitive: usage-bearing comparison stays
  `INSUFFICIENT_DATA` until the deferred parameters are ratified.

## 3. Native-before-normalized (Axiom 1, binding)

**Rule:** no normalized comparison without a preserved native measurement.

Mechanically: every `MeasurementObservation` with `native_or_normalized =
NORMALIZED` MUST carry `source_claim_refs` and a resolvable chain to the native
observations it derives from. A normalized metric whose native source is missing
is invalid at construction. Validation family 6D.5 (false-comparison detection)
enforces this at test time.

Worked non-comparabilities (from the corpus; detailed in the validation doc):

```text
Solana TPS           vs  Ethereum transactions   -> NOT_COMPARABLE (unit differs)
                       vs  rollup batches          -> NOT_COMPARABLE (layer differs)
Validator count      PoS vs BFT federation vs permissioned ledger -> NOT_COMPARABLE
                       (security model differs; count is not the same construct)
"TVL" on AMM vs lending vs restaking vs perps -> NOT_COMPARABLE as one total
                       (semantically different capital constructs; Book 5 forbids the merge)
```

Each false comparison names the required normalization, or states that
comparison is impossible, or remains `NOT_COMPARABLE`. Silence is not an option.

## 4. Normalization types (candidates, stressed, not all ratified)

| Normalization | Definition | Structural validity notes |
|---|---|---|
| PER_TIME | value ÷ time | valid for rates; invalid for stocks unless the rate is the target |
| PER_USER | value ÷ user count | valid when the user identity rule is declared and sybil-bounded; invalid for chains with no user concept (→ NOT_APPLICABLE) |
| PER_TRANSACTION | value ÷ tx | valid when the tx unit is family-native and stable; cross-family invalid |
| PER_CAPITAL | value ÷ capital (Book 5) | valid within a unit/cohort; invalid across heterogeneous units without valuation |
| PER_VALIDATOR | value ÷ validator count | valid within a consensus model; invalid across models |
| PER_BLOCK | value ÷ block | family-gated; cadence varies |
| PER_UNIT_SECURITY | value ÷ security stock | cross-model sensitivity high; often NOT_COMPARABLE |
| SHARE_OF_TOTAL | value ÷ cohort total | valid only with an explicit cohort; "total" must never be a silent global |
| GROWTH_RATE | Δvalue ÷ prior value | valid; requires the prior window's method to match; a price-only Δ is not growth |
| INDEX_TO_BASE | rebased series | legible as a descriptive index, never as an investment score; must carry base + cohort |
| PERCENTILE_WITHIN_COHORT | rank within cohort | **REJECT for now** — percentile is an ordering; it is a ranking surface in disguise and conflicts with §5.3a. Revisit only if reframed as a distribution, not a rank. |

**Ratified-for-planning:** PER_TIME, PER_USER, PER_TRANSACTION, PER_CAPITAL,
PER_VALIDATOR, PER_BLOCK, SHARE_OF_TOTAL (cohort-explicit), GROWTH_RATE,
INDEX_TO_BASE, PER_UNIT_SECURITY (sensitivity-flagged). **Rejected:**
PERCENTILE_WITHIN_COHORT (ranking surface). Some normalizations are
structurally invalid for specific metric families (per the notes above) —
validity is per (metric × cohort), never global.

Whether normalization is a separate contract class or a `MetricDefinition`
attribute is an open operator decision with materially different consequences →
**D6M-2**.

## 5. Cohort doctrine

Comparison requires a cohort. A cohort is an **explicit, versioned** set:

```text
cohort_id + version
dimensions (a subset of): architecture_family, economic_function,
  protocol_role, chain_role, maturity_band, deployment_environment,
  security_model
```

Rules:

1. **"All chains" is not an automatic cohort.** A cross-family cohort is only
   valid where the dimension's `comparability_class` permits it, and then with
   per-family native measurements preserved.
2. Cohort identity is versioned; a cohort change does not silently rewrite prior
   comparisons (same supersession discipline as measurements).
3. A subject outside the declared cohort is `NOT_IN_COHORT`, never silently
   included or excluded.
4. `SHARE_OF_TOTAL` is cohort-relative; the cohort is part of the methodology
   identity.

## 6. Comparability verdicts

```text
6B_CANDIDATE_DIMENSIONS = 9 (matrix answered for all)
STRUCTURALLY_NOT_COMPARABLE_ACROSS_FAMILIES = activity(throughput-style),
  economic security, "TVL" totals
COHORT_REQUIRED = TRUE (no global "all chains" auto-cohort)
NORMALIZED_WITHOUT_NATIVE = IMPOSSIBLE (Axiom 1, enforced in 6D.5)
PERCENTILE_NORMALIZATION = REJECTED (ranking surface)
OPEN = D6M-2 (normalization contract shape)
```

Nothing is normalized yet: 6A native measurement and its preservation precede
every entry in this matrix, and 6D will stress each row against
missingness, methodology sensitivity, and false-comparison detection.
