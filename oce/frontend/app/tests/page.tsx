"use client";

import { useState } from "react";

interface TestResult {
  test_file: string;
  status: "passed" | "failed" | "timeout" | "skipped";
  phase: number | null;
  passed: number | null;
  failed: number | null;
  duration_ms: number | null;
}

const mockTests: TestResult[] = [
  { test_file: "test_observer_core.py", status: "passed", phase: 1, passed: 42, failed: 0, duration_ms: 1250 },
  { test_file: "test_consensus.py", status: "passed", phase: 2, passed: 28, failed: 0, duration_ms: 890 },
  { test_file: "test_spawn_engine.py", status: "passed", phase: 3, passed: 35, failed: 0, duration_ms: 1100 },
  { test_file: "test_field_learning.py", status: "passed", phase: 4, passed: 14, failed: 0, duration_ms: 620 },
  { test_file: "test_chaos_engine.py", status: "passed", phase: 11, passed: 20, failed: 0, duration_ms: 3500 },
  { test_file: "test_continuity_72h.py", status: "timeout", phase: 11, passed: 7, failed: 0, duration_ms: null },
  { test_file: "test_orchestration_11_5.py", status: "skipped", phase: 11, passed: null, failed: null, duration_ms: null },
];

function TestRow({ test }: { test: TestResult }) {
  const statusColor =
    test.status === "passed"
      ? "text-[var(--accent-success)]"
      : test.status === "failed"
      ? "text-[var(--accent-danger)]"
      : test.status === "timeout"
      ? "text-[var(--accent-warning)]"
      : "text-[var(--text-muted)]";

  return (
    <tr className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-tertiary)]/50">
      <td className="py-3 px-4 text-sm text-[var(--text-primary)]">{test.test_file}</td>
      <td className="py-3 px-4 text-sm">
        <span className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${
            test.status === "passed" ? "bg-[var(--accent-success)]" :
            test.status === "failed" ? "bg-[var(--accent-danger)]" :
            test.status === "timeout" ? "bg-[var(--accent-warning)]" :
            "bg-[var(--text-muted)]"
          }`} />
          <span className={statusColor}>{test.status}</span>
        </span>
      </td>
      <td className="py-3 px-4 text-sm text-[var(--text-muted)] text-center">
        {test.phase !== null ? test.phase : "—"}
      </td>
      <td className="py-3 px-4 text-sm text-[var(--accent-success)] text-center">
        {test.passed !== null ? test.passed : "—"}
      </td>
      <td className="py-3 px-4 text-sm text-[var(--accent-danger)] text-center">
        {test.failed !== null ? test.failed : "—"}
      </td>
      <td className="py-3 px-4 text-sm text-[var(--text-muted)] text-center">
        {test.duration_ms !== null ? `${test.duration_ms.toFixed(0)}ms` : "—"}
      </td>
    </tr>
  );
}

export default function TestsPage() {
  const [tests] = useState<TestResult[]>(mockTests);
  const totalPassed = tests.reduce((sum, t) => sum + (t.passed || 0), 0);
  const totalFailed = tests.reduce((sum, t) => sum + (t.failed || 0), 0);
  const passRate = tests.filter((t) => t.status === "passed").length / tests.length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          TEST RESULTS VIEWER
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {totalPassed} passed / {totalFailed} failed ({(passRate * 100).toFixed(0)}%)
        </span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 p-4">
        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">Total Tests</span>
          <p className="text-lg font-mono text-[var(--text-primary)]">{tests.length}</p>
        </div>
        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">Passed</span>
          <p className="text-lg font-mono text-[var(--accent-success)]">{totalPassed}</p>
        </div>
        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">Failed</span>
          <p className="text-lg font-mono text-[var(--accent-danger)]">{totalFailed}</p>
        </div>
        <div className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">Pass Rate</span>
          <p className="text-lg font-mono text-[var(--accent-primary)]">{(passRate * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* Test Table */}
      <div className="flex-1 px-4 pb-4 overflow-y-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--border-subtle)]">
              <th className="py-2 px-4 text-left text-[10px] font-mono text-[var(--text-muted)] uppercase">Test File</th>
              <th className="py-2 px-4 text-left text-[10px] font-mono text-[var(--text-muted)] uppercase">Status</th>
              <th className="py-2 px-4 text-center text-[10px] font-mono text-[var(--text-muted)] uppercase">Phase</th>
              <th className="py-2 px-4 text-center text-[10px] font-mono text-[var(--text-muted)] uppercase">Passed</th>
              <th className="py-2 px-4 text-center text-[10px] font-mono text-[var(--text-muted)] uppercase">Failed</th>
              <th className="py-2 px-4 text-center text-[10px] font-mono text-[var(--text-muted)] uppercase">Duration</th>
            </tr>
          </thead>
          <tbody>
            {tests.map((test) => (
              <TestRow key={test.test_file} test={test} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}