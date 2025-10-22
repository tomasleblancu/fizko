import clsx from 'clsx';
import { DollarSign, TrendingUp, TrendingDown, Calculator } from 'lucide-react';
import type { TaxSummary } from '../types/fizko';
import type { ColorScheme } from '../hooks/useColorScheme';
import { TaxSummaryCardSkeleton } from './TaxSummaryCardSkeleton';

interface TaxSummaryCardProps {
  taxSummary: TaxSummary | null;
  loading: boolean;
  scheme: ColorScheme;
  isCompact?: boolean;
}

export function TaxSummaryCard({ taxSummary, loading, scheme, isCompact = false }: TaxSummaryCardProps) {
  if (loading) {
    return <TaxSummaryCardSkeleton isCompact={isCompact} />;
  }

  // Don't show empty state if we're still loading or data is null
  // This prevents flash of "No hay datos disponibles" during initial load
  if (!taxSummary) {
    // Show skeleton instead of empty state during initial load
    return <TaxSummaryCardSkeleton isCompact={isCompact} />;
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-CL', { month: 'short', year: 'numeric' });
  };

  // Compact horizontal layout
  if (isCompact) {
    return (
      <div className="overflow-hidden rounded-2xl border border-slate-200/70 bg-white/90 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
        <div className="flex items-center gap-2 px-4 py-3">
          <Calculator className="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <div className="flex flex-1 items-center gap-4 overflow-x-auto">
            {/* Revenue */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Ingresos:</span>
              <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                {formatCurrency(taxSummary.total_revenue)}
              </span>
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

            {/* Expenses */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <TrendingDown className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Gastos:</span>
              <span className="text-xs font-bold text-rose-600 dark:text-rose-400">
                {formatCurrency(taxSummary.total_expenses)}
              </span>
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

            {/* IVA Neto */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">IVA Neto:</span>
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                {formatCurrency(taxSummary.net_iva)}
              </span>
            </div>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />

            {/* Income Tax */}
            <div className="flex items-center gap-2 whitespace-nowrap">
              <DollarSign className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Impuesto Renta:</span>
              <span className="text-xs font-bold text-purple-600 dark:text-purple-400">
                {formatCurrency(taxSummary.income_tax)}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Full vertical layout
  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Resumen Tributario
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {formatDate(taxSummary.period_start)} - {formatDate(taxSummary.period_end)}
          </p>
        </div>
        <Calculator className="h-6 w-6 text-emerald-500" />
      </div>

      <div className="space-y-3">
        {/* Revenue */}
        <div className="flex items-center justify-between rounded-xl bg-emerald-50 p-3 dark:bg-emerald-950/30">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Ingresos
            </span>
          </div>
          <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
            {formatCurrency(taxSummary.total_revenue)}
          </span>
        </div>

        {/* Expenses */}
        <div className="flex items-center justify-between rounded-xl bg-rose-50 p-3 dark:bg-rose-950/30">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-rose-600 dark:text-rose-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Gastos
            </span>
          </div>
          <span className="text-sm font-bold text-rose-600 dark:text-rose-400">
            {formatCurrency(taxSummary.total_expenses)}
          </span>
        </div>

        {/* IVA */}
        <div className="space-y-2 rounded-xl bg-blue-50 p-3 dark:bg-blue-950/30">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-600 dark:text-slate-400">IVA Cobrado</span>
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">
              {formatCurrency(taxSummary.iva_collected)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-600 dark:text-slate-400">IVA Pagado</span>
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">
              {formatCurrency(taxSummary.iva_paid)}
            </span>
          </div>
          <div className="border-t border-blue-200 pt-2 dark:border-blue-800">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                IVA Neto
              </span>
              <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                {formatCurrency(taxSummary.net_iva)}
              </span>
            </div>
          </div>
        </div>

        {/* Income Tax */}
        <div className="flex items-center justify-between rounded-xl bg-purple-50 p-3 dark:bg-purple-950/30">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Impuesto a la Renta
            </span>
          </div>
          <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
            {formatCurrency(taxSummary.income_tax)}
          </span>
        </div>
      </div>
    </div>
  );
}
