"use client";

import { useEffect, useState } from "react";
import { srraApi, TestSummary, TestResult } from "../lib/api";

function TestRow({ test }: { test: TestResult }) {
  const statusColor =
    test.status === "passed"
      ? "text-green-400"
      : test.status === "failed"
      ? "text-red-400"
      : test.status === "timeout"
      ? "text-yellow-400"
      : "text-gray-400";

  const dotColor =
    test.status === "passed"
      ? "active"
      : test.status === "failed"
      ? "error"
      : test.status === "timeout"
      ? "repairing"
      : "inactive";

  return (
    <tr className="border-b border-default hover:bg-bg-tertiary/50">
      <td className="py-3 px-4 text-sm text-gray-300">{test.test_file}</td>
      <td className="py-3 px-4 text-sm">
        <span className="flex items-center gap-1.5">
          <span className={`status-dot ${dotColor}`} />
          <span className={statusColor}>{test.status}</span>
        </span>
      </td>
      <td className="py-3 px-4 text-sm text-gray-400 text-center">
        {test.phase || "—"}
      </td>
      <td className="py-3 px-4 text-sm text-green-400 text-center">
        {test.passed ?? "—"}
      </td>
      <td className="py-3 px-4 text-sm text-red-400 text-center">
        {test.failed ?? "—"}
      </td>
      <td className="py-3 px-4 text-sm text-gray-400 text-center">
        {test.duration_ms !== null ? `${test.duration_ms.toFixed(0)}ms` : "—"}
      </td>
    </tr>
  );
}

export default function TestsPage() {
  const [summary, setSummary] = useState<TestSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTests = async () => {
    try {
      const data = await srraApi.tests();
      setSummary(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch tests");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTests();
    const interval = setInterval(fetchTests, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center max-w-md mx-auto mt-20">
        <p className="text-accent-red font-semibold">Error</p>
        <p className="text-gray-400 text-sm mt-2">{error}</p>
      </div>
    );
  }

  const passRate = summary && summary.total_tests > 0
    ? ((summary.passed / summary.total_tests) * 100).toFixed(1)
    : "0";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Test Results</h1>
          <p className="text-sm text-gray-500 mt-1">
            {summary?.last_run
              ? `Last run: ${new Date(summary.last_run).toLocaleString()}`
              : "No runs yet"}
          </p>
        </div>
      </div>

      {/* Summary Bar */}
      <div className="card mb-6">
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Pass Rate</span>
              <span className="text-sm font-semibold text-white">{passRate}%</span>
            </div>
            <div className="w-full bg-bg-tertiary rounded-full h-3 overflow-hidden flex">
              {summary && summary.passed > 0 && (
                <div
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${(summary.passed / summary.total_tests) * 100}%` }}
                />
              )}
              {summary && summary.failed > 0 && (
                <div
                  className="h-full bg-red-500 transition-all"
                  style={{ width: `${(summary.failed / summary.total_tests) * 100}%` }}
                />
              )}
            </div>
          </div>
          <div className="flex gap-6 text-center">
            <div>
              <p className="text-2xl font-bold text-white">{summary?.total_tests ?? 0}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-400">{summary?.passed ?? 0}</p>
              <p className="text-xs text-gray-500">Passed</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-400">{summary?.failed ?? 0}</p>
              <p className="text-xs text-gray-500">Failed</p>
            </div>
          </div>
        </div>
      </div>

      {/* Test Table */}
      <div className="card overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-default text-xs text-gray-500 uppercase tracking-wider">
              <th className="py-3 px-4">Test File</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-center">Phase</th>
              <th className="py-3 px-4 text-center">Passed</th>
              <th className="py-3 px-4 text-center">Failed</th>
              <th className="py-3 px-4 text-center">Duration</th>
            </tr>
          </thead>
          <tbody>
            {summary?.phases?.map((test) => (
              <TestRow key={test.test_file} test={test} />
            ))}
          </tbody>
        </table>
        {(!summary?.phases || summary.phases.length === 0) && (
          <p className="text-gray-500 text-sm text-center py-8">No test results available</p>
        )}
      </div>
    </div>
  );
}
