# Register OpenClaw Gateway Scheduled Tasks
# Run this script as Administrator to create auto-start tasks

$ErrorActionPreference = "Stop"

# OC1 Gateway Task
$oc1Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/min /c "C:\Users\wifik\.openclaw\gateway.cmd"' -WorkingDirectory "C:\Users\wifik\.openclaw"
$oc1Trigger = New-ScheduledTaskTrigger -AtLogon
$oc1Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Register-ScheduledTask -TaskName "OpenClaw-1-Gateway" -Action $oc1Action -Trigger $oc1Trigger -Settings $oc1Settings -Description "OpenClaw 1 Gateway (OC1) - Port 18789" -Force
    Write-Output "OC1 scheduled task created successfully"
} catch {
    Write-Output "OC1 task creation failed: $($_.Exception.Message)"
    Write-Output "Run this script as Administrator to create scheduled tasks"
}

# OC2 Gateway Task
$oc2Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/min /c "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd"' -WorkingDirectory "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
$oc2Trigger = New-ScheduledTaskTrigger -AtLogon
$oc2Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Register-ScheduledTask -TaskName "OpenClaw-2-Gateway" -Action $oc2Action -Trigger $oc2Trigger -Settings $oc2Settings -Description "OpenClaw 2 Gateway (OC2) - Port 18790" -Force
    Write-Output "OC2 scheduled task created successfully"
} catch {
    Write-Output "OC2 task creation failed: $($_.Exception.Message)"
    Write-Output "Run this script as Administrator to create scheduled tasks"
}

Write-Output "`nNote: Startup folder entries are already configured as fallback."
Write-Output "Both gateways will auto-start on login via the startup folder."
