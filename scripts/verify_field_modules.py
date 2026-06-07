#!/usr/bin/env python3
"""Verify all field/ modules are importable and instantiable.

Goes beyond pytest — directly imports each module and:
1. Imports the module
2. Instantiates the Config
3. Instantiates the Module
4. Calls start() and stop()
5. Verifies state transitions
"""
import importlib
import sys
import time
from pathlib import Path

# Ensure the workspace root is on sys.path so `import field.X.Y` works
WORKSPACE = Path(__file__).parent.parent.resolve()
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

PHASES = [
    "phase4_instrumentation",
    "phase5_continuity",
    "phase6_resonance",
    "phase7_multiscale",
    "phase8_coevolution",
    "phase9_emergence",
]

# Map of phase -> list of module file names
MODULES_BY_PHASE = {
    "phase4_instrumentation": [
        "adaptive_profiler", "consensus_observer", "field_state_snapshot",
        "instrumentation_bus", "resource_orchestrator", "sovereign_dashboard",
    ],
    "phase5_continuity": [
        "continuity_guardian", "dream_state_engine", "knowledge_graph",
        "long_term_memory", "memory_consolidation", "pattern_librarian",
        "session_bridger", "temporal_reasoner",
    ],
    "phase6_resonance": [
        "belief_propagation", "cognitive_harmony", "collective_reasoning",
        "emergent_insight_detector", "resonance_bus",
    ],
    "phase7_multiscale": [
        "bar_engine", "daily_engine", "scale_bridge", "scale_router",
        "session_engine", "tick_engine", "weekly_engine",
    ],
    "phase8_coevolution": [
        "autonomy_manager", "coevolution_tracker", "feedback_collector",
        "field_adaptation", "operator_profiles", "suggestion_engine",
        "trust_calibration",
    ],
    "phase9_emergence": [
        "emergence_monitor", "field_consciousness", "field_drift_correction",
        "goal_formation", "priority_arbiter", "self_model",
    ],
}


def verify_module(phase: str, module_name: str) -> dict:
    """Verify one module. Returns dict with results."""
    fqdn = f"field.{phase}.{module_name}"
    result = {
        "phase": phase,
        "module": module_name,
        "fqdn": fqdn,
        "import_ok": False,
        "config_ok": False,
        "module_ok": False,
        "start_ok": False,
        "stop_ok": False,
        "error": None,
    }
    try:
        mod = importlib.import_module(fqdn)
        result["import_ok"] = True

        # Find the Config and Module classes
        class_name = module_name.title().replace("_", "")
        config_cls = getattr(mod, f"{class_name}Config", None)
        module_cls = getattr(mod, f"{class_name}Module", None)

        if config_cls is None:
            result["error"] = f"No {class_name}Config class"
            return result

        if module_cls is None:
            result["error"] = f"No {class_name}Module class"
            return result

        # Instantiate
        config = config_cls()
        result["config_ok"] = config.enabled is True

        instance = module_cls()
        result["module_ok"] = instance.config.enabled is True

        # Test state transitions
        instance.start()
        result["start_ok"] = instance.running is True

        instance.stop()
        result["stop_ok"] = instance.running is False

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"

    return result


def main() -> int:
    """Run verification on all 39 modules. Returns 0 if all pass."""
    print("=" * 70)
    print("FIELD MODULE DEEP VERIFICATION")
    print("=" * 70)
    print(f"Importing {sum(len(v) for v in MODULES_BY_PHASE.values())} modules "
          f"across {len(PHASES)} phases...\n")

    results = []
    for phase in PHASES:
        phase_modules = MODULES_BY_PHASE[phase]
        print(f"[{phase}] ({len(phase_modules)} modules)")
        for module_name in phase_modules:
            r = verify_module(phase, module_name)
            results.append(r)
            status = "OK" if all([
                r["import_ok"], r["config_ok"], r["module_ok"],
                r["start_ok"], r["stop_ok"]
            ]) else "FAIL"
            detail = f" ({r['error']})" if r["error"] else ""
            print(f"  [{status:>4}] {module_name:<35} {detail}")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = len(results)
    passing = sum(1 for r in results if all([
        r["import_ok"], r["config_ok"], r["module_ok"],
        r["start_ok"], r["stop_ok"]
    ]))
    failing = total - passing

    print(f"  Total modules: {total}")
    print(f"  Passing:       {passing} ({100*passing//total}%)")
    print(f"  Failing:       {failing}")

    # Per-phase breakdown
    print("\n  Per phase:")
    for phase in PHASES:
        phase_results = [r for r in results if r["phase"] == phase]
        phase_passing = sum(1 for r in phase_results if all([
            r["import_ok"], r["config_ok"], r["module_ok"],
            r["start_ok"], r["stop_ok"]
        ]))
        print(f"    {phase:<30} {phase_passing}/{len(phase_results)}")

    if failing > 0:
        print("\n  FAILURES:")
        for r in results:
            if not all([r["import_ok"], r["config_ok"], r["module_ok"],
                        r["start_ok"], r["stop_ok"]]):
                print(f"    - {r['fqdn']}: {r['error']}")
        return 1

    print(f"\n  All {total} modules VERIFIED OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
