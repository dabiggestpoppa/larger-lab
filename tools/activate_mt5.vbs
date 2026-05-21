Set objShell = CreateObject("WScript.Shell")
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")

' Find MT5 process
Set colProcesses = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE Name LIKE '%terminal64%'")
For Each objProcess In colProcesses
    WScript.Echo "Found MT5: " & objProcess.ProcessId
Next

' Use AppActivate to bring MT5 to front
On Error Resume Next
objShell.AppActivate "650898"
If Err.Number <> 0 Then
    objShell.AppActivate "OxSecurities"
End If
On Error GoTo 0

WScript.Sleep 1000

' Click at the Algo Trading button position
' MT5 toolbar: Algo Trading button is typically at x=258, y=48
Set objMouse = CreateObject("WScript.Shell")
' Use SendKeys to send Alt+T (Tools menu) then look for Algo Trading
' Actually, let's try a different approach - use the MT5 hotkey
' Ctrl+Shift+A is sometimes used, but not standard

' Let's try clicking using a helper
WScript.Echo "MT5 activated, ready to click"
