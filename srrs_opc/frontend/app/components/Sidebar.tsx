"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard", icon: "◈" },
  { href: "/modules", label: "Modules", icon: "⬡" },
  { href: "/topology", label: "Topology", icon: "⬢" },
  { href: "/tests", label: "Tests", icon: "✓" },
  { href: "/events", label: "Events", icon: "◉" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-bg-secondary border-r border-default flex flex-col z-50">
      {/* Logo */}
      <div className="p-5 border-b border-default">
        <h1 className="text-lg font-bold text-accent-blue tracking-wide">
          ◈ SRRA-OPH
        </h1>
        <p className="text-xs text-gray-500 mt-1">
          Self-Repairing Recursive Architecture
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-5 py-3 text-sm transition-colors ${
                isActive
                  ? "bg-bg-tertiary text-accent-blue border-r-2 border-accent-blue"
                  : "text-gray-400 hover:bg-bg-tertiary hover:text-gray-200"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-5 border-t border-default">
        <div className="flex items-center gap-2">
          <span className="status-dot active" />
          <span className="text-xs text-gray-500">System Online</span>
        </div>
        <p className="text-xs text-gray-600 mt-2">v1.0.0 • 9 Phases</p>
      </div>
    </aside>
  );
}
