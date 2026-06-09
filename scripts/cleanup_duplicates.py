"""
CLEANUP SCRIPT — Kill ALL duplicate engine processes.
Run this BEFORE starting any engine. No exceptions. No mercy.
"""
import subprocess
import sys
import time

def kill_duplicates():
    """Kill ALL duplicate engine processes. Keep only the newest of each type."""
    
    # Get all Python processes with their command lines
    result = subprocess.run(
        ["powershell", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
         "Where-Object { $_.CommandLine -match 'cerebus_live_bridge|signal_bot|telegram_gateway|po_watchdog|pm2_watchdog' } | "
         "Select-Object ProcessId, CommandLine, StartTime | "
         "Sort-Object StartTime -Descending | "
         "ConvertTo-Json"],
        capture_output=True, text=True, timeout=10
    )
    
    if not result.stdout.strip():
        print("No engine processes found.")
        return
    
    import json
    try:
        processes = json.loads(result.stdout)
        if isinstance(processes, dict):
            processes = [processes]
    except:
        print("Failed to parse process list.")
        return
    
    # Group by type, keep only the newest of each
    types = {}
    for p in processes:
        cmd = p.get('CommandLine', '')
        if 'cerebus_live_bridge' in cmd:
            t = 'bridge'
        elif 'signal_bot' in cmd:
            t = 'signal'
        elif 'telegram_gateway' in cmd:
            t = 'telegram'
        elif 'watchdog' in cmd:
            t = 'watchdog'
        else:
            continue
        
        if t not in types:
            types[t] = []
        types[t].append(p)
    
    killed = 0
    for t, procs in types.items():
        # Sort by StartTime descending (newest first)
        procs.sort(key=lambda x: x.get('StartTime', ''), reverse=True)
        
        # Keep the newest, kill all others
        for p in procs[1:]:
            pid = p.get('ProcessId')
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                             capture_output=True, timeout=5)
                print(f"Killed duplicate {t} PID {pid}")
                killed += 1
            except:
                pass
    
    if killed > 0:
        time.sleep(3)  # Wait for full shutdown
        print(f"Cleaned up {killed} duplicate processes.")
    else:
        print("No duplicates found.")

if __name__ == "__main__":
    kill_duplicates()
