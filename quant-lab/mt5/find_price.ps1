$file = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_executor.py"
$lines = Get-Content $file
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '"price":\s*price') {
        Write-Host "Line $($i+1): $($lines[$i].Trim())"
    }
}
