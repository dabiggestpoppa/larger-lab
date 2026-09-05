# LOWER-FIELD-5 DECISION

**Decision:** `PASS_LOWER_FIELD_5`

## Stage A: PASS

PIT asset-date substrate integrity verified:
- 4.4M rows, 7,658 assets, 2,195 dates
- All 10 integrity checks pass (no future rows in features, no band truncation inside windows, rank sign verified, LF2 parity, no duplicates, missingness documented, causal windows, sane scaling, finite values, causal listing age)

## Stage B: PASS

All five peer families VALID with 78-84% event coverage:
- Rank peers: VALID (deterministic, reproducible)
- Behavioral peers: VALID (18.4% false loner rate — primary finding)
- Correlation peers: VALID (previously DATA_BLOCKED; now causal trailing 60D/120D)
- State peers: VALID (same-date cohorts)
- Hybrid peers: VALID (18.6% false loner rate)

### Key Results

1. **18.4% of rank-only loners are false loners** under behavioral peer definitions. This materially changes the interpretation of "lonely dump" events — roughly 1 in 5 isolated-down events is NOT isolated relative to its historically relevant peers.

2. **1σ recovery gate is a conditional stabilization marker**: Events achieving 1σ by 1D have 58-73% full repair probability; events failing 1σ by 7D show 0% full repair.

3. **Price and rank are separate clocks**: PRICE_UP + RANK_DOWN is a stable health state, not a contradiction.

4. **All 22 analyses** now use genuine peer-relative measurements, not rank-only placeholders.

### Remaining Limitations

- Next-window out-of-sample similarity validation not yet computed (requires forward-looking peer comparison)
- Membership turnover / Jaccard persistence not estimated
- Sequence atlas requires purged FDR validation
- Trade-level validation not attempted (no strategy work)

### What Changed from Previous LF5

- Correlation peers upgraded from DATA_BLOCKED to VALID
- True/false loner audit now computed (was DATA_BLOCKED)
- All downstream outputs now use true peers
- 1σ semantics repaired (recovery from shock anchor)
- Price vs rank health clocks computed with future PIT ranks

## Governance

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`

No strategy. No PnL. No trading signal. No entry/exit rules. No position sizing. No leverage. No deployment. Statistical existence does not imply executable alpha.
