"""Workspace cleanup script — removes bloat, stale processes, cache dirs."""
import os, sys, shutil, subprocess, datetime

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"

def get_size_mb(path):
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
    except: pass
    return round(total / (1024*1024), 1)

def cleanup_pycaches():
    """Remove all __pycache__ directories."""
    removed = 0
    freed = 0
    for dirpath, dirnames, filenames in os.walk(WORKSPACE, topdown=False):
        if os.path.basename(dirpath) == "__pycache__":
            if dirpath == WORKSPACE or ".git" in dirpath:
                continue
            size = get_size_mb(dirpath)
            try:
                shutil.rmtree(dirpath)
                removed += 1
                freed += size
                print(f"  🗑️  Removed __pycache__: {dirpath.replace(WORKSPACE,'.')} ({size}MB)")
            except Exception as e:
                print(f"  ⚠️  Failed: {dirpath}: {e}")
    return removed, freed

def cleanup_bak_files():
    """Remove .bak, .tmp, .swp files."""
    removed = 0
    freed = 0
    for dirpath, dirnames, filenames in os.walk(WORKSPACE):
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.bak', '.tmp', '.swp', '~'):
                fp = os.path.join(dirpath, f)
                size = os.path.getsize(fp)
                try:
                    os.remove(fp)
                    removed += 1
                    freed += size / (1024*1024)
                    print(f"  🗑️  Removed: {f}")
                except: pass
    return removed, round(freed, 1)

def cleanup_next_build():
    """Remove .next build cache."""
    next_dir = os.path.join(WORKSPACE, ".next")
    if os.path.exists(next_dir):
        size = get_size_mb(next_dir)
        try:
            shutil.rmtree(next_dir)
            print(f"  🗑️  Removed .next build cache ({size}MB)")
            return size
        except: return 0
    return 0

def cleanup_logs():
    """Archive old logs."""
    log_dir = os.path.join(WORKSPACE, "logs")
    if not os.path.exists(log_dir):
        return 0
    size = get_size_mb(log_dir)
    return size

def count_workspace_items():
    files = 0
    dirs = 0
    for _, d, f in os.walk(WORKSPACE):
        files += len(f)
        dirs += len(d)
    return files, dirs

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 OWL WORKSPACE CLEANUP")
    print("=" * 60)
    print(f"Workspace: {WORKSPACE}")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    files_before, dirs_before = count_workspace_items()
    print(f"📊 Before: {files_before} files, {dirs_before} dirs")
    print()

    print("🧹 Cleaning __pycache__ directories...")
    pyc_removed, pyc_freed = cleanup_pycaches()

    print("🧹 Cleaning .bak/.tmp/.swp files...")
    bak_removed, bak_freed = cleanup_bak_files()

    print("🧹 Cleaning .next build cache...")
    next_freed = cleanup_next_build()

    print("🧹 Checking logs directory...")
    log_size = cleanup_logs()
    if log_size > 50:
        print(f"  ⚠️  Logs directory is {log_size}MB — consider archiving")
    else:
        print(f"  ✅ Logs: {log_size}MB (healthy)")

    files_after, dirs_after = count_workspace_items()
    print()
    print("=" * 60)
    print("📊 CLEANUP SUMMARY")
    print(f"  __pycache__ dirs removed: {pyc_removed} ({pyc_freed}MB freed)")
    print(f"  .bak/.tmp files removed: {bak_removed} ({bak_freed}MB freed)")
    print(f"  .next cache freed: {next_freed}MB")
    print(f"  Files: {files_before} → {files_after} ({files_before - files_after} removed)")
    print(f"  Dirs:  {dirs_before} → {dirs_after} ({dirs_before - dirs_after} removed)")
    print(f"  Total freed: ~{round(pyc_freed + bak_freed + next_freed, 1)}MB")
    print("=" * 60)
