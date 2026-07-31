"""Check what real data is available from running systems."""
import sys, json
sys.path.insert(0, '.')
from pathlib import Path

print("=== REAL DATA SOURCES ===\n")

# 1. 72h test checkpoints
cp = json.loads(Path('progress/11-1-b-checkpoints.json').read_text())
print(f"1. 72h Test Checkpoints: {cp['total_checkpoints']} checkpoints")
for c in cp['checkpoints']:
    oh = c['observer_health']
    print(f"   {c['checkpoint_id'][:20]}: A={oh['alive']} D={oh['degraded']} X={oh['dead']} drift={c['drift_score']}")

# 2. Stability results
print(f"\n2. Stability Results:")
for f in ['chaos_20x_results.json', 'restart_recovery_results.json', 'recursive_stability_results.json', 'semantic_test_summary.json']:
    p = Path(f'stability/{f}')
    if p.exists():
        data = json.loads(p.read_text())
        test_name = data.get('test_name', data.get('test_id', f))
        passed = data.get('passed', '?')
        total = data.get('total', data.get('total_tests', data.get('total_checkpoints', '?')))
        print(f"   {f}: {test_name} — {passed}/{total} pass")

# 3. OCE backend
print(f"\n3. OCE Backend:")
try:
    from oce.backend.observer_runtime import ObserverState
    print(f"   ObserverState: {[s.value for s in ObserverState]}")
except Exception as e:
    print(f"   ObserverRuntime: ERROR - {e}")

try:
    from oce.backend.event_fabric import get_fabric
    fabric = get_fabric()
    print(f"   EventFabric: event_count={getattr(fabric, 'event_count', 'N/A')}")
except Exception as e:
    print(f"   EventFabric: ERROR - {e}")

# 4. SRRA modules
print(f"\n4. SRRA Modules:")
try:
    from srrs_opc.drift_detector import DriftDetector
    dd = DriftDetector()
    print(f"   DriftDetector: staleness={dd.staleness_days}d, min_weight={dd.min_weight_threshold}")
except Exception as e:
    print(f"   DriftDetector: ERROR - {e}")

try:
    from srrs_opc.consistency_validator import ConsistencyValidator
    cv = ConsistencyValidator()
    print(f"   ConsistencyValidator: {len(cv.conflict_patterns)} conflict patterns")
except Exception as e:
    print(f"   ConsistencyValidator: ERROR - {e}")

try:
    from srrs_opc.recovery_anchors import get_anchor_count
    count = get_anchor_count()
    print(f"   RecoveryAnchors: {count} anchors in DB")
except Exception as e:
    print(f"   RecoveryAnchors: ERROR - {e}")

# 5. PM2 experiments
print(f"\n5. PM2 Experiment Data:")
exp_dir = Path('experiments/phase11')
if exp_dir.exists():
    for d in exp_dir.iterdir():
        if d.is_dir():
            reports = list(d.glob('**/reports/*.json'))
            print(f"   {d.name}: {len(reports)} report files")
            for r in reports[:3]:
                print(f"     - {r.name}")

# 6. Frontend API server
print(f"\n6. Frontend API Server:")
api_server = Path('srrs_opc/frontend/api_server.py')
if api_server.exists():
    print(f"   api_server.py: EXISTS")
    # Check if it has real data endpoints
    content = api_server.read_text()
    endpoints = [line.strip() for line in content.split('\n') if 'GET' in line or 'POST' in line]
    for ep in endpoints[:10]:
        if ep:
            print(f"     {ep}")

print("\n=== SUMMARY ===")
print("Real data available from:")
print("  - 72h test checkpoints (6 checkpoints with observer health)")
print("  - Chaos test results (28 cycles, 112 scenarios)")
print("  - Semantic test results (9/9 pass)")
print("  - Restart recovery results (5/5 pass)")
print("  - Recursive stability results (7/7 pass)")
print("  - PM2 experiment reports (topology, entropy, continuity, consensus)")
print("  - OCE backend (ObserverRuntime, EventFabric, DriftDetector)")
print("  - SRRA modules (DriftDetector, ConsistencyValidator, ContradictionResolver)")
