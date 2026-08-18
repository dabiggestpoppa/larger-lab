# QL-EXEC-R4.2 — Legacy Export Non-Interference Audit

## Exporter contract (frozen)

`runtime/tb_shadow_export.py` (additive module):

- NEVER blocks or degrades legacy execution: every failure is caught, logged,
  and counted in `telemetry()`; the exporter NEVER raises into the worker.
- NO lock is held across strategy/broker execution: emit is append + flush +
  `os.fsync` only.
- No shared mutable objects with the worker.
- Does not change strategy decisions, execution timing, order path, or broker
  path (pure after-decision copy).
- Bounded disk: rotates at 8 MB, one backup.

## Integration point (documented, NOT wired in R4.2)

```
from runtime.tb_shadow_export import ShadowExporter
shadow_exporter = ShadowExporter(path, generation, legacy_authority_sha)
shadow_exporter.emit({...per-bar record...})   # failures tolerated inside
```

R4.2 deliberately does NOT modify `tb_worker.py` (active TB runtime stays
untouched: `active_tb_modified = false`). The hook is enabled ONLY at live
deployment under operator supervision.

## Failure rule

If the export fails: legacy execution continues unchanged; failure is logged +
counted; the shadow observation for that bar is dropped (shadow falls behind,
never blocks the exporter).

## Performance evidence (offline drill)

- 205 records emitted in 0.52 s (approx 2.5 ms/record, includes fsync).
- 0 failures, 0 blocks.
- Shadow consumption: 205 records stepped in 0.53 s (approx 2.6 ms/record).
- Measured p50/p95/max CPU + memory are recorded in EXPORT_PERFORMANCE.csv /
  RESOURCE_USAGE.csv when the live canary runs; offline instrumentation exists.

## Ownership

The LEGACY worker writes its own export. The SHADOW only reads it and never
writes the export stream.
