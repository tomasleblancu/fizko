/**
 * Calendar Widget Component
 * Displays upcoming tax calendar events
 */

import { Calendar, Receipt, Clock } from "lucide-react";
import { ChateableWrapper } from "@/components/ui/ChateableWrapper";
import type { UpcomingEventsResponse } from "@/types/calendar";

interface CalendarWidgetProps {
  upcomingEvents: UpcomingEventsResponse | undefined;
  isLoading: boolean;
  formatDueDate: (date: string) => string;
  formatDaysLeft: (days: number) => string;
}

export function CalendarWidget({
  upcomingEvents,
  isLoading,
  formatDueDate,
  formatDaysLeft,
}: CalendarWidgetProps) {
  // Separate events into urgent (0-10 days) and upcoming (11-60 days)
  const urgentEvents = upcomingEvents?.data.filter(event => event.days_until_due <= 10) || [];
  const upcomingLaterEvents = upcomingEvents?.data.filter(event => event.days_until_due > 10) || [];

  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <div className="flex flex-shrink-0 items-center gap-2 p-6 pb-4">
        <Calendar className="h-5 w-5 text-slate-600 dark:text-slate-400" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Calendario Tributario
        </h3>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
        </div>
      ) : !upcomingEvents || upcomingEvents.data.length === 0 ? (
        <div className="py-8 text-center">
          <Calendar className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" />
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            No hay eventos próximos
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-6 pb-6">
          {/* Urgent Events Section (0-10 days) */}
          {urgentEvents.length > 0 && (
            <div className="mb-6">
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-red-600 dark:text-red-400">
                Próximos 10 días
              </h4>
              <div className="space-y-3">
                {urgentEvents.map((event) => (
                  <ChateableWrapper
                    key={event.id}
                    message={`Dame información sobre mi obligación tributaria: ${event.event_template.name} que vence el ${formatDueDate(event.due_date)}`}
                    contextData={{
                      eventId: event.id,
                      eventTitle: event.event_template.name,
                      dueDate: event.due_date,
                      status: event.status,
                      eventCode: event.event_template.code,
                      daysUntil: event.days_until_due,
                    }}
                    uiComponent="tax_calendar_event"
                    entityId={event.id}
                    entityType="calendar_event"
                  >
                    <div className="rounded-lg border-2 border-red-200 bg-red-50 p-4 shadow-sm dark:border-red-900/50 dark:bg-red-900/10">
                      <div className="mb-2 flex items-start gap-2">
                        <Receipt className="h-5 w-5 text-red-600 dark:text-red-400" />
                        <div className="flex-1">
                          <p className="font-semibold text-slate-900 dark:text-white">
                            {event.event_template.name}
                          </p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            Vence: {formatDueDate(event.due_date)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-red-600" />
                        <span className="text-sm font-semibold text-red-700 dark:text-red-400">
                          {formatDaysLeft(event.days_until_due)}
                        </span>
                      </div>
                    </div>
                  </ChateableWrapper>
                ))}
              </div>
            </div>
          )}

          {/* Later Events Section (11-60 days) */}
          {upcomingLaterEvents.length > 0 && (
            <div>
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Más adelante (11-60 días)
              </h4>
              <div className="space-y-2">
                {upcomingLaterEvents.map((event) => (
                  <ChateableWrapper
                    key={event.id}
                    message={`Dame información sobre mi obligación tributaria: ${event.event_template.name} que vence el ${formatDueDate(event.due_date)}`}
                    contextData={{
                      eventId: event.id,
                      eventTitle: event.event_template.name,
                      dueDate: event.due_date,
                      status: event.status,
                      eventCode: event.event_template.code,
                      daysUntil: event.days_until_due,
                    }}
                    uiComponent="tax_calendar_event"
                    entityId={event.id}
                    entityType="calendar_event"
                  >
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900 dark:text-white">
                            {event.event_template.name}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            {formatDueDate(event.due_date)} · {formatDaysLeft(event.days_until_due)}
                          </p>
                        </div>
                        <Receipt className="h-4 w-4 flex-shrink-0 text-slate-400 dark:text-slate-500" />
                      </div>
                    </div>
                  </ChateableWrapper>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
