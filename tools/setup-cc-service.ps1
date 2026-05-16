# CC Service Setup — Run CC Cron as a Windows Scheduled Task
# This gives CC the same always-on capability as OpenClaw's gateway
#
# Usage (run as Administrator):
#   powershell -ExecutionPolicy Bypass -File tools\setup-cc-service.ps1
#
# To remove:
#   powershell -ExecutionPolicy Bypass -File tools\setup-cc-service.ps1 -Remove

param(
    [switch]$Remove,
    [int]$IntervalSeconds = 300  # 5 minutes default
)

$TaskName = "LargerLab-CC-Cron"
$WorkspaceRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
$PythonExe = "python"
$ScriptPath = Join-Path $WorkspaceRoot "tools\cc-cron.py"
$LogPath = Join-Path $WorkspaceRoot "progress\cc-cron.log"

if ($Remove) {
    Write-Host "Removing CC Cron scheduled task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "CC Cron task removed."
    return
}

# Create the scheduled task
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$ScriptPath`" --loop --interval $IntervalSeconds" `
    -WorkingDirectory $WorkspaceRoot

$Trigger = New-ScheduledTaskTrigger -AtLogon

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Write-Host "Creating CC Cron scheduled task..."
Write-Host "  Task name: $TaskName"
Write-Host "  Interval: ${IntervalSeconds}s"
Write-Host "  Workspace: $WorkspaceRoot"
Write-Host "  Script: $ScriptPath"

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Claude Code continuous workflow engine for larger-lab" `
    -Force

Write-Host ""
Write-Host "CC Cron task created successfully!"
Write-Host ""
Write-Host "Commands:"
Write-Host "  Start now:  Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Stop:       Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Status:     Get-ScheduledTask -TaskName $TaskName | Select State"
Write-Host "  Run once:   python tools\cc-cron.py --once"
Write-Host "  Loop:       python tools\cc-cron.py --loop"
Write-Host "  Remove:     powershell -File tools\setup-cc-service.ps1 -Remove"
