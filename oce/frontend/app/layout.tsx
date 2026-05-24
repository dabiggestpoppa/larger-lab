import type { Metadata } from "next";
import "./globals.css";
import TopNav from "@/components/layout/TopNav";
import StatusBar from "@/components/layout/StatusBar";
import RightPanel from "@/components/layout/RightPanel";

export const metadata: Metadata = {
  title: "OCE — Operator Continuity Engine",
  description: "Operational cockpit for the Operator Continuity Engine",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen max-h-[100dvh] overflow-hidden antialiased">
        <div className="flex flex-col h-full">
          <TopNav />
          <div className="flex flex-1 overflow-hidden">
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
            <RightPanel />
          </div>
          <StatusBar />
        </div>
      </body>
    </html>
  );
}
