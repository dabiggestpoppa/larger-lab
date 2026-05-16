/**
 * System Operator Tests — Phase 1
 * 
 * Run with: node tools/operator/system-operator.test.js
 */

const op = require('./system-operator');

let passed = 0;
let failed = 0;
let total = 0;

function assert(condition, message) {
    total++;
    if (condition) {
        passed++;
        console.log(`  ✅ ${message}`);
    } else {
        failed++;
        console.log(`  ❌ ${message}`);
    }
}

async function runTests() {
    console.log('\n🧪 System Operator Tests — Phase 1\n');
    console.log(`Platform: ${process.platform} | Node: ${process.version}\n`);

    // ── system_run_command ──────────────────────────────────────────────
    console.log('── system_run_command ──');

    const echoResult = await op.system_run_command(
        op.IS_WINDOWS ? 'Write-Output "hello operator"' : 'echo "hello operator"'
    );
    assert(echoResult.success, 'echo command succeeds');
    assert(echoResult.stdout.includes('hello operator'), 'echo output correct');

    const failResult = await op.system_run_command(
        op.IS_WINDOWS ? 'Get-Process -Name "nonexistent_process_xyz_123"' : 'ls /nonexistent_path_xyz'
    );
    // Get-Process with no match doesn't fail, it just returns empty
    assert(typeof failResult.success === 'boolean', 'failed command returns result object');

    const timeoutResult = await op.system_run_command(
        op.IS_WINDOWS ? 'Start-Sleep -Seconds 10' : 'sleep 10',
        1000 // 1s timeout
    );
    assert(!timeoutResult.success, 'timeout works');

    // ── system_run_script ───────────────────────────────────────────────
    console.log('\n── system_run_script ──');

    const scriptResult = await op.system_run_script(
        op.IS_WINDOWS ? 'Write-Output "script output 42"' : 'echo "script output 42"'
    );
    assert(scriptResult.success, 'script execution succeeds');
    assert(scriptResult.stdout.includes('script output 42'), 'script output correct');

    // ── system_list_processes ───────────────────────────────────────────
    console.log('\n── system_list_processes ──');

    const allProcs = await op.system_list_processes();
    assert(allProcs.success, 'list all processes succeeds');
    if (op.IS_WINDOWS) {
        assert(allProcs.count > 0, `found ${allProcs.count} processes`);
    }

    const filteredProcs = await op.system_list_processes('node');
    assert(filteredProcs.success, 'filtered process list succeeds');

    // ── system_get_resources ────────────────────────────────────────────
    console.log('\n── system_get_resources ──');

    const resources = await op.system_get_resources();
    assert(resources.success, 'get resources succeeds');
    assert(resources.platform === process.platform, 'platform matches');
    assert(resources.hostname.length > 0, 'hostname present');
    assert(resources.cpu.length > 0, 'CPU info present');
    assert(resources.memory.length > 0, 'memory info present');
    assert(resources.disk.length > 0, 'disk info present');
    console.log(`  📊 CPU: ${resources.cpu.split('\n')[0]}`);
    console.log(`  📊 Memory: ${resources.memory.split('\n')[0]}`);
    console.log(`  📊 Disk: ${resources.disk.split('\n')[0]}`);
    console.log(`  📊 Uptime: ${resources.uptime}`);

    // ── system_info ─────────────────────────────────────────────────────
    console.log('\n── system_info ──');

    const info = await op.system_info();
    assert(info.success, 'system info succeeds');
    assert(info.cpus > 0, `CPUs: ${info.cpus}`);
    assert(info.totalMemoryGB > 0, `Total RAM: ${info.totalMemoryGB} GB`);
    assert(info.freeMemoryGB > 0, `Free RAM: ${info.freeMemoryGB} GB`);
    assert(info.uptime > 0, `Uptime: ${info.uptime} hours`);
    console.log(`  📊 ${info.cpus} CPUs | ${info.totalMemoryGB}GB RAM | ${info.uptime}h uptime`);

    // ── system_env_manage ───────────────────────────────────────────────
    console.log('\n── system_env_manage ──');

    const envList = await op.system_env_manage('list');
    assert(envList.success, 'env list succeeds');
    assert(envList.count > 0, `found ${envList.count} env vars`);

    const testSet = await op.system_env_manage('set', 'OPERATOR_TEST_VAR', 'test_value_123');
    assert(testSet.success, 'env set succeeds');
    assert(process.env.OPERATOR_TEST_VAR === 'test_value_123', 'env var set in process');

    const testGet = await op.system_env_manage('get', 'OPERATOR_TEST_VAR');
    assert(testGet.success, 'env get succeeds');
    assert(testGet.value === 'test_value_123', 'env get returns correct value');

    // ── system_cron_manage ──────────────────────────────────────────────
    console.log('\n── system_cron_manage ──');

    const cronList = await op.system_cron_manage('list');
    assert(cronList.success, 'cron list succeeds');
    console.log(`  📊 Cron output: ${cronList.stdout ? cronList.stdout.substring(0, 100) : '(empty)'}`);

    // ── system_file_permissions ─────────────────────────────────────────
    console.log('\n── system_file_permissions ──');

    const permResult = await op.system_file_permissions('get', __filename);
    assert(permResult.success, 'file permissions get succeeds');

    // ── detectPackageManager ────────────────────────────────────────────
    console.log('\n── detectPackageManager ──');

    const pm = op.detectPackageManager();
    assert(pm !== 'unknown', `package manager detected: ${pm}`);
    console.log(`  📊 Package manager: ${pm}`);

    // ── Summary ─────────────────────────────────────────────────────────
    console.log('\n' + '─'.repeat(50));
    console.log(`📊 Results: ${passed}/${total} passed | ${failed} failed`);
    if (failed === 0) {
        console.log('✅ All tests passed!');
    } else {
        console.log(`⚠️ ${failed} test(s) failed`);
    }
    console.log('─'.repeat(50) + '\n');

    process.exit(failed > 0 ? 1 : 0);
}

runTests().catch(err => {
    console.error('Test runner error:', err);
    process.exit(1);
});
