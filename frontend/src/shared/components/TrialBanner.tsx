/**
 * Banner to show when user is in trial period
 */

import { Clock } from "lucide-react";
import { useMemo } from "react";

interface TrialBannerProps {
  trialEndsAt: string | undefined;
  onViewPlansClick: () => void;
}

export function TrialBanner({ trialEndsAt, onViewPlansClick }: TrialBannerProps) {
  const daysRemaining = useMemo(() => {
    if (!trialEndsAt) return null;

    const endDate = new Date(trialEndsAt);
    const now = new Date();
    const diffTime = endDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    return diffDays;
  }, [trialEndsAt]);

  if (daysRemaining === null) return null;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 sm:px-4 py-2.5 sm:py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
      <div className="flex items-center gap-2 sm:gap-3 flex-1 w-full">
        <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          {/* Mobile: Short text */}
          <span className="text-xs font-medium text-blue-900 block sm:hidden">
            {daysRemaining > 0
              ? `Prueba: ${daysRemaining} ${daysRemaining === 1 ? "día" : "días"} restantes`
              : "Tu prueba termina hoy"}
          </span>
          {/* Desktop: Full text */}
          <div className="hidden sm:flex sm:items-center sm:gap-2">
            <span className="text-sm font-semibold text-blue-900">
              Período de prueba activo —
            </span>
            <span className="text-sm text-blue-700">
              {daysRemaining > 0
                ? `Te quedan ${daysRemaining} ${daysRemaining === 1 ? "día" : "días"} de prueba gratuita.`
                : "Tu período de prueba termina hoy."}
            </span>
          </div>
        </div>
      </div>
      <button
        onClick={onViewPlansClick}
        className="w-full sm:w-auto px-3 sm:px-4 py-1.5 sm:py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-medium rounded-md transition-colors whitespace-nowrap"
      >
        <span className="sm:hidden">Ver planes</span>
        <span className="hidden sm:inline">Ver planes y precios</span>
      </button>
    </div>
  );
}
