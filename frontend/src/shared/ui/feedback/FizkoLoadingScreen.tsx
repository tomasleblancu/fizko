import { useState, useEffect } from 'react';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';

const LOADING_MESSAGES = [
  'Conectando con el SII...',
  'Sincronizando documentos tributarios...',
  'Cargando información financiera...',
  'Preparando tu dashboard...',
  'Verificando obligaciones tributarias...',
  'Actualizando datos de impuestos...',
  'Organizando tus documentos...',
];

interface FizkoLoadingScreenProps {
  /**
   * Optional custom message to display instead of rotating messages
   */
  message?: string;
  /**
   * Optional className for the container
   */
  className?: string;
}

/**
 * Enhanced loading screen with Fizko branding and rotating feature messages.
 * Shows contextual messages about what Fizko does while loading.
 */
export function FizkoLoadingScreen({ message, className }: FizkoLoadingScreenProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Don't rotate if custom message is provided
    if (message) return;

    const interval = setInterval(() => {
      // Fade out
      setIsVisible(false);

      // Wait for fade out, then change message and fade in
      setTimeout(() => {
        setCurrentMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
        setIsVisible(true);
      }, 300); // Half of the transition duration
    }, 2500); // Change message every 2.5 seconds

    return () => clearInterval(interval);
  }, [message]);

  const currentMessage = message || LOADING_MESSAGES[currentMessageIndex];

  return (
    <div className={`flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 ${className || ''}`}>
      <div className="flex flex-col items-center gap-6 text-center">
        {/* Fizko Logo with pulse animation */}
        <div className="relative">
          <div className="absolute inset-0 animate-ping rounded-full bg-emerald-400/20 dark:bg-emerald-500/20" style={{ animationDuration: '2s' }} />
          <div className="relative rounded-full bg-white p-4 shadow-lg dark:bg-slate-800">
            <FizkoLogo className="h-12 w-12" />
          </div>
        </div>

        {/* Rotating message with fade transition */}
        <div className="min-h-[2rem] px-4">
          <p
            className={`text-sm font-medium text-slate-600 transition-opacity duration-300 dark:text-slate-400 ${
              isVisible ? 'opacity-100' : 'opacity-0'
            }`}
          >
            {currentMessage}
          </p>
        </div>
      </div>
    </div>
  );
}
