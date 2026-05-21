# 🐛 Telegram bot command limit exceeded (144 > 100)

- **Severity:** warn
- **Category:** telegram
- **First Seen:** 2026-05-21T06:51:26.478-04:00
- **Last Seen:** 2026-05-21T10:58:12.366-04:00
- **Occurrences:** 4
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{"0":"{\"subsystem\":\"channels/telegram\"}","1":"Telegram limits bots to 100 commands. 172 configured; registering first 100. Use channels.telegram.commands.native: false to disable, or reduce plugin/skill/custom commands.","_meta":{"runtime":"node","runtimeVersion":"26.1.0","hostname":"BLRRR","name":"{\"subsystem\":\"channels/telegram\"}","parentNames":["openclaw"],"date":"2026-05-21T10:51:26.47
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
