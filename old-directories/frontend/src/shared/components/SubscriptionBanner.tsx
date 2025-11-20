/**
 * Banner to show when user doesn't have an active subscription
 */

import { AlertCircle } from "lucide-react";

interface SubscriptionBannerProps {
  onUpgradeClick: () => void;
}

export function SubscriptionBanner({ onUpgradeClick }: SubscriptionBannerProps) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 sm:px-4 py-2.5 sm:py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
      <div className="flex items-center gap-2 sm:gap-3 flex-1 w-full">
        <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-yellow-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          {/* Mobile: Short text */}
          <span className="text-xs font-medium text-yellow-900 block sm:hidden">
            Acceso limitado — Activa tu suscripción
          </span>
          {/* Desktop: Full text in one line */}
          <span className="hidden sm:block text-sm font-medium text-yellow-900">
            Sin suscripción tienes acceso limitado — Los documentos no se sincronizarán automáticamente desde el SII
          </span>
        </div>
      </div>
      <button
        onClick={onUpgradeClick}
        className="w-full sm:w-auto px-3 sm:px-4 py-1.5 sm:py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-xs sm:text-sm font-medium rounded-md transition-colors whitespace-nowrap"
      >
        <span className="sm:hidden">Iniciar prueba</span>
        <span className="hidden sm:inline">Iniciar prueba gratis (14 días)</span>
      </button>
    </div>
  );
}
