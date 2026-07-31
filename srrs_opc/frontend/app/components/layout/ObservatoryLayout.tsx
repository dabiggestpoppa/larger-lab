"use client";

import { ReactNode } from "react";
import LeftRail from "./LeftRail";
import RightPanel from "./RightPanel";
import BottomTimeline from "./BottomTimeline";
import TopBar from "./TopBar";

interface ObservatoryLayoutProps {
  children: ReactNode;
}

export default function ObservatoryLayout({ children }: ObservatoryLayoutProps) {
  return (
    <div className="observatory-grid">
      <TopBar />
      <LeftRail />
      <main className="overflow-hidden bg-[var(--bg-primary)]">
        {children}
      </main>
      <RightPanel />
      <BottomTimeline />
    </div>
  );
}
