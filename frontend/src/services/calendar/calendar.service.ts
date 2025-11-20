/**
 * Calendar Service
 *
 * Handles calendar events, event templates, and company event configuration
 * Uses Supabase client directly for database operations
 */

import { createClient } from '@/lib/supabase/client';
import { CeleryTaskService } from '@/services/celery/celery-task.service';
import type {
  EventTemplate,
  CompanyEvent,
  CalendarEvent,
  EventHistory,
  EventTask,
  ListEventsParams,
  CreateCalendarEventRequest,
  UpdateCalendarEventRequest,
  AddEventHistoryRequest,
  CalendarEventFull,
} from '@/types/calendar.types';

export class CalendarService {
  /**
   * Get all available event templates (global catalog)
   *
   * @returns List of all event templates
   */
  static async getEventTemplates(): Promise<EventTemplate[]> {
    console.log('[Calendar Service] Fetching event templates');

    const supabase = createClient();

    const { data, error } = await supabase
      .from('event_templates')
      .select('*')
      .order('category', { ascending: true })
      .order('name', { ascending: true });

    if (error) {
      console.error('[Calendar Service] Error fetching event templates:', error);
      throw new Error(`Error al obtener templates: ${error.message}`);
    }

    console.log(`[Calendar Service] Found ${data.length} event templates`);

    return data as EventTemplate[];
  }

  /**
   * Get a specific event template by code
   *
   * @param code - Event template code (e.g., 'f29', 'f22')
   * @returns Event template
   */
  static async getEventTemplateByCode(code: string): Promise<EventTemplate> {
    console.log(`[Calendar Service] Fetching event template: ${code}`);

    const supabase = createClient();

    const { data, error } = await supabase
      .from('event_templates')
      .select('*')
      .eq('code', code)
      .single();

    if (error) {
      console.error('[Calendar Service] Error fetching event template:', error);
      throw new Error(`Error al obtener template: ${error.message}`);
    }

    return data as EventTemplate;
  }

  /**
   * Initialize calendar events for a company
   *
   * Creates company_events (company-template relationships) for mandatory events
   * and optionally for other selected event templates.
   *
   * This is called during onboarding after company setup is complete.
   *
   * @param companyId - Company UUID
   * @param selectedTemplateIds - Optional: specific event template IDs to enable (if not provided, only mandatory events)
   * @returns Created company events
   */
  static async initializeCompanyCalendar(
    companyId: string,
    selectedTemplateIds?: string[]
  ): Promise<CompanyEvent[]> {
    console.log(
      `[Calendar Service] Initializing calendar for company ${companyId}`
    );

    const supabase = createClient();

    // Get event templates to create company_events for
    let query = supabase.from('event_templates').select('id, code, name');

    if (selectedTemplateIds && selectedTemplateIds.length > 0) {
      // Create company_events for selected templates
      query = query.in('id', selectedTemplateIds);
    } else {
      // Only create company_events for mandatory templates
      query = query.eq('is_mandatory', true);
    }

    const { data: templates, error: templatesError } = await query;

    if (templatesError) {
      console.error('[Calendar Service] Error fetching templates:', templatesError);
      throw new Error(`Error al obtener templates: ${templatesError.message}`);
    }

    if (!templates || templates.length === 0) {
      console.log('[Calendar Service] No templates found to initialize');
      return [];
    }

    console.log(
      `[Calendar Service] Creating company_events for ${templates.length} templates:`,
      templates.map((t) => t.code).join(', ')
    );

    // Create company_events for each template
    const companyEventsToInsert = templates.map((template) => ({
      company_id: companyId,
      event_template_id: template.id,
      is_active: true,
      custom_config: {},
    }));

    const { data: companyEvents, error: insertError } = await supabase
      .from('company_events')
      .upsert(companyEventsToInsert, {
        onConflict: 'company_id,event_template_id',
        ignoreDuplicates: false,
      })
      .select();

    if (insertError) {
      console.error('[Calendar Service] Error creating company_events:', insertError);
      throw new Error(`Error al crear eventos: ${insertError.message}`);
    }

    console.log(
      `[Calendar Service] Created ${companyEvents.length} company events`
    );

    // Launch calendar sync task to generate concrete calendar_events
    try {
      console.log('[Calendar Service] Launching calendar sync task');
      await CeleryTaskService.syncCompanyCalendar(companyId);
      console.log('[Calendar Service] Calendar sync task launched successfully');
    } catch (error) {
      console.error('[Calendar Service] Failed to launch calendar sync task:', error);
      // Don't throw - company_events were created successfully
      // The sync can be triggered manually later if needed
    }

    return companyEvents as CompanyEvent[];
  }

  /**
   * Get company events (company-template relationships)
   *
   * @param companyId - Company UUID
   * @param isActive - Filter by active status
   * @returns List of company events for the company
   */
  static async getCompanyEvents(
    companyId: string,
    isActive?: boolean
  ): Promise<CompanyEvent[]> {
    console.log(`[Calendar Service] Fetching company events for ${companyId}`);

    const supabase = createClient();

    let query = supabase
      .from('company_events')
      .select('*')
      .eq('company_id', companyId);

    if (isActive !== undefined) {
      query = query.eq('is_active', isActive);
    }

    const { data, error } = await query.order('created_at', { ascending: false });

    if (error) {
      console.error('[Calendar Service] Error fetching company events:', error);
      throw new Error(`Error al obtener eventos de empresa: ${error.message}`);
    }

    console.log(`[Calendar Service] Found ${data.length} company events`);

    return data as CompanyEvent[];
  }

  /**
   * Enable or disable an event template for a company
   *
   * @param companyId - Company UUID
   * @param eventTemplateId - Event template UUID
   * @param isActive - Whether to enable or disable
   * @returns Updated company event
   */
  static async toggleCompanyEvent(
    companyId: string,
    eventTemplateId: string,
    isActive: boolean
  ): Promise<CompanyEvent> {
    console.log(
      `[Calendar Service] ${isActive ? 'Enabling' : 'Disabling'} event template ${eventTemplateId} for company ${companyId}`
    );

    const supabase = createClient();

    // Check if company_event exists
    const { data: existing } = await supabase
      .from('company_events')
      .select('*')
      .eq('company_id', companyId)
      .eq('event_template_id', eventTemplateId)
      .maybeSingle();

    if (existing) {
      // Update existing
      const { data, error } = await supabase
        .from('company_events')
        .update({ is_active: isActive })
        .eq('company_id', companyId)
        .eq('event_template_id', eventTemplateId)
        .select()
        .single();

      if (error) {
        console.error('[Calendar Service] Error updating company event:', error);
        throw new Error(`Error al actualizar evento: ${error.message}`);
      }

      return data as CompanyEvent;
    } else {
      // Create new
      const { data, error } = await supabase
        .from('company_events')
        .insert({
          company_id: companyId,
          event_template_id: eventTemplateId,
          is_active: isActive,
          custom_config: {},
        })
        .select()
        .single();

      if (error) {
        console.error('[Calendar Service] Error creating company event:', error);
        throw new Error(`Error al crear evento: ${error.message}`);
      }

      return data as CompanyEvent;
    }
  }

  /**
   * List calendar events for a company
   *
   * @param params - Query parameters (dates, status, filters)
   * @returns List of calendar events
   */
  static async listEvents(
    params: ListEventsParams
  ): Promise<CalendarEvent[]> {
    console.log(
      `[Calendar Service] Listing events for company ${params.company_id}`
    );

    const supabase = createClient();

    let query = supabase
      .from('calendar_events')
      .select('*')
      .eq('company_id', params.company_id);

    if (params.start_date) {
      query = query.gte('due_date', params.start_date);
    }

    if (params.end_date) {
      query = query.lte('due_date', params.end_date);
    }

    if (params.status) {
      query = query.eq('status', params.status);
    }

    if (params.event_template_id) {
      query = query.eq('event_template_id', params.event_template_id);
    }

    if (params.limit) {
      query = query.limit(params.limit);
    }

    if (params.offset) {
      query = query.range(params.offset, params.offset + (params.limit || 50) - 1);
    }

    const { data, error } = await query.order('due_date', { ascending: true });

    if (error) {
      console.error('[Calendar Service] Error listing events:', error);
      throw new Error(`Error al listar eventos: ${error.message}`);
    }

    console.log(`[Calendar Service] Found ${data.length} calendar events`);

    return data as CalendarEvent[];
  }

  /**
   * Get a single calendar event by ID with optional relations
   *
   * @param eventId - Calendar event UUID
   * @param includeTemplate - Include event template data
   * @param includeHistory - Include event history
   * @param includeTasks - Include event tasks
   * @returns Calendar event with optional relations
   */
  static async getEvent(
    eventId: string,
    includeTemplate = false,
    includeHistory = false,
    includeTasks = false
  ): Promise<CalendarEventFull> {
    console.log(`[Calendar Service] Fetching event ${eventId}`);

    const supabase = createClient();

    // Build select string
    let selectString = '*';
    if (includeTemplate) {
      selectString += ', event_template:event_templates(*)';
    }

    const { data: event, error } = await supabase
      .from('calendar_events')
      .select(selectString)
      .eq('id', eventId)
      .single();

    if (error || !event) {
      console.error('[Calendar Service] Error fetching event:', error);
      throw new Error(`Error al obtener evento: ${error?.message || 'Evento no encontrado'}`);
    }

    // Create result object with proper typing
    const result = event as any;

    // Fetch history if requested
    if (includeHistory) {
      const { data: history } = await supabase
        .from('event_history')
        .select('*')
        .eq('calendar_event_id', eventId)
        .order('created_at', { ascending: false });

      result.history = history || [];
    }

    // Fetch tasks if requested
    if (includeTasks) {
      const { data: tasks } = await supabase
        .from('event_tasks')
        .select('*')
        .eq('calendar_event_id', eventId)
        .order('order_index', { ascending: true });

      result.tasks = tasks || [];
    }

    return result as CalendarEventFull;
  }

  /**
   * Create a new calendar event
   *
   * @param request - Calendar event creation request
   * @returns Created calendar event
   */
  static async createEvent(
    request: CreateCalendarEventRequest
  ): Promise<CalendarEvent> {
    console.log('[Calendar Service] Creating calendar event');

    const supabase = createClient();

    const { data, error } = await supabase
      .from('calendar_events')
      .insert({
        company_event_id: request.company_event_id,
        company_id: request.company_id,
        event_template_id: request.event_template_id,
        title: request.title,
        description: request.description,
        due_date: request.due_date,
        period_start: request.period_start,
        period_end: request.period_end,
        status: request.status || 'pending',
        auto_generated: false,
        metadata: request.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[Calendar Service] Error creating event:', error);
      throw new Error(`Error al crear evento: ${error.message}`);
    }

    console.log(`[Calendar Service] Created event ${data.id}`);

    return data as CalendarEvent;
  }

  /**
   * Update an existing calendar event
   *
   * @param eventId - Calendar event UUID
   * @param request - Update request
   * @returns Updated calendar event
   */
  static async updateEvent(
    eventId: string,
    request: UpdateCalendarEventRequest
  ): Promise<CalendarEvent> {
    console.log(`[Calendar Service] Updating event ${eventId}`);

    const supabase = createClient();

    const { data, error } = await supabase
      .from('calendar_events')
      .update(request)
      .eq('id', eventId)
      .select()
      .single();

    if (error) {
      console.error('[Calendar Service] Error updating event:', error);
      throw new Error(`Error al actualizar evento: ${error.message}`);
    }

    return data as CalendarEvent;
  }

  /**
   * Update event status
   *
   * Convenience method for updating only the status field
   *
   * @param eventId - Calendar event UUID
   * @param status - New status
   * @param completionData - Optional completion data (for 'completed' status)
   * @returns Updated calendar event
   */
  static async updateEventStatus(
    eventId: string,
    status: string,
    completionData?: Record<string, any>
  ): Promise<CalendarEvent> {
    console.log(`[Calendar Service] Updating event ${eventId} status to ${status}`);

    return this.updateEvent(eventId, {
      status: status as any,
      ...(status === 'completed' && {
        completion_date: new Date().toISOString(),
        completion_data: completionData,
      }),
    });
  }

  /**
   * Delete a calendar event
   *
   * @param eventId - Calendar event UUID
   * @returns Success status
   */
  static async deleteEvent(eventId: string): Promise<{ success: boolean }> {
    console.log(`[Calendar Service] Deleting event ${eventId}`);

    const supabase = createClient();

    const { error } = await supabase
      .from('calendar_events')
      .delete()
      .eq('id', eventId);

    if (error) {
      console.error('[Calendar Service] Error deleting event:', error);
      throw new Error(`Error al eliminar evento: ${error.message}`);
    }

    return { success: true };
  }

  /**
   * Get event history for a calendar event
   *
   * @param eventId - Calendar event UUID
   * @returns List of event history entries
   */
  static async getEventHistory(eventId: string): Promise<EventHistory[]> {
    console.log(`[Calendar Service] Fetching history for event ${eventId}`);

    const supabase = createClient();

    const { data, error } = await supabase
      .from('event_history')
      .select('*')
      .eq('calendar_event_id', eventId)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('[Calendar Service] Error fetching event history:', error);
      throw new Error(`Error al obtener historial: ${error.message}`);
    }

    console.log(`[Calendar Service] Found ${data.length} history entries`);

    return data as EventHistory[];
  }

  /**
   * Add an entry to event history
   *
   * @param request - History entry request
   * @returns Created history entry
   */
  static async addEventHistory(
    request: AddEventHistoryRequest
  ): Promise<EventHistory> {
    console.log(
      `[Calendar Service] Adding history entry to event ${request.calendar_event_id}`
    );

    const supabase = createClient();

    const { data, error } = await supabase
      .from('event_history')
      .insert({
        calendar_event_id: request.calendar_event_id,
        user_id: request.user_id,
        event_type: request.event_type,
        title: request.title,
        description: request.description,
        metadata: request.metadata || {},
      })
      .select()
      .single();

    if (error) {
      console.error('[Calendar Service] Error adding history entry:', error);
      throw new Error(`Error al agregar historial: ${error.message}`);
    }

    return data as EventHistory;
  }

  /**
   * Get tasks for a calendar event
   *
   * @param eventId - Calendar event UUID
   * @returns List of event tasks
   */
  static async getEventTasks(eventId: string): Promise<EventTask[]> {
    console.log(`[Calendar Service] Fetching tasks for event ${eventId}`);

    const supabase = createClient();

    const { data, error } = await supabase
      .from('event_tasks')
      .select('*')
      .eq('calendar_event_id', eventId)
      .order('order_index', { ascending: true });

    if (error) {
      console.error('[Calendar Service] Error fetching event tasks:', error);
      throw new Error(`Error al obtener tareas: ${error.message}`);
    }

    console.log(`[Calendar Service] Found ${data.length} tasks`);

    return data as EventTask[];
  }

  /**
   * Update event task status
   *
   * @param taskId - Event task UUID
   * @param status - New task status
   * @param completionData - Optional completion data
   * @returns Updated task
   */
  static async updateTaskStatus(
    taskId: string,
    status: string,
    completionData?: Record<string, any>
  ): Promise<EventTask> {
    console.log(`[Calendar Service] Updating task ${taskId} status to ${status}`);

    const supabase = createClient();

    const { data, error } = await supabase
      .from('event_tasks')
      .update({
        status: status as any,
        ...(status === 'completed' && {
          completed_at: new Date().toISOString(),
          completion_data: completionData,
        }),
      })
      .eq('id', taskId)
      .select()
      .single();

    if (error) {
      console.error('[Calendar Service] Error updating task status:', error);
      throw new Error(`Error al actualizar tarea: ${error.message}`);
    }

    return data as EventTask;
  }

  /**
   * Get upcoming events for a company
   *
   * Convenience method to get pending events with upcoming due dates
   *
   * @param companyId - Company UUID
   * @param daysAhead - Number of days to look ahead (default: 30)
   * @returns List of upcoming events
   */
  static async getUpcomingEvents(
    companyId: string,
    daysAhead = 30
  ): Promise<CalendarEvent[]> {
    const today = new Date();
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + daysAhead);

    return this.listEvents({
      company_id: companyId,
      start_date: today.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      status: 'pending',
    });
  }

  /**
   * Get overdue events for a company
   *
   * Convenience method to get events that are past due date
   *
   * @param companyId - Company UUID
   * @returns List of overdue events
   */
  static async getOverdueEvents(companyId: string): Promise<CalendarEvent[]> {
    return this.listEvents({
      company_id: companyId,
      status: 'overdue',
    });
  }
}
