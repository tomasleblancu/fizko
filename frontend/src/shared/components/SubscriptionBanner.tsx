/**
 * Banner to show when user doesn't have an active subscription
 */

import { AlertCircle } from "lucide-react";

interface SubscriptionBannerProps {
  onUpgradeClick: () => void;
}

export function SubscriptionBanner({ onUpgradeClick }: SubscriptionBannerProps) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <h3 className="text-sm font-semibold text-yellow-900">
          Activa tu suscripción para acceder a todas las funcionalidades
        </h3>
        <p className="text-sm text-yellow-700 mt-1">
          Sin suscripción, tienes acceso limitado. Los documentos no se
          sincronizarán automáticamente desde el SII.
        </p>
        <button
          onClick={onUpgradeClick}
          className="mt-3 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium rounded-md transition-colors"
        >
          Iniciar prueba gratis (14 días)
        </button>
      </div>
    </div>
  );
}
