# Check for Microsoft Store TradingView
$packages = Get-AppxPackage -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*trading*" -or $_.Name -like "*Trading*" }
if ($packages) {
    $packages | ForEach-Object { Write-Output "STORE: $($_.Name) | $($_.InstallLocation) | $($_.PackageFullName)" }
} else {
    Write-Output "No TradingView UWP packages found"
}

# Check for electron apps in local data
$localData = "C:\Users\wifik\AppData\Local"
Get-ChildItem $localData -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*trading*" } | ForEach-Object { 
    Write-Output "LOCAL DIR: $($_.FullName)"
    Get-ChildItem $_.FullName -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue -Depth 3 | ForEach-Object { Write-Output "  EXE: $($_.FullName)" }
}

# Check if there's a TV Bridge or similar tool
Get-ChildItem "C:\Users\wifik\Desktop\projects\larger-lab" -Recurse -Filter "*bridge*" -ErrorAction SilentlyContinue -Depth 3 | Where-Object { $_.PSIsContainer } | ForEach-Object { Write-Output "BRIDGE DIR: $($_.FullName)" }
