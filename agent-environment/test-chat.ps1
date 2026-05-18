$body = @{
    agentId = "1b4942de"
    text = "Test message from fix verification"
    type = "chat"
} | ConvertTo-Json -Compress

$r = Invoke-RestMethod -Uri 'http://localhost:9000/api/rooms/chat-room/messages' -Method POST -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$r | ConvertTo-Json -Depth 2
