/**
 * Mobile Forms List Component
 * Card-based layout optimized for mobile devices
 */

import React from "react";
import type { CombinedF29Form, CombinedF29Status } from "@/types/f29";

interface FormsListMobileProps {
  forms: CombinedF29Form[];
  onSelectForm: (form: CombinedF29Form) => void;
  formatPeriod: (year: number, month: number) => string;
  formatCurrency: (amount: number) => string;
  getStatusColor: (status: CombinedF29Status) => string;
  getStatusLabel: (status: CombinedF29Status) => string;
  extractF29Data: (extraData: Record<string, any> | null) => Record<string, any>;
}

export function FormsListMobile({
  forms,
  onSelectForm,
  formatPeriod,
  formatCurrency,
  getStatusColor,
  getStatusLabel,
  extractF29Data,
}: FormsListMobileProps) {
  return (
    <div className="divide-y divide-slate-100 lg:hidden dark:divide-slate-800">
      {forms.map((form) => {
        // Extract total_pagar_plazo_legal from extra_data if available
        const extractedData = extractF29Data(form.source === 'sii' && (form as any).extra_data ? (form as any).extra_data : null);
        const displayAmount = extractedData.total_pagar_plazo_legal !== undefined
          ? extractedData.total_pagar_plazo_legal
          : form.amount;

        return (
          <div
            key={form.id}
            onClick={() => onSelectForm(form)}
            className="cursor-pointer p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-900 dark:text-white">
                  F29 - {formatPeriod(form.period_year, form.period_month)}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {formatCurrency(displayAmount)}
                </p>
              </div>
              <span className={`ml-3 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${getStatusColor(form.status)}`}>
                {getStatusLabel(form.status)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
