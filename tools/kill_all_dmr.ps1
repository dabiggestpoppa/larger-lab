Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
    if ($cmd -match "dmr_live_v2") {
        Write-Host "Killing PID $($_.Id): $($cmd.Substring(0, [Math]::Min(100, $cmd.Length)))"
        Stop-Process -Id $_.Id -Force
    }
}
Start-Sleep -Seconds 2
Write-Host "Done killing DMR processes"
