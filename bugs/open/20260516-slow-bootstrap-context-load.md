# 🐛 Slow bootstrap context load

- **Severity:** warn
- **Category:** performance
- **First Seen:** 2026-05-16T04:23:04.772-04:00
- **Last Seen:** 2026-05-16T12:23:09.385-04:00
- **Occurrences:** 10
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"agent/embedded\"}","1":"[trace:embedded-run] prep stages: runId=0ff0aaf4-b767-4575-ba68-20d6e7738377 sessionId=a9ce9396-3571-40ea-a8cb-3908bd5c8c70 phase=stream-ready totalMs=9751 stages=workspace-sandbox:6ms@6ms,skills:0ms@6ms,core-plugin-tools:6216ms@6222ms,bootstrap-context:57ms@6279ms,bundle-tools:1295ms@7574ms,system-prompt:16ms@7590ms,session-resource-loader:2099ms@968
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
