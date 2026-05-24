"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/topology", label: "Topology", icon: "◉" },
  { href: "/entropy", label: "Entropy", icon: "▦" },
  { href: "/repair", label: "Repair", icon: "◈" },
  { href: "/attractors", label: "Attractors", icon: "◎" },
  { href: "/experiments", label: "Experiments", icon: "▣" },
  { href: "/playback", label: "Playback", icon: "▶" },
];

export default function LeftRail() {
  const pathname = usePathname();

  return (
    <aside
      className="flex flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-y-auto observatory-scroll"
      style={{ width: "var(--left-rail-width)" }}
    >
      {/* Logo / Title */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h1 className="text-sm font-mono font-bold text-[var(--text-primary)] tracking-wider">
          SRRA OBSERVATORY
        </h1>
        <p className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
          Continuity Substrate Monitor
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-mono transition-colors ${
                isActive
                  ? "bg-[var(--bg-tertiary)] text-[var(--field-active)] border-l-2 border-[var(--field-active)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] border-l-2 border-transparent"
              }`}
            >
              <span className="text-[10px]">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Status */}
      <div className="px-4 py-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--field-stable)] node-pulse" />
          <span className="text-[10px] font-mono text-[var(--text-muted)]">
            SYSTEM STABLE
          </span>
        </div>
      </div>
    </aside>
  );
}
