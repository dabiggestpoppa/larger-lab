# QL-EXEC-R4.1 — Market Data Sharing Options

## Options considered

### A. Generic shadow reads MT5 independently

- Pros: independent data path; no legacy coupling.
- Cons: requires resolving MT5 concurrent-read safety (currently UNRESOLVED);
  requires the shadow to hold its own external-session auth; risks session
  binding collision with the active worker.
- Verdict: **DEFER** until MT5_CONCURRENT_READ_AUDIT_PLAN resolves to
  SAFE_CONCURRENT_READ.

### B. Legacy TB exports read-only normalized snapshots; generic consumes them

- Pros: lowest risk; zero concurrent MT5 access; reuses the already-proven
  legacy data pipeline (including its synchronized-common-bar and freshness
  gates); also provides the legacy *decision* observation surface in the same
  export, satisfying LEGACY_OBSERVATION_CONTRACT.
- Cons: needs a small read-only export/telemetry addition to the legacy stack
  (planned here, implemented only in R4.2 with review).
- Verdict: **PREFERRED (G1)**.

### C. Shared read-only market-data service provides both

- Pros: cleanest long-term; both consumers symmetric.
- Cons: new infrastructure; more moving parts; unnecessary for a first shadow
  canary.
- Verdict: **FUTURE OPTION**, revisit at fleet scale (R5+).

## Preferred path

`preferred_market_data_sharing_path = LEGACY_EXPORT_READ_ONLY_SNAPSHOT`

G1 consumes a frozen, normalized, append-only JSONL snapshot emitted by the
legacy stack, containing:

- synchronized closed-bar triangle (GBPAUD / GBPNZD / AUDNZD at the same
  common bar-open timestamp)
- source (bar-open) timestamps preserved, never re-keyed to UTC
- freshness / spread / cross-leg-skew health
- server-clock calibration
- legacy PRIMARY + CONTROL decisions (basis, z, direction, weights, target
  lots, basket state, blocker)

The export is **data-collection only**; it never submits orders. This mirrors
the existing `quant-lab/tb_live/snapshot_capture.py` audit tool (read-only,
fails closed when MT5 is unavailable) and generalizes it into a continuous
feed.

## Restructure prohibition

The active TB stack is NOT restructured to make the shadow elegant. The export
is an additive read-only side-channel, planned here and implemented only under
R4.2 review.
