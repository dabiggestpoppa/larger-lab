Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    
    public static void ForceForeground(IntPtr hWnd) {
        IntPtr fgHwnd = GetForegroundWindow();
        uint fgPid;
        uint fgThread = GetWindowThreadProcessId(fgHwnd, out fgPid);
        uint currentThread = GetCurrentThreadId();
        AttachThreadInput(currentThread, fgThread, true);
        SetForegroundWindow(hWnd);
        AttachThreadInput(currentThread, fgThread, false);
    }
}
"@

$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if (-not $proc) { Write-Output "MT5 not found"; exit }

$hwnd = $proc.MainWindowHandle
Write-Output "MT5: $($proc.MainWindowTitle)"

if ([Win32]::IsIconic($hwnd)) {
    [Win32]::ShowWindow($hwnd, 9)
    Start-Sleep -Milliseconds 500
}

[Win32]::ForceForeground($hwnd)
Start-Sleep -Seconds 1

$fg = [Win32]::GetForegroundWindow()
Write-Output "Foreground: $fg (MT5: $hwnd) - Match: $($fg -eq $hwnd)"

$rect = New-Object Win32+RECT
[Win32]::GetWindowRect($hwnd, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
Write-Output "Window: $($rect.Left),$($rect.Top) - $($rect.Right),$($rect.Bottom) (${width}x${height})"

# Screenshot before
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\at_before.png')
$graphics.Dispose()
$bitmap.Dispose()
Write-Output "Before screenshot saved"

# Click Algo Trading button
Write-Output "Clicking at (258, 48)..."
[Win32]::SetCursorPos(258, 48)
Start-Sleep -Milliseconds 300
[Win32]::mouse_event(0x0002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 100
[Win32]::mouse_event(0x0004, 0, 0, 0, 0)
Start-Sleep -Seconds 2

# Screenshot after
$bitmap2 = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics2 = [System.Drawing.Graphics]::FromImage($bitmap2)
$graphics2.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap2.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\at_after.png')
$graphics2.Dispose()
$bitmap2.Dispose()
Write-Output "After screenshot saved"
