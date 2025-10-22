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
            {/* Revenue skeleton */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div className="h-3.5 w-3.5 animate-pulse rounded bg-emerald-300 dark:bg-emerald-700" />
              <div className="h-3 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-3 w-20 animate-pulse rounded bg-emerald-200 dark:bg-emerald-800" />
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

            {/* Expenses skeleton */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div className="h-3.5 w-3.5 animate-pulse rounded bg-rose-300 dark:bg-rose-700" />
              <div className="h-3 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-3 w-20 animate-pulse rounded bg-rose-200 dark:bg-rose-800" />
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

            {/* IVA skeleton */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div className="h-3 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-3 w-20 animate-pulse rounded bg-blue-200 dark:bg-blue-800" />
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

            {/* Income Tax skeleton */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div className="h-3.5 w-3.5 animate-pulse rounded bg-purple-300 dark:bg-purple-700" />
              <div className="h-3 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-3 w-20 animate-pulse rounded bg-purple-200 dark:bg-purple-800" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Full vertical layout
  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
      {/* Header skeleton */}
      <div className="mb-4 flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-6 w-40 animate-pulse rounded-lg bg-slate-300 dark:bg-slate-700" />
          <div className="h-3 w-32 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800" />
        </div>
        <div className="h-6 w-6 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
      </div>

      <div className="space-y-3">
        {/* Revenue skeleton */}
        <div className="flex items-center justify-between rounded-xl bg-emerald-50 p-3 dark:bg-emerald-950/30">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-pulse rounded bg-emerald-300 dark:bg-emerald-700" />
            <div className="h-4 w-16 animate-pulse rounded bg-emerald-200/70 dark:bg-emerald-800/70" />
          </div>
          <div className="h-4 w-24 animate-pulse rounded bg-emerald-200 dark:bg-emerald-800" />
        </div>

        {/* Expenses skeleton */}
        <div className="flex items-center justify-between rounded-xl bg-rose-50 p-3 dark:bg-rose-950/30">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-pulse rounded bg-rose-300 dark:bg-rose-700" />
            <div className="h-4 w-16 animate-pulse rounded bg-rose-200/70 dark:bg-rose-800/70" />
          </div>
          <div className="h-4 w-24 animate-pulse rounded bg-rose-200 dark:bg-rose-800" />
        </div>

        {/* IVA skeleton */}
        <div className="space-y-2 rounded-xl bg-blue-50 p-3 dark:bg-blue-950/30">
          <div className="flex items-center justify-between">
            <div className="h-3 w-20 animate-pulse rounded bg-blue-200/70 dark:bg-blue-800/70" />
            <div className="h-3 w-20 animate-pulse rounded bg-blue-200 dark:bg-blue-800" />
          </div>
          <div className="flex items-center justify-between">
            <div className="h-3 w-20 animate-pulse rounded bg-blue-200/70 dark:bg-blue-800/70" />
            <div className="h-3 w-20 animate-pulse rounded bg-blue-200 dark:bg-blue-800" />
          </div>
          <div className="border-t border-blue-200 pt-2 dark:border-blue-800">
            <div className="flex items-center justify-between">
              <div className="h-4 w-16 animate-pulse rounded bg-blue-200/70 dark:bg-blue-800/70" />
              <div className="h-4 w-24 animate-pulse rounded bg-blue-200 dark:bg-blue-800" />
            </div>
          </div>
        </div>

        {/* Income Tax skeleton */}
        <div className="flex items-center justify-between rounded-xl bg-purple-50 p-3 dark:bg-purple-950/30">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-pulse rounded bg-purple-300 dark:bg-purple-700" />
            <div className="h-4 w-32 animate-pulse rounded bg-purple-200/70 dark:bg-purple-800/70" />
          </div>
          <div className="h-4 w-24 animate-pulse rounded bg-purple-200 dark:bg-purple-800" />
        </div>
      </div>
    </div>
  );
}
