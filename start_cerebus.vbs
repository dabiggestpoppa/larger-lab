' CEREBUS 24/7 Starter - Completely hidden, no windows
Set WshShell = CreateObject("WScript.Shell")
repo = "C:\Users\wifik\Desktop\projects\larger-lab"
py = repo & "\.venv\Scripts\python.exe"

' Start each scanner completely hidden (0 = hidden window)
WshShell.Run """" & py & """ -m oce.backend.main", 0, False
WScript.Sleep 3000
WshShell.Run """" & py & """ scripts/telegram_gateway.py", 0, False
WScript.Sleep 3000
WshShell.Run """" & py & """ quant-lab/ml/run_cerebus_live.py --interval 300 --engine both", 0, False
WScript.Sleep 3000
WshShell.Run """" & py & """ quant-lab/mlr_validation/mlr_scanner.py", 0, False
WScript.Sleep 3000
WshShell.Run """" & py & """ scripts/signal_bot.py", 0, False
