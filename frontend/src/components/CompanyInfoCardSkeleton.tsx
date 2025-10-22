export function CompanyInfoCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-blue-50 to-purple-50 p-6 dark:border-slate-800/70 dark:from-blue-950/30 dark:to-purple-950/30">
      <div className="flex items-center gap-3">
        {/* Icon skeleton */}
        <div className="h-12 w-12 animate-pulse rounded-xl bg-gradient-to-br from-slate-300 to-slate-400 dark:from-slate-700 dark:to-slate-600" />

        <div className="flex-1 space-y-2">
          {/* Business name skeleton */}
          <div className="h-6 w-3/4 animate-pulse rounded-lg bg-slate-300/70 dark:bg-slate-700/70" />

          {/* RUT skeleton */}
          <div className="h-4 w-1/2 animate-pulse rounded-lg bg-slate-200/70 dark:bg-slate-800/70" />
        </div>
      </div>
    </div>
  );
}
