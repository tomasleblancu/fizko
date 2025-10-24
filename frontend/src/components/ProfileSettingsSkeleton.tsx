export function ProfileSettingsSkeleton() {
  return (
    <section className="flex h-full w-full flex-col overflow-hidden">
      {/* Tabs Skeleton */}
      <div className="flex-shrink-0 border-b border-slate-200/60 px-6 dark:border-slate-800/60">
        <div className="flex gap-1">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-11 w-24 animate-pulse rounded-t-lg bg-slate-200/70 dark:bg-slate-700/70"
            />
          ))}
        </div>
      </div>

      {/* Content Skeleton */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-4">
          {/* User Info Card Skeleton */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="h-3 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              </div>
            </div>
          </div>

          {/* Contact Information Card Skeleton */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <div className="h-5 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-8 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            </div>

            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i}>
                  <div className="mb-1 h-4 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                  <div className="h-10 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
                </div>
              ))}
            </div>
          </div>

          {/* Email Card Skeleton */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-1 h-4 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-10 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
            <div className="mt-1 h-3 w-40 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          </div>

          {/* SII Credentials Card Skeleton */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 h-5 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-4 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          </div>
        </div>
      </div>
    </section>
  );
}
