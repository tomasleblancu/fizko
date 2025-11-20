/**
 * Notification Subscription and Preferences types
 */

import type { NotificationTemplate, NotificationCategory } from './notification-template'

export interface NotificationSubscription {
  id: string
  company_id: string
  notification_template_id: string
  is_enabled: boolean
  custom_timing_config: Record<string, any> | null
  custom_message_template: string | null
  channels: string[]
  filters: Record<string, any> | null
  created_at: string
  updated_at: string
  template: NotificationTemplate
}

export interface NotificationSubscriptionRequest {
  notification_template_id: string
  is_enabled?: boolean
  custom_timing_config?: Record<string, any> | null
  custom_message_template?: string | null
}

export interface NotificationSubscriptionUpdateRequest {
  is_enabled?: boolean
  custom_timing_config?: Record<string, any> | null
  custom_message_template?: string | null
}

export interface NotificationSubscriptionsResponse {
  data: NotificationSubscription[]
}

export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'

export interface NotificationPreferences {
  id?: string
  user_id?: string
  company_id?: string
  notifications_enabled: boolean
  quiet_hours_start: string | null
  quiet_hours_end: string | null
  quiet_days: DayOfWeek[] | null
  muted_categories: NotificationCategory[] | null
  muted_templates: string[]
  max_notifications_per_day: number
  min_interval_minutes: number
  created_at?: string
  updated_at?: string
}

export interface NotificationPreferencesRequest {
  company_id?: string
  notifications_enabled?: boolean
  quiet_hours_start?: string | null
  quiet_hours_end?: string | null
  quiet_days?: DayOfWeek[] | null
  muted_categories?: NotificationCategory[] | null
  muted_templates?: string[] | null
  max_notifications_per_day?: number
  min_interval_minutes?: number
}

export interface NotificationPreferencesResponse {
  data: NotificationPreferences
}
