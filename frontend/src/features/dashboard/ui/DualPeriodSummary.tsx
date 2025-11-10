import { Calendar, TrendingUp, Receipt, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import type { TaxSummary } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { TaxSummaryCardSkeleton } from './TaxSummaryCardSkeleton';
import { useChateableClick } from "@/shared/hooks/useChateableClick";
import '@/app/styles/chateable.css';

interface DualPeriodSummaryProps {
  previousMonth: TaxSummary | null;
  currentMonth: TaxSummary | null;
  loading: boolean;
  scheme: ColorScheme;
  isInDrawer?: boolean;
}

export function DualPeriodSummary({
  previousMonth,
  currentMonth,
  loading,
  scheme,
  isInDrawer = false
}: DualPeriodSummaryProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getMonthName = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-CL', { month: 'long', year: 'numeric' });
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-CL', { month: 'short', year: 'numeric' });
  };

  const getDueDate = () => {
    const now = new Date();
    const dueDate = new Date(now.getFullYear(), now.getMonth(), 20);
    return dueDate.toLocaleDateString('es-CL', { day: 'numeric', month: 'long' });
  };

  // Period strings for context
  const previousPeriodString = previousMonth
    ? `${formatDate(previousMonth.period_start)} - ${formatDate(previousMonth.period_end)}`
    : '';

  const currentPeriodString = currentMonth
    ? `${formatDate(currentMonth.period_start)} - ${formatDate(currentMonth.period_end)}`
    : '';

  // Chateable click handlers for previous month
  const prevIvaClickProps = useChateableClick({
    message: previousMonth
      ? `Explícame cómo se calculó el impuesto de ${formatCurrency(previousMonth.monthly_tax)} del período ${previousPeriodString}`
      : '',
    contextData: previousMonth ? {
      amount: previousMonth.monthly_tax,
      period: previousPeriodString,
      type: 'monthly_tax',
      iva_collected: previousMonth.iva_collected,
      iva_paid: previousMonth.iva_paid,
      previous_month_credit: previousMonth.previous_month_credit,
    } : {},
    disabled: !previousMonth,
    uiComponent: 'tax_summary_iva',
    entityId: previousMonth?.period_start || '',
    entityType: 'tax_period',
  });

  const prevRevenueClickProps = useChateableClick({
    message: previousMonth
      ? `Dame detalles de mis ingresos de ${formatCurrency(previousMonth.total_revenue)} en ${previousPeriodString}`
      : '',
    contextData: previousMonth ? {
      amount: previousMonth.total_revenue,
      period: previousPeriodString,
      type: 'revenue',
    } : {},
    disabled: !previousMonth,
    uiComponent: 'tax_summary_revenue',
  });

  const prevExpensesClickProps = useChateableClick({
    message: previousMonth
      ? `Analiza mis gastos de ${formatCurrency(previousMonth.total_expenses)} en ${previousPeriodString}`
      : '',
    contextData: previousMonth ? {
      amount: previousMonth.total_expenses,
      period: previousPeriodString,
      type: 'expenses',
    } : {},
    disabled: !previousMonth,
    uiComponent: 'tax_summary_expenses',
  });

  // Chateable click handlers for current month
  const currentIvaClickProps = useChateableClick({
    message: currentMonth
      ? `Explícame cómo se calculó el impuesto proyectado de ${formatCurrency(currentMonth.monthly_tax)} del período ${currentPeriodString}`
      : '',
    contextData: currentMonth ? {
      amount: currentMonth.monthly_tax,
      period: currentPeriodString,
      type: 'monthly_tax',
      iva_collected: currentMonth.iva_collected,
      iva_paid: currentMonth.iva_paid,
      previous_month_credit: currentMonth.previous_month_credit,
    } : {},
    disabled: !currentMonth,
    uiComponent: 'tax_summary_iva',
    entityId: currentMonth?.period_start || '',
    entityType: 'tax_period',
  });

  const currentRevenueClickProps = useChateableClick({
    message: currentMonth
      ? `Dame detalles de mis ingresos de ${formatCurrency(currentMonth.total_revenue)} en ${currentPeriodString}`
      : '',
    contextData: currentMonth ? {
      amount: currentMonth.total_revenue,
      period: currentPeriodString,
      type: 'revenue',
    } : {},
    disabled: !currentMonth,
    uiComponent: 'tax_summary_revenue',
  });

  const currentExpensesClickProps = useChateableClick({
    message: currentMonth
      ? `Analiza mis gastos de ${formatCurrency(currentMonth.total_expenses)} en ${currentPeriodString}`
      : '',
    contextData: currentMonth ? {
      amount: currentMonth.total_expenses,
      period: currentPeriodString,
      type: 'expenses',
    } : {},
    disabled: !currentMonth,
    uiComponent: 'tax_summary_expenses',
  });

  // Chateable click handler for Pay button
  const payClickProps = useChateableClick({
    message: previousMonth
      ? `Ayúdame a pagar mi F29 de ${formatCurrency(previousMonth.monthly_tax)} del período ${previousPeriodString}`
      : '',
    contextData: previousMonth ? {
      amount: previousMonth.monthly_tax,
      period: previousPeriodString,
      type: 'payment',
    } : {},
    disabled: !previousMonth,
    uiComponent: 'pay_latest_f29',
    entityId: previousMonth?.period_start || '',
    entityType: 'tax_period',
  });

  if (loading) {
    return (
      <div className={clsx(
        "flex gap-6 items-stretch",
        isInDrawer ? "flex-col" : "flex-col xl:flex-row"
      )}>
        {/* Previous Month Skeleton */}
        <div className="relative overflow-hidden rounded-xl border border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50 p-3 shadow-sm dark:border-orange-900/40 dark:from-orange-950/20 dark:to-amber-950/20 flex flex-col xl:w-[38%]">
          {/* Header Skeleton */}
          <div className="mb-3 flex items-start justify-between">
            <div className="h-4 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
            <div className="h-5 w-16 animate-pulse rounded-full bg-orange-300 dark:bg-orange-700" />
          </div>

          <div className="space-y-3">
            {/* Stepper Skeleton */}
            <div className="rounded-lg bg-white/60 p-2.5 dark:bg-slate-900/30">
              <div className="flex items-center justify-between">
                <div className="flex flex-col items-center flex-1">
                  <div className="h-6 w-6 animate-pulse rounded-full bg-orange-300 dark:bg-orange-700" />
                  <div className="mt-1 h-2 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                </div>
                <div className="flex-1 h-0.5 bg-slate-300 dark:bg-slate-600 mx-1" />
                <div className="flex flex-col items-center flex-1">
                  <div className="h-6 w-6 animate-pulse rounded-full bg-slate-300 dark:bg-slate-600" />
                  <div className="mt-1 h-2 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                </div>
                <div className="flex-1 h-0.5 bg-slate-300 dark:bg-slate-600 mx-1" />
                <div className="flex flex-col items-center flex-1">
                  <div className="h-6 w-6 animate-pulse rounded-full bg-slate-300 dark:bg-slate-600" />
                  <div className="mt-1 h-2 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                </div>
              </div>
            </div>

            {/* Tax Skeleton */}
            <div className="rounded-lg bg-white/60 p-2.5 dark:bg-slate-900/30">
              <div className="h-3 w-16 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              <div className="mt-0.5 h-6 w-32 animate-pulse rounded bg-orange-300 dark:bg-orange-700" />
            </div>

            {/* Revenue & Expenses Skeleton */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-white/40 p-2 dark:bg-slate-900/20">
                <div className="h-3 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-0.5 h-4 w-20 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
              <div className="rounded-lg bg-white/40 p-2 dark:bg-slate-900/20">
                <div className="h-3 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-0.5 h-4 w-20 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
            </div>
          </div>
        </div>

        {/* Current Month Skeleton */}
        <div className="relative overflow-hidden rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 to-teal-50 p-3 dark:border-emerald-700 dark:from-emerald-950/30 dark:to-teal-950/30 flex flex-col flex-1">
          {/* Header Skeleton */}
          <div className="mb-3 flex items-start justify-between">
            <div className="h-5 w-32 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
            <div className="h-5 w-16 animate-pulse rounded-full bg-emerald-300 dark:bg-emerald-700" />
          </div>

          <div className="space-y-5">
            {/* Tax Projection Skeleton */}
            <div className="rounded-xl bg-white/70 p-5 dark:bg-slate-900/40">
              <div className="h-3 w-32 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              <div className="mt-2 h-10 w-48 animate-pulse rounded bg-emerald-300 dark:bg-emerald-700" />
            </div>

            {/* Revenue & Expenses Skeleton */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-white/50 p-4 dark:bg-slate-900/30">
                <div className="h-3 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-1.5 h-6 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
              <div className="rounded-lg bg-white/50 p-4 dark:bg-slate-900/30">
                <div className="h-3 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-1.5 h-6 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx(
      "flex gap-6 items-stretch",
      isInDrawer ? "flex-col" : "flex-col xl:flex-row"
    )}>
      {/* Previous Month Card - To Pay (Smaller) */}
      <div className="relative overflow-hidden rounded-xl border border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50 p-3 shadow-sm dark:border-orange-900/40 dark:from-orange-950/20 dark:to-amber-950/20 flex flex-col xl:w-[38%]">
        {/* Header with Badge */}
        <div className="mb-3 flex items-start justify-between">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {previousMonth ? getMonthName(previousMonth.period_start) : 'Mes Anterior'}
          </h3>
          <span className="flex-shrink-0 rounded-full bg-orange-600 px-2 py-0.5 text-xs font-semibold text-white dark:bg-orange-500">
            A Pagar
          </span>
        </div>

        {previousMonth ? (
          <div className="space-y-3">
            {/* Status Stepper */}
            <div className="rounded-lg bg-white/60 p-2.5 dark:bg-slate-900/30">
              <div className="flex items-center justify-between">
                {/* Step 1: Calculado */}
                <div className="flex flex-col items-center flex-1">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-orange-600 text-white dark:bg-orange-500">
                    <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="mt-1 text-[10px] font-medium text-orange-700 dark:text-orange-400">Calculado</span>
                </div>

                {/* Connector 1 */}
                <div className="flex-1 h-0.5 bg-slate-300 dark:bg-slate-600 mx-1" />

                {/* Step 2: Confirmado */}
                <div className="flex flex-col items-center flex-1">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-300 text-slate-600 dark:bg-slate-600 dark:text-slate-400">
                    <span className="text-xs font-bold">2</span>
                  </div>
                  <span className="mt-1 text-[10px] font-medium text-slate-500 dark:text-slate-400">Confirmar</span>
                </div>

                {/* Connector 2 */}
                <div className="flex-1 h-0.5 bg-slate-300 dark:bg-slate-600 mx-1" />

                {/* Step 3: Pagado */}
                <div className="flex flex-col items-center flex-1">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-300 text-slate-600 dark:bg-slate-600 dark:text-slate-400">
                    <span className="text-xs font-bold">3</span>
                  </div>
                  <span className="mt-1 text-[10px] font-medium text-slate-500 dark:text-slate-400">Pagar</span>
                </div>
              </div>
            </div>

            {/* Monthly Tax */}
            <div
              {...prevIvaClickProps}
              className="chateable-element rounded-lg bg-white/60 p-2.5 dark:bg-slate-900/30"
            >
              <p className="text-xs text-slate-600 dark:text-slate-400">Impuesto</p>
              <p className="mt-0.5 text-xl font-bold text-orange-700 dark:text-orange-300">
                {formatCurrency(previousMonth.monthly_tax)}
              </p>
            </div>

            {/* Revenue, Expenses & Pay Button - All in one row */}
            <div className="flex items-stretch gap-2">
              <div
                {...prevRevenueClickProps}
                className="chateable-element flex-1 rounded-lg bg-white/40 p-2 dark:bg-slate-900/20"
              >
                <p className="text-xs text-slate-600 dark:text-slate-400">Ventas</p>
                <p className="mt-0.5 text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {formatCurrency(previousMonth.total_revenue)}
                </p>
              </div>
              <div
                {...prevExpensesClickProps}
                className="chateable-element flex-1 rounded-lg bg-white/40 p-2 dark:bg-slate-900/20"
              >
                <p className="text-xs text-slate-600 dark:text-slate-400">Gastos</p>
                <p className="mt-0.5 text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {formatCurrency(previousMonth.total_expenses)}
                </p>
              </div>
              {/* Pagar button - inline with Ventas and Gastos */}
              <button
                {...payClickProps}
                className="flex items-center justify-center gap-2 rounded-lg bg-orange-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition-all hover:bg-orange-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-1 dark:bg-orange-500 dark:hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Receipt className="h-4 w-4" />
                <span>Pagar</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg bg-white/60 p-2 dark:bg-slate-900/30">
            <AlertCircle className="h-3 w-3 text-orange-600 dark:text-orange-400" />
            <p className="text-xs text-slate-600 dark:text-slate-400">Sin datos</p>
          </div>
        )}
      </div>

      {/* Current Month Card - In Progress (Larger) */}
      <div className="relative overflow-hidden rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 to-teal-50 p-3 dark:border-emerald-700 dark:from-emerald-950/30 dark:to-teal-950/30 flex flex-col flex-1">
        {/* Header with Badge */}
        <div className="mb-3 flex items-start justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {currentMonth ? getMonthName(currentMonth.period_start) : 'Mes Actual'}
          </h3>
          <span className="flex-shrink-0 rounded-full bg-emerald-600 px-2 py-0.5 text-xs font-semibold text-white dark:bg-emerald-500">
            En Curso
          </span>
        </div>

        {currentMonth ? (
          <div className="space-y-5">
            {/* Monthly Tax Projection */}
            <div
              {...currentIvaClickProps}
              className="chateable-element rounded-xl bg-white/70 p-5 dark:bg-slate-900/40"
            >
              <p className="text-sm text-slate-600 dark:text-slate-400">Impuesto Proyectado</p>
              <p className="mt-2 text-4xl font-bold text-emerald-700 dark:text-emerald-300">
                {formatCurrency(currentMonth.monthly_tax)}
              </p>
            </div>

            {/* Revenue & Expenses */}
            <div className="grid grid-cols-2 gap-4">
              <div
                {...currentRevenueClickProps}
                className="chateable-element rounded-lg bg-white/50 p-4 dark:bg-slate-900/30"
              >
                <p className="text-xs text-slate-600 dark:text-slate-400">Ventas</p>
                <p className="mt-1.5 text-lg font-bold text-slate-900 dark:text-slate-100">
                  {formatCurrency(currentMonth.total_revenue)}
                </p>
              </div>
              <div
                {...currentExpensesClickProps}
                className="chateable-element rounded-lg bg-white/50 p-4 dark:bg-slate-900/30"
              >
                <p className="text-xs text-slate-600 dark:text-slate-400">Gastos</p>
                <p className="mt-1.5 text-lg font-bold text-slate-900 dark:text-slate-100">
                  {formatCurrency(currentMonth.total_expenses)}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg bg-white/60 p-3 dark:bg-slate-900/30">
            <AlertCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <p className="text-sm text-slate-600 dark:text-slate-400">Sin datos</p>
          </div>
        )}
      </div>
    </div>
  );
}
