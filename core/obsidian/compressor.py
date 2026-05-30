"""
Compressor — Phase 0B
Convert runtime noise into compressed operational abstractions.

Core principle: Raw execution traces are entropy landfill.
Compressed operational knowledge is reusable intelligence.

Input:  Raw tracebacks, context, fix attempts, execution logs
Output: Structured markdown with CAUSE/FIX/RESULT/LINKS

Usage:
    from core.obsidian.compressor import compress_trace, extract_signal
    note = compress_trace(traceback_str, context, fix_attempts)
"""

import re
from typing import Optional


# Patterns that constitute "noise" — removed during compression
NOISE_PATTERNS = [
    r"Traceback \(most recent call last\):",
    r"File \".*?\", line \d+, in .*",
    r"^\s*\^+\s*$",  # Caret lines
    r"During handling of the above exception",
    r"Traceback \(innermost last\)",
    r"^\s*$",  # Empty lines (collapsed later)
]

# Patterns that constitute "signal" — kept during compression
SIGNAL_PATTERNS = [
    r"\w+Error:",           # Error types
    r"\w+Exception:",       # Exception types
    r"AssertionError",      # Assertion failures
    r"Failed to .*",        # Failure descriptions
    r"Expected .*",         # Expected values
    r"Got .*",              # Actual values
    r"Fixed by .*",         # Fix descriptions
    r"Result: .*",          # Results
    r"Root cause: .*",      # Root cause analysis
]


def compress_trace(
    traceback: str,
    context: str = "",
    fix_attempts: list[str] | None = None,
    fix_applied: str = "",
    result: str = "",
) -> str:
    """
    Compress a raw execution trace into operational markdown.

    Args:
        traceback: Raw traceback string
        context: Additional context about what was happening
        fix_attempts: List of fix attempts (noise — only last kept)
        fix_applied: The fix that actually worked
        result: Outcome after fix

    Returns:
        Compressed markdown string following CAUSE/FIX/RESULT/LINKS format
    """
    lines = traceback.strip().split("\n")
    signal_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Check if line matches any signal pattern
        for pattern in SIGNAL_PATTERNS:
            if re.search(pattern, stripped):
                signal_lines.append(stripped)
                break

    # Deduplicate while preserving order
    seen = set()
    unique_signals = []
    for line in signal_lines:
        if line not in seen:
            seen.add(line)
            unique_signals.append(line)

    # Build compressed output
    output_lines = []

    # CAUSE: Extract from traceback signals + context
    output_lines.append("CAUSE:")
    if context:
        output_lines.append(context.strip())
    for sig in unique_signals[:5]:  # Cap at 5 signal lines
        output_lines.append(sig)
    output_lines.append("")

    # FIX
    output_lines.append("FIX:")
    if fix_applied:
        output_lines.append(fix_applied.strip())
    elif fix_attempts:
        # Keep only the last (successful) attempt
        output_lines.append(fix_attempts[-1].strip())
    output_lines.append("")

    # RESULT
    output_lines.append("RESULT:")
    if result:
        output_lines.append(result.strip())
    else:
        output_lines.append("Pending verification")
    output_lines.append("")

    # LINKS: Auto-extract potential wiki-links from error types
    links = []
    for sig in unique_signals:
        # Extract error class names as potential links
        match = re.search(r"(\w+Error|\w+Exception)", sig)
        if match:
            links.append(match.group(1))

    if links:
        output_lines.append("LINKS:")
        for link in set(links):
            output_lines.append(f"[[{link}]]")
        output_lines.append("")

    return "\n".join(output_lines)


def extract_signal(raw_text: str) -> dict:
    """
    Extract operational signal from unstructured text.

    Returns dict with keys: cause, fix, result, links
    """
    result = {"cause": "", "fix": "", "result": "", "links": []}

    # Try to find labeled sections
    sections = {}
    current_section = None
    current_content = []

    for line in raw_text.split("\n"):
        upper = line.strip().upper()
        if upper in ("CAUSE:", "FIX:", "RESULT:", "LINKS:"):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = upper.rstrip(":")
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    if "CAUSE" in sections:
        result["cause"] = sections["CAUSE"]
    if "FIX" in sections:
        result["fix"] = sections["FIX"]
    if "RESULT" in sections:
        result["result"] = sections["RESULT"]
    if "LINKS" in sections:
        # Extract [[WikiLinks]]
        links = re.findall(r"\[\[(.+?)\]\]", sections["LINKS"])
        result["links"] = links

    return result


def is_noise(text: str) -> bool:
    """Check if a line of text is noise (not operational signal)."""
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, text.strip()):
            return True
    return False


def filter_noise(lines: list[str]) -> list[str]:
    """Remove noise lines from a list of strings."""
    return [line for line in lines if not is_noise(line)]
