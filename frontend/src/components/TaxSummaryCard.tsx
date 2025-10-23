import { useState } from 'react';
import clsx from 'clsx';
import { TrendingUp, TrendingDown, Receipt, Calculator, BarChart3, X } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TaxSummary } from '../types/fizko';
import type { ColorScheme } from '../hooks/useColorScheme';
import { TaxSummaryCardSkeleton } from './TaxSummaryCardSkeleton';
import { useChateableClick } from '../hooks/useChateableClick';
import '../styles/chateable.css';

interface TaxSummaryCardProps {
  taxSummary: TaxSummary | null;
  loading: boolean;
  scheme: ColorScheme;
  isCompact?: boolean;
}

export function TaxSummaryCard({ taxSummary, loading, scheme, isCompact = false }: TaxSummaryCardProps) {
  const [showChart, setShowChart] = useState(false);

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
  const netBalance = taxSummary ? taxSummary.total_revenue - taxSummary.total_expenses : 0;
  const profitMargin = taxSummary && taxSummary.total_revenue > 0
    ? (netBalance / taxSummary.total_revenue) * 100
    : 0;
  const periodString = taxSummary
    ? `${formatDate(taxSummary.period_start)} - ${formatDate(taxSummary.period_end)}`
    : '';

  // Chateable click handlers for internal elements (must be called unconditionally)
  const ivaClickProps = useChateableClick({
    message: taxSummary
      ? `Explícame cómo se calculó el IVA de ${formatCurrency(taxSummary.net_iva)} del período ${periodString}`
      : '',
    contextData: taxSummary ? {
      amount: taxSummary.net_iva,
      period: periodString,
      type: 'iva',
    } : {},
    disabled: !taxSummary,
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
  });

  const profitClickProps = useChateableClick({
    message: taxSummary
      ? `Explícame mi utilidad neta de ${formatCurrency(netBalance)} y el margen de ${formatPercent(profitMargin)} del período ${periodString}`
      : '',
    contextData: taxSummary ? {
      amount: netBalance,
      margin: profitMargin,
      period: periodString,
      type: 'profit',
    } : {},
    disabled: !taxSummary,
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
      <div className="overflow-hidden rounded-2xl border border-slate-200/70 bg-white/90 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
        <div className="flex items-center gap-2 px-4 py-3">
          <Calculator className="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <div className="flex flex-1 items-center gap-4 overflow-x-auto">
            {/* Utilidad Neta */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <div className={clsx(
                "rounded-full p-1",
                netBalance >= 0 ? "bg-emerald-100 dark:bg-emerald-950/30" : "bg-rose-100 dark:bg-rose-950/30"
              )}>
                {netBalance >= 0 ? (
                  <TrendingUp className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-rose-600 dark:text-rose-400" />
                )}
              </div>
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Utilidad:</span>
              <span className={clsx(
                "text-xs font-bold",
                netBalance >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
              )}>
                {formatCurrency(netBalance)}
              </span>
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

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
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
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
          {/* Header - Tax Payment Info with toggle button */}
          <div className="relative mb-6">
            <div {...ivaClickProps} className={`${ivaClickProps.className} text-center p-3 -m-3 rounded-xl`}>
              <div className="mb-2 text-sm font-medium text-slate-600 dark:text-slate-400">
                Impuesto próximo mes
              </div>
              <div className="text-4xl font-bold text-blue-900 dark:text-blue-100">
                {formatCurrency(taxSummary.net_iva)}
              </div>
              <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {formatDate(taxSummary.period_start)} - {formatDate(taxSummary.period_end)}
              </div>
            </div>
            {/* Toggle button in top-right corner */}
            <button
              onClick={() => setShowChart(true)}
              className="absolute right-0 top-0 rounded-lg p-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Ver gráfico"
              title="Ver gráfico"
            >
              <BarChart3 className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            </button>
          </div>

      {/* Main Grid - Ingresos y Gastos */}
      <div className="mb-6 grid grid-cols-2 gap-4">
        {/* Ingresos */}
        <div {...revenueClickProps} className={`${revenueClickProps.className} rounded-xl border border-emerald-200/60 bg-gradient-to-br from-emerald-50 to-white p-4 text-center dark:border-emerald-900/40 dark:from-emerald-950/30 dark:to-slate-900/50`}>
          <div className="mb-2 flex items-center justify-center gap-2 text-emerald-600 dark:text-emerald-400">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Ingresos</span>
          </div>
          <div className="text-2xl font-bold text-emerald-900 dark:text-emerald-100">
            {formatCurrency(taxSummary.total_revenue)}
          </div>
        </div>

        {/* Gastos */}
        <div {...expensesClickProps} className={`${expensesClickProps.className} rounded-xl border border-rose-200/60 bg-gradient-to-br from-rose-50 to-white p-4 text-center dark:border-rose-900/40 dark:from-rose-950/30 dark:to-slate-900/50`}>
          <div className="mb-2 flex items-center justify-center gap-2 text-rose-600 dark:text-rose-400">
            <TrendingDown className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Gastos</span>
          </div>
          <div className="text-2xl font-bold text-rose-900 dark:text-rose-100">
            {formatCurrency(taxSummary.total_expenses)}
          </div>
        </div>
      </div>

      {/* Utilidad Neta */}
      <div {...profitClickProps} className={clsx(
        profitClickProps.className,
        "mb-5 rounded-xl border p-4",
        netBalance >= 0
          ? "border-emerald-200/40 bg-gradient-to-br from-emerald-50/50 to-emerald-50/20 dark:border-emerald-800/40 dark:from-emerald-900/25 dark:to-emerald-950/10"
          : "border-rose-300/60 bg-gradient-to-br from-rose-100/80 to-rose-50/40 dark:border-rose-800/50 dark:from-rose-900/40 dark:to-rose-950/20"
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {netBalance >= 0 ? (
              <TrendingUp className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <TrendingDown className="h-5 w-5 text-rose-600 dark:text-rose-400" />
            )}
            <span className={clsx(
              "text-sm font-semibold",
              netBalance >= 0
                ? "text-emerald-900 dark:text-emerald-100"
                : "text-rose-900 dark:text-rose-100"
            )}>
              Utilidad Neta
            </span>
          </div>
          <div className="text-right">
            <div className={clsx(
              "text-xl font-bold",
              netBalance >= 0
                ? "text-emerald-900 dark:text-emerald-100"
                : "text-rose-900 dark:text-rose-100"
            )}>
              {formatCurrency(netBalance)}
            </div>
            <div className={clsx(
              "text-xs",
              netBalance >= 0
                ? "text-emerald-700 dark:text-emerald-300"
                : "text-rose-700 dark:text-rose-300"
            )}>
              Margen: {formatPercent(profitMargin)}
            </div>
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
}
