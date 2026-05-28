"use client";

import { useState } from "react";

export default function BrowserPage() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const openUrl = async () => {
    if (!url) return;
    setLoading(true);
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `open ${url}` }),
      });
      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (e) {
      setResult(`Error: ${e}`);
    }
    setLoading(false);
  };

  const checkStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch("/browser/status");
      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (e) {
      setResult(`Error: ${e}`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary p-6">
      <h1 className="text-2xl font-bold mb-6">Browser Control</h1>
      
      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Open URL via OC2</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="flex-1 bg-bg-secondary border border-border-primary rounded px-3 py-2 text-text-primary"
          />
          <button
            onClick={openUrl}
            disabled={loading || !url}
            className="px-4 py-2 bg-accent-primary text-white rounded disabled:opacity-50"
          >
            {loading ? "Opening..." : "Open"}
          </button>
        </div>
        
        <button
          onClick={checkStatus}
          disabled={loading}
          className="px-4 py-2 bg-accent-secondary text-white rounded disabled:opacity-50"
        >
          Check Status
        </button>
      </div>

      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">OC2 Gateway UI</h2>
        <p className="text-sm text-text-secondary mb-4">
          Access the full OC2 control panel with browser automation:
        </p>
        <a
          href="http://127.0.0.1:18790/"
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-accent-primary text-white rounded inline-block"
        >
          Open OC2 Gateway UI
        </a>
      </div>

      {result && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-2">Result</h2>
          <pre className="bg-bg-secondary p-4 rounded overflow-x-auto text-sm">
            {result}
          </pre>
        </div>
      )}
    </div>
  );
}