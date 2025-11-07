/**
 * Subscription settings page - shows current plan and available plans
 */

import { CheckCircle2, Loader2 } from "lucide-react";
import { useSubscription } from "@/shared/hooks/useSubscription";
import { useSubscriptionPlans } from "@/shared/hooks/useSubscriptionPlans";

export function SubscriptionSettings() {
  const { data: subscription, isLoading: subscriptionLoading } = useSubscription();

  // Fetch available plans (precargado desde Home)
  const { data: plans, isLoading: plansLoading } = useSubscriptionPlans();

  if (subscriptionLoading || plansLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
        <span className="ml-2 text-gray-600 dark:text-gray-400">Cargando información...</span>
      </div>
    );
  }

  const currentPlanCode = subscription?.plan?.code;
  const isInTrial = subscription?.status === "trialing";

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">
          Estado actual
        </h2>

        {subscription ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span className="font-medium text-gray-900 dark:text-slate-100">
                {subscription.plan?.name || "Plan Activo"}
              </span>
              {subscription.plan?.tagname && (
                <span className="text-sm text-gray-500 dark:text-slate-400">
                  ({subscription.plan.tagname})
                </span>
              )}
            </div>

            {isInTrial && subscription.trial_end && (
              <p className="text-sm text-gray-600 dark:text-slate-400 ml-7">
                Período de prueba activo hasta{" "}
                {new Date(subscription.trial_end).toLocaleDateString("es-CL")}
              </p>
            )}

            {!isInTrial && subscription.current_period_end && (
              <p className="text-sm text-gray-600 dark:text-slate-400 ml-7">
                Renovación: {new Date(subscription.current_period_end).toLocaleDateString("es-CL")}
              </p>
            )}
          </div>
        ) : (
          <div className="text-gray-600 dark:text-slate-400">
            <p>No tienes una suscripción activa.</p>
            <p className="text-sm mt-1">
              Selecciona un plan abajo para comenzar.
            </p>
          </div>
        )}
      </div>

      {/* Available Plans */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">
          Planes
        </h2>

        <div className="grid md:grid-cols-2 gap-6">
          {plans?.map((plan) => {
            const isCurrent = currentPlanCode === plan.code;

            return (
              <div
                key={plan.code}
                className={`rounded-lg border-2 p-6 ${
                  isCurrent
                    ? "border-emerald-500 bg-emerald-50 dark:border-emerald-600 dark:bg-emerald-950/30"
                    : "border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    {/* Tagname en grande, nombre del plan en pequeño */}
                    {plan.tagname && (
                      <h3 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-1">
                        {plan.tagname}
                      </h3>
                    )}
                    <p className="text-sm text-gray-600 dark:text-slate-400">
                      {plan.name}
                    </p>
                  </div>
                  {isCurrent && (
                    <span className="px-2 py-1 bg-emerald-600 text-white text-xs font-medium rounded dark:bg-emerald-500">
                      Actual
                    </span>
                  )}
                </div>

                {plan.tagline && (
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                    {plan.tagline}
                  </p>
                )}

                <div className="mb-4">
                  {/* Precio en UF */}
                  <p className="text-3xl font-bold text-gray-900 dark:text-slate-100">
                    {plan.price_monthly_uf?.toFixed(2)} UF
                    <span className="text-base font-normal text-gray-600 dark:text-slate-400">
                      /mes
                    </span>
                  </p>
                  {/* Equivalencia en CLP como referencia */}
                  <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
                    ≈ ${plan.price_monthly.toLocaleString("es-CL")} CLP
                  </p>
                  {plan.trial_days > 0 && !isCurrent && (
                    <p className="text-sm text-emerald-600 dark:text-emerald-400 mt-1">
                      {plan.trial_days} días de prueba gratuita
                    </p>
                  )}
                </div>

                <button
                  disabled={isCurrent}
                  className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                    isCurrent
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-slate-800 dark:text-slate-500"
                      : "bg-emerald-600 hover:bg-emerald-700 text-white dark:bg-emerald-500 dark:hover:bg-emerald-600"
                  }`}
                >
                  {isCurrent ? "Plan actual" : "Seleccionar plan"}
                </button>

                <p className="text-xs text-gray-500 dark:text-slate-400 text-center mt-3">
                  Contáctanos para activar
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Features Info */}
      <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-6 text-sm text-gray-600 dark:text-slate-400">
        <p>
          <strong className="text-gray-900 dark:text-slate-100">Nota:</strong> Por el momento, para activar o cambiar de
          plan, contáctanos a través de nuestros canales de soporte. Pronto
          habilitaremos el cambio automático de planes.
        </p>
      </div>
    </div>
  );
}
