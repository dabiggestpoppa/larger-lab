$file = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_executor.py"
$lines = Get-Content $file
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i].Trim()
    if ($line -match '\bprice\b' -and $line -notmatch 'order_price' -and $line -notmatch 'entry_price' -and $line -notmatch 'check_price' -and $line -notmatch 'sl_price' -and $line -notmatch 'tp_price' -and $line -notmatch 'swing_origin' -and $line -notmatch 'imp_' -and $line -notmatch '#' -and $line -notmatch "'price'" -and $line -notmatch 'price_to' -and $line -notmatch 'price_') {
        Write-Host "Line $($i+1): $line"
    }
}
