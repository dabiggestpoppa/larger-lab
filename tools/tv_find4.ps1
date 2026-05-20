# Search entire system for TradingView.exe
Get-ChildItem "C:\" -Recurse -Filter "TradingView.exe" -ErrorAction SilentlyContinue -Depth 4 | Select-Object FullName, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}} | Format-Table -AutoSize | Out-String
