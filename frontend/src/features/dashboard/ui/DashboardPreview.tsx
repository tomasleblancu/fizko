import { FinancialDashboard } from './FinancialDashboard';
import type { Company, TaxSummary, TaxDocument } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";

// Mock data for the landing page preview
const mockCompany: Company = {
  id: 'preview-company',
  rut: '76.123.456-7',
  business_name: 'Empresa Demo SpA',
  trade_name: 'Demo',
  created_at: new Date().toISOString(),
};

const currentDate = new Date();
const currentYear = currentDate.getFullYear();
const currentMonth = currentDate.getMonth() + 1;

const mockTaxSummary: TaxSummary = {
  id: 'preview-summary',
  company_id: 'preview-company',
  period_start: `${currentYear}-${currentMonth.toString().padStart(2, '0')}-01`,
  period_end: `${currentYear}-${currentMonth.toString().padStart(2, '0')}-${new Date(currentYear, currentMonth, 0).getDate()}`,
  total_revenue: 3220540,
  total_expenses: 2174980,
  iva_collected: 611703,
  iva_paid: 413046,
  net_iva: 198657,
  income_tax: 156320,
  previous_month_credit: 50000,
  monthly_tax: 148657, // iva_collected - iva_paid - previous_month_credit = 611703 - 413046 - 50000
  created_at: new Date().toISOString(),
};

const mockDocuments: TaxDocument[] = [
  {
    id: '1',
    company_id: 'preview-company',
    document_type: 'Factura Electrónica',
    document_number: '12345',
    issue_date: new Date(currentYear, currentMonth - 1, 15).toISOString(),
    amount: 850000,
    tax_amount: 161500,
    status: 'Emitida',
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    company_id: 'preview-company',
    document_type: 'Boleta Electrónica',
    document_number: '67890',
    issue_date: new Date(currentYear, currentMonth - 1, 12).toISOString(),
    amount: 125000,
    tax_amount: 23750,
    status: 'Emitida',
    created_at: new Date().toISOString(),
  },
  {
    id: '3',
    company_id: 'preview-company',
    document_type: 'Factura de Compra',
    document_number: '11223',
    issue_date: new Date(currentYear, currentMonth - 1, 10).toISOString(),
    amount: 450000,
    tax_amount: 85500,
    status: 'Recibida',
    created_at: new Date().toISOString(),
  },
];

interface DashboardPreviewProps {
  scheme?: ColorScheme;
}

/**
 * DashboardPreview component for the landing page.
 * Shows a real dashboard with mock data to give users a preview of the app.
 */
export function DashboardPreview({ scheme = 'light' }: DashboardPreviewProps) {
  // Create a mock context provider that returns our mock data
  const MockDashboardCacheProvider = ({ children }: { children: React.ReactNode }) => {
    return <>{children}</>;
  };

  // We need to mock the hooks that FinancialDashboard uses
  // The simplest approach is to render a simplified version directly
  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-800">
        <div className="relative">
          {/* Fake browser chrome */}
          <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-900">
            <div className="flex items-center space-x-2">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <div className="h-3 w-3 rounded-full bg-yellow-500" />
              <div className="h-3 w-3 rounded-full bg-green-500" />
            </div>
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Dashboard Fiscal
            </div>
            <div className="w-16" /> {/* Spacer for symmetry */}
          </div>

          {/* Dashboard content with mock data */}
          <div className="max-h-[600px] overflow-hidden p-6">
            <MockDashboardCacheProvider>
              <div className="pointer-events-none space-y-4 opacity-95">
                {/* Company Info - matching CompanyInfoCard */}
                <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-blue-50 to-purple-50 p-3 dark:border-slate-800/70 dark:from-blue-950/30 dark:to-purple-950/30">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-md">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {mockCompany.business_name}
                      </h3>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        RUT: {mockCompany.rut}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Tax Summary - matching TaxSummaryCard */}
                <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70">
                  {/* Header */}
                  <div className="mb-6 text-center">
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      Resumen Tributario
                    </h3>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      Período actual
                    </p>
                  </div>

                  {/* Main Grid - Ingresos, Gastos, IVA */}
                  <div className="grid gap-4 sm:grid-cols-3">
                    {/* Ingresos */}
                    <div className="rounded-xl border border-emerald-200/70 bg-emerald-50 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/30">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-xs font-medium uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
                          Ingresos
                        </span>
                        <svg className="h-4 w-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      </div>
                      <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">
                        {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(mockTaxSummary.total_revenue)}
                      </p>
                    </div>

                    {/* Gastos */}
                    <div className="rounded-xl border border-rose-200/70 bg-rose-50 p-4 dark:border-rose-900/40 dark:bg-rose-950/30">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-xs font-medium uppercase tracking-wide text-rose-700 dark:text-rose-400">
                          Gastos
                        </span>
                        <svg className="h-4 w-4 text-rose-600 dark:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                        </svg>
                      </div>
                      <p className="text-2xl font-bold text-rose-700 dark:text-rose-400">
                        {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(mockTaxSummary.total_expenses)}
                      </p>
                    </div>

                    {/* IVA Net */}
                    <div className="rounded-xl border border-blue-200/70 bg-blue-50 p-4 dark:border-blue-900/40 dark:bg-blue-950/30">
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-xs font-medium uppercase tracking-wide text-blue-700 dark:text-blue-400">
                          IVA Neto
                        </span>
                        <svg className="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      </div>
                      <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                        {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(mockTaxSummary.net_iva)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Recent Documents - matching RecentDocumentsCard (collapsed view) */}
                <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                        Documentos Tributarios Recientes
                      </h3>
                      <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                        {mockDocuments.length}
                      </span>
                    </div>
                    <svg className="h-6 w-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="space-y-1.5">
                    {mockDocuments.map((doc) => {
                      const formatDocType = (type: string) => {
                        return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                      };

                      return (
                        <div
                          key={doc.id}
                          className="flex items-center justify-between py-2 px-1 rounded-lg"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                              {doc.description || 'Sin descripción'}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                              {formatDocType(doc.document_type)} #{doc.document_number}
                            </p>
                          </div>
                          <div className="ml-4 flex-shrink-0">
                            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                              {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(doc.amount)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </MockDashboardCacheProvider>
          </div>

          {/* Gradient overlay at bottom to indicate more content */}
          <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent dark:from-gray-800" />
        </div>
      </div>
    </div>
  );
}
