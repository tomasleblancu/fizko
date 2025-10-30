type ErrorOverlayProps = {
  error: string | null;
  fallbackMessage: string | null;
  onRetry: (() => void) | null;
  retryLabel?: string;
};

export function ErrorOverlay({
  error,
  fallbackMessage,
  onRetry,
  retryLabel = "Reintentar",
}: ErrorOverlayProps) {
  const message = error ?? fallbackMessage;

  if (!message) {
    return null;
  }

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/95 backdrop-blur-sm transition-all dark:bg-slate-950/95">
      <div className="mx-auto max-w-md space-y-4 px-6 text-center">
        <div className="space-y-2">
          {error && (
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
              <svg
                className="h-6 w-6 text-red-600 dark:text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
          )}
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {error ? "Error al cargar el asistente" : "Cargando..."}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {retryLabel}
          </button>
        )}
      </div>
    </div>
  );
}
