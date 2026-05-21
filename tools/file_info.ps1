$f = Get-Item "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py"
Write-Host "Last write: $($f.LastWriteTime)"
Write-Host "Size: $($f.Length)"
