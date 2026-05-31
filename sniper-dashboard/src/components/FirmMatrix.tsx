import { getDeploymentMatrix } from '@/lib/api';

interface FirmMix {
  firm: string;
  accounts: number;
  size: number;
  promo_applied: string;
  true_cost: number;
  ff_eligible: boolean;
  strategy: string;
  alert_level: string;
  pes_score?: number;
  rank?: number;
}

export default async function FirmMatrix({ firms }: { firms: FirmMix[] }) {
  const data = firms && firms.length > 0 ? firms : await getDeploymentMatrix().then(m => m.firm_mix || []);

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
        <h3 className="text-sm font-medium">Firm Comparison Matrix</h3>
        <span className="text-xs text-dark-muted">{data.length} firms tracked</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-dark-muted text-xs border-b border-dark-border">
              <th className="text-left px-4 py-2.5 font-medium">Firm</th>
              <th className="text-right px-4 py-2.5 font-medium">Accounts</th>
              <th className="text-right px-4 py-2.5 font-medium">Size</th>
              <th className="text-right px-4 py-2.5 font-medium">Cost</th>
              <th className="text-center px-4 py-2.5 font-medium">F&F</th>
              <th className="text-center px-4 py-2.5 font-medium">Strategy</th>
              <th className="text-center px-4 py-2.5 font-medium">Alert</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-dark-muted">No deployment data yet. Run scope-care to generate.</td></tr>
            ) : (
              data.map((firm: FirmMix, i: number) => (
                <tr key={i} className="border-b border-dark-border/50 hover:bg-dark-border/30 transition-colors">
                  <td className="px-4 py-3 font-medium">{firm.firm}</td>
                  <td className="px-4 py-3 text-right">{firm.accounts}</td>
                  <td className="px-4 py-3 text-right">${(firm.size / 1000).toFixed(0)}K</td>
                  <td className="px-4 py-3 text-right">${firm.true_cost.toFixed(0)}</td>
                  <td className="px-4 py-3 text-center">
                    {firm.ff_eligible ? (
                      <span className="text-dark-success text-xs">YES</span>
                    ) : (
                      <span className="text-dark-muted text-xs">NO</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs px-2 py-0.5 rounded bg-dark-accent/20 text-dark-accent">
                      {firm.strategy}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <AlertBadge level={firm.alert_level} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AlertBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    OK: 'bg-dark-success/20 text-dark-success',
    WATCH: 'bg-dark-warning/20 text-dark-warning',
    PATCHED: 'bg-dark-danger/20 text-dark-danger',
    SUSPENDED: 'bg-dark-danger/20 text-dark-danger',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded ${colors[level] || colors.OK}`}>
      {level}
    </span>
  );
}
