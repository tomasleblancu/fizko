import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { TrendingUp, TrendingDown, Receipt, Calculator, BarChart3, ChevronDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TaxSummary } from "@/shared/types/fizko";
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import { TaxSummaryCardSkeleton } from './TaxSummaryCardSkeleton';
import { useChateableClick } from "@/shared/hooks/useChateableClick";
import '@/app/styles/chateable.css';

interface TaxSummaryCardProps {
  taxSummary: TaxSummary | null;
  loading: boolean;
  scheme: ColorScheme;
  isCompact?: boolean;
  onPeriodChange?: (period: string | undefined) => void;
  isInDrawer?: boolean;
}

export function TaxSummaryCard({ taxSummary, loading, scheme, isCompact = false, onPeriodChange, isInDrawer = false }: TaxSummaryCardProps) {
  const [showChart, setShowChart] = useState(false);
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth() + 1;

  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [selectedMonth, setSelectedMonth] = useState(currentMonth);

  // Notify parent when period changes
  useEffect(() => {
    if (onPeriodChange) {
      const period = `${selectedYear}-${selectedMonth.toString().padStart(2, '0')}`;
      onPeriodChange(period);
    }
  }, [selectedYear, selectedMonth, onPeriodChange]);

  // Month names in Spanish (short version)
  const months = [
    { value: 1, label: 'Ene' },
    { value: 2, label: 'Feb' },
    { value: 3, label: 'Mar' },
    { value: 4, label: 'Abr' },
    { value: 5, label: 'May' },
    { value: 6, label: 'Jun' },
    { value: 7, label: 'Jul' },
    { value: 8, label: 'Ago' },
    { value: 9, label: 'Sep' },
    { value: 10, label: 'Oct' },
    { value: 11, label: 'Nov' },
    { value: 12, label: 'Dic' },
  ];

  // Generate years (last 2 years + current year + next year)
  const years = [];
  for (let year = currentYear - 2; year <= currentYear + 1; year++) {
    years.push(year);
  }

  // Helper functions
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-CL', { month: 'short', year: 'numeric' });
  };

  // Calculate metrics (safe to use even if taxSummary is null)
  const periodString = taxSummary
    ? `${formatDate(taxSummary.period_start)} - ${formatDate(taxSummary.period_end)}`
    : '';

  // Chateable click handlers for internal elements (must be called unconditionally)
  const ivaClickProps = useChateableClick({
    message: taxSummary
      ? `Explícame cómo se calculó el impuesto del mes de ${formatCurrency(taxSummary.monthly_tax)} del período ${periodString}`
      : '',
    contextData: taxSummary ? {
      amount: taxSummary.monthly_tax,
      period: periodString,
      type: 'monthly_tax',
      iva_collected: taxSummary.iva_collected,
      iva_paid: taxSummary.iva_paid,
      previous_month_credit: taxSummary.previous_month_credit,
    } : {},
    disabled: !taxSummary,
    uiComponent: 'tax_summary_iva',
    entityId: `${selectedYear}-${selectedMonth.toString().padStart(2, '0')}`,
    entityType: 'tax_period',
  });

  const revenueClickProps = useChateableClick({
    message: taxSummary
      ? `Dame detalles de mis ingresos de ${formatCurrency(taxSummary.total_revenue)} en ${periodString}`
      : '',
    contextData: taxSummary ? {
      amount: taxSummary.total_revenue,
      period: periodString,
      type: 'revenue',
    } : {},
    disabled: !taxSummary,
    uiComponent: 'tax_summary_revenue',
  });

  const expensesClickProps = useChateableClick({
    message: taxSummary
      ? `Analiza mis gastos de ${formatCurrency(taxSummary.total_expenses)} en ${periodString}`
      : '',
    contextData: taxSummary ? {
      amount: taxSummary.total_expenses,
      period: periodString,
      type: 'expenses',
    } : {},
    disabled: !taxSummary,
    uiComponent: 'tax_summary_expenses',
  });

  // Early returns AFTER all hooks have been called
  if (loading) {
    return <TaxSummaryCardSkeleton isCompact={isCompact} />;
  }

  // Don't show empty state if we're still loading or data is null
  // This prevents flash of "No hay datos disponibles" during initial load
  if (!taxSummary) {
    // Show skeleton instead of empty state during initial load
    return <TaxSummaryCardSkeleton isCompact={isCompact} />;
  }

  // Generate mock historical data for chart (last 6 months)
  const generateMockChartData = () => {
    const months = ['Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    return months.map((month, index) => {
      const variation = 0.7 + (Math.random() * 0.6); // Random variation 70-130%
      return {
        month,
        ingresos: Math.round(taxSummary.total_revenue * variation),
        gastos: Math.round(taxSummary.total_expenses * variation),
      };
    });
  };

  const chartData = generateMockChartData();

  // Compact horizontal layout
  if (isCompact) {
    return (
      <div className={isInDrawer ? "overflow-hidden transition-all duration-300" : "overflow-hidden rounded-2xl border border-slate-200/70 bg-white/90 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70"}>
        <div className="flex items-center gap-2 px-4 py-3">
          <Calculator className="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <div className="flex flex-1 items-center gap-4 overflow-x-auto">
            {/* IVA Neto */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <Receipt className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">IVA:</span>
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                {formatCurrency(taxSummary.net_iva)}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Full vertical layout - Simple and clean
  return (
    <div className={isInDrawer ? "transition-all duration-300" : "rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70"}>
      {/* Chart View */}
      {showChart ? (
        <div className="space-y-4">
          {/* Header with toggle */}
          <div className="relative">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Ingresos y Gastos - Últimos 6 Meses
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Datos de prueba
              </p>
            </div>
            <button
              onClick={() => setShowChart(false)}
              className="absolute right-0 top-0 rounded-lg p-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Ver resumen"
              title="Ver resumen"
            >
              <Calculator className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            </button>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis
                  dataKey="month"
                  className="text-xs"
                  tick={{ fill: 'currentColor', className: 'fill-slate-600 dark:fill-slate-400' }}
                />
                <YAxis
                  className="text-xs"
                  tick={{ fill: 'currentColor', className: 'fill-slate-600 dark:fill-slate-400' }}
                  tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgb(255 255 255 / 0.95)',
                    border: '1px solid rgb(226 232 240)',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem'
                  }}
                  formatter={(value: number) => formatCurrency(value)}
                  labelStyle={{ fontWeight: 'bold', marginBottom: '0.25rem' }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '0.875rem', paddingTop: '1rem' }}
                />
                <Line
                  type="monotone"
                  dataKey="ingresos"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Ingresos"
                  dot={{ fill: '#10b981', r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="gastos"
                  stroke="#f43f5e"
                  strokeWidth={2}
                  name="Gastos"
                  dot={{ fill: '#f43f5e', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <>
          {/* Header - Tax Payment Info with period selector and toggle button */}
          <div className="relative mb-6">
            {/* Period Selector - Responsive */}
            {onPeriodChange && (
              <div className="mb-4 flex items-center justify-center gap-2 sm:absolute sm:left-0 sm:top-0 sm:z-10 sm:mb-0 sm:justify-start">
                <select
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 sm:px-2 sm:py-1 sm:text-xs"
                >
                  {months.map((month) => (
                    <option key={month.value} value={month.value}>
                      {month.label}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 sm:px-2 sm:py-1 sm:text-xs"
                >
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="text-center">
              <div className="mb-2 text-sm font-medium text-slate-600 dark:text-slate-400">
                Impuesto próximo mes
              </div>
              <div {...ivaClickProps} className={`${ivaClickProps.className} inline-block p-2 rounded-lg`}>
                <div className="text-4xl font-bold text-blue-900 dark:text-blue-100">
                  {formatCurrency(taxSummary.monthly_tax)}
                </div>
              </div>
              {/* Pagar button */}
              <button
                onClick={() => {
                  // TODO: Implement payment logic
                  console.log('Pagar clicked for period:', periodString);
                }}
                className="mt-3 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:bg-emerald-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:bg-emerald-500 dark:hover:bg-emerald-600"
              >
                <Receipt className="h-4 w-4" />
                Pagar
              </button>
            </div>

            {/* Toggle button in top-right corner */}
            <button
              onClick={() => setShowChart(true)}
              className="absolute right-0 top-0 z-10 rounded-lg p-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Ver gráfico"
              title="Ver gráfico"
            >
              <BarChart3 className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            </button>
          </div>

      {/* Main Grid - Ingresos y Gastos */}
      <div className="grid grid-cols-2 gap-4">
        {/* Ingresos */}
        <div {...revenueClickProps} className={`${revenueClickProps.className} rounded-xl border border-emerald-200/60 bg-gradient-to-br from-emerald-50 to-white p-4 text-center shadow-sm dark:border-emerald-900/40 dark:from-emerald-950/30 dark:to-slate-900/50`}>
          <div className="mb-2 flex items-center justify-center gap-2 text-emerald-600 dark:text-emerald-400">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Ingresos</span>
          </div>
          <div className="text-2xl font-bold text-emerald-900 dark:text-emerald-100">
            {formatCurrency(taxSummary.total_revenue)}
          </div>
        </div>

        {/* Gastos */}
        <div {...expensesClickProps} className={`${expensesClickProps.className} rounded-xl border border-rose-200/60 bg-gradient-to-br from-rose-50 to-white p-4 text-center shadow-sm dark:border-rose-900/40 dark:from-rose-950/30 dark:to-slate-900/50`}>
          <div className="mb-2 flex items-center justify-center gap-2 text-rose-600 dark:text-rose-400">
            <TrendingDown className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Gastos</span>
          </div>
          <div className="text-2xl font-bold text-rose-900 dark:text-rose-100">
            {formatCurrency(taxSummary.total_expenses)}
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
}
