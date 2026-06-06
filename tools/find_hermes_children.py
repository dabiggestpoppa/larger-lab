"""Find children of hermes_telegram processes."""
import subprocess
import re

# Get all python processes
result = subprocess.run(
    ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,ParentProcessId,CommandLine"],
    capture_output=True, text=True
)
print(result.stdout[:3000])
