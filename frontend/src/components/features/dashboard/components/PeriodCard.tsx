/**
 * Period Card Component
 * Displays tax summary for a specific period (previous or current month)
 */

import { CheckCircle, FileText } from "lucide-react";
import { useChateableClick } from "@/hooks/useChateableClick";

interface PeriodCardProps {
  period: string;
  year: number;
  month: number;
  monthlyTax: number;
  totalRevenue: number;
  totalExpenses: number;
  isLoading: boolean;
  isPrevious?: boolean;
  f29Form?: {
    status: string;
  } | null;
  formatCurrency: (amount: number) => string;
  formatMonthYear: (year: number, month: number) => string;
}

export function PeriodCard({
  period,
  year,
  month,
  monthlyTax,
  totalRevenue,
  totalExpenses,
  isLoading,
  isPrevious = false,
  f29Form,
  formatCurrency,
  formatMonthYear,
}: PeriodCardProps) {
  const isSubmitted = f29Form?.status === 'submitted' || f29Form?.status === 'accepted';
  const isPaid = f29Form?.status === 'accepted';

  // Chateable click handlers
  const ivaClickProps = useChateableClick({
    message: `Explícame cómo se calculó el impuesto ${isPrevious ? '' : 'proyectado '}de ${formatCurrency(monthlyTax)} del período ${period}`,
    contextData: {
      amount: monthlyTax,
      period,
      type: 'monthly_tax',
    },
    disabled: isLoading,
    uiComponent: 'tax_summary_iva',
    entityId: `${year}-${month}`,
    entityType: 'tax_period',
  });

  const revenueClickProps = useChateableClick({
    message: `Dame detalles de mis ingresos de ${formatCurrency(totalRevenue)} en ${period}`,
    contextData: {
      amount: totalRevenue,
      period,
      type: 'revenue',
    },
    disabled: isLoading,
    uiComponent: 'tax_summary_revenue',
    entityId: `${year}-${month}`,
    entityType: 'tax_period',
  });

  const expensesClickProps = useChateableClick({
    message: `Analiza mis compras de ${formatCurrency(totalExpenses)} en ${period}`,
    contextData: {
      amount: totalExpenses,
      period,
      type: 'expenses',
    },
    disabled: isLoading,
    uiComponent: 'tax_summary_expenses',
    entityId: `${year}-${month}`,
    entityType: 'tax_period',
  });

  const payClickProps = useChateableClick({
    message: `Ayúdame a pagar mi F29 de ${formatCurrency(monthlyTax)} del período ${period}`,
    contextData: {
      amount: monthlyTax,
      period,
      type: 'payment',
    },
    disabled: isLoading || !isPrevious,
    uiComponent: 'pay_latest_f29',
    entityId: `${year}-${month}`,
    entityType: 'tax_period',
  });

  if (isPrevious) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/10">
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-red-500 border-t-transparent" />
            </div>
          ) : (
            <>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-medium text-red-900 dark:text-red-200">
                  {formatMonthYear(year, month)}
                </h3>
                <span className="rounded-full bg-red-600 px-3 py-1 text-xs font-medium text-white">
                  {monthlyTax > 0 ? "A Pagar" : "Al día"}
                </span>
              </div>

              {/* Steps */}
              <div className="mb-3 flex items-center gap-2">
                {[
                  { id: 1, label: "Declarado", completed: !!f29Form },
                  { id: 2, label: "Guardado", completed: isSubmitted },
                  { id: 3, label: "Pagado", completed: isPaid },
                ].map((step, index, arr) => (
                  <div key={step.id} className="flex items-center gap-2">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full ${
                        step.completed
                          ? "bg-red-600 text-white"
                          : "border-2 border-red-300 bg-white text-red-400"
                      }`}
                    >
                      {step.completed ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <span className="text-xs font-bold">{step.id}</span>
                      )}
                    </div>
                    {index < arr.length - 1 && (
                      <div className="h-0.5 w-8 bg-red-200" />
                    )}
                  </div>
                ))}
              </div>

              {/* Tax Amount - Chateable */}
              <div className="mb-3">
                <p className="text-xs text-red-700 dark:text-red-300">Impuesto</p>
                <p
                  {...ivaClickProps}
                  className="chateable-element text-2xl font-bold text-red-900 dark:text-red-100"
                >
                  {formatCurrency(monthlyTax)}
                </p>
              </div>

              {/* Sales and Purchases - Chateable */}
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-xs text-red-700 dark:text-red-300">Ventas</p>
                  <p
                    {...revenueClickProps}
                    className="chateable-element text-base font-semibold text-red-900 dark:text-red-100"
                  >
                    {formatCurrency(totalRevenue)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-red-700 dark:text-red-300">Compras</p>
                  <p
                    {...expensesClickProps}
                    className="chateable-element text-base font-semibold text-red-900 dark:text-red-100"
                  >
                    {formatCurrency(totalExpenses)}
                  </p>
                </div>
              </div>

              {/* Pay Button */}
              <button
                {...payClickProps}
                className="w-full rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span className="flex items-center justify-center gap-2">
                  <FileText className="h-4 w-4" />
                  Pagar
                </span>
              </button>
            </>
          )}
      </div>
    );
  }

  // Current month card (compact)
  return (
    <div className="flex-1 flex h-full flex-col justify-between rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-900/10">
        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          </div>
        ) : (
          <>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-emerald-900 dark:text-emerald-200">
                {formatMonthYear(year, month)}
              </h3>
              <span className="rounded-full bg-emerald-600 px-2.5 py-0.5 text-xs font-medium text-white">
                En Curso
              </span>
            </div>

            {/* Projected Tax - Chateable */}
            <div className="mb-3">
              <p className="text-xs text-emerald-700 dark:text-emerald-300">
                Impuesto Proyectado
              </p>
              <p
                {...ivaClickProps}
                className="chateable-element text-2xl font-bold text-emerald-900 dark:text-emerald-100"
              >
                {formatCurrency(monthlyTax)}
              </p>
            </div>

            {/* Sales and Purchases - Chateable */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-emerald-700 dark:text-emerald-300">Ventas</p>
                <p
                  {...revenueClickProps}
                  className="chateable-element text-base font-semibold text-emerald-900 dark:text-emerald-100"
                >
                  {formatCurrency(totalRevenue)}
                </p>
              </div>
              <div>
                <p className="text-xs text-emerald-700 dark:text-emerald-300">Compras</p>
                <p
                  {...expensesClickProps}
                  className="chateable-element text-base font-semibold text-emerald-900 dark:text-emerald-100"
                >
                  {formatCurrency(totalExpenses)}
                </p>
              </div>
            </div>
          </>
        )}
    </div>
  );
}
