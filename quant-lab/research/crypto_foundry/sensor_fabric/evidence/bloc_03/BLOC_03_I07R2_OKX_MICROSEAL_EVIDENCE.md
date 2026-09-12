# SENSOR-B3-I07R2 — OKX Window-Overlap Truth Microseal Evidence

**Review verdict:** `HOLD_PASS_SENSOR_B3_I07R1_OKX_SEALED_PENDING_I07R2_MICROSEAL`
(operator accepted all I07R1 repairs; one residual quality-classification
defect remained).  **Target verdict if earned:** `PASS_SENSOR_B3_I07R2_OKX_SEALED`.

**Scope:** microseal only.  OKX architecture, I14 set, roles, symbol scope,
access, schema seal, timestamps, raw preservation, typed errors and the
completion/resume invariants are all UNCHANGED.  This is still NOT a global
Bloc 3 pass.

## Starting SHA

`0371a29708be0d59b3af093b5ac06d8aea0f7187` (branch
`agent/crypto-sensor-fabric-build`, clean tree, lineage verified:
`63154bd7 -> ffbdfdfd -> 820feca4 -> 0371a297`).

## Residual defect

The I07R1 historical-page classification used

    actual_first < request.end_time AND actual_last >= request.start_time

where `actual_first_timestamp` = timestamp of `rows[0]` and
`actual_last_timestamp` = timestamp of `rows[-1]`.  Those are first/last
RETURNED rows, NOT chronological min/max.  OKX trade history can be returned in
descending time order (rows[0] = newest), so a page containing a valid
in-window row could be misclassified `GAP_DETECTED` instead of
`PARTIAL_INTERVAL` — violating the I07R1 evidence statement "rows overlapping
the requested window -> PARTIAL_INTERVAL; rows entirely outside it ->
GAP_DETECTED."

## Exact repaired algorithm (I07R2A)

For historical MECHANICAL_FUNDING and MECHANICAL_TRADE:

    row_datetimes = [convenience datetime of each schema-validated row]
    if any(row_datetime is None):
        raise ProviderSemanticError        # invariant violation — fail closed,
                                           # never silently classify as GAP

    has_in_window = any(request.start_time <= dt < request.end_time
                        for dt in row_datetimes)

    if rows and has_in_window:  quality_flags += PARTIAL_INTERVAL
    elif rows:                  quality_flags += GAP_DETECTED

Historical acquisition remains `is_complete=False`, `next_resume_token=None`
(continuation direction still unresolved).  Overlap never implies completeness.
`PARTIAL_INTERVAL` and `GAP_DETECTED` are mutually exclusive by construction.

## Why row ordering cannot define overlap

`actual_first/actual_last` describe returned PROVIDER ROW ORDER (a valid,
evidence-preserving meaning for the FetchBatch convenience boundaries).  They
are not chronological bounds unless the provider guarantees ascending order —
which committed evidence does not for OKX history-trades.  Classifying from
the evidence itself (each validated row timestamp) makes the decision invariant
to provider ordering behavior.  `actual_first/actual_last` are deliberately
NOT redefined as min/max (the common FetchBatch contract does not define them
as chronological boundaries; changing that would be a generic contract repair
outside this microseal).  A dedicated test locks their meaning on a descending
page (first = newest, last = oldest).

## Descending trade adversarial results

Requested window contains only ONE row of a descending page `[t3 newest, t2,
t1 oldest]` (600 s apart):

| scenario | returned page | expected | result |
|---|---|---|---|
| oldest row only in window | descending | PARTIAL_INTERVAL | PASS |
| newest row only in window | descending | PARTIAL_INTERVAL | PASS |
| middle row only in window | descending | PARTIAL_INTERVAL | PASS |
| no row in window | descending | GAP_DETECTED | PASS |

Each also asserts `is_complete=False` and `next_resume_token=None`.

## Non-monotonic (scrambled) page result

Scrambled order `[t2, t3, t1]` with t3 inside the requested window ->
`PARTIAL_INTERVAL`, no `GAP_DETECTED`, `is_complete=False` — classification is
independent of row ordering.

## Ascending funding regression

Ascending funding page with an in-window row -> `PARTIAL_INTERVAL` only; with a
window before all rows -> `GAP_DETECTED` only; `is_complete=False` in both.
I07R1 behavior preserved.

## Quality flag exclusivity

For every non-empty historical case `PARTIAL_INTERVAL` and `GAP_DETECTED` are
mutually exclusive (asserted per test).  Independent flags such as
`DUPLICATE_EDGE` may coexist; none were affected.

## Completion / resume semantics

- Historical (funding/trade): `is_complete = False` ALWAYS; `next_resume_token
  = None`; overlap does NOT imply completeness (tested).
- Empty historical default page: `row_count=0`, `EMPTY_VALID` present,
  `is_complete=False`, no invented `GAP_DETECTED` (an empty default page does
  not prove the requested window is empty).  Unchanged from I07R1.
- BOOK_SNAPSHOT: CURRENT_ONLY, `is_complete=True` per current snapshot unit,
  no historical overlap classification.  Unchanged.

## Unchanged invariants

Exact 3-sensor I14 set (BOOK_SNAPSHOT CURRENT_ONLY, FUNDING PRIMARY, TRADE
PRIMARY); `BTC-USDT-SWAP` production scope only; ETH/SOL/DOGE probe-only;
PUBLIC_REST / NO_AUTH / $0; funding PUBLIC namespace (never /market);
history-trades route; ms-epoch STRING timestamp contract; 7-field funding /
7-field trade / 4-field book required schemas; exact-int seqId; book level
`len >= 2`; markPrice additive/unverified; raw `RawPayloadEnvelope` before
parse release; SchemaDrift carries the envelope; typed errors; typed
unsupported sensors; verified history; methodology pins; PIT state; archive
boundary; no premium/basis expansion; no deep historical-book expansion.

## Tests

- OKX provider tests: **142 passed** (was 135 in I07R1; +7 from the
  order-invariant adversarial class).
- Full `tests/crypto_sensor_fabric/` suite: **1074 passed / 0 failed**
  (floor 1067 not reduced).
- Kraken regression: green (unchanged, frozen).
- Gate regression: green (unchanged, frozen).

## Conformance

OKX common `PRODUCTION_CANDIDATE` conformance (real `OkxAdapter` + fake
transport): **0 failed** — the suite never asserts historical
`is_complete=True`, so the window-truth invariants keep it green.

## Lint / type

- `ruff check` (full repo): clean.
- mypy on the changed OKX module (`adapter.py`): clean (remaining repo errors
  pre-existing: planner/rest/probe).

## Network calls

ZERO network calls in I07R2 (fake transport only).  Network smoke remains
reserved for SENSOR-B3-I14.

## Readiness state

| Sensor | adapter_status | pagination/resume | window replay | smoke |
|---|---|---|---|---|
| MECHANICAL_BOOK_SNAPSHOT | ADAPTER_READY | n/a (CURRENT_ONLY) | n/a (CURRENT_ONLY) | NOT_RUN |
| MECHANICAL_FUNDING | ADAPTER_READY | LIMITED | LIMITED | NOT_RUN |
| MECHANICAL_TRADE | ADAPTER_READY | LIMITED | LIMITED | NOT_RUN |

## Ledger state

`SENSOR-B3-I07R2 COMPLETE` proposed; OKX
`adapter_implemented = TRUE · boundary_hardened = TRUE · offline_sealed = TRUE
· network_smoke = NOT_RUN`; Kraken OFFLINE_FROZEN; Gate OFFLINE_FROZEN;
REAL_PROVIDER_ADAPTERS = 3; `next_provider_authorized = FALSE`;
`next_checkpoint_authorized = FALSE`; recommended next = SENSOR-B3-I08
DERIBIT (NOT AUTHORIZED until operator review).

## Verdict

Proposed only if all gates pass: `PASS_SENSOR_B3_I07R2_OKX_SEALED`.
Still NOT `PASS_BLOC_03`.  Deribit was NOT started.
