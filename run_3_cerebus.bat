@echo off
cd /d C:\Users\wifik\Desktop\projects\larger-lab
start "CEREBUS" /B .venv\Scripts\python.exe quant-lab/ml/run_cerebus_live.py --interval 300 --engine both
