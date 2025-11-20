/**
 * Calendar System Types
 *
 * TypeScript interfaces for the Fizko calendar system (event templates, company events, calendar events)
 */

// ============================================================================
// ENUMS
// ============================================================================

export type EventCategory =
  | 'impuesto_mensual' // F29, etc.
  | 'impuesto_anual' // F22, Declaración Renta
  | 'prevision' // Previred
  | 'aduanas' // Declaraciones de importación
  | 'laboral' // Finiquitos, contratos
  | 'otros';

export type EventStatus =
  | 'pending' // Pendiente
  | 'in_progress' // En progreso
  | 'completed' // Completado
  | 'overdue' // Vencido
  | 'cancelled'; // Cancelado

export type TaskStatus = 'pending' | 'completed' | 'failed' | 'skipped';

export type RecurrenceFrequency = 'monthly' | 'quarterly' | 'annual' | 'custom';

export type EventHistoryType =
  | 'created' // Evento creado
  | 'status_changed' // Cambio de estado
  | 'note_added' // Nota agregada
  | 'document_attached' // Documento adjunto
  | 'task_completed' // Tarea completada
  | 'reminder_sent' // Recordatorio enviado
  | 'updated' // Actualización general
  | 'completed' // Evento completado
  | 'cancelled' // Evento cancelado
  | 'system_action'; // Acción automática del sistema

// ============================================================================
// RECURRENCE CONFIG
// ============================================================================

export interface RecurrenceConfig {
  frequency: RecurrenceFrequency;
  interval: number;
  day_of_month?: number;
  months?: number[]; // [1,2,3,4,5,6,7,8,9,10,11,12]
  start_date?: string; // ISO date
  end_date?: string | null; // ISO date
  business_days_adjustment?: boolean;
  advance_days?: number;
}

export interface NotificationSettings {
  enabled: boolean;
  channels: string[]; // ['email', 'in_app', 'whatsapp']
  reminder_days: number[]; // [7, 3, 1]
}

// ============================================================================
// EVENT TEMPLATE (Global catalog)
// ============================================================================

export interface EventTemplate {
  id: string; // UUID
  // Identificación
  code: string; // 'f29', 'f22', 'previred'
  name: string; // 'Declaración Mensual F29'
  description?: string;
  // Clasificación
  category: EventCategory;
  authority?: string; // 'SII', 'Previred', 'Aduana'
  // Aplicabilidad
  is_mandatory: boolean; // Si aplica a todas las empresas
  applies_to_regimes?: string[]; // ['pro_pyme', 'general', '14ter']
  // Configuración por defecto
  default_recurrence: RecurrenceConfig;
  // Metadata
  metadata?: Record<string, any>;
  // Timestamps
  created_at: string;
  updated_at: string;
}

// ============================================================================
// COMPANY EVENT (Company-Template relationship)
// ============================================================================

export interface CompanyEvent {
  id: string; // UUID
  // Relaciones
  company_id: string; // UUID
  event_template_id: string; // UUID
  // Configuración
  is_active: boolean;
  // Configuraciones personalizadas (edge cases only)
  custom_config?: Record<string, any>;
  // Timestamps
  created_at: string;
  updated_at: string;
}

// ============================================================================
// CALENDAR EVENT (Concrete instance)
// ============================================================================

export interface CalendarEvent {
  id: string; // UUID
  // Relaciones
  company_event_id: string; // UUID
  company_id: string; // UUID
  event_template_id: string; // UUID
  // Información del evento
  title: string; // 'F29 Octubre 2025'
  description?: string;
  // Fechas
  due_date: string; // Date (YYYY-MM-DD)
  period_start?: string; // Date (YYYY-MM-DD)
  period_end?: string; // Date (YYYY-MM-DD)
  // Estado
  status: EventStatus;
  // Cumplimiento
  completion_date?: string; // ISO timestamp
  completion_data?: Record<string, any>;
  // Metadata
  auto_generated: boolean;
  metadata?: Record<string, any>;
  // Timestamps
  created_at: string;
  updated_at: string;
}

// ============================================================================
// EVENT TASK (Task within an event)
// ============================================================================

export interface EventTask {
  id: string; // UUID
  // Relación
  calendar_event_id: string; // UUID
  // Información de la tarea
  task_type: string; // 'calculate_iva', 'submit_f29'
  title: string;
  description?: string;
  // Orden y estado
  order_index: number;
  status: TaskStatus;
  // Automatización
  is_automated: boolean;
  automation_config?: Record<string, any>;
  // Resultado
  completion_data?: Record<string, any>;
  completed_at?: string; // ISO timestamp
  // Timestamps
  created_at: string;
  updated_at: string;
}

// ============================================================================
// EVENT DEPENDENCY
// ============================================================================

export interface EventDependency {
  id: string; // UUID
  event_template_id: string; // UUID
  depends_on_event_template_id: string; // UUID
  dependency_type: string; // 'blocks', 'suggests', 'requires_data'
  description?: string;
  created_at: string;
}

// ============================================================================
// EVENT HISTORY
// ============================================================================

export interface EventHistory {
  id: string; // UUID
  calendar_event_id: string; // UUID
  user_id?: string; // UUID (NULL for system actions)
  event_type: EventHistoryType;
  title: string;
  description?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

// ============================================================================
// API REQUEST/RESPONSE TYPES
// ============================================================================

// List events query parameters
export interface ListEventsParams {
  company_id: string;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  status?: EventStatus;
  event_template_id?: string;
  limit?: number;
  offset?: number;
}

// Create calendar event request
export interface CreateCalendarEventRequest {
  company_event_id: string;
  company_id: string;
  event_template_id: string;
  title: string;
  description?: string;
  due_date: string; // YYYY-MM-DD
  period_start?: string; // YYYY-MM-DD
  period_end?: string; // YYYY-MM-DD
  status?: EventStatus;
  metadata?: Record<string, any>;
}

// Update calendar event request
export interface UpdateCalendarEventRequest {
  title?: string;
  description?: string;
  due_date?: string; // YYYY-MM-DD
  status?: EventStatus;
  completion_date?: string; // ISO timestamp
  completion_data?: Record<string, any>;
  metadata?: Record<string, any>;
}

// Add event history request
export interface AddEventHistoryRequest {
  calendar_event_id: string;
  user_id?: string;
  event_type: EventHistoryType;
  title: string;
  description?: string;
  metadata?: Record<string, any>;
}

// Extended types with joined data
export interface CalendarEventWithTemplate extends CalendarEvent {
  event_template?: EventTemplate;
}

export interface CalendarEventWithHistory extends CalendarEvent {
  history?: EventHistory[];
}

export interface CalendarEventWithTasks extends CalendarEvent {
  tasks?: EventTask[];
}

// Full calendar event with all relations
export interface CalendarEventFull extends CalendarEvent {
  event_template?: EventTemplate;
  history?: EventHistory[];
  tasks?: EventTask[];
}
