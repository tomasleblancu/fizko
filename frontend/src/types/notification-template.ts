/**
 * Notification Template types
 */

export type NotificationCategory = 'calendar' | 'tax_document' | 'payroll' | 'system' | 'custom'
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent'

export interface NotificationTemplate {
  id: string
  code: string
  name: string
  description: string | null
  category: NotificationCategory
  entity_type: string | null
  message_template: string
  timing_config: Record<string, any> | null
  priority: NotificationPriority
  is_active: boolean
  can_repeat: boolean
  max_repeats: number | null
  repeat_interval_hours: number | null
  auto_assign_to_new_companies: boolean
  created_at: string
  updated_at: string
}
