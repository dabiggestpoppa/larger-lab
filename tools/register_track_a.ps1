$task = @{
    task_type = "monitor"
    source = "owl-track-a"
    priority = 1
    max_retries = 0
    timeout_sec = 0
    tags = @("track-a", "ninjascript", "cerebus")
    payload = @{
        name = "Track A - NinjaScript Build"
        description = "Monitor Track A deliverables"
        steps = @(
            @{ id = 1; name = "Crypto Scanner"; status = "done"; file = "crypto/CryptoAssetScanner.py" },
            @{ id = 2; name = "ST NinjaScript"; status = "done"; file = "tradovate/CEREBUS_ST_NT8.cs" },
            @{ id = 3; name = "P90 NinjaScript"; status = "done"; file = "tradovate/CEREBUS_P90_NT8.cs" },
            @{ id = 4; name = "NT8 Backtest Harness"; status = "pending" },
            @{ id = 5; name = "Deployment Config"; status = "pending" },
            @{ id = 6; name = "Trade Copier Bridge"; status = "pending" },
            @{ id = 7; name = "Multi-Asset Config"; status = "pending" }
        )
    }
} | ConvertTo-Json -Depth 5

$resp = Invoke-RestMethod -Uri "http://localhost:8000/execution/submit" -Method POST -Body $task -ContentType "application/json" -TimeoutSec 10
Write-Host "Task registered:"
$resp | ConvertTo-Json -Depth 3
