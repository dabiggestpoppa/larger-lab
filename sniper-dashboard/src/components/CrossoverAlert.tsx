export default function CrossoverAlert() {
  const crossoverThreshold = 12000;
  const currentAUM = 8200;
  const pct = Math.round((currentAUM / crossoverThreshold) * 100);
  const remaining = crossoverThreshold - currentAUM;

  return (
    <div className="bg-dark-warning/10 border border-dark-warning/30 rounded-lg px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-dark-warning/20 flex items-center justify-center">
          <span className="text-dark-warning text-sm">!</span>
        </div>
        <div>
          <p className="text-sm font-medium text-dark-warning">Crossover Proximity Alert</p>
          <p className="text-xs text-dark-muted">
            Current AUM ${currentAUM.toLocaleString()} — ${remaining.toLocaleString()} below crossover (${crossoverThreshold.toLocaleString()})
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-32 h-2 bg-dark-border rounded-full overflow-hidden">
          <div className="h-full bg-dark-warning rounded-full" style={{ width: `${Math.min(pct, 100)}%` }} />
        </div>
        <span className="text-xs text-dark-muted">{pct}%</span>
      </div>
    </div>
  );
}
