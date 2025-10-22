import { useEffect, useState, useCallback } from 'react';
import clsx from 'clsx';
import type { ColorScheme } from '../hooks/useColorScheme';
import { useTaxSummary } from '../hooks/useTaxSummary';
import { useTaxDocuments } from '../hooks/useTaxDocuments';
import { CompanyInfoCard } from './CompanyInfoCard';
import { PeriodCarousel } from './PeriodCarousel';
import { TaxSummaryCard } from './TaxSummaryCard';
import { RecentDocumentsCard } from './RecentDocumentsCard';
import { useDashboardCache } from '../contexts/DashboardCacheContext';
import type { Company } from '../types/fizko';

interface FinancialDashboardProps {
  scheme: ColorScheme;
  companyId?: string | null;
  isInDrawer?: boolean;
  company: Company | null;
}

export function FinancialDashboard({ scheme, companyId, isInDrawer = false, company }: FinancialDashboardProps) {
  // Company is now passed as prop to avoid multiple fetches
  const cache = useDashboardCache();
  const [isDocumentsExpanded, setIsDocumentsExpanded] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<{ year: number; month: number } | null>(null);

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

  // Handle period change from PeriodCarousel
  const handlePeriodChange = useCallback((year: number, month: number) => {
    console.log('[FinancialDashboard] Period changed:', { year, month });
    setSelectedPeriod({ year, month });
    // In the future, we can filter data based on this period
    // For now, it's just tracked in state
  }, []);

  // Prefetch data for adjacent periods (for future use when period filtering is implemented)
  const handlePrefetchPeriod = useCallback((year: number, month: number) => {
    if (!activeCompanyId) return;

    // This is a placeholder for future period-based data fetching
    // When we implement period filtering, this will prefetch data for adjacent periods
    console.log('[FinancialDashboard] Ready to prefetch data for:', { year, month });
  }, [activeCompanyId]);

  // Note: NO manual refresh needed here - useTaxSummary and useTaxDocuments
  // already handle fetching when companyId or period changes via their useEffect

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
        <div className="w-full overflow-hidden" style={{ minWidth: 0 }}>
          <PeriodCarousel
            onPeriodChange={handlePeriodChange}
            onPrefetchPeriod={handlePrefetchPeriod}
          />
        </div>
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
  // Matching ChatKit container style from Home.tsx line 168
  return (
    <section className="flex h-full flex-col overflow-hidden rounded-3xl bg-white/80 shadow-lg ring-1 ring-slate-200/60 backdrop-blur lg:shadow-xl dark:bg-slate-900/70 dark:shadow-xl lg:dark:shadow-2xl dark:ring-slate-800/60">
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

        {/* Company Info Card - Fixed height */}
        <div className="flex-shrink-0">
          <CompanyInfoCard company={company} loading={isInitialLoading} scheme={scheme} />
        </div>

        {/* Period Carousel - Fixed height */}
        <div className="flex-shrink-0 w-full overflow-hidden" style={{ minWidth: 0 }}>
          <PeriodCarousel
            onPeriodChange={handlePeriodChange}
            onPrefetchPeriod={handlePrefetchPeriod}
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
