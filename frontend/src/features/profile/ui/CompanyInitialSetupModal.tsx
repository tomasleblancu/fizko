import { useState } from 'react';
import clsx from 'clsx';
import { ColorScheme } from "@/shared/hooks/useColorScheme";
import { useCompanySettings, CompanySettingsUpdate } from "@/shared/hooks/useCompanySettings";

interface CompanyInitialSetupModalProps {
  companyId: string;
  companyName: string;
  scheme: ColorScheme;
  onComplete: () => void;
}

type SettingValue = boolean | null;

interface Question {
  key: keyof CompanySettingsUpdate;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const questions: Question[] = [
  {
    key: 'has_formal_employees',
    title: '¿Tiene empleados con contrato de trabajo formal?',
    description: 'Empleados con contrato indefinido, a plazo fijo o por obra.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    key: 'has_imports',
    title: '¿Realiza importaciones?',
    description: 'Compra de productos o servicios desde el extranjero.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    key: 'has_exports',
    title: '¿Realiza exportaciones?',
    description: 'Venta de productos o servicios hacia el extranjero.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
      </svg>
    ),
  },
  {
    key: 'has_lease_contracts',
    title: '¿Tiene contratos de arriendo?',
    description: 'Arrienda oficinas, locales, bodegas u otros inmuebles.',
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
];

export function CompanyInitialSetupModal({ companyId, companyName, scheme, onComplete }: CompanyInitialSetupModalProps) {
  const { updateSettings } = useCompanySettings(companyId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  // State for each question - start with null (unanswered)
  const [answers, setAnswers] = useState<Record<string, SettingValue>>({
    has_formal_employees: null,
    has_imports: null,
    has_exports: null,
    has_lease_contracts: null,
  });

  const currentQuestion = questions[currentStep];
  const isLastQuestion = currentStep === questions.length - 1;
  const progress = ((currentStep + 1) / questions.length) * 100;

  const handleAnswer = (value: SettingValue) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.key]: value,
    }));

    // Auto-advance to next question after short delay
    setTimeout(() => {
      if (isLastQuestion) {
        // Don't auto-submit, let user click "Finalizar"
      } else {
        setCurrentStep(prev => prev + 1);
      }
    }, 300);
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };


  const handleComplete = async () => {
    setLoading(true);
    setError(null);

    try {
      await updateSettings.mutateAsync(answers as CompanySettingsUpdate);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar configuración');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-slate-900 dark:via-slate-900 dark:to-emerald-950 md:p-4">
      {/* Animated background patterns */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-emerald-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob dark:bg-emerald-500 dark:opacity-10" />
        <div className="absolute top-0 -right-4 w-72 h-72 bg-teal-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000 dark:bg-teal-500 dark:opacity-10" />
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-emerald-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000 dark:bg-emerald-500 dark:opacity-10" />
      </div>

      <div
        className={clsx(
          'relative w-full h-full md:h-auto md:max-w-lg md:rounded-xl md:border overflow-hidden md:shadow-xl',
          'bg-white/80 backdrop-blur-xl md:border-slate-200',
          'dark:bg-slate-900/80 dark:backdrop-blur-xl md:dark:border-slate-700',
          'flex flex-col'
        )}
      >
        <div className="relative flex-1 flex flex-col p-6 md:p-6 overflow-y-auto">
          {/* Header */}
          <div className="mb-6 md:mb-6">
            <h2 className="text-lg md:text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1">
              Configuración inicial
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {companyName}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6 md:mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {currentStep + 1} de {questions.length}
              </span>
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
              <div
                className="h-full bg-emerald-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Question Card */}
          <div className="mb-6 md:mb-6 flex-1 flex flex-col justify-center" key={currentStep}>
            <div className="flex items-start gap-3 mb-6">
              <div className="flex-shrink-0 text-slate-400 dark:text-slate-500 mt-1">
                {currentQuestion.icon}
              </div>
              <h3 className="text-base md:text-base font-medium text-slate-900 dark:text-slate-100 leading-relaxed">
                {currentQuestion.title}
              </h3>
            </div>

            {/* Answer Options */}
            <div className="space-y-3">
              <button
                onClick={() => handleAnswer(true)}
                disabled={loading}
                className={clsx(
                  'w-full p-4 md:p-3 rounded-lg border text-left transition-all flex items-center gap-2',
                  answers[currentQuestion.key] === true
                    ? 'border-emerald-500 bg-emerald-50 dark:border-emerald-500 dark:bg-emerald-900/20'
                    : 'border-slate-200 bg-white hover:border-emerald-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-emerald-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <svg className={clsx(
                  'h-4 w-4 flex-shrink-0',
                  answers[currentQuestion.key] === true
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-slate-400 dark:text-slate-500'
                )} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className={clsx(
                  'text-sm font-medium',
                  answers[currentQuestion.key] === true
                    ? 'text-emerald-700 dark:text-emerald-300'
                    : 'text-slate-700 dark:text-slate-300'
                )}>
                  Sí
                </span>
              </button>

              <button
                onClick={() => handleAnswer(false)}
                disabled={loading}
                className={clsx(
                  'w-full p-4 md:p-3 rounded-lg border text-left transition-all flex items-center gap-2',
                  answers[currentQuestion.key] === false
                    ? 'border-slate-400 bg-slate-50 dark:border-slate-500 dark:bg-slate-800/50'
                    : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <svg className={clsx(
                  'h-4 w-4 flex-shrink-0',
                  answers[currentQuestion.key] === false
                    ? 'text-slate-600 dark:text-slate-400'
                    : 'text-slate-400 dark:text-slate-500'
                )} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span className={clsx(
                  'text-sm font-medium',
                  answers[currentQuestion.key] === false
                    ? 'text-slate-700 dark:text-slate-300'
                    : 'text-slate-700 dark:text-slate-300'
                )}>
                  No
                </span>
              </button>

              <button
                onClick={() => handleAnswer(null)}
                disabled={loading}
                className={clsx(
                  'w-full p-4 md:p-3 rounded-lg border text-left transition-all flex items-center gap-2',
                  answers[currentQuestion.key] === null
                    ? 'border-slate-300 bg-slate-100 dark:border-slate-600 dark:bg-slate-800/30'
                    : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <svg className={clsx(
                  'h-4 w-4 flex-shrink-0',
                  answers[currentQuestion.key] === null
                    ? 'text-slate-500 dark:text-slate-400'
                    : 'text-slate-400 dark:text-slate-500'
                )} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className={clsx(
                  'text-sm font-medium',
                  answers[currentQuestion.key] === null
                    ? 'text-slate-600 dark:text-slate-400'
                    : 'text-slate-700 dark:text-slate-300'
                )}>
                  No estoy seguro
                </span>
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-900/20">
              <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
            </div>
          )}
        </div>

        {/* Navigation Buttons - Fixed at bottom on mobile */}
        <div className="sticky bottom-0 left-0 right-0 p-6 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 md:border-t-0 md:static md:bg-transparent md:dark:bg-transparent">
          <div className="flex items-center justify-between gap-3">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                disabled={loading}
                className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 disabled:opacity-50"
              >
                ← Anterior
              </button>
            )}

            {isLastQuestion && (
              <button
                onClick={handleComplete}
                disabled={loading}
                className={clsx(
                  'ml-auto px-6 py-3 md:px-5 md:py-2 text-sm font-medium text-white rounded-lg transition-all',
                  'bg-emerald-600 hover:bg-emerald-700',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                {loading ? 'Guardando...' : 'Finalizar'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
