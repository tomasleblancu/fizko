/**
 * Desktop Forms List Component
 * Full table layout with all columns
 */

import React from "react";
import { FileText, Calendar } from "lucide-react";
import type { CombinedF29Form, CombinedF29Status } from "@/types/f29";

interface FormsListDesktopProps {
  forms: CombinedF29Form[];
  onSelectForm: (form: CombinedF29Form) => void;
  formatPeriod: (year: number, month: number) => string;
  formatDate: (dateString: string) => string;
  formatCurrency: (amount: number) => string;
  getStatusColor: (status: CombinedF29Status) => string;
  getStatusLabel: (status: CombinedF29Status) => string;
  extractF29Data: (extraData: Record<string, any> | null) => Record<string, any>;
}

export function FormsListDesktop({
  forms,
  onSelectForm,
  formatPeriod,
  formatDate,
  formatCurrency,
  getStatusColor,
  getStatusLabel,
  extractF29Data,
}: FormsListDesktopProps) {
  return (
    <div className="hidden lg:block overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
              Tipo
            </th>
            <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
              Período
            </th>
            <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
              Estado
            </th>
            <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
              Fecha Presentación
            </th>
            <th className="px-6 py-4 text-right text-sm font-medium text-slate-600 dark:text-slate-400">
              Impuesto a Pagar
            </th>
          </tr>
        </thead>
        <tbody>
          {forms.map((form) => {
            // Extract total_pagar_plazo_legal from extra_data if available
            const extractedData = extractF29Data(form.source === 'sii' && (form as any).extra_data ? (form as any).extra_data : null);
            const displayAmount = extractedData.total_pagar_plazo_legal !== undefined
              ? extractedData.total_pagar_plazo_legal
              : form.amount;

            return (
              <tr
                key={form.id}
                onClick={() => onSelectForm(form)}
                className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span className="font-medium text-slate-900 dark:text-white">
                      F29
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                  {formatPeriod(form.period_year, form.period_month)}
                </td>
                <td className="px-6 py-4">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(form.status)}`}>
                    {getStatusLabel(form.status)}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {form.submission_date ? formatDate(form.submission_date) : '-'}
                  </div>
                </td>
                <td className="px-6 py-4 text-right font-medium text-slate-900 dark:text-white">
                  {formatCurrency(displayAmount)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
