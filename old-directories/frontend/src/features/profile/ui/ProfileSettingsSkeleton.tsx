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
        <div className="space-y-3">
          {/* User Info Card Skeleton - Compact */}
          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3.5 w-40 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="h-3 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              </div>
            </div>
          </div>

          {/* Contact Information Card Skeleton - Compact */}
          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center justify-between">
              <div className="h-4 w-40 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
              <div className="h-6 w-12 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            </div>

            <div className="space-y-3">
              {/* Nombre y Apellido en fila */}
              <div className="grid grid-cols-2 gap-3">
                {[1, 2].map((i) => (
                  <div key={i}>
                    <div className="mb-1 h-3 w-16 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                    <div className="h-8 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
                  </div>
                ))}
              </div>

              {/* Celular */}
              <div>
                <div className="mb-1 h-3 w-12 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                <div className="h-8 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
              </div>

              {/* Verification status */}
              <div className="h-9 w-full animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800/50" />
            </div>
          </div>

          {/* Email Card Skeleton - Compact */}
          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-1 h-3 w-12 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-8 w-full animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700" />
            <div className="mt-1 h-3 w-36 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          </div>

          {/* SII Credentials Card Skeleton - Compact */}
          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-2 h-4 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          </div>

          {/* Logout Card Skeleton - Compact */}
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
            <div className="flex items-center justify-between">
              <div className="flex-1 space-y-1.5">
                <div className="h-4 w-24 animate-pulse rounded bg-red-200 dark:bg-red-800" />
                <div className="h-3 w-32 animate-pulse rounded bg-red-200 dark:bg-red-800" />
              </div>
              <div className="h-7 w-16 animate-pulse rounded-lg bg-red-200 dark:bg-red-800" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
