@echo off
REM Quick restore wrapper - bypasses execution policy
powershell -ExecutionPolicy Bypass -File "%~dp0restore-workspace.ps1" %*