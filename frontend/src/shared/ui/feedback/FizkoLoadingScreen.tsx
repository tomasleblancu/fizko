import { useState, useEffect } from 'react';
import { HeartbeatLogo } from '@/shared/ui/branding/HeartbeatLogo';

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
        {/* Heartbeat Logo */}
        <HeartbeatLogo className="h-32 w-32" />
      </div>
    </div>
  );
}
