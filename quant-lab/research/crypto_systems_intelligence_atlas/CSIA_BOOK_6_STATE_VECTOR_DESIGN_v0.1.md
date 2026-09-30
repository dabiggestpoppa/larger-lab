# CSIA — BOOK 6 FUNDAMENTAL STATE VECTOR DESIGN v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phases 20–22 — Bloc 6C state dimensions, descriptive state
> language, state derivation.
> **NO COMPOSITE INVESTMENT RATING** (Constitution §5.3a; roadmap Bloc 6C).

---

## 1. The shape: a vector, never a score

A `FundamentalStateVector` is a **set of named descriptive dimensions**. It has
no total, no average, no weight vector, no rank. Anything that would reduce the
vector to a single number is out of scope by constitution, not by preference.

```text
FundamentalStateVector (PLANNED, not implemented)
  subject_ref
  as_of_valid_time
  dimensions: ordered set of StateDimension (below)
  status            COMPLETE | INCOMPLETE (any dimension INSUFFICIENT_DATA)
  construction_ref  the measurement set + methodologies it was derived from
```

```text
StateDimension (PLANNED)
  dimension_id       one of the planned dimensions
  state              descriptive state name (closed vocabulary, §3)
  measurement_refs   the observations this state was derived from
  methodology_ref    the versioned derivation rule
  valid_time
  observed_at
  missingness        per-dimension missingness (never inherited from a sibling)
  coverage
  epistemic_status   Book 2 currentness of the underlying authority, if
                     constitutionally permitted (see §5)
  sensitivity_note   if the state flips under a reasonable methodology variant
```

## 2. Candidate dimensions (not ratified blindly)

The roadmap's candidate list, each checked for a native input, a
threshold-free derivable state, and no hidden composite:

| Dimension | Native input (6A) | Threshold-free state possible? | Verdict |
|---|---|---|---|
| activity_state | chain/protocol activity metrics | yes (own-history direction) | KEEP (gated by 6A + D2-6 for usage readings) |
| capital_state | Book 5 same-unit stocks/flows (+valuation where methoded) | yes (own-history) | KEEP |
| liquidity_state | Book 5 reserves/components + depth methodology | yes (own-history) | KEEP |
| developer_state | 6A.5 measures | yes (own-history) | KEEP (source-limited, flagged) |
| integration_state | integration lifecycle (D2-6 ladder) | yes (own-history) | KEEP (used-state gated by D2-6) |
| dependency_state | Book 4 graph centrality (read-only) | yes (own-history) | KEEP (Book 4 metrics only) |
| token_utility_state | 6A.3 role-scoped measures | yes (own-history) | KEEP (role taxonomy required) |
| value_capture_state | fees/revenue + Book 5 claims | yes (own-history) | KEEP (fee≠revenue flagged) |
| economic_security_state | 6A.1 security measures | yes (own-history) | KEEP (cross-model NOT_COMPARABLE) |

Every dimension is **own-history relative**. None is a cross-subject band,
because cross-subject bands would require the thresholds D2-6 deferred (and a
weight-free band is still an adoption judgment).

## 3. Descriptive state language (closed vocabulary, tested)

**Allowed** (descriptive, threshold-free, own-history or data-absence):

```text
INCREASING / DECREASING / STABLE        (direction under one methodology)
VOLATILE / EXPANDING / CONTRACTING      (shape under one methodology)
HIGHER_THAN_OWN_HISTORY / LOWER_THAN_OWN_HISTORY
INSUFFICIENT_DATA                       (input non-observed, coverage below
                                         floor, methodology disagreement, or a
                                         required threshold unratified (D2-6))
NOT_APPLICABLE                          (dimension's metric does not exist for
                                         this subject/architecture)
```

**Prohibited** (prescriptive; a constitutional violation, not a naming choice —
§5.3a):

```text
ATTRACTIVE  STRONG_BUY  UNDERVALUED  OVERVALUED  TOP_TIER  HIGH_QUALITY
WINNER  BEST  BUY  SELL  HEALTHY  STRONG  ROBUST  PROMISING  INVESTABLE
```

Rule: a state name may not imply a fitness, quality, merit, or investment
judgment. If a proposed name cannot be defined without "how good is this," it
belongs to the prohibited list. `HEALTHY` is explicitly prohibited as a state
name while D2-6 defers health parameters (D2-6 reconciliation doc §3).

## 4. State derivation: every state is replayable

A state exists only if it can be rebuilt from stored inputs. Required for every
state:

```text
measurement_refs      the exact observations (with their methodology versions)
methodology_ref       the versioned derivation rule
threshold/rule version (if thresholds exist — none ratified yet; D2-6)
window                the derivation window, explicit
comparison basis      OWN_HISTORY (current default) or an explicit cohort
missingness behavior  what the state is when inputs are missing/partial
```

Prohibitions:

- **No state created from analyst prose.**
- **No hidden weights.** No dimension is a function of another; no dimension
  carries an implicit weight; nothing sums the vector.
- **No state without measurement refs.** A state with no resolvable
  `measurement_refs` is invalid at construction.
- **No threshold hiding.** If a rule uses a cutoff, the cutoff is a named,
  versioned field — not an inline literal, and not ratified here.

## 5. Epistemic status of a state

A state is **descriptive of measured inputs**, not a claim about the world
directly. Its epistemic status is inherited from its `measurement_refs`' Book 2
authority (current / contested / superseded) — Book 6 does not introduce a new
confidence vocabulary. If Book 2 authority for an input decays, the dimension
does not silently persist: the state recomputes or reads `INSUFFICIENT_DATA`
per its `missingness behavior` (the R4/R5 "registered-then ≠ authoritative-now"
discipline applies to measurements as they apply to Book 5 records).

## 6. Vector completeness

- `status = INCOMPLETE` if any dimension is `INSUFFICIENT_DATA`,
  `NOT_APPLICABLE`, or below its coverage floor. An incomplete vector is still
  published (it is honest), but it never presents partial dimensions as
  complete.
- There is no "completeness score" and no "how complete is this" number; the
  flag is the surface.
- `NOT_APPLICABLE` on a dimension (e.g. economic security on a non-consensus
  ledger) is data, not a defect.

## 7. Anti-score firewall (structural, pre-ratification)

The vector design contains no field that can host a composite:

- no `total`, `score`, `rating`, `grade`, `rank`, `index_to_quality`;
- no ordering of subjects by vector;
- no cross-subject percentile (rejected in the comparability doc);
- no state dimension that is itself a weighted blend.

Enforcement belongs to 6D validation (firewall test family) so it is
mechanically testable, not just declared.

## 8. State-vector verdict

```text
STATE_SHAPE = VECTOR (no total, no score, no weight, no rank)
DIMENSIONS = 9 candidates, all own-history-relative
VOCABULARY = CLOSED (descriptive allowed list; prescriptive list prohibited)
DERIVATION = REPLAYABLE (refs + methodology + window + comparison basis)
THRESHOLDS = NONE RATIFIED (D2-6); states needing one read INSUFFICIENT_DATA
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```
