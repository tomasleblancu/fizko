import clsx from 'clsx';
import { ColorScheme } from "@/shared/hooks/useColorScheme";

interface HeaderProps {
  scheme: ColorScheme;
  onThemeChange: (scheme: ColorScheme) => void;
  onNavigateToSettings?: () => void;
  currentView?: 'dashboard' | 'settings';
}

export function Header({ scheme, onThemeChange, onNavigateToSettings, currentView = 'dashboard' }: HeaderProps) {
  const toggleTheme = () => {
    onThemeChange(scheme === 'dark' ? 'light' : 'dark');
  };

  const isInSettings = currentView === 'settings';

  return (
    <header
      className={clsx(
        'sticky top-0 z-50 border-b backdrop-blur-sm',
        'border-slate-200/70 bg-white/80',
        'dark:border-slate-800/70 dark:bg-slate-950/80'
      )}
    >
      <div className="mx-auto flex h-16 max-w-[1800px] items-center justify-between px-4 sm:px-6">
        {/* Logo / Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center">
            <img
              src="/encabezado.png"
              alt="Fizko Logo"
              className="h-full w-full object-contain"
            />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Fizko
            </h1>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Plataforma Contable Inteligente
            </p>
          </div>
        </div>

        {/* Right side - Theme toggle & Settings */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className={clsx(
              'rounded-lg p-2 transition-colors',
              'hover:bg-slate-100 dark:hover:bg-slate-800',
              'text-slate-600 dark:text-slate-300'
            )}
            aria-label="Toggle theme"
            title="Cambiar tema"
          >
            {scheme === 'dark' ? (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            )}
          </button>

          {/* Navigation Button - toggles between Dashboard and Settings */}
          {onNavigateToSettings && (
            <button
              onClick={onNavigateToSettings}
              className={clsx(
                'rounded-lg p-2 transition-colors',
                'hover:bg-slate-100 dark:hover:bg-slate-800',
                'text-slate-600 dark:text-slate-300'
              )}
              aria-label={isInSettings ? 'Dashboard' : 'Settings'}
              title={isInSettings ? 'Volver al Dashboard' : 'Configuración'}
            >
              {isInSettings ? (
                // Dashboard icon
                <svg
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                  />
                </svg>
              ) : (
                // Settings icon
                <svg
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              )}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
