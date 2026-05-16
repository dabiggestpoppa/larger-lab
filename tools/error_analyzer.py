"""
Error Analyzer — Pattern Detection & Fix Suggestions
=====================================================
Analyzes error-db.json to detect recurring patterns and suggest
logic updates, skill improvements, and preventive measures.

Designed for PM to run periodically (every 20 errors or weekly).

Usage:
    python tools/error_analyzer.py          # Full analysis
    python tools.error_analyzer.py --pm     # PM-focused: suggest skills/logic updates
    python tools.error_analyzer.py --summary  # Quick stats
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from error_logger import get_errors, get_patterns, get_stats, log_error


def analyze_patterns(min_occurrences: int = 2) -> dict:
    """Full pattern analysis."""
    patterns = get_patterns(min_occurrences=min_occurrences)
    stats = get_stats()
    
    analysis = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "patterns": [],
        "recommendations": [],
    }
    
    for p in patterns:
        rec = {
            "pattern_id": p["id"],
            "service": p["service"],
            "symptom": p["symptom_pattern"],
            "occurrences": p["occurrences"],
            "severity": p["max_severity"],
            "agents": p["agents_involved"],
            "total_attempts": p["total_attempts"],
        }
        
        # Generate recommendation based on pattern
        if p["occurrences"] >= 3:
            rec["action"] = "CREATE_SKILL"
            rec["suggestion"] = f"Create a dedicated skill for {p['service']} {p['symptom_pattern']} errors. Occurred {p['occurrences']}x across agents {', '.join(p['agents_involved'])}."
        elif p["total_attempts"] > 5:
            rec["action"] = "UPDATE_LOGIC"
            rec["suggestion"] = f"Update Diagnostic Soft Logic in AGENTS.md. Pattern '{p['symptom_pattern']}' in {p['service']} required {p['total_attempts']} total attempts."
        elif p["max_severity"] == "critical":
            rec["action"] = "ADD_CHECK"
            rec["suggestion"] = f"Add pre-flight check for {p['service']} {p['symptom_pattern']}. Critical error occurred {p['occurrences']}x."
        else:
            rec["action"] = "MONITOR"
            rec["suggestion"] = f"Monitor {p['service']} {p['symptom_pattern']}. Currently {p['occurrences']} occurrences."
        
        analysis["recommendations"].append(rec)
        analysis["patterns"].append(p)
    
    return analysis


def pm_report() -> str:
    """Generate PM-focused report: what skills to create/update."""
    analysis = analyze_patterns(min_occurrences=1)
    
    lines = []
    lines.append("# Error Pattern Analysis — PM Report")
    lines.append(f"Generated: {analysis['generated_at']}")
    lines.append("")
    
    # Stats
    stats = analysis["stats"]
    lines.append(f"## Stats: {stats['total']} errors | {stats['open']} open | {stats['resolved']} resolved | {stats['patterns_detected']} patterns")
    lines.append("")
    
    if stats["by_severity"]:
        lines.append("### By Severity")
        for sev, count in stats["by_severity"].items():
            if count > 0:
                lines.append(f"  {sev}: {count}")
        lines.append("")
    
    if stats["by_service"]:
        lines.append("### By Service")
        for svc, count in sorted(stats["by_service"].items(), key=lambda x: -x[1]):
            lines.append(f"  {svc}: {count}")
        lines.append("")
    
    # High-attempt errors (persistent issues)
    high_attempt = get_errors(min_attempts=3)
    if high_attempt:
        lines.append("## Persistent Errors (>2 attempts)")
        for e in high_attempt:
            lines.append(f"  {e['id']}: [{e['agent']}] {e['symptom']} — {e['attempts']} attempts, {e['severity']}")
            if e["solution"]:
                lines.append(f"    Solution: {e['solution'][:100]}")
        lines.append("")
    
    # Pattern recommendations
    if analysis["recommendations"]:
        lines.append("## Recommendations")
        for rec in analysis["recommendations"]:
            lines.append(f"  [{rec['action']}] {rec['suggestion']}")
        lines.append("")
    
    # Skill suggestions
    lines.append("## Suggested Skills to Create/Update")
    skills_suggested = set()
    for rec in analysis["recommendations"]:
        if rec["action"] == "CREATE_SKILL":
            svc = rec["service"]
            if svc not in skills_suggested:
                skills_suggested.add(svc)
                lines.append(f"  - {svc}-troubleshooter: Auto-diagnose and repair common {svc} errors")
        elif rec["action"] == "UPDATE_LOGIC":
            lines.append(f"  - Update AGENTS.md Diagnostic Soft Logic: Add pattern for '{rec['symptom']}'")
    
    if not skills_suggested:
        lines.append("  No new skills needed yet. Keep monitoring.")
    
    return "\n".join(lines)


def summary_report() -> str:
    """Quick summary."""
    stats = get_stats()
    patterns = get_patterns(min_occurrences=2)
    
    lines = []
    lines.append(f"Error DB: {stats['total']} total | {stats['open']} open | {stats['resolved']} resolved")
    lines.append(f"Patterns detected: {len(patterns)}")
    
    if patterns:
        lines.append("\nTop patterns:")
        for p in patterns[:5]:
            lines.append(f"  {p['id']}: {p['service']}/{p['symptom_pattern']} — {p['occurrences']}x ({p['max_severity']})")
    
    high = stats.get("high_attempt_errors", 0)
    if high > 0:
        lines.append(f"\nHigh-attempt errors (>2 tries): {high}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Error Pattern Analyzer")
    parser.add_argument("--pm", action="store_true", help="PM-focused report")
    parser.add_argument("--summary", action="store_true", help="Quick summary")
    parser.add_argument("--json", action="store_true", help="Full JSON output")
    parser.add_argument("--min-occurrences", type=int, default=2, help="Min occurrences for pattern")
    args = parser.parse_args()
    
    if args.pm:
        print(pm_report())
    elif args.summary:
        print(summary_report())
    elif args.json:
        print(json.dumps(analyze_patterns(min_occurrences=args.min_occurrences), indent=2, default=str))
    else:
        # Default: full analysis
        analysis = analyze_patterns(min_occurrences=args.min_occurrences)
        print(json.dumps(analysis, indent=2, default=str))


if __name__ == "__main__":
    main()
