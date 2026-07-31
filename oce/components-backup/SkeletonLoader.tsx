"use client";

export function SkeletonCard() {
  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4 animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="w-4 h-4 bg-[#1a1a24] rounded" />
      </div>
      <div className="text-xl font-bold bg-[#1a1a24] rounded h-7 w-20" />
      <div className="text-xs bg-[#1a1a24] rounded h-3 w-24 mt-2" />
    </div>
  );
}

export function SkeletonPanel() {
  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 space-y-4 animate-pulse">
      <div className="h-4 bg-[#1a1a24] rounded w-32" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-[#1a1a24] rounded-lg p-4 space-y-2">
            <div className="h-3 bg-[#27272a] rounded w-16" />
            <div className="h-6 bg-[#27272a] rounded w-20" />
          </div>
        ))}
      </div>
      <div className="h-24 bg-[#1a1a24] rounded" />
    </div>
  );
}

export function SkeletonHealthBars() {
  return (
    <div className="space-y-2 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="h-3 bg-[#1a1a24] rounded w-24" />
          <div className="flex-1 h-2 bg-[#1a1a24] rounded-full" />
          <div className="h-3 bg-[#1a1a24] rounded w-10" />
        </div>
      ))}
    </div>
  );
}
