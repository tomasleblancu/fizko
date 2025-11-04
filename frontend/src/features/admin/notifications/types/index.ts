/**
 * Notification Template Types
 */

export interface NotificationTemplate {
  id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  entity_type: string | null;
  message_template: string;
  timing_config: {
    type: string;
    offset_days?: number;
    time?: string;
  };
  priority: string;
  is_active: boolean;
  auto_assign_to_new_companies: boolean;
  metadata: any;
  // WhatsApp Template ID (from Meta Business Manager)
  whatsapp_template_id?: string | null;
}

export interface SummaryConfig {
  service_method: string;
  lookback_days: number;
  date_offset: number;
  send_hour: number;
  send_minute: number;
}

export interface CreateNotificationTemplateForm {
  code: string;
  name: string;
  description: string;
  category: string;
  entity_type: string;
  message_template: string;
  timing_type: string;
  offset_days: string;
  timing_time: string;
  priority: string;
  is_active: boolean;
  auto_assign_to_new_companies: boolean;
  // Summary config (for business summary templates)
  is_summary_template: boolean;
  service_method: string;
  lookback_days: string;
  date_offset: string;
  // WhatsApp Template ID (from Meta Business Manager)
  whatsapp_template_id: string;
}

export const INITIAL_FORM_DATA: CreateNotificationTemplateForm = {
  code: '',
  name: '',
  description: '',
  category: 'calendar',
  entity_type: '',
  message_template: '',
  timing_type: 'relative',
  offset_days: '-1',
  timing_time: '09:00',
  priority: 'normal',
  is_active: true,
  auto_assign_to_new_companies: false,
  // Summary config defaults
  is_summary_template: false,
  service_method: 'get_daily_summary',
  lookback_days: '1',
  date_offset: '-1',
  // WhatsApp Template ID (optional)
  whatsapp_template_id: '',
};
