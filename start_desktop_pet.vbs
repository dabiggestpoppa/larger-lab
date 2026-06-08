' Desktop Pet Launcher — Start the VTuber Desktop Pet
' Double-click to launch

Set objShell = CreateObject("WScript.Shell")

' Get the script's directory
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Activate the Python venv and run the desktop pet
objShell.Run "cmd /c cd /d """ & strPath & """ && call .venv\Scripts\activate.bat && python vtuber_integration\desktop_pet.py", 0, False

' Wait a moment
WScript.Sleep 2000

' Show a brief notification
MsgBox "Desktop Pet started! Look for the floating window.", vbInformation, "Desktop Pet"
