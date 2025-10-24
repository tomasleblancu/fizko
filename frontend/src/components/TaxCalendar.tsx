import { Calendar, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';
import { ChateableWrapper } from './ChateableWrapper';
import type { ColorScheme } from '../hooks/useColorScheme';

interface TaxCalendarProps {
  scheme: ColorScheme;
  loading?: boolean;
}

interface TaxEvent {
  id: string;
  title: string;
  dueDate: string;
  status: 'pending' | 'completed' | 'overdue';
  type: 'payment' | 'declaration' | 'other';
}

export function TaxCalendar({ scheme, loading = false }: TaxCalendarProps) {
  // Mock data - Replace with real API data later
  const mockEvents: TaxEvent[] = [
    {
      id: '1',
      title: 'Pagar Impuesto Mensual',
      dueDate: '2025-11-12',
      status: 'pending',
      type: 'payment',
    },
    {
      id: '2',
      title: 'Declarar Importación',
      dueDate: '2025-11-15',
      status: 'pending',
      type: 'declaration',
    },
    {
      id: '3',
      title: 'Pagar Previred',
      dueDate: '2025-11-10',
      status: 'pending',
      type: 'payment',
    },
  ];

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

  const getStatusBadge = (event: TaxEvent) => {
    const daysUntil = getDaysUntil(event.dueDate);

    if (event.status === 'completed') {
      return {
        icon: CheckCircle2,
        text: 'Completado',
        className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400',
      };
    }

    if (daysUntil < 0) {
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
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400',
    };
  };

  const getEventIcon = (type: TaxEvent['type']) => {
    const iconClasses = 'h-4 w-4';
    switch (type) {
      case 'payment':
        return '💰';
      case 'declaration':
        return '📋';
      default:
        return '📌';
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 dark:border-slate-800/70 dark:bg-slate-900/70">
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
  const sortedEvents = [...mockEvents].sort((a, b) =>
    new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
  );

  return (
    <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 transition-all duration-300 dark:border-slate-800/70 dark:bg-slate-900/70">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <Calendar className="h-5 w-5 text-slate-600 dark:text-slate-400" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Calendario Tributario
        </h3>
      </div>

      {/* Events List */}
      <div className="space-y-3">
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
            const daysUntil = getDaysUntil(event.dueDate);

            return (
              <ChateableWrapper
                key={event.id}
                message={`Dame información sobre mi obligación tributaria: ${event.title} que vence el ${formatDate(event.dueDate)}`}
                contextData={{
                  eventId: event.id,
                  eventTitle: event.title,
                  dueDate: event.dueDate,
                  status: event.status,
                  type: event.type,
                  daysUntil: daysUntil,
                }}
                uiComponent="tax_calendar_event"
              >
                <div
                  className={clsx(
                    "rounded-lg border p-3 transition-all cursor-pointer",
                    "border-slate-200 bg-white hover:border-emerald-500 hover:shadow-sm",
                    "dark:border-slate-700 dark:bg-slate-800/50 dark:hover:border-emerald-500"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      {/* Event Icon */}
                      <div className="flex-shrink-0 text-xl">
                        {getEventIcon(event.type)}
                      </div>

                      {/* Event Details */}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-slate-900 dark:text-slate-100 truncate">
                          {event.title}
                        </h4>
                        <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
                          Vence: {formatDate(event.dueDate)}
                        </p>
                      </div>
                    </div>

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
              </ChateableWrapper>
            );
          })
        )}
      </div>
    </div>
  );
}
