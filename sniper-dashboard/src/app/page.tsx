import FirmMatrix from '@/components/FirmMatrix';
import DeploymentPanel from '@/components/DeploymentPanel';
import PESChart from '@/components/PESChart';
import CrossoverAlert from '@/components/CrossoverAlert';
import PromoTracker from '@/components/PromoTracker';
import HealthIndicator from '@/components/HealthIndicator';
import { getDeploymentMatrix } from '@/lib/api';

export default async function DashboardPage() {
  const matrix = await getDeploymentMatrix();

  return (
    <div className="space-y-6">
      {/* Summary Bar */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard
          label="Directives"
          value={matrix.firm_mix.length.toString()}
          sub="Active firm configs"
          color="blue"
        />
        <SummaryCard
          label="Crossover Threshold"
          value={`$${(matrix.crossover_threshold_usd / 1000).toFixed(0)}K`}
          sub="Capital limit"
          color="green"
        />
        <SummaryCard
          label="Active Firms"
          value={matrix.firm_mix.length.toString()}
          sub={`Risk: ${matrix.risk_parameters.risk_per_trade * 100}%`}
          color="green"
        />
        <SummaryCard
          label="Risk/Trade"
          value={`${(matrix.risk_parameters.risk_per_trade * 100).toFixed(0)}%`}
          sub={`Max corr: ${matrix.risk_parameters.max_correlated_exposure}`}
          color="blue"
        />
      </div>

      {/* Crossover Alert */}
      <CrossoverAlert />

      {/* Row 2: Firm Matrix + Health */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <FirmMatrix firms={matrix.firm_mix} />
        </div>
        <div>
          <HealthIndicator />
        </div>
      </div>

      {/* Row 3: PES Chart + Promo Tracker */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <PESChart />
        </div>
        <div>
          <PromoTracker />
        </div>
      </div>

      {/* Deployments */}
      <DeploymentPanel />
    </div>
  );
}

function SummaryCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  color: 'blue' | 'green' | 'amber' | 'red';
}) {
  const valueColors: Record<string, string> = {
    blue: 'text-dark-accent',
    green: 'text-dark-success',
    amber: 'text-dark-warning',
    red: 'text-dark-danger',
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-4">
      <div className="text-[11px] text-dark-muted uppercase tracking-wider">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${valueColors[color]}`}>{value}</div>
      <div className="text-[11px] text-dark-muted mt-0.5">{sub}</div>
    </div>
  );
}
