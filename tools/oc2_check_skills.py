"""Check OC2 skills for issues."""
import json
from pathlib import Path

# Check each skills directory
dirs = [
    Path(r"C:\Users\wifik\.openclaw-2\skills"),
    Path(r"C:\Users\wifik\Desktop\projects\larger-lab\.agents\skills"),
    Path(r"C:\Users\wifik\Desktop\projects\larger-lab\skills"),
]

for d in dirs:
    if not d.exists():
        continue
    skills = [f.name for f in d.iterdir() if f.is_dir()]
    print(f"\n=== {d} ({len(skills)} skills) ===")
    # Check for any skill with obvious issues
    for skill in sorted(skills):
        skill_dir = d / skill
        # Check for SKILL.md or similar
        for f in skill_dir.iterdir():
            if f.name.lower() in ("skill.md", "skill.json", "package.json"):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")[:200]
                    if "error" in content.lower() or "fail" in content.lower():
                        print(f"  ⚠ {skill}: {f.name} contains error references")
                except Exception:
                    pass
