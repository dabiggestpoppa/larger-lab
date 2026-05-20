$reports = Get-ChildItem 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports' -Filter 'DMR*'
foreach ($r in $reports) {
    Write-Output "$($r.FullName) | Size: $([math]::Round($r.Length/1KB,1)) KB | Modified: $($r.LastWriteTime)"
}
Write-Output "---"
$trades = Get-ChildItem 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5' -Filter 'dmr_trades_*'
foreach ($t in $trades) {
    Write-Output "$($t.FullName) | Size: $([math]::Round($t.Length/1KB,1)) KB"
}
