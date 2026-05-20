$procs = Get-Process python -ErrorAction SilentlyContinue
if ($procs) {
    foreach ($p in $procs) {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine
        Write-Output "PID $($p.Id): $cmd"
    }
} else {
    Write-Output "No python processes running"
}
Write-Output "---"
$stateFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_forward_test_state.json"
if (Test-Path $stateFile) {
    Get-Content $stateFile
} else {
    Write-Output "No state file found"
}
