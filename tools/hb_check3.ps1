$tv = Get-Process -Name "TradingView" -ErrorAction SilentlyContinue
if ($tv) {
    $tv | ForEach-Object { Write-Output "TradingView PID=$($_.Id) Mem=$([math]::Round($_.WorkingSet64/1MB,1))MB" }
} else {
    Write-Output "TradingView: NOT RUNNING"
}

# Check TV MCP
$tvMcp = "C:\Users\wifik\Desktop\projects\larger-lab\tools\tradingview-mcp"
Write-Output "TV MCP package.json: $(Test-Path "$tvMcp\package.json")"
Write-Output "TV MCP node_modules: $(Test-Path "$tvMcp\node_modules")"
Write-Output "TV MCP server.js: $(Test-Path "$tvMcp\server.js")"

# Check PineScript
$ps = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\conversions\pinescript\CEREBUS_V5_WITH_DMR.pine"
if (Test-Path $ps) {
    $info = Get-Item $ps
    Write-Output "CEREBUS_V5_WITH_DMR.pine: EXISTS | Size: $($info.Length) | Modified: $($info.LastWriteTime)"
} else {
    Write-Output "CEREBUS_V5_WITH_DMR.pine: NOT FOUND"
}

# Check config
$config = "C:\Users\wifik\Desktop\projects\larger-lab\config\tradingview-mcp.json"
Write-Output "TV MCP config: $(Test-Path $config)"
