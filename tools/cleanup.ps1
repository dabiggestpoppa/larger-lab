$workspace = "C:\Users\wifik\Desktop\projects\larger-lab"

Write-Host "=== WORKSPACE CLEANUP ===" -ForegroundColor Cyan

# 1. Remove __pycache__ directories
$pycaches = Get-ChildItem -Path $workspace -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\.git*" }
$pyCount = 0
foreach ($d in $pycaches) {
    Remove-Item $d.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $pyCount++
}
Write-Host "Removed $pyCount __pycache__ dirs"

# 2. Remove .bak/.tmp/.swp files
$baks = Get-ChildItem -Path $workspace -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '\.(bak|tmp|swp)$' -and $_.FullName -notlike '*\.git*' -and $_.FullName -notlike '*\node_modules*' }
$bakCount = 0
foreach ($f in $baks) {
    Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue
    $bakCount++
}
Write-Host "Removed $bakCount .bak/.tmp/.swp files"

# 3. Remove .next cache
$nextDir = Join-Path $workspace ".next"
if (Test-Path $nextDir) {
    $sz = [math]::Round((Get-ChildItem $nextDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Remove-Item $nextDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Removed .next cache ($sz MB)"
}

# 4. Kill stale node processes (>2h old, not current)
$killed = 0
Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.Id -ne $PID -and (Get-Date) -gt $_.StartTime.AddHours(2)
} | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    $killed++
}
Write-Host "Killed $killed stale node processes"

# 5. Kill stale python (>2h old, not current)
$pk = 0
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Id -ne $PID -and (Get-Date) -gt $_.StartTime.AddHours(2)
} | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    $pk++
}
Write-Host "Killed $pk stale python processes"

Write-Host "=== CLEANUP COMPLETE ===" -ForegroundColor Green
