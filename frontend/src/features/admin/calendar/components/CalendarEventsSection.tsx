import { useState } from 'react';
import { Calendar, CheckCircle2, Clock, AlertCircle, XCircle, Loader2 } from 'lucide-react';
import { useCalendarEvents } from "@/shared/hooks/useCalendarEvents";

interface CalendarEventsSectionProps {
  companyId: string;
}

export default function CalendarEventsSection({ companyId }: CalendarEventsSectionProps) {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // Use React Query hook
  const { data: events = [], isLoading: loading, error } = useCalendarEvents(companyId, {
    status: statusFilter,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
      case 'overdue':
        return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-600 dark:text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: 'Pendiente',
      in_progress: 'En Progreso',
      completed: 'Completado',
      overdue: 'Vencido',
      cancelled: 'Cancelado',
    };
    return labels[status] || status;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      overdue: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[status] || colors.pending;
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatPeriod = (startDate: string | null, endDate: string | null) => {
    if (!startDate || !endDate) return 'N/A';
    const start = new Date(startDate);
    const end = new Date(endDate);
    return `${start.toLocaleDateString('es-CL', { month: 'short', year: 'numeric' })} - ${end.toLocaleDateString('es-CL', { month: 'short', year: 'numeric' })}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-900/20">
        <p className="text-red-700 dark:text-red-200">
          {error instanceof Error ? error.message : 'Error desconocido'}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
      <div className="border-b border-gray-200 p-6 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Eventos del Calendario
            </h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {events.length} eventos encontrados
            </p>
          </div>

          {/* Status Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setStatusFilter(undefined)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                statusFilter === undefined
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setStatusFilter('saved')}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                statusFilter === 'saved'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Guardados
            </button>
            <button
              onClick={() => setStatusFilter('completed')}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                statusFilter === 'completed'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Completados
            </button>
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="p-6">
        {events.length === 0 ? (
          <div className="py-12 text-center">
            <Calendar className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              No hay eventos en el calendario para esta empresa.
            </p>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
              Configura los eventos tributarios y sincroniza el calendario.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                className="rounded-lg border border-gray-200 bg-gray-50 p-4 transition-all hover:shadow-sm dark:border-gray-700 dark:bg-gray-900"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(event.status)}
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {event.title}
                      </h3>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${getCategoryColor(
                          event.category
                        )}`}
                      >
                        {event.event_template_code.toUpperCase()}
                      </span>
                    </div>

                    {event.description && (
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        {event.description}
                      </p>
                    )}

                    <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Vence: {formatDate(event.due_date)}
                      </span>
                      {event.period_start && event.period_end && (
                        <span>Período: {formatPeriod(event.period_start, event.period_end)}</span>
                      )}
                      {event.completion_date && (
                        <span>Completado: {formatDate(event.completion_date)}</span>
                      )}
                    </div>
                  </div>

                  {/* Status Badge */}
                  <span
                    className={`flex-shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${getStatusColor(
                      event.status
                    )}`}
                  >
                    {getStatusLabel(event.status)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
