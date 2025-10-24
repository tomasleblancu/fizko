import { useState, useCallback } from 'react';
import clsx from 'clsx';
import { Building2, Sun, Moon, Home, Users, Settings } from 'lucide-react';
import type { ColorScheme } from '../hooks/useColorScheme';
import { useTaxSummary } from '../hooks/useTaxSummary';
import { useTaxDocuments } from '../hooks/useTaxDocuments';
import { CompanyInfoCard } from './CompanyInfoCard';
import { TaxSummaryCard } from './TaxSummaryCard';
import { TaxCalendar } from './TaxCalendar';
import { RecentDocumentsCard } from './RecentDocumentsCard';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import type { Company } from '../types/fizko';

interface FinancialDashboardProps {
  scheme: ColorScheme;
  companyId?: string | null;
  isInDrawer?: boolean;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToSettings?: () => void;
  onNavigateToContacts?: () => void;
  currentView?: 'dashboard' | 'contacts' | 'settings';
}

export function FinancialDashboard({ scheme, companyId, isInDrawer = false, company, onThemeChange, onNavigateToSettings, onNavigateToContacts, currentView = 'dashboard' }: FinancialDashboardProps) {
  // Company is now passed as prop to avoid multiple fetches
  const cache = useDashboardCache();
  const [isDocumentsExpanded, setIsDocumentsExpanded] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<string | undefined>(undefined);

  // Use companyId from props if provided, otherwise use company.id
  const activeCompanyId = companyId || company?.id || null;

  // Tax summary uses period filter to show metrics for selected month
  const { taxSummary, loading: taxLoading, error: taxError, refresh: refreshTax } = useTaxSummary(activeCompanyId, selectedPeriod);

  // Documents list does NOT filter by period - always shows recent documents
  // This prevents re-fetching documents every time user changes period
  // Fetch more when expanded to show all available documents
  const { documents, loading: docsLoading, error: docsError, refresh: refreshDocs } = useTaxDocuments(activeCompanyId, isDocumentsExpanded ? 50 : 10);

  // Handle period change from TaxSummaryCard
  const handlePeriodChange = useCallback((period: string | undefined) => {
    console.log('[FinancialDashboard] Period changed:', period);
    setSelectedPeriod(period);
  }, []);

  // Note: NO manual refresh needed here - useTaxSummary and useTaxDocuments
  // already handle fetching when companyId or period changes via their useEffect

  const toggleTheme = () => {
    if (onThemeChange) {
      onThemeChange(scheme === 'dark' ? 'light' : 'dark');
    }
  };

  const isInSettings = currentView === 'settings';

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
        <TaxSummaryCard
          taxSummary={taxSummary}
          loading={isInitialLoading}
          scheme={scheme}
          isCompact={isDocumentsExpanded}
          onPeriodChange={handlePeriodChange}
        />
        {!isDocumentsExpanded && (
          <TaxCalendar scheme={scheme} loading={isInitialLoading} />
        )}
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
                    <Sun className="h-5 w-5" />
                  ) : (
                    <Moon className="h-5 w-5" />
                  )}
                </button>
              )}

              {/* Navigation Pills */}
              <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
                {/* Dashboard Button */}
                <button
                  onClick={() => {}} // Already on dashboard
                  disabled
                  className={clsx(
                    'rounded-md p-2 transition-colors cursor-default',
                    currentView === 'dashboard'
                      ? 'bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400'
                      : 'text-slate-400 dark:text-slate-600'
                  )}
                  aria-label="Dashboard"
                  title="Dashboard"
                >
                  <Home className="h-5 w-5" />
                </button>

                {/* Contacts Button */}
                {onNavigateToContacts && (
                  <button
                    onClick={onNavigateToContacts}
                    className={clsx(
                      'rounded-md p-2 transition-colors',
                      currentView === 'contacts'
                        ? 'bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400'
                        : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100'
                    )}
                    aria-label="Contactos"
                    title="Contactos"
                  >
                    <Users className="h-5 w-5" />
                  </button>
                )}

                {/* Settings Button */}
                {onNavigateToSettings && (
                  <button
                    onClick={onNavigateToSettings}
                    className={clsx(
                      'rounded-md p-2 transition-colors',
                      currentView === 'settings'
                        ? 'bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-400'
                        : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700/50 dark:hover:text-slate-100'
                    )}
                    aria-label="Configuración"
                    title="Configuración"
                  >
                    <Settings className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content - Flex layout WITH scroll */}
      <div className="flex h-full flex-col gap-6 overflow-y-auto p-6">
        {hasError && (
          <div className="flex-shrink-0 rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900/40 dark:bg-rose-900/20">
            <p className="text-sm text-rose-700 dark:text-rose-200">
              Error al cargar los datos. Por favor, intenta nuevamente.
            </p>
            {taxError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Impuestos: {taxError}</p>}
            {docsError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Documentos: {docsError}</p>}
          </div>
        )}

        {/* Tax Summary - Fixed height or compact */}
        <div className="flex-shrink-0">
          <TaxSummaryCard
            taxSummary={taxSummary}
            loading={isInitialLoading}
            scheme={scheme}
            isCompact={isDocumentsExpanded}
            onPeriodChange={handlePeriodChange}
          />
        </div>

        {/* Tax Calendar and Documents - Side by side or Documents expanded */}
        {isDocumentsExpanded ? (
          /* Documents expanded - takes full width */
          <div className="flex-1 min-h-0">
            <RecentDocumentsCard
              documents={documents}
              loading={docsLoading}
              scheme={scheme}
              isExpanded={isDocumentsExpanded}
              onToggleExpand={() => setIsDocumentsExpanded(!isDocumentsExpanded)}
            />
          </div>
        ) : (
          /* Tax Calendar and Documents side by side */
          <div className="flex flex-1 min-h-0 gap-6 overflow-hidden">
            {/* Tax Calendar - Left side (more square) */}
            <div className="flex w-[45%] min-w-0 flex-col">
              <TaxCalendar scheme={scheme} loading={isInitialLoading} />
            </div>

            {/* Recent Documents - Right side (wider) */}
            <div className="flex flex-1 min-w-0 flex-col">
              <RecentDocumentsCard
                documents={documents}
                loading={docsLoading}
                scheme={scheme}
                isExpanded={isDocumentsExpanded}
                onToggleExpand={() => setIsDocumentsExpanded(!isDocumentsExpanded)}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
