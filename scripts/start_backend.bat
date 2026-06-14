@echo off
cd /d C:\Users\wifik\Desktop\projects\larger-lab
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe -m uvicorn oce.backend.main:app --host 0.0.0.0 --port 8000 --log-level info
