Get-Process | Where-Object { $_.ProcessName -match 'mt5|terminal' } | Select-Object Id, ProcessName, MainWindowTitle
