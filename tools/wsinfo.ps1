$root = "C:\Users\wifik\Desktop\projects\larger-lab"
$ws = Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue
$totalMB = [math]::Round(($ws | Measure-Object -Property Length -Sum).Sum/1MB, 1)
$totalFiles = $ws.Count
Write-Output "Workspace: $totalFiles files, $totalMB MB total"
$dirs = @("oce","srrs_opc","tools","skills",".agents/skills","projects","quant-lab","agent-environment","research","meditation-room","shared-conversations","progress")
foreach ($d in $dirs) {
    $p = Join-Path $root $d
    if (Test-Path $p) {
        $c = (Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue).Count
        Write-Output "  $d : $c files"
    }
}
