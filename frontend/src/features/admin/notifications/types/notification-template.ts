/**
 * Type definitions for notification templates
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
}

export interface NotificationTemplateFormData {
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
}

export const DEFAULT_FORM_DATA: NotificationTemplateFormData = {
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
};
