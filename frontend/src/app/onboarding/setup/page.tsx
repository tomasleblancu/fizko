'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import clsx from 'clsx';
import { setupQuestions, getInitialAnswers, type SettingValue } from '@/config/setup-questions';
import { useUserSessions } from '@/hooks/useUserSessions';
import { createClient } from '@/lib/supabase/client';
import { CalendarService } from '@/services/calendar/calendar.service';
import Image from 'next/image';

export default function CompanySetupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: sessions } = useUserSessions();
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [companyName, setCompanyName] = useState<string>('Tu Empresa');
  const [loading, setLoading] = useState(false);
  const [showingFinalLoader, setShowingFinalLoader] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  // State for each question - initialized from config
  const [answers, setAnswers] = useState<Record<string, SettingValue>>(getInitialAnswers());

  // Get company ID from URL query param (priority) or active session
  useEffect(() => {
    const companyIdFromUrl = searchParams.get('companyId');

    if (companyIdFromUrl) {
      // Use company ID from URL (came from SII login)
      setCompanyId(companyIdFromUrl);

      // Find matching session to get company name
      const matchingSession = sessions?.find(s => s.company_id === companyIdFromUrl);
      if (matchingSession) {
        setCompanyName(matchingSession.company?.business_name || matchingSession.company?.rut || 'Tu Empresa');
      }
    } else if (sessions && sessions.length > 0) {
      // Fallback: use first session if no URL param
      const session = sessions[0];
      setCompanyId(session.company_id);
      setCompanyName(session.company?.business_name || session.company?.rut || 'Tu Empresa');
    }
  }, [sessions, searchParams]);

  const currentQuestion = setupQuestions[currentStep];
  const isLastQuestion = currentStep === setupQuestions.length - 1;
  const progress = ((currentStep + 1) / setupQuestions.length) * 100;

  const handleLogoClick = () => {
    // Placeholder - no real logout logic yet
    router.push('/');
  };

  const handleAnswer = (value: SettingValue) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.key]: value,
    }));

    // Auto-advance to next question after short delay (only for boolean questions)
    if (currentQuestion.type !== 'text') {
      setTimeout(() => {
        if (isLastQuestion) {
          // Don't auto-submit, let user click "Finalizar"
        } else {
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
    if (!companyId) {
      setError('No se pudo obtener el ID de la empresa. Por favor, intenta nuevamente.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const supabase = createClient();

      // Check if settings already exist
      const { data: existing } = await supabase
        .from('company_settings')
        .select('id, is_initial_setup_complete')
        .eq('company_id', companyId)
        .maybeSingle();

      const updateData = {
        ...answers,
        is_initial_setup_complete: true,
        initial_setup_completed_at: new Date().toISOString(),
      };

      if (existing) {
        // Update existing settings
        const { error } = await supabase
          .from('company_settings')
          .update(updateData)
          .eq('company_id', companyId);

        if (error) throw error;
      } else {
        // Create new settings
        const { error } = await supabase
          .from('company_settings')
          .insert({
            company_id: companyId,
            ...updateData,
          });

        if (error) throw error;
      }

      // Initialize calendar events for the company
      // This creates company_events for all mandatory tax event templates
      console.log('[Setup] Initializing calendar for company:', companyId);
      await CalendarService.initializeCompanyCalendar(companyId);
      console.log('[Setup] Calendar initialized successfully');

      // Show full-screen loader for 3 seconds before redirecting
      setShowingFinalLoader(true);
      setTimeout(() => {
        router.push('/dashboard');
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar la configuración');
      setLoading(false);
    }
  };

  // Show full-screen loader after completing setup
  if (showingFinalLoader) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-slate-900 dark:via-slate-900 dark:to-emerald-950">
        <div className="text-center">
          <div className="mb-6 flex justify-center">
            <Image
              src="/encabezado.png"
              alt="Fizko Icon"
              width={64}
              height={64}
              className="h-16 w-auto animate-pulse"
            />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
            Configurando tu empresa...
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Estamos preparando todo para ti
          </p>
        </div>
      </div>
    );
  }

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
          'relative w-full h-full md:h-auto md:max-w-xl md:rounded-xl md:border overflow-hidden md:shadow-xl',
          'bg-white/80 backdrop-blur-xl md:border-slate-200',
          'dark:bg-slate-900/80 dark:backdrop-blur-xl md:dark:border-slate-700',
          'flex flex-col'
        )}
      >
        <div className="relative flex-1 flex flex-col p-6 md:p-8 overflow-y-auto">
          {/* Header */}
          <div className="mb-6 md:mb-8">
            {/* Logo - clickable to return */}
            <div className="mb-6 flex justify-center">
              <button
                onClick={handleLogoClick}
                className="flex items-center gap-2 opacity-90 hover:opacity-100 transition-opacity"
                aria-label="Volver al inicio"
              >
                <Image
                  src="/encabezado.png"
                  alt="Fizko Icon"
                  width={40}
                  height={40}
                  className="h-8 md:h-10 w-auto"
                />
                <Image
                  src="/encabezado_fizko.svg"
                  alt="Fizko"
                  width={80}
                  height={40}
                  className="h-8 md:h-10 w-auto"
                />
              </button>
            </div>

            <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-2 text-center">
              Configuración inicial
            </h2>
            <p className="text-sm md:text-base text-slate-600 dark:text-slate-400 text-center">
              {companyName}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6 md:mb-6">
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
          <div className="mb-6 md:mb-8 flex-1 flex flex-col justify-center" key={currentStep}>
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

            {/* Show "Continuar" button for text questions, "Finalizar" for last question */}
            {currentQuestion.type === 'text' && !isLastQuestion && (
              <button
                onClick={handleNext}
                disabled={loading}
                className={clsx(
                  'ml-auto px-6 py-3 text-base font-medium text-white rounded-lg transition-all',
                  'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800',
                  'disabled:cursor-not-allowed disabled:opacity-50',
                  'shadow-sm hover:shadow-md'
                )}
              >
                Continuar →
              </button>
            )}

            {isLastQuestion && (
              <button
                onClick={handleComplete}
                disabled={loading}
                className={clsx(
                  'ml-auto px-6 py-3 text-base font-medium text-white rounded-lg transition-all',
                  'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800',
                  'disabled:cursor-not-allowed disabled:opacity-50',
                  'shadow-sm hover:shadow-md'
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
