# CR-BLOCK4-D0.1 -- Causal known_time Audit

## Finding
The D0 output used `known_time = decision.decision_timestamp`. But the final
economic exposure ALSO requires the BoundAccountSnapshot (equity + currency
observed at `snapshot.observed_at`). If the snapshot observation is later
than the capital decision, the economic target could not have been known at
the earlier decision time.

## Repair (confirmed by source semantics)
    known_time = max(event.entry_known_timestamp,
                     decision.decision_timestamp,
                     snapshot.observed_at)

computed on timezone-aware parsed timestamps. NEVER datetime.now().

## Timestamp handling
- required: event.entry_known_timestamp, decision.decision_timestamp,
  snapshot.observed_at — empty / unparseable -> InvalidTimestampError
- the sealed ledger timestamps are already timezone-aware ISO 8601
  ("2023-07-10 13:00:00+00:00"); naive hand-built timestamps are normalized
  to UTC (documented sealed semantics: naive wall-clock == UTC), so naive and
  aware instants compare zone-safely
- output format: ISO 8601 with explicit offset (datetime.isoformat)

## Rejected events
Design choice (documented, per the frozen R1.1 handoff contract): **full
handoff validation** — a rejected event still requires a valid binding +
account snapshot, because the output is a FULLY BOUND translation record
carrying account identity / snapshot truth, and the R1.1
CapitalTranslationRequest schema includes all four components for every
request. The rejected record carries zero exposure and its causal known_time
(max of the three timestamps); it never reconsiders H1.
