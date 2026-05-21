import os, sys, shutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
SKIP_DIRS = {".git", "node_modules", ".next"}

print("SWEEP START")

# Count before
fb, db = 0, 0
for _, dd, ff in os.walk(WORKSPACE):
    fb += len(ff); db += len(dd)
print(f"Before: {fb} files, {db} dirs")

# Remove __pycache_
pyc = 0
for dp, dn, fn in os.walk(WORKSPACE, topdown=False):
    if os.path.basename(dp) == "__pycache__":
        try: shutil.rmtree(dp); pyc += 1
        except: pass
print(f"pycache removed: {pyc}")

# Remove .bak/.tmp/.swp
bak = 0
for dp, dn, fn in os.walk(WORKSPACE):
    dn[:] = [d for d in dn if d not in SKIP_DIRS]
    for f in fn:
        if os.path.splitext(f)[1].lower() in (".bak", ".tmp", ".swp"):
            try: os.remove(os.path.join(dp, f)); bak += 1
            except: pass
print(f"bak/tmp removed: {bak}")

# Count after
fa, da = 0, 0
for _, dd, ff in os.walk(WORKSPACE):
    fa += len(ff); da += len(da)
print(f"After: {fa} files, {da} dirs")
print("SWEEP DONE")
