Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Native {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
}
"@

# Find MT5
$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if (-not $proc) { Write-Output "MT5 not found"; exit }

$hwnd = $proc.MainWindowHandle
Write-Output "MT5: $($proc.MainWindowTitle)"

# Restore if minimized, then force foreground
if ([Native]::IsIconic($hwnd)) {
    [Native]::ShowWindow($hwnd, 9)
    Start-Sleep -Milliseconds 500
}

# Use a more aggressive approach: minimize all other windows first
# Press Win+M to minimize all, then restore only MT5
# Actually, let's just use SetForegroundWindow with a retry
for ($i = 0; $i -lt 5; $i++) {
    [Native]::SetForegroundWindow($hwnd)
    Start-Sleep -Milliseconds 500
    $fg = [Native]::GetForegroundWindow()
    if ($fg -eq $hwnd) {
        Write-Output "MT5 is now foreground (attempt $($i+1))"
        break
    }
}

Start-Sleep -Seconds 1

# Get the window rect to verify position
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Take screenshot before click
$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_before_click.png')
$graphics.Dispose()
$bitmap.Dispose()
Write-Output "Before-click screenshot saved"

# Click Algo Trading button at (258, 48)
Write-Output "Moving cursor to (258, 48)..."
[Native]::SetCursorPos(258, 48)
Start-Sleep -Milliseconds 300
[Native]::mouse_event(0x0002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 100
[Native]::mouse_event(0x0004, 0, 0, 0, 0)
Write-Output "Clicked!"
Start-Sleep -Seconds 2

# Take screenshot after click
$bitmap2 = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics2 = [System.Drawing.Graphics]::FromImage($bitmap2)
$graphics2.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap2.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_after_click2.png')
$graphics2.Dispose()
$bitmap2.Dispose()
Write-Output "After-click screenshot saved"
