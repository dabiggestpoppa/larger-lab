"""Fix task_intent_analyzer.py domain ordering."""
import re

path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\task_intent_analyzer.py"
content = open(path).read()

# Fix 1: Reorder DOMAIN_PATTERNS so repair/debugging come before coding
old_patterns = '''# Task domain classification patterns
DOMAIN_PATTERNS: dict[str, list[str]] = {
    "coding": [
        r"\\b(code|implement|write|build|create|develop|function|class|module|api|endpoint)\\b",
        r"\\b(fix|bug|debug|patch|refactor|optimize)\\b",
        r"\\b(test|unittest|pytest|jest)\\b",
    ],
    "research": [
        r"\\b(research|analyze|investigate|study|explore|survey|review)\\b",
        r"\\b(what|how|why|when|compare|difference)\\b",
        r"\\b(documentation|docs|readme)\\b",
    ],
    "architecture": [
        r"\\b(architecture|design|structure|pattern|system|infrastructure)\\b",
        r"\\b(plan|blueprint|roadmap|strategy)\\b",
        r"\\b(microservice|monolith|layer|component|module)\\b",
    ],
    "repair": [
        r"\\b(repair|fix|recover|restore|heal|stabilize)\\b",
        r"\\b(broken|error|crash|fail|degrad)\\b",
        r"\\b(restart|reboot|reset|clean)\\b",
    ],
    "debugging": [
        r"\\b(debug|trace|log|stack|exception|error|issue|problem)\\b",
        r"\\b(why.*not|doesn't work|not working|fails?)\\b",
        r"\\b(investigate|diagnose|inspect)\\b",
    ],'''

new_patterns = '''# Task domain classification patterns
# Order matters: more specific domains first
DOMAIN_PATTERNS: dict[str, list[str]] = {
    "repair": [
        r"\\b(repair|recover|restore|heal|stabilize)\\b",
        r"\\b(broken|crash|degrad)\\b",
        r"\\b(restart|reboot|reset)\\b",
    ],
    "debugging": [
        r"\\b(debug|trace|log|stack|exception|issue|problem)\\b",
        r"\\b(why.*not|doesn't work|not working|fails?)\\b",
        r"\\b(investigate|diagnose|inspect)\\b",
    ],
    "coding": [
        r"\\b(code|implement|write|build|create|develop|function|class|module|api|endpoint)\\b",
        r"\\b(bug|patch|refactor|optimize)\\b",
        r"\\b(test|unittest|pytest|jest)\\b",
    ],
    "research": [
        r"\\b(research|analyse|investigate|study|explore|survey|review)\\b",
        r"\\b(what|how|why|when|compare|difference)\\b",
        r"\\b(documentation|docs|readme)\\b",
    ],
    "architecture": [
        r"\\b(architecture|design|structure|pattern|system|infrastructure)\\b",
        r"\\b(plan|blueprint|roadmap|strategy)\\b",
        r"\\b(microservice|monolith|layer|component|module)\\b",
    ],'''

if old_patterns in content:
    content = content.replace(old_patterns, new_patterns)
    print("Fixed domain patterns ordering")
else:
    print("Pattern not found - checking...")
    # Try to find the section
    if "DOMAIN_PATTERNS" in content:
        print("DOMAIN_PATTERNS exists but pattern mismatch")
    else:
        print("DOMAIN_PATTERNS not found!")

open(path, "w").write(content)
print("Done")
