$procs = Get-Process -Name python -EA SilentlyContinue | Where-Object { $_.CommandLine -match 'guardian|bridge|p90|symmetry' }
if ($procs) {
    $procs | ForEach-Object {
        $type = if ($_.CommandLine -match 'guardian') { 'GUARDIAN' }
                elseif ($_.CommandLine -match 'bridge') { 'BRIDGE' }
                elseif ($_.CommandLine -match 'p90') { 'P90' }
                else { 'ST' }
        Write-Output "$type PID:$($_.ProcessId) Age:$((Get-Date)-$_.CreationDate)"
    }
} else {
    Write-Output "NO CEREBUS PROCESSES FOUND"
}
