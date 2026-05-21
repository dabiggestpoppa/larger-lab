import os, sys, shutil, subprocess

# Fix encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WS = r"C:\Users\wifik\Desktop\projects\larger-lab"
SKIP = {".git", "node_modules"}

print("[CLEAN] Starting...")

# 1. Count pycache dirs (fast - just walk dirs)
pyc_count = 0
for dp, dn, fn in os.walk(WS):
    dn[:] = [d for d in dn if d not in SKIP]
    if os.path.basename(dp) == "__pycache__":
        try:
            shutil.rmtree(dp)
            pyc_count += 1
        except:
            pass
print(f"[CLEAN] pycache removed: {pyc_count}")

# 2. Remove .bak/.tmp/.swp (only in known clean areas)
bak_count = 0
for dp, dn, fn in os.walk(WS):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        ext = os.path.splitext(f)[1].lower()
        if ext in (".bak", ".tmp", ".swp"):
            try:
                os.remove(os.path.join(dp, f))
                bak_count += 1
            except:
                pass
print(f"[CLEAN] bak/tmp removed: {bak_count}")

# 3. Kill stale node processes using tasklist + taskkill
print("[CLEAN] Checking stale processes...")
try:
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, timeout=10
    )
    print(f"[CLEAN] Node processes: {result.stdout.strip()}")
except:
    pass

print("[CLEAN] Done.")
