Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Native {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
}
"@

$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if (-not $proc) { Write-Output "MT5 not found"; exit }

$hwnd = $proc.MainWindowHandle
Write-Output "MT5 HWND: $hwnd"
[Native]::SetForegroundWindow($hwnd)
Start-Sleep -Seconds 1

# Click Algo Trading button
[Native]::SetCursorPos(258, 48)
Start-Sleep -Milliseconds 200
[Native]::mouse_event(0x0002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 50
[Native]::mouse_event(0x0004, 0, 0, 0, 0)
Write-Output "Clicked at (258, 48)"
Start-Sleep -Seconds 2

# Screenshot
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
