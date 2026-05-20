$results = @()
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5 -UseBasicParsing
    $results += "OCE backend :8000 - UP (HTTP $($r.StatusCode))"
} catch {
    $results += "OCE backend :8000 - DOWN ($($_.Exception.Message))"
}
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8001/health' -TimeoutSec 5 -UseBasicParsing
    $results += "SRRA API :8001 - UP (HTTP $($r.StatusCode))"
} catch {
    $results += "SRRA API :8001 - DOWN ($($_.Exception.Message))"
}
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 5 -UseBasicParsing
    $results += "OCE frontend :3000 - UP (HTTP $($r.StatusCode))"
} catch {
    $results += "OCE frontend :3000 - DOWN ($($_.Exception.Message))"
}
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:3001' -TimeoutSec 5 -UseBasicParsing
    $results += "SRRA frontend :3001 - UP (HTTP $($r.StatusCode))"
} catch {
    $results += "SRRA frontend :3001 - DOWN ($($_.Exception.Message))"
}
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:9000' -TimeoutSec 5 -UseBasicParsing
    $results += "Agent env :9000 - UP (HTTP $($r.StatusCode))"
} catch {
    $results += "Agent env :9000 - DOWN ($($_.Exception.Message))"
}
$results | ForEach-Object { Write-Output $_ }

# Check forward test log
Write-Output "---FORWARD TEST---"
$logDir = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5"
$logs = Get-ChildItem $logDir -Filter "*.log" -ErrorAction SilentlyContinue
if ($logs) {
    foreach ($log in $logs) {
        Write-Output "Log: $($log.Name) | Size: $($log.Length) | Modified: $($log.LastWriteTime)"
        Get-Content $log.FullName -Tail 5 | ForEach-Object { Write-Output "  $_" }
    }
} else {
    Write-Output "No log files found in $logDir"
}

# Check forward test process
$ftProc = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 4016 }
if ($ftProc) {
    Write-Output "Forward test (PID 4016): RUNNING since $($ftProc.StartTime) | Mem: $([math]::Round($ftProc.WorkingSet64/1MB,1))MB"
} else {
    Write-Output "Forward test (PID 4016): NOT FOUND"
}
