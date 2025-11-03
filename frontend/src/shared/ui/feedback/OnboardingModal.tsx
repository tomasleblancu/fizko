import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { ColorScheme } from "@/shared/hooks/useColorScheme";
import { useAuth } from "@/app/providers/AuthContext";

interface OnboardingModalProps {
  scheme: ColorScheme;
  onComplete: (credentials: { rut: string; password: string }) => Promise<void>;
}

export function OnboardingModal({ scheme, onComplete }: OnboardingModalProps) {
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const [rut, setRut] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');

  // Listen for SSE progress events from useSession mutation
  useEffect(() => {
    const handleProgress = (event: Event) => {
      const customEvent = event as CustomEvent<{ progress: number; message: string }>;
      setProgress(customEvent.detail.progress);
      setProgressMessage(customEvent.detail.message);
    };

    window.addEventListener('sii-login-progress', handleProgress);

    return () => {
      window.removeEventListener('sii-login-progress', handleProgress);
    };
  }, []);

  const handleLogoClick = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (err) {
      console.error('Error during logout:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!rut.trim() || !password.trim()) {
      setError('Por favor completa todos los campos');
      return;
    }

    setLoading(true);
    setProgress(0);
    setProgressMessage('');

    try {
      await onComplete({ rut: rut.trim(), password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar credenciales');
      setProgress(0);
      setProgressMessage('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-white via-emerald-50/30 to-teal-50/20 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 md:from-black/40 md:via-slate-900/30 md:to-emerald-950/20 md:backdrop-blur-sm animate-in fade-in duration-500 md:p-4">
      <div
        className={clsx(
          'relative w-full h-full md:h-auto md:max-w-lg md:rounded-3xl md:border overflow-y-auto md:shadow-2xl md:backdrop-blur-2xl animate-in zoom-in-95 slide-in-from-bottom-8 duration-500 md:max-h-[90vh]',
          'bg-gradient-to-br from-white/95 via-white/90 to-emerald-50/50 md:border-emerald-200/40',
          'dark:from-slate-900/95 dark:via-slate-900/90 dark:to-slate-800/50 md:dark:border-emerald-500/20',
          'flex flex-col'
        )}
      >
        {/* Decorative gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-teal-500/5 pointer-events-none" />

        {/* Animated background shapes - hidden on mobile */}
        <div className="hidden md:block absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="hidden md:block absolute -bottom-24 -left-24 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

        <div className="relative flex-1 flex flex-col justify-center p-6 md:p-10">
          {/* Header */}
          <div className="mb-6 md:mb-8 text-center">
            <button
              type="button"
              onClick={handleLogoClick}
              disabled={loading}
              className="mx-auto mb-4 flex h-16 w-16 md:h-20 md:w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/30 animate-in zoom-in duration-500 hover:scale-105 transition-transform duration-200 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Volver al inicio"
            >
              <img
                src="/encabezado.png"
                alt="Fizko Logo"
                className="h-10 w-10 md:h-12 md:w-12 object-contain brightness-0 invert"
              />
            </button>
            <h2 className="text-xl md:text-3xl font-bold bg-gradient-to-r from-slate-900 via-emerald-900 to-teal-900 dark:from-white dark:via-emerald-100 dark:to-teal-100 bg-clip-text text-transparent mb-2 animate-in slide-in-from-top-4 duration-500">
              Conecta tu cuenta SII
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 animate-in slide-in-from-top-4 duration-500" style={{ animationDelay: '100ms' }}>
              Ingresa tus credenciales para sincronizar tu información tributaria
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4 md:space-y-5 max-w-md mx-auto w-full">
            {error && (
              <div className="rounded-xl border border-red-200/60 bg-gradient-to-br from-red-50 to-red-100/50 p-4 shadow-sm dark:border-red-900/40 dark:from-red-900/30 dark:to-red-800/20 animate-in slide-in-from-top-2 duration-300">
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
                RUT
              </label>
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
                <input
                  type="text"
                  id="rut"
                  value={rut}
                  onChange={(e) => setRut(e.target.value)}
                  placeholder="12.345.678-9"
                  disabled={loading}
                  className={clsx(
                    'relative block w-full rounded-xl border-2 px-4 py-3.5 md:py-3 text-base md:text-sm font-medium transition-all duration-200',
                    'border-slate-200 bg-white/80 backdrop-blur-sm text-slate-900 placeholder-slate-400',
                    'focus:border-emerald-500 focus:outline-none focus:ring-4 focus:ring-emerald-500/10',
                    'dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-100 dark:placeholder-slate-500',
                    'dark:focus:border-emerald-400 dark:focus:ring-emerald-400/10',
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
                Contraseña
              </label>
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className={clsx(
                    'relative block w-full rounded-xl border-2 pr-12 px-4 py-3.5 md:py-3 text-base md:text-sm font-medium transition-all duration-200',
                    'border-slate-200 bg-white/80 backdrop-blur-sm text-slate-900 placeholder-slate-400',
                    'focus:border-emerald-500 focus:outline-none focus:ring-4 focus:ring-emerald-500/10',
                    'dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-100 dark:placeholder-slate-500',
                    'dark:focus:border-emerald-400 dark:focus:ring-emerald-400/10',
                    'disabled:cursor-not-allowed disabled:opacity-50'
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-emerald-600 dark:text-slate-500 dark:hover:text-emerald-400 transition-all duration-200 hover:scale-110 disabled:cursor-not-allowed"
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

            {/* Progress Bar */}
            {loading && (
              <div className="space-y-3 p-5 rounded-2xl bg-gradient-to-br from-emerald-50/50 to-teal-50/30 dark:from-emerald-900/10 dark:to-teal-900/5 border border-emerald-200/30 dark:border-emerald-500/20 animate-in slide-in-from-bottom-4 duration-300">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-emerald-900 dark:text-emerald-100 flex items-center gap-2">
                    <svg className="h-4 w-4 animate-spin text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    {progressMessage || 'Conectando...'}
                  </span>
                  <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">
                    {progress}%
                  </span>
                </div>
                <div className="relative h-3 w-full overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-700/80 shadow-inner">
                  <div
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-500 transition-all duration-500 ease-out shadow-lg"
                    style={{ width: `${progress}%` }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent animate-pulse" />
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={clsx(
                'relative w-full rounded-xl px-6 py-4 md:py-3.5 text-base md:text-sm font-bold text-white transition-all duration-200 overflow-hidden group',
                'bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-600',
                'hover:from-emerald-700 hover:via-emerald-600 hover:to-teal-700',
                'focus:outline-none focus:ring-4 focus:ring-emerald-500/20',
                'active:scale-[0.98] shadow-lg shadow-emerald-500/30',
                'disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:from-emerald-600 disabled:hover:via-emerald-500 disabled:hover:to-teal-600'
              )}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              <span className="relative flex items-center justify-center gap-2">
                {loading ? (
                  <>
                    <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Conectando...
                  </>
                ) : (
                  <>
                    Conectar con SII
                    <svg className="h-5 w-5 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </span>
            </button>

            {/* Security note */}
            <div className="flex items-start gap-2 p-3 rounded-lg bg-slate-100/50 dark:bg-slate-800/30 border border-slate-200/50 dark:border-slate-700/50">
              <svg className="h-4 w-4 text-slate-500 dark:text-slate-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Tus credenciales son encriptadas y almacenadas de forma segura. Nunca compartiremos tu información.
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
