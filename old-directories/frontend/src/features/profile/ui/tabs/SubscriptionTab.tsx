import { useState } from 'react';
import clsx from 'clsx';
import { AlertTriangle } from 'lucide-react';
import { useAuth } from '@/app/providers/AuthContext';
import type { ColorScheme } from '@/shared/hooks/useColorScheme';

interface SubscriptionTabProps {
  scheme: ColorScheme;
  isInDrawer?: boolean;
}

export function SubscriptionTab({ scheme, isInDrawer = false }: SubscriptionTabProps) {
  const { user } = useAuth();
  const [showPlanComparison, setShowPlanComparison] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteAccount = async () => {
    if (confirmText !== 'ELIMINAR') {
      return;
    }

    setIsDeleting(true);

    try {
      console.log('Account deletion requested');
      alert('Funcionalidad de eliminación de cuenta por implementar');
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('Error al intentar eliminar la cuenta');
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
      setConfirmText('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Current Plan Badge */}
      <div className="rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50 p-4 dark:border-emerald-800 dark:from-emerald-950/30 dark:to-teal-950/30">
        <div className="flex items-center gap-3">
          <svg className="h-6 w-6 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <div>
            <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
              Plan Actual: <span className="font-bold">Básico</span>
            </p>
          </div>
        </div>
      </div>

      {/* Plans Comparison */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
          Planes Disponibles
        </h3>

        <div className={isInDrawer ? "space-y-4" : "grid gap-4 sm:grid-cols-2"}>
          {/* Basic Plan */}
          <div className="rounded-xl border-2 border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h4 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Básico
                </h4>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  Perfecto para comenzar
                </p>
              </div>
              <div className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
                Actual
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-slate-900 dark:text-slate-100">0.25 UF</span>
              <span className="text-sm text-slate-600 dark:text-slate-400">/mes</span>
            </div>
          </div>

          {/* Professional Plan */}
          <div className="rounded-xl border-2 border-emerald-500 bg-white p-5 shadow-md dark:border-emerald-600 dark:bg-slate-900">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h4 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  Profesional
                </h4>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  Para pequeñas empresas
                </p>
              </div>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">1 UF</span>
              <span className="text-sm text-slate-600 dark:text-slate-400">/mes</span>
            </div>
            <button
              disabled
              className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white opacity-50 transition-colors dark:bg-emerald-700"
            >
              Próximamente
            </button>
          </div>
        </div>

        {/* Plan Comparison Toggle */}
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => setShowPlanComparison(!showPlanComparison)}
            className="flex items-center gap-2 rounded-lg bg-slate-100 px-4 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            <span>Comparar planes</span>
            <svg
              className={clsx(
                "h-4 w-4 transition-transform",
                showPlanComparison && "rotate-180"
              )}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Plan Comparison Table */}
        {showPlanComparison && (
          <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[500px]">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Característica
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Básico
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                      Profesional
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Precio mensual
                    </td>
                    <td className="px-4 py-3 text-center text-xs font-medium text-slate-900 dark:text-slate-100">
                      0.25 UF
                    </td>
                    <td className="px-4 py-3 text-center text-xs font-medium text-emerald-600 dark:text-emerald-400">
                      1 UF
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Sincronización con el SII
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Documentos
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Ilimitados
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Ilimitados
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Asistente IA
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Básico
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Avanzado
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Calendario tributario
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Resolución de F29
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Reportes personalizados
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <svg className="mx-auto h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                      Soporte
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Chat
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-slate-700 dark:text-slate-300">
                      Chat + Email
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Billing History */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
          Historial de Facturación
        </h3>
        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3.5 dark:border-slate-700 dark:bg-slate-800/50">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            No hay facturas disponibles para tu plan actual.
          </p>
        </div>
      </div>

      {/* Danger Zone */}
      <div>
        <div className="flex items-start gap-3 mb-3">
          <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-300">
              Zona de Peligro
            </h3>
            <p className="text-sm text-red-700 dark:text-red-400 mt-0.5">
              Las acciones en esta sección son irreversibles.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-red-200 bg-white p-4 dark:border-red-800 dark:bg-slate-800/50">
          <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-2">
            Eliminar cuenta
          </h4>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            Una vez que elimines tu cuenta, no hay vuelta atrás. Por favor, asegúrate de estar completamente seguro.
          </p>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Eliminar mi cuenta
            </button>
          ) : (
            <div className="space-y-4 border-t border-slate-200 dark:border-slate-700 pt-4">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">
                  ¿Estás absolutamente seguro?
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Esta acción no se puede deshacer. Esto eliminará permanentemente tu cuenta y todos los datos asociados.
                </p>
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-2">
                  Por favor escribe <span className="font-mono font-bold text-red-600 dark:text-red-500">ELIMINAR</span> para confirmar:
                </p>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 dark:bg-slate-800 dark:border-slate-600 dark:text-slate-100"
                  placeholder="Escribe ELIMINAR"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleDeleteAccount}
                  disabled={confirmText !== 'ELIMINAR' || isDeleting}
                  className={clsx(
                    'px-4 py-2.5 font-medium rounded-lg transition-colors text-sm',
                    confirmText === 'ELIMINAR' && !isDeleting
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-slate-300 text-slate-500 cursor-not-allowed dark:bg-slate-700 dark:text-slate-500'
                  )}
                >
                  {isDeleting ? 'Eliminando...' : 'Confirmar eliminación'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setConfirmText('');
                  }}
                  disabled={isDeleting}
                  className="px-4 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium rounded-lg transition-colors text-sm dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-300"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 dark:bg-slate-800/50 dark:border-slate-700">
        <p className="text-xs text-slate-600 dark:text-slate-400">
          <strong>Nota:</strong> Si tienes problemas con tu cuenta o deseas hacer una pausa temporal,
          te recomendamos contactar a nuestro equipo de soporte antes de eliminar tu cuenta.
        </p>
      </div>
    </div>
  );
}
