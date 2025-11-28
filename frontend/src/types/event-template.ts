export type EventCategory =
  | 'impuesto_mensual'
  | 'impuesto_anual'
  | 'prevision'
  | 'aduanas'
  | 'laboral'
  | 'otros';

export type RecurrenceFrequency = 'monthly' | 'annual' | 'one_time';

export interface RecurrenceConfig {
  frequency: RecurrenceFrequency;
  day_of_month?: number;
  month_of_year?: number;
  business_days_adjustment?: 'before' | 'after' | 'none';
}

export interface EventTemplate {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: EventCategory;
  authority: string | null;
  is_mandatory: boolean;
  applies_to_regimes: string[] | null;
  default_recurrence: RecurrenceConfig;
  metadata: Record<string, any>;
  display_days_before: number;
  created_at: string;
  updated_at: string;
}

export interface CreateEventTemplateDto {
  code: string;
  name: string;
  description?: string;
  category: EventCategory;
  authority?: string;
  is_mandatory?: boolean;
  applies_to_regimes?: string[];
  default_recurrence: RecurrenceConfig;
  metadata?: Record<string, any>;
  display_days_before?: number;
}

export interface UpdateEventTemplateDto {
  code?: string;
  name?: string;
  description?: string;
  category?: EventCategory;
  authority?: string;
  is_mandatory?: boolean;
  applies_to_regimes?: string[];
  default_recurrence?: RecurrenceConfig;
  metadata?: Record<string, any>;
  display_days_before?: number;
}
