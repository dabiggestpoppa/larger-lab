Get-Process -Name python -EA SilentlyContinue | Select-Object ProcessId, Id, WorkingSet64, StartTime | Format-Table -AutoSize
