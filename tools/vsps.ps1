Get-Process -Name 'Code' | Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, @{N='Threads';E={$_.Threads.Count}} | Format-Table -AutoSize
