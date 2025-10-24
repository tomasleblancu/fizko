import { useState, useCallback } from 'react';
import type { ColorScheme } from '../hooks/useColorScheme';
import { useTaxSummary } from '../hooks/useTaxSummary';
import { useTaxDocuments } from '../hooks/useTaxDocuments';
import { CompanyInfoCard } from './CompanyInfoCard';
import { TaxSummaryCard } from './TaxSummaryCard';
import { TaxCalendar } from './TaxCalendar';
import { RecentDocumentsCard } from './RecentDocumentsCard';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import { ViewContainer } from './layout/ViewContainer';
import { FizkoLogo } from './FizkoLogo';
import type { ViewType } from './layout/NavigationPills';
import type { Company } from '../types/fizko';

interface FinancialDashboardProps {
  scheme: ColorScheme;
  companyId?: string | null;
  isInDrawer?: boolean;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToSettings?: () => void;
  onNavigateToContacts?: () => void;
  currentView?: ViewType;
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

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    if (view === 'contacts' && onNavigateToContacts) onNavigateToContacts();
    if (view === 'settings' && onNavigateToSettings) onNavigateToSettings();
  }, [onNavigateToContacts, onNavigateToSettings]);

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

  // Desktop view using ViewContainer
  return (
    <ViewContainer
      icon={<FizkoLogo className="h-7 w-7" />}
      iconGradient="from-white to-white"
      title={company?.business_name || 'Cargando...'}
      subtitle={`RUT: ${company?.rut || '---'}`}
      currentView={currentView}
      onNavigate={handleNavigate}
      scheme={scheme}
      onThemeChange={onThemeChange}
      isInDrawer={isInDrawer}
      contentClassName="flex h-full flex-col gap-6 overflow-y-auto px-6 py-6"
    >
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
          /* Tax Calendar and Documents side by side on large screens, stacked on small */
          <div className="flex flex-1 min-h-0 flex-col gap-6 overflow-hidden xl:flex-row">
            {/* Tax Calendar - Left side (narrower) */}
            <div className="flex min-w-0 flex-col overflow-hidden xl:w-[38%]">
              <TaxCalendar scheme={scheme} loading={isInitialLoading} />
            </div>

            {/* Recent Documents - Right side (wider) */}
            <div className="flex flex-1 min-w-0 flex-col overflow-hidden">
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
    </ViewContainer>
  );
}
