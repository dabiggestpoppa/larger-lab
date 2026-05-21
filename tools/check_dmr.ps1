$procs = Get-Process python -ErrorAction SilentlyContinue
$dmr = $procs | Where-Object { $_.MainWindowTitle -match 'dmr' -or $_.CommandLine -match 'dmr_live' }
if (-not $dmr) {
    # Try broader match
    $dmr = $procs | Where-Object { $_.CommandLine -match 'mt5' }
}
if ($dmr) {
    Write-Output "DMR-related processes:"
    $dmr | Format-Table Id, ProcessName, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} -AutoSize
} else {
    Write-Output "No DMR process found. All python processes:"
    $procs | Format-Table Id, ProcessName, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} -AutoSize
}
