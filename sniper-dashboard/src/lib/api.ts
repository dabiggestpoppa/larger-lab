/**
 * API Layer — Sniper Dashboard
 *
 * Connects to Sniper FastAPI server at localhost:8090.
 * Replace API_BASE with env var for production deployment.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8090';

async function fetchApi(path: string): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

// ── TYPES ──────────────────────────────────────────────────

export interface FirmMix {
  firm: string;
  accounts: number;
  size: number;
  promo_applied: string;
  true_cost: number;
  ff_eligible: boolean;
  strategy: string;
  alert_level: string;
  pes_score: number;
}

export interface DeploymentMatrix {
  generated_at: string;
  crossover_threshold_usd: number;
  firm_mix: FirmMix[];
  risk_parameters: {
    risk_per_trade: number;
    max_correlated_exposure: number;
    consistency_buffer: number;
  };
  notes: string[];
}

export interface Deployment {
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

export interface PESPoint {
  date: string;
  pes: number;
  firm: string;
}

// ── API FUNCTIONS ──────────────────────────────────────────

export async function getDeploymentMatrix(): Promise<DeploymentMatrix> {
  return fetchApi('/api/matrix');
}

export async function getActiveDeployments(): Promise<Deployment[]> {
  const data = await fetchApi('/api/deployments/active-full');
  return data.deployments || [];
}

export async function getPESHistory(_days: number = 30): Promise<PESPoint[]> {
  const data = await fetchApi('/api/pes/latest');
  return (data.snapshots || []).map((s: any) => ({
    date: s.snapshot_date || '',
    pes: s.pes_score || 0,
    firm: s.firm_name || 'Unknown',
  }));
}

export async function getHealthReport() {
  return fetchApi('/api/health');
}

export async function getOverview() {
  return fetchApi('/api/overview');
}
