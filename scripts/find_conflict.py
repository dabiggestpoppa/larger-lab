"""Find what's causing the Telegram 409 conflict."""
import subprocess
import sys

# Get all processes with commandlines
result = subprocess.run(
    ['powershell', '-Command', '''
Get-CimInstance Win32_Process | Select-Object ProcessId, Name, CommandLine |
Where-Object { $_.CommandLine -and ($_.CommandLine -like "*telegram*" -or $_.CommandLine -like "*watchdog*" -or $_.CommandLine -like "*gateway*" -or $_.Name -like "*python*" -or $_.Name -like "*powershell*" -or $_.Name -like "*cmd*") } |
Sort-Object ProcessId |
ForEach-Object { Write-Host ("PID {0} [{1}]: {2}" -f $_.ProcessId, $_.Name, $_.CommandLine) }
'''],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print("STDOUT:", result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
print("STDERR:", result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)

# Check scheduled tasks
result2 = subprocess.run(
    ['powershell', '-Command', '''
Get-ScheduledTask | Where-Object { $_.TaskName -like "*PO*" -or $_.TaskName -like "*telegram*" -or $_.TaskName -like "*gateway*" -or $_.TaskName -like "*watchdog*" } |
Select-Object TaskName, State, Actions | Format-List
'''],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print("\nSCHEDULED TASKS:", result2.stdout[-2000:])