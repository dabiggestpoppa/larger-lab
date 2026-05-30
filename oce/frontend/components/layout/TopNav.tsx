"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUIStore } from "@/stores/uiStore";

const navItems = [
  { href: "/agents", label: "Agents", icon: "◉" },
  { href: "/topology", label: "Topology", icon: "▦" },
  { href: "/entropy", label: "Entropy", icon: "◎" },
  { href: "/repair", label: "Repair", icon: "◈" },
  { href: "/attractors", label: "Attractors", icon: "◉" },
  { href: "/playback", label: "Playback", icon: "▶" },
  { href: "/experiments", label: "Experiments", icon: "⚗" },
  { href: "/events", label: "Events", icon: "⚡" },
  { href: "/modules", label: "Modules", icon: "▣" },
  { href: "/tests", label: "Tests", icon: "✓" },
  { href: "/browser", label: "Browser", icon: "🌐" },
  { href: "/substrate", label: "Substrate", icon: "🖥️" },
  { href: "/persistence", label: "Persistence", icon: "◷" },
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/vault", label: "Vault", icon: "📂" },
];

export default function TopNav() {
  const pathname = usePathname();
  const { activeLayer, setActiveLayer } = useUIStore();

  return (
    <header className="h-12 bg-[var(--bg-secondary)] border-b border-[var(--border-default)] flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-6">
        <span className="text-xs font-mono font-bold text-[var(--text-primary)]">
          OCE
        </span>
        <nav className="flex items-center gap-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 text-xs font-mono transition-colors ${
                  isActive
                    ? "text-[var(--accent-primary)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                <span className="text-[10px]">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-[10px] font-mono text-[var(--text-muted)]">Layer:</span>
        <div className="flex items-center gap-1">
          {(["layer1", "layer2", "layer3"] as const).map((layer) => (
            <button
              key={layer}
              onClick={() => setActiveLayer(layer)}
              className={`px-2 py-0.5 text-[10px] font-mono rounded border ${
                activeLayer === layer
                  ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)]"
              }`}
            >
              {layer === "layer1" ? "1" : layer === "layer2" ? "2" : "3"}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}