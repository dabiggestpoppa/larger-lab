# Search for TradingView exe across common locations
$searchPaths = @(
    "C:\Program Files",
    "C:\Program Files (x86)",
    "$env:LOCALAPPDATA",
    "$env:APPDATA",
    "C:\Users\wifik\Desktop",
    "C:\Users\wifik\AppData\Roaming"
)
foreach ($base in $searchPaths) {
    $found = Get-ChildItem $base -Recurse -Filter "TradingView.exe" -ErrorAction SilentlyContinue -Depth 3
    foreach ($f in $found) {
        Write-Output "FOUND: $($f.FullName)"
    }
}

# Check Start Menu shortcuts
$startMenu = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
    "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs"
)
foreach ($sm in $startMenu) {
    $lnks = Get-ChildItem $sm -Recurse -Filter "*TradingView*" -ErrorAction SilentlyContinue
    foreach ($l in $lnks) {
        Write-Output "SHORTCUT: $($l.FullName)"
    }
}
