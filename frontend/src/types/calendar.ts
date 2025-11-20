/**
 * Calendar event types for tax calendar
 */

export interface CalendarEvent {
  id: string
  title: string
  event_template: EventTemplate
  due_date: string
  days_until_due: number
  status: EventStatus
}

export interface EventTemplate {
  code: string
  name: string
}

export type EventStatus = 'saved' | 'in_progress' | 'completed' | 'overdue' | 'cancelled'

export interface UpcomingEventsResponse {
  data: CalendarEvent[]
  total: number
  period: {
    start: string
    end: string
    days: number
  }
}
