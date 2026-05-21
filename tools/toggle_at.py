"""Toggle MT5 AutoTrading by clicking the Algo Trading button."""
import subprocess
import time

# Use PowerShell to move mouse and click
# First bring MT5 to front, then click the Algo Trading button
ps_script = '''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Native {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
}
"@

# Find MT5
$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if (-not $proc) { Write-Output "MT5 not found"; exit }

$hwnd = $proc.MainWindowHandle
[Native]::SetForegroundWindow($hwnd)
Start-Sleep -Seconds 1

# Get window position
Add-Type -AssemblyName System.Windows.Forms
$rect = [System.Windows.Forms.Screen]::PrimaryScreen
# MT5 is fullscreen at 0,0

# Click Algo Trading button at approximately (258, 48)
[Native]::SetCursorPos(258, 48)
Start-Sleep -Milliseconds 200
[Native]::mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
Start-Sleep -Milliseconds 50
[Native]::mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP

Write-Output "Clicked Algo Trading button"
Start-Sleep -Seconds 2

# Take screenshot to verify
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_after_click.png')
$graphics.Dispose()
$bitmap.Dispose()
Write-Output "Screenshot saved"
'''

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\tools\toggle_at.ps1', 'w') as f:
    f.write(ps_script)

result = subprocess.run(
    ['powershell', '-NoProfile', '-File', r'C:\Users\wifik\Desktop\projects\larger-lab\tools\toggle_at.ps1'],
    capture_output=True, text=True, timeout=20
)
print(result.stdout)
if result.stderr:
    print(f"STDERR: {result.stderr}")
