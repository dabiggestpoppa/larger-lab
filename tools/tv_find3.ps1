# Find TradingView Desktop exe
$regPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
foreach ($rp in $regPaths) {
    Get-ItemProperty $rp -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like "*TradingView*" } | Select-Object DisplayName, InstallLocation, UninstallString | Format-List | Out-String
}

# Also check if there's a running process we can get path from
Get-Process | Where-Object { $_.ProcessName -like "*trading*" -or $_.ProcessName -like "*Trading*" } | Select-Object Id, ProcessName, Path | Format-List | Out-String

# Check common Electron app locations
$electronPaths = @(
    "$env:LOCALAPPDATA\Programs",
    "$env:LOCALAPPDATA\Apps",
    "C:\Users\wifik\AppData\Local\Programs"
)
foreach ($ep in $electronPaths) {
    if (Test-Path $ep) {
        Get-ChildItem $ep -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*trading*" -or $_.Name -like "*Trading*" } | ForEach-Object { Write-Output "DIR: $($_.FullName)" }
    }
}
