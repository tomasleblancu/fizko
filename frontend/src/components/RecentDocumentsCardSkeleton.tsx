interface RecentDocumentsCardSkeletonProps {
  count?: number;
}

export function RecentDocumentsCardSkeleton({ count = 5 }: RecentDocumentsCardSkeletonProps) {
  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
      {/* Header skeleton */}
      <div className="mb-4 flex flex-shrink-0 items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-6 w-56 animate-pulse rounded-lg bg-slate-300 dark:bg-slate-700" />
          <div className="h-5 w-8 animate-pulse rounded-full bg-purple-200 dark:bg-purple-900/30" />
        </div>
        <div className="h-6 w-6 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
      </div>

      {/* Document list skeleton */}
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, index) => (
          <div
            key={index}
            className="flex items-center justify-between rounded-xl border border-slate-200/50 bg-slate-50/50 p-3 dark:border-slate-800/50 dark:bg-slate-800/30"
          >
            <div className="flex min-w-0 flex-1 items-center gap-3">
              {/* Status icon skeleton */}
              <div className="h-4 w-4 flex-shrink-0 animate-pulse rounded-full bg-slate-300 dark:bg-slate-700" />

              <div className="min-w-0 flex-1 space-y-2">
                {/* Document type and number skeleton */}
                <div className="flex items-center gap-2">
                  <div className="h-4 w-32 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                  <div className="h-4 w-16 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
                </div>

                {/* Date and description skeleton */}
                <div className="flex items-center gap-3">
                  <div className="h-3 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
                  <div className="h-3 w-40 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
                </div>
              </div>
            </div>

            {/* Amount skeleton */}
            <div className="ml-3 flex flex-col items-end space-y-1">
              <div className="h-4 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              <div className="h-3 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
