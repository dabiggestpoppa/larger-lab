Get-ChildItem 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5' -Filter '*.py' | ForEach-Object {
    Write-Output "$($_.Name) | $([math]::Round($_.Length/1KB,1)) KB | $($_.LastWriteTime)"
}
