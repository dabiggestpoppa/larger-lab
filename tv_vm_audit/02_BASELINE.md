# Baseline

Status: NOT CAPTURED

A guest baseline could not be captured because no disposable Windows 11 VM was available. No host baseline is substituted for the requested guest baseline.

Unavailable runtime baseline items:
- Running processes
- Services
- Scheduled tasks
- Startup entries and Run/RunOnce keys
- Defender configuration
- Installed applications
- Listening ports and active TCP connections
- Browser profile directories
- AppData, ProgramData, and TEMP listings
- Hosts file
- DNS cache
- Relevant Windows event logs

Static pre-execution facts collected on the host:
- The source is a 137,495,959-byte outer ZIP.
- It contains one nested ZIP entry named `TradingView_Premium_Desktop_(password_github).zip`.
- The nested ZIP contains an executable named `TradingView Premium Desktop.exe` with the expected size and SHA-256.
- The nested ZIP also contains DLLs including `libx264-142.dll`, `openvr_api.dll`, and `libswscale-8.dll`.
- The nested ZIP inventory includes numerous Linux-style filesystem/package paths (for example `usbutils/`, `pam/`, `etc/`, `usr/`, and `var/`). This is an unusual packaging observation, not proof of execution or maliciousness.
