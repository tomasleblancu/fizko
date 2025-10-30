import { useState } from 'react';
import clsx from 'clsx';
import { ColorScheme } from "@/shared/hooks/useColorScheme";

interface OnboardingModalProps {
  scheme: ColorScheme;
  onComplete: (credentials: { rut: string; password: string }) => Promise<void>;
}

export function OnboardingModal({ scheme, onComplete }: OnboardingModalProps) {
  const [rut, setRut] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!rut.trim() || !password.trim()) {
      setError('Por favor completa todos los campos');
      return;
    }

    setLoading(true);
    try {
      await onComplete({ rut: rut.trim(), password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar credenciales');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-md animate-in fade-in duration-300 p-4">
      <div
        className={clsx(
          'w-full max-w-lg rounded-3xl border p-6 md:p-10 shadow-2xl backdrop-blur-xl animate-in zoom-in-95 duration-300 max-h-[90vh] overflow-y-auto',
          'bg-white/95 border-slate-200/60 shadow-emerald-500/10',
          'dark:bg-slate-900/95 dark:border-slate-700/60 dark:shadow-emerald-500/20'
        )}
      >
        {/* Header */}
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center animate-in zoom-in duration-500">
            <img
              src="/encabezado.png"
              alt="Fizko Logo"
              className="h-full w-full object-contain"
            />
          </div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            Conecta tu cuenta SII
          </h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-900/30">
              <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
            </div>
          )}

          <div className="space-y-1.5">
            <label
              htmlFor="rut"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              RUT
            </label>
            <input
              type="text"
              id="rut"
              value={rut}
              onChange={(e) => setRut(e.target.value)}
              placeholder="12.345.678-9"
              disabled={loading}
              className={clsx(
                'block w-full rounded-lg border px-3 py-2.5 text-sm transition-all',
                'border-slate-300 bg-white text-slate-900 placeholder-slate-400',
                'focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
                'dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500',
                'dark:focus:border-emerald-400 dark:focus:ring-emerald-400/20',
                'disabled:cursor-not-allowed disabled:opacity-50'
              )}
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Contraseña
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className={clsx(
                  'block w-full rounded-lg border pr-10 px-3 py-2.5 text-sm transition-all',
                  'border-slate-300 bg-white text-slate-900 placeholder-slate-400',
                  'focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
                  'dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500',
                  'dark:focus:border-emerald-400 dark:focus:ring-emerald-400/20',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors disabled:cursor-not-allowed"
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {showPassword ? (
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={clsx(
              'w-full rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-all mt-2',
              'bg-emerald-600 hover:bg-emerald-700',
              'focus:outline-none focus:ring-2 focus:ring-emerald-500/50',
              'active:scale-[0.98]',
              'disabled:cursor-not-allowed disabled:opacity-60'
            )}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Conectando...
              </span>
            ) : (
              'Conectar'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
