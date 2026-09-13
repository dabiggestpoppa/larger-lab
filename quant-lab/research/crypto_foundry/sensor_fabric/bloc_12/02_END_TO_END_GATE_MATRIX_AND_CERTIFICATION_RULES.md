# BLOC 12 — END-TO-END GATE MATRIX + CERTIFICATION RULES

## 1. Purpose

Convert Blocs 1–11 into one non-ambiguous final acceptance matrix.

The execution agent must never reduce this to `pytest passed`.

---

## 2. Gate classes

```text
G0 BLOCKING INVARIANT
G1 REQUIRED FUNCTIONAL
G2 REQUIRED SCIENTIFIC
G3 REQUIRED RESILIENCE
G4 REQUIRED OPERABILITY
G5 ADVISORY / NON-BLOCKING
```

A single failed G0 blocks the full stack.

---

## 3. Bloc-by-bloc certification matrix

### BLOC 1 — CONTRACTS / SEMANTICS

Blocking gates:
- canonical sensor vocabulary has no unresolved collision;
- access classes recognized everywhere;
- missingness types preserved;
- semantic equivalence classes versioned;
- quality flags schema-valid;
- no provider-specific names leak into canonical sensor contracts.

Evidence:
- schema validation report;
- registry diff report;
- forbidden-field scan.

### BLOC 2 — CAPABILITY PROBES

Blocking gates:
- every enabled provider has a reproducible probe receipt;
- claimed historical support is separated from verified support;
- 2021/2022/2024/2026/recent checkpoints attempted where meaningful;
- auth/free status verified;
- unsupported/history-unavailable explicitly typed.

Scientific gates:
- critical sensor families have actual historical evidence, not docs-only claims.

### BLOC 3 — PROVIDER ADAPTERS

Blocking gates:
- common interface honored;
- unsupported methods return typed `NOT_SUPPORTED`;
- native payload preserved before interpretation;
- retries bounded;
- cursor loops detected;
- rate limits respected;
- no paid/trading fallback;
- deterministic request fingerprinting.

Resilience gates:
- restart/resume;
- duplicate-page handling;
- schema drift fixture;
- access-policy change handling.

### BLOC 4 — T0 RAW LAKE

Blocking gates:
- exact-byte SHA identity;
- atomic commit order;
- source mutation preserved;
- manifest referential integrity;
- T0B lineage to T0A;
- no destructive rewrite;
- resume advancement only after durable commit.

Resilience:
- crash at each commit stage;
- checksum corruption quarantine;
- restore verification.

### BLOC 5 — T1 PIT NORMALIZATION

Blocking gates:
- canonical identity resolved PIT;
- contract lifecycle respected;
- current symbol map cannot rewrite historical identity;
- timestamps retain source semantics;
- `market_available_at` rules enforced;
- revisions do not leak backward;
- stablecoin conversion is PIT-valid;
- native values preserved;
- T1→T0 full lineage;
- hard-ID dedupe only when valid.

Scientific gates:
- liquidation side semantics fixtures;
- aggressor semantics fixtures;
- OI unit fixtures;
- funding interval fixtures;
- inverse/linear fixtures;
- book sequence fixtures.

### BLOC 6 — QUALITY / REDUNDANCY / FAILOVER

Blocking gates:
- provider health != sensor health;
- aggregator dependencies do not inflate independent source count;
- source comparability gates cross-venue operations;
- valid zero != missing;
- failover does not erase source identity;
- hard quality failures cannot be averaged away.

Scientific gates:
- disagreement surface preserved;
- quorum policy deterministic;
- quality vector visible to downstream consumers.

### BLOC 7 — HISTORICAL BACKFILL

Blocking gates:
- deterministic shard plan;
- PIT instrument lifecycle clips requests;
- ragged history retained;
- every successful shard flows T0→T1→quality;
- revision history preserved;
- provider fallback cannot relabel venue gap as repaired.

Functional gates:
- bounded pilot complete before full sweep;
- coverage heatmap/redundancy matrix generated;
- event-window coverage query works.

### BLOC 8 — LIVE RECORDER

Blocking gates:
- exact live payload archival;
- explicit event-time/arrival-time;
- reconnect creates new session;
- sequence gap invalidates continuity where required;
- no silent fake book reconstruction;
- live gap registry created on outages;
- reboot recovery does not hide downtime.

Resilience gates:
- forced disconnect;
- feed stall;
- sequence skip;
- checksum failure;
- machine restart;
- disk pressure;
- provider outage.

### BLOC 9 — T2 OBSERVABLE FABRIC

Blocking gates:
- venue-local state precedes cross-venue state;
- cross-venue operations require Bloc 6 permissions;
- physical and standardized amplitudes retained;
- static + rolling protocols implemented;
- no universal stress score introduced;
- generation metadata complete;
- historical and live compiler outputs converge.

Scientific gates:
- breadth always includes denominator/coverage;
- consensus exposes source set/independence;
- dispersion remains visible;
- baseline sample support reported.

### BLOC 10 — SENSOR SERVICE

Blocking gates:
- read-only;
- provider/network calls impossible from service;
- offline query works;
- exact generation pinning;
- `AS_KNOWN_THEN` semantics honored;
- quality/coverage/lineage included;
- failure contract typed rather than empty response.

### BLOC 11 — REPLAY / MARKET OS

Blocking gates:
- `mechanical_replay(t)` deterministic;
- PIT universe locked;
- run generations locked;
- NullBoundary propagated;
- replay cannot invent lifecycle stages;
- shadow-live equivalence passes;
- Market OS runtime schemas validate.

Scientific gates:
- event packet distinguishes observed vs derived state;
- missingness asymmetry measurable;
- no infrastructure promotion of research status.

---

## 4. Cross-bloc invariants

These are tested end-to-end, not only locally.

### X1 — provenance closure

For any T2 value:

```text
T2
→ T1 rows
→ T0B projection
→ AcquisitionRecord
→ T0A EvidenceBlob
```

must resolve without broken links.

### X2 — temporal closure

For `AS_KNOWN_THEN(t)` every source and transformation must be demonstrably available by `t` under declared methodology.

### X3 — semantic closure

No cross-provider arithmetic is allowed unless the semantic registry and Bloc 6 eligibility permit it.

### X4 — quality monotonicity

Downstream layers may retain or downgrade input quality. They may never silently upgrade it.

### X5 — revision isolation

Later source revisions may create new generations but cannot mutate old certified replay runs.

### X6 — offline reproducibility

A pinned historical replay must run without provider network access.

### X7 — free-only closure

No required runtime or historical step depends on a paid source.

### X8 — research firewall

Research packet fields are canonical mechanics, not provider-native implementation details.

---

## 5. Certification levels by research scope

Certification is not just system-wide; it is also scope-aware.

```text
C0 INVALID
C1 VENUE_LOCAL
C2 MULTI_PROVIDER_CORROBORATED
C3 CROSS_VENUE_RESEARCH_READY
C4 MULTI_ERA_RESEARCH_READY
C5 SHADOW_LIVE_VALIDATED
```

Examples:
- Deribit liquidation anatomy may be C1/C2 and still useful locally.
- BTC OI may reach C4.
- a live BTC mechanical packet may reach C5 after shadow-live equivalence.

No scope may claim a higher level than its weakest blocking dimension.

---

## 6. Required final matrix

Implementation produces a table keyed by:

```text
sensor
asset/universe
venue/global
start
end
granularity
certification_level
quality_mode
independent_sources
coverage
historical_depth
live_validated
replay_validated
blocking_issues
```

This matrix is the authoritative answer to:

> What can the research agents safely study right now?

---

## 7. Stop rule

If a blocking failure occurs, the agent must:

1. stop certification for affected scope;
2. preserve evidence;
3. classify cause;
4. report nearest valid scope;
5. never weaken the gate to obtain green status.
