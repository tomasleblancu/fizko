/**
 * Subscription settings page - shows current plan and available plans
 */

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useAuth } from "@/app/providers/AuthContext";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";
import { useSubscription } from "@/shared/hooks/useSubscription";
import type { SubscriptionPlanListResponse } from "@/shared/types/subscription";

export function SubscriptionSettings() {
  const { session } = useAuth();
  const { data: subscription, isLoading: subscriptionLoading } = useSubscription();

  // Fetch available plans
  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: queryKeys.subscription.plans,
    queryFn: async (): Promise<SubscriptionPlanListResponse> => {
      const response = await apiFetch("/api/subscriptions/plans");
      if (!response.ok) {
        throw new Error("Failed to fetch plans");
      }
      return response.json();
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  if (subscriptionLoading || plansLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Cargando información...</span>
      </div>
    );
  }

  const currentPlanCode = subscription?.plan?.code;
  const isInTrial = subscription?.status === "trialing";

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Estado actual
        </h2>

        {subscription ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span className="font-medium text-gray-900">
                {subscription.plan?.name || "Plan Activo"}
              </span>
              {subscription.plan?.tagname && (
                <span className="text-sm text-gray-500">
                  ({subscription.plan.tagname})
                </span>
              )}
            </div>

            {isInTrial && subscription.trial_end && (
              <p className="text-sm text-gray-600 ml-7">
                Período de prueba activo hasta{" "}
                {new Date(subscription.trial_end).toLocaleDateString("es-CL")}
              </p>
            )}

            {!isInTrial && subscription.current_period_end && (
              <p className="text-sm text-gray-600 ml-7">
                Renovación: {new Date(subscription.current_period_end).toLocaleDateString("es-CL")}
              </p>
            )}
          </div>
        ) : (
          <div className="text-gray-600">
            <p>No tienes una suscripción activa.</p>
            <p className="text-sm mt-1">
              Selecciona un plan abajo para comenzar.
            </p>
          </div>
        )}
      </div>

      {/* Available Plans */}
      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Planes disponibles
        </h2>

        <div className="grid md:grid-cols-2 gap-6">
          {plansData?.plans.map((plan) => {
            const isCurrent = currentPlanCode === plan.code;

            return (
              <div
                key={plan.code}
                className={`rounded-lg border-2 p-6 ${
                  isCurrent
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {plan.name}
                    </h3>
                    {plan.tagname && (
                      <p className="text-sm font-medium text-blue-600">
                        {plan.tagname}
                      </p>
                    )}
                  </div>
                  {isCurrent && (
                    <span className="px-2 py-1 bg-blue-600 text-white text-xs font-medium rounded">
                      Actual
                    </span>
                  )}
                </div>

                {plan.tagline && (
                  <p className="text-sm text-gray-600 mb-4">
                    {plan.tagline}
                  </p>
                )}

                <div className="mb-4">
                  <p className="text-3xl font-bold text-gray-900">
                    ${plan.price_monthly.toLocaleString("es-CL")}
                    <span className="text-base font-normal text-gray-600">
                      /mes
                    </span>
                  </p>
                  {plan.trial_days > 0 && !isCurrent && (
                    <p className="text-sm text-green-600 mt-1">
                      {plan.trial_days} días de prueba gratuita
                    </p>
                  )}
                </div>

                <button
                  disabled={isCurrent}
                  className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                    isCurrent
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "bg-blue-600 hover:bg-blue-700 text-white"
                  }`}
                >
                  {isCurrent ? "Plan actual" : "Seleccionar plan"}
                </button>

                <p className="text-xs text-gray-500 text-center mt-3">
                  Contáctanos para activar
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Features Info */}
      <div className="bg-gray-50 rounded-lg p-6 text-sm text-gray-600">
        <p>
          <strong>Nota:</strong> Por el momento, para activar o cambiar de
          plan, contáctanos a través de nuestros canales de soporte. Pronto
          habilitaremos el cambio automático de planes.
        </p>
      </div>
    </div>
  );
}
