import { HeartbeatLogo } from '@/shared/ui/branding/HeartbeatLogo';

interface FizkoLoadingScreenProps {
  /**
   * Optional className for the container
   */
  className?: string;
}

/**
 * Enhanced loading screen with Fizko branding.
 */
export function FizkoLoadingScreen({ className }: FizkoLoadingScreenProps) {

  return (
    <div className={`flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 ${className || ''}`}>
      <div className="flex flex-col items-center gap-6 text-center">
        {/* Heartbeat Logo */}
        <HeartbeatLogo className="h-20 w-20" />
      </div>
    </div>
  );
}
