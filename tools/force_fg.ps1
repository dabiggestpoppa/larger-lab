Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Native {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern short VkKeyScan(char ch);
}
"@

# Find MT5
$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if (-not $proc) { Write-Output "MT5 not found"; exit }

$hwnd = $proc.MainWindowHandle
Write-Output "MT5: $($proc.MainWindowTitle) HWND: $hwnd"

# Restore if minimized
if ([Native]::IsIconic($hwnd)) {
    [Native]::ShowWindow($hwnd, 9)
    Start-Sleep -Milliseconds 500
}

# Force foreground using thread attachment
$fgHwnd = [Native]::GetForegroundWindow()
$currentThread = [Native]::GetCurrentThreadId()
$fgThread = [Native]::GetWindowThreadProcessId($fgHwnd, [IntPtr]::Zero)
[Native]::AttachThreadInput($currentThread, $fgThread, $true)
[Native]::SetForegroundWindow($hwnd)
[Native]::AttachThreadInput($currentThread, $fgThread, $false)
Start-Sleep -Seconds 1

# Verify
$fg = [Native]::GetForegroundWindow()
Write-Output "Foreground window: $fg (MT5 is $hwnd)"

# Take screenshot to confirm MT5 is visible
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_fg_check.png')
$graphics.Dispose()
$bitmap.Dispose()
Write-Output "Screenshot saved"
