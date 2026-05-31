import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CEREBUS Trading Dashboard",
  description: "Live trading dashboard — CEREBUS FX v4.0 | Symmetry Trap + P90 CASCADE",
};

const navItems = [
  { label: "Overview", href: "/", icon: "◈" },
  { label: "Strategies", href: "/strategies", icon: "⬡" },
  { label: "Trades", href: "/trades", icon: "▤" },
  { label: "Backtests", href: "/backtests", icon: "◠" },
  { label: "Health", href: "/health", icon: "♥" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="w-52 min-h-screen bg-dark-card border-r border-dark-border flex flex-col sticky top-0 shrink-0">
          {/* Logo */}
          <div className="p-4 border-b border-dark-border">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded bg-dark-success/20 border border-dark-success/40 flex items-center justify-center text-dark-success font-bold text-sm">
                C
              </div>
              <div>
                <div className="text-sm font-bold text-dark-primary tracking-wide">CEREBUS</div>
                <div className="text-[10px] text-dark-muted">Trading Dashboard v2.0</div>
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 p-3 space-y-0.5">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-dark-muted hover:text-dark-primary hover:bg-white/5 transition-colors"
              >
                <span className="text-xs opacity-50 w-4 text-center">{item.icon}</span>
                {item.label}
              </a>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-dark-border space-y-1">
            <div className="text-[10px] text-dark-muted">OCE Unified Field</div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-dark-success" />
              <span className="text-[10px] text-dark-success">Live</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-h-screen overflow-x-hidden">
          {/* Top Bar */}
          <header className="sticky top-0 z-10 bg-dark-bg/80 backdrop-blur-sm border-b border-dark-border px-6 py-3 flex items-center justify-between">
            <div>
              <h1 className="text-base font-semibold text-dark-primary">
                CEREBUS FX v4.0
              </h1>
              <p className="text-xs text-dark-muted">
                Symmetry Trap + P90 CASCADE | Live Trading Dashboard
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-dark-success/15 border border-dark-success/30">
                <span className="w-1.5 h-1.5 rounded-full bg-dark-success animate-pulse" />
                <span className="text-[10px] text-dark-success font-medium">LIVE</span>
              </div>
              <div className="text-[10px] text-dark-muted">
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
