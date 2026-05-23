"use client";

import { ChevronRight } from "lucide-react";

interface QuickStatProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  trend?: "up" | "down" | "stable";
  href?: string;
  onClick?: () => void;
  subtitle?: string;
}

export function QuickStat({ label, value, icon: Icon, color, trend, href, onClick, subtitle }: QuickStatProps) {
  const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
  const trendColor = trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-gray-500";

  const content = (
    <>
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <div className="flex items-center gap-1">
          {trend && <span className={`text-xs ${trendColor}`}>{trendIcon}</span>}
          {(href || onClick) && <ChevronRight className="w-3 h-3 text-gray-600" />}
        </div>
      </div>
      <div className="text-xl font-bold text-white">{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
      {subtitle && <div className="text-[10px] text-gray-600 mt-0.5">{subtitle}</div>}
    </>
  );

  if (href) {
    return (
      <a
        href={href}
        className="bg-[#111118] border border-[#27272a] rounded-lg p-4 hover:border-indigo-500/40 hover:bg-[#14141f] transition-all block group"
      >
        {content}
      </a>
    );
  }

  if (onClick) {
    return (
      <button
        onClick={onClick}
        className="bg-[#111118] border border-[#27272a] rounded-lg p-4 hover:border-indigo-500/40 hover:bg-[#14141f] transition-all text-left w-full group cursor-pointer"
      >
        {content}
      </button>
    );
  }

  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4">
      {content}
    </div>
  );
}
