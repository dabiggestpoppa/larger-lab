import os, sys, json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WS = r"C:\Users\wifik\Desktop\projects\larger-lab"

# Scan 1: memory-bank directory
bank = os.path.join(WS, "memory-bank")
print("=== MEMORY BANK CONTENTS ===")
if os.path.exists(bank):
    for f in sorted(os.listdir(bank)):
        fp = os.path.join(bank, f)
        sz = os.path.getsize(fp)
        print(f"  {f} ({sz} bytes)")
else:
    print("  memory-bank/ does not exist")

# Scan 2: skills with self/improve/learn/evolv/grow
print("\n=== SELF-IMPROVEMENT RELATED SKILLS ===")
skills_dirs = [
    os.path.join(WS, "skills"),
    os.path.join(WS, ".agents", "skills"),
]
keywords = ["self", "improv", "learn", "evolv", "grow", "reflect", "adapt", "optimize"]
for sd in skills_dirs:
    if not os.path.exists(sd):
        print(f"  {sd}: not found")
        for d in os.listdir(sd):
            # Only look at dirs whose names match our keywords
            for kw in keywords:
                if kw in d.lower():
                    print(f"  MATCH: {d}")
                    break

# Scan 3: All skills
print("\n=== ALL SKILLS ===")
for sd in skills_dirs:
    if not os.path.exists(sd):
        continue
    print(f"\n  Dir: {sd}")
    for d in sorted(os.listdir(sd)):
        full = os.path.join(sd, d)
        if os.path.isdir(full):
            print(f"    {d}")

print("\n=== SCAN COMPLETE ===")
