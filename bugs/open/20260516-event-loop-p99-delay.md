# 🐛 Event loop P99 delay

- **Severity:** warn
- **Category:** performance
- **First Seen:** 2026-05-16T07:24:28.577-04:00
- **Last Seen:** 2026-05-16T07:49:21.240-04:00
- **Occurrences:** 4
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"diagnostic\"}","1":"liveness warning: reasons=event_loop_utilization interval=207s eventLoopDelayP99Ms=0 eventLoopDelayMaxMs=0 eventLoopUtilization=1 cpuCoreRatio=0.051 active=1 waiting=0 queued=1 phase=channels.telegram.start-account recentPhases=sidecars.subagent-recovery:24ms,sidecars.main-session-recovery:6ms,post-attach.update-sentinel:0ms,sidecars.session-locks:60ms,si
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
