import { useState, useCallback, useMemo } from 'react';
import clsx from 'clsx';
import { FileText } from 'lucide-react';
import { useF29FormsQuery, type FormType, type F29Form } from "@/shared/hooks/useF29FormsQuery";
import { ViewContainer } from '@/shared/layouts/ViewContainer';
import { FizkoLogo } from '@/shared/ui/branding/FizkoLogo';
import type { ViewType } from '@/shared/layouts/NavigationPills';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import type { Company } from "@/shared/types/fizko";
import { FormDetail } from './FormDetail';

interface FormsProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
  onNavigateBack?: () => void;
  company: Company | null;
  onThemeChange?: (scheme: ColorScheme) => void;
  onNavigateToDashboard?: () => void;
  onNavigateToSettings?: () => void;
  onNavigateToPersonnel?: () => void;
  onNavigateToContacts?: () => void;
  currentView?: ViewType;
}

export function Forms({
  scheme,
  isInDrawer = false,
  company,
  onThemeChange,
  onNavigateToDashboard,
  onNavigateToSettings,
  onNavigateToPersonnel,
  onNavigateToContacts,
  currentView = 'contacts'
}: FormsProps) {
  const [formTypeFilter, setFormTypeFilter] = useState<FormType>('monthly');
  const [yearFilter, setYearFilter] = useState<number>(new Date().getFullYear());
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedForm, setSelectedForm] = useState<F29Form | null>(null);

  const { data, isLoading: loading, error } = useF29FormsQuery({
    companyId: company?.id,
    formType: formTypeFilter,
    year: yearFilter
  });

  // Generate year options (current year and 4 years back)
  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return Array.from({ length: 5 }, (_, i) => currentYear - i);
  }, []);

  // Handle navigation
  const handleNavigate = useCallback((view: ViewType) => {
    // If clicking on forms tab while viewing a form detail, go back to list
    if (view === 'forms' && selectedForm) {
      setSelectedForm(null);
      return;
    }

    if (view === 'dashboard' && onNavigateToDashboard) onNavigateToDashboard();
    if (view === 'personnel' && onNavigateToPersonnel) onNavigateToPersonnel();
    if (view === 'settings' && onNavigateToSettings) onNavigateToSettings();
    if (view === 'contacts' && onNavigateToContacts) onNavigateToContacts();
  }, [selectedForm, onNavigateToDashboard, onNavigateToPersonnel, onNavigateToSettings, onNavigateToContacts]);

  // Handle form selection
  const handleFormClick = useCallback((form: F29Form) => {
    setSelectedForm(form);
  }, []);

  // Handle back to list
  const handleBackToList = useCallback(() => {
    setSelectedForm(null);
  }, []);

  // Filter forms by search term
  const filteredForms = useMemo(() => {
    if (!data?.forms) return [];

    return data.forms.filter(form => {
      const matchesSearch = searchTerm === '' ||
        form.folio.toLowerCase().includes(searchTerm.toLowerCase()) ||
        form.period_display.includes(searchTerm);
      return matchesSearch;
    });
  }, [data?.forms, searchTerm]);

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium";
    switch (status) {
      case 'Vigente':
        return `${baseClasses} bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400`;
      case 'Rectificado':
        return `${baseClasses} bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400`;
      case 'Anulado':
        return `${baseClasses} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`;
      default:
        return `${baseClasses} bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400`;
    }
  };

  const getPDFStatusBadge = (pdfStatus: string, hasPdf: boolean) => {
    const baseClasses = "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium";
    if (pdfStatus === 'downloaded' && hasPdf) {
      return `${baseClasses} bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400`;
    } else if (pdfStatus === 'error') {
      return `${baseClasses} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`;
    } else {
      return `${baseClasses} bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400`;
    }
  };

  const getPDFStatusLabel = (pdfStatus: string, hasPdf: boolean) => {
    if (pdfStatus === 'downloaded' && hasPdf) return 'PDF disponible';
    if (pdfStatus === 'error') return 'Error PDF';
    return 'Pendiente';
  };

  const formatAmount = (amountCents: number) => {
    const amount = amountCents;
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPeriod = (periodDisplay: string) => {
    // Convert "2024-01" to "Enero 2024"
    const [year, month] = periodDisplay.split('-');
    const monthNames = [
      'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  };

  // Content component (shared between drawer and normal mode)
  const renderContent = () => {
    // If a form is selected, show the detail view
    if (selectedForm) {
      return (
        <FormDetail
          form={selectedForm}
          onBack={handleBackToList}
          scheme={scheme}
          companyId={company?.id}
        />
      );
    }

    // Otherwise, show the list view
    return (
    <>
      {/* Filters and Search */}
      <div className={clsx(
        "flex-shrink-0 py-4 px-4 sm:px-6",
        isInDrawer
          ? "border-b border-slate-200/50 dark:border-slate-700/50"
          : "border-b border-slate-200/60 bg-white/30 dark:border-slate-800/60 dark:bg-slate-900/30"
      )}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              placeholder="Buscar por folio o periodo..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={clsx(
                "w-full rounded-lg border px-4 py-2.5 pl-10 text-base transition-colors",
                "border-slate-200 bg-white placeholder-slate-400",
                "focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20",
                "dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
              )}
            />
            <svg
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Filter buttons */}
          <div className="flex gap-2">
            {/* Year selector */}
            <select
              value={yearFilter}
              onChange={(e) => setYearFilter(Number(e.target.value))}
              className={clsx(
                "rounded-lg px-4 py-2 text-sm font-medium transition-colors border",
                "border-slate-200 bg-white text-slate-700",
                "hover:bg-slate-50 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20",
                "dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              )}
            >
              {yearOptions.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>

            {/* Type filter */}
            {[
              { value: 'monthly' as const, label: 'Mensuales' },
              { value: 'annual' as const, label: 'Anuales' },
            ].map((filterOption) => (
              <button
                key={filterOption.value}
                onClick={() => setFormTypeFilter(filterOption.value)}
                className={clsx(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  formTypeFilter === filterOption.value
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                )}
              >
                {filterOption.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-hidden py-4 sm:py-6">
        {loading ? (
          <div className="px-4 sm:px-6">
            <div className="grid w-full gap-3 sm:gap-4 overflow-y-auto">
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700 sm:h-5" />
                      <div className="mt-1 h-3 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
                    </div>
                    <div className="h-5 w-20 animate-pulse rounded-full bg-slate-200 dark:bg-slate-700 flex-shrink-0" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center px-4 sm:px-6">
            <div className="text-center">
              <p className="text-sm text-red-600 dark:text-red-400">
                {error instanceof Error ? error.message : String(error)}
              </p>
            </div>
          </div>
        ) : filteredForms.length === 0 ? (
          <div className="flex h-full items-center justify-center px-4 sm:px-6">
            <div className="text-center">
              <FileText className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700" />
              <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
                {searchTerm ? 'No se encontraron formularios' : 'Aún no hay formularios'}
              </p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
                Los formularios se sincronizan automáticamente desde el SII
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto overflow-y-auto h-full">
            <div className="inline-block min-w-full align-middle px-4 sm:px-6">
              <table className="min-w-full">
              <thead className="sticky top-0 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="pb-3 px-2 text-left text-sm font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    Periodo
                  </th>
                  <th className="pb-3 px-2 text-left text-sm font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    Folio
                  </th>
                  <th className="pb-3 px-2 text-left text-sm font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    Monto
                  </th>
                  <th className="pb-3 px-2 text-left text-sm font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    Estado
                  </th>
                  <th className="pb-3 px-2 text-left text-sm font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    PDF
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredForms.map((form) => (
                  <tr
                    key={form.id}
                    className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700"
                    onClick={() => handleFormClick(form)}
                  >
                    <td className="py-3 px-2">
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900 dark:text-slate-100">
                          {formatPeriod(form.period_display)}
                        </p>
                        {form.submission_date && (
                          <p className="text-sm text-slate-500 dark:text-slate-500">
                            {new Date(form.submission_date).toLocaleDateString('es-CL')}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-2 whitespace-nowrap">
                      <span className="text-slate-700 dark:text-slate-300 font-mono text-sm">
                        {form.folio}
                      </span>
                    </td>
                    <td className="py-3 px-2 whitespace-nowrap">
                      <span className="text-slate-900 dark:text-slate-100 font-medium">
                        {formatAmount(form.amount_cents)}
                      </span>
                    </td>
                    <td className="py-3 px-2 whitespace-nowrap">
                      <span className={getStatusBadge(form.status)}>
                        {form.status}
                      </span>
                    </td>
                    <td className="py-3 px-2 whitespace-nowrap">
                      <span className={getPDFStatusBadge(form.pdf_download_status, form.has_pdf)}>
                        {getPDFStatusLabel(form.pdf_download_status, form.has_pdf)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
        )}
      </div>

      {/* Footer with count */}
      {!loading && !error && filteredForms.length > 0 && (
        <div className={clsx(
          "flex-shrink-0 py-3 px-4 sm:px-6",
          isInDrawer
            ? "border-t border-slate-200/50 dark:border-slate-700/50"
            : "border-t border-slate-200/60 bg-white/30 dark:border-slate-800/60 dark:bg-slate-900/30"
        )}>
          <p className="text-base text-slate-600 dark:text-slate-400">
            Mostrando {filteredForms.length} {filteredForms.length === 1 ? 'formulario' : 'formularios'}
            {data && data.total > filteredForms.length && ` de ${data.total} total`}
          </p>
        </div>
      )}
    </>
    );
  };

  // Drawer mode - simple container with padding
  if (isInDrawer) {
    return (
      <div className="flex h-full flex-col overflow-hidden">
        {renderContent()}
      </div>
    );
  }

  // Normal mode - with ViewContainer
  return (
    <ViewContainer
      icon={<FizkoLogo className="h-7 w-7" />}
      iconGradient="from-white to-white"
      title="Formularios"
      subtitle="Gestiona tus formularios F29"
      currentView={currentView}
      onNavigate={handleNavigate}
      scheme={scheme}
      onThemeChange={onThemeChange}
      isInDrawer={false}
      contentClassName="flex-1 overflow-hidden flex flex-col px-4 sm:px-6"
    >
      {renderContent()}
    </ViewContainer>
  );
}
