# 🐛 Event loop delay detected

- **Severity:** warn
- **Category:** performance
- **First Seen:** 2026-05-16T02:39:10.317-04:00
- **Last Seen:** 2026-05-16T12:51:59.479-04:00
- **Occurrences:** 169
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"diagnostic\"}","1":"liveness warning: reasons=event_loop_delay interval=30s eventLoopDelayP99Ms=88.1 eventLoopDelayMaxMs=2485.1 eventLoopUtilization=0.213 cpuCoreRatio=0.237 active=1 waiting=0 queued=1 phase=channels.telegram.start-account recentPhases=sidecars.subagent-recovery:41ms,sidecars.main-session-recovery:15ms,post-attach.update-sentinel:1ms,sidecars.model-prewarm:8
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
