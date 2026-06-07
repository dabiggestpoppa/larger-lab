"""Smoke test: import PO's root modules + a scaffolded module to verify they coexist."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

print("=== PO ROOT MODULES ===")
from field.field_introspector import FieldIntrospector
print(f"FieldIntrospector: {FieldIntrospector}")
methods = [m for m in dir(FieldIntrospector) if not m.startswith("_")][:8]
print(f"  methods: {methods}")

from field.sovereign_health_monitor import SovereignHealthMonitor
print(f"SovereignHealthMonitor: {SovereignHealthMonitor}")
methods = [m for m in dir(SovereignHealthMonitor) if not m.startswith("_")][:8]
print(f"  methods: {methods}")

print()
print("=== SCAFFOLDED MODULES (sample) ===")
from field.phase4_instrumentation.adaptive_profiler import AdaptiveProfilerModule
m = AdaptiveProfilerModule()
print(f"AdaptiveProfilerModule: enabled={m.config.enabled}, running={m.running}")
m.start()
print(f"  after start: running={m.running}")
m.stop()
print(f"  after stop: running={m.running}")

print()
print("OK: PO modules and scaffolded modules coexist")
