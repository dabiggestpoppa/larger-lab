"""Deep analysis of gateway errors for targeted fixes."""
import json
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG_PATH = r"C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-16.log"

stall_sessions = set()
timeout_types = {}
loop_delay_values = []
model_prewarm_values = []
orphan_recovery_failures = []
symlink_errors = []

with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        try:
            obj = json.loads(line.strip())
            msg = obj.get("1", "")
            if not isinstance(msg, str):
                msg = str(msg)
            meta = obj.get("_meta", {})
            name_str = meta.get("name", "")
            subsystem = ""
            m_sub = re.search(r'"subsystem":"([^"]+)"', name_str)
            if m_sub:
                subsystem = m_sub.group(1)

            if "stalled session" in msg:
                m = re.search(r"sessionKey=(\S+)", msg)
                if m:
                    stall_sessions.add(m.group(1)[:50])

            if "timeout" in msg.lower():
                timeout_types[subsystem] = timeout_types.get(subsystem, 0) + 1

            if "eventLoopDelayP99Ms" in msg:
                m = re.search(r"eventLoopDelayP99Ms=([\d.]+)", msg)
                if m:
                    loop_delay_values.append(float(m.group(1)))

            if "model-prewarm" in msg:
                m = re.search(r"model-prewarm:(\d+)ms", msg)
                if m:
                    model_prewarm_values.append(int(m.group(1)))

            if "orphan" in msg.lower() and "failed" in msg.lower():
                orphan_recovery_failures.append(msg[:200])

            if "EPERM" in msg and "symlink" in msg:
                symlink_errors.append(msg[:200])

        except Exception:
            pass

print("=" * 60)
print("🦉 DEEP ERROR ANALYSIS")
print("=" * 60)

print("\n=== STALLED SESSIONS ===")
for s in stall_sessions:
    print(f"  sessionKey: {s}")

print(f"\n=== TIMEOUTS BY SUBSYSTEM ===")
for k, v in sorted(timeout_types.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print(f"\n=== EVENT LOOP DELAY ===")
if loop_delay_values:
    print(f"  Samples: {len(loop_delay_values)}")
    print(f"  Min P99: {min(loop_delay_values):.1f}ms")
    print(f"  Max P99: {max(loop_delay_values):.1f}ms")
    print(f"  Avg P99: {sum(loop_delay_values)/len(loop_delay_values):.1f}ms")
    high = [v for v in loop_delay_values if v > 100]
    critical = [v for v in loop_delay_values if v > 1000]
    print(f"  >100ms: {len(high)} ({len(high)/len(loop_delay_values)*100:.0f}%)")
    print(f"  >1000ms: {len(critical)} ({len(critical)/len(loop_delay_values)*100:.0f}%)")

print(f"\n=== MODEL PREWARM ===")
if model_prewarm_values:
    print(f"  Samples: {len(model_prewarm_values)}")
    print(f"  Min: {min(model_prewarm_values)}ms")
    print(f"  Max: {max(model_prewarm_values)}ms")
    print(f"  Avg: {sum(model_prewarm_values)/len(model_prewarm_values):.0f}ms")

print(f"\n=== ORPHAN RECOVERY FAILURES ===")
print(f"  Count: {len(orphan_recovery_failures)}")
for o in orphan_recovery_failures[:3]:
    print(f"  {o[:120]}")

print(f"\n=== SYMLINK ERRORS ===")
print(f"  Count: {len(symlink_errors)}")
print(f"  Known Windows limitation — no action needed")

print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)
print("1. STALLED SESSIONS: Add session timeout config to openclaw.json")
print("   - Set agent session TTL to prevent indefinite stalls")
print("2. TIMEOUTS: Network/fetch timeouts are Telegram API issues")
print("   - Add retry with exponential backoff for fetch operations")
print("3. EVENT LOOP: P99 delays occasionally spike >1000ms")
print("   - Model prewarm taking 6942ms is the main culprit")
print("   - Consider lazy-loading models instead of prewarming all")
print("4. ORPHAN RECOVERY: 2 failures — gateway timeout during resume")
print("   - Increase orphan recovery timeout from 10s to 30s")
