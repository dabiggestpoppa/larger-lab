' CEREBUS 24/7 Hidden Launcher
Set WshShell = CreateObject("WScript.Shell")
repo = "C:\Users\wifik\Desktop\projects\larger-lab"
python = repo & "\.venv\Scripts\python.exe"

WshShell.Run "cmd /c """ & python & """ -m oce.backend.main", 1, False
WScript.Sleep 2000
WshShell.Run "cmd /c """ & python & """ scripts/telegram_gateway.py", 1, False
WScript.Sleep 2000
WshShell.Run "cmd /c """ & python & """ quant-lab/ml/run_cerebus_live.py --interval 300 --engine both", 1, False
WScript.Sleep 3000
WshShell.Run "cmd /c """ & python & """ quant-lab/mlr_validation/mlr_scanner.py", 1, False
WScript.Sleep 2000
WshShell.Run "cmd /c """ & python & """ scripts/signal_bot.py", 1, False
