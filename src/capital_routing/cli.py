"""
Command-line interface for Capital Routing Research System.

Provides commands for running the capital routing research pipeline,
managing artifacts, and executing analysis phases.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .backend.reality_lock import (
    ready_for_phase_1,
    get_failure_reasons,
    _validate_artifact,
    BOOK_2_SCHEMA,
    BOOK_3_SCHEMA,
    APPROVAL_SCHEMA,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging level."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    logging.getLogger().setLevel(numeric_level)


def run_phase_0() -> Dict[str, Any]:
    """Run Phase 0 - Reality Lock."""
    logger.info("Running Phase 0 - Reality Lock")
    
    # Check if ready for Phase 1
    if ready_for_phase_1():
        logger.info("✅ Ready for Phase 1")
        return {
            "status": "PASS",
            "phase": 0,
            "message": "Ready for Phase 1",
            "timestamp": None,  # Would be current time in real implementation
        }
    else:
        reasons = get_failure_reasons()
        logger.warning(f"❌ Not ready for Phase 1: {reasons}")
        return {
            "status": "FAIL",
            "phase": 0,
            "message": "Not ready for Phase 1",
            "reasons": reasons,
            "timestamp": None,
        }


def run_phase_1() -> Dict[str, Any]:
    """Run Phase 1 - Data Discovery."""
    logger.info("Running Phase 1 - Data Discovery")
    
    # This would implement the data discovery logic
    # For now, return a placeholder
    return {
        "status": "NOT_IMPLEMENTED",
        "phase": 1,
        "message": "Phase 1 - Data Discovery (to be implemented)",
        "timestamp": None,
    }


def run_phase_2() -> Dict[str, Any]:
    """Run Phase 2 - Acquisition and Normalization."""
    logger.info("Running Phase 2 - Acquisition and Normalization")
    
    # This would implement the acquisition and normalization logic
    # For now, return a placeholder
    return {
        "status": "NOT_IMPLEMENTED",
        "phase": 2,
        "message": "Phase 2 - Acquisition and Normalization (to be implemented)",
        "timestamp": None,
    }


def run_phase_3() -> Dict[str, Any]:
    """Run Phase 3 - QC, H4, Daily, Alignment."""
    logger.info("Running Phase 3 - QC, H4, Daily, Alignment")
    
    # This would implement the QC and alignment logic
    # For now, return a placeholder
    return {
        "status": "NOT_IMPLEMENTED",
        "phase": 3,
        "message": "Phase 3 - QC, H4, Daily, Alignment (to be implemented)",
        "timestamp": None,
    }


def run_phase_4() -> Dict[str, Any]:
    """Run Phase 4 - Factor Engine."""
    logger.info("Running Phase 4 - Factor Engine")
    
    # This would implement the factor engine logic
    # For now, return a placeholder
    return {
        "status": "NOT_IMPLEMENTED",
        "phase": 4,
        "message": "Phase 4 - Factor Engine (to be implemented)",
        "timestamp": None,
    }


def run_all_phases() -> List[Dict[str, Any]]:
    """Run all phases sequentially."""
    results = []
    
    # Phase 0
    phase_0_result = run_phase_0()
    results.append(phase_0_result)
    
    if phase_0_result["status"] == "PASS":
        # Phase 1
        phase_1_result = run_phase_1()
        results.append(phase_1_result)
        
        if phase_1_result["status"] == "PASS":
            # Phase 2
            phase_2_result = run_phase_2()
            results.append(phase_2_result)
            
            if phase_2_result["status"] == "PASS":
                # Phase 3
                phase_3_result = run_phase_3()
                results.append(phase_3_result)
                
                if phase_3_result["status"] == "PASS":
                    # Phase 4
                    phase_4_result = run_phase_4()
                    results.append(phase_4_result)
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "results": results,
            "summary": {
                "total_phases": len(results),
                "passed_phases": sum(1 for r in results if r["status"] == "PASS"),
                "failed_phases": sum(1 for r in results if r["status"] == "FAIL"),
                "not_implemented_phases": sum(1 for r in results if r["status"] == "NOT_IMPLEMENTED"),
            },
        }, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Capital Routing Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  capital-routing run                    # Run all phases
  capital-routing phase-0                # Run only Phase 0
  capital-routing phase-1                # Run only Phase 1
  capital-routing save-results results.json  # Save results to file
        """,
    )
    
    parser.add_argument(
        "command",
        choices=["run", "phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "save-results"],
        help="Command to execute",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results.json"),
        help="Output file path for results",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Execute command
    if args.command == "run":
        results = run_all_phases()
        save_results(results, args.output)
        
        # Print summary
        print("\n" + "="*50)
        print("CAPITAL ROUTING RESEARCH SYSTEM - SUMMARY")
        print("="*50)
        
        for result in results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "NOT_IMPLEMENTED": "⚠️",
            }.get(result["status"], "❓")
            
            print(f"{status_icon} Phase {result['phase']}: {result['message']}")
        
        print(f"\nTotal: {len(results)} phases")
        print(f"Passed: {sum(1 for r in results if r['status'] == 'PASS')}")
        print(f"Failed: {sum(1 for r in results if r['status'] == 'FAIL')}")
        print(f"Not Implemented: {sum(1 for r in results if r['status'] == 'NOT_IMPLEMENTED')}")
        
    elif args.command == "phase-0":
        result = run_phase_0()
        print(f"Phase 0 Result: {result}")
        
    elif args.command == "phase-1":
        result = run_phase_1()
        print(f"Phase 1 Result: {result}")
        
    elif args.command == "phase-2":
        result = run_phase_2()
        print(f"Phase 2 Result: {result}")
        
    elif args.command == "phase-3":
        result = run_phase_3()
        print(f"Phase 3 Result: {result}")
        
    elif args.command == "phase-4":
        result = run_phase_4()
        print(f"Phase 4 Result: {result}")
        
    elif args.command == "save-results":
        print(f"Results would be saved to {args.output}")
        print("(Run 'capital-routing run' to execute phases and save results)")


if __name__ == "__main__":
    main()