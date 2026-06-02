' Launch bridge hidden, detached from any console
Set WshShell = CreateObject("WScript.Shell")
' Run hidden (0), don't wait (False)
WshShell.Run """C:\Users\wifik\AppData\Local\Programs\Python\Python311\python.exe"" ""C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live_bridge.py""", 0, False
Set WshShell = Nothing
