"""Fix all remaining issues."""
import re

# Fix 1: continuity_memory.py REPO_ROOT
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\continuity_memory.py"
content = open(path).read()
content = content.replace(
    'REPO_ROOT = Path(__file__).resolve().parents[3]',
    'REPO_ROOT = Path(__file__).resolve().parents[2]'
)
open(path, "w").write(content)
print("Fixed continuity_memory REPO_ROOT")

# Fix 2: task_intent_analyzer - make repair/debugging patterns stronger
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\task_intent_analyzer.py"
content = open(path).read()

# The issue is that "Fix the broken API endpoint" matches coding (api, endpoint) before repair (fix, broken)
# We need to make repair patterns score higher
old_repair = '''    "repair": [
        r"\\b(repair|fix|recover|restore|heal|stabilize)\\b",
        r"\\b(broken|crash|degrad)\\b",
        r"\\b(restart|reboot|reset)\\b",
    ],'''
new_repair = '''    "repair": [
        r"\\b(repair|fix|recover|restore|heal|stabilize)\\b",
        r"\\b(broken|crash|degrad|failure)\\b",
        r"\\b(restart|reboot|reset)\\b",
        r"\\b(fix.*broken|broken.*fix|repair.*system|system.*repair)\\b",
    ],'''

if old_repair in content:
    content = content.replace(old_repair, new_repair)
    print("Fixed repair patterns")
else:
    print("Repair pattern not found - trying alternate")
    # Show what's there
    idx = content.find('"repair"')
    if idx >= 0:
        print(repr(content[idx:idx+300]))

open(path, "w").write(content)
print("Done")
