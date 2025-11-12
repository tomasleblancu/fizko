import { useState, useCallback, useMemo } from 'react';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { useTaxSummaryQuery } from "@/shared/hooks/useTaxSummaryQuery";
import { useTaxDocumentsQuery } from "@/shared/hooks/useTaxDocumentsQuery";
import { useCalendarQuery } from "@/shared/hooks/useCalendarQuery";
import { CompanyInfoCard } from './CompanyInfoCard';
import { TaxCalendar } from './TaxCalendar';
import { RecentDocumentsCard } from './RecentDocumentsCard';
import { DualPeriodSummary } from './DualPeriodSummary';
import { ViewContainer } from '@/shared/layouts/ViewContainer';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
import type { ViewType } from '@/shared/layouts/NavigationPills';
import type { Company } from "@/shared/types/fizko";

interface FinancialDashboardProps {
  scheme: ColorScheme;
  companyId?: string | null;
  isInDrawer?: boolean;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToSettings?: () => void;
  onNavigateToContacts?: () => void;
  onNavigateToForms?: () => void;
  onNavigateToPersonnel?: () => void;
  currentView?: ViewType;
}

export function FinancialDashboard({ scheme, companyId, isInDrawer = false, company, onThemeChange, onNavigateToSettings, onNavigateToContacts, onNavigateToForms, onNavigateToPersonnel, currentView = 'dashboard' }: FinancialDashboardProps) {
  // Company is now passed as prop to avoid multiple fetches
  const [isDocumentsExpanded, setIsDocumentsExpanded] = useState(false);

  // Use companyId from props if provided, otherwise use company.id
  const activeCompanyId = companyId || company?.id || null;

  // Only fetch data if we have a company (not in onboarding)
  const shouldFetchData = !!company;

  // Calculate previous and current month periods
  const { previousMonthPeriod, currentMonthPeriod } = useMemo(() => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;

    // Previous month
    const prevDate = new Date(currentYear, currentMonth - 2, 1); // -2 because getMonth() is 0-indexed
    const prevYear = prevDate.getFullYear();
    const prevMonth = prevDate.getMonth() + 1;

    return {
      previousMonthPeriod: `${prevYear}-${String(prevMonth).padStart(2, '0')}`,
      currentMonthPeriod: `${currentYear}-${String(currentMonth).padStart(2, '0')}`
    };
  }, []);

  // Fetch both periods for DualPeriodSummary
  const { data: previousMonthData = null, isLoading: prevLoading, error: prevError } = useTaxSummaryQuery(activeCompanyId, previousMonthPeriod, shouldFetchData);
  const { data: currentMonthData = null, isLoading: currentLoading, error: currentError } = useTaxSummaryQuery(activeCompanyId, currentMonthPeriod, shouldFetchData);

  // Documents list does NOT filter by period - always shows recent documents
  // This prevents re-fetching documents every time user changes period
  // Always fetch 50 documents upfront (pre-fetch) for instant expansion
  const { data: documents = [], isLoading: docsLoading, error: docsError } = useTaxDocumentsQuery(activeCompanyId, 50, undefined, shouldFetchData);

  // Calendar events for tax obligations
  const { data: calendarData, isLoading: calendarLoading, error: calendarError } = useCalendarQuery(activeCompanyId, 30, false, shouldFetchData);
  const events = calendarData?.events || [];

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    if (view === 'contacts' && onNavigateToContacts) onNavigateToContacts();
    if (view === 'forms' && onNavigateToForms) onNavigateToForms();
    if (view === 'personnel' && onNavigateToPersonnel) onNavigateToPersonnel();
    if (view === 'settings' && onNavigateToSettings) onNavigateToSettings();
  }, [onNavigateToContacts, onNavigateToForms, onNavigateToPersonnel, onNavigateToSettings]);

  const hasError = docsError || calendarError || prevError || currentError;
  // Synchronize loading states: wait for ALL data to be ready before showing content
  // This ensures all components load their content at the same time
  const isInitialLoading = docsLoading || calendarLoading || prevLoading || currentLoading;

  // When in drawer, render without outer container
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col divide-y divide-slate-200/50 overflow-y-auto px-4 sm:px-6 dark:divide-slate-700/50">
        {hasError && (
          <div className="pb-4 pt-2">
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900/40 dark:bg-rose-900/20">
              <p className="text-sm text-rose-700 dark:text-rose-200">
                Error al cargar los datos. Por favor, intenta nuevamente.
              </p>
              {prevError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Resumen anterior: {prevError}</p>}
              {currentError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Resumen actual: {currentError}</p>}
              {docsError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Documentos: {docsError}</p>}
              {calendarError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Calendario: {calendarError}</p>}
            </div>
          </div>
        )}

        {/* Hide company info and summary when documents are expanded */}
        {!isDocumentsExpanded && (
          <>
            <div className="py-4">
              <CompanyInfoCard company={company} loading={isInitialLoading} scheme={scheme} isInDrawer={true} />
            </div>
            {/* <div className="py-4">
              <MonthCarousel
                onMonthSelect={handlePeriodChange}
                selectedMonth={selectedPeriod}
                monthsToShow={6}
              />
            </div> */}
            <div className="py-4">
              <DualPeriodSummary
                previousMonth={previousMonthData}
                currentMonth={currentMonthData}
                loading={isInitialLoading}
                scheme={scheme}
                isInDrawer={true}
              />
            </div>
            <div className="py-4">
              <TaxCalendar scheme={scheme} loading={isInitialLoading} events={events} error={calendarError} isInDrawer={true} />
            </div>
          </>
        )}

        <div className="py-4">
          <RecentDocumentsCard
            documents={documents}
            loading={isInitialLoading}
            scheme={scheme}
            isExpanded={isDocumentsExpanded}
            onToggleExpand={() => setIsDocumentsExpanded(!isDocumentsExpanded)}
            isInDrawer={true}
          />
        </div>
      </div>
    );
  }

  // Desktop view using ViewContainer
  return (
    <ViewContainer
      icon={<FizkoLogo className="h-8 w-8" />}
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
            {prevError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Resumen anterior: {prevError}</p>}
            {currentError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Resumen actual: {currentError}</p>}
            {docsError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Documentos: {docsError}</p>}
            {calendarError && <p className="mt-1 text-xs text-rose-600 dark:text-rose-300">Calendario: {calendarError}</p>}
          </div>
        )}

        {/* Month Carousel */}
        {/* <div className="flex-shrink-0">
          <MonthCarousel
            onMonthSelect={handlePeriodChange}
            selectedMonth={selectedPeriod}
            monthsToShow={6}
          />
        </div> */}

        {/* Dual Period Summary - Previous & Current Month - Hidden when documents expanded */}
        {!isDocumentsExpanded && (
          <div className="flex-shrink-0">
            <DualPeriodSummary
              previousMonth={previousMonthData}
              currentMonth={currentMonthData}
              loading={isInitialLoading}
              scheme={scheme}
              isInDrawer={false}
            />
          </div>
        )}

        {/* Tax Calendar and Documents - Side by side or Documents expanded */}
        {isDocumentsExpanded ? (
          /* Documents expanded - takes full width */
          <div className="flex-1 min-h-0">
            <RecentDocumentsCard
              documents={documents}
              loading={isInitialLoading}
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
              <TaxCalendar scheme={scheme} loading={isInitialLoading} events={events} error={calendarError} />
            </div>

            {/* Recent Documents - Right side (wider) */}
            <div className="flex flex-1 min-w-0 flex-col overflow-hidden">
              <RecentDocumentsCard
                documents={documents}
                loading={isInitialLoading}
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
