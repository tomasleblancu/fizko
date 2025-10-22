import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import clsx from 'clsx';
import { ColorScheme } from '../hooks/useColorScheme';

interface HeaderProps {
  scheme: ColorScheme;
  onThemeChange: (scheme: ColorScheme) => void;
  onNavigateToSettings?: () => void;
}

export function Header({ scheme, onThemeChange, onNavigateToSettings }: HeaderProps) {
  const { user, signOut } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    try {
      await signOut();
      setIsDropdownOpen(false);
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };


  const toggleTheme = () => {
    onThemeChange(scheme === 'dark' ? 'light' : 'dark');
  };

  const getUserInitials = () => {
    if (!user?.email) return '?';
    return user.email.charAt(0).toUpperCase();
  };

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

        {/* Right side - Theme toggle & User menu */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className={clsx(
              'rounded-lg p-2 transition-colors',
              'hover:bg-slate-100 dark:hover:bg-slate-800',
              'text-slate-600 dark:text-slate-300'
            )}
            aria-label="Toggle theme"
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

          {/* User Menu */}
          {user && (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className={clsx(
                  'flex items-center gap-2 rounded-lg p-2 transition-colors',
                  'hover:bg-slate-100 dark:hover:bg-slate-800'
                )}
              >
                <div
                  className={clsx(
                    'flex h-8 w-8 items-center justify-center rounded-full font-medium',
                    'bg-gradient-to-br from-emerald-600 to-teal-700 text-white text-sm shadow-md'
                  )}
                >
                  {getUserInitials()}
                </div>
                <svg
                  className={clsx(
                    'h-4 w-4 transition-transform text-slate-600 dark:text-slate-300',
                    isDropdownOpen && 'rotate-180'
                  )}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {isDropdownOpen && (
                <div
                  className={clsx(
                    'absolute right-0 mt-2 w-64 origin-top-right rounded-lg shadow-lg',
                    'border border-slate-200 bg-white',
                    'dark:border-slate-700 dark:bg-slate-800',
                    'py-1'
                  )}
                >
                  <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      Sesión activa
                    </p>
                    <p className="mt-1 truncate text-sm text-slate-600 dark:text-slate-400">
                      {user.email}
                    </p>
                  </div>

                  <div className="py-1">
                    {onNavigateToSettings && (
                      <button
                        onClick={() => {
                          onNavigateToSettings();
                          setIsDropdownOpen(false);
                        }}
                        className={clsx(
                          'flex w-full items-center gap-3 px-4 py-2 text-sm transition-colors',
                          'text-slate-700 hover:bg-slate-100',
                          'dark:text-slate-300 dark:hover:bg-slate-800'
                        )}
                      >
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
                        Configuración
                      </button>
                    )}
                    <button
                      onClick={handleSignOut}
                      className={clsx(
                        'flex w-full items-center gap-3 px-4 py-2 text-sm transition-colors',
                        'text-red-600 hover:bg-red-50',
                        'dark:text-red-400 dark:hover:bg-red-900/20'
                      )}
                    >
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
                          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                        />
                      </svg>
                      Cerrar sesión
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
