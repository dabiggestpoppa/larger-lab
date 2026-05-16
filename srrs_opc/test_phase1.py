"""
Test Phase 1 Implementation
===========================
"""

from srrs_opc import (
    PlannerPatch,
    ExecutionPatch,
    MemoryPatch,
    RepairPatch,
    CollarLayer,
    AgentBridge,
    CollarState
)
from datetime import datetime


def test_phase1():
    """Test the foundational observer mesh."""
    print("=" * 50)
    print("SRRA-OPH Phase 1 Test")
    print("=" * 50)
    
    # Create collar layer
    collar = CollarLayer()
    
    # Register all patches
    planner = PlannerPatch()
    execution = ExecutionPatch()
    memory = MemoryPatch()
    repair = RepairPatch()
    
    collar.register_patch(planner)
    collar.register_patch(execution)
    collar.register_patch(memory)
    collar.register_patch(repair)
    
    print(f"\nRegistered {len(collar.patches)} patches:")
    for pid in collar.patches:
        print(f"  - {pid}")
    
    # Create agent bridge
    bridge = AgentBridge()
    
    # Run 3 cycles
    for i in range(3):
        print(f"\n--- Cycle {i+1} ---")
        results = collar.run_cycle()
        
        # Sync to agents
        sync_data = bridge.sync_from_patches(results)
        
        for pid, state in results.items():
            print(f"{pid}: {state.objective} (conf: {state.confidence:.2f})")
    
    # Show status
    print("\n--- Status ---")
    status = collar.get_status()
    for pid, info in status["patches"].items():
        print(f"{pid}: stable={info['is_stable']}, repairs={info['repair_count']}")
    
    print(f"\nTotal sync cycles: {status['sync_count']}")
    print("\nPhase 1 test complete!")


if __name__ == "__main__":
    test_phase1()