#!/usr/bin/env python3
"""
cloud-burst.py — Burst GPU Compute Engine for SRRA-OPH Agent System

Manages on-demand GPU instance lifecycle across multiple cloud providers.
Integrates with Phase 9 "Entropy Economics" for cost-aware resource allocation.

Usage:
    python tools/cloud-burst.py --list-providers
    python tools/cloud-burst.py --estimate --hours 4 --vram 12
    python tools/cloud-burst.py --spawn --provider octaspace --gpu RTX_5070 --hours 4
    python tools/cloud-burst.py --status
    python tools/cloud-burst.py --shutdown --session-id <id>

Providers:
    - octaSpace: Decentralized GPU marketplace (cheapest, $0.06-0.29/hr)
    - runpod: Community cloud GPU ($0.24-0.40/hr spot)
    - vastai: Decentralized GPU ($0.20/hr, less reliable)
    - hetzner: Dedicated servers (no GPU, always-on, €35/mo)

Cost Tracking:
    All sessions logged to srrs_opc/docs/resource_costs.md
    Phase 9 entropy economics metrics updated automatically.
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

# ─── Provider Pricing Data (updated 2026-05-16) ───────────────────────────────

class Provider(Enum):
    OCTASPACE = "octaspace"
    RUNPOD = "runpod"
    VASTAI = "vastai"
    HETZNER = "hetzner"
    KAMTERA = "kamtera"


@dataclass
class GPUInstance:
    provider: str
    gpu_name: str
    vram_gb: int
    hourly_rate: float  # USD
    available: int = 0
    reliability: str = "medium"  # high, medium, low

    @property
    def daily_rate(self) -> float:
        return self.hourly_rate * 24

    @property
    def monthly_rate(self) -> float:
        return self.hourly_rate * 24 * 30


# Live pricing from provider websites (2026-05-16)
GPU_CATALOG: list[GPUInstance] = [
    # OctaSpace (decentralized, cheapest)
    GPUInstance("octaspace", "RTX_4070", 12, 0.04, 9, "medium"),
    GPUInstance("octaspace", "RTX_4080", 16, 0.04, 2, "medium"),
    GPUInstance("octaspace", "RTX_5070", 12, 0.06, 15, "medium"),
    GPUInstance("octaspace", "RTX_3090", 24, 0.11, 50, "medium"),
    GPUInstance("octaspace", "RTX_4090", 24, 0.22, 30, "medium"),
    GPUInstance("octaspace", "RTX_5090", 24, 0.29, 50, "medium"),
    GPUInstance("octaspace", "A100_40GB", 40, 0.48, 1, "medium"),
    GPUInstance("octaspace", "H100_80GB", 80, 0.12, 8, "medium"),
    # RunPod (community cloud)
    GPUInstance("runpod", "RTX_3090", 24, 0.24, 100, "high"),
    GPUInstance("runpod", "RTX_4090", 24, 0.40, 50, "high"),
    GPUInstance("runpod", "A100_40GB", 40, 0.79, 10, "high"),
    # Vast.ai (decentralized, less reliable)
    GPUInstance("vastai", "RTX_3090", 24, 0.20, 200, "low"),
    GPUInstance("vastai", "RTX_4090", 24, 0.35, 80, "low"),
    GPUInstance("vastai", "A100_40GB", 40, 0.60, 20, "low"),
    # Hetzner (dedicated, no GPU)
    GPUInstance("hetzner", "AX42_CPU", 0, 0.049, 999, "high"),  # €35/mo
    GPUInstance("hetzner", "AX162_CPU", 0, 0.097, 999, "high"),  # €70/mo
]


# ─── Session Tracking ──────────────────────────────────────────────────────────

SESSIONS_FILE = Path("srrs_opc/docs/resource_costs.md")
SESSIONS_DIR = Path("srrs_opc/docs/burst_sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class BurstSession:
    session_id: str
    provider: str
    gpu_name: str
    vram_gb: int
    hourly_rate: float
    started_at: str
    expected_hours: float
    status: str = "pending"  # pending, running, completed, failed, shutdown
    ended_at: Optional[str] = None
    actual_hours: float = 0.0
    total_cost: float = 0.0
    task_description: str = ""
    instance_id: Optional[str] = None
    ssh_address: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BurstSession":
        return cls(**d)

    def complete(self):
        self.ended_at = datetime.now(timezone.utc).isoformat()
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.ended_at)
            self.actual_hours = (end - start).total_seconds() / 3600
            self.total_cost = round(self.actual_hours * self.hourly_rate, 4)
        self.status = "completed"


# ─── Provider API Integrations ─────────────────────────────────────────────────

class OctaSpaceProvider:
    """OctaSpace decentralized GPU marketplace integration."""

    name = "octaspace"
    api_base = "https://api.octa.space"

    @staticmethod
    def create_client(api_key: str):
        try:
            import octaspace
            config = octaspace.ClientConfig(api_key=api_key)
            return octaspace.OctaSpaceClient(config)
        except ImportError:
            print("[ERROR] octaspace SDK not installed. Run: uv pip install octaspace")
            return None

    @staticmethod
    def list_available_nodes(client, min_vram: int = 12) -> list[dict]:
        """List available GPU nodes matching criteria."""
        try:
            nodes = client.nodes.list()
            available = []
            for node in nodes:
                gpu_vram = getattr(node, 'gpu_vram', 0)
                if gpu_vram >= min_vram:
                    available.append({
                        'id': getattr(node, 'id', 'unknown'),
                        'gpu': getattr(node, 'gpu_name', 'unknown'),
                        'vram': gpu_vram,
                        'price_hr': getattr(node, 'price_per_hour', 0),
                        'location': getattr(node, 'location', 'unknown'),
                        'status': getattr(node, 'status', 'unknown'),
                    })
            return available
        except Exception as e:
            print(f"[WARN] Could not list OctaSpace nodes: {e}")
            return []

    @staticmethod
    def spawn_instance(client, gpu_name: str, docker_image: str = "ubuntu:22.04") -> Optional[dict]:
        """Spawn a GPU instance on OctaSpace."""
        try:
            # Find matching node
            nodes = client.nodes.list()
            for node in nodes:
                node_gpu = getattr(node, 'gpu_name', '').replace(' ', '_').upper()
                if gpu_name.upper() in node_gpu and getattr(node, 'status', '') == 'available':
                    # Create session/instance
                    session = client.sessions.post(
                        node_id=getattr(node, 'id', ''),
                        image=docker_image,
                    )
                    return {
                        'session_id': getattr(session, 'id', 'unknown'),
                        'node_id': getattr(node, 'id', 'unknown'),
                        'ssh_address': getattr(session, 'ssh_address', None),
                        'status': 'running',
                    }
            print(f"[WARN] No available nodes matching {gpu_name}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to spawn OctaSpace instance: {e}")
            return None

    @staticmethod
    def shutdown_instance(client, session_id: str) -> bool:
        """Shutdown an OctaSpace instance."""
        try:
            client.sessions.delete(session_id)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to shutdown session {session_id}: {e}")
            return False


class RunPodProvider:
    """RunPod community cloud integration (placeholder for API integration)."""

    name = "runpod"
    api_base = "https://api.runpod.io/v2"

    @staticmethod
    def create_client(api_key: str):
        """Create RunPod API client."""
        try:
            import requests
            return {
                'api_key': api_key,
                'session': requests.Session(),
            }
        except ImportError:
            print("[ERROR] requests not installed.")
            return None

    @staticmethod
    def spawn_instance(client: dict, gpu_type: str, template: str = "runpod/stable-diffusion") -> Optional[dict]:
        """Spawn a RunPod serverless GPU pod."""
        # RunPod API v2 integration would go here
        # POST /v2/{gpuType}/run
        print(f"[INFO] RunPod spawn: {gpu_type} (template: {template})")
        print("[WARN] RunPod API integration requires API key. Set RUNPOD_API_KEY env var.")
        return None


# ─── Cost Estimation Engine ────────────────────────────────────────────────────

def estimate_cost(hours: float, vram_min: int = 12, provider: Optional[str] = None) -> list[dict]:
    """Estimate cost across providers for given requirements."""
    results = []
    for gpu in GPU_CATALOG:
        if gpu.vram_gb >= vram_min:
            if provider and gpu.provider != provider:
                continue
            total = round(gpu.hourly_rate * hours, 2)
            results.append({
                'provider': gpu.provider,
                'gpu': gpu.gpu_name,
                'vram': gpu.vram_gb,
                'hourly': gpu.hourly_rate,
                'hours': hours,
                'total_cost': total,
                'reliability': gpu.reliability,
                'available': gpu.available,
            })
    results.sort(key=lambda x: x['total_cost'])
    return results


def recommend_instance(task_type: str, vram_needed: int, max_budget: float = None) -> Optional[dict]:
    """Recommend best GPU instance for a task type."""
    recommendations = {
        'inference': {'min_vram': 12, 'preferred': ['RTX_4090', 'RTX_5090', 'A100_40GB']},
        'training': {'min_vram': 24, 'preferred': ['A100_40GB', 'H100_80GB', 'RTX_4090']},
        'video': {'min_vram': 12, 'preferred': ['RTX_4090', 'RTX_3090', 'RTX_5070']},
        'backtest': {'min_vram': 0, 'preferred': ['AX42_CPU', 'AX162_CPU']},  # CPU is fine
        'image_gen': {'min_vram': 12, 'preferred': ['RTX_4090', 'RTX_3090', 'RTX_5070']},
        'embedding': {'min_vram': 8, 'preferred': ['RTX_3090', 'RTX_4070', 'RTX_5070']},
    }

    task = recommendations.get(task_type, {'min_vram': vram_needed, 'preferred': []})
    min_vram = max(vram_needed, task['min_vram'])

    candidates = [g for g in GPU_CATALOG if g.vram_gb >= min_vram]
    if max_budget:
        candidates = [g for g in candidates if g.hourly_rate <= max_budget]

    # Prefer recommended GPUs
    for pref in task['preferred']:
        for c in candidates:
            if pref in c.gpu_name:
                return {
                    'provider': c.provider,
                    'gpu': c.gpu_name,
                    'vram': c.vram_gb,
                    'hourly': c.hourly_rate,
                    'reasoning': f"Preferred for {task_type}",
                }

    # Fallback: cheapest available
    if candidates:
        cheapest = min(candidates, key=lambda g: g.hourly_rate)
        return {
            'provider': cheapest.provider,
            'gpu': cheapest.gpu_name,
            'vram': cheapest.vram_gb,
            'hourly': cheapest.hourly_rate,
            'reasoning': f"Cheapest available (≥{min_vram}GB VRAM)",
        }
    return None


# ─── Session Logging ───────────────────────────────────────────────────────────

def log_session(session: BurstSession):
    """Log a burst session to the cost tracking file."""
    session_file = SESSIONS_DIR / f"{session.session_id}.json"
    with open(session_file, 'w') as f:
        json.dump(session.to_dict(), f, indent=2)
    update_cost_summary()


def update_cost_summary():
    """Update the resource cost summary markdown file."""
    sessions = []
    for f in SESSIONS_DIR.glob("*.json"):
        with open(f) as fh:
            sessions.append(json.load(fh))

    total_cost = sum(s.get('total_cost', 0) for s in sessions)
    total_hours = sum(s.get('actual_hours', 0) for s in sessions)

    by_provider = {}
    for s in sessions:
        p = s.get('provider', 'unknown')
        if p not in by_provider:
            by_provider[p] = {'cost': 0, 'hours': 0, 'sessions': 0}
        by_provider[p]['cost'] += s.get('total_cost', 0)
        by_provider[p]['hours'] += s.get('actual_hours', 0)
        by_provider[p]['sessions'] += 1

    lines = [
        "# 💰 Resource Cost Tracking — Burst Compute",
        "",
        f"> Auto-generated by `tools/cloud-burst.py`",
        f"> Last updated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Sessions | {len(sessions)} |",
        f"| Total Compute Hours | {total_hours:.1f} |",
        f"| Total Cost | ${total_cost:.2f} |",
        f"| Avg Cost/Hour | ${total_cost/max(total_hours,0.01):.2f} |",
        "",
        "## By Provider",
        "",
        "| Provider | Sessions | Hours | Cost |",
        "|----------|----------|-------|------|",
    ]
    for p, data in sorted(by_provider.items()):
        lines.append(f"| {p} | {data['sessions']} | {data['hours']:.1f} | ${data['cost']:.2f} |")

    lines += [
        "",
        "## Phase 9 Entropy Economics Metrics",
        "",
        "| Metric | Value | Target |",
        "|--------|-------|--------|",
        f"| Coherence-per-resource | ${total_cost/max(len(sessions),1):.2f}/session | Minimize |",
        f"| Entropy-aware scaling | {len(set(s.get('gpu_name','') for s in sessions))} GPU types used | Match task to GPU |",
        f"| Adaptive compression | {total_hours:.1f}h total | Burst only when needed |",
        f"| Sustainability | ${total_cost:.2f} total | Under budget |",
        "",
        "## Session Log",
        "",
        "| Session | Provider | GPU | Hours | Cost | Status |",
        "|---------|----------|-----|-------|------|--------|",
    ]
    for s in sorted(sessions, key=lambda x: x.get('started_at', ''), reverse=True)[:50]:
        lines.append(
            f"| {s.get('session_id','?')[:12]} | {s.get('provider','?')} | "
            f"{s.get('gpu_name','?')} | {s.get('actual_hours',0):.1f} | "
            f"${s.get('total_cost',0):.2f} | {s.get('status','?')} |"
        )

    lines.append("")
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, 'w') as f:
        f.write('\n'.join(lines))


# ─── CLI Interface ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cloud Burst Engine — On-demand GPU for SRRA-OPH agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # --list-providers
    subparsers.add_parser('list-providers', help='List all providers and GPU instances')

    # --estimate
    est_parser = subparsers.add_parser('estimate', help='Estimate cost for workload')
    est_parser.add_argument('--hours', type=float, required=True, help='Expected hours')
    est_parser.add_argument('--vram', type=int, default=12, help='Minimum VRAM (GB)')
    est_parser.add_argument('--provider', type=str, default=None, help='Filter by provider')

    # --recommend
    rec_parser = subparsers.add_parser('recommend', help='Recommend GPU for task type')
    rec_parser.add_argument('--task', type=str, required=True,
                            choices=['inference', 'training', 'video', 'backtest', 'image_gen', 'embedding'])
    rec_parser.add_argument('--vram', type=int, default=12, help='Minimum VRAM (GB)')
    rec_parser.add_argument('--budget', type=float, default=None, help='Max hourly budget (USD)')

    # --spawn
    spawn_parser = subparsers.add_parser('spawn', help='Spawn a GPU instance')
    spawn_parser.add_argument('--provider', type=str, default='octaspace', help='Provider')
    spawn_parser.add_argument('--gpu', type=str, required=True, help='GPU name (e.g., RTX_5070)')
    spawn_parser.add_argument('--hours', type=float, default=4, help='Expected duration')
    spawn_parser.add_argument('--task', type=str, default='', help='Task description')
    spawn_parser.add_argument('--image', type=str, default='ubuntu:22.04', help='Docker image')

    # --status
    subparsers.add_parser('status', help='Show active sessions')

    # --shutdown
    sd_parser = subparsers.add_parser('shutdown', help='Shutdown an instance')
    sd_parser.add_argument('--session-id', type=str, required=True, help='Session ID to shutdown')
    sd_parser.add_argument('--provider', type=str, default='octaspace', help='Provider')

    # --cost-report
    subparsers.add_parser('cost-report', help='Generate cost report')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'list-providers':
        print("\n🖥️  GPU Cloud Providers & Pricing (2026-05-16)\n")
        print(f"{'Provider':<12} {'GPU':<16} {'VRAM':>5}  {'$/hr':>6}  {'$/day':>7}  {'$/mo':>8}  {'Avail':>5}  {'Rel':<8}")
        print("─" * 80)
        for gpu in sorted(GPU_CATALOG, key=lambda g: g.hourly_rate):
            print(f"{gpu.provider:<12} {gpu.gpu_name:<16} {gpu.vram_gb:>4}GB  "
                  f"${gpu.hourly_rate:>5.2f}  ${gpu.daily_rate:>6.2f}  ${gpu.monthly_rate:>7.2f}  "
                  f"{gpu.available:>4}  {gpu.reliability:<8}")
        print()

    elif args.command == 'estimate':
        results = estimate_cost(args.hours, args.vram, args.provider)
        print(f"\n💰 Cost Estimate: {args.hours}h, ≥{args.vram}GB VRAM\n")
        print(f"{'Provider':<12} {'GPU':<16} {'VRAM':>5}  {'$/hr':>6}  {'Total':>8}  {'Rel':<8}")
        print("─" * 70)
        for r in results:
            print(f"{r['provider']:<12} {r['gpu']:<16} {r['vram']:>4}GB  "
                  f"${r['hourly']:>5.2f}  ${r['total_cost']:>7.2f}  {r['reliability']:<8}")
        print()
        if results:
            best = results[0]
            print(f"✅ Best: {best['provider']} {best['gpu']} at ${best['total_cost']:.2f} total")
        print()

    elif args.command == 'recommend':
        rec = recommend_instance(args.task, args.vram, args.budget)
        if rec:
            print(f"\n🎯 Recommendation for '{args.task}' (≥{args.vram}GB VRAM):\n")
            print(f"  Provider:  {rec['provider']}")
            print(f"  GPU:       {rec['gpu']} ({rec['vram']}GB)")
            print(f"  Cost:      ${rec['hourly']:.2f}/hr")
            print(f"  4h cost:   ${rec['hourly'] * 4:.2f}")
            print(f"  Reason:    {rec['reasoning']}")
            print()
        else:
            print(f"\n❌ No suitable GPU found for {args.task} (≥{args.vram}GB VRAM)\n")

    elif args.command == 'spawn':
        session_id = f"burst-{int(time.time())}"
        print(f"\n🚀 Spawning {args.gpu} on {args.provider}...")
        print(f"   Session: {session_id}")
        print(f"   Expected: {args.hours}h")
        print(f"   Task: {args.task or 'N/A'}")

        # Find matching GPU in catalog
        gpu_match = None
        for g in GPU_CATALOG:
            if g.provider == args.provider and args.gpu.upper() in g.gpu_name.upper():
                gpu_match = g
                break

        if not gpu_match:
            print(f"   [ERROR] No matching GPU found: {args.provider}/{args.gpu}")
            sys.exit(1)

        # Create session record
        session = BurstSession(
            session_id=session_id,
            provider=args.provider,
            gpu_name=gpu_match.gpu_name,
            vram_gb=gpu_match.vram_gb,
            hourly_rate=gpu_match.hourly_rate,
            started_at=datetime.now(timezone.utc).isoformat(),
            expected_hours=args.hours,
            task_description=args.task,
        )

        # Attempt to spawn via provider API
        api_key = os.environ.get('OCTASPACE_API_KEY', '')
        if args.provider == 'octaspace':
            if not api_key:
                print("   [WARN] OCTASPACE_API_KEY not set. Set env var to enable actual spawning.")
                print("   [INFO] Session recorded for tracking. Run with --status to see.")
                session.status = "pending_api_key"
            else:
                client = OctaSpaceProvider.create_client(api_key)
                if client:
                    result = OctaSpaceProvider.spawn_instance(client, gpu_match.gpu_name, args.image)
                    if result:
                        session.instance_id = result.get('session_id')
                        session.ssh_address = result.get('ssh_address')
                        session.status = "running"
                        print(f"   ✅ Instance spawned!")
                        print(f"   SSH: {session.ssh_address or 'N/A'}")
                    else:
                        session.status = "failed"
                        print(f"   ❌ Spawn failed. Check node availability.")
        else:
            print(f"   [WARN] {args.provider} API integration not yet implemented.")
            session.status = "pending_integration"

        log_session(session)
        print(f"   📊 Session logged to {SESSIONS_DIR}/{session_id}.json")
        print()

    elif args.command == 'status':
        sessions = []
        for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True)[:20]:
            with open(f) as fh:
                sessions.append(json.load(fh))

        if not sessions:
            print("\n📊 No burst sessions recorded yet.\n")
            return

        print(f"\n📊 Burst Sessions (last {len(sessions)})\n")
        print(f"{'Session':<20} {'Provider':<12} {'GPU':<16} {'Hours':>6}  {'Cost':>7}  {'Status':<12}")
        print("─" * 80)
        for s in sessions:
            print(f"{s.get('session_id','?')[:18]:<20} {s.get('provider','?'):<12} "
                  f"{s.get('gpu_name','?'):<16} {s.get('actual_hours',0):>5.1f}  "
                  f"${s.get('total_cost',0):>6.2f}  {s.get('status','?'):<12}")
        print()

    elif args.command == 'shutdown':
        session_file = SESSIONS_DIR / f"{args.session_id}.json"
        if not session_file.exists():
            print(f"\n❌ Session {args.session_id} not found\n")
            sys.exit(1)

        with open(session_file) as f:
            session_data = json.load(f)

        session = BurstSession.from_dict(session_data)
        print(f"\n🛑 Shutting down {args.session_id}...")

        if args.provider == 'octaspace' and session.instance_id:
            api_key = os.environ.get('OCTASPACE_API_KEY', '')
            if api_key:
                client = OctaSpaceProvider.create_client(api_key)
                if client:
                    OctaSpaceProvider.shutdown_instance(client, session.instance_id)

        session.complete()
        log_session(session)
        print(f"   ✅ Shutdown complete. Cost: ${session.total_cost:.2f} ({session.actual_hours:.1f}h)")
        print()

    elif args.command == 'cost-report':
        update_cost_summary()
        print(f"\n📊 Cost report updated: {SESSIONS_FILE}\n")
        if SESSIONS_FILE.exists():
            with open(SESSIONS_FILE) as f:
                print(f.read())


if __name__ == '__main__':
    main()
