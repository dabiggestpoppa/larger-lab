"""
Clean up duplicate processes for stable 24/7 runtime.
Keeps only the first instance of each service type.
"""
import subprocess
import sys
import os

def get_python_processes():
    """Get all python processes with their command lines."""
    result = subprocess.run(
        ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'ProcessId,CommandLine', '/format:csv'],
        capture_output=True, text=True
    )
    processes = []
    for line in result.stdout.strip().split('\n'):
        if 'python.exe' in line and 'wmic' not in line:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                pid = parts[1].strip()
                cmd = parts[2].strip() if len(parts) > 2 else ''
                if pid.isdigit():
                    processes.append((int(pid), cmd))
    return processes

def kill_pid(pid):
    """Kill a process by PID."""
    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
        return True
    except:
        return False

def main():
    processes = get_python_processes()
    
    # Group by service type
    groups = {
        'telegram_gateway': [],
        'obsidian_vault_sync': [],
        'gateway_watchdog': [],
        'oc2_gateway': [],
        'cerebus_live_bridge': [],
        'symmetry_trap_executor': [],
        'cerebus_guardian': [],
        'p90_cascade_executor': [],
        'oce_backend': [],
        'other': [],
    }
    
    for pid, cmd in processes:
        cmd_lower = cmd.lower()
        if 'telegram_gateway' in cmd_lower:
            groups['telegram_gateway'].append(pid)
        elif 'obsidian_vault_sync' in cmd_lower:
            groups['obsidian_vault_sync'].append(pid)
        elif 'gateway_watchdog' in cmd_lower:
            groups['gateway_watchdog'].append(pid)
        elif 'oc2_gateway' in cmd_lower:
            groups['oc2_gateway'].append(pid)
        elif 'cerebus_live_bridge' in cmd_lower:
            groups['cerebus_live_bridge'].append(pid)
        elif 'symmetry_trap_executor' in cmd_lower:
            groups['symmetry_trap_executor'].append(pid)
        elif 'cerebus_guardian' in cmd_lower:
            groups['cerebus_guardian'].append(pid)
        elif 'p90_cascade' in cmd_lower:
            groups['p90_cascade_executor'].append(pid)
        elif 'uvicorn' in cmd_lower or 'oce.backend.main' in cmd_lower:
            groups['oce_backend'].append(pid)
        else:
            groups['other'].append(pid)
    
    killed = 0
    for service, pids in groups.items():
        if len(pids) > 1:
            print(f"  {service}: {len(pids)} instances — keeping {pids[0]}, killing {len(pids)-1}")
            for pid in pids[1:]:
                if kill_pid(pid):
                    killed += 1
                    print(f"    Killed PID {pid}")
        elif len(pids) == 1:
            print(f"  {service}: 1 instance (PID {pids[0]}) ✓")
        else:
            print(f"  {service}: 0 instances — DOWN ⚠️")
    
    print(f"\n✅ Cleaned up {killed} duplicate processes")
    return groups

if __name__ == "__main__":
    main()
