import type { Metadata } from "next";
import "./globals.css";
import "./styles/tokens.css";
import ObservatoryLayout from "./components/layout/ObservatoryLayout";

export const metadata: Metadata = {
  title: "SRRA-OPH Observatory — Continuity Substrate Monitor",
  description: "Observability interface for SRRA+OPH runtime substrate",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[var(--bg-primary)] text-[var(--text-primary)] antialiased">
        <ObservatoryLayout>{children}</ObservatoryLayout>
      </body>
    </html>
  );
}
