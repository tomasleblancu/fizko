import { Calendar, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";
import type { CalendarEvent, EventCategory } from "@/shared/types/fizko";

interface TaxCalendarProps {
  scheme: ColorScheme;
  loading?: boolean;
  events?: CalendarEvent[];
  error?: string | null;
  isInDrawer?: boolean;
}

export function TaxCalendar({ scheme, loading = false, events = [], error, isInDrawer = false }: TaxCalendarProps) {

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-CL', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const getDaysUntil = (dateStr: string) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(dateStr);
    dueDate.setHours(0, 0, 0, 0);
    const diffTime = dueDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getStatusBadge = (event: CalendarEvent) => {
    const daysUntil = getDaysUntil(event.due_date);

    if (event.status === 'completed') {
      return {
        icon: CheckCircle2,
        text: 'Completado',
        className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400',
      };
    }

    if (event.status === 'overdue' || daysUntil < 0) {
      return {
        icon: AlertCircle,
        text: 'Vencido',
        className: 'bg-rose-100 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400',
      };
    }

    if (daysUntil <= 3) {
      return {
        icon: AlertCircle,
        text: `${daysUntil} día${daysUntil !== 1 ? 's' : ''}`,
        className: 'bg-amber-100 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400',
      };
    }

    return {
      icon: Clock,
      text: `${daysUntil} días`,
      className: 'bg-teal-100 text-teal-700 dark:bg-teal-950/30 dark:text-teal-400',
    };
  };

  const getEventIcon = (category: EventCategory) => {
    switch (category) {
      case 'impuesto_mensual':
        return '💰';
      case 'impuesto_anual':
        return '📊';
      case 'prevision':
        return '👥';
      case 'declaracion_jurada':
        return '📋';
      case 'libros':
        return '📚';
      default:
        return '📌';
    }
  };

  if (loading) {
    return (
      <div className={isInDrawer ? "p-0" : "rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70"}>
        <div className="mb-4 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Calendario Tributario
          </h3>
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="h-16 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-700"
            />
          ))}
        </div>
      </div>
    );
  }

  // Sort events by due date
  const sortedEvents = [...events].sort((a, b) =>
    new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
  );

  return (
    <div className={isInDrawer ? "flex h-full w-full flex-col transition-all duration-300" : "flex h-full w-full flex-col rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70"} style={{ boxSizing: 'border-box' }}>
      {/* Header */}
      <div className="mb-4 flex flex-shrink-0 items-center gap-2">
        <Calendar className="h-5 w-5 text-slate-600 dark:text-slate-400" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Calendario Tributario
        </h3>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 p-3 dark:border-rose-900/40 dark:bg-rose-900/20">
          <p className="text-xs text-rose-700 dark:text-rose-200">
            Error al cargar eventos: {error}
          </p>
        </div>
      )}

      {/* Events List - Scrollable */}
      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden" style={{ scrollbarGutter: 'stable' }}>
        <div className="flex flex-col gap-3">
          {sortedEvents.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center dark:border-slate-700 dark:bg-slate-800/50">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                No hay eventos próximos
              </p>
            </div>
          ) : (
            sortedEvents.map((event) => {
              const badge = getStatusBadge(event);
              const StatusIcon = badge.icon;
              const daysUntil = getDaysUntil(event.due_date);

              return (
                <ChateableWrapper
                  key={event.id}
                  message={`Dame información sobre mi obligación tributaria: ${event.title} que vence el ${formatDate(event.due_date)}`}
                  contextData={{
                    eventId: event.id,
                    eventTitle: event.title,
                    dueDate: event.due_date,
                    status: event.status,
                    category: event.event_template?.category,
                    daysUntil: daysUntil,
                    periodStart: event.period_start,
                    periodEnd: event.period_end,
                  }}
                  uiComponent="tax_calendar_event"
                  entityType="calendar_event"
                  entityId={event.id}
                >
                  <div
                    className={clsx(
                      "rounded-lg border p-3 transition-all cursor-pointer",
                      "border-slate-200 bg-white hover:border-emerald-500 hover:shadow-sm",
                      "dark:border-slate-700 dark:bg-slate-800/50 dark:hover:border-emerald-500"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {/* Event Icon */}
                      <div className="flex-shrink-0 text-xl">
                        {getEventIcon(event.event_template?.category || 'otros')}
                      </div>

                      {/* Event Details */}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-slate-900 dark:text-slate-100 truncate">
                          {event.title}
                        </h4>
                        <div className="mt-0.5 flex items-center justify-between gap-3">
                          <p className="text-xs text-slate-600 dark:text-slate-400">
                            Vence: {formatDate(event.due_date)}
                          </p>
                          {/* Status Badge */}
                          <div className={clsx(
                            "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium flex-shrink-0",
                            badge.className
                          )}>
                            <StatusIcon className="h-3.5 w-3.5" />
                            <span>{badge.text}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </ChateableWrapper>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
