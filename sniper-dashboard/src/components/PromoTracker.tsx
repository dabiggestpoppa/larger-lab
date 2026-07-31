import { getDeploymentMatrix } from '@/lib/api';

export default async function PromoTracker() {
  const promos = await getDeploymentMatrix().then(m =>
    (m.firm_mix || [])
      .filter((f: { promo_applied: string }) => f.promo_applied)
      .map((f: { firm: string; promo_applied: string; ff_eligible: boolean }) => ({
        firm: f.firm,
        code: f.promo_applied,
        discount: 50,
        ff_eligible: f.ff_eligible,
      }))
  );

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg">
      <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
        <h3 className="text-sm font-medium">Active Promos</h3>
        <span className="text-xs text-dark-muted">{promos.length} active</span>
      </div>
      <div className="p-2 space-y-1">
        {promos.length === 0 ? (
          <p className="text-sm text-dark-muted text-center py-6">No active promos detected.</p>
        ) : (
          promos.map((promo: { firm: string; code: string; discount: number; ff_eligible: boolean }, i: number) => (
            <PromoCard key={i} promo={promo} />
          ))
        )}
      </div>
    </div>
  );
}

function PromoCard({ promo }: { promo: { firm: string; code: string; discount: number; ff_eligible: boolean } }) {
  return (
    <div className="flex items-center justify-between px-3 py-2 rounded-md hover:bg-dark-border/30 transition-colors">
      <div>
        <p className="text-sm font-medium">{promo.firm}</p>
        <p className="text-xs text-dark-muted">Code: <span className="text-dark-accent font-mono">{promo.code}</span></p>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs px-2 py-0.5 rounded bg-dark-success/20 text-dark-success">-{promo.discount}%</span>
        {promo.ff_eligible && (
          <span className="text-xs px-2 py-0.5 rounded bg-dark-accent/20 text-dark-accent">F&F</span>
        )}
      </div>
    </div>
  );
}
