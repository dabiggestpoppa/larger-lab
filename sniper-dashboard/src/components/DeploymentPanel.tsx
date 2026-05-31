import { getActiveDeployments } from '@/lib/api';

interface Deployment {
  deployment_id: string;
  firm_name: string;
  account_size: number;
  quantity: number;
  total_cost: number;
  pes_score: number;
  status: string;
  deployed_at: string;
  strategy: string;
}

export default async function DeploymentPanel({ deployments }: { deployments?: Deployment[] }) {
  const data = deployments && deployments.length > 0 ? deployments : await getActiveDeployments();

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
        <h3 className="text-sm font-medium">Active Deployments</h3>
        <span className="text-xs text-dark-muted">{data.length} active</span>
      </div>
      {data.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-sm text-dark-muted">No active deployments.</p>
          <p className="text-xs text-dark-muted mt-1">Run scope-care to generate deployment config.</p>
        </div>
      ) : (
        <div className="divide-y divide-dark-border">
          {data.map((dep, i) => (
            <div key={i} className="px-4 py-3 flex items-center justify-between hover:bg-dark-border/20 transition-colors">
              <div className="flex items-center gap-4">
                <p className="text-sm font-medium">{dep.firm_name}</p>
                <p className="text-xs text-dark-muted">{dep.quantity}x ${(dep.account_size / 1000).toFixed(0)}K</p>
              </div>
              <div className="flex items-center gap-6 text-sm">
                <div className="text-right">
                  <p className="text-dark-muted text-xs">Cost</p>
                  <p>${dep.total_cost.toFixed(0)}</p>
                </div>
                <div className="text-right">
                  <p className="text-dark-muted text-xs">PES</p>
                  <p className="text-dark-accent">{dep.pes_score.toFixed(2)}</p>
                </div>
                <span className="text-xs px-2 py-0.5 rounded bg-dark-accent/20 text-dark-accent">{dep.strategy}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-dark-success/20 text-dark-success">{dep.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
