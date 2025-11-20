import { useState } from 'react';
import clsx from 'clsx';
import { useCompanySettings, CompanySettingsUpdate } from "@/shared/hooks/useCompanySettings";
import { setupQuestions, getInitialAnswers, type SettingValue } from "@/pages/onboarding/config/setup-questions";

interface SetupQuestionsCarouselProps {
  companyId: string;
  companyName?: string;
  onComplete: () => void | Promise<void>;
  onSkip?: () => void;
  showCompanyHeader?: boolean;
}

export function SetupQuestionsCarousel({
  companyId,
  companyName,
  onComplete,
  onSkip,
  showCompanyHeader = true,
}: SetupQuestionsCarouselProps) {
  const { updateSettings } = useCompanySettings(companyId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, SettingValue>>(getInitialAnswers());

  const currentQuestion = setupQuestions[currentStep];
  const isLastQuestion = currentStep === setupQuestions.length - 1;
  const progress = ((currentStep + 1) / setupQuestions.length) * 100;

  const handleAnswer = (value: SettingValue) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.key]: value,
    }));

    // Auto-advance to next question after short delay (only for boolean questions)
    if (currentQuestion.type !== 'text') {
      setTimeout(() => {
        if (!isLastQuestion) {
          setCurrentStep(prev => prev + 1);
        }
      }, 300);
    }
  };

  const handleNext = () => {
    if (!isLastQuestion) {
      setCurrentStep(prev => prev + 1);
    }
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
      await onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar configuración');
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      {showCompanyHeader && (
        <div className="mb-6">
          <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-2 text-center">
            Configuración inicial
          </h2>
          <p className="text-sm md:text-base text-slate-600 dark:text-slate-400 text-center">
            {companyName || 'Configurando tu empresa...'}
          </p>
        </div>
      )}

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {currentStep + 1} de {setupQuestions.length}
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
      <div className="mb-6 flex-1 flex flex-col justify-center" key={currentStep}>
        <div className="flex items-start gap-4 mb-6">
          <div className="flex-shrink-0 text-emerald-500 dark:text-emerald-400 mt-1">
            {currentQuestion.icon}
          </div>
          <div className="flex-1">
            <h3 className="text-base md:text-lg font-medium text-slate-900 dark:text-slate-100 leading-relaxed mb-1">
              {currentQuestion.title}
            </h3>
            <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400">
              {currentQuestion.description}
            </p>
          </div>
        </div>

        {/* Answer Options */}
        <div className="space-y-3">
          {currentQuestion.type === 'text' ? (
            <div>
              <textarea
                value={answers[currentQuestion.key] as string || ''}
                onChange={(e) => setAnswers(prev => ({
                  ...prev,
                  [currentQuestion.key]: e.target.value,
                }))}
                placeholder={currentQuestion.placeholder}
                maxLength={currentQuestion.maxLength}
                disabled={loading}
                className={clsx(
                  'w-full p-4 rounded-lg border transition-all resize-none',
                  'border-slate-200 bg-white hover:border-emerald-300',
                  'dark:border-slate-700 dark:bg-slate-800 dark:hover:border-emerald-600',
                  'text-slate-900 dark:text-slate-100',
                  'placeholder:text-slate-400 dark:placeholder:text-slate-500',
                  'focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
                rows={6}
              />
              {currentQuestion.maxLength && (
                <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 text-right">
                  {(answers[currentQuestion.key] as string || '').length} / {currentQuestion.maxLength} caracteres
                </div>
              )}
            </div>
          ) : (
            <>
              <button
                onClick={() => handleAnswer(true)}
                disabled={loading}
                className={clsx(
                  'w-full p-4 rounded-lg border text-left transition-all flex items-center gap-3',
                  answers[currentQuestion.key] === true
                    ? 'border-emerald-500 bg-emerald-50 dark:border-emerald-500 dark:bg-emerald-900/20 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-emerald-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-emerald-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <svg className={clsx(
                  'h-5 w-5 flex-shrink-0',
                  answers[currentQuestion.key] === true
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-slate-400 dark:text-slate-500'
                )} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className={clsx(
                  'text-base font-medium',
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
                  'w-full p-4 rounded-lg border text-left transition-all flex items-center gap-3',
                  answers[currentQuestion.key] === false
                    ? 'border-slate-400 bg-slate-50 dark:border-slate-500 dark:bg-slate-800/50 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <svg className={clsx(
                  'h-5 w-5 flex-shrink-0',
                  answers[currentQuestion.key] === false
                    ? 'text-slate-600 dark:text-slate-400'
                    : 'text-slate-400 dark:text-slate-500'
                )} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span className={clsx(
                  'text-base font-medium',
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
                  'w-full p-4 rounded-lg border text-left transition-all flex items-center gap-3',
                  answers[currentQuestion.key] === null
                    ? 'border-slate-300 bg-slate-100 dark:border-slate-600 dark:bg-slate-800/30 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <svg className={clsx(
                  'h-5 w-5 flex-shrink-0',
                  answers[currentQuestion.key] === null
                    ? 'text-slate-500 dark:text-slate-400'
                    : 'text-slate-400 dark:text-slate-500'
                )} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className={clsx(
                  'text-base font-medium',
                  answers[currentQuestion.key] === null
                    ? 'text-slate-600 dark:text-slate-400'
                    : 'text-slate-700 dark:text-slate-300'
                )}>
                  No estoy seguro
                </span>
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-900/20">
          <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleBack}
          disabled={currentStep === 0 || loading}
          className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
        >
          Anterior
        </button>

        {isLastQuestion ? (
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading}
            className="flex-1 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-emerald-500 dark:hover:bg-emerald-600 transition-colors"
          >
            {loading ? 'Guardando...' : 'Finalizar'}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleNext}
            disabled={
              loading ||
              (currentQuestion.type === 'text' && !(answers[currentQuestion.key] as string)?.trim())
            }
            className="flex-1 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-emerald-500 dark:hover:bg-emerald-600 transition-colors"
          >
            Continuar
          </button>
        )}
      </div>

      {/* Optional Skip Button */}
      {onSkip && (
        <button
          type="button"
          onClick={onSkip}
          disabled={loading}
          className="mt-3 text-center text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Saltar por ahora
        </button>
      )}
    </div>
  );
}
