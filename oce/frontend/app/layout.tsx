import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OCE — Operator Continuity Engine",
  description: "Clean operator interface for the Operator Continuity Engine",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="text-gray-700 bg-[#EDEFF2]/90 h-screen max-h-[100dvh] overflow-hidden antialiased">
        {children}
      </body>
    </html>
  );
}
