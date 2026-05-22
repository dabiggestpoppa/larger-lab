# 🐛 Embedded run aborted (surface error)

- **Severity:** error
- **Category:** failover
- **First Seen:** 2026-05-22T01:48:10.763-04:00
- **Last Seen:** 2026-05-22T03:48:10.635-04:00
- **Occurrences:** 2
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"agent/embedded\"}","1":{"event":"embedded_run_failover_decision","tags":["error_handling","failover","assistant","surface_error"],"runId":"e43030c4-7d89-4156-9df2-69b7a4a13dc5","stage":"assistant","decision":"surface_error","failoverReason":"timeout","profileFailureReason":"timeout","provider":"openrouter","model":"openrouter/owl-alpha","sourceProvider":"openrouter","sourceM
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
