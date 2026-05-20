# Check Windows Apps (Microsoft Store apps)
$windowsApps = "C:\Program Files\WindowsApps"
if (Test-Path $windowsApps) {
    Get-ChildItem $windowsApps -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*trading*" -or $_.Name -like "*Trading*" } | ForEach-Object { Write-Output "STORE APP: $($_.FullName)" }
}

# Check Start Menu shortcuts
$startPaths = @(
    "C:\Users\wifik\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
    "C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
)
foreach ($sp in $startPaths) {
    Get-ChildItem $sp -Recurse -Filter "*.lnk" -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*trading*" -or $_.Name -like "*Trading*" } | ForEach-Object { Write-Output "SHORTCUT: $($_.FullName)" }
}

# Check Desktop
$desktop = "C:\Users\wifik\Desktop"
Get-ChildItem $desktop -Filter "*trading*" -ErrorAction SilentlyContinue | ForEach-Object { Write-Output "DESKTOP: $($_.FullName)" }
Get-ChildItem "$env:PUBLIC\Desktop" -Filter "*trading*" -ErrorAction SilentlyContinue | ForEach-Object { Write-Output "PUBLIC DESKTOP: $($_.FullName)" }

# Check if it's in PATH
$env:PATH -split ";" | Where-Object { $_ -like "*trading*" -or $_ -like "*Trading*" } | ForEach-Object { Write-Output "PATH: $_" }
