Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Drawing;
using System.Drawing.Imaging;

public class MT5Capture {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, int nFlags);
    
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left, Top, Right, Bottom;
    }
    
    public static void CaptureWindow(IntPtr hWnd, string filename) {
        RECT rect;
        GetWindowRect(hWnd, out rect);
        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        
        Bitmap bmp = new Bitmap(width, height);
        Graphics g = Graphics.FromImage(bmp);
        IntPtr hdc = g.GetHdc();
        PrintWindow(hWnd, hdc, 0);
        g.ReleaseHdc(hdc);
        g.Dispose();
        bmp.Save(filename, ImageFormat.Png);
        bmp.Dispose();
    }
}
"@

$proc = Get-Process | Where-Object { $_.ProcessName -match 'terminal64' } | Select-Object -First 1
if ($proc) {
    $hwnd = $proc.MainWindowHandle
    Write-Output "Capturing MT5 window: $($proc.MainWindowTitle)"
    
    # Minimize other windows first - use Alt+Tab to get to MT5
    [MT5Capture]::SetForegroundWindow($hwnd)
    Start-Sleep -Milliseconds 500
    
    $filename = 'C:\Users\wifik\Desktop\projects\larger-lab\tools\mt5_window.png'
    [MT5Capture]::CaptureWindow($hwnd, $filename)
    Write-Output "Saved to $filename"
} else {
    Write-Output "MT5 not found"
}
