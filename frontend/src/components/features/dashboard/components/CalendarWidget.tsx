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
        <div className="flex-1 space-y-3 overflow-y-auto px-6 pb-6">
          {upcomingEvents.data.map((event) => (
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
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800">
                <div className="mb-2 flex items-start gap-2">
                  <Receipt className="h-5 w-5 text-red-600 dark:text-red-400" />
                  <div className="flex-1">
                    <p className="font-medium text-slate-900 dark:text-white">
                      {event.event_template.name}
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Vence: {formatDueDate(event.due_date)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                    {formatDaysLeft(event.days_until_due)}
                  </span>
                </div>
              </div>
            </ChateableWrapper>
          ))}
        </div>
      )}
    </div>
  );
}
