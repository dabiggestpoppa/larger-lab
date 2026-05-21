"use client";

export function SkeletonCard() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-bg-tertiary rounded w-32" />
          <div className="h-3 bg-bg-tertiary rounded w-20" />
        </div>
        <div className="w-3 h-3 bg-bg-tertiary rounded-full" />
      </div>
      <div className="flex items-center gap-3 mt-3">
        <div className="h-5 bg-bg-tertiary rounded w-16" />
        <div className="h-5 bg-bg-tertiary rounded w-14" />
      </div>
    </div>
  );
}

export function SkeletonStatCard() {
  return (
    <div className="card animate-pulse">
      <div className="h-3 bg-bg-tertiary rounded w-16 mb-2" />
      <div className="h-7 bg-bg-tertiary rounded w-12" />
      <div className="h-3 bg-bg-tertiary rounded w-20 mt-1" />
    </div>
  );
}

export function SkeletonPhaseBar() {
  return (
    <div className="flex items-center gap-4 animate-pulse">
      <span className="text-xs text-gray-500 w-6">P-</span>
      <div className="flex-1 bg-bg-tertiary rounded-full h-2" />
      <span className="text-xs text-gray-400 w-24 truncate">---</span>
      <span className="text-xs px-2 py-0.5 rounded bg-bg-tertiary w-12 h-4" />
    </div>
  );
}

export function SkeletonEventRow() {
  return (
    <div className="flex items-center gap-3 py-2 animate-pulse">
      <span className="status-dot active" />
      <span className="text-xs text-gray-500 font-mono w-32 shrink-0 bg-bg-tertiary rounded h-3" />
      <span className="text-xs text-gray-300 flex-1 truncate bg-bg-tertiary rounded h-3" />
      <span className="text-xs text-gray-600 bg-bg-tertiary rounded h-3 w-16" />
    </div>
  );
}
