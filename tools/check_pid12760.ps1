$cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=12760").CommandLine
Write-Host "PID 12760 cmd: $cmd"
$f = Get-Item "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py"
Write-Host "File last write: $($f.LastWriteTime)"
Write-Host "File size: $($f.Length)"
