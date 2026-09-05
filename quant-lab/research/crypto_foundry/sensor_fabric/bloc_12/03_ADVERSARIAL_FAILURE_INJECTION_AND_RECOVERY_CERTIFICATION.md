# BLOC 12 — ADVERSARIAL FAILURE INJECTION + RECOVERY CERTIFICATION

## 1. Purpose

A sensor fabric that works only when every endpoint is healthy is not certified.

Bloc 12 therefore requires deliberate breakage.

---

## 2. Failure-injection principle

For every critical subsystem:

```text
BREAK IT
→ OBSERVE FAILURE STATE
→ VERIFY NO FALSE DATA
→ RECOVER
→ VERIFY LINEAGE / GAPS / QUALITY
→ REPLAY
```

The test is not merely whether the process restarts. The test is whether scientific truth survives the failure.

---

## 3. Provider / transport failures

Inject:

1. DNS/network loss;
2. connection refused;
3. TLS/session interruption;
4. WebSocket disconnect;
5. WebSocket silent stall;
6. heartbeat-only connection with stale market feed;
7. REST 429;
8. REST 5xx burst;
9. permanent 4xx;
10. malformed JSON;
11. schema field removal;
12. unexpected field type;
13. cursor loop;
14. repeated page;
15. out-of-order page;
16. archive 404;
17. corrupted archive;
18. checksum mismatch;
19. geo/access block;
20. endpoint moves from free to paid/auth-required.

Expected behavior:
- typed failure;
- no fabricated observation;
- provider/feed health downgrade;
- explicit gap if applicable;
- no paid fallback;
- no silent source substitution.

---

## 4. Storage failures

Inject crashes at:

```text
before download completes
before hash
before fsync
before atomic rename
after blob commit / before acquisition commit
after acquisition / before projection
after projection / before manifest
after manifest / before resume advancement
```

Expected invariant:

> resume token never advances beyond durable evidence.

Additional failures:
- file corruption;
- missing blob;
- manifest points to missing projection;
- duplicate blob under repeated acquisition;
- same source boundary returns changed bytes;
- disk full;
- filesystem permission failure;
- second-copy restore hash mismatch.

---

## 5. Identity / PIT failures

Fixtures must attack:

- symbol reused for a different contract;
- contract relisted;
- quote asset changes;
- linear vs inverse misclassification;
- multiplier changes;
- settlement-asset changes;
- exchange rename/alias;
- delisted instrument still present in current registry;
- historical archive discovered after the fact;
- later source revision;
- future stablecoin conversion observation accidentally available;
- current metadata accidentally back-projected.

Expected behavior:
- ambiguity produces typed block/low-confidence state;
- later knowledge does not leak into `AS_KNOWN_THEN`;
- corrected semantics create new generation rather than old-data mutation.

---

## 6. Mechanical semantic failures

### Liquidations
Inject:
- long/short field reversed;
- execution side mistaken for position side;
- base quantity interpreted as USD;
- duplicate liquidation interval;
- provider empty interval mistaken for zero.

### OI
Inject:
- contracts mistaken for base units;
- USD OI double-converted;
- inverse contract notional error;
- cumulative/stock field differenced incorrectly.

### Funding
Inject:
- predicted funding used as realized;
- 1h and 8h rates compared without interval metadata;
- annualization error;
- duplicate publication.

### Order flow
Inject:
- `isBuyerMaker` semantics reversed;
- aggressor direction unknown;
- duplicate trades;
- CVD reset misread as market event.

### Books
Inject:
- missing delta;
- update-id gap;
- checksum fail;
- stale snapshot;
- partial depth presented as full depth.

All must fail loudly or degrade explicitly.

---

## 7. Redundancy / dependency failures

Inject source graphs such as:

```text
Coinalyze ← Binance + Bybit
Binance direct
Bybit direct
```

Verify:

```text
raw sources = 3
independent groups = 2
```

Then remove one underlying venue and confirm aggregator evidence does not masquerade as an independent replacement.

Also test:
- dependency unknown;
- aggregator methodology changes;
- two feeds share same upstream exchange;
- corroboration-only source accidentally requested for arithmetic aggregation.

---

## 8. Disagreement attacks

Construct cases where:

```text
Kraken high
Gate low
Bybit medium
```

and separately where one source is intentionally corrupted.

The reconciliation engine must distinguish:
- plausible venue heterogeneity;
- semantic mismatch;
- likely data corruption.

No majority vote may automatically overwrite minority evidence.

---

## 9. Historical backfill failures

Inject:
- shard interrupted halfway;
- REST repair overlaps archive coverage;
- archive changed after first acquisition;
- history begins later than docs claim;
- provider returns suspicious empty response;
- request crosses listing boundary;
- request crosses delisting boundary;
- rate budget exhausted;
- disk budget exhausted;
- deep-book scope too large.

Expected:
- deterministic shard status;
- resumability;
- typed ragged coverage;
- explicit revision handling;
- no rectangular imputation.

---

## 10. Live recorder failures

Mandatory drill sequence:

```text
healthy capture
→ forced network loss
→ bounded gap creation
→ reconnect
→ new session
→ sequence validation
→ historical repair request
→ repaired / unrepaired classification
```

Additional drills:
- machine process kill;
- full machine restart;
- clock jump;
- backlog burst;
- disk reaches WATCH / CONSTRAINED / CRITICAL;
- one provider feed stale while transport remains alive;
- one provider fully down while redundant providers remain healthy.

---

## 11. T2 / service / replay failures

Inject:
- quality mode degraded;
- denominator coverage drops;
- one independent source disappears;
- baseline sample insufficient;
- T1 generation changes mid-run;
- T2 registry changes mid-run;
- sensor-service cache contains old generation;
- replay called with unavailable historical scope;
- NullBoundary encountered;
- network access blocked completely.

Expected:
- pinned requests stay pinned;
- stale cache cannot cross generation key;
- replay remains deterministic;
- missing region stays NULL/DATA_BLOCKED;
- offline replay still works from local certified evidence.

---

## 12. Shadow-live challenge

Select closed intervals from the live pilot and later replay them.

For each observable compare:

```text
semantic identity
source-set identity / documented difference
physical values
standardized values
quality vector
coverage
state label
transition metadata
```

Allowed differences:
- acquisition lineage;
- receipt IDs;
- normalization execution timestamps;
- explicitly declared post-hoc revision mode.

Blocking differences:
- economic state;
- side/sign;
- unit;
- quality mode;
- `AS_KNOWN_THEN` evidence set;
- baseline version.

---

## 13. Required adversarial evidence packet

Every drill produces:

```text
failure_id
injection_method
pre_state
expected_failure_mode
observed_failure_mode
false_data_emitted = true/false
gap_created
quality_transition
recovery_action
recovery_state
lineage_after_recovery
replay_check
pass/fail
```

Any test that emits false healthy data is a blocking failure.
