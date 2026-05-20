Get-ChildItem 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5' -Recurse | Select-Object FullName, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}}, LastWriteTime | Format-Table -AutoSize
