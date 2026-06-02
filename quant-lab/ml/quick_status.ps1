$procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, @{
    Name='Type';Expression={
        $cmd = $_.CommandLine
        if ($cmd -match 'guardian') { 'GUARDIAN' }
        elseif ($cmd -match 'bridge') { 'BRIDGE' }
        elseif ($cmd -match 'p90') { 'P90' }
        elseif ($cmd -match 'symmetry|st_executor') { 'ST' }
        elseif ($cmd -match 'uvicorn|fastapi|oce') { 'OCE' }
        elseif ($cmd -match 'train') { 'TRAIN' }
        elseif ($cmd -match 'pytest|test') { 'TEST' }
        else { 'OTHER' }
    }
}, @{Name='Age';Expression={((Get-Date) - $_.CreationDate).ToString('hh:mm:ss')}}
$procs | Format-Table -AutoSize
