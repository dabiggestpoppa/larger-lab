Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 16172 } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
# Verify killed
$proc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 16172 }
if ($proc) { Write-Output "Still running!" } else { Write-Output "Killed successfully" }
