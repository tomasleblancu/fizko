interface TaxSummaryCardSkeletonProps {
  isCompact?: boolean;
}

export function TaxSummaryCardSkeleton({ isCompact = false }: TaxSummaryCardSkeletonProps) {
  // Compact horizontal layout
  if (isCompact) {
    return (
      <div className="overflow-hidden rounded-2xl border border-slate-200/70 bg-white/90 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
        <div className="flex items-center gap-2 px-4 py-3">
          {/* Icon skeleton */}
          <div className="h-5 w-5 flex-shrink-0 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />

          <div className="flex flex-1 items-center gap-4 overflow-x-auto">
            {/* IVA skeleton */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div className="h-3.5 w-3.5 animate-pulse rounded bg-blue-300 dark:bg-blue-700" />
              <div className="h-3 w-12 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-3 w-20 animate-pulse rounded bg-blue-200 dark:bg-blue-800" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Full vertical layout
  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
      {/* Header skeleton with period selector */}
      <div className="relative mb-6">
        {/* Period Selector skeleton - Left side */}
        <div className="absolute left-0 top-0 z-10 flex items-center gap-1.5">
          <div className="h-6 w-14 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
          <div className="h-6 w-16 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
        </div>

        {/* Header content - Centered */}
        <div className="text-center">
          <div className="mx-auto mb-2 h-4 w-40 animate-pulse rounded-lg bg-slate-300 dark:bg-slate-700" />
          <div className="mx-auto h-10 w-48 animate-pulse rounded-lg bg-blue-300 dark:bg-blue-700" />
          <div className="mx-auto mt-1 h-3 w-32 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800" />
        </div>

        {/* Chart toggle button skeleton - Right side */}
        <div className="absolute right-0 top-0 z-10 h-9 w-9 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
      </div>

      {/* Grid skeleton - Ingresos y Gastos */}
      <div className="grid grid-cols-2 gap-4">
        {/* Ingresos skeleton */}
        <div className="rounded-xl border border-emerald-200/60 bg-gradient-to-br from-emerald-50 to-white p-4 text-center dark:border-emerald-900/40 dark:from-emerald-950/30 dark:to-slate-900/50">
          <div className="mb-2 flex items-center justify-center gap-2">
            <div className="h-4 w-4 animate-pulse rounded bg-emerald-300 dark:bg-emerald-700" />
            <div className="h-3 w-16 animate-pulse rounded bg-emerald-200/70 dark:bg-emerald-800/70" />
          </div>
          <div className="mx-auto h-8 w-28 animate-pulse rounded bg-emerald-200 dark:bg-emerald-800" />
        </div>

        {/* Gastos skeleton */}
        <div className="rounded-xl border border-rose-200/60 bg-gradient-to-br from-rose-50 to-white p-4 text-center dark:border-rose-900/40 dark:from-rose-950/30 dark:to-slate-900/50">
          <div className="mb-2 flex items-center justify-center gap-2">
            <div className="h-4 w-4 animate-pulse rounded bg-rose-300 dark:bg-rose-700" />
            <div className="h-3 w-16 animate-pulse rounded bg-rose-200/70 dark:bg-rose-800/70" />
          </div>
          <div className="mx-auto h-8 w-28 animate-pulse rounded bg-rose-200 dark:bg-rose-800" />
        </div>
      </div>
    </div>
  );
}
