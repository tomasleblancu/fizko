import { useState } from 'react';
import { Calendar, RefreshCw, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useCalendarConfig, useToggleEventTemplate, useSyncCalendar } from "@/shared/hooks/useCalendarConfig";

interface CalendarConfigProps {
  companyId: string;
}

export default function CalendarConfig({ companyId }: CalendarConfigProps) {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Use React Query hooks
  const { data: config, isLoading: loading, error } = useCalendarConfig(companyId);
  const toggleMutation = useToggleEventTemplate(companyId);
  const syncMutation = useSyncCalendar(companyId);

  const handleToggleEvent = (eventTemplateId: string, isActive: boolean) => {
    toggleMutation.mutate(
      { eventTemplateId, isActive },
      {
        // No success message needed - optimistic update provides instant feedback
        onError: (err) => {
          setErrorMessage(err instanceof Error ? err.message : 'Error al actualizar evento');
          setTimeout(() => setErrorMessage(null), 5000);
        },
      }
    );
  };

  const handleSyncCalendar = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (data) => {
        // Construir mensaje con detalles de eventos creados y actualizados
        let detailMessage = '';
        if (data.total_created > 0 && data.total_updated > 0) {
          detailMessage = ` (${data.total_created} creados, ${data.total_updated} actualizados)`;
        } else if (data.total_created > 0) {
          detailMessage = ` (${data.total_created} creados)`;
        } else if (data.total_updated > 0) {
          detailMessage = ` (${data.total_updated} actualizados)`;
        }

        setSuccessMessage(data.message + detailMessage);
        setTimeout(() => setSuccessMessage(null), 5000);
      },
      onError: (err) => {
        setErrorMessage(err instanceof Error ? err.message : 'Error desconocido');
        setTimeout(() => setErrorMessage(null), 5000);
      },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!config) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-900/20">
        <p className="text-red-700 dark:text-red-200">Error al cargar la configuración</p>
      </div>
    );
  }

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      impuesto_mensual: 'Impuesto Mensual',
      impuesto_anual: 'Impuesto Anual',
      prevision: 'Previsión',
      declaracion_jurada: 'Declaración Jurada',
      libros: 'Libros Contables',
      otros: 'Otros',
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      impuesto_mensual: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      impuesto_anual: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      prevision: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      declaracion_jurada: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      libros: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
      otros: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
    };
    return colors[category] || colors.otros;
  };

  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      monthly: 'Mensual',
      quarterly: 'Trimestral',
      annual: 'Anual',
      biannual: 'Semestral',
    };
    return labels[frequency] || frequency;
  };

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="text-center">
        <div className="text-2xl font-bold text-gray-900 dark:text-white">
          {config.total_active}
          <span className="text-lg font-normal text-gray-500 dark:text-gray-400">
            /{config.total_available}
          </span>
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400">eventos activos</p>
      </div>

      {/* Sync Button */}
      <button
        onClick={handleSyncCalendar}
        disabled={syncMutation.isPending || config.total_active === 0}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {syncMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Sincronizando...
          </>
        ) : (
          <>
            <RefreshCw className="h-4 w-4" />
            Sincronizar
          </>
        )}
      </button>

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-900 dark:bg-green-900/20">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-green-600 dark:text-green-400" />
          <p className="text-sm text-green-700 dark:text-green-200">{successMessage}</p>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-900/20">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-600 dark:text-red-400" />
          <p className="text-sm text-red-700 dark:text-red-200">{errorMessage}</p>
        </div>
      )}

      {/* Compact Event Types List with Checkboxes */}
      <div className="space-y-1.5">
        {config.event_templates.map((eventTemplate) => (
          <label
            key={eventTemplate.event_template_id}
            className="flex cursor-pointer items-start gap-2 rounded-lg border border-gray-200 bg-white p-2.5 transition-all hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-750"
          >
            {/* Checkbox */}
            <input
              type="checkbox"
              checked={eventTemplate.is_active}
              onChange={() => handleToggleEvent(eventTemplate.event_template_id, eventTemplate.is_active)}
              className="mt-0.5 h-4 w-4 flex-shrink-0 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
            />

            {/* Event Info - Stacked Layout */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {eventTemplate.name}
                </span>
                {eventTemplate.is_mandatory && (
                  <span className="rounded-full bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                    Oblig.
                  </span>
                )}
              </div>

              {/* Secondary info */}
              <div className="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span
                  className={`rounded px-1.5 py-0.5 font-medium ${getCategoryColor(
                    eventTemplate.category
                  )}`}
                >
                  {eventTemplate.code.toUpperCase()}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {getFrequencyLabel(eventTemplate.default_recurrence.frequency)}
                </span>
              </div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}
