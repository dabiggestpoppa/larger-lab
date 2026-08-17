# TB-R6.1 — Remove the TB runtime logon task.
#
# Also stops the supervisor/worker if running.
#
# Run (PowerShell, as the current user):
#     powershell -ExecutionPolicy Bypass -File .\uninstall_windows_runtime.ps1

$ErrorActionPreference = "Stop"

$TaskName = "TB-Runtime-Supervisor"

# stop runtime first
python -m tbctl stop 2>$null | Out-Null
python "$PSScriptRoot\tbctl.py" stop 2>$null | Out-Null

$T = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($T) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Task removed: $TaskName"
} else {
    Write-Host "Task not found: $TaskName (nothing to remove)"
}
