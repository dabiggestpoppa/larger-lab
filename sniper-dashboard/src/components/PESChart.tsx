import { getLatestPES } from '@/lib/api';

export default async function PESChart() {
  const raw = await getLatestPES();

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
        <h3 className="text-sm font-medium">PES Score History</h3>
        <span className="text-xs text-dark-muted">30 days</span>
      </div>
      <div className="p-4 h-64 flex items-center justify-center">
        {!raw || raw.length === 0 ? (
          <p className="text-sm text-dark-muted">No PES history yet. Data will appear after first scope run.</p>
        ) : (
          <PESChartInner data={raw} />
        )}
      </div>
    </div>
  );
}

function PESChartInner({ data }: { data: Array<any> }) {
  if (!data || data.length === 0) return null;
  const mapped = data.map(d => ({
    pes: d.pes_score ?? d.pes ?? 0,
    date: d.snapshot_date ?? d.date ?? '',
    firm: d.firm_name ?? d.firm ?? '',
  }));
  const max = Math.max(...mapped.map(d => d.pes), 1);
  const min = Math.min(...mapped.map(d => d.pes), 0);
  const range = max - min || 1;
  const w = 500;
  const h = 160;
  const pad = 20;

  const points = mapped.map((d, i) => {
    const x = pad + (i / Math.max(mapped.length - 1, 1)) * (w - pad * 2);
    const y = h - pad - ((d.pes - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full">
      {[0, 0.25, 0.5, 0.75, 1].map(frac => {
        const y = pad + frac * (h - pad * 2);
        return <line key={frac} x1={pad} y1={y} x2={w - pad} y2={y} stroke="#1e1e2e" strokeWidth={1} />;
      })}
      <polyline points={points} fill="none" stroke="#3b82f6" strokeWidth={2} />
      {mapped.map((d, i) => {
        const x = pad + (i / Math.max(mapped.length - 1, 1)) * (w - pad * 2);
        const y = h - pad - ((d.pes - min) / range) * (h - pad * 2);
        return <circle key={i} cx={x} cy={y} r={3} fill="#3b82f6" />;
      })}
    </svg>
  );
}
