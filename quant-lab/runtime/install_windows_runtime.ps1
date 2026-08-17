# TB-R6.1 — Install Windows auto-start (logon task) for the TB runtime.
#
# Registers a Task Scheduler entry that launches the TB SUPERVISOR at user
# logon. The task runs as the CURRENT USER (limited privilege) — it inherits
# the user's own token/ACLs, so it can be removed by the user with:
#     schtasks /Delete /TN "TB-Runtime-Supervisor" /F
# or via Task Scheduler UI — no takeown/icacls gymnastics.
#
# The supervisor honors the durable desired-state flag: if the user ran
# `tbctl stop`, the task starts the supervisor but the worker stays stopped
# until `tbctl start`.
#
# Run (PowerShell, as the current user):
#     powershell -ExecutionPolicy Bypass -File .\install_windows_runtime.ps1

$ErrorActionPreference = "Stop"

$TaskName = "TB-Runtime-Supervisor"
$Repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # ...\larger-lab
$Supervisor = Join-Path $Repo "quant-lab\runtime\tb_supervisor.py"

if (-not (Test-Path $Supervisor)) {
    Write-Error "supervisor not found: $Supervisor"
    exit 1
}

$Py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Py) {
    $Py = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $Py) {
    Write-Error "python not found on PATH"
    exit 1
}

# Resolve python fully (python launcher 'py' may need -3; prefer python.exe)
if ($Py -like "*py.exe") {
    $Py = "$Py -3"
}

$Action = New-ScheduledTaskAction -Execute $Py -Argument "-u `"$Supervisor`"" `
    -WorkingDirectory $Repo
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "TB runtime logon task installed: $TaskName"
Write-Host "  python: $Py"
Write-Host "  supervisor: $Supervisor"
Write-Host "The supervisor will start at next logon. To start now: tbctl start"
