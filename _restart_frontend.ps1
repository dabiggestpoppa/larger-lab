$ErrorActionPreference = "SilentlyContinue"
Get-Process -Name node | Stop-Process -Force
Start-Sleep -Seconds 3
Remove-Item -Recurse -Force "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend\.next" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend\node_modules\.cache" -ErrorAction SilentlyContinue
Set-Location "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend"
npm run build 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "BUILD SUCCESS - Starting production server..."
    Start-Process -WindowStyle Hidden -FilePath "npm" -ArgumentList "run start -- -p 3000" -WorkingDirectory "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend"
    Start-Sleep -Seconds 5
    Write-Host "Frontend should be running on http://localhost:3000"
} else {
    Write-Host "BUILD FAILED"
}
