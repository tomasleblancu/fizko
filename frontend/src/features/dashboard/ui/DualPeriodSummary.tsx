import { Calendar, TrendingUp, Receipt, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import type { TaxSummary } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
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
      ? `Analiza mis compras de ${formatCurrency(previousMonth.total_expenses)} en ${previousPeriodString}`
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
      ? `Analiza mis compras de ${formatCurrency(currentMonth.total_expenses)} en ${currentPeriodString}`
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
        <div className="relative overflow-hidden rounded-xl border border-rose-200 bg-gradient-to-br from-rose-50 to-red-50 p-3 shadow-sm dark:border-rose-900/40 dark:from-rose-950/20 dark:to-red-950/20 flex flex-col flex-shrink-0 xl:w-[38%] max-w-full">
          {/* Header Skeleton */}
          <div className="mb-3 flex items-start justify-between">
            <div className="h-4 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
            <div className="h-5 w-16 animate-pulse rounded-full bg-rose-300 dark:bg-rose-700" />
          </div>

          <div className="space-y-2.5">
            {/* Stepper Skeleton */}
            <div className="rounded-lg bg-white/60 p-2 dark:bg-slate-900/30">
              <div className="flex items-center justify-between">
                <div className="flex flex-col items-center flex-1">
                  <div className="h-5 w-5 animate-pulse rounded-full bg-rose-300 dark:bg-rose-700" />
                  <div className="mt-0.5 h-2.5 w-14 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                </div>
                <div className="flex-1 h-0.5 bg-slate-300 dark:bg-slate-600 mx-1" />
                <div className="flex flex-col items-center flex-1">
                  <div className="h-5 w-5 animate-pulse rounded-full bg-slate-300 dark:bg-slate-600" />
                  <div className="mt-0.5 h-2.5 w-14 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                </div>
                <div className="flex-1 h-0.5 bg-slate-300 dark:bg-slate-600 mx-1" />
                <div className="flex flex-col items-center flex-1">
                  <div className="h-5 w-5 animate-pulse rounded-full bg-slate-300 dark:bg-slate-600" />
                  <div className="mt-0.5 h-2.5 w-14 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                </div>
              </div>
            </div>

            {/* Tax Skeleton */}
            <div className="rounded-lg bg-white/60 p-2 dark:bg-slate-900/30">
              <div className="h-3 w-16 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              <div className="mt-0.5 h-5 w-36 animate-pulse rounded bg-rose-300 dark:bg-rose-700" />
            </div>

            {/* Revenue & Expenses Skeleton */}
            <div className="flex items-stretch gap-1.5">
              <div className="flex-1 rounded-lg bg-white/40 p-1.5 dark:bg-slate-900/20">
                <div className="h-2.5 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-0.5 h-4 w-20 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
              <div className="flex-1 rounded-lg bg-white/40 p-1.5 dark:bg-slate-900/20">
                <div className="h-2.5 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-0.5 h-4 w-20 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
              <div className="rounded-lg bg-rose-300 dark:bg-rose-700 px-3 py-1.5 animate-pulse">
                <div className="h-3.5 w-12" />
              </div>
            </div>
          </div>
        </div>

        {/* Current Month Skeleton */}
        <div className="relative overflow-hidden rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 to-teal-50 p-3 dark:border-emerald-700 dark:from-emerald-950/30 dark:to-teal-950/30 flex flex-col flex-1 max-w-full">
          {/* Header Skeleton */}
          <div className="mb-3 flex items-start justify-between">
            <div className="h-5 w-32 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
            <div className="h-5 w-16 animate-pulse rounded-full bg-emerald-300 dark:bg-emerald-700" />
          </div>

          <div className="space-y-4">
            {/* Tax Projection Skeleton */}
            <div className="rounded-xl bg-white/70 p-4 dark:bg-slate-900/40">
              <div className="h-3 w-32 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              <div className="mt-1.5 h-8 w-48 animate-pulse rounded bg-emerald-300 dark:bg-emerald-700" />
            </div>

            {/* Revenue & Expenses Skeleton */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-white/50 p-3 dark:bg-slate-900/30">
                <div className="h-3 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-1 h-5 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
              <div className="rounded-lg bg-white/50 p-3 dark:bg-slate-900/30">
                <div className="h-3 w-12 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
                <div className="mt-1 h-5 w-24 animate-pulse rounded bg-slate-300 dark:bg-slate-700" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // F29 status logic for previous month
  const f29Status = previousMonth?.generated_f29?.status;
  const isPaid = f29Status === 'paid';
  const isPending = f29Status === 'saved';

  // Determine card styling based on payment status
  const previousCardClasses = isPaid
    ? "relative overflow-hidden rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 to-teal-50 p-3 shadow-sm dark:border-emerald-700 dark:from-emerald-950/30 dark:to-teal-950/30 flex flex-col flex-shrink-0 xl:w-[38%] max-w-full"
    : "relative overflow-hidden rounded-xl border border-rose-200 bg-gradient-to-br from-rose-50 to-red-50 p-3 shadow-sm dark:border-rose-900/40 dark:from-rose-950/20 dark:to-red-950/20 flex flex-col flex-shrink-0 xl:w-[38%] max-w-full";

  const previousBadgeClasses = isPaid
    ? "flex-shrink-0 rounded-full bg-emerald-600 px-2 py-0.5 text-xs font-semibold text-white dark:bg-emerald-500"
    : "flex-shrink-0 rounded-full bg-rose-600 px-2 py-0.5 text-xs font-semibold text-white dark:bg-rose-500";

  const previousBadgeText = isPaid ? "Pagado" : "A Pagar";

  return (
    <div className={clsx(
      "flex gap-6 items-stretch",
      isInDrawer ? "flex-col" : "flex-col xl:flex-row"
    )}>
      {/* Previous Month Card - Dynamic based on F29 status */}
      <div className={previousCardClasses}>
        {/* Header with Badge */}
        <div className="mb-2.5 flex items-start justify-between">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {previousMonth ? getMonthName(previousMonth.period_start) : 'Mes Anterior'}
          </h3>
          <span className={previousBadgeClasses}>
            {previousBadgeText}
          </span>
        </div>

        {previousMonth ? (
          <div className="space-y-2.5">
            {/* Status Stepper */}
            <div className="rounded-lg bg-white/60 p-2 dark:bg-slate-900/30">
              <div className="flex items-center justify-between">
                {/* Step 1: Calculado - Always completed */}
                <div className="flex flex-col items-center flex-1">
                  <div className={clsx(
                    "flex h-5 w-5 items-center justify-center rounded-full text-white",
                    isPaid ? "bg-emerald-600 dark:bg-emerald-500" : "bg-rose-600 dark:bg-rose-500"
                  )}>
                    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className={clsx(
                    "mt-0.5 text-[9px] font-medium",
                    isPaid ? "text-emerald-700 dark:text-emerald-400" : "text-rose-700 dark:text-rose-400"
                  )}>Calculado</span>
                </div>

                {/* Connector 1 */}
                <div className={clsx(
                  "flex-1 h-0.5 mx-1",
                  (isPending || isPaid)
                    ? isPaid ? "bg-emerald-400 dark:bg-emerald-600" : "bg-rose-400 dark:bg-rose-600"
                    : "bg-slate-300 dark:bg-slate-600"
                )} />

                {/* Step 2: Guardado - Completed when pending or paid */}
                <div className="flex flex-col items-center flex-1">
                  <div className={clsx(
                    "flex h-5 w-5 items-center justify-center rounded-full",
                    (isPending || isPaid)
                      ? isPaid
                        ? "bg-emerald-600 text-white dark:bg-emerald-500"
                        : "bg-rose-600 text-white dark:bg-rose-500"
                      : "bg-slate-300 text-slate-600 dark:bg-slate-600 dark:text-slate-400"
                  )}>
                    {(isPending || isPaid) ? (
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <span className="text-[10px] font-bold">2</span>
                    )}
                  </div>
                  <span className={clsx(
                    "mt-0.5 text-[9px] font-medium",
                    (isPending || isPaid)
                      ? isPaid
                        ? "text-emerald-700 dark:text-emerald-400"
                        : "text-rose-700 dark:text-rose-400"
                      : "text-slate-500 dark:text-slate-400"
                  )}>Guardado</span>
                </div>

                {/* Connector 2 */}
                <div className={clsx(
                  "flex-1 h-0.5 mx-1",
                  isPaid
                    ? "bg-emerald-400 dark:bg-emerald-600"
                    : "bg-slate-300 dark:bg-slate-600"
                )} />

                {/* Step 3: Pagado - Completed only when paid */}
                <div className="flex flex-col items-center flex-1">
                  <div className={clsx(
                    "flex h-5 w-5 items-center justify-center rounded-full",
                    isPaid
                      ? "bg-emerald-600 text-white dark:bg-emerald-500"
                      : "bg-slate-300 text-slate-600 dark:bg-slate-600 dark:text-slate-400"
                  )}>
                    {isPaid ? (
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <span className="text-[10px] font-bold">3</span>
                    )}
                  </div>
                  <span className={clsx(
                    "mt-0.5 text-[9px] font-medium",
                    isPaid
                      ? "text-emerald-700 dark:text-emerald-400"
                      : "text-slate-500 dark:text-slate-400"
                  )}>Pagado</span>
                </div>
              </div>
            </div>

            {/* Monthly Tax */}
            <div
              {...prevIvaClickProps}
              className="chateable-element rounded-lg bg-white/60 p-2 dark:bg-slate-900/30"
            >
              <p className="text-xs text-slate-600 dark:text-slate-400">Impuesto</p>
              <p className={clsx(
                "mt-0.5 text-lg font-bold",
                isPaid
                  ? "text-emerald-700 dark:text-emerald-300"
                  : "text-rose-700 dark:text-rose-300"
              )}>
                {formatCurrency(previousMonth.monthly_tax)}
              </p>
            </div>

            {/* Revenue, Expenses & Pay Button - All in one row */}
            <div className="flex items-stretch gap-1.5">
              <div
                {...prevRevenueClickProps}
                className="chateable-element flex-1 rounded-lg bg-white/40 p-1.5 dark:bg-slate-900/20"
              >
                <p className="text-[10px] text-slate-600 dark:text-slate-400">Ventas</p>
                <p className="mt-0.5 text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {formatCurrency(previousMonth.total_revenue)}
                </p>
              </div>
              <div
                {...prevExpensesClickProps}
                className="chateable-element flex-1 rounded-lg bg-white/40 p-1.5 dark:bg-slate-900/20"
              >
                <p className="text-[10px] text-slate-600 dark:text-slate-400">Compras</p>
                <p className="mt-0.5 text-xs font-semibold text-slate-900 dark:text-slate-100">
                  {formatCurrency(previousMonth.total_expenses)}
                </p>
              </div>
              {/* Pay button - Only shown when not paid */}
              {!isPaid && (
                <button
                  {...payClickProps}
                  className="flex items-center justify-center gap-1.5 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm transition-all hover:bg-rose-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-1 dark:bg-rose-500 dark:hover:bg-rose-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Receipt className="h-3.5 w-3.5" />
                  <span>Pagar</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg bg-white/60 p-2 dark:bg-slate-900/30">
            <AlertCircle className="h-3 w-3 text-rose-600 dark:text-rose-400" />
            <p className="text-xs text-slate-600 dark:text-slate-400">Sin datos</p>
          </div>
        )}
      </div>

      {/* Current Month Card - In Progress (Larger) */}
      <div className="relative overflow-hidden rounded-xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 to-teal-50 p-3 dark:border-emerald-700 dark:from-emerald-950/30 dark:to-teal-950/30 flex flex-col flex-1 max-w-full">
        {/* Header with Badge */}
        <div className="mb-2.5 flex items-start justify-between">
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            {currentMonth ? getMonthName(currentMonth.period_start) : 'Mes Actual'}
          </h3>
          <span className="flex-shrink-0 rounded-full bg-emerald-600 px-2 py-0.5 text-xs font-semibold text-white dark:bg-emerald-500">
            En Curso
          </span>
        </div>

        {currentMonth ? (
          <div className="space-y-4">
            {/* Monthly Tax Projection */}
            <div
              {...currentIvaClickProps}
              className="chateable-element rounded-xl bg-white/70 p-4 dark:bg-slate-900/40"
            >
              <p className="text-xs text-slate-600 dark:text-slate-400">Impuesto Proyectado</p>
              <p className="mt-1.5 text-3xl font-bold text-emerald-700 dark:text-emerald-300">
                {formatCurrency(currentMonth.monthly_tax)}
              </p>
            </div>

            {/* Revenue & Expenses */}
            <div className="grid grid-cols-2 gap-3">
              <div
                {...currentRevenueClickProps}
                className="chateable-element rounded-lg bg-white/50 p-3 dark:bg-slate-900/30"
              >
                <p className="text-xs text-slate-600 dark:text-slate-400">Ventas</p>
                <p className="mt-1 text-base font-bold text-slate-900 dark:text-slate-100">
                  {formatCurrency(currentMonth.total_revenue)}
                </p>
              </div>
              <div
                {...currentExpensesClickProps}
                className="chateable-element rounded-lg bg-white/50 p-3 dark:bg-slate-900/30"
              >
                <p className="text-xs text-slate-600 dark:text-slate-400">Compras</p>
                <p className="mt-1 text-base font-bold text-slate-900 dark:text-slate-100">
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
