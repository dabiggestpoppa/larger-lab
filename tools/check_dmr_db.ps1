$dbFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db"
if (Test-Path $dbFile) {
    Write-Output "Database exists: $dbFile"
    Write-Output "Size: $((Get-Item $dbFile).Length) bytes"
} else {
    Write-Output "Database NOT found"
}

$stateFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
if (Test-Path $stateFile) {
    Write-Output "`nState file exists: $stateFile"
    Get-Content $stateFile -Raw
} else {
    Write-Output "`nState file NOT found"
}

$configFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
if (Test-Path $configFile) {
    Write-Output "`nConfig file:"
    Get-Content $configFile -Raw
}
