export default function HealthIndicator() {
  const indicators = [
    { label: 'CEREBUS Edge', status: 'ok', detail: '85.7% WR' },
    { label: 'Symmetry Trap', status: 'ok', detail: 'LIVE on EURUSD' },
    { label: 'P90 CASCADE', status: 'ok', detail: 'LIVE on USDCHF' },
    { label: 'Sniper Engine', status: 'ok', detail: 'v1.0 ready' },
    { label: 'Scraper', status: 'warning', detail: 'Awaiting Scrapling' },
    { label: 'PayoutJunction', status: 'warning', detail: 'Not scraped yet' },
    { label: 'Cron Fleet', status: 'ok', detail: '4 jobs active' },
    { label: 'Database', status: 'ok', detail: 'sniper.db connected' },
  ];

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-medium">System Health</h3>
      </div>
      <div className="p-2 space-y-0.5">
        {indicators.map((ind, i) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 rounded-md">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                ind.status === 'ok' ? 'bg-dark-success' : ind.status === 'warning' ? 'bg-dark-warning' : 'bg-dark-danger'
              }`} />
              <span className="text-sm">{ind.label}</span>
            </div>
            <span className="text-xs text-dark-muted">{ind.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
