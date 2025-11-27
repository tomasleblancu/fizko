/**
 * Period Card Component
 * Displays tax summary for a specific period (previous or current month)
 */

import { FileText, TrendingUp, DollarSign, ShoppingCart } from "lucide-react";
import { useChateableClick } from "@/hooks/useChateableClick";
import type { Form29SiiDownload } from "@/types/tax";

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
  form29SiiDownload?: Form29SiiDownload | null;
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
  form29SiiDownload,
  formatCurrency,
  formatMonthYear,
}: PeriodCardProps) {
  // If SII download exists, it's the source of truth (verified by SII)
  // Otherwise, use local f29Form status
  const isPaidViaSii = form29SiiDownload !== null && form29SiiDownload !== undefined;
  const isSubmitted = isPaidViaSii || f29Form?.status === 'submitted' || f29Form?.status === 'accepted';
  const isPaid = isPaidViaSii || f29Form?.status === 'accepted';

  // Use SII's exact amount if available, otherwise use calculated monthlyTax
  const displayAmount = form29SiiDownload?.extra_data?.f29_data?.summary?.total_pagar ?? monthlyTax;

  // Chateable click handlers
  const ivaClickProps = useChateableClick({
    message: `Explícame cómo se calculó el impuesto ${isPrevious ? '' : 'proyectado '}de ${formatCurrency(displayAmount)} del período ${period}`,
    contextData: {
      amount: displayAmount,
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
    message: `Ayúdame a pagar mi F29 de ${formatCurrency(displayAmount)} del período ${period}`,
    contextData: {
      amount: displayAmount,
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
      <div className={`w-full rounded-xl p-4 shadow-sm ${
        isPaid
          ? 'hidden lg:block border border-green-200 bg-green-50 dark:border-green-900/50 dark:bg-green-900/10'
          : 'border border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-900/10'
      }`}>
          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <div className={`h-6 w-6 animate-spin rounded-full border-2 border-t-transparent ${
                isPaid ? "border-green-500" : "border-red-500"
              }`} />
            </div>
          ) : (
            <>
              <div className="mb-3 flex items-center justify-between">
                <h3 className={`text-sm font-medium ${
                  isPaid
                    ? "text-green-900 dark:text-green-200"
                    : "text-red-900 dark:text-red-200"
                }`}>
                  {formatMonthYear(year, month)}
                </h3>
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium text-white ${
                  isPaid
                    ? "bg-green-600"
                    : displayAmount > 0
                      ? "bg-red-600"
                      : "bg-gray-500"
                }`}>
                  {isPaid ? "Pagado" : displayAmount > 0 ? "A Pagar" : "Al día"}
                </span>
              </div>

              {/* Tax Amount */}
              <div className="mb-3 flex flex-col items-center justify-center py-4">
                <p className={`text-xs mb-2 ${
                  isPaid
                    ? "text-green-700 dark:text-green-300"
                    : "text-red-700 dark:text-red-300"
                }`}>
                  {isPaid ? "Monto Pagado" : "Monto a Pagar"}
                </p>
                <p
                  {...ivaClickProps}
                  className={`chateable-element text-4xl font-bold ${
                    isPaid
                      ? "text-green-900 dark:text-green-100"
                      : "text-red-900 dark:text-red-100"
                  }`}
                >
                  {formatCurrency(displayAmount)}
                </p>
              </div>

              {/* Pay Button - Only show if not paid */}
              {!isPaid && (
                <button
                  {...payClickProps}
                  disabled={isLoading}
                  className="w-full rounded-lg px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span className="flex items-center justify-center gap-2">
                    <FileText className="h-4 w-4" />
                    Pagar
                  </span>
                </button>
              )}
            </>
          )}
      </div>
    );
  }

  // Current month card - Vibrant & Animated
  return (
    <div className="flex-1 flex h-full flex-col justify-between rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 via-emerald-100/50 to-teal-50 p-4 shadow-lg shadow-emerald-200/50 transition-all hover:shadow-xl hover:shadow-emerald-300/50 dark:border-emerald-700 dark:from-emerald-900/20 dark:via-emerald-800/20 dark:to-teal-900/20">
        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          </div>
        ) : (
          <>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-100">
                {formatMonthYear(year, month)}
              </h3>
              <span className="animate-pulse rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 px-2.5 py-1 text-xs font-bold text-white shadow-lg shadow-emerald-500/30">
                En Curso
              </span>
            </div>

            {/* Projected Tax - Chateable with Icon */}
            <div className="mb-3 rounded-xl bg-white/60 p-4 backdrop-blur-sm dark:bg-slate-800/40">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                  Impuesto Proyectado
                </p>
              </div>
              <p
                {...ivaClickProps}
                className="chateable-element text-4xl font-black text-emerald-900 dark:text-emerald-100 transition-transform hover:scale-105"
              >
                {formatCurrency(displayAmount)}
              </p>
            </div>

            {/* Sales and Purchases - Chateable with Icons & Gradient Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="group rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-200/50 p-3 transition-all hover:shadow-md dark:from-emerald-900/40 dark:to-emerald-800/40">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <DollarSign className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300">Ventas</p>
                </div>
                <p
                  {...revenueClickProps}
                  className="chateable-element text-xl font-bold text-emerald-900 dark:text-emerald-100 transition-transform group-hover:scale-105"
                >
                  {formatCurrency(totalRevenue)}
                </p>
              </div>
              <div className="group rounded-xl bg-gradient-to-br from-teal-100 to-teal-200/50 p-3 transition-all hover:shadow-md dark:from-teal-900/40 dark:to-teal-800/40">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <ShoppingCart className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                  <p className="text-xs font-semibold text-teal-700 dark:text-teal-300">Compras</p>
                </div>
                <p
                  {...expensesClickProps}
                  className="chateable-element text-xl font-bold text-teal-900 dark:text-teal-100 transition-transform group-hover:scale-105"
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
