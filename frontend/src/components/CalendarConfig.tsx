import { useEffect, useState } from 'react';
import { Calendar, Check, X, RefreshCw, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../lib/config';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../lib/api-client';

interface EventTemplateConfig {
  event_template_id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  authority: string;
  is_mandatory: boolean;
  default_recurrence: {
    frequency: string;
    day_of_month?: number;
    month_of_year?: number;
  };
  is_active: boolean;
  company_event_id: string | null;
  custom_config: any;
}

interface CalendarConfigData {
  company_id: string;
  company_name: string;
  event_templates: EventTemplateConfig[];
  total_available: number;
  total_active: number;
}

interface CalendarConfigProps {
  companyId: string;
}

export default function CalendarConfig({ companyId }: CalendarConfigProps) {
  const { session } = useAuth();
  const [config, setConfig] = useState<CalendarConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchConfig = async () => {
    if (!session?.access_token) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${companyId}/calendar-config`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error al cargar configuración');
      }

      const data = await response.json();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEvent = (eventTemplateId: string, currentlyActive: boolean) => {
    if (!session?.access_token) return;

    // Actualización optimista: actualizar el estado inmediatamente en el UI
    const newActiveState = !currentlyActive;
    setConfig((prevConfig) => {
      if (!prevConfig) return prevConfig;
      return {
        ...prevConfig,
        event_templates: prevConfig.event_templates.map((eventTemplate) =>
          eventTemplate.event_template_id === eventTemplateId
            ? { ...eventTemplate, is_active: newActiveState }
            : eventTemplate
        ),
        total_active: prevConfig.total_active + (newActiveState ? 1 : -1),
      };
    });

    // Hacer la llamada al backend en segundo plano (sin await)
    const endpoint = currentlyActive ? 'deactivate' : 'activate';
    apiFetch(
      `${API_BASE_URL}/admin/companies/${companyId}/calendar-config/${endpoint}`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ event_template_id: eventTemplateId }),
      }
    )
      .then(async (response) => {
        if (!response.ok) {
          // Si falla, revertir el cambio optimista
          setConfig((prevConfig) => {
            if (!prevConfig) return prevConfig;
            return {
              ...prevConfig,
              event_templates: prevConfig.event_templates.map((eventTemplate) =>
                eventTemplate.event_template_id === eventTemplateId
                  ? { ...eventTemplate, is_active: currentlyActive }
                  : eventTemplate
              ),
              total_active: prevConfig.total_active + (currentlyActive ? 1 : -1),
            };
          });
          throw new Error('Error al actualizar evento');
        }
        const data = await response.json();
        setSuccessMessage(data.message);
        setTimeout(() => setSuccessMessage(null), 3000);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Error desconocido');
        setTimeout(() => setError(null), 5000);
      });
  };

  const handleSyncCalendar = async () => {
    if (!session?.access_token) return;

    try {
      setSyncing(true);
      setError(null);
      setSuccessMessage(null);

      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${companyId}/sync-calendar`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al sincronizar calendario');
      }

      const data = await response.json();
      setSuccessMessage(data.message + ` (${data.total_events} eventos creados)`);

      // Limpiar mensaje después de 5 segundos
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [companyId, session?.access_token]);

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
        disabled={syncing || config.total_active === 0}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {syncing ? (
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

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-900/20">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-600 dark:text-red-400" />
          <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
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
