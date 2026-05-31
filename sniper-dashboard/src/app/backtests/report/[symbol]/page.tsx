import { getBacktestReport } from '@/lib/api';

export const revalidate = 60;

export default async function BacktestReportPage({ params }: { params: { symbol: string } }) {
  const symbol = params.symbol.toUpperCase();
  const data = await getBacktestReport(symbol);

  if (!data) {
    return (
      <div className="text-dark-muted text-sm py-12 text-center">
        Report not found for {symbol}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <a href="/backtests" className="text-xs text-dark-accent hover:underline">← Back to Backtests</a>
      <div className="bg-dark-card border border-dark-border rounded-lg">
        <div className="px-4 py-3 border-b border-dark-border">
          <h2 className="text-lg font-semibold">{symbol} — Full Backtest Report</h2>
        </div>
        <div className="p-6">
          <pre className="text-sm text-dark-primary whitespace-pre-wrap font-mono leading-relaxed">
            {data.content}
          </pre>
        </div>
      </div>
    </div>
  );
}
