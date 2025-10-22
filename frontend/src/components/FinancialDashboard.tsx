import { useEffect, useState, useCallback, useRef } from 'react';
import clsx from 'clsx';
import { Building2 } from 'lucide-react';
import type { ColorScheme } from '../hooks/useColorScheme';
import { useTaxSummary } from '../hooks/useTaxSummary';
import { useTaxDocuments } from '../hooks/useTaxDocuments';
import { CompanyInfoCard } from './CompanyInfoCard';
import { PeriodSelector } from './PeriodSelector';
import { TaxSummaryCard } from './TaxSummaryCard';
import { RecentDocumentsCard } from './RecentDocumentsCard';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import { useAuth } from '../contexts/AuthContext';
import type { Company } from '../types/fizko';

interface FinancialDashboardProps {
  scheme: ColorScheme;
  companyId?: string | null;
  isInDrawer?: boolean;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToSettings?: () => void;
}

export function FinancialDashboard({ scheme, companyId, isInDrawer = false, company, onThemeChange, onNavigateToSettings }: FinancialDashboardProps) {
  // Company is now passed as prop to avoid multiple fetches
  const cache = useDashboardCache();
  const { user, signOut } = useAuth();
  const [isDocumentsExpanded, setIsDocumentsExpanded] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<{ year: number; month: number } | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Use companyId from props if provided, otherwise use company.id
  const activeCompanyId = companyId || company?.id || null;

  // Format period as YYYY-MM for API
  const periodParam = selectedPeriod
    ? `${selectedPeriod.year}-${selectedPeriod.month.toString().padStart(2, '0')}`
    : undefined;

  // Tax summary uses period filter to show metrics for selected month
  const { taxSummary, loading: taxLoading, error: taxError, refresh: refreshTax } = useTaxSummary(activeCompanyId, periodParam);

  // Documents list does NOT filter by period - always shows recent documents
  // This prevents re-fetching documents every time user changes period
  // Fetch more when expanded to show all available documents
  const { documents, loading: docsLoading, error: docsError, refresh: refreshDocs } = useTaxDocuments(activeCompanyId, isDocumentsExpanded ? 50 : 10);

  // Handle period change from PeriodSelector
  const handlePeriodChange = useCallback((year: number, month: number) => {
    console.log('[FinancialDashboard] Period changed:', { year, month });
    setSelectedPeriod({ year, month });
    // In the future, we can filter data based on this period
    // For now, it's just tracked in state
  }, []);

  // Note: NO manual refresh needed here - useTaxSummary and useTaxDocuments
  // already handle fetching when companyId or period changes via their useEffect

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleTheme = () => {
    if (onThemeChange) {
      onThemeChange(scheme === 'dark' ? 'light' : 'dark');
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      setIsDropdownOpen(false);
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const getUserInitials = () => {
    if (!user?.email) return '?';
    return user.email.charAt(0).toUpperCase();
  };

  const hasError = taxError || docsError;
  // Synchronize loading states: show skeletons for tax data
  const isInitialLoading = taxLoading;

  // When in drawer, render without outer container
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col space-y-4 overflow-y-auto">
        {hasError && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900/40 dark:bg-rose-900/20">
            <p className="text-sm text-rose-700 dark:text-rose-200">
              Error al cargar los datos. Por favor, intenta nuevamente.
            </p>
            {taxError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Impuestos: {taxError}</p>}
            {docsError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Documentos: {docsError}</p>}
          </div>
        )}

        <CompanyInfoCard company={company} loading={isInitialLoading} scheme={scheme} />
        {/* Period Selector - Dropdown based */}
        <PeriodSelector
          onPeriodChange={handlePeriodChange}
        />
        <TaxSummaryCard taxSummary={taxSummary} loading={isInitialLoading} scheme={scheme} isCompact={isDocumentsExpanded} />
        <RecentDocumentsCard
          documents={documents}
          loading={docsLoading}
          scheme={scheme}
          isExpanded={isDocumentsExpanded}
          onToggleExpand={() => setIsDocumentsExpanded(!isDocumentsExpanded)}
        />
      </div>
    );
  }

  // Desktop view with full container - NO SCROLL, flex layout
  // Styles are now in the wrapper container in Home.tsx (matching ChatKit pattern)
  return (
    <section className="flex h-full w-full flex-col overflow-hidden">
      {/* Header Toolbar - Company info, Theme toggle and Profile */}
      {!isInDrawer && (
        <div className="flex-shrink-0 border-b border-slate-200/70 bg-white/50 px-6 py-3 backdrop-blur dark:border-slate-800/70 dark:bg-slate-900/50">
          <div className="flex items-center justify-between gap-4">
            {/* Company Info - Left side */}
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-md">
                <Building2 className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  {company?.business_name || 'Cargando...'}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  RUT: {company?.rut || '---'}
                </p>
              </div>
            </div>

            {/* Controls - Right side */}
            <div className="flex items-center gap-3">
            {/* Theme Toggle */}
            {onThemeChange && (
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
            )}

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
                      'absolute right-0 mt-2 w-64 origin-top-right rounded-lg shadow-lg z-50',
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
        </div>
      )}

      {/* Content - Flex layout WITHOUT scroll */}
      <div className="flex h-full flex-col gap-6 overflow-hidden p-6">
        {hasError && (
          <div className="flex-shrink-0 rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900/40 dark:bg-rose-900/20">
            <p className="text-sm text-rose-700 dark:text-rose-200">
              Error al cargar los datos. Por favor, intenta nuevamente.
            </p>
            {taxError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Impuestos: {taxError}</p>}
            {docsError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Documentos: {docsError}</p>}
          </div>
        )}

        {/* Period Selector - Dropdown based */}
        <div className="flex-shrink-0">
          <PeriodSelector
            onPeriodChange={handlePeriodChange}
          />
        </div>

        {/* Tax Summary - Fixed height or compact */}
        <div className="flex-shrink-0">
          <TaxSummaryCard taxSummary={taxSummary} loading={isInitialLoading} scheme={scheme} isCompact={isDocumentsExpanded} />
        </div>

        {/* Recent Documents - Fixed height, no flex-1 to prevent expansion */}
        <div className="flex-shrink-0">
          <RecentDocumentsCard
            documents={documents}
            loading={docsLoading}
            scheme={scheme}
            isExpanded={isDocumentsExpanded}
            onToggleExpand={() => setIsDocumentsExpanded(!isDocumentsExpanded)}
          />
        </div>
      </div>
    </section>
  );
}
