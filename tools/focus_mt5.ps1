Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);
}
"@

$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if ($proc) {
    $hwnd = $proc.MainWindowHandle
    Write-Output "MT5 HWND: $hwnd"
    Write-Output "Title: $($proc.MainWindowTitle)"
    
    # Restore if minimized
    if ([Win32]::IsIconic($hwnd)) {
        [Win32]::ShowWindow($hwnd, 9)  # SW_RESTORE
        Write-Output "Restored minimized window"
    }
    
    # Bring to front
    [Win32]::SetForegroundWindow($hwnd)
    Write-Output "Brought to foreground"
    
    Start-Sleep -Seconds 2
    
    # Take screenshot
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bounds = $screen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $bitmap.Save('C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_focused.png')
    $graphics.Dispose()
    $bitmap.Dispose()
    Write-Output "Screenshot saved"
} else {
    Write-Output "MT5 not found"
}
