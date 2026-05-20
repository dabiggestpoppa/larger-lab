$results = Get-ChildItem 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab' -Recurse -Include '*.json','*.csv','*.md' | Where-Object { $_.Name -match 'tier|manual|injection|volatil|cluster|temporal|mc_|monte|dmr|backtest|result' } | Select-Object FullName, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}}, LastWriteTime | Format-Table -AutoSize
$results
