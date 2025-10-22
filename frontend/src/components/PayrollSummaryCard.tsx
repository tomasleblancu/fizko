import clsx from 'clsx';
import { Users, DollarSign, TrendingDown, Briefcase } from 'lucide-react';
import type { PayrollSummary } from '../types/fizko';
import type { ColorScheme } from '../hooks/useColorScheme';

interface PayrollSummaryCardProps {
  payrollSummary: PayrollSummary | null;
  loading: boolean;
  scheme: ColorScheme;
}

export function PayrollSummaryCard({ payrollSummary, loading, scheme }: PayrollSummaryCardProps) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70">
        <div className="flex items-center justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-blue-600 dark:border-slate-700 dark:border-t-blue-400" />
        </div>
      </div>
    );
  }

  if (!payrollSummary) {
    return (
      <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Resumen de Planilla
          </h3>
          <Users className="h-6 w-6 text-slate-400" />
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No hay datos disponibles para este período
        </p>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-CL', { month: 'long', year: 'numeric' });
  };

  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Resumen de Planilla
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {formatDate(payrollSummary.period)}
          </p>
        </div>
        <Users className="h-6 w-6 text-blue-500" />
      </div>

      <div className="space-y-3">
        {/* Total Employees */}
        <div className="flex items-center justify-between rounded-xl bg-blue-50 p-3 dark:bg-blue-950/30">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Total Empleados
            </span>
          </div>
          <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
            {payrollSummary.total_employees}
          </span>
        </div>

        {/* Gross Salary */}
        <div className="flex items-center justify-between rounded-xl bg-emerald-50 p-3 dark:bg-emerald-950/30">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Salario Bruto Total
            </span>
          </div>
          <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
            {formatCurrency(payrollSummary.total_gross_salary)}
          </span>
        </div>

        {/* Deductions */}
        <div className="flex items-center justify-between rounded-xl bg-rose-50 p-3 dark:bg-rose-950/30">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-rose-600 dark:text-rose-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Descuentos Totales
            </span>
          </div>
          <span className="text-sm font-bold text-rose-600 dark:text-rose-400">
            {formatCurrency(payrollSummary.total_deductions)}
          </span>
        </div>

        {/* Net Salary */}
        <div className="flex items-center justify-between rounded-xl bg-slate-100 p-3 dark:bg-slate-800/70">
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-slate-700 dark:text-slate-300" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Salario Líquido Total
            </span>
          </div>
          <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
            {formatCurrency(payrollSummary.total_net_salary)}
          </span>
        </div>

        {/* Employer Contributions */}
        <div className="flex items-center justify-between rounded-xl bg-amber-50 p-3 dark:bg-amber-950/30">
          <div className="flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Aportes Patronales
            </span>
          </div>
          <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
            {formatCurrency(payrollSummary.total_employer_contributions)}
          </span>
        </div>
      </div>
    </div>
  );
}
