# VM Configuration

Status: NOT EXECUTED

The requested audit requires a disposable Windows 11 VM. No disposable VM was available to this session.

Observed execution environment:
- Host shell: MINGW64_NT-10.0-26200
- Host-side PowerShell was available.
- `Get-VM` / Hyper-V PowerShell command: unavailable.
- Hyper-V VMMS service: absent.
- `VBoxManage`: unavailable.
- `vmrun`: unavailable.
- QEMU/libvirt tooling: unavailable.
- Windows Sandbox feature state: not collected because querying optional Windows features required elevation; elevation was not requested.

Required controls not established:
- CLEAN_BASELINE snapshot
- Disposable Windows 11 guest
- Throwaway guest account
- NAT-only guest networking
- Procmon/Sysmon/Process Explorer/TCPView capture in guest
- No shared clipboard, folders, mapped drives, or host credential mounts

Safety boundary:
- The sample was not extracted.
- The sample was not launched.
- No credentials, cookies, wallets, tokens, or profiles were supplied.
- No Defender/security controls were changed.
