"""
Workspace Monitor — watches git + file changes + process health
Runs every 5 minutes, reports to MAD via Telegram if something changes.
"""
import subprocess
import time
import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
LAST_STATE_FILE = WORKSPACE / "quant-lab" / "ml" / "watch_state.json"

def get_git_log(n=3):
    result = subprocess.run(
        ["git", "log", "--oneline", f"-{n}", "--format=%h %s %ar"],
        cwd=str(WORKSPACE), capture_output=True, text=True
    )
    return result.stdout.strip()

def get_new_commits_since(last_hash):
    result = subprocess.run(
        ["git", "log", "--oneline", f"{last_hash}..HEAD", "--format=%h %s %ar"],
        cwd=str(WORKSPACE), capture_output=True, text=True
    )
    return result.stdout.strip()

def get_recent_files(minutes=5):
    """Get files modified in last N minutes."""
    cutoff = time.time() - (minutes * 60)
    recent = []
    for root, dirs, files in os.walk(str(WORKSPACE)):
        # Skip noise
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', 'data')]
        for f in files:
            if f.endswith(('.parquet', '.pkl')):
                continue
            fp = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fp)
                if mtime > cutoff:
                    rel = os.path.relpath(fp, str(WORKSPACE))
                    recent.append(rel)
            except OSError:
                pass
    return recent

def check_processes():
    """Check if key processes are running."""
    result = subprocess.run(
        ["powershell", "-Command",
         "Get-Process -Name 'python' -ErrorAction SilentlyContinue | "
         "Where-Object { $_.CommandLine -match 'cerebus|guardian' } | "
         "Select-Object ProcessId, @{Name='Type';Expression={"
         "if($_.CommandLine -match 'guardian'){'GUARDIAN'}"
         "elseif($_.CommandLine -match 'bridge'){'BRIDGE'}"
         "elseif($_.CommandLine -match 'p90'){'P90'}"
         "elseif($_.CommandLine -match 'symmetry|st_executor'){'ST'}"
         "else{'OTHER'}}}, "
         "@{Name='Age';Expression={((Get-Date)-$_.CreationDate).ToString('hh:mm:ss')}} | "
         "Format-List | Out-String"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def load_state():
    if LAST_STATE_FILE.exists():
        return json.loads(LAST_STATE_FILE.read_text())
    return {"last_commit": "", "last_check": ""}

def save_state(state):
    LAST_STATE_FILE.write_text(json.dumps(state, indent=2))

def main():
    state = load_state()
    now = datetime.now().strftime("%H:%M:%S")
    
    print(f"\n[{now}] Workspace check...")
    
    # Check git
    git_log = get_git_log(1)
    if git_log:
        latest_line = git_log.split('\n')[0]
        latest_hash = latest_line.split()[0]
        
        if latest_hash != state.get("last_commit", ""):
            new_commits = get_new_commits_since(state.get("last_commit", "HEAD~5"))
            print(f"  NEW COMMITS:\n{new_commits}")
            state["last_commit"] = latest_hash
        else:
            print(f"  Git: no new commits (latest: {latest_line})")
    
    # Check recent files
    recent = get_recent_files(5)
    if recent:
        print(f"  RECENT FILES ({len(recent)}):")
        for f in recent[:10]:
            print(f"    {f}")
        if len(recent) > 10:
            print(f"    ... and {len(recent)-10} more")
    else:
        print(f"  Files: no changes in last 5 min")
    
    # Check processes
    procs = check_processes()
    if procs:
        print(f"  PROCESSES:\n{procs}")
    else:
        print(f"  PROCESSES: No cerebus processes found!")
    
    state["last_check"] = now
    save_state(state)

if __name__ == "__main__":
    main()
