$r = Invoke-RestMethod -Uri 'http://localhost:9000/api/world'
Write-Output "=== AGENTS ==="
foreach ($a in $r.agents) {
    Write-Output "$($a.name) | online=$($a.online) | status=$($a.status) | room=$($a.currentRoom)"
}
Write-Output ""
Write-Output "=== ROOMS ==="
foreach ($rm in $r.rooms) {
    Write-Output "$($rm.name) | icon=$($rm.icon) | color=$($rm.color) | agents=$($rm.agentCount)"
}
Write-Output ""
Write-Output "=== ACTIVITY ==="
foreach ($e in $r.recentActivity) {
    Write-Output "$($e.agentId): $($e.action)"
}
