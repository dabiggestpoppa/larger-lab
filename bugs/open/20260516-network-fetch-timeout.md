# 🐛 Network fetch timeout

- **Severity:** error
- **Category:** timeout
- **First Seen:** 2026-05-16T01:56:39.399-04:00
- **Last Seen:** 2026-05-16T12:22:55.014-04:00
- **Occurrences:** 34
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"fetch-timeout\"}","1":{"timeoutMs":10000,"elapsedMs":31155,"timerDelayMs":21155,"eventLoopDelayHint":"timer delayed 21155ms, likely event-loop starvation","operation":"fetchWithTimeout","url":"https://api.telegram.org/bot871844…B2J4/getMe"},"2":"fetch timeout reached; aborting operation","_meta":{"runtime":"node","runtimeVersion":"26.1.0","hostname":"BLRRR","name":"{\"subsys
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
