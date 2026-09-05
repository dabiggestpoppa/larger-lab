# TEST-COUNT RECONCILIATION

## MECH-2 statistical tests (`19_TEST_COUNT_RECONCILIATION.csv`)

| workstream | tests |
|---|---|
| A — common-factor band lead/lag | 126 (3 metrics × 21 band pairs × 2 variants) |
| B — conditional lead/lag | 708 (pair × state × lag cells; 10 states) |
| E — chain-flow hierarchy | 258 (12 chains × 6 links × 4 lags, filtered n≥120) |
| D — leader-first sector propagation | 6,783 episodes (each one corr test per lag) |

Additional tested cells (not hypothesis tests per se):
- C — rank-migration precursor events: 37,485 event-date × band × window rows
  (each event is compared against same-band controls; statistics are descriptive).
- J — transfer entropy: 3 pairs × 200 surrogates (fixed seed).
- G — morphism catalog: 201 motifs (frequency classification, no p-values).
- H — hierarchy decomposition: 169 clusters (variance decomposition, no p-values).
- F — propagation failures: 8 pattern-outcome rows (4 patterns × 3 windows, of which
  1 pattern never fired — LOWER_RANK_ACCELERATION: 0 pattern days).

**Total statistical hypothesis tests: 126 + 708 + 258 + 6,783 = 7,875.**
Every tested cell is retained in artifacts (05, 05b, 08 — no results dropped).

## Multiple-testing control

- A: BH-FDR over 126 cells (123 significant at q<0.05 — contemporaneous, see 04).
- B: BH-FDR per (metric × band-pair) family over the 10 state conditions.
- E: BH-FDR over all 258 chain cells (77 survive q<0.05).
- D: per-episode corr tests reported descriptively; not FDR-corrected (episodes are
  the sampling unit; significance is not claimed from them).
- All permutation tests use fixed seeds; bootstrap block structure is deterministic
  (seed `20260826` family).

## Integrity test accounting (this checkpoint)

`tests/test_alt_mech_2.py`: **31/31 passing**, covering: input hash match, PIT row
counts, V1-field non-consumption, per-chain AVAILABLE_NEXT_DAY shifting,
no-future-column structural checks on every artifact, FDR reproducibility,
deterministic seeds, transfer-entropy robustness to all-NaN inputs, and absence of
PnL / trade / exit / weight / alpha columns.

## Parent-suite reconciliation (for continuity with MECH-1)

| suite | tests | scope |
|---|---|---|
| DATA-0 | 21 | raw ingestion truth |
| DATA-0.1 | 20 | first enrichment layer |
| DATA-1 | 50 | PIT universe + V2 features |
| DATA-1.1 | 19 | benchmark truth seal + capital-flow enrichment |
| **Total** | **110** | canonical full stack |

The parent MECH-1 checkpoint reported 69/69 (DATA-1 + DATA-1.1) in the commit
message and 91/91 (DATA-0 + DATA-0.1 + DATA-1) in the decision doc; both are
consistent slices of the same 110-test stack. MECH-1's own suite was 17/17; MECH-2
adds 31. No scientific results were altered during reconciliation.
