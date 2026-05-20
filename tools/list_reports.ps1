Get-ChildItem 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports' | ForEach-Object {
    Write-Output "$($_.FullName) | $([math]::Round($_.Length/1KB,1)) KB | $($_.LastWriteTime)"
}
