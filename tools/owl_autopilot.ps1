# OWL Autopilot v3 — Full autonomous monitoring with rate limit handling
param([int]$IntervalSeconds = 300)
$ErrorActionPreference = "Continue"
$script:RateLimitUntil = [datetime]::MinValue

function Write-Log($msg) { $ts = Get-Date -Format "HH:mm:ss"; Write-Host "[$ts] $msg" }

function Test-ChaosRunning {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 10128 } | Select-Object -First 1
}

function Get-ChaosProgress {
    $log = "C:\Users\wifik\Desktop\projects\larger-lab\tools\testing\chaos\stability\chaos_20x_trace.log"
    if (Test-Path $log) { Get-Content $log -Tail 3 } else { "No trace log" }
}

function Get-ChaosResults {
    $json = "C:\Users\wifik\Desktop\projects\larger-lab\tools\testing\chaos\stability\chaos_20x_results.json"
    if (Test-Path $json) {
        try {
            $d = Get-Content $json -Raw | ConvertFrom-Json
            return "Cycles: $($d.total_cycles) | Amp: $($d.final_amplification) | Passed: $(($d.cycles | Where-Object { $_.passed }).Count)"
        } catch { return "Results file exists but can't parse" }
    }
    return "No results file"
}

Write-Log "=== OWL Autopilot v3 Started ==="
Write-Log "Monitoring chaos test PID 10128, interval ${IntervalSeconds}s"

while ($true) {
    $chaos = Test-ChaosRunning
    if ($chaos) {
        $progress = Get-ChaosProgress
        Write-Log "Chaos RUNNING | $($progress -join ' | ')"
    } else {
        Write-Log "Chaos test ENDED"
        $results = Get-ChaosResults
        Write-Log "Final results: $results"
        
        $json = "C:\Users\wifik\Desktop\projects\larger-lab\tools\testing\chaos\stability\chaos_20x_results.json"
        if (Test-Path $json) {
            $d = Get-Content $json -Raw | ConvertFrom-Json
            $passed = ($d.cycles | Where-Object { $_.passed }).Count
            $total = $d.total_cycles
            $amp = $d.final_amplification
            
            if ($passed -eq $total -and $total -gt 0) {
                Write-Log "ALL $total cycles PASSED at amp $amp! Phase 11.2 COMPLETE."
                Write-Log "Next: Phase 11.3 — Adversarial Drift & Identity Coherence Testing"
                "PHASE_11.2_COMPLETE: $total cycles, amp $amp" | Out-File "C:\Users\wifik\Desktop\projects\larger-lab\progress\phase-11.2-status.txt" -Force
            } else {
                Write-Log "Test ended with $passed/$total passed. May need investigation."
                "PHASE_11_2_INCOMPLETE: $passed/$total passed, amp $amp" | Out-File "C:\Users\wifik\Desktop\projects\larger-lab\progress\phase-11.2-status.txt" -Force
            }
        }
        break
    }
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Log "=== Autopilot cycle complete ==="
