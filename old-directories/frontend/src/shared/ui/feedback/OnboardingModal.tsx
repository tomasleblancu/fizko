import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { ColorScheme } from "@/shared/hooks/useColorScheme";
import { useAuth } from "@/app/providers/AuthContext";
import { formatRUT } from "@/shared/lib/formatters";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-slate-900 dark:via-slate-900 dark:to-emerald-950 md:p-6">
      {/* Animated background patterns */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-emerald-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob dark:bg-emerald-500 dark:opacity-10" />
        <div className="absolute top-0 -right-4 w-72 h-72 bg-teal-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000 dark:bg-teal-500 dark:opacity-10" />
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-emerald-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000 dark:bg-emerald-500 dark:opacity-10" />
      </div>

      <div
        className={clsx(
          'relative w-full h-full md:h-auto md:max-w-xl md:rounded-xl md:border overflow-hidden md:shadow-xl',
          'bg-white/80 backdrop-blur-xl md:border-slate-200',
          'dark:bg-slate-900/80 dark:backdrop-blur-xl md:dark:border-slate-700',
          'flex flex-col'
        )}
      >
        <div className="relative flex-1 flex flex-col p-6 md:p-8 overflow-y-auto justify-center">
          {/* Header */}
          <div className="mb-8 md:mb-8">
            <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-2 text-center">
              Conecta tu cuenta SII
            </h2>
            <p className="text-sm md:text-base text-slate-600 dark:text-slate-400 mb-4 text-center">
              Ingresa tus credenciales para sincronizar tu información tributaria
            </p>

            {/* Security Badge */}
            <div className="flex items-start gap-2 p-3 rounded-lg bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900/50">
              <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-emerald-800 dark:text-emerald-300 mb-0.5">
                  Tus credenciales están protegidas
                </p>
                <p className="text-xs text-emerald-700 dark:text-emerald-400">
                  Tu contraseña se encripta con AES-256 antes de almacenarse. Solo tú y el SII pueden acceder a ella.
                </p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5 md:space-y-6">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-900/20">
                <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
              </div>
            )}

            <div className="space-y-2">
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
                onChange={(e) => {
                  const formatted = formatRUT(e.target.value);
                  setRut(formatted);
                }}
                placeholder="12.345.678-9"
                disabled={loading}
                className={clsx(
                  'block w-full rounded-lg border px-4 py-3 text-base transition-colors',
                  'border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
                  'dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              />
            </div>

            <div className="space-y-2">
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
                    'block w-full rounded-lg border pr-12 px-4 py-3 text-base transition-colors',
                    'border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
                    'dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100',
                    'disabled:cursor-not-allowed disabled:opacity-50'
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-400 disabled:cursor-not-allowed"
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
              <div className="space-y-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    {progressMessage || 'Conectando...'}
                  </span>
                  <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    {progress}%
                  </span>
                </div>
                <div className="h-1 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={clsx(
                'w-full rounded-lg px-4 py-3 text-base font-medium text-white transition-all',
                'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800',
                'disabled:cursor-not-allowed disabled:opacity-50',
                'shadow-sm hover:shadow-md'
              )}
            >
              {loading ? 'Conectando...' : 'Conectar con SII'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
