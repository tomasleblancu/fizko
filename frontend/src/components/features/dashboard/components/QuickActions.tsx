/**
 * Quick Actions Component
 * Grid of quick action buttons for common tasks
 */

import { Plus, BarChart3, HelpCircle } from "lucide-react";
import { ChateableWrapper } from "@/components/ui/ChateableWrapper";

export function QuickActions() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
      <div className="grid grid-cols-3 gap-2">
        <ChateableWrapper
          message="Ayúdame a agregar un nuevo gasto o compra"
          contextData={{}}
          uiComponent="quick_action_add_expense"
          entityType="quick_action"
        >
          <button className="flex h-[72px] w-full flex-col items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
            <Plus className="h-5 w-5 flex-shrink-0" />
            <span className="text-center text-xs leading-tight">Gasto</span>
          </button>
        </ChateableWrapper>

        <ChateableWrapper
          message="Dame un resumen detallado de mi situación tributaria actual"
          contextData={{}}
          uiComponent="quick_action_tax_summary"
          entityType="quick_action"
        >
          <button className="flex h-[72px] w-full flex-col items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
            <BarChart3 className="h-5 w-5 flex-shrink-0" />
            <span className="text-center text-xs leading-tight">Resumen</span>
          </button>
        </ChateableWrapper>

        <ChateableWrapper
          message="Muéstrame la información completa de mi sociedad y empresa"
          contextData={{}}
          uiComponent="quick_action_company_info"
          entityType="quick_action"
        >
          <button className="flex h-[72px] w-full flex-col items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">
            <HelpCircle className="h-5 w-5 flex-shrink-0" />
            <span className="text-center text-xs leading-tight">Sociedad</span>
          </button>
        </ChateableWrapper>
      </div>
    </div>
  );
}
