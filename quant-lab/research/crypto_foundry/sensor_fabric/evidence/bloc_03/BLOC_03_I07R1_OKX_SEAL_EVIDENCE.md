# SENSOR-B3-I07R1 — OKX Acquisition-Truth + Schema-Boundary Seal Evidence

**Review verdict:** `HOLD_PASS_SENSOR_B3_I07_OKX_ADAPTER_OFFLINE_PENDING_I07R1`
(operator accepted implementation direction, held final pass pending this
repair).  **Target verdict if earned:** `PASS_SENSOR_B3_I07R1_OKX_SEALED`.

**Scope:** narrow repair only.  The I14 production sensor set, OKX roles,
production symbol scope, access class, methodology pins, frozen history
boundaries, CURRENT_ONLY book classification, Kraken and Gate are UNCHANGED.
This is still NOT a global Bloc 3 pass.

## Starting SHA

`63154bd72c0b4fd8d7db485e4d2c9cb5df9621a1` (branch
`agent/crypto-sensor-fabric-build`, clean tree, lineage verified).

## Review hold reason

The operator found that a HISTORICAL funding/trade `FetchRequest` carrying a
requested `[start_time, end_time)` window could receive an arbitrary default
page and still be certified `is_complete=True`.  Because committed I13 evidence
does not prove the `after`/`before` continuation direction, the returned page
cannot be shown to satisfy the requested window — certifying completeness
manufactured acquisition truth.

Additional findings: parser required-field sets were narrower than the closed
committed schema fingerprints; `isinstance(seqId, int)` accepted `bool`; book
levels accepted a single price-only element; and `markPrice` was claimed as
evidence-backed though it appears only in probe/synthetic fixtures, not the
committed runtime fingerprint.

## Repair commits

| SHA | Commit |
|---|---|
| `ffbdfdfd` | SENSOR-B3-I07R1A — make OKX historical acquisition completion truthful |
| `820feca4` | SENSOR-B3-I07R1B — seal OKX parser schema and book-level boundaries |
| (this commit) | SENSOR-B3-I07R1C — reconcile evidence, README, readiness, ledger |

Final SHA after push: see repository HEAD (this document is reconciled in the
I07R1C commit).

## Requested-window issue — exact defect and final behavior

**Defect:** `FetchRequest.start_time` / `end_time` were accepted and then
ignored; the adapter issued a single default page and echoed
`is_complete=True`.

**Final behavior (I07R1A):**

- FUNDING / TRADE (HISTORICAL surfaces): `is_complete` is ALWAYS `False`.  The
  adapter can never prove a single page satisfies the requested window while
  continuation direction is unresolved, so it never certifies completeness.
- No continuation token is ever invented: `next_resume_token` stays `None`.
- The returned page is preserved as partial evidence with a truthful quality
  flag: rows overlapping the requested window -> `PARTIAL_INTERVAL`; rows
  entirely outside it -> `GAP_DETECTED`.
- `requested_start` / `requested_end` are preserved verbatim; `actual_first_*`
  / `actual_last_*` describe ONLY the returned provider rows.
- BOOK_SNAPSHOT (CURRENT_ONLY): unchanged — a single current-snapshot
  acquisition unit is complete (`is_complete=True`, no window promise).
- A valid empty DEFAULT page remains `EMPTY_VALID` at page level but is NOT
  complete: an empty page does not prove the requested window is empty.

## Cursor status

- **FUNDING:** after/before continuation direction UNRESOLVED (committed I13
  evidence does not pin it).  Single evidence-backed window; deeper traversal
  LIMITED/UNRESOLVED.  Cursor semantics keyed around `fundingTime` (epoch ms).
- **TRADE:** after/before continuation direction UNRESOLVED.  Single
  evidence-backed window; deeper traversal LIMITED/UNRESOLVED.  Cursor
  semantics keyed around provider-native trade ids — deliberately SEPARATE from
  funding (no shared generic cursor).

## Completion semantics

`is_complete=True` is only emitted when the adapter has evidence-backed grounds
that the requested acquisition unit is complete.  For historical funding/trade
at this checkpoint that is never provable, so `False` is the only truthful
answer.  UNKNOWN / PARTIAL / INCOMPLETE are valid states; false completeness is
not.

## Arbitrary historical-window capability status

NOT fully satisfiable at this checkpoint: an arbitrary
`FetchRequest.start_time` / `end_time` cannot be honored as a complete
replay because continuation direction is unresolved.  The adapter returns the
single default page as partial evidence (never complete).  Full arbitrary-range
replay is gated on evidence (or the later SENSOR-B3-I14 network-smoke
characterization).

## Requested-vs-actual timestamp behavior

`FetchBatch.requested_start/end` carry the request window untouched;
`actual_first_timestamp/actual_last_timestamp` are derived strictly from the
returned rows' validated ms-epoch strings.  They never echo the requested
bounds.  Tests assert the separation explicitly.

## Parser field-by-field decisions (09_SCHEMA_FINGERPRINTS.jsonl authority)

### FUNDING — closed 7-field record, all structurally required

| field | required | type | evidence |
|---|---|---|---|
| `formulaType` | YES | str | fingerprint (all funding entries) |
| `fundingRate` | YES | str | fingerprint |
| `fundingTime` | YES | str (ms epoch) | fingerprint |
| `instId` | YES | str | fingerprint |
| `instType` | YES | str | fingerprint |
| `method` | YES | str | fingerprint |
| `realizedRate` | YES | str | fingerprint |
| `markPrice` | NO — optional/unverified ADDITIVE | str | NOT in fingerprint (probe fixture only); present => ADDITIVE + preserved |

### TRADE — closed 7-field record, all structurally required

| field | required | type | evidence |
|---|---|---|---|
| `instId` | YES | str | fingerprint (was missing from required set) |
| `px` | YES | str | fingerprint |
| `side` | YES | str | fingerprint |
| `source` | YES | str | fingerprint (was missing from required set) |
| `sz` | YES | str | fingerprint |
| `tradeId` | YES | str | fingerprint |
| `ts` | YES | str (ms epoch) | fingerprint |

### BOOK — closed 4-field record, all structurally required

| field | required | type | evidence |
|---|---|---|---|
| `asks` | YES | list[list[str]] | fingerprint |
| `bids` | YES | list[list[str]] | fingerprint |
| `seqId` | YES | EXACT int (`type(v) is int`, bool rejected) | fingerprint `seqId:int` |
| `ts` | YES | str (ms epoch) | fingerprint |

No field observed in the runtime fingerprint is treated as optional; no
fixture-only field is promoted to required.

## seqId strictness

`type(book["seqId"]) is int` — `True` / `False` (bool subclasses int) are
BREAKING_SCHEMA_CHANGE; a genuine int (e.g. `1001`) is accepted.  Applied to
the book snapshot; no other OKX int-typed field accepts bool.

## Book-level cardinality

A level must contain at least `[price, size]` (`len(level) >= 2`), all parts
provider-native strings.  `[]` / `["29512.0"]` fail closed; the minimal
`["29498.0", "1.2"]` and the full evidenced 4-element row pass.  No conversion
to float; strings preserved.

## markPrice evidence disposition

Committed runtime evidence (09_SCHEMA_FINGERPRINTS.jsonl, all six OKX funding
fingerprints) does NOT include `markPrice`.  It appears only in the committed
Bloc 2 probe fixture (`tests/.../probe_payloads/okx/funding_rate_history_success.json`)
and the synthetic I07 fixture.  Therefore:

- the I07 claim that markPrice is "present in committed fixture (I13 evidence)"
  was INCORRECT — I13 evidence is the fingerprint, which excludes it;
- markPrice was removed from the happy baseline fixture row (which now matches
  the closed 7-field fingerprint exactly);
- markPrice is modeled as an OPTIONAL / UNVERIFIED additive field: when present
  it flags `ADDITIVE_SCHEMA_CHANGE` and is preserved under its native name;
  when absent the schema stays `KNOWN_SCHEMA`.  It is never required.

## Synthetic fixture doctrine

All I07 fixtures are `SYNTHETIC_SCHEMA_FIXTURE`.  They test schemas already
established by committed evidence; they never establish field existence,
history, cursor direction, capability, timestamp semantics, role, or
production symbol support.  Wording implying a fixture proves provider reality
was repaired (markPrice claim, completion language).

## Test results

- OKX provider tests: **135 passed** (was 106 in I07; +29 from the new
  window-truth, per-field missing, seqId-bool, level-cardinality and
  markPrice-additive tests).
- Full `tests/crypto_sensor_fabric/` suite: **1067 passed / 0 failed**
  (parent floor 1038 not reduced).
- Kraken regression: green (unchanged).
- Gate regression: green (unchanged).

## Common conformance (PRODUCTION_CANDIDATE)

Run with the REAL `OkxAdapter` + fake transport: **0 failed**.  The window-truth
change keeps conformance green — the suite never asserts `is_complete=True` on
a historical fetch; it asserts dispatch returns a valid `FetchBatch` and
EMPTY_VALID vs unsupported distinction, both preserved.

## Lint / type

- `ruff check` on `providers/okx/` + OKX tests: clean.
- mypy (permissive, OKX modules): OKX `adapter.py` / `parsers.py` /
  `requests.py` / `errors.py` / `capabilities.py` clean; remaining errors are
  pre-existing (planner/rest/probe).

## Network calls

ZERO network calls in I07R1 (fake transport only; no curl / requests / httpx
live).  Network smoke remains reserved for SENSOR-B3-I14.

## Unchanged invariants

- Exact I14 sensor set: BOOK_SNAPSHOT (CURRENT_ONLY), FUNDING (PRIMARY),
  TRADE (PRIMARY) — no fourth path, no omission.
- Production symbol scope: `BTC-USDT-SWAP` only; ETH/SOL/DOGE stay probe-only
  and fail typed `InvalidInstrument`.
- PUBLIC_REST / NO_AUTH / FREE_AUTOMATED / $0; free-only gate pre-transport.
- Funding PUBLIC namespace (never `/market`); no invented `interval` param;
  fundingRate vs realizedRate distinct; interval NOT frozen to "8h".
- ms-epoch STRING timestamps validated strictly; no silent coercion.
- Raw payload preserved in `RawPayloadEnvelope` before parse release;
  SchemaDrift carries the envelope (unchanged).
- Typed unsupported sensors; typed provider errors; nonzero code != EMPTY_VALID.
- No archive substitution, no premium/basis expansion, no deep historical-book
  expansion, no Deribit code, no Bloc 4 work.

## Readiness state

| Sensor | adapter_status | pagination/resume | window replay | smoke |
|---|---|---|---|---|
| MECHANICAL_BOOK_SNAPSHOT | ADAPTER_READY | n/a (CURRENT_ONLY) | n/a (CURRENT_ONLY) | NOT_RUN |
| MECHANICAL_FUNDING | ADAPTER_READY | LIMITED | LIMITED | NOT_RUN |
| MECHANICAL_TRADE | ADAPTER_READY | LIMITED | LIMITED | NOT_RUN |

LIMITED is a documented limitation, not failure; false certainty is the only
failure.  `ADAPTER_READINESS_MATRIX.csv` retains `resume_pass=LIMITED` for
funding/trade; window replay is recorded here and in the README/ledger.

## Known remaining limitations

1. Funding/trade multi-window `after`/`before` continuation direction
   UNRESOLVED from committed evidence — single-window acquisition only, never
   certified complete (I07R1 makes this explicit rather than silent).
2. Arbitrary historical-window replay NOT fully satisfiable until continuation
   semantics are evidenced (I14 network smoke is the natural future
   characterization point).
3. `markPrice` is an unverified additive field until runtime evidence proves
   it in funding-rate-history rows.
4. No live network validation in I07R1 (network smoke reserved for
   SENSOR-B3-I14).

## Verdict

Proposed only if all gates pass: `PASS_SENSOR_B3_I07R1_OKX_SEALED`.
Still NOT `PASS_BLOC_03`.  Next checkpoint remains `SENSOR-B3-I08 — DERIBIT`,
NOT AUTHORIZED in this session.
