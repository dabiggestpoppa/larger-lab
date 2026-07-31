/**
 * System Operator — Phase 1
 * 
 * Gives OpenClaw full system-level control via shell commands,
 * process management, and resource monitoring.
 * 
 * Windows-first: PowerShell + winget
 * All tools return { success: boolean, ...data }
 * 
 * Usage:
 *   const operator = require('./system-operator');
 *   const result = await operator.system_run_command('Get-Process | Select-Object -First 5');
 *   const resources = await operator.system_get_resources();
 */

const { exec, execSync, spawn } = require('child_process');
const { promisify } = require('util');
const os = require('os');
const fs = require('fs');
const path = require('path');

const execAsync = promisify(exec);

// ── Helpers ──────────────────────────────────────────────────────────────────

const IS_WINDOWS = os.platform() === 'win32';
const IS_MAC = os.platform() === 'darwin';
const IS_LINUX = os.platform() === 'linux';

/**
 * Execute a shell command and return structured result.
 * @param {string} command - Command to execute
 * @param {object} options - Options (timeout, cwd, shell)
 * @returns {Promise<{success: boolean, stdout: string, stderr: string, exitCode: number}>}
 */
async function runCommand(command, options = {}) {
    const timeout = options.timeout || 30000;
    const cwd = options.cwd || process.cwd();
    const shell = options.shell || (IS_WINDOWS ? 'powershell.exe' : '/bin/bash');

    try {
        const { stdout, stderr } = await execAsync(command, {
            cwd,
            timeout,
            shell,
            maxBuffer: 10 * 1024 * 1024, // 10MB buffer
            encoding: 'utf8',
        });
        return {
            success: true,
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: 0,
        };
    } catch (error) {
        return {
            success: false,
            stdout: (error.stdout || '').trim(),
            stderr: (error.stderr || '').trim(),
            exitCode: error.code || 1,
            error: error.message,
        };
    }
}

/**
 * Execute a long-running command with streaming output.
 * @param {string} command - Command to execute
 * @param {function} onOutput - Callback for each line of output
 * @returns {Promise<{success: boolean, exitCode: number}>}
 */
function runCommandStreaming(command, onOutput) {
    return new Promise((resolve) => {
        const shell = IS_WINDOWS ? 'powershell.exe' : '/bin/bash';
        const child = spawn(shell, ['-Command', command], {
            cwd: process.cwd(),
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        let exited = false;

        child.stdout.on('data', (data) => {
            const lines = data.toString().split('\n').filter(l => l.trim());
            lines.forEach(line => onOutput && onOutput('stdout', line));
        });

        child.stderr.on('data', (data) => {
            const lines = data.toString().split('\n').filter(l => l.trim());
            lines.forEach(line => onOutput && onOutput('stderr', line));
        });

        child.on('close', (code) => {
            if (!exited) {
                exited = true;
                resolve({ success: code === 0, exitCode: code });
            }
        });

        child.on('error', (err) => {
            if (!exited) {
                exited = true;
                resolve({ success: false, exitCode: 1, error: err.message });
            }
        });
    });
}

// ── Tool: system_run_command ─────────────────────────────────────────────────

/**
 * Execute a shell command.
 * @param {string} command - Command to execute
 * @param {number} timeout - Timeout in ms (default: 30000)
 * @param {string} cwd - Working directory
 * @returns {Promise<object>}
 */
async function system_run_command(command, timeout = 30000, cwd = null) {
    return runCommand(command, { timeout, cwd });
}

// ── Tool: system_run_script ──────────────────────────────────────────────────

/**
 * Create and run a temporary script.
 * @param {string} scriptContent - Script content
 * @param {string} extension - File extension (.ps1, .sh, .bat)
 * @param {number} timeout - Timeout in ms
 * @returns {Promise<object>}
 */
async function system_run_script(scriptContent, extension = null, timeout = 30000) {
    const ext = extension || (IS_WINDOWS ? '.ps1' : '.sh');
    const tmpDir = path.join(os.tmpdir(), 'operator-scripts');
    fs.mkdirSync(tmpDir, { recursive: true });
    const scriptPath = path.join(tmpDir, `script-${Date.now()}${ext}`);
    fs.writeFileSync(scriptPath, scriptContent, 'utf-8');

    try {
        const result = await runCommand(scriptPath, { timeout });
        // Cleanup
        try { fs.unlinkSync(scriptPath); } catch (e) { /* ignore */ }
        return result;
    } catch (error) {
        try { fs.unlinkSync(scriptPath); } catch (e) { /* ignore */ }
        return { success: false, error: error.message, exitCode: 1 };
    }
}

// ── Tool: system_list_processes ──────────────────────────────────────────────

/**
 * List running processes.
 * @param {string} filter - Optional filter by name
 * @returns {Promise<{success: boolean, processes: Array}>}
 */
async function system_list_processes(filter = null) {
    try {
        let command;
        if (IS_WINDOWS) {
            command = filter
                ? `Get-Process -Name "*${filter}*" | Select-Object Id, ProcessName, @{N='CPU(s)';E={[math]::Round($_.CPU,1)}}, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-List`
                : `Get-Process | Select-Object Id, ProcessName, @{N='CPU(s)';E={[math]::Round($_.CPU,1)}}, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-List`;
        } else {
            command = filter
                ? `ps aux | grep -i "${filter}" | grep -v grep`
                : `ps aux --sort=-%mem | head -20`;
        }

        const result = await runCommand(command);
        if (!result.success) return result;

        // Parse Windows output into structured array
        if (IS_WINDOWS) {
            const processes = [];
            const blocks = result.stdout.split('\n\n').filter(b => b.trim());
            for (const block of blocks) {
                const proc = {};
                for (const line of block.split('\n')) {
                    const match = line.match(/^\s*(\w+)\s*:\s*(.+)/);
                    if (match) proc[match[1].trim()] = match[2].trim();
                }
                if (Object.keys(proc).length > 0) processes.push(proc);
            }
            return { success: true, processes, count: processes.length };
        }

        return { success: true, stdout: result.stdout, raw: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: system_kill_process ────────────────────────────────────────────────

/**
 * Kill a process by PID or name.
 * @param {number|string} target - PID or process name
 * @returns {Promise<object>}
 */
async function system_kill_process(target) {
    try {
        let command;
        if (IS_WINDOWS) {
            if (typeof target === 'number' || /^\d+$/.test(target)) {
                command = `Stop-Process -Id ${target} -Force`;
            } else {
                command = `Stop-Process -Name "${target}" -Force`;
            }
        } else {
            if (typeof target === 'number' || /^\d+$/.test(target)) {
                command = `kill -9 ${target}`;
            } else {
                command = `pkill -9 "${target}"`;
            }
        }
        return await runCommand(command);
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: system_get_resources ───────────────────────────────────────────────

/**
 * Get system resource usage (CPU, memory, disk, network).
 * @returns {Promise<object>}
 */
async function system_get_resources() {
    try {
        const result = {};

        // CPU
        if (IS_WINDOWS) {
            const cpuInfo = await runCommand(
                `Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, LoadPercentage | Format-List`
            );
            result.cpu = cpuInfo.success ? cpuInfo.stdout : 'N/A';

            const memInfo = await runCommand(
                `$os = Get-CimInstance Win32_OperatingSystem; [PSCustomObject]@{TotalGB=[math]::Round($os.TotalVisibleMemorySize/1MB,2); FreeGB=[math]::Round($os.FreePhysicalMemory/1MB,2); UsedGB=[math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB,2); UsagePct=[math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100,1)} | Format-List`
            );
            result.memory = memInfo.success ? memInfo.stdout : 'N/A';

            const diskInfo = await runCommand(
                `Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, @{N='TotalGB';E={[math]::Round($_.Size/1GB,2)}}, @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,2)}}, @{N='UsedPct';E={[math]::Round(($_.Size-$_.FreeSpace)/$_.Size*100,1)}} | Format-List`
            );
            result.disk = diskInfo.success ? diskInfo.stdout : 'N/A';

            const netInfo = await runCommand(
                `Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" | Select-Object Description, @{N='IPAddress';E={$_.IPAddress -join ', '}}, @{N='Gateway';E={$_.DefaultIPGateway -join ', '}} | Format-List`
            );
            result.network = netInfo.success ? netInfo.stdout : 'N/A';

            const uptimeInfo = await runCommand(
                `$uptime = (Get-Date) - $os.LastBootUpTime; "{0}d {1}h {2}m" -f $uptime.Days, $uptime.Hours, $uptime.Minutes`
            );
            result.uptime = uptimeInfo.success ? uptimeInfo.stdout : 'N/A';
        } else {
            const cpuInfo = await runCommand("top -l 1 | head -10");
            result.cpu = cpuInfo.success ? cpuInfo.stdout : 'N/A';

            const memInfo = await runCommand("vm_stat");
            result.memory = memInfo.success ? memInfo.stdout : 'N/A';

            const diskInfo = await runCommand("df -h /");
            result.disk = diskInfo.success ? diskInfo.stdout : 'N/A';

            const uptimeInfo = await runCommand("uptime");
            result.uptime = uptimeInfo.success ? uptimeInfo.stdout : 'N/A';
        }

        result.platform = os.platform();
        result.hostname = os.hostname();
        result.timestamp = new Date().toISOString();

        return { success: true, ...result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: system_install_package ─────────────────────────────────────────────

/**
 * Install a package using the system's package manager.
 * @param {string} packageName - Package to install
 * @param {string} manager - Package manager (auto-detected if not specified)
 * @returns {Promise<object>}
 */
async function system_install_package(packageName, manager = null) {
    try {
        let command;
        const mgr = manager || detectPackageManager();

        switch (mgr) {
            case 'winget':
                command = `winget install --accept-package-agreements --accept-source-agreements "${packageName}"`;
                break;
            case 'choco':
                command = `choco install ${packageName} -y`;
                break;
            case 'brew':
                command = `brew install ${packageName}`;
                break;
            case 'apt':
                command = `sudo apt-get install -y ${packageName}`;
                break;
            case 'npm':
                command = `npm install -g ${packageName}`;
                break;
            case 'pip':
                command = `pip install ${packageName}`;
                break;
            default:
                return { success: false, error: `No package manager detected. Supported: winget, choco, brew, apt, npm, pip` };
        }

        return await runCommand(command, { timeout: 120000 }); // 2 min timeout for installs
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Detect the system's package manager.
 * @returns {string}
 */
function detectPackageManager() {
    if (IS_WINDOWS) {
        try {
            execSync('winget --version', { stdio: 'pipe' });
            return 'winget';
        } catch (e) {
            try {
                execSync('choco --version', { stdio: 'pipe' });
                return 'choco';
            } catch (e2) {
                return 'winget'; // default
            }
        }
    }
    if (IS_MAC) return 'brew';
    if (IS_LINUX) return 'apt';
    return 'unknown';
}

// ── Tool: system_cron_manage ─────────────────────────────────────────────────

/**
 * Manage cron jobs / scheduled tasks.
 * @param {string} action - 'list', 'add', 'remove'
 * @param {object} options - Options for add/remove
 * @returns {Promise<object>}
 */
async function system_cron_manage(action, options = {}) {
    try {
        if (IS_WINDOWS) {
            switch (action) {
                case 'list':
                    return await runCommand('Get-ScheduledTask | Where-Object {$_.State -ne "Disabled"} | Select-Object TaskName, State, @{N="NextRun";E={(Get-ScheduledTaskInfo $_).NextRunTime}} | Format-List');
                case 'add': {
                    const { name, command, schedule = 'DAILY', time = '09:00' } = options;
                    if (!name || !command) return { success: false, error: 'name and command required' };
                    const psCommand = `
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command \\"${command}\\""
$trigger = New-ScheduledTaskTrigger -${schedule} -At "${time}"
Register-ScheduledTask -TaskName "${name}" -Action $action -Trigger $trigger -Description "Operator-managed task"
`;
                    return await runCommand(psCommand);
                }
                case 'remove': {
                    const { name } = options;
                    if (!name) return { success: false, error: 'name required' };
                    return await runCommand(`Unregister-ScheduledTask -TaskName "${name}" -Confirm:$false`);
                }
                default:
                    return { success: false, error: `Unknown action: ${action}. Use: list, add, remove` };
            }
        } else {
            switch (action) {
                case 'list':
                    return await runCommand('crontab -l 2>/dev/null || echo "No crontab"');
                case 'add': {
                    const { schedule, command } = options;
                    if (!schedule || !command) return { success: false, error: 'schedule and command required' };
                    const cronLine = `${schedule} ${command}`;
                    return await runCommand(`(crontab -l 2>/dev/null; echo "${cronLine}") | crontab -`);
                }
                case 'remove': {
                    const { pattern } = options;
                    if (!pattern) return { success: false, error: 'pattern required' };
                    return await runCommand(`crontab -l 2>/dev/null | grep -v "${pattern}" | crontab -`);
                }
                default:
                    return { success: false, error: `Unknown action: ${action}. Use: list, add, remove` };
            }
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: system_env_manage ──────────────────────────────────────────────────

/**
 * Manage environment variables.
 * @param {string} action - 'get', 'set', 'list'
 * @param {string} key - Variable name
 * @param {string} value - Variable value (for set)
 * @returns {Promise<object>}
 */
async function system_env_manage(action, key = null, value = null) {
    try {
        switch (action) {
            case 'get':
                if (!key) return { success: false, error: 'key required' };
                return { success: true, key, value: process.env[key] || null };
            case 'set':
                if (!key || value === null) return { success: false, error: 'key and value required' };
                if (IS_WINDOWS) {
                    await runCommand(`[Environment]::SetEnvironmentVariable("${key}", "${value}", "User")`);
                } else {
                    await runCommand(`echo 'export ${key}="${value}"' >> ~/.bashrc`);
                }
                process.env[key] = value;
                return { success: true, key, value };
            case 'list': {
                const vars = {};
                for (const [k, v] of Object.entries(process.env)) {
                    // Filter out sensitive keys
                    if (!k.match(/key|token|secret|password|credential/i)) {
                        vars[k] = v;
                    }
                }
                return { success: true, variables: vars, count: Object.keys(vars).length };
            }
            default:
                return { success: false, error: `Unknown action: ${action}. Use: get, set, list` };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: system_file_permissions ────────────────────────────────────────────

/**
 * Manage file permissions.
 * @param {string} action - 'get', 'chmod', 'chown'
 * @param {string} filePath - Target file path
 * @param {string} mode - Permission mode (for chmod)
 * @param {string} owner - Owner (for chown)
 * @returns {Promise<object>}
 */
async function system_file_permissions(action, filePath, mode = null, owner = null) {
    try {
        if (IS_WINDOWS) {
            switch (action) {
                case 'get': {
                    const result = await runCommand(
                        `Get-Acl "${filePath}" | Select-Object Owner, @{N='Access';E={($_.Access | Select-Object IdentityReference, FileSystemRights, AccessControlType) | ConvertTo-Json}} | Format-List`
                    );
                    return result;
                }
                case 'chmod': {
                    // Windows: set read-only attribute
                    if (mode === 'readonly') {
                        return await runCommand(`attrib +R "${filePath}"`);
                    } else if (mode === 'writable') {
                        return await runCommand(`attrib -R "${filePath}"`);
                    }
                    return { success: false, error: 'Windows modes: readonly, writable' };
                }
                default:
                    return { success: false, error: `Windows supports: get, chmod` };
            }
        } else {
            switch (action) {
                case 'get':
                    return await runCommand(`ls -la "${filePath}"`);
                case 'chmod':
                    if (!mode) return { success: false, error: 'mode required' };
                    return await runCommand(`chmod ${mode} "${filePath}"`);
                case 'chown':
                    if (!owner) return { success: false, error: 'owner required' };
                    return await runCommand(`sudo chown ${owner} "${filePath}"`);
                default:
                    return { success: false, error: `Unknown action: ${action}` };
            }
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Tool: system_info ────────────────────────────────────────────────────────

/**
 * Get comprehensive system information.
 * @returns {Promise<object>}
 */
async function system_info() {
    try {
        const info = {
            platform: os.platform(),
            arch: os.arch(),
            hostname: os.hostname(),
            cpus: os.cpus().length,
            totalMemoryGB: Math.round(os.totalmem() / (1024 ** 3) * 10) / 10,
            freeMemoryGB: Math.round(os.freemem() / (1024 ** 3) * 10) / 10,
            uptime: Math.round(os.uptime() / 3600 * 10) / 10, // hours
            nodeVersion: process.version,
            timestamp: new Date().toISOString(),
        };

        if (IS_WINDOWS) {
            const osInfo = await runCommand(
                `Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture | Format-List`
            );
            if (osInfo.success) info.osDetails = osInfo.stdout;
        }

        return { success: true, ...info };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
    // Core commands
    system_run_command,
    system_run_script,
    runCommandStreaming,

    // Process management
    system_list_processes,
    system_kill_process,

    // Resources
    system_get_resources,
    system_info,

    // Package management
    system_install_package,
    detectPackageManager,

    // Scheduling
    system_cron_manage,

    // Environment
    system_env_manage,

    // File permissions
    system_file_permissions,

    // Helpers
    runCommand,
    IS_WINDOWS,
    IS_MAC,
    IS_LINUX,
};
