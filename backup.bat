@echo off
REM Quick backup wrapper - bypasses execution policy
powershell -ExecutionPolicy Bypass -File "%~dp0backup-workspace.ps1" %*