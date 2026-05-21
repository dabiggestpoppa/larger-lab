# 🐛 Embedded run aborted (surface error)

- **Severity:** error
- **Category:** failover
- **First Seen:** 2026-05-21T05:48:09.582-04:00
- **Last Seen:** 2026-05-21T09:48:40.144-04:00
- **Occurrences:** 3
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"agent/embedded\"}","1":{"event":"embedded_run_failover_decision","tags":["error_handling","failover","assistant","surface_error"],"runId":"f3d1f0c6-4681-4ef9-84f5-c428b9387376","stage":"assistant","decision":"surface_error","failoverReason":"timeout","profileFailureReason":"timeout","provider":"openrouter","model":"openrouter/owl-alpha","sourceProvider":"openrouter","sourceM
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
