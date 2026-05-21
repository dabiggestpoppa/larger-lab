import os, sys, shutil, subprocess, re, datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"

def sweep():
    print("=" * 50)
    print("SWEEP: Workspace cleanup + terminal cleanup")
    print("=" * 50)

    # 1. Count before
    fb, db = 0, 0
    for _, dd, ff in os.walk(WORKSPACE):
        fb += len(ff); db += len(dd)
    print(f"Before: {fb} files, {db} dirs")

    # 2. Remove __pycache__
    pyc_removed = 0
    for dirpath, dirnames, filenames in os.walk(WORKSPACE, topdown=False):
        bn = os.path.basename(dirpath)
        if bn == "__pycache__" and ".git" not in dirpath:
            try:
                shutil.rmtree(dirpath)
                pyc_removed += 1
            except: pass
    print(f"Removed {pyc_removed} __pycache__ dirs")

    # 3. Remove .bak/.tmp/.swp
    bak_removed = 0
    SKIP = {".git", "node_modules", ".next"}
    for dirpath, dirnames, filenames in os.walk(WORKSPACE):
        # skip large dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in (".bak", ".tmp", ".swp"):
                fp = os.path.join(dirpath, f)
                try:
                    os.remove(fp)
                    bak_removed += 1
                except: pass
    print(f"Removed {bak_removed} .bak/.tmp files")

    # 4. Remove .next cache
    next_dir = os.path.join(WORKSPACE, ".next")
    if os.path.exists(next_dir):
        try:
            sz = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fs in os.walk(next_dir) for f in fs) / (1024*1024)
            shutil.rmtree(next_dir)
            print(f"Removed .next cache ({sz:.1f}MB)")
        except: pass

    # 5. Kill stale node processes (>2h old)
    killed = 0
    try:
        result = subprocess.run(
            ["wmic", "process", "where", 'name="node.exe" or name="python.exe"',
             "get", "ProcessId,CreationDate", "/format:csv"],
            capture_output=True, text=True, timeout=15
        )
        now = datetime.datetime.now()
        for line in result.stdout.strip().split("\n"):
            parts = line.strip().split(",")
            if len(parts) >= 3:
                try:
                    pid = parts[1].strip()
                    created = parts[2].strip()[:14]
                    if created:
                        dt = datetime.datetime.strptime(created, "%Y%m%d%H%M%S")
                        age = (now - dt).total_seconds()
                        if age > 7200 and pid != str(os.getpid()):
                            subprocess.run(["taskkill", "/PID", pid, "/F"],
                                           capture_output=True, timeout=5)
                            killed += 1
                except: pass
    except: pass
    print(f"Killed {killed} stale processes (>2h)")

    # 6. Count after
    fa, da = 0, 0
    for _, dd, ff in os.walk(WORKSPACE):
        fa += len(ff); da += len(dd)
    print(f"After: {fa} files, {da} dirs ({fb - fa} files removed)")
    print("=" * 50)
    print("SWEEP COMPLETE")

if __name__ == "__main__":
    sweep()
