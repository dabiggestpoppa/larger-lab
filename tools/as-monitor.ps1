# AS Monitor Loop — Polls team-chat for CC entries
# Runs until CC posts a new message after the last known entry

$teamChat = "C:\Users\wifik\Desktop\projects\larger-lab\shared-conversations\team-chat.md"
$lastKnown = "2026-05-17 14:00 UTC"  # Last PM entry before AS cleanup
$pollSec = 30
$maxLoops = 240  # 2 hours max

Write-Host "=== AS MONITOR ACTIVE ===" 
Write-Host "Watching for CC entries after: $lastKnown"
Write-Host "Polling every ${pollSec}s (max ${maxLoops} loops / 2hr)"
Write-Host ""

for ($i = 0; $i -lt $maxLoops; $i++) {
    $content = Get-Content $teamChat -Raw -ErrorAction SilentlyContinue
    if (-not $content) { Start-Sleep -Seconds $pollSec; continue }

    # Find all CC entries with timestamps
    $ccEntries = [regex]::Matches($content, '##?\s+🔵\s+\[CC\].*?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+UTC)')
    
    $newEntries = @()
    foreach ($match in $ccEntries) {
        $ts = $match.Groups[1].Value
        if ($ts -gt $lastKnown) {
            $newEntries += $ts
        }
    }

    if ($newEntries.Count -gt 0) {
        Write-Host ""
        Write-Host "=== CC NEW ENTRY DETECTED ===" -ForegroundColor Green
        Write-Host "Timestamps: $($newEntries -join ', ')"
        Write-Host ""
        
        # Extract the new CC entry block
        $lines = $content -split "`n"
        $inCC = $false
        $ccBlock = @()
        foreach ($line in $lines) {
            if ($line -match '##?\s+🔵\s+\[CC\]') { $inCC = $true; $ccBlock = @($line); continue }
            if ($inCC) {
                if ($line -match '^---' -or $line -match '##\s+\w') { 
                    if ($ccBlock.Count -gt 1) { break } 
                }
                $ccBlock += $line
            }
        }
        $ccBlock | ForEach-Object { Write-Host $_ }
        Write-Host ""
        Write-Host "=== END CC ENTRY ===" -ForegroundColor Green
        
        # Signal file for AS to pick up
        $signalPath = "C:\Users\wifik\Desktop\projects\larger-lab\tools\cc-task-signal.txt"
        $ccBlock | Out-File $signalPath -Force
        Write-Host "Signal written to: $signalPath"
        break
    }

    if ($i % 10 -eq 0) {
        Write-Host "[$i] $(Get-Date -Format 'HH:mm:ss') — No new CC entries yet..."
    }
    Start-Sleep -Seconds $pollSec
}

Write-Host "Monitor loop complete."
