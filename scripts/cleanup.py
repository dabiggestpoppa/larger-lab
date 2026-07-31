import os, glob

base = r"C:\Users\wifik\Desktop\projects\larger-lab"

# Clean temp scripts
scripts = [
    "scripts/process_map.py", "scripts/process_map2.py", "scripts/process_map3.py",
    "scripts/map_processes.py", "scripts/map_processes2.py",
    "scripts/find_conflict.py", "scripts/check_ports.py",
    "scripts/fix_hermes_status.py", "scripts/kill_live.py", "scripts/launch_demo.py",
]

for s in scripts:
    path = os.path.join(base, s)
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted: {s}")
    else:
        print(f"Not found (skip): {s}")

# Clean up archived backup that was already moved
for f in glob.glob(os.path.join(base, "quant-lab/mt5","*signals*")):
    print(f"Archive file (keep): {os.path.basename(f)}")

print("\nCleanup done.")