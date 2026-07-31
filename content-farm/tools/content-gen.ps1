# Content Farm — Batch Media Generator
# Usage: .\tools\content-gen.ps1
# Or from another script: node tools/generate.mjs --prompt "..." --output "..."

param(
    [string]$Prompt,
    [string]$Output = "output.png",
    [string]$Width = "1024",
    [string]$Height = "1024",
    [string]$Provider = "pollinations",
    [string]$Model = "google/gemini-2.5-flash-image"
)

$ErrorActionPreference = "Stop"

$cmdArgs = @(
    "tools/generate.mjs",
    "--prompt", $Prompt,
    "--output", $Output,
    "--width", $Width,
    "--height", $Height,
    "--provider", $Provider
)

if ($Model -ne "google/gemini-2.5-flash-image") {
    $cmdArgs += @("--model", $Model)
}

Write-Host "[content-farm] Running: node $cmdArgs" -ForegroundColor Cyan
& node @cmdArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "[content-farm] Success!" -ForegroundColor Green
} else {
    Write-Host "[content-farm] Failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
