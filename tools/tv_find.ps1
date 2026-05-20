$paths = @(
    "$env:LOCALAPPDATA\TradingView",
    "$env:LOCALAPPDATA\Programs\TradingView",
    "C:\Program Files\TradingView",
    "C:\Program Files (x86)\TradingView",
    "$env:APPDATA\TradingView"
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Output "FOUND: $p"
        Get-ChildItem $p -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object FullName | ForEach-Object { Write-Output "  $($_.FullName)" }
    }
}
# Also search running processes for their path
Get-Process -Name "TradingView" -ErrorAction SilentlyContinue | Select-Object Id, Path | ForEach-Object { Write-Output "RUNNING: PID=$($_.Id) Path=$($_.Path)" }
