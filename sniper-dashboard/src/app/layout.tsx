import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sniper Dashboard — Prop Firm Capital Optimizer",
  description: "Phase 5 Skeleton — Deployment monitoring & PES analytics",
};

const navItems = [
  { label: "Dashboard", href: "/", icon: "◈" },
  { label: "Firm Matrix", href: "#matrix", icon: "▦" },
  { label: "Deployments", href: "#deployments", icon: "▶" },
  { name: "PES History", href: "#pes", icon: "◠" },
  { label: "Promos", href: "#promos", icon: "◈" },
  { label: "Health", href: "#health", icon: "♥" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="w-56 min-h-screen bg-sniper-surface border-r border-sniper-border flex flex-col sticky top-0">
          {/* Logo */}
          <div className="p-4 border-b border-sniper-border">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-sniper-accent/20 border border-sniper-accent/40 flex items-center justify-center text-sniper-accent font-bold text-sm">
                S
              </div>
              <div>
                <div className="text-sm font-bold text-white">SNIPER</div>
                <div className="text-[10px] text-sniper-muted">Dashboard v0.1</div>
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 p-3 space-y-1">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <span className="text-xs opacity-60">{item.icon}</span>
                {item.label}
              </a>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-sniper-border">
            <div className="text-[10px] text-sniper-muted">
              Phase 5 Skeleton
            </div>
            <div className="text-[10px] text-sniper-muted">
              Engine: SALLOW_WELL
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-h-screen overflow-x-hidden">
          {/* Top Bar */}
          <header className="sticky top-0 z-10 bg-sniper-bg/80 backdrop-blur-sm border-b border-sniper-border px-6 py-3 flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-white">
                Prop Firm Capital Optimizer
              </h1>
              <p className="text-xs text-sniper-muted">
                Capital allocation decision layer — above the venue
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="badge badge-success text-[10px]">ENGINE ONLINE</div>
              <div className="text-[10px] text-sniper-muted">
                {new Date().toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </header>

          {/* Page Content */}
          <div className="p-6">{children}</div>
        </main>
      </body>
    </html>
  );
}
