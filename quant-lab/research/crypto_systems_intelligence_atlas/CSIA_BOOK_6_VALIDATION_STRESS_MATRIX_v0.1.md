# CSIA — BOOK 6 VALIDATION STRESS MATRIX v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phases 23–26 — roadmap Bloc 6D validation families, methodology
> sensitivity, cross-source parity, and the false-comparison corpus.
> **These are planned test obligations for a future implementation phase.** No
> test was run; this document defines what must later be proven.

---

## 1. The five validation families (6D.1–6D.5)

| Family | Question it must answer | Planned obligation |
|---|---|---|
| **6D.1 missingness** | Can missingness ever collapse into zero, false, or another state? | every missingness state reachable; no collapse; coverage floors enforced; `INSUFFICIENT_DATA` propagates per dimension |
| **6D.2 methodology sensitivity** | Does a reasonable methodology change flip a state? | every state re-derived under declared variants; flips surfaced, not hidden |
| **6D.3 historical sanity** | Do restated histories stay coherent? | supersession preserves originals; recomputation is recorded; no overwrite; reorg bounded |
| **6D.4 cross-source parity** | Can disagreeing sources be averaged into a smoother lie? | disagreement preserved per source; no silent averaging; Book 2 authority decides currency |
| **6D.5 false-comparison detection** | Does the system ever permit an invalid comparison? | every corpus row (below) must be refused or gated; native-source preservation enforced |

## 2. 6D.1 — missingness stress (rows are obligations, not results)

Every row must hold *mechanically* once implemented:

```text
M1  observed zero != missing            (ZERO_OBSERVED vs NOT_COLLECTED distinct)
M2  NOT_APPLICABLE != ZERO_OBSERVED     (no per-tx fee metric on a chain with no
                                         per-tx fee model is not "0 fees")
M3  NOT_SUPPORTED != SOURCE_UNAVAILABLE (chain does not expose it vs source down)
M4  UNKNOWN missingness is a first-class value (we may not know why it is missing)
M5  partial coverage never renders as complete
M6  missingness never inherits across dimensions or subjects
M7  missing denominator != ratio (never divide through missingness)
M8  a dimension with any non-observed input reads INSUFFICIENT_DATA, never 0
```

## 3. 6D.2 — methodology sensitivity (required stress examples)

For each row, the state is re-derived under the listed variants; a flip is a
**surfaced sensitivity**, not a failure to hide:

| Metric | Variants | Expected |
|---|---|---|
| active addresses | 1-day vs 7-day vs 30-day | direction may flip → sensitivity surfaced; cohort/method pinned in state |
| volume | gross vs net vs wash-filtered | magnitude changes; the *variant* is part of methodology identity |
| fees | paid fees vs protocol revenue | different constructs — never the same metric |
| TVL | native units vs common-value | native vs measured product; heterogeneous stays vector |
| developer | commits vs contributors vs releases | three metrics, not one "developer activity" |
| liquidity | reserves vs executable depth | reserves != depth; both may exist, separately named |
| security | stake value vs validator distribution vs cost-to-attack proxy | three metrics; cost-to-attack needs price → valuation methodology |

Rule: **if a state flips under reasonable methodologies, the sensitivity is
part of the output** (`sensitivity_note`), never suppressed.

## 4. 6D.3 — historical sanity

```text
H1 supersession preserves the original observation
H2 a methodology change is a new version + superseding observation, not a relabel
H3 a reorg revision is bounded to the reorged window
H4 derived metrics/states recompute and are themselves recorded as superseding
H5 current authority decays with Book 2 (a state's inputs going non-current
   makes the state recompute or INSUFFICIENT_DATA)
```

## 5. 6D.4 — cross-source parity

Sources considered as *independent observations of the same construct*:

```text
native chain/API        (E0/E1)
official protocol dashboard
independent indexer
third-party analytics   (E3)
```

Rules:

1. Disagreement **does not average automatically**. Averaging is itself a
   methodology and must be explicit, versioned, and justified.
2. Source-specific observations are **preserved separately** when
   methodologies differ; a cross-source panel is a first-class object, not a
   collapsed mean.
3. **Book 2 authority still applies** to which source is current; a source's
   claim going non-current removes it from *authority*, not from history.
4. A "consensus number" across sources is `NOT_AVAILABLE` unless a ratified
   reconciliation methodology exists.

## 6. 6D.5 — false-comparison corpus (the required stress set)

Each row: why naive comparison fails; the native metric; the required
normalization; whether comparison is possible; the resulting gate.

| # | Naive comparison | Why it fails | Native metric | Required normalization | Possible? | Result |
|---|---|---|---|---|---|---|
| 1 | Ethereum L1 tx vs rollup tx | different layers; a rollup batch is not an L1 user tx | per-layer exec counts | none valid across layers | no | NOT_COMPARABLE |
| 2 | Solana instructions vs EVM tx | instruction ≠ transaction (one action = many instructions) | family-native exec unit | none valid across units | no | NOT_COMPARABLE |
| 3 | active accounts vs active wallets | account identity vs wallet-cluster identity; sybil differs | both, separately named | none that preserves both | as separate metrics only | NOT_COMPARABLE as one metric |
| 4 | validator count across consensus models | PoS / BFT / permissioned constructs differ | per-model validator/security metrics | none valid | no | NOT_COMPARABLE |
| 5 | DEX volume vs aggregator-routed volume | routed volume includes the underlying DEX volume; overlap unknown | venue-native volume + routing attribution | share/routing methodology (explicit) | conditional | comparable only with explicit routing methodology |
| 6 | lending TVL vs supplied vs borrowed | different constructs; TVL often = deposits (a liability elsewhere) | Book 5 deposits/borrows/collateral (owner truth) | Book 5 same-unit discipline | yes, as distinct metrics | comparable as three, not one |
| 7 | staking TVL vs restaked claims | restaked claims may double-count underlying stake | Book 5 stake/claim records with lineage | lineage-aware dedup (Book 5) | conditional | Book 5 lineage must precede any total |
| 8 | perp notional vs collateral capital | notional is exposure domain, not principal (Book 5 ALG-5/9) | Book 5 notional vs capital, separate domains | none that mixes them | no | NOT_COMPARABLE (exposure ≠ principal) |
| 9 | stablecoin supply vs reserve value | supply (count) vs common-value (valuation) | supply (native) vs ValuationObservation | numeraire + price methodology (Book 6) | conditional | two products, never one |
| 10 | GitHub commits vs deployed developer activity | off-chain activity vs structural deployment | 6A.5 measures (source-tagged) | none that makes commits equal deployment | no | NOT_COMPARABLE |
| 11 | fees vs revenue | fees paid ≠ protocol revenue (stake/validators/LPs take cuts) | fees paid + revenue (separate) | revenue-split methodology | yes, as distinct | comparable as two |
| 12 | gross bridge flow vs net capital migration | gross includes round-trips; net ≠ gross − fees | gross flow + net migration (Book 5 flows) | wash/migration methodology | conditional | comparable only with net methodology |
| 13 | token holders vs protocol users | token ≠ protocol (Axiom 2) | holders (token metric) vs users (protocol metric) | none valid | no | NOT_COMPARABLE |
| 14 | nominal USD growth from price alone | price appreciation masquerades as native growth | native quantity (unit) + price separately | growth in *native* units; USD growth labeled as valuation-driven | yes, if labeled | comparable only as native growth + separate price effect |
| 15 | chain TPS with different failed-tx treatment | one chain counts attempts, another successes | successful vs attempted, per family | per-family success rule (pinned) | conditional | comparable only with matched success semantics |

Corpus rule: a comparison that is not possible **says so** (`NOT_COMPARABLE`)
and names why. A comparison that is conditional **names the methodology** that
would license it. Silence is forbidden; 6D.5 mechanically asserts that none of
these rows can produce a bare comparable number.

## 7. Anti-score firewall as a validation obligation

6D additionally carries the firewall tests (Phase 31): the system must be
incapable of emitting a composite investment score, a rank, a leaderboard, or
prescriptive state names — enforced structurally, not by review.

## 8. Validation verdict (planned, not executed)

```text
6D_FAMILIES = 5 (6D.1-6D.5) + firewall
FALSE_COMPARISON_CORPUS = 15 rows (7 NOT_COMPARABLE / 6 conditional / 2 as-distinct)
SENSITIVITY_RULE = flips are surfaced
PARITY_RULE = no silent averaging; Book 2 authority governs currency
6D_EXECUTION_STATUS = NOT RUN (implementation phase obligation)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

No row in this matrix reports a passing test, because no Book 6 code exists.
It is the contract a future implementation must satisfy to earn
`PASS_CSIA_B6_FUNDAMENTAL_MEASUREMENT_SEALED`.
