export function CompanyInfoCardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-blue-50 to-purple-50 p-3 dark:border-slate-800/70 dark:from-blue-950/30 dark:to-purple-950/30">
      <div className="flex items-center gap-2.5">
        {/* Icon skeleton */}
        <div className="h-9 w-9 animate-pulse rounded-lg bg-gradient-to-br from-slate-300 to-slate-400 dark:from-slate-700 dark:to-slate-600" />

        <div className="flex-1 space-y-1.5">
          {/* Business name skeleton */}
          <div className="h-5 w-3/4 animate-pulse rounded-lg bg-slate-300/70 dark:bg-slate-700/70" />

          {/* RUT skeleton */}
          <div className="h-3 w-1/2 animate-pulse rounded-lg bg-slate-200/70 dark:bg-slate-800/70" />
        </div>
      </div>
    </div>
  );
}
