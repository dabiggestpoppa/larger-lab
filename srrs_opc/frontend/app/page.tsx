"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/topology");
  }, [router]);

  return (
    <div className="flex items-center justify-center h-full">
      <p className="text-xs font-mono text-[var(--text-muted)]">Loading Observatory...</p>
    </div>
  );
}
