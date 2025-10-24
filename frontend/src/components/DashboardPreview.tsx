import { FinancialDashboard } from './FinancialDashboard';
import type { Company, TaxSummary, TaxDocument } from '../types/fizko';
import type { ColorScheme } from '../hooks/useColorScheme';

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
                {/* Company Info */}
                <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-md">
                      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {mockCompany.business_name}
                      </h3>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        RUT: {mockCompany.rut}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Tax Summary */}
                <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <h3 className="mb-4 text-lg font-bold text-slate-900 dark:text-slate-100">
                    Resumen Tributario
                  </h3>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
                      <p className="text-sm text-slate-600 dark:text-slate-400">Ingresos</p>
                      <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                        {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(mockTaxSummary.total_revenue)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-red-50 p-4 dark:bg-red-900/20">
                      <p className="text-sm text-slate-600 dark:text-slate-400">Gastos</p>
                      <p className="text-2xl font-bold text-red-700 dark:text-red-400">
                        {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(mockTaxSummary.total_expenses)}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
                    <p className="text-sm text-slate-600 dark:text-slate-400">IVA a pagar</p>
                    <p className="text-3xl font-bold text-blue-700 dark:text-blue-400">
                      {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(mockTaxSummary.net_iva)}
                    </p>
                  </div>
                </div>

                {/* Recent Documents */}
                <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <h3 className="mb-3 text-lg font-bold text-slate-900 dark:text-slate-100">
                    Documentos Recientes
                  </h3>
                  <div className="space-y-2">
                    {mockDocuments.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-700"
                      >
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {doc.document_type} #{doc.document_number}
                          </p>
                          <p className="text-xs text-slate-600 dark:text-slate-400">
                            {new Date(doc.issue_date).toLocaleDateString('es-CL')}
                          </p>
                        </div>
                        <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
                          {new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }).format(doc.amount)}
                        </p>
                      </div>
                    ))}
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
