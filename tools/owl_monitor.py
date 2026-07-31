#!/usr/bin/env python3
"""
OWL Active Monitor v4 — Continuous workspace monitoring with rate limit recovery.
Runs autonomously: checks workspace, posts updates, handles errors with sleep backoff.
"""
import os, sys, json, time, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
CHAT_FILE = WORKSPACE / "shared-conversations" / "team-chat.md"
STATE_FILE = WORKSPACE / "progress" / "owl-monitor-state.json"
LOG_FILE = WORKSPACE / "logs" / "owl-monitor.log"

CHECK_INTERVAL = 900  # 15 minutes
RATE_LIMIT_BACKOFF = [60, 120, 300, 600, 1800]
MAX_ERRORS = 5

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def log(msg):
    ts = now_utc()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def read_chat():
    try:
        return CHAT_FILE.read_text(encoding="utf-8")
    except Exception:
        return ""

def append_chat(entry):
    try:
        content = read_chat()
        marker = "\n## Next Steps"
        if marker in content:
            content = content.replace(marker, entry + "\n" + marker)
        else:
            content = content.rstrip() + "\n" + entry + "\n"
        CHAT_FILE.write_text(content, encoding="utf-8")
        log("Posted to team chat")
    except Exception as e:
        log(f"ERROR writing chat: {e}")

def get_python_processes():
    procs = []
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process python -ErrorAction SilentlyContinue | "
             "Select-Object Id, ProcessName, @{N='Memory(MB)';Expression={[math]::Round($_.WorkingSet64/1MB,1)}}, "
             "CPU, @{N='CmdLine';Expression={(Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine}} | "
             "ConvertTo-Json"],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for p in data:
                cmd = p.get("CmdLine", "")
                # Skip self
                if "owl_monitor" in cmd:
                    continue
                procs.append({
                    "pid": p.get("Id"),
                    "name": p.get("ProcessName"),
                    "mem": p.get("Memory(MB)", 0),
                    "cpu": p.get("CPU", 0),
                    "cmd": cmd[:120]
                })
    except Exception as e:
        log(f"ERROR getting processes: {e}")
    return procs

def get_checkpoint_data():
    cp_path = WORKSPACE / "progress" / "11-1-b-checkpoints.json"
    if cp_path.exists():
        try:
            return json.loads(cp_path.read_text())
        except Exception:
            pass
    return None

def get_agent_status():
    agents = {
        "CC": ("claude-code-progress.md", "claude-code-memory.md"),
        "AS": ("assistant-progress.md", "assistant-memory.md"),
        "PM": ("polymorph-progress.md", "polymorph-memory.md"),
        "PM2": ("PM2-progress.md", "PM2-memory.md"),
        "RL": ("rl-progress.md", "rl-memory.md"),
        "Copilot": ("copilot-progress.md", "copilot-memory.md"),
    }
    results = {}
    for agent, (prog, mem) in agents.items():
        prog_path = WORKSPACE / "progress" / prog
        mem_path = WORKSPACE / "progress" / mem
        prog_time = prog_path.stat().st_mtime if prog_path.exists() else 0
        mem_time = mem_path.stat().st_mtime if mem_path.exists() else 0
        results[agent] = {
            "prog_age_h": round((time.time() - prog_time) / 3600, 1) if prog_time else -1,
            "mem_age_h": round((time.time() - mem_time) / 3600, 1) if mem_time else -1,
            "has_prog": prog_path.exists(),
            "has_mem": mem_path.exists(),
        }
    return results

def get_git_head():
    try:
        result = subprocess.run(
            ["git", "-C", str(WORKSPACE), "log", "--oneline", "-1", "--format=%H %s"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def get_new_git_count(last_hash):
    try:
        result = subprocess.run(
            ["git", "-C", str(WORKSPACE), "rev-list", f"{last_hash}..HEAD", "--count"],
            capture_output=True, text=True, timeout=10
        )
        return int(result.stdout.strip())
    except Exception:
        return 0

def check_72h_test_health(cp_data):
    if not cp_data:
        return "unknown", {}
    
    chk_count = cp_data.get("total_checkpoints", 0)
    passed = cp_data.get("passed_checkpoints", 0)
    failed = cp_data.get("failed_checkpoints", 0)
    max_drift = cp_data.get("max_drift_score", 0)
    
    observers = cp_data.get("observers", {})
    alive = sum(1 for o in observers.values() if o.get("status") == "alive")
    degraded = sum(1 for o in observers.values() if o.get("status") == "degraded")
    dead = sum(1 for o in observers.values() if o.get("status") == "dead")
    
    health = {
        "checkpoints": chk_count,
        "passed": passed,
        "failed": failed,
        "max_drift": max_drift,
        "alive": alive,
        "degraded": degraded,
        "dead": dead,
    }
    
    if dead > 0:
        status = "critical"
    elif failed > passed:
        status = "warning"
    elif passed > 0 and failed == 0:
        status = "healthy"
    else:
        status = "watching"
    
    return status, health

def run_check(check_num, last_state):
    log(f"=== CHECK #{check_num} ===")
    errors = []
    
    # 1. Process check
    procs = get_python_processes()
    log(f"Processes: {len(procs)} running")
    for p in procs:
        log(f"  PID {p['pid']}: {p['cmd'][:80]} ({p['mem']}MB)")
    
    # 2. 72h test check
    cp_data = get_checkpoint_data()
    test_health, test_details = check_72h_test_health(cp_data)
    log(f"72h Test: {test_health} | Chk: {test_details.get('passed',0)}/{test_details.get('checkpoints',0)} | "
        f"Drift: {test_details.get('max_drift',0)} | Obs: {test_details.get('alive',0)}A/{test_details.get('degraded',0)}D/{test_details.get('dead',0)}X")
    
    # Check for new checkpoints
    prev_chk = last_state.get("last_checkpoint", 0)
    cur_chk = test_details.get("checkpoints", 0)
    if cur_chk > prev_chk:
        log(f"  NEW CHECKPOINT #{cur_chk} detected!")
        last_state["last_checkpoint"] = cur_chk
    
    # 3. Agent status
    agents = get_agent_status()
    stale = []
    active = []
    for agent, info in agents.items():
        if info["prog_age_h"] >= 0 and info["prog_age_h"] < 2:
            active.append(agent)
        elif info["prog_age_h"] > 6 or info["prog_age_h"] < 0:
            stale.append(agent)
    
    if active:
        log(f"Active agents: {', '.join(active)}")
    if stale:
        log(f"Stale agents: {', '.join(stale)}")
    
    # 4. Git check
    git_head = get_git_head()
    prev_hash = last_state.get("last_git_hash", "")
    new_commits = 0
    if prev_hash and git_head != "unknown":
        new_commits = get_new_git_count(prev_hash.split()[0]) if prev_hash.split() else 0
    last_state["last_git_hash"] = git_head.split()[0] if git_head.split() else ""
    
    if new_commits > 0:
        log(f"Git: {new_commits} new commit(s) | HEAD: {git_head[:80]}")
    
    # 5. Post to chat if significant changes
    should_post = False
    post_lines = [f"\n## [OWL] {now_utc()} — Monitor Check #{check_num}"]
    
    if cur_chk > prev_chk:
        should_post = True
        post_lines.append(f"\n### 72h Test Checkpoint #{cur_chk}")
        post_lines.append(f"- Status: {test_health.upper()}")
        post_lines.append(f"- Drift: {test_details.get('max_drift', 0)}")
        post_lines.append(f"- Observers: {test_details.get('alive',0)}A/{test_details.get('degraded',0)}D/{test_details.get('dead',0)}X")
    
    if new_commits > 0:
        should_post = True
        post_lines.append(f"\n### Git Activity")
        post_lines.append(f"- {new_commits} new commit(s)")
        post_lines.append(f"- Latest: {git_head[:100]}")
    
    if test_health == "critical":
        should_post = True
        post_lines.append(f"\n⚠️ CRITICAL: Observer death detected in 72h test!")
    
    if should_post:
        append_chat("\n".join(post_lines))
    
    # Save state
    try:
        STATE_FILE.write_text(json.dumps(last_state, indent=2))
    except Exception:
        pass
    
    return last_state

def main():
    log("=" * 60)
    log("  OWL ACTIVE MONITOR v4")
    log(f"  Workspace: {WORKSPACE}")
    log(f"  Check interval: {CHECK_INTERVAL}s ({CHECK_INTERVAL/60} min)")
    log(f"  Started: {now_utc()}")
    log("=" * 60)
    
    # Load state
    last_state = {}
    if STATE_FILE.exists():
        try:
            last_state = json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    
    check_num = 0
    error_count = 0
    
    while True:
        try:
            check_num += 1
            last_state = run_check(check_num, last_state)
            error_count = 0  # Reset on success
            
            log(f"Check #{check_num} complete. Sleeping {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Monitor stopped by user.")
            break
        except Exception as e:
            error_count += 1
            log(f"ERROR in check #{check_num}: {e}")
            if error_count >= MAX_ERRORS:
                backoff = RATE_LIMIT_BACKOFF[min(error_count - MAX_ERRORS, len(RATE_LIMIT_BACKOFF) - 1)]
                log(f"MAX ERRORS ({MAX_ERRORS}) — backing off {backoff}s")
                time.sleep(backoff)
            else:
                log(f"Error {error_count}/{MAX_ERRORS} — retrying in {CHECK_INTERVAL}s")
                time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
