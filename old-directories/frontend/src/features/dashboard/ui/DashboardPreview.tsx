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

          {/* Dashboard content with real screenshots - responsive */}
          <div className="max-h-[600px] overflow-hidden px-6 pb-6">
            {/* Desktop: side by side */}
            <div className="hidden lg:flex gap-4">
              {/* Chat Panel - Left */}
              <div className="w-[35%] flex-shrink-0 rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="/solo_chat.png"
                  alt="Asistente tributario AI disponible 24/7"
                  className="w-full h-full object-cover object-top"
                />
              </div>

              {/* Dashboard - Right */}
              <div className="flex-1 rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="/solo_dash.png"
                  alt="Dashboard fiscal con resumen tributario y proyecciones"
                  className="w-full h-full object-cover object-top"
                />
              </div>
            </div>

            {/* Mobile/Tablet: stacked */}
            <div className="lg:hidden space-y-4">
              {/* Dashboard first on mobile */}
              <div className="rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="/solo_dash.png"
                  alt="Dashboard fiscal con resumen tributario y proyecciones"
                  className="w-full h-auto"
                />
              </div>

              {/* Chat second on mobile */}
              <div className="rounded-2xl overflow-hidden shadow-2xl">
                <img
                  src="/solo_chat.png"
                  alt="Asistente tributario AI disponible 24/7"
                  className="w-full h-auto"
                />
              </div>
            </div>
          </div>

          {/* Gradient overlay at bottom to indicate more content */}
          <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent dark:from-gray-800" />
        </div>
      </div>
    </div>
  );
}
