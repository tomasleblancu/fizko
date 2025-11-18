import { useState, useEffect, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { useSIILogin } from '@/shared/hooks/useSIILogin';
import { useCompanyContext } from '@/app/providers/CompanyContext';
import { formatRUT } from '@/shared/lib/formatters';
import { SetupQuestionsCarousel } from '@/features/onboarding/ui/SetupQuestionsCarousel';

interface AddCompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ModalStep = 'credentials' | 'setup';

export function AddCompanyModal({ isOpen, onClose }: AddCompanyModalProps) {
  const { mutateAsync: loginToSII, isPending } = useSIILogin();
  const { setSelectedCompany } = useCompanyContext();
  const [step, setStep] = useState<ModalStep>('credentials');
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [companyName, setCompanyName] = useState<string | null>(null);
  const [rut, setRut] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');

  // Listen for SSE progress events
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

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setStep('credentials');
      setCompanyId(null);
      setCompanyName(null);
      setRut('');
      setPassword('');
      setError(null);
      setProgress(0);
      setProgressMessage('');
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!rut.trim() || !password.trim()) {
      setError('Por favor completa todos los campos');
      return;
    }

    setProgress(0);
    setProgressMessage('Conectando con el SII...');

    try {
      const result = await loginToSII({
        rut: rut.trim(),
        password: password.trim(),
      });

      // Debug log
      console.log('SII Login result:', result);
      console.log('needs_initial_setup:', result.needs_initial_setup);

      // Store company information
      setCompanyId(result.company.id);
      setCompanyName(result.company.business_name || result.company.rut);

      // Check if needs initial setup
      if (result.needs_initial_setup) {
        // Show setup questions step
        setProgressMessage('Empresa conectada. Configurando...');
        setProgress(100);
        setTimeout(() => {
          setStep('setup');
          setProgress(0);
          setProgressMessage('');
        }, 500);
      } else {
        // Success - select the new company and reload
        setProgressMessage('Empresa agregada exitosamente. Recargando...');
        setProgress(100);

        // Wait a bit to show success message
        setTimeout(() => {
          // Set the new company as selected and reload
          setSelectedCompany(result.company.id);
        }, 1000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al conectar con el SII');
      setProgress(0);
      setProgressMessage('');
    }
  };

  const handleSetupComplete = () => {
    // Setup completed - select the new company and reload
    if (companyId) {
      setSelectedCompany(companyId);
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={isPending ? () => {} : onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-slate-900 p-6 text-left align-middle shadow-xl transition-all">
                {step === 'credentials' ? (
                  <>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <Dialog.Title
                          as="h3"
                          className="text-lg font-semibold text-slate-900 dark:text-slate-100"
                        >
                          Agregar Empresa
                        </Dialog.Title>
                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                          Conecta una nueva empresa con tus credenciales del SII
                        </p>
                      </div>
                      {!isPending && (
                        <button
                          onClick={onClose}
                          className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors"
                        >
                          <X className="h-5 w-5" />
                        </button>
                      )}
                    </div>

                {/* Logo Section */}
                <div className="mb-6 flex items-center justify-center gap-3">
                  <img
                    src="/encabezado.png"
                    alt="Fizko Icon"
                    className="h-10 w-auto"
                  />
                  <div className="flex flex-col items-center justify-center mx-2 h-8">
                    {isPending ? (
                      <svg className="h-5 w-5 text-emerald-500 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <>
                        <svg className="h-3 w-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                        </svg>
                        <svg className="h-3 w-6 text-emerald-500 -mt-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                        </svg>
                      </>
                    )}
                  </div>
                  <img
                    src="/logo_sii.png"
                    alt="SII"
                    className="h-10 w-auto"
                  />
                </div>

                {/* Security Badge */}
                <div className="mb-6 flex items-start gap-2 p-3 rounded-lg bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900/50">
                  <svg className="h-5 w-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-emerald-800 dark:text-emerald-300">
                      Conexión segura
                    </p>
                    <p className="text-xs text-emerald-700 dark:text-emerald-400">
                      Tu contraseña se encripta con AES-256 antes de almacenarse
                    </p>
                  </div>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-900/20 flex items-start gap-2">
                      <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <label
                      htmlFor="add-company-rut"
                      className="block text-sm font-medium text-slate-700 dark:text-slate-300"
                    >
                      RUT
                    </label>
                    <input
                      type="text"
                      id="add-company-rut"
                      name="add-company-rut"
                      autoComplete="off"
                      value={rut}
                      onChange={(e) => {
                        const formatted = formatRUT(e.target.value);
                        setRut(formatted);
                      }}
                      placeholder="12.345.678-9"
                      disabled={isPending}
                      className={clsx(
                        'block w-full rounded-lg border px-3 py-2.5 text-sm transition-colors',
                        'border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
                        'dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100',
                        'disabled:cursor-not-allowed disabled:opacity-50'
                      )}
                    />
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="add-company-password"
                      className="block text-sm font-medium text-slate-700 dark:text-slate-300"
                    >
                      Contraseña
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        id="add-company-password"
                        name="add-company-password"
                        autoComplete="off"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        disabled={isPending}
                        className={clsx(
                          'block w-full rounded-lg border pr-10 px-3 py-2.5 text-sm transition-colors',
                          'border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20',
                          'dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100',
                          'disabled:cursor-not-allowed disabled:opacity-50'
                        )}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isPending}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-400 disabled:cursor-not-allowed"
                        aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
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
                  {isPending && (
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

                  {/* Actions */}
                  <div className="flex gap-3 pt-2">
                    <button
                      type="button"
                      onClick={onClose}
                      disabled={isPending}
                      className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={isPending}
                      className="flex-1 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-emerald-500 dark:hover:bg-emerald-600 transition-colors"
                    >
                      {isPending ? 'Conectando...' : 'Conectar'}
                    </button>
                  </div>
                </form>
                  </>
                ) : (
                  <>
                    {/* Setup Questions Step */}
                    <div className="flex items-start justify-between mb-4">
                      <Dialog.Title
                        as="h3"
                        className="text-lg font-semibold text-slate-900 dark:text-slate-100"
                      >
                        Configuración Inicial
                      </Dialog.Title>
                    </div>

                    <SetupQuestionsCarousel
                      companyId={companyId!}
                      companyName={companyName || undefined}
                      onComplete={handleSetupComplete}
                      showCompanyHeader={false}
                    />
                  </>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
