import { useState } from 'react';
import clsx from 'clsx';
import { ColorScheme } from '../hooks/useColorScheme';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-md animate-in fade-in duration-300">
      <div
        className={clsx(
          'w-full max-w-lg mx-4 rounded-3xl border p-10 shadow-2xl backdrop-blur-xl animate-in zoom-in-95 duration-300',
          'bg-white/95 border-slate-200/60 shadow-emerald-500/10',
          'dark:bg-slate-900/95 dark:border-slate-700/60 dark:shadow-emerald-500/20'
        )}
      >
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-24 w-24 items-center justify-center animate-in zoom-in duration-500">
            <img
              src="/encabezado.png"
              alt="Fizko Logo"
              className="h-full w-full object-contain"
            />
          </div>
          <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-3">
            Bienvenido a Fizko
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Para comenzar, conecta tu cuenta del Servicio de Impuestos Internos (SII) de forma segura
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-xl border-2 border-red-200 bg-red-50/80 backdrop-blur-sm p-4 dark:border-red-900/40 dark:bg-red-900/30 animate-in slide-in-from-top-2 duration-300">
              <div className="flex items-start gap-3">
                <svg className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-700 dark:text-red-200 flex-1">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <label
              htmlFor="rut"
              className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
            >
              RUT de la Empresa
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
                <svg className="h-5 w-5 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <input
                type="text"
                id="rut"
                value={rut}
                onChange={(e) => setRut(e.target.value)}
                placeholder="12.345.678-9"
                disabled={loading}
                className={clsx(
                  'block w-full rounded-xl border-2 pl-11 pr-4 py-3 text-sm font-medium transition-all relative',
                  'border-slate-300 bg-white/50 backdrop-blur-sm text-slate-900 placeholder-slate-400',
                  'focus:border-emerald-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-emerald-500/20',
                  'dark:border-slate-600 dark:bg-slate-800/50 dark:text-slate-100 dark:placeholder-slate-500',
                  'dark:focus:border-emerald-400 dark:focus:bg-slate-800 dark:focus:ring-emerald-400/20',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label
              htmlFor="password"
              className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
            >
              Contraseña del SII
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
                <svg className="h-5 w-5 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className={clsx(
                  'block w-full rounded-xl border-2 pl-11 pr-12 py-3 text-sm font-medium transition-all relative',
                  'border-slate-300 bg-white/50 backdrop-blur-sm text-slate-900 placeholder-slate-400',
                  'focus:border-emerald-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-emerald-500/20',
                  'dark:border-slate-600 dark:bg-slate-800/50 dark:text-slate-100 dark:placeholder-slate-500',
                  'dark:focus:border-emerald-400 dark:focus:bg-slate-800 dark:focus:ring-emerald-400/20',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors disabled:cursor-not-allowed z-10"
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {showPassword ? (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              'w-full rounded-xl px-6 py-3.5 text-sm font-semibold text-white transition-all mt-6',
              'bg-gradient-to-r from-emerald-600 to-teal-600',
              'hover:from-emerald-700 hover:to-teal-700 hover:shadow-xl hover:shadow-emerald-500/30 hover:scale-[1.02]',
              'focus:outline-none focus:ring-4 focus:ring-emerald-500/50',
              'active:scale-[0.98]',
              'disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100 disabled:hover:shadow-lg',
              'shadow-lg shadow-emerald-500/30'
            )}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
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
              <span className="flex items-center justify-center gap-2">
                Conectar con el SII
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
            )}
          </button>
        </form>

        {/* Info notice */}
        <div className="mt-8 rounded-xl border-2 border-emerald-200/60 bg-emerald-50/50 backdrop-blur-sm p-4 dark:border-emerald-900/40 dark:bg-emerald-900/20">
          <div className="flex items-start gap-3">
            <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <p className="text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed flex-1">
              <span className="font-bold">Tus datos están seguros.</span> Las credenciales se guardan de forma encriptada
              y solo se utilizan para obtener información tributaria de tu empresa directamente desde el SII.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
