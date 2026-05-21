$workspace = "C:\Users\wifik\Desktop\projects\larger-lab"
Write-Host "=== FULL WORKSPACE CLEANUP ===" -ForegroundColor Cyan

# 1. __pycache__
$py = Get-ChildItem -Path $workspace -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "__pycache__" -and $_.FullName -notlike "*\.git*" }
$c = 0; foreach ($d in $py) { Remove-Item $d.FullName -Recurse -Force -EA SilentlyContinue; $c++ }
Write-Host "pycache removed: $c"

# 2. .bak/.tmp/.swp
$exts = @('.bak','.tmp','.swp')
$files = Get-ChildItem -Path $workspace -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $exts -contains $_.Extension -and $_.FullName -notlike '*\.git*' -and $_.FullName -notlike '*\node_modules*' }
$c2 = 0; foreach ($f in $files) { Remove-Item $f.FullName -Force -EA SilentlyContinue; $c2++ }
Write-Host "bak/tmp removed: $c2"

# 3. .next
$nd = Join-Path $workspace ".next"
if (Test-Path $nd) { $sz=[math]::Round((Get-ChildItem $nd -Recurse -File -EA SilentlyContinue|Measure-Object -Property Length -Sum).Sum/1MB,1); Remove-Item $nd -Recurse -Force -EA SilentlyContinue; Write-Host "Removed .next ($sz MB)" } else { Write-Host ".next: not found (clean)" }

# 4. Stale node (>2h)
$k=0; Get-Process node -EA SilentlyContinue | Where-Object { $_.Id -ne $PID -and (Get-Date).Subtract($_.StartTime).TotalHours -gt 2 } | ForEach-Object { Stop-Process -Id $_.Id -Force -EA SilentlyContinue; $k++ }
Write-Host "Stale node killed: $k"

# 5. Stale python (>2h)
$p=0; Get-Process python -EA SilentlyContinue | Where-Object { $_.Id -ne $PID -and (Get-Date).Subtract($_.StartTime).TotalHours -gt 2 } | ForEach-Object { Stop-Process -Id $_.Id -Force -EA SilentlyContinue; $p++ }
Write-Host "Stale python killed: $p"

# 6. Summary
$totalFiles = (Get-ChildItem -Path $workspace -Recurse -File -EA SilentlyContinue | Measure-Object).Count
$totalDirs = (Get-ChildItem -Path $workspace -Recurse -Directory -EA SilentlyContinue | Measure-Object).Count
Write-Host "Workspace: $totalFiles files, $totalDirs dirs"
Write-Host "=== DONE ===" -ForegroundColor Green
