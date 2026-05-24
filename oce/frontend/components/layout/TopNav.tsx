"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/tasks", label: "Tasks" },
  { href: "/agents", label: "Agents" },
  { href: "/chaos", label: "Chaos" },
  { href: "/settings", label: "Settings" },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <nav className="h-12 bg-bg-secondary border-b border-border-light flex items-center px-4 gap-1 shrink-0">
      <Link href="/dashboard" className="text-sm font-semibold text-accent-primary mr-4 no-underline">
        OCE
      </Link>
      {navItems.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`text-xs px-3 py-1.5 rounded-md no-underline transition-colors ${
              isActive
                ? "bg-accent-primary/10 text-accent-primary font-medium"
                : "text-text-secondary hover:bg-bg-tertiary hover:text-text-primary"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
      <div className="flex-1" />
      <div className="flex items-center gap-2">
        <span className="badge badge-success">● Live</span>
        <span className="text-xs text-text-muted">:3000</span>
      </div>
    </nav>
  );
}
