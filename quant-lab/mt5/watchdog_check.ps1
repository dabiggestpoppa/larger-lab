$results = @()

# Check guardian
$g = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match 'cerebus_guardian' }
if ($g) { $results += 'GUARDIAN_RUNNING pid=' + $g.ProcessId } else { $results += 'GUARDIAN_DEAD' }

# Check executors
$p90 = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match 'p90_cascade_executor' }
if ($p90) { $results += 'P90_RUNNING pid=' + $p90.ProcessId } else { $results += 'P90_DEAD' }

$st = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match 'symmetry_trap_executor' }
if ($st) { $results += 'ST_RUNNING pid=' + $st.ProcessId } else { $results += 'ST_DEAD' }

$bridge = Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -match 'cerebus_live_bridge' }
if ($bridge) { $results += 'BRIDGE_RUNNING pid=' + $bridge.ProcessId } else { $results += 'BRIDGE_DEAD' }

$results -join "`n"
